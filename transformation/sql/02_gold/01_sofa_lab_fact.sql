CREATE OR REPLACE TABLE GOLD.SOFA_LAB_FACT AS
SELECT
    LABEVENT_ID,
    SUBJECT_ID,
    HADM_ID,
    ITEMID,
    SOFA_COMPONENT,
    CHARTTIME,
    VALUENUM,
    VALUEUOM,
    FLAG,
    CASE
        WHEN SOFA_COMPONENT = 'renal_creatinine' THEN
            CASE
                WHEN VALUENUM < 1.2 THEN 0
                WHEN VALUENUM >= 1.2 AND VALUENUM < 2.0 THEN 1
                WHEN VALUENUM >= 2.0 AND VALUENUM < 3.5 THEN 2
                WHEN VALUENUM >= 3.5 AND VALUENUM < 5.0 THEN 3
                WHEN VALUENUM >= 5.0 THEN 4
                ELSE NULL
            END
        WHEN SOFA_COMPONENT = 'liver_bilirubin' THEN
            CASE
                WHEN VALUENUM < 1.2 THEN 0
                WHEN VALUENUM >= 1.2 AND VALUENUM < 2.0 THEN 1
                WHEN VALUENUM >= 2.0 AND VALUENUM < 6.0 THEN 2
                WHEN VALUENUM >= 6.0 AND VALUENUM < 12.0 THEN 3
                WHEN VALUENUM >= 12.0 THEN 4
                ELSE NULL
            END
        WHEN SOFA_COMPONENT = 'coag_platelets' THEN
            CASE
                WHEN VALUENUM >= 150 THEN 0
                WHEN VALUENUM < 150 AND VALUENUM >= 100 THEN 1
                WHEN VALUENUM < 100 AND VALUENUM >= 50 THEN 2
                WHEN VALUENUM < 50 AND VALUENUM >= 20 THEN 3
                WHEN VALUENUM < 20 THEN 4
                ELSE NULL
            END
        WHEN SOFA_COMPONENT = 'resp_pao2' THEN
            CASE
                WHEN VALUENUM >= 400 THEN 0
                WHEN VALUENUM < 400 AND VALUENUM >= 300 THEN 1
                WHEN VALUENUM < 300 AND VALUENUM >= 200 THEN 2
                WHEN VALUENUM < 200 AND VALUENUM >= 100 THEN 3
                WHEN VALUENUM < 100 THEN 4
                ELSE NULL
            END
        ELSE NULL
    END AS SOFA_SCORE
FROM SILVER.LABEVENTS_SOFA_CLEAN
WHERE VALUENUM IS NOT NULL;
