"""
Entity Linker & Graph Node Disambiguation
=========================================
Resolves raw text mentions of companies, commodities, sectors, and macro factors
to canonical Neo4j knowledge graph node IDs with resolution confidence scores.
"""

import logging
import re
from typing import Dict, List, Optional, Set, Tuple

from ml.nlp.schemas import ExtractedEntity

logger = logging.getLogger(__name__)

# Canonical Entity Gazetteer: mapping aliases to (node_id, entity_type)
ENTITY_GAZETTEER: Dict[str, Tuple[str, str]] = {
    # --- Companies (.NS Tickers) ---
    "tata motors": ("TATAMOTORS.NS", "COMPANY"),
    "tatamotors": ("TATAMOTORS.NS", "COMPANY"),
    "jlr": ("TATAMOTORS.NS", "COMPANY"),
    "jaguar land rover": ("TATAMOTORS.NS", "COMPANY"),
    "maruti": ("MARUTI.NS", "COMPANY"),
    "maruti suzuki": ("MARUTI.NS", "COMPANY"),
    "mahindra": ("M&M.NS", "COMPANY"),
    "mahindra & mahindra": ("M&M.NS", "COMPANY"),
    "m&m": ("M&M.NS", "COMPANY"),
    "bajaj auto": ("BAJAJ-AUTO.NS", "COMPANY"),
    "bharat forge": ("BHARATFORG.NS", "COMPANY"),
    "motherson": ("MOTHERSON.NS", "COMPANY"),
    "samvardhana motherson": ("MOTHERSON.NS", "COMPANY"),
    "bosch": ("BOSCHLTD.NS", "COMPANY"),
    "apollo tyres": ("APOLLOTYRE.NS", "COMPANY"),
    "mrf": ("MRF.NS", "COMPANY"),

    "tata steel": ("TATASTEEL.NS", "COMPANY"),
    "tatasteel": ("TATASTEEL.NS", "COMPANY"),
    "jsw steel": ("JSWSTEEL.NS", "COMPANY"),
    "jswsteel": ("JSWSTEEL.NS", "COMPANY"),
    "jindal steel": ("JINDALSTEL.NS", "COMPANY"),
    "jspl": ("JINDALSTEL.NS", "COMPANY"),
    "sail": ("SAIL.NS", "COMPANY"),
    "steel authority of india": ("SAIL.NS", "COMPANY"),
    "hindalco": ("HINDALCO.NS", "COMPANY"),
    "vedanta": ("VEDL.NS", "COMPANY"),
    "nmdc": ("NMDC.NS", "COMPANY"),
    "nalco": ("NATIONALUM.NS", "COMPANY"),
    "national aluminium": ("NATIONALUM.NS", "COMPANY"),

    "reliance": ("RELIANCE.NS", "COMPANY"),
    "reliance industries": ("RELIANCE.NS", "COMPANY"),
    "ril": ("RELIANCE.NS", "COMPANY"),
    "ongc": ("ONGC.NS", "COMPANY"),
    "oil and natural gas corporation": ("ONGC.NS", "COMPANY"),
    "ioc": ("IOC.NS", "COMPANY"),
    "indian oil": ("IOC.NS", "COMPANY"),
    "bpcl": ("BPCL.NS", "COMPANY"),
    "bharat petroleum": ("BPCL.NS", "COMPANY"),
    "gail": ("GAIL.NS", "COMPANY"),
    "oil india": ("OIL.NS", "COMPANY"),
    "petronet": ("PETRONET.NS", "COMPANY"),
    "petronet lng": ("PETRONET.NS", "COMPANY"),
    "gujarat gas": ("GUJGASLTD.NS", "COMPANY"),

    "tcs": ("TCS.NS", "COMPANY"),
    "tata consultancy": ("TCS.NS", "COMPANY"),
    "infosys": ("INFY.NS", "COMPANY"),
    "infy": ("INFY.NS", "COMPANY"),
    "wipro": ("WIPRO.NS", "COMPANY"),
    "hcl tech": ("HCLTECH.NS", "COMPANY"),
    "hcl technologies": ("HCLTECH.NS", "COMPANY"),
    "tech mahindra": ("TECHM.NS", "COMPANY"),
    "ltimindtree": ("LTIM.NS", "COMPANY"),
    "ltim": ("LTIM.NS", "COMPANY"),
    "persistent": ("PERSISTENT.NS", "COMPANY"),
    "persistent systems": ("PERSISTENT.NS", "COMPANY"),
    "coforge": ("COFORGE.NS", "COMPANY"),
    "mphasis": ("MPHASIS.NS", "COMPANY"),
    "ltts": ("LTTS.NS", "COMPANY"),
    "kpit": ("KPITTECH.NS", "COMPANY"),
    "kpit technologies": ("KPITTECH.NS", "COMPANY"),

    # --- Commodities ---
    "brent crude": ("COMM_BRENT_CRUDE", "COMMODITY"),
    "crude oil": ("COMM_BRENT_CRUDE", "COMMODITY"),
    "brent": ("COMM_BRENT_CRUDE", "COMMODITY"),
    "oil prices": ("COMM_BRENT_CRUDE", "COMMODITY"),
    "natural gas": ("COMM_NATURAL_GAS", "COMMODITY"),
    "lng": ("COMM_NATURAL_GAS", "COMMODITY"),
    "coking coal": ("COMM_COKING_COAL", "COMMODITY"),
    "metallurgical coal": ("COMM_COKING_COAL", "COMMODITY"),
    "iron ore": ("COMM_IRON_ORE", "COMMODITY"),
    "iron ore fines": ("COMM_IRON_ORE", "COMMODITY"),
    "hot rolled coil": ("COMM_HRC_STEEL", "COMMODITY"),
    "hot-rolled coil": ("COMM_HRC_STEEL", "COMMODITY"),
    "hrc": ("COMM_HRC_STEEL", "COMMODITY"),
    "flat steel": ("COMM_HRC_STEEL", "COMMODITY"),
    "steel products": ("COMM_HRC_STEEL", "COMMODITY"),
    "aluminum": ("COMM_ALUMINUM", "COMMODITY"),
    "aluminium": ("COMM_ALUMINUM", "COMMODITY"),
    "copper": ("COMM_COPPER", "COMMODITY"),
    "semiconductor": ("COMM_CHIP_SEMI", "COMMODITY"),
    "semiconductors": ("COMM_CHIP_SEMI", "COMMODITY"),
    "chip shortage": ("COMM_CHIP_SEMI", "COMMODITY"),
    "auto chips": ("COMM_CHIP_SEMI", "COMMODITY"),

    # --- Sectors ---
    "automotive": ("SEC_AUTO", "SECTOR"),
    "auto sector": ("SEC_AUTO", "SECTOR"),
    "automobiles": ("SEC_AUTO", "SECTOR"),
    "steel sector": ("SEC_STEEL", "SECTOR"),
    "metals sector": ("SEC_STEEL", "SECTOR"),
    "steel": ("SEC_STEEL", "SECTOR"),
    "metals": ("SEC_STEEL", "SECTOR"),
    "energy sector": ("SEC_ENERGY", "SECTOR"),
    "oil and gas": ("SEC_ENERGY", "SECTOR"),
    "it sector": ("SEC_IT", "SECTOR"),
    "information technology": ("SEC_IT", "SECTOR"),
    "it services": ("SEC_IT", "SECTOR"),

    # --- Macro Factors ---
    "repo rate": ("MACRO_RBI_REPO", "MACRO"),
    "rbi repo": ("MACRO_RBI_REPO", "MACRO"),
    "monetary policy committee": ("MACRO_RBI_REPO", "MACRO"),
    "interest rate": ("MACRO_RBI_REPO", "MACRO"),
    "usd inr": ("MACRO_USD_INR", "MACRO"),
    "usd/inr": ("MACRO_USD_INR", "MACRO"),
    "rupee": ("MACRO_USD_INR", "MACRO"),
    "inflation": ("MACRO_INDIA_CPI", "MACRO"),
    "cpi": ("MACRO_INDIA_CPI", "MACRO"),
    "treasury yield": ("MACRO_US_10Y_YIELD", "MACRO"),
    "us 10-year": ("MACRO_US_10Y_YIELD", "MACRO"),
}


class EntityLinker:
    """Disambiguates and links text phrases to graph node IDs."""

    def __init__(self) -> None:
        # Sort gazetteer keys by descending length for greedy longest-phrase matching
        self._sorted_keys = sorted(ENTITY_GAZETTEER.keys(), key=len, reverse=True)

    def extract_entities(self, text: str) -> List[ExtractedEntity]:
        """Extract and resolve entities from raw text with confidence scores."""
        text_lower = text.lower()
        extracted: List[ExtractedEntity] = []
        seen_node_ids: Set[str] = set()

        for phrase in self._sorted_keys:
            pattern = r"\b" + re.escape(phrase) + r"\b"
            if re.search(pattern, text_lower):
                node_id, entity_type = ENTITY_GAZETTEER[phrase]
                if node_id not in seen_node_ids:
                    seen_node_ids.add(node_id)
                    confidence = 0.95 if entity_type == "COMPANY" else 0.90
                    extracted.append(
                        ExtractedEntity(
                            name=phrase.title(),
                            matched_node_id=node_id,
                            entity_type=entity_type,
                            confidence=confidence,
                            mention_role="DIRECT_TARGET"
                        )
                    )

        return extracted
