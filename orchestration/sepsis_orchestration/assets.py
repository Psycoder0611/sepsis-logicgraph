from pathlib import Path

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


