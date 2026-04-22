// ==========================================
// SEPSIS-LOGICGRAPH: NEO4J BUILD SCRIPT
// ==========================================

// 1. Create Constraints and Indexes
CREATE CONSTRAINT FOR (p:Patient) REQUIRE p.subject_id IS UNIQUE;
CREATE CONSTRAINT FOR (i:ICUStay) REQUIRE i.stay_id IS UNIQUE;
CREATE INDEX FOR (i:ICUStay) ON (i.hadm_id);

// 2. Load ICU Cohort
LOAD CSV WITH HEADERS FROM 'file:///icu_cohort.csv' AS row
MERGE (p:Patient {subject_id: row.SUBJECT_ID})
ON CREATE SET p.gender = row.GENDER, p.age = toFloat(row.ANCHOR_AGE)
MERGE (i:ICUStay {stay_id: row.STAY_ID})
ON CREATE SET i.hadm_id = row.HADM_ID, 
              i.intime = localdatetime(replace(substring(row.INTIME, 0, 19), ' ', 'T')), 
              i.outtime = localdatetime(replace(substring(row.OUTTIME, 0, 19), ' ', 'T'))
MERGE (p)-[:ADMITTED_TO]->(i);

// 3. Load Infections
LOAD CSV WITH HEADERS FROM 'file:///infections.csv' AS row
MATCH (i:ICUStay {hadm_id: row.HADM_ID})
CREATE (d:InfectionDiagnosis {
    icd_code: row.ICD_CODE,
    title: row.DIAGNOSIS_TITLE
})
CREATE (i)-[:HAS_INFECTION]->(d);

// 4. Load Lab Events
LOAD CSV WITH HEADERS FROM 'file:///sofa_labs.csv' AS row
MATCH (i:ICUStay {stay_id: row.STAY_ID})
CREATE (l:LabEvent {
    charttime: localdatetime(replace(substring(row.CHARTTIME, 0, 19), ' ', 'T')),
    sofa_score: toInteger(row.SOFA_SCORE)
})
CREATE (i)-[:HAS_LAB_EVENT]->(l);
