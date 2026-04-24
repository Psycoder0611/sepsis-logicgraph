CREATE OR REPLACE TABLE GOLD.SEPSIS_CANDIDATES AS
WITH infection_hadm AS (
    SELECT DISTINCT
        SUBJECT_ID,
        HADM_ID
    FROM SILVER.INFECTION_DIAGNOSIS_CLEAN
)
SELECT
    s.SUBJECT_ID,
    s.HADM_ID,
    s.STAY_ID,
    c.INTIME,
    c.OUTTIME,
    c.FIRST_CAREUNIT,
    c.LAST_CAREUNIT,
    s.renal_score,
    s.liver_score,
    s.coag_score,
    s.resp_score,
    s.total_sofa_score,
    CASE
        WHEN i.HADM_ID IS NOT NULL THEN 1
        ELSE 0
    END AS infection_flag,
    CASE
        WHEN i.HADM_ID IS NOT NULL
         AND s.total_sofa_score >= 2 THEN 1
        ELSE 0
    END AS sepsis_candidate_flag
FROM GOLD.SOFA_STAY_SUMMARY s
LEFT JOIN SILVER.ICU_COHORT_CLEAN c
    ON s.SUBJECT_ID = c.SUBJECT_ID
   AND s.HADM_ID = c.HADM_ID
   AND s.STAY_ID = c.STAY_ID
LEFT JOIN infection_hadm i
    ON s.SUBJECT_ID = i.SUBJECT_ID
   AND s.HADM_ID = i.HADM_ID;
