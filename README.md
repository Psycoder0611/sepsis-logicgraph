# Sepsis-LogicGraph
A Real-Time Clinical Alerting Pipeline with Graph-Native Temporal Logic  
and Multi-Tool Performance Benchmark

**Course:** DATA 226: Data Warehouses and Pipelines | SJSU  
**Instructor:** Dr. Vishnu Pendyala  
**Group 5**

---

## What This Project Does
Sepsis kills 11 million people per year. This pipeline detects sepsis 
in ICU patients in real time using the official Sepsis-3 clinical rule, 
then benchmarks Neo4j (graph database) against Snowflake SQL to find 
the better approach for time-window medical logic.

---

## Team
| Member | Role |
|---|---|
| Trapti Kulshrestha | Ingestion Lead |
| Karthik Pragada | Transformation Lead |
| Poushali Deb Purkayastha | Graph & Benchmark Lead |
| Akanksha Shukla | Orchestration & Delivery Lead — Dagster pipeline, Preset.io, Slack |

---

## Tech Stack
- **Ingestion:** Coupler.io
- **Storage:** Snowflake (Bronze / Silver / Gold)
- **Transformation:** dbt
- **Graph DB:** Neo4j + Cypher
- **Orchestration:** Dagster Pipeline
- **Monitoring:** Slack Alerts, Preset.io Dashboard
- **Data:** MIMIC-IV v3.1 (PhysioNet)

---

## Folder Structure
