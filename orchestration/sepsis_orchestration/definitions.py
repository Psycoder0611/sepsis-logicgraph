from dagster import Definitions, ScheduleDefinition, define_asset_job

from sepsis_orchestration.assets import (
    bronze_labevents_sofa_load,
    gold_dim_admission_refresh,
    gold_dim_lab_component_refresh,
    gold_dim_patient_refresh,
    gold_dim_stay_refresh,
    gold_fact_sofa_lab_refresh,
    silver_labevents_sofa_incremental_merge,
)
from sepsis_orchestration.resources import snowflake_resource

sepsis_pipeline_job = define_asset_job(
    name="sepsis_pipeline_job",
    selection=[
        silver_labevents_sofa_incremental_merge,
        gold_dim_patient_refresh,
        gold_dim_admission_refresh,
        gold_dim_stay_refresh,
        gold_dim_lab_component_refresh,
        gold_fact_sofa_lab_refresh,
    ],
)

sepsis_pipeline_schedule = ScheduleDefinition(
    job=sepsis_pipeline_job,
    cron_schedule="*/15 * * * *",  # Every 15 minutes
)

defs = Definitions(
    assets=[
        bronze_labevents_sofa_load,
        silver_labevents_sofa_incremental_merge,
        gold_dim_patient_refresh,
        gold_dim_admission_refresh,
        gold_dim_stay_refresh,
        gold_dim_lab_component_refresh,
        gold_fact_sofa_lab_refresh,
    ],
    jobs=[sepsis_pipeline_job],
    schedules=[sepsis_pipeline_schedule],
    resources={"snowflake": snowflake_resource},
)
