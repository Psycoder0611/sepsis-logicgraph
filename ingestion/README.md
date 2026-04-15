# Ingestion Layer

**Owner:** Trapti Kulshrestha  
**Role:** Ingestion Lead

## What's here
- `sql_files/bronze_setup.sql` — Snowflake Bronze layer setup: database, schemas, tables, and COPY INTO commands for all 8 source files

## Tables loaded into BRONZE layer
| Table | Source | Rows |
|---|---|---|
| PATIENTS | hosp/patients.csv.gz | 364,627 |
| ADMISSIONS | hosp/admissions.csv.gz | 546,028 |
| DIAGNOSES_ICD | hosp/diagnoses_icd.csv.gz | 6,364,488 |
| D_ICD_DIAGNOSES | hosp/d_icd_diagnoses.csv.gz | 112,107 |
| LABEVENTS | hosp/labevents.csv.gz | 11,807,228 |
| D_LABITEMS | hosp/d_labitems.csv.gz | 1,650 |
| ICUSTAYS | icu/icustays.csv.gz | 94,458 |
| D_ITEMS | icu/d_items.csv.gz | 4,095 |

## Data source
MIMIC-IV v3.1 — PhysioNet. Access requires credentialing.  
Do NOT commit any data files.
