# Transformation Layer

This folder contains the Snowflake SQL for the Sepsis-LogicGraph transformation phase.

## Objective
Transform Bronze-layer raw MIMIC-IV tables into:
- Silver: cleaned, standardized, analysis-ready models
- Gold: SOFA, infection, and sepsis analytical models

## Source Bronze Tables
- PATIENTS
- ADMISSIONS
- ICUSTAYS
- DIAGNOSES_ICD
- D_ICD_DIAGNOSES
- LABEVENTS
- D_LABITEMS
- D_ITEMS

## Current Scope
Initial budget-safe implementation focuses on:
- cohort preparation
- diagnosis-based infection proxy
- partial SOFA using lab-based components:
  - creatinine
  - bilirubin
  - platelets
  - PaO2 if available

## Notes
This implementation is designed to minimize Snowflake credit usage by:
- using X-SMALL warehouse
- filtering LABEVENTS early
- testing on small cohorts first