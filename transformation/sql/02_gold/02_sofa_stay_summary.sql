CREATE OR REPLACE TABLE GOLD.SOFA_STAY_SUMMARY AS
WITH sofa_agg AS (
    SELECT
        SUBJECT_ID,
        HADM_ID,
        MAX(CASE WHEN SOFA_COMPONENT = 'renal_creatinine' THEN SOFA_SCORE END) AS renal_score,
        MAX(CASE WHEN SOFA_COMPONENT = 'liver_bilirubin' THEN SOFA_SCORE END) AS liver_score,
        MAX(CASE WHEN SOFA_COMPONENT = 'coag_platelets' THEN SOFA_SCORE END) AS coag_score,
        MAX(CASE WHEN SOFA_COMPONENT = 'resp_pao2' THEN SOFA_SCORE END) AS resp_score
    FROM GOLD.SOFA_LAB_FACT
    GROUP BY SUBJECT_ID, HADM_ID
)
SELECT
    c.SUBJECT_ID,
    c.HADM_ID,
    c.STAY_ID,
    s.renal_score,
    s.liver_score,
    s.coag_score,
    s.resp_score,
    COALESCE(s.renal_score, 0) +
    COALESCE(s.liver_score, 0) +
    COALESCE(s.coag_score, 0) +
    COALESCE(s.resp_score, 0) AS total_sofa_score
FROM SILVER.ICU_COHORT_CLEAN c
LEFT JOIN sofa_agg s
    ON c.SUBJECT_ID = s.SUBJECT_ID
   AND c.HADM_ID = s.HADM_ID;
