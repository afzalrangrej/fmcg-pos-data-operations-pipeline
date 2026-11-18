import re
import pandas as pd
from rapidfuzz import fuzz

WORKBOOK_PATH = "POS_Operations_Staging.xlsx"

# 1. Domain Abbreviation Dictionary (Retail POS NLP Normalization)
ABBREVIATION_MAP = {
    r"\bBTR\b": "BUTTER",
    r"\bPAST\b": "PASTEURISED",
    r"\bMLK\b": "MILK",
    r"\bCRM&ONN\b": "CREAM AND ONION",
    r"\bPCH\b": "POUCH",
    r"\bBRIT\b": "BRITANNIA",
    r"\bBISC\b": "BISCUITS",
    r"\bGD\b": "GOOD DAY",
    r"\bCOKE\b": "COCA-COLA",
    r"\bCOCA COLA\b": "COCA-COLA",
    r"\bDRK\b": "DRINK",
    r"\bBTL\b": "BOTTLE",
    r"\bNDL\b": "NOODLES",
    r"\bASHIRWAD\b": "AASHIRVAAD",
    r"\bFLR\b": "ATTA",
    r"\bBB\b": "BROOKE BOND",
    r"\bLBL\b": "LABEL",
}

def extract_normalized_pack(text: str):
    """Extracts pack size and normalizes kg->g and L/ltr->ml."""
    text_clean = text.upper()
    match = re.search(r"(\d+(?:\.\d+)?)\s*(KG|G|GM|GMS|ML|L|LTR)\b", text_clean)
    if not match:
        return None, None
    val = float(match.group(1))
    unit = match.group(2)
    if unit == "KG":
        return int(round(val * 1000)), "g"
    elif unit in ("G", "GM", "GMS"):
        return int(round(val)), "g"
    elif unit in ("L", "LTR"):
        return int(round(val * 1000)), "ml"
    elif unit == "ML":
        return int(round(val)), "ml"
    return None, None

def normalize_sku_text(text: str) -> str:
    """Expands retail abbreviations and removes pack size tokens for clean semantic matching."""
    s = str(text).upper().strip()
    for pattern, replacement in ABBREVIATION_MAP.items():
        s = re.sub(pattern, replacement, s)
    s = re.sub(r"\d+(?:\.\d+)?\s*(KG|G|GM|GMS|ML|L|LTR)\b", "", s)
    s = re.sub(r"[^A-Z0-9\s\-]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def classify_sku_ai(raw_desc: str, catalog_df: pd.DataFrame):
    """Hybrid NLP + Unit-Constrained Fuzzy AI Matcher with Confidence Score."""
    pack_val, pack_unit = extract_normalized_pack(raw_desc)
    clean_desc = normalize_sku_text(raw_desc)

    # Filter catalog by exact normalized pack size if detected (prevents 500g matching 1000g)
    candidates = catalog_df
    if pack_val is not None and pack_unit is not None:
        unit_matches = catalog_df[
            (catalog_df["Pack_Size_Value"] == pack_val) &
            (catalog_df["Pack_Unit"] == pack_unit)
        ]
        if not unit_matches.empty:
            candidates = unit_matches

    best_score = -1.0
    best_row = None

    for _, row in candidates.iterrows():
        target_text = f"{row['Canonical_Brand']} {row['Sub_Category']} {row['Category']}".upper()
        # Combine token_set_ratio and partial_ratio for robust brand+product matching
        score_set = fuzz.token_set_ratio(clean_desc, target_text)
        score_part = fuzz.partial_ratio(clean_desc, target_text)
        hybrid_score = round((0.65 * score_set) + (0.35 * score_part), 1)

        # Boost confidence when normalized pack size & unit match exactly
        if pack_val == row["Pack_Size_Value"] and pack_unit == row["Pack_Unit"]:
            hybrid_score = min(99.5, round(hybrid_score + 12.0, 1))

        if hybrid_score > best_score:
            best_score = hybrid_score
            best_row = row

    if best_row is None:
        return "UNRESOLVED", "UNKNOWN", 0.0, "NEW_ITEM_SETUP_REQUIRED"

    if best_score >= 88.0:
        decision = "AI_AUTO_APPROVED"
    elif best_score >= 70.0:
        decision = "ANALYST_REVIEW_QUEUE"
    else:
        decision = "NEW_ITEM_SETUP_REQUIRED"

    return best_row["NIQ_Item_Code"], best_row["Canonical_Brand"], best_score, decision

def diagnose_anomaly_ai(row, catalog_lookup: dict):
    """Generates AI Root-Cause Triage tags and operational audit notes."""
    status = row["DOA_Quality_Status"]
    units = row["Units_Sold"]
    var_pct = row["Price_Variance_Pct"]
    ai_code = row["Final_NIQ_Code"]

    # Re-evaluate price variance if AI just mapped a previously unmapped item
    base_mrp = catalog_lookup.get(ai_code, 0)
    realized_price = row["Realized_Unit_Price"]
    if base_mrp > 0:
        var_pct = round((realized_price - base_mrp) / base_mrp, 4)

    if units < 0:
        return (
            "UNFLAGGED_CUSTOMER_RETURN",
            f"Negative volume ({units} units) submitted as regular sale; reclassify to Returns bucket."
        )
    if base_mrp > 0 and var_pct > 2.0:
        return (
            "SCANNER_DECIMAL_SHIFT_10X",
            f"Unit price ₹{realized_price} is ~10x Base MRP (₹{base_mrp}); likely POS decimal entry error."
        )
    if base_mrp > 0 and var_pct < -0.50:
        return (
            "SCANNER_DECIMAL_SHIFT_0.1X",
            f"Unit price ₹{realized_price} is ~90% below Base MRP (₹{base_mrp}); verify scanner/multipack defect."
        )
    if status == "ERR_UNMAPPED_SKU" and row["AI_Triage_Decision"] == "AI_AUTO_APPROVED":
        return (
            "MISSING_EAN_RESOLVED_BY_AI",
            f"Barcode missing/corrupt; AI mapped description to {ai_code} at {row['AI_Confidence_Pct']}% confidence."
        )
    if status == "ERR_UNMAPPED_SKU":
        return (
            "LOW_CONFIDENCE_SKU_HOLD",
            f"Barcode missing and AI confidence ({row['AI_Confidence_Pct']}%) below 88% auto-approval threshold."
        )
    return ("CLEAN_VALIDATED", "Passed deterministic & AI quality gates.")

def main():
    print("Loading NIQ_POS_Operations_Engine.xlsx...")
    df_catalog = pd.read_excel(WORKBOOK_PATH, sheet_name="NIQ_Master_Catalog", dtype={"EAN_Barcode": str})
    df_pos = pd.read_excel(WORKBOOK_PATH, sheet_name="POS_Operations_Staging", dtype={"Barcode_EAN": str})

    catalog_mrp_map = dict(zip(df_catalog["NIQ_Item_Code"], df_catalog["Base_MRP"]))
    catalog_cat_map = dict(zip(df_catalog["NIQ_Item_Code"], df_catalog["Category"]))

    final_codes = []
    final_brands = []
    ai_confidences = []
    ai_decisions = []

    print("Running AI SKU Attribute Extraction & Confidence Scoring...")
    for _, row in df_pos.iterrows():
        if row["Mapped_NIQ_Code"] != "UNMAPPED":
            final_codes.append(row["Mapped_NIQ_Code"])
            final_brands.append(row["Canonical_Brand"])
            ai_confidences.append(100.0)
            ai_decisions.append("EXACT_EAN_MATCH")
        else:
            code, brand, conf, decision = classify_sku_ai(row["Retailer_SKU_Desc"], df_catalog)
            final_codes.append(code)
            final_brands.append(brand)
            ai_confidences.append(conf)
            ai_decisions.append(decision)

    df_pos["Final_NIQ_Code"] = final_codes
    df_pos["Final_Brand"] = final_brands
    df_pos["Final_Category"] = df_pos["Final_NIQ_Code"].map(catalog_cat_map).fillna("Unclassified")
    df_pos["AI_Confidence_Pct"] = ai_confidences
    df_pos["AI_Triage_Decision"] = ai_decisions

    print("Running AI Anomaly Root-Cause Triage...")
    root_causes = []
    audit_notes = []
    for _, row in df_pos.iterrows():
        cause, note = diagnose_anomaly_ai(row, catalog_mrp_map)
        root_causes.append(cause)
        audit_notes.append(note)

    df_pos["AI_Root_Cause"] = root_causes
    df_pos["AI_Audit_Note"] = audit_notes

    # Mark final client-delivery readiness
    df_pos["Client_Cube_Ready"] = df_pos.apply(
        lambda r: "YES" if (r["AI_Triage_Decision"] in ("EXACT_EAN_MATCH", "AI_AUTO_APPROVED")
                            and r["AI_Root_Cause"] in ("CLEAN_VALIDATED", "MISSING_EAN_RESOLVED_BY_AI"))
        else "NO_HOLD",
        axis=1
    )

    # Save back to Excel as a new tab without overwriting existing sheets
    with pd.ExcelWriter(WORKBOOK_PATH, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        df_pos.to_excel(writer, sheet_name="AI_Resolved_Master_Feed", index=False)

    # Print DOA Operational Summary
    total = len(df_pos)
    exact = (df_pos["AI_Triage_Decision"] == "EXACT_EAN_MATCH").sum()
    ai_approved = (df_pos["AI_Triage_Decision"] == "AI_AUTO_APPROVED").sum()
    ready = (df_pos["Client_Cube_Ready"] == "YES").sum()

    print("\n--- NIQ DOA AI TRIAGE SUMMARY ---")
    print(f"Total Deduplicated POS Rows : {total}")
    print(f"Exact Barcode Matches       : {exact} ({exact/total:.1%})")
    print(f"AI Auto-Coded SKUs (>=88%)  : {ai_approved} ({ai_approved/total:.1%})")
    print(f"Total Clean Client-Ready    : {ready} ({ready/total:.1%})")
    print("Saved 'AI_Resolved_Master_Feed' tab into NIQ_POS_Operations_Engine.xlsx!")

if __name__ == "__main__":
    main()