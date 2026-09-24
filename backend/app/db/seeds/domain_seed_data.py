"""
Domain Seed Data Catalog
========================
Curated seed entities and relationships for the 4 MVP sectors, 8 commodities,
4 macro factors, and 36 core Indian equities matching /docs/schema.md.

All graph relationships are tagged strictly with source: "manual_seed".
"""

from typing import Any, Dict, List

# 1. MVP Sectors
SECTORS_SEED: List[Dict[str, Any]] = [
    {
        "sector_id": "SEC_AUTO",
        "name": "Automotive & Components",
        "description": "Passenger vehicles, commercial vehicles, tractors, two-wheelers, and auto ancillaries.",
    },
    {
        "sector_id": "SEC_STEEL",
        "name": "Steel & Metals Mining",
        "description": "Integrated flat and long steel manufacturing, non-ferrous metals, and mining inputs.",
    },
    {
        "sector_id": "SEC_ENERGY",
        "name": "Energy, Oil & Gas",
        "description": "Upstream exploration, oil refining, petrochemicals, and natural gas distribution.",
    },
    {
        "sector_id": "SEC_IT",
        "name": "Information Technology Services",
        "description": "Global enterprise software services, digital transformation, and consulting.",
    },
]

# 2. MVP Commodities
COMMODITIES_SEED: List[Dict[str, Any]] = [
    {
        "commodity_id": "COMM_BRENT_CRUDE",
        "name": "Brent Crude Oil",
        "unit": "USD/Barrel",
        "fred_series_id": "DCOILBRENTEU",
        "yf_symbol": "CL=F",
    },
    {
        "commodity_id": "COMM_NATURAL_GAS",
        "name": "Natural Gas",
        "unit": "USD/MMBtu",
        "fred_series_id": "DHHNGSP",
        "yf_symbol": "NG=F",
    },
    {
        "commodity_id": "COMM_COKING_COAL",
        "name": "Metallurgical Coking Coal",
        "unit": "USD/MT",
        "fred_series_id": "PCOALAUUSDM",
        "yf_symbol": None,
    },
    {
        "commodity_id": "COMM_IRON_ORE",
        "name": "Iron Ore 62% Fe Fines",
        "unit": "USD/dmt",
        "fred_series_id": "PIORECRUSDM",
        "yf_symbol": "TIO=F",
    },
    {
        "commodity_id": "COMM_HRC_STEEL",
        "name": "Hot Rolled Steel Coil (Domestic)",
        "unit": "INR/MT",
        "fred_series_id": "WPU101704",
        "yf_symbol": "HRC=F",
    },
    {
        "commodity_id": "COMM_ALUMINUM",
        "name": "Primary Aluminum",
        "unit": "USD/MT",
        "fred_series_id": "PALUMUSDM",
        "yf_symbol": "ALI=F",
    },
    {
        "commodity_id": "COMM_COPPER",
        "name": "Grade A Copper Cathode",
        "unit": "USD/MT",
        "fred_series_id": "PCOPPUSDM",
        "yf_symbol": "HG=F",
    },
    {
        "commodity_id": "COMM_CHIP_SEMI",
        "name": "Automotive Microcontrollers & Semiconductor Chips",
        "unit": "Index",
        "fred_series_id": "PCU334413334413",
        "yf_symbol": "^SOX",
    },
]

# 3. Macro Factors
MACRO_FACTORS_SEED: List[Dict[str, Any]] = [
    {
        "factor_id": "MACRO_RBI_REPO",
        "name": "RBI Monetary Policy Repo Rate",
        "unit": "Percent",
        "fred_series_id": "INTDSRINM193N",
    },
    {
        "factor_id": "MACRO_USD_INR",
        "name": "USD to INR Exchange Rate",
        "unit": "INR/USD",
        "fred_series_id": "DEXINUS",
    },
    {
        "factor_id": "MACRO_INDIA_CPI",
        "name": "India Consumer Price Index (Headline)",
        "unit": "Index",
        "fred_series_id": "INDCPIALLMINMEI",
    },
    {
        "factor_id": "MACRO_US_10Y_YIELD",
        "name": "US 10-Year Treasury Constant Maturity Yield",
        "unit": "Percent",
        "fred_series_id": "DGS10",
    },
]

# 4. Target Companies (36 Core Liquid Indian Equities)
COMPANIES_SEED: List[Dict[str, Any]] = [
    # Automotive Sector (9)
    {"ticker": "TATAMOTORS.NS", "name": "Tata Motors Limited", "sector_id": "SEC_AUTO", "isin": "INE155A01022", "market_cap_category": "LARGE_CAP", "summary": "Commercial and passenger vehicles manufacturer with global JLR subsidiary."},
    {"ticker": "MARUTI.NS", "name": "Maruti Suzuki India Limited", "sector_id": "SEC_AUTO", "isin": "INE585B01010", "market_cap_category": "LARGE_CAP", "summary": "India's largest passenger vehicle OEM."},
    {"ticker": "M&M.NS", "name": "Mahindra & Mahindra Limited", "sector_id": "SEC_AUTO", "isin": "INE101A01026", "market_cap_category": "LARGE_CAP", "summary": "SUVs, commercial vehicles, and agricultural farm equipment OEM."},
    {"ticker": "BAJAJ-AUTO.NS", "name": "Bajaj Auto Limited", "sector_id": "SEC_AUTO", "isin": "INE917I01012", "market_cap_category": "LARGE_CAP", "summary": "Two-wheeler and three-wheeler manufacturer with major export footprint."},
    {"ticker": "BHARATFORG.NS", "name": "Bharat Forge Limited", "sector_id": "SEC_AUTO", "isin": "INE465A01025", "market_cap_category": "LARGE_CAP", "summary": "Leading global forging company supplying chassis and powertrain components."},
    {"ticker": "MOTHERSON.NS", "name": "Samvardhana Motherson International Ltd", "sector_id": "SEC_AUTO", "isin": "INE775A01035", "market_cap_category": "LARGE_CAP", "summary": "Global automotive wiring harness and rearview vision systems supplier."},
    {"ticker": "BOSCHLTD.NS", "name": "Bosch Limited", "sector_id": "SEC_AUTO", "isin": "INE323A01026", "market_cap_category": "LARGE_CAP", "summary": "Automotive electronics, fuel injection systems, and mobility solutions."},
    {"ticker": "APOLLOTYRE.NS", "name": "Apollo Tyres Limited", "sector_id": "SEC_AUTO", "isin": "INE438A01022", "market_cap_category": "MID_CAP", "summary": "Automotive tire manufacturer with strong commercial vehicle exposure."},
    {"ticker": "MRF.NS", "name": "MRF Limited", "sector_id": "SEC_AUTO", "isin": "INE883A01011", "market_cap_category": "LARGE_CAP", "summary": "Premium automotive and aviation tire manufacturing."},

    # Steel & Metals Sector (8)
    {"ticker": "TATASTEEL.NS", "name": "Tata Steel Limited", "sector_id": "SEC_STEEL", "isin": "INE081A01020", "market_cap_category": "LARGE_CAP", "summary": "Major integrated steel producer with domestic blast furnaces and European operations."},
    {"ticker": "JSWSTEEL.NS", "name": "JSW Steel Limited", "sector_id": "SEC_STEEL", "isin": "INE019A01038", "market_cap_category": "LARGE_CAP", "summary": "Leading Indian manufacturer of flat and long steel products."},
    {"ticker": "JINDALSTEL.NS", "name": "Jindal Steel & Power Limited", "sector_id": "SEC_STEEL", "isin": "INE749A01030", "market_cap_category": "LARGE_CAP", "summary": "Integrated steel, power, and infrastructure solutions producer."},
    {"ticker": "SAIL.NS", "name": "Steel Authority of India Limited", "sector_id": "SEC_STEEL", "isin": "INE114A01011", "market_cap_category": "LARGE_CAP", "summary": "State-owned steelmaking enterprise with captive iron ore mines."},
    {"ticker": "HINDALCO.NS", "name": "Hindalco Industries Limited", "sector_id": "SEC_STEEL", "isin": "INE038A01020", "market_cap_category": "LARGE_CAP", "summary": "Global aluminum and copper producer with Novelis downstream operations."},
    {"ticker": "VEDL.NS", "name": "Vedanta Limited", "sector_id": "SEC_STEEL", "isin": "INE205A01025", "market_cap_category": "LARGE_CAP", "summary": "Diversified natural resources major spanning zinc, aluminum, oil, and iron ore."},
    {"ticker": "NMDC.NS", "name": "NMDC Limited", "sector_id": "SEC_STEEL", "isin": "INE584A01023", "market_cap_category": "LARGE_CAP", "summary": "India's largest merchant iron ore mining corporation."},
    {"ticker": "NATIONALUM.NS", "name": "National Aluminium Company Limited", "sector_id": "SEC_STEEL", "isin": "INE139A01034", "market_cap_category": "MID_CAP", "summary": "Integrated bauxite mining, alumina refining, and aluminum smelting."},

    # Energy & Oil/Gas Sector (8)
    {"ticker": "RELIANCE.NS", "name": "Reliance Industries Limited", "sector_id": "SEC_ENERGY", "isin": "INE002A01018", "market_cap_category": "LARGE_CAP", "summary": "Conglomerate operating Jamnagar complex refining, petrochemicals, and retail."},
    {"ticker": "ONGC.NS", "name": "Oil and Natural Gas Corporation Limited", "sector_id": "SEC_ENERGY", "isin": "INE213A01029", "market_cap_category": "LARGE_CAP", "summary": "India's primary upstream crude oil and natural gas exploration company."},
    {"ticker": "IOC.NS", "name": "Indian Oil Corporation Limited", "sector_id": "SEC_ENERGY", "isin": "INE242A01010", "market_cap_category": "LARGE_CAP", "summary": "State-owned oil refining and downstream petroleum marketing leader."},
    {"ticker": "BPCL.NS", "name": "Bharat Petroleum Corporation Limited", "sector_id": "SEC_ENERGY", "isin": "INE029A01011", "market_cap_category": "LARGE_CAP", "summary": "Downstream oil refining, aviation fuel, and retail fuel stations."},
    {"ticker": "GAIL.NS", "name": "GAIL (India) Limited", "sector_id": "SEC_ENERGY", "isin": "INE129A01019", "market_cap_category": "LARGE_CAP", "summary": "Natural gas transmission, processing, petrochemicals, and city gas."},
    {"ticker": "OIL.NS", "name": "Oil India Limited", "sector_id": "SEC_ENERGY", "isin": "INE274J01014", "market_cap_category": "MID_CAP", "summary": "Upstream crude exploration and production focused on North-East India."},
    {"ticker": "PETRONET.NS", "name": "Petronet LNG Limited", "sector_id": "SEC_ENERGY", "isin": "INE348B01021", "market_cap_category": "LARGE_CAP", "summary": "Liquefied natural gas regasification terminal operator at Dahej and Kochi."},
    {"ticker": "GUJGASLTD.NS", "name": "Gujarat Gas Limited", "sector_id": "SEC_ENERGY", "isin": "INE844O01030", "market_cap_category": "MID_CAP", "summary": "City gas distribution network serving industrial ceramics and households."},

    # IT Services Sector (11)
    {"ticker": "TCS.NS", "name": "Tata Consultancy Services Limited", "sector_id": "SEC_IT", "isin": "INE467B01029", "market_cap_category": "LARGE_CAP", "summary": "Global digital transformation, cloud integration, and enterprise consulting."},
    {"ticker": "INFY.NS", "name": "Infosys Limited", "sector_id": "SEC_IT", "isin": "INE009A01021", "market_cap_category": "LARGE_CAP", "summary": "Next-generation digital services, software development, and cloud services."},
    {"ticker": "WIPRO.NS", "name": "Wipro Limited", "sector_id": "SEC_IT", "isin": "INE075A01022", "market_cap_category": "LARGE_CAP", "summary": "Technology consulting, cyber security, and digital engineering services."},
    {"ticker": "HCLTECH.NS", "name": "HCL Technologies Limited", "sector_id": "SEC_IT", "isin": "INE860A01027", "market_cap_category": "LARGE_CAP", "summary": "Engineering and R&D services, digital enterprise software, and infrastructure."},
    {"ticker": "TECHM.NS", "name": "Tech Mahindra Limited", "sector_id": "SEC_IT", "isin": "INE669C01036", "market_cap_category": "LARGE_CAP", "summary": "Telecom networking software solutions and digital enterprise services."},
    {"ticker": "LTIM.NS", "name": "LTIMindtree Limited", "sector_id": "SEC_IT", "isin": "INE214T01019", "market_cap_category": "LARGE_CAP", "summary": "Enterprise cloud migrations, banking technology, and analytics."},
    {"ticker": "PERSISTENT.NS", "name": "Persistent Systems Limited", "sector_id": "SEC_IT", "isin": "INE262H01013", "market_cap_category": "MID_CAP", "summary": "Digital product engineering and enterprise software modernization."},
    {"ticker": "COFORGE.NS", "name": "Coforge Limited", "sector_id": "SEC_IT", "isin": "INE591G01017", "market_cap_category": "MID_CAP", "summary": "Domain-focused IT solutions for insurance, banking, and travel."},
    {"ticker": "MPHASIS.NS", "name": "Mphasis Limited", "sector_id": "SEC_IT", "isin": "INE356A01018", "market_cap_category": "MID_CAP", "summary": "Cloud and cognitive banking IT solutions."},
    {"ticker": "LTTS.NS", "name": "L&T Technology Services Limited", "sector_id": "SEC_IT", "isin": "INE010V01017", "market_cap_category": "MID_CAP", "summary": "Pure-play engineering R&D services spanning transportation and industrial products."},
    {"ticker": "KPITTECH.NS", "name": "KPIT Technologies Limited", "sector_id": "SEC_IT", "isin": "INE04I401011", "market_cap_category": "MID_CAP", "summary": "Automotive embedded software, autonomous driving, and EV powertrain tech."},
]

# 5. Curated Supply Chain & Dependency Edges (Graph Model)
GRAPH_EDGES_SEED: List[Dict[str, Any]] = [
    # --- SUPPLIES_TO (Company -> Company) ---
    {"source": "TATASTEEL.NS", "target": "TATAMOTORS.NS", "type": "SUPPLIES_TO", "strength": 0.70, "lead_time_days": 14, "source_tag": "manual_seed", "confidence": 0.95},
    {"source": "JSWSTEEL.NS", "target": "MARUTI.NS", "type": "SUPPLIES_TO", "strength": 0.75, "lead_time_days": 10, "source_tag": "manual_seed", "confidence": 0.95},
    {"source": "BHARATFORG.NS", "target": "TATAMOTORS.NS", "type": "SUPPLIES_TO", "strength": 0.65, "lead_time_days": 21, "source_tag": "manual_seed", "confidence": 0.90},
    {"source": "BHARATFORG.NS", "target": "M&M.NS", "type": "SUPPLIES_TO", "strength": 0.60, "lead_time_days": 21, "source_tag": "manual_seed", "confidence": 0.90},
    {"source": "MOTHERSON.NS", "target": "MARUTI.NS", "type": "SUPPLIES_TO", "strength": 0.80, "lead_time_days": 7, "source_tag": "manual_seed", "confidence": 0.95},
    {"source": "MOTHERSON.NS", "target": "TATAMOTORS.NS", "type": "SUPPLIES_TO", "strength": 0.65, "lead_time_days": 7, "source_tag": "manual_seed", "confidence": 0.92},
    {"source": "BOSCHLTD.NS", "target": "MARUTI.NS", "type": "SUPPLIES_TO", "strength": 0.75, "lead_time_days": 14, "source_tag": "manual_seed", "confidence": 0.92},
    {"source": "BOSCHLTD.NS", "target": "M&M.NS", "type": "SUPPLIES_TO", "strength": 0.70, "lead_time_days": 14, "source_tag": "manual_seed", "confidence": 0.92},
    {"source": "APOLLOTYRE.NS", "target": "TATAMOTORS.NS", "type": "SUPPLIES_TO", "strength": 0.55, "lead_time_days": 5, "source_tag": "manual_seed", "confidence": 0.88},
    {"source": "MRF.NS", "target": "MARUTI.NS", "type": "SUPPLIES_TO", "strength": 0.60, "lead_time_days": 5, "source_tag": "manual_seed", "confidence": 0.88},
    {"source": "NMDC.NS", "target": "TATASTEEL.NS", "type": "SUPPLIES_TO", "strength": 0.50, "lead_time_days": 10, "source_tag": "manual_seed", "confidence": 0.90},
    {"source": "NMDC.NS", "target": "JSWSTEEL.NS", "type": "SUPPLIES_TO", "strength": 0.80, "lead_time_days": 10, "source_tag": "manual_seed", "confidence": 0.95},
    {"source": "KPITTECH.NS", "target": "TATAMOTORS.NS", "type": "SUPPLIES_TO", "strength": 0.45, "lead_time_days": 30, "source_tag": "manual_seed", "confidence": 0.85},
    {"source": "LTTS.NS", "target": "M&M.NS", "type": "SUPPLIES_TO", "strength": 0.40, "lead_time_days": 30, "source_tag": "manual_seed", "confidence": 0.85},
    {"source": "PETRONET.NS", "target": "GAIL.NS", "type": "SUPPLIES_TO", "strength": 0.85, "lead_time_days": 2, "source_tag": "manual_seed", "confidence": 0.95},
    {"source": "GAIL.NS", "target": "GUJGASLTD.NS", "type": "SUPPLIES_TO", "strength": 0.75, "lead_time_days": 1, "source_tag": "manual_seed", "confidence": 0.92},
    {"source": "ONGC.NS", "target": "IOC.NS", "type": "SUPPLIES_TO", "strength": 0.75, "lead_time_days": 3, "source_tag": "manual_seed", "confidence": 0.95},
    {"source": "ONGC.NS", "target": "BPCL.NS", "type": "SUPPLIES_TO", "strength": 0.70, "lead_time_days": 3, "source_tag": "manual_seed", "confidence": 0.95},

    # --- CONSUMES_COMMODITY (Company -> Commodity) ---
    {"source": "TATASTEEL.NS", "target": "COMM_COKING_COAL", "type": "CONSUMES_COMMODITY", "strength": 0.85, "cost_share_pct": 0.35, "source_tag": "manual_seed", "confidence": 0.95},
    {"source": "JSWSTEEL.NS", "target": "COMM_COKING_COAL", "type": "CONSUMES_COMMODITY", "strength": 0.90, "cost_share_pct": 0.40, "source_tag": "manual_seed", "confidence": 0.95},
    {"source": "JINDALSTEL.NS", "target": "COMM_COKING_COAL", "type": "CONSUMES_COMMODITY", "strength": 0.80, "cost_share_pct": 0.32, "source_tag": "manual_seed", "confidence": 0.92},
    {"source": "TATASTEEL.NS", "target": "COMM_IRON_ORE", "type": "CONSUMES_COMMODITY", "strength": 0.60, "cost_share_pct": 0.25, "source_tag": "manual_seed", "confidence": 0.90},
    {"source": "JSWSTEEL.NS", "target": "COMM_IRON_ORE", "type": "CONSUMES_COMMODITY", "strength": 0.85, "cost_share_pct": 0.35, "source_tag": "manual_seed", "confidence": 0.95},
    {"source": "TATAMOTORS.NS", "target": "COMM_HRC_STEEL", "type": "CONSUMES_COMMODITY", "strength": 0.75, "cost_share_pct": 0.22, "source_tag": "manual_seed", "confidence": 0.92},
    {"source": "MARUTI.NS", "target": "COMM_HRC_STEEL", "type": "CONSUMES_COMMODITY", "strength": 0.78, "cost_share_pct": 0.24, "source_tag": "manual_seed", "confidence": 0.92},
    {"source": "M&M.NS", "target": "COMM_HRC_STEEL", "type": "CONSUMES_COMMODITY", "strength": 0.72, "cost_share_pct": 0.20, "source_tag": "manual_seed", "confidence": 0.90},
    {"source": "BHARATFORG.NS", "target": "COMM_HRC_STEEL", "type": "CONSUMES_COMMODITY", "strength": 0.82, "cost_share_pct": 0.45, "source_tag": "manual_seed", "confidence": 0.95},
    {"source": "HINDALCO.NS", "target": "COMM_ALUMINUM", "type": "CONSUMES_COMMODITY", "strength": 0.90, "cost_share_pct": 0.60, "source_tag": "manual_seed", "confidence": 0.95},
    {"source": "MOTHERSON.NS", "target": "COMM_COPPER", "type": "CONSUMES_COMMODITY", "strength": 0.80, "cost_share_pct": 0.30, "source_tag": "manual_seed", "confidence": 0.92},
    {"source": "MARUTI.NS", "target": "COMM_CHIP_SEMI", "type": "CONSUMES_COMMODITY", "strength": 0.70, "cost_share_pct": 0.12, "source_tag": "manual_seed", "confidence": 0.90},
    {"source": "TATAMOTORS.NS", "target": "COMM_CHIP_SEMI", "type": "CONSUMES_COMMODITY", "strength": 0.72, "cost_share_pct": 0.14, "source_tag": "manual_seed", "confidence": 0.90},
    {"source": "IOC.NS", "target": "COMM_BRENT_CRUDE", "type": "CONSUMES_COMMODITY", "strength": 0.95, "cost_share_pct": 0.85, "source_tag": "manual_seed", "confidence": 0.98},
    {"source": "BPCL.NS", "target": "COMM_BRENT_CRUDE", "type": "CONSUMES_COMMODITY", "strength": 0.95, "cost_share_pct": 0.85, "source_tag": "manual_seed", "confidence": 0.98},
    {"source": "RELIANCE.NS", "target": "COMM_BRENT_CRUDE", "type": "CONSUMES_COMMODITY", "strength": 0.90, "cost_share_pct": 0.75, "source_tag": "manual_seed", "confidence": 0.95},
    {"source": "GUJGASLTD.NS", "target": "COMM_NATURAL_GAS", "type": "CONSUMES_COMMODITY", "strength": 0.90, "cost_share_pct": 0.70, "source_tag": "manual_seed", "confidence": 0.95},

    # --- REGULATED_BY (Company -> Sector / Policy Authority) ---
    {"source": "TATASTEEL.NS", "target": "SEC_STEEL", "type": "REGULATED_BY", "strength": 0.90, "tariff_exposure": 0.85, "source_tag": "manual_seed", "confidence": 0.92},
    {"source": "JSWSTEEL.NS", "target": "SEC_STEEL", "type": "REGULATED_BY", "strength": 0.90, "tariff_exposure": 0.85, "source_tag": "manual_seed", "confidence": 0.92},
    {"source": "TATAMOTORS.NS", "target": "SEC_AUTO", "type": "REGULATED_BY", "strength": 0.85, "tariff_exposure": 0.40, "source_tag": "manual_seed", "confidence": 0.90},
    {"source": "RELIANCE.NS", "target": "SEC_ENERGY", "type": "REGULATED_BY", "strength": 0.90, "tariff_exposure": 0.70, "source_tag": "manual_seed", "confidence": 0.92},
    {"source": "ONGC.NS", "target": "SEC_ENERGY", "type": "REGULATED_BY", "strength": 0.95, "tariff_exposure": 0.80, "source_tag": "manual_seed", "confidence": 0.95},

    # --- SENSITIVE_TO (Sector -> MacroFactor) ---
    {"source": "SEC_AUTO", "target": "MACRO_RBI_REPO", "type": "SENSITIVE_TO", "strength": 0.75, "elasticity_direction": "INVERSE", "source_tag": "manual_seed", "confidence": 0.90},
    {"source": "SEC_IT", "target": "MACRO_USD_INR", "type": "SENSITIVE_TO", "strength": 0.85, "elasticity_direction": "DIRECT", "source_tag": "manual_seed", "confidence": 0.92},
    {"source": "SEC_IT", "target": "MACRO_US_10Y_YIELD", "type": "SENSITIVE_TO", "strength": 0.70, "elasticity_direction": "INVERSE", "source_tag": "manual_seed", "confidence": 0.88},
    {"source": "SEC_ENERGY", "target": "MACRO_USD_INR", "type": "SENSITIVE_TO", "strength": 0.65, "elasticity_direction": "INVERSE", "source_tag": "manual_seed", "confidence": 0.85},
]

# 6. Sample Initial Event Seed
SAMPLE_EVENTS_SEED: List[Dict[str, Any]] = [
    {
        "event_id": "evt_2022_steel_tariff_hike",
        "occurred_at": "2022-05-22T00:00:00+00:00",
        "headline": "Government of India levies 15% Export Duty on Steel Products",
        "raw_source_text": "To curb domestic inflation and increase availability for local manufacturing, the Ministry of Finance announced an export duty of 15% on hot-rolled and cold-rolled steel coils, flat steel, and pig iron.",
        "source_channel": "POLICY_NOTIFICATION",
        "source_url": "https://pib.gov.in/PressReleasePage.aspx?PRID=1827408",
        "archetype": "POLICY_TAX_CHANGE",
        "origin_entity_id": "SEC_STEEL",
        "origin_entity_type": "SECTOR",
        "shock_magnitude": -0.80,
        "nlp_confidence": 0.95,
        "finbert_sentiment": -0.72,
        "llm_classification_metadata": {
            "policy_type": "EXPORT_TARIFF",
            "tariff_rate_pct": 15.0,
            "direct_mechanism": "Export duty reduces foreign sales realization, expanding domestic supply and dampening domestic steel prices.",
            "touched_sectors": ["SEC_STEEL", "SEC_AUTO"],
            "touched_commodities": ["COMM_HRC_STEEL", "COMM_IRON_ORE"]
        },
        "links": [
            {"entity_id": "TATASTEEL.NS", "entity_type": "COMPANY", "mention_role": "DIRECT_TARGET", "confidence": 0.95},
            {"entity_id": "JSWSTEEL.NS", "entity_type": "COMPANY", "mention_role": "DIRECT_TARGET", "confidence": 0.95},
            {"entity_id": "COMM_HRC_STEEL", "entity_type": "COMMODITY", "mention_role": "PRIMARY_SOURCE", "confidence": 0.95},
            {"entity_id": "SEC_AUTO", "entity_type": "SECTOR", "mention_role": "MENTIONED_PEER", "confidence": 0.85},
        ]
    },
    {
        "event_id": "evt_2023_crude_supply_choke",
        "occurred_at": "2023-04-12T00:00:00+00:00",
        "headline": "Red Sea Shipping Disruptions and Refinery Outage Choke Crude Feedstock",
        "raw_source_text": "Attacks on commercial maritime transit and unexpected maintenance shutdowns at major Middle Eastern export terminals have triggered a sharp spike in freight rates and delivered crude prices for Asian refiners.",
        "source_channel": "REUTERS_ENERGY",
        "source_url": "https://reuters.com/business/energy/middle-east-crude-supply",
        "archetype": "SUPPLY_DISRUPTION",
        "origin_entity_id": "COMM_BRENT_CRUDE",
        "origin_entity_type": "COMMODITY",
        "shock_magnitude": -0.65,
        "nlp_confidence": 0.92,
        "finbert_sentiment": -0.68,
        "llm_classification_metadata": {
            "disruption_cause": "MARITIME_CHOKEPOINT",
            "direct_mechanism": "Crude shipping delays increase landed cost of feedstock, compressing gross refining margins for downstream downstream petrochemical producers.",
            "touched_sectors": ["SEC_ENERGY"],
            "touched_commodities": ["COMM_BRENT_CRUDE", "COMM_NATURAL_GAS"]
        },
        "links": [
            {"entity_id": "IOC.NS", "entity_type": "COMPANY", "mention_role": "DIRECT_TARGET", "confidence": 0.95},
            {"entity_id": "BPCL.NS", "entity_type": "COMPANY", "mention_role": "DIRECT_TARGET", "confidence": 0.95},
            {"entity_id": "RELIANCE.NS", "entity_type": "COMPANY", "mention_role": "DIRECT_TARGET", "confidence": 0.90},
            {"entity_id": "COMM_BRENT_CRUDE", "entity_type": "COMMODITY", "mention_role": "PRIMARY_SOURCE", "confidence": 0.98},
        ]
    },
    {
        "event_id": "evt_2023_rbi_repo_hike_50bps",
        "occurred_at": "2023-02-08T00:00:00+00:00",
        "headline": "RBI Monetary Policy Committee Hikes Repo Rate by 50 bps to 6.50%",
        "raw_source_text": "The Reserve Bank of India raised the benchmark repo rate by 50 basis points to anchor core inflation and stabilize the exchange rate, signaling sustained vigilance on borrowing costs.",
        "source_channel": "RBI_MONETARY_POLICY",
        "source_url": "https://rbi.org.in/press/mpc_2023",
        "archetype": "MACRO_RATE_SHIFT",
        "origin_entity_id": "MACRO_RBI_REPO",
        "origin_entity_type": "MACRO",
        "shock_magnitude": -0.55,
        "nlp_confidence": 0.98,
        "finbert_sentiment": -0.45,
        "llm_classification_metadata": {
            "rate_change_bps": 50.0,
            "direct_mechanism": "Higher policy rates increase auto loan financing rates, dampening discretionary consumer vehicle purchases and dealership floor-plan liquidity.",
            "touched_sectors": ["SEC_AUTO"],
            "touched_commodities": []
        },
        "links": [
            {"entity_id": "TATAMOTORS.NS", "entity_type": "COMPANY", "mention_role": "SENSITIVE_TARGET", "confidence": 0.88},
            {"entity_id": "MARUTI.NS", "entity_type": "COMPANY", "mention_role": "SENSITIVE_TARGET", "confidence": 0.88},
            {"entity_id": "M&M.NS", "entity_type": "COMPANY", "mention_role": "SENSITIVE_TARGET", "confidence": 0.85},
            {"entity_id": "SEC_AUTO", "entity_type": "SECTOR", "mention_role": "PRIMARY_SOURCE", "confidence": 0.92},
        ]
    },
    {
        "event_id": "evt_2023_coking_coal_surge",
        "occurred_at": "2023-09-18T00:00:00+00:00",
        "headline": "Queensland Flooding Causes 28% Spike in Premium Coking Coal Benchmark",
        "raw_source_text": "Severe cyclone precipitation flooded open-cut coal pits in the Bowen Basin, halting rail haulage to ports and driving metallurgical coking coal spot prices to multi-month highs.",
        "source_channel": "COMMODITY_INSIGHTS",
        "source_url": "https://spglobal.com/commodityinsights/coal",
        "archetype": "COMMODITY_SHOCK",
        "origin_entity_id": "COMM_COKING_COAL",
        "origin_entity_type": "COMMODITY",
        "shock_magnitude": 0.72,
        "nlp_confidence": 0.94,
        "finbert_sentiment": -0.58,
        "llm_classification_metadata": {
            "commodity": "COKING_COAL",
            "price_move_pct": 28.0,
            "direct_mechanism": "Coking coal is a non-substitutable primary reducing agent in blast furnaces; price spikes immediately elevate cost per tonne of liquid steel.",
            "touched_sectors": ["SEC_STEEL"],
            "touched_commodities": ["COMM_COKING_COAL", "COMM_HRC_STEEL"]
        },
        "links": [
            {"entity_id": "TATASTEEL.NS", "entity_type": "COMPANY", "mention_role": "DIRECT_TARGET", "confidence": 0.96},
            {"entity_id": "JSWSTEEL.NS", "entity_type": "COMPANY", "mention_role": "DIRECT_TARGET", "confidence": 0.96},
            {"entity_id": "COMM_COKING_COAL", "entity_type": "COMMODITY", "mention_role": "PRIMARY_SOURCE", "confidence": 0.98},
            {"entity_id": "SEC_STEEL", "entity_type": "SECTOR", "mention_role": "AFFECTED_SECTOR", "confidence": 0.95},
        ]
    },
    {
        "event_id": "evt_2023_auto_chip_shortage",
        "occurred_at": "2023-06-25T00:00:00+00:00",
        "headline": "Taiwanese Fab Contamination Halts Automotive MCU Fabrication Lines",
        "raw_source_text": "Chemical contamination at a leading 300mm wafer fabrication facility has caused an estimated 6-week halt in micro-controller unit (MCU) supply, prompting auto manufacturers to trim production schedules.",
        "source_channel": "SEMICONDUCTOR_DIGEST",
        "source_url": "https://digitimes.com/news/auto_semi",
        "archetype": "SUPPLY_DISRUPTION",
        "origin_entity_id": "COMM_CHIP_SEMI",
        "origin_entity_type": "COMMODITY",
        "shock_magnitude": -0.60,
        "nlp_confidence": 0.91,
        "finbert_sentiment": -0.62,
        "llm_classification_metadata": {
            "subsystem": "POWERTRAIN_MCUS",
            "direct_mechanism": "Chip shortage limits vehicle assembly completion, causing finished inventory delays and margin dilution.",
            "touched_sectors": ["SEC_AUTO"],
            "touched_commodities": ["COMM_CHIP_SEMI"]
        },
        "links": [
            {"entity_id": "TATAMOTORS.NS", "entity_type": "COMPANY", "mention_role": "DIRECT_TARGET", "confidence": 0.92},
            {"entity_id": "MARUTI.NS", "entity_type": "COMPANY", "mention_role": "DIRECT_TARGET", "confidence": 0.92},
            {"entity_id": "BOSCHLTD.NS", "entity_type": "COMPANY", "mention_role": "TIER1_SUPPLIER", "confidence": 0.95},
            {"entity_id": "SEC_AUTO", "entity_type": "SECTOR", "mention_role": "PRIMARY_SOURCE", "confidence": 0.90},
        ]
    }
]

# 7. Initial Chronological Walk-Forward Split Seed
DATASET_SPLITS_SEED: List[Dict[str, Any]] = [
    {
        "split_id": "SPLIT_2020_2023_WALK_FORWARD_V1",
        "split_type": "TRAIN_VAL_TEST_CHRONOLOGICAL",
        "train_start_date": "2020-01-01",
        "train_end_date": "2022-06-30",
        "val_start_date": "2022-07-01",
        "val_end_date": "2022-12-31",
        "test_start_date": "2023-01-01",
        "test_end_date": "2023-12-31",
        "embargo_window_days": 7,
        "is_purged": True,
    }
]
