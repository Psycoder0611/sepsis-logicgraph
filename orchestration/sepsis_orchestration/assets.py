from pathlib import Path
import json
import os
import urllib.request

from dagster import AssetExecutionContext, ResourceParam, asset
from dagster_snowflake import SnowflakeResource

REPO_ROOT = Path(__file__).resolve().parents[2]


def _run_sql_file(
    context: AssetExecutionContext, snowflake: SnowflakeResource, sql_file: Path
) -> None:
    sql_text = sql_file.read_text(encoding="utf-8")
    statements = [s.strip() for s in sql_text.split(";") if s.strip()]

    with snowflake.get_connection() as conn:
        cursor = conn.cursor()
        try:
            for statement in statements:
                cursor.execute(statement)
        finally:
            cursor.close()

    context.log.info(f"Executed {len(statements)} SQL statements from {sql_file}")


@asset(group_name="incremental_pipeline")
def bronze_labevents_sofa_load(
    context: AssetExecutionContext, snowflake: ResourceParam[SnowflakeResource]
) -> str:
    sql_file = REPO_ROOT / "ingestion/sql_files/bronze_load_only_labevents_sofa.sql"
    _run_sql_file(context, snowflake, sql_file)
    return "bronze_labevents_sofa_load completed"


@asset(group_name="incremental_pipeline")
def silver_labevents_sofa_incremental_merge(
    context: AssetExecutionContext, snowflake: ResourceParam[SnowflakeResource]
) -> str:
    sql_file = REPO_ROOT / "transformation/sql/01_silver/06_silver_labevents_sofa_clean.sql"
    _run_sql_file(context, snowflake, sql_file)
    return "silver_labevents_sofa_incremental_merge completed"


@asset(
    group_name="incremental_pipeline",
    deps=[silver_labevents_sofa_incremental_merge],
)
def gold_dim_patient_refresh(
    context: AssetExecutionContext, snowflake: ResourceParam[SnowflakeResource]
) -> str:
    sql_file = REPO_ROOT / "transformation/sql/02_gold/04_dim_patient.sql"
    _run_sql_file(context, snowflake, sql_file)
    return "gold_dim_patient_refresh completed"


@asset(
    group_name="incremental_pipeline",
    deps=[gold_dim_patient_refresh],
)
def gold_dim_admission_refresh(
    context: AssetExecutionContext, snowflake: ResourceParam[SnowflakeResource]
) -> str:
    sql_file = REPO_ROOT / "transformation/sql/02_gold/05_dim_admission.sql"
    _run_sql_file(context, snowflake, sql_file)
    return "gold_dim_admission_refresh completed"


@asset(
    group_name="incremental_pipeline",
    deps=[gold_dim_admission_refresh],
)
def gold_dim_stay_refresh(
    context: AssetExecutionContext, snowflake: ResourceParam[SnowflakeResource]
) -> str:
    sql_file = REPO_ROOT / "transformation/sql/02_gold/06_dim_stay.sql"
    _run_sql_file(context, snowflake, sql_file)
    return "gold_dim_stay_refresh completed"


@asset(
    group_name="incremental_pipeline",
    deps=[silver_labevents_sofa_incremental_merge],
)
def gold_dim_lab_component_refresh(
    context: AssetExecutionContext, snowflake: ResourceParam[SnowflakeResource]
) -> str:
    sql_file = REPO_ROOT / "transformation/sql/02_gold/07_dim_lab_component.sql"
    _run_sql_file(context, snowflake, sql_file)
    return "gold_dim_lab_component_refresh completed"


@asset(
    group_name="incremental_pipeline",
    deps=[
        gold_dim_patient_refresh,
        gold_dim_admission_refresh,
        gold_dim_stay_refresh,
        gold_dim_lab_component_refresh,
    ],
)
def gold_fact_sofa_lab_refresh(
    context: AssetExecutionContext, snowflake: ResourceParam[SnowflakeResource]
) -> str:
    sql_file = REPO_ROOT / "transformation/sql/02_gold/01_sofa_lab_fact.sql"
    _run_sql_file(context, snowflake, sql_file)
    return "gold_fact_sofa_lab_refresh completed"


@asset(
    group_name="incremental_pipeline",
    deps=[gold_fact_sofa_lab_refresh],
)
def sepsis_slack_alerts(
    context: AssetExecutionContext, snowflake: ResourceParam[SnowflakeResource]
) -> str:
    """Send Slack alerts for SOFA_SCORE >= 2 events from GOLD.FACT_SOFA_LAB."""
    webhook = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook:
        context.log.warning("SLACK_WEBHOOK_URL not set; skipping Slack alerts.")
        return "sepsis_slack_alerts skipped (no webhook)"

    query = """
    SELECT
      f.LABEVENT_ID,
      f.SUBJECT_ID,
      f.SOFA_SCORE,
      a.ADMISSION_LOCATION,
      a.ADMISSION_TYPE,
      f.SOFA_COMPONENT AS COMPONENT
    FROM SEPSIS_LOGICGRAPH.GOLD.FACT_SOFA_LAB f
    LEFT JOIN SEPSIS_LOGICGRAPH.GOLD.DIM_ADMISSION a
      ON f.ADMISSION_SK = a.ADMISSION_SK
    WHERE f.SOFA_SCORE >= 2
    ORDER BY f.LABEVENT_ID DESC
    LIMIT 50
    """

    with snowflake.get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
        finally:
            cursor.close()

    if not rows:
        context.log.info("No SOFA >= 2 rows found; no Slack alerts sent.")
        return "sepsis_slack_alerts completed (0 alerts)"

    sent = 0
    for labevent_id, subject_id, sofa_score, admission_location, admission_type, component in rows:
        text = (
            "Sepsis Alert: "
            f"LABEVENT_ID={labevent_id} | "
            f"SUBJECT_ID={subject_id} | "
            f"SOFA_SCORE={sofa_score} | "
            f"COMPONENT={component} | "
            f"ADMISSION_TYPE={admission_type} | "
            f"ADMISSION_LOCATION={admission_location}"
        )
        payload = {"text": text}
        req = urllib.request.Request(
            webhook,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req).read().decode()
        sent += 1

    context.log.info(f"Sent {sent} Slack sepsis alerts.")
    return f"sepsis_slack_alerts completed ({sent} alerts)"


