CREATE DATABASE sepsis_logicgraph;

USE DATABASE sepsis_logicgraph;

CREATE SCHEMA bronze;
CREATE SCHEMA silver;
CREATE SCHEMA gold;

SHOW SCHEMAS IN DATABASE sepsis_logicgraph;

USE DATABASE SEPSIS_LOGICGRAPH;
USE SCHEMA BRONZE;
USE WAREHOUSE COMPUTE_WH;

USE DATABASE SEPSIS_LOGICGRAPH;
USE SCHEMA BRONZE;

-- 1. PATIENTS
CREATE OR REPLACE TABLE PATIENTS (
    subject_id          INTEGER,
    gender              VARCHAR(1),
    anchor_age          INTEGER,
    anchor_year         INTEGER,
    anchor_year_group   VARCHAR(20),
    dod                 DATE
);

-- 2. ADMISSIONS
CREATE OR REPLACE TABLE ADMISSIONS (
    subject_id              INTEGER,
    hadm_id                 INTEGER,
    admittime               TIMESTAMP_NTZ,
    dischtime               TIMESTAMP_NTZ,
    deathtime               TIMESTAMP_NTZ,
    admission_type          VARCHAR(50),
    admit_provider_id       VARCHAR(20),
    admission_location      VARCHAR(60),
    discharge_location      VARCHAR(60),
    insurance               VARCHAR(30),
    language                VARCHAR(20),
    marital_status          VARCHAR(30),
    race                    VARCHAR(80),
    edregtime               TIMESTAMP_NTZ,
    edouttime               TIMESTAMP_NTZ,
    hospital_expire_flag    INTEGER
);

ALTER TABLE ADMISSIONS MODIFY COLUMN language VARCHAR(50);
ALTER TABLE ADMISSIONS MODIFY COLUMN admission_type VARCHAR(100);
ALTER TABLE ADMISSIONS MODIFY COLUMN admission_location VARCHAR(100);
ALTER TABLE ADMISSIONS MODIFY COLUMN discharge_location VARCHAR(100);
ALTER TABLE ADMISSIONS MODIFY COLUMN race VARCHAR(100);

-- 3. DIAGNOSES_ICD
CREATE OR REPLACE TABLE DIAGNOSES_ICD (
    subject_id      INTEGER,
    hadm_id         INTEGER,
    seq_num         INTEGER,
    icd_code        VARCHAR(10),
    icd_version     INTEGER
);

-- 4. D_ICD_DIAGNOSES (lookup table)
CREATE OR REPLACE TABLE D_ICD_DIAGNOSES (
    icd_code        VARCHAR(10),
    icd_version     INTEGER,
    long_title      VARCHAR(300)
);

-- 5. LABEVENTS
CREATE OR REPLACE TABLE LABEVENTS (
    labevent_id     INTEGER,
    subject_id      INTEGER,
    hadm_id         INTEGER,
    specimen_id     INTEGER,
    itemid          INTEGER,
    charttime       TIMESTAMP_NTZ,
    storetime       TIMESTAMP_NTZ,
    value           VARCHAR(100),
    valuenum        FLOAT,
    valueuom        VARCHAR(20),
    ref_range_lower FLOAT,
    ref_range_upper FLOAT,
    flag            VARCHAR(10),
    priority        VARCHAR(10),
    comments        VARCHAR(500)
);

-- 6. D_LABITEMS (lookup table)
CREATE OR REPLACE TABLE D_LABITEMS (
    itemid          INTEGER,
    label           VARCHAR(100),
    fluid           VARCHAR(50),
    category        VARCHAR(50)
);

-- 7. ICUSTAYS
CREATE OR REPLACE TABLE ICUSTAYS (
    subject_id      INTEGER,
    hadm_id         INTEGER,
    stay_id         INTEGER,
    first_careunit  VARCHAR(50),
    last_careunit   VARCHAR(50),
    intime          TIMESTAMP_NTZ,
    outtime         TIMESTAMP_NTZ,
    los             FLOAT
);

-- 8. D_ITEMS (lookup table)
CREATE OR REPLACE TABLE D_ITEMS (
    itemid          INTEGER,
    label           VARCHAR(200),
    abbreviation    VARCHAR(100),
    linksto         VARCHAR(50),
    category        VARCHAR(50),
    unitname        VARCHAR(50),
    param_type      VARCHAR(30),
    lownormalvalue  FLOAT,
    highnormalvalue FLOAT
);

ALTER WAREHOUSE COMPUTE_WH SET AUTO_SUSPEND = 60;
-- First create a stage specifically for large files
CREATE OR REPLACE STAGE large_files_stage
FILE_FORMAT = (
    TYPE = CSV
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    COMPRESSION = AUTO
);

SHOW STAGES IN SCHEMA SEPSIS_LOGICGRAPH.BRONZE;



-- Issue occured so Dropped and recreated LABEVENTS with the correct 16 columns
DROP TABLE SEPSIS_LOGICGRAPH.BRONZE.LABEVENTS;

CREATE OR REPLACE TABLE SEPSIS_LOGICGRAPH.BRONZE.LABEVENTS (
    labevent_id     INTEGER,
    subject_id      INTEGER,
    hadm_id         INTEGER,
    specimen_id     INTEGER,
    itemid          INTEGER,
    charttime       TIMESTAMP_NTZ,
    storetime       TIMESTAMP_NTZ,
    value           VARCHAR(200),
    valuenum        FLOAT,
    valueuom        VARCHAR(50),
    ref_range_lower FLOAT,
    ref_range_upper FLOAT,
    flag            VARCHAR(10),
    priority        VARCHAR(10),
    comments        VARCHAR(600),
    order_provider_id VARCHAR(20)
);

COPY INTO SEPSIS_LOGICGRAPH.BRONZE.LABEVENTS
FROM @large_files_stage
FILE_FORMAT = (
    TYPE = CSV
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    COMPRESSION = NONE
)
PATTERN = '.*labevents_part_.*'
ON_ERROR = CONTINUE;

ALTER TABLE SEPSIS_LOGICGRAPH.BRONZE.LABEVENTS 
MODIFY COLUMN order_provider_id VARCHAR(50);


-- checking uploaded counts now
SELECT 'PATIENTS'        AS tbl, COUNT(*) AS row_count FROM PATIENTS
UNION ALL
SELECT 'ADMISSIONS'      AS tbl, COUNT(*) AS row_count FROM ADMISSIONS
UNION ALL
SELECT 'DIAGNOSES_ICD'   AS tbl, COUNT(*) AS row_count FROM DIAGNOSES_ICD
UNION ALL
SELECT 'D_ICD_DIAGNOSES' AS tbl, COUNT(*) AS row_count FROM D_ICD_DIAGNOSES
UNION ALL
SELECT 'LABEVENTS'       AS tbl, COUNT(*) AS row_count FROM LABEVENTS
UNION ALL
SELECT 'D_LABITEMS'      AS tbl, COUNT(*) AS row_count FROM D_LABITEMS
UNION ALL
SELECT 'ICUSTAYS'        AS tbl, COUNT(*) AS row_count FROM ICUSTAYS
UNION ALL
SELECT 'D_ITEMS'         AS tbl, COUNT(*) AS row_count FROM D_ITEMS;


SELECT COUNT(*) FROM SEPSIS_LOGICGRAPH.BRONZE.LABEVENTS;