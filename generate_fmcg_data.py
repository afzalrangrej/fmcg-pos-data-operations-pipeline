import os
import random
import pandas as pd
import numpy as np

# Set seed for reproducibility
random.seed(42)
np.random.seed(42)

os.makedirs("Raw_POS_Feeds", exist_ok=True)

# 1. Create the Canonical NIQ Master Catalog
master_catalog = [
    {"NIQ_Item_Code": "NIQ-1001", "EAN_Barcode": "8901262010016", "Canonical_Brand": "Amul", "Category": "Dairy", "Sub_Category": "Butter", "Pack_Size_Value": 500, "Pack_Unit": "g", "Base_MRP": 285.0},
    {"NIQ_Item_Code": "NIQ-1002", "EAN_Barcode": "8901262010023", "Canonical_Brand": "Amul", "Category": "Dairy", "Sub_Category": "Milk", "Pack_Size_Value": 1000, "Pack_Unit": "ml", "Base_MRP": 68.0},
    {"NIQ_Item_Code": "NIQ-1003", "EAN_Barcode": "8901491101837", "Canonical_Brand": "Lay's", "Category": "Snacks", "Sub_Category": "Potato Chips", "Pack_Size_Value": 52, "Pack_Unit": "g", "Base_MRP": 20.0},
    {"NIQ_Item_Code": "NIQ-1004", "EAN_Barcode": "8901491101844", "Canonical_Brand": "Lay's", "Category": "Snacks", "Sub_Category": "Potato Chips", "Pack_Size_Value": 90, "Pack_Unit": "g", "Base_MRP": 50.0},
    {"NIQ_Item_Code": "NIQ-1005", "EAN_Barcode": "8901063092617", "Canonical_Brand": "Britannia", "Category": "Snacks", "Sub_Category": "Biscuits", "Pack_Size_Value": 200, "Pack_Unit": "g", "Base_MRP": 40.0},
    {"NIQ_Item_Code": "NIQ-1006", "EAN_Barcode": "8901063092624", "Canonical_Brand": "Britannia", "Category": "Snacks", "Sub_Category": "Biscuits", "Pack_Size_Value": 600, "Pack_Unit": "g", "Base_MRP": 110.0},
    {"NIQ_Item_Code": "NIQ-1007", "EAN_Barcode": "8901764012273", "Canonical_Brand": "Coca-Cola", "Category": "Beverages", "Sub_Category": "Carbonated Soft Drinks", "Pack_Size_Value": 750, "Pack_Unit": "ml", "Base_MRP": 45.0},
    {"NIQ_Item_Code": "NIQ-1008", "EAN_Barcode": "8901764012280", "Canonical_Brand": "Coca-Cola", "Category": "Beverages", "Sub_Category": "Carbonated Soft Drinks", "Pack_Size_Value": 2000, "Pack_Unit": "ml", "Base_MRP": 95.0},
    {"NIQ_Item_Code": "NIQ-1009", "EAN_Barcode": "8902080000227", "Canonical_Brand": "Pepsi", "Category": "Beverages", "Sub_Category": "Carbonated Soft Drinks", "Pack_Size_Value": 750, "Pack_Unit": "ml", "Base_MRP": 45.0},
    {"NIQ_Item_Code": "NIQ-1010", "EAN_Barcode": "8901058851458", "Canonical_Brand": "Maggi", "Category": "Packaged Food", "Sub_Category": "Instant Noodles", "Pack_Size_Value": 280, "Pack_Unit": "g", "Base_MRP": 56.0},
    {"NIQ_Item_Code": "NIQ-1011", "EAN_Barcode": "8901058851465", "Canonical_Brand": "Maggi", "Category": "Packaged Food", "Sub_Category": "Instant Noodles", "Pack_Size_Value": 560, "Pack_Unit": "g", "Base_MRP": 105.0},
    {"NIQ_Item_Code": "NIQ-1012", "EAN_Barcode": "8901725121112", "Canonical_Brand": "Aashirvaad", "Category": "Staples", "Sub_Category": "Atta", "Pack_Size_Value": 5000, "Pack_Unit": "g", "Base_MRP": 265.0},
    {"NIQ_Item_Code": "NIQ-1013", "EAN_Barcode": "8901725121129", "Canonical_Brand": "Aashirvaad", "Category": "Staples", "Sub_Category": "Atta", "Pack_Size_Value": 10000, "Pack_Unit": "g", "Base_MRP": 510.0},
    {"NIQ_Item_Code": "NIQ-1014", "EAN_Barcode": "8901030865213", "Canonical_Brand": "Brooke Bond Red Label", "Category": "Beverages", "Sub_Category": "Tea", "Pack_Size_Value": 500, "Pack_Unit": "g", "Base_MRP": 270.0},
    {"NIQ_Item_Code": "NIQ-1015", "EAN_Barcode": "8901207019821", "Canonical_Brand": "Tropicana", "Category": "Beverages", "Sub_Category": "Fruit Juice", "Pack_Size_Value": 1000, "Pack_Unit": "ml", "Base_MRP": 125.0},
]

df_master = pd.DataFrame(master_catalog)
df_master.to_csv("NIQ_Master_Catalog.csv", index=False)

# 2. Messy Retailer Description Templates (simulating real POS scanner strings)
messy_descriptions = {
    "NIQ-1001": ["AMUL BTR PAST 500G", "Amul Butter 0.5kg Carton", "AMUL PASTEURISED BTR 500 GM"],
    "NIQ-1002": ["AMUL TAAZA MILK 1L", "Amul Milk Pouch 1000ml", "AMUL MLK 1 LTR"],
    "NIQ-1003": ["LAYS CRM&ONN 52G", "Lays Magic Masala 52gm Pch", "LAYS POTATO CHIPS 52 G"],
    "NIQ-1004": ["LAYS FAMILY PACK 90G", "Lays Classic Salted 90 gm", "LAYS CHIPS 90G"],
    "NIQ-1005": ["BRIT GOOD DAY 200G", "Britannia GoodDay Cashew 200gm", "BRITANNIA BISC 200 G"],
    "NIQ-1006": ["BRIT GOOD DAY MEGA 600G", "Britannia Biscuits 0.6kg", "BRIT GD 600GM"],
    "NIQ-1007": ["COKE PET 750ML", "Coca Cola Soft Drink 0.75L", "COCA-COLA 750 ML BTL"],
    "NIQ-1008": ["COKE JUMBO 2L", "Coca Cola 2000ml PET", "COCA COLA 2 LTR"],
    "NIQ-1009": ["PEPSI PET 750ML", "Pepsi Black/Reg 0.75L", "PEPSI SOFT DRK 750 ML"],
    "NIQ-1010": ["MAGGI 2MIN NOODLES 280G", "Maggi Masala 4-Pack 280gm", "MAGGI NDL 280 G"],
    "NIQ-1011": ["MAGGI 8-PACK 560G", "Maggi Masala Noodles 0.56kg", "MAGGI NDL 560GM"],
    "NIQ-1012": ["AASHIRVAAD ATTA 5KG", "Aashirvaad Shudh Chakki 5000g", "ASHIRWAD WHEAT FLR 5 KG"],
    "NIQ-1013": ["AASHIRVAAD ATTA 10KG", "Aashirvaad Whole Wheat 10000gm", "ASHIRWAD ATTA 10 KG"],
    "NIQ-1014": ["RED LABEL TEA 500G", "Brooke Bond Red Label 0.5kg", "BB RED LBL TEA 500GM"],
    "NIQ-1015": ["TROPICANA MIXED FRUIT 1L", "Tropicana Juice 1000ml Tetra", "TROPICANA 1 LTR"],
}

retailers = [
    {"name": "Reliance_Smart", "prefix": "REL-GJ-", "stores": 12, "rows": 1100},
    {"name": "DMart", "prefix": "DMT-GJ-", "stores": 10, "rows": 1000},
    {"name": "BigBasket", "prefix": "BBK-GJ-", "stores": 8, "rows": 900},
]

for retailer in retailers:
    records = []
    for i in range(retailer["rows"]):
        item = random.choice(master_catalog)
        store_id = f"{retailer['prefix']}{random.randint(1, retailer['stores']):02d}"
        raw_desc = random.choice(messy_descriptions[item["NIQ_Item_Code"]])
        
        # Add messy whitespace/casing occasionally
        if random.random() < 0.25:
            raw_desc = f"  {raw_desc.lower()}  "
            
        units_sold = random.randint(5, 180)
        promo_flag = "Y" if random.random() < 0.18 else "N"
        
        # Normal slight retail price variance (-8% to +2%)
        unit_price = round(item["Base_MRP"] * random.uniform(0.92, 1.02), 2)
        if promo_flag == "Y":
            unit_price = round(item["Base_MRP"] * random.uniform(0.80, 0.88), 2)
            
        barcode = item["EAN_Barcode"]
        defect_roll = random.random()
        
        # Inject DOA Data Quality Defects:
        if defect_roll < 0.15:
            # 15%: Missing or corrupted barcode (forces AI/Fuzzy SKU matching)
            barcode = "" if random.random() < 0.6 else f"999{random.randint(1000000000, 9999999999)}"
        elif defect_roll < 0.19:
            # 4%: Decimal shift / scanner price anomaly
            unit_price = round(unit_price * (10 if random.random() < 0.5 else 0.1), 2)
        elif defect_roll < 0.22:
            # 3%: Unflagged negative units (returns not separated)
            units_sold = -random.randint(1, 15)
            promo_flag = "N"
            
        gross_revenue = round(units_sold * unit_price, 2)
        
        records.append({
            "Retailer": retailer["name"],
            "Store_ID": store_id,
            "Week_Ending": "2026-11-08",
            "Retailer_SKU_Desc": raw_desc,
            "Barcode_EAN": barcode,
            "Units_Sold": units_sold,
            "Gross_Revenue_INR": gross_revenue,
            "Promo_Flag": promo_flag
        })
        
    df_feed = pd.DataFrame(records)
    
    # Inject 2% duplicate store submissions
    dupes = df_feed.sample(frac=0.02, random_state=42)
    df_feed = pd.concat([df_feed, dupes], ignore_index=True)
    
    file_path = f"Raw_POS_Feeds/{retailer['name']}_W45.csv"
    df_feed.to_csv(file_path, index=False)
    print(f"Created {file_path} ({len(df_feed)} rows)")

print("Done! NIQ_Master_Catalog.csv and 3 Raw POS Feeds are ready.")