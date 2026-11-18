# Automated FMCG POS Data Hygiene, AI SKU Coding & Anomaly Triage System

An end-to-end **Retail Point-of-Sale (POS) Data Operations Pipeline** built with **Advanced Excel (Power Query, XLOOKUP, Dynamic Arrays, Pivot Dashboards)** and **Python NLP/Fuzzy AI (`pandas`, `rapidfuzz`)** to replicate and automate the core daily workflows of a **Data Operations Analyst (DOA) at NielsenIQ (NIQ)**.

---

## Business Problem & Operational Impact
Retailers submit weekly POS transaction feeds with abbreviated product descriptions (`"AMUL BTR PAST 500G"`), missing or corrupted EAN/UPC barcodes, duplicate store submissions, unflagged negative returns, and scanner decimal-shift price errors (`10x` / `0.1x` Base MRP).

This pipeline automates deterministic data hygiene in Excel and routes complex exceptions through a confidence-scored Python AI triage layer before releasing validated data to client reporting cubes.

### Key Pipeline Metrics (Week 45 Multi-Retailer Run)
* **Raw POS Records Ingested:** `3,060` rows across 3 retail chains (*Reliance Smart*, *DMart*, *BigBasket*)
* **Deduplicated Validated Rows:** `3,000` (`60` duplicate store-week submissions removed via Power Query)
* **Exact Barcode (`EAN`) Mapping Yield:** `85.2%` (`2,556` rows)
* **AI Auto-Coded SKUs ($\ge 88\%$ Confidence):** `+9.3%` lift (`280` missing/corrupt barcode rows resolved automatically, bringing total SKU coding yield to **`94.5%`**)
* **Clean Client-Cube Ready SLA:** `87.7%` (`2,630` rows), with `370` anomaly rows (`₹81,65,508` held revenue exposure) isolated with automated AI root-cause audit notes

---

## System Architecture

```text
[Raw_POS_Feeds/*.csv] ──► [Excel Power Query ETL] ──► [Excel Quality Gate Engine]
                                                            │
      ┌─────────────────────────────────────────────────────┘
      ▼
[Python AI SKU Coding & Root-Cause Triage (ai_sku_triage.py)]
      │
      ├──► Confidence >= 88%  ──► AI_AUTO_APPROVED (Client Cube Ready)
      ├──► Confidence 70–87%  ──► ANALYST_REVIEW_QUEUE
      └──► Price/Unit Anomaly ──► AI_Root_Cause + Audit Note (NO_HOLD)
      │
      ▼
[DOA_Executive_Dashboard (KPI Cards, SLA & Category Revenue Pivot Charts)]