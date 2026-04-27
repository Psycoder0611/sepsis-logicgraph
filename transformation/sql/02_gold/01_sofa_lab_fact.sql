CREATE OR REPLACE TABLE GOLD.FACT_SOFA_LAB AS
WITH base AS (
    SELECT
        s.LABEVENT_ID,
        s.SUBJECT_ID,
        s.HADM_ID,
        s.ITEMID,
        s.SOFA_COMPONENT,
        s.CHARTTIME,
        s.VALUENUM,
        s.VALUEUOM,
        s.FLAG,
        CASE
            WHEN s.SOFA_COMPONENT = 'renal_creatinine' THEN
                CASE
                    WHEN s.VALUENUM < 1.2 THEN 0
                    WHEN s.VALUENUM >= 1.2 AND s.VALUENUM < 2.0 THEN 1
                    WHEN s.VALUENUM >= 2.0 AND s.VALUENUM < 3.5 THEN 2
                    WHEN s.VALUENUM >= 3.5 AND s.VALUENUM < 5.0 THEN 3
                    WHEN s.VALUENUM >= 5.0 THEN 4
                    ELSE NULL
                END
            WHEN s.SOFA_COMPONENT = 'liver_bilirubin' THEN
                CASE
                    WHEN s.VALUENUM < 1.2 THEN 0
                    WHEN s.VALUENUM >= 1.2 AND s.VALUENUM < 2.0 THEN 1
                    WHEN s.VALUENUM >= 2.0 AND s.VALUENUM < 6.0 THEN 2
                    WHEN s.VALUENUM >= 6.0 AND s.VALUENUM < 12.0 THEN 3
                    WHEN s.VALUENUM >= 12.0 THEN 4
                    ELSE NULL
                END
            WHEN s.SOFA_COMPONENT = 'coag_platelets' THEN
                CASE
                    WHEN s.VALUENUM >= 150 THEN 0
                    WHEN s.VALUENUM < 150 AND s.VALUENUM >= 100 THEN 1
                    WHEN s.VALUENUM < 100 AND s.VALUENUM >= 50 THEN 2
                    WHEN s.VALUENUM < 50 AND s.VALUENUM >= 20 THEN 3
                    WHEN s.VALUENUM < 20 THEN 4
                    ELSE NULL
                END
            WHEN s.SOFA_COMPONENT = 'resp_pao2' THEN
                CASE
                    WHEN s.VALUENUM >= 400 THEN 0
                    WHEN s.VALUENUM < 400 AND s.VALUENUM >= 300 THEN 1
                    WHEN s.VALUENUM < 300 AND s.VALUENUM >= 200 THEN 2
                    WHEN s.VALUENUM < 200 AND s.VALUENUM >= 100 THEN 3
                    WHEN s.VALUENUM < 100 THEN 4
                    ELSE NULL
                END
            ELSE NULL
        END AS SOFA_SCORE
    FROM SILVER.LABEVENTS_SOFA_CLEAN s
    WHERE s.LABEVENT_ID IS NOT NULL
      AND s.VALUENUM IS NOT NULL
),
stay_match AS (
    SELECT
        b.LABEVENT_ID,
        ds.STAY_SK,
        ROW_NUMBER() OVER (
            PARTITION BY b.LABEVENT_ID
            ORDER BY ABS(DATEDIFF('minute', ds.INTIME, b.CHARTTIME))
        ) AS RN
    FROM base b
    LEFT JOIN GOLD.DIM_STAY ds
      ON b.SUBJECT_ID = ds.SUBJECT_ID
     AND b.HADM_ID = ds.HADM_ID
)
SELECT
    SHA2(TO_VARCHAR(b.LABEVENT_ID), 256) AS FACT_SOFA_LAB_SK,
    dp.PATIENT_SK,
    da.ADMISSION_SK,
    sm.STAY_SK,
    dlc.LAB_COMPONENT_SK,
    b.LABEVENT_ID,
    b.SUBJECT_ID,
    b.HADM_ID,
    b.ITEMID,
    b.SOFA_COMPONENT,
    b.CHARTTIME,
    b.VALUENUM,
    b.SOFA_SCORE,
    b.VALUEUOM,
    b.FLAG,
    CURRENT_TIMESTAMP() AS CREATED_AT,
    CURRENT_TIMESTAMP() AS UPDATED_AT
FROM base b
LEFT JOIN GOLD.DIM_PATIENT dp
  ON b.SUBJECT_ID = dp.SUBJECT_ID
LEFT JOIN GOLD.DIM_ADMISSION da
  ON b.HADM_ID = da.HADM_ID
LEFT JOIN (
    SELECT LABEVENT_ID, STAY_SK
    FROM stay_match
    WHERE RN = 1
) sm
  ON b.LABEVENT_ID = sm.LABEVENT_ID
LEFT JOIN GOLD.DIM_LAB_COMPONENT dlc
  ON b.ITEMID = dlc.ITEMID
 AND b.SOFA_COMPONENT = dlc.SOFA_COMPONENT;
