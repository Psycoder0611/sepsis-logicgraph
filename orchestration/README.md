# Dagster + Snowflake Starter

This folder contains a starter orchestration setup for running your Snowflake
pipeline in Dagster.

## 1) Setup environment

```bash
cd /Users/akanksha/Documents/projects/sepsis-logicgraph/orchestration
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Now fill in Snowflake values in `.env`.

## 2) Export environment variables

```bash
set -a
source .env
set +a
```

## 3) Start Dagster UI

```bash
dagster dev -m sepsis_orchestration.definitions
```

Open [http://127.0.0.1:3000](http://127.0.0.1:3000), materialize assets,
and verify logs from:

- `silver_labevents_sofa_incremental_merge`
- `gold_dim_patient_refresh`
- `gold_dim_admission_refresh`
- `gold_dim_stay_refresh`
- `gold_dim_lab_component_refresh`
- `gold_fact_sofa_lab_refresh`
- `sepsis_slack_alerts`

`sepsis_pipeline_job` starts from Silver and reads from existing
`BRONZE.LABEVENTS_SOFA`.
`bronze_labevents_sofa_load` is optional/manual if you still want direct stage
to Bronze COPY behavior.

## Notes

- Bronze load SQL is executed from
  `ingestion/sql_files/bronze_load_only_labevents_sofa.sql`.
- Silver incremental MERGE SQL is executed from
  `transformation/sql/01_silver/06_silver_labevents_sofa_clean.sql`.
- Gold SQLs are executed from:
  - `transformation/sql/02_gold/04_dim_patient.sql` (from `SILVER.ICU_COHORT_CLEAN`, one row per `SUBJECT_ID`)
  - `transformation/sql/02_gold/05_dim_admission.sql` (from cohort, one row per `HADM_ID`)
  - `transformation/sql/02_gold/06_dim_stay.sql` (from cohort, one row per `STAY_ID`)
  - `transformation/sql/02_gold/07_dim_lab_component.sql` (from `SILVER.LABEVENTS_SOFA_CLEAN`)
  - `transformation/sql/02_gold/01_sofa_lab_fact.sql` builds `GOLD.FACT_SOFA_LAB` with surrogate keys joined to the dims above
- Slack alerts are sent by `sepsis_slack_alerts` for `SOFA_SCORE >= 3` rows from
  `GOLD.FACT_SOFA_LAB` when `SLACK_WEBHOOK_URL` is set.
- This starter intentionally keeps SQL simple; you can later replace transform
  steps with dbt assets.
- Slack integration and Elasticsearch/Kibana logging can be added on top of
  this base.
