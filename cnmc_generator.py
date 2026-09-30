"""
================================================================================
SAMAAN — AI-Driven Common National Material Code (CNMC) Generation Framework
================================================================================
Smart India Hackathon (SIH) — National Unified Material Master Framework
'One Nation – One Material Code'

Key Capabilities:
1. Normalizes and rationalizes messy legacy CPSE material descriptions.
2. Domain & Category Classification across Electrical, Electronics, Mechanical,
   Piping, Instrumentation, and Fasteners.
3. Parametric Engineering Extraction: Extract exact functional attributes.
4. Canonical Technical Identity Key: Deterministic fingerprint of functional equivalence.
5. Persistent National CNMC Registry: Ensures stable, unique national code generation.
6. Standardized National Descriptions: 'One Nation – One Description'.
7. Real-Time Single Item & Batch Code Generation: CLI, Python function, and REST API.
================================================================================
"""

import os
import re
import sys
import json
import logging
import argparse
from pathlib import Path
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CNMC_Engine")

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
BHEL_INPUT_FILE = BASE_DIR / "bhel_material_codes_descriptions_868_clean.csv"
OUTPUT_FILE = DATA_DIR / "unified_material_master.csv"
REGISTRY_FILE = DATA_DIR / "cnmc_registry.json"
CLUSTERS_FILE = DATA_DIR / "cnmc_duplicate_clusters.csv"
CROSS_CPSE_DEMO_FILE = DATA_DIR / "cross_cpse_national_mapping.csv"

# ----------------------------------------------------------------------
# 1. DOMAINS & CATEGORIES
# ----------------------------------------------------------------------
DOMAINS = {
    "EE": "ELECTRICAL_AND_ELECTRONICS",
    "MP": "MECHANICAL_AND_PIPING",
    "IN": "INSTRUMENTATION_AND_CONTROL",
    "FH": "FASTENERS_AND_HARDWARE",
    "GN": "GENERAL_MATERIALS",
}

CATEGORY_RULES = [
    # Electrical & Electronics
    (r"\b(RES|RESISTOR|RES\.|POTENTIOMETER|TRIMPOT|THERMISTOR|VARISTOR|MOV)\b", ("EE", "RES", "RESISTOR")),
    (r"\b(CAP|CAPACITOR|ELEC\s+CAP|TANTALUM|CERAMIC\s+CAP)\b", ("EE", "CAP", "CAPACITOR")),
    (r"\b(CNCTR|CONNECTOR|D-?SUB|HEADER|IDC|EURO\s+MALE|EURO\s+FEMALE|EURO\s+SHELL|TEST\s+JACK|SOCKET\s+TEST|PLUG|TERMINAL\s+BLOCK)\b", ("EE", "CONN", "CONNECTOR")),
    (r"\b(SW|SWITCH|DIL\s+SW|DPDT|SPDT|ROTARY\s+SW|TOGGLE|PUSH\s*BUTTON|LIMIT\s+SW)\b", ("EE", "SW", "SWITCH")),
    (r"\b(RELAY|CONTACTOR|SSR)\b", ("EE", "REL", "RELAY")),
    (r"\b(FUSE|HRC|SEMICONDUCTOR\s+FUSE|FUSE\s+BASE)\b", ("EE", "FUSE", "FUSE")),
    (r"\b(DC-?DC|DC/DC|CONVERTER|INVERTER|POWER\s+SUPPLY|SMPS)\b", ("EE", "PWR", "POWER_CONVERTER")),
    (r"\b(TRANSFORMER|TRANSFMR|XFMR|CHOKE|INDUCTOR|COIL)\b", ("EE", "XFMR", "TRANSFORMER")),
    (r"\b(DIODE|ZENER|RECTIFIER|TRANSISTOR|MOSFET|IGBT|THYRISTOR|TRIAC|LED|OPTOCOUPLER)\b", ("EE", "SEMI", "SEMICONDUCTOR")),
    (r"\b(IC|INTEGRATED\s+CIRCUIT|DGTL|OP-?AMP|MICROCONTROLLER|EEPROM|FLASH|BUFFER|LOGIC)\b", ("EE", "IC", "INTEGRATED_CIRCUIT")),
    (r"\b(CABLE|WIRE|CORD|HARNESS|SLEEVE|LUG|LEAD)\b", ("EE", "CABL", "CABLE_AND_WIRE")),
    (r"\b(PCB|MODULE|CARD|ASSEMBLY|MOTHERBOARD)\b", ("EE", "MOD", "ELECTRONIC_MODULE")),

    # Mechanical & Piping
    (r"\b(PIPE|PIPING|TUBE|TUBING)\b", ("MP", "PIPE", "PIPE")),
    (r"\b(VALVE|GATE\s+VALVE|GLOBE\s+VALVE|BALL\s+VALVE|CHECK\s+VALVE|BUTTERFLY\s+VALVE)\b", ("MP", "VALV", "VALVE")),
    (r"\b(FLANGE|BLIND\s+FLANGE|WELD\s+NECK)\b", ("MP", "FLNG", "FLANGE")),
    (r"\b(GASKET|O-?RING|SEAL|PACKING)\b", ("MP", "GSKT", "GASKET_AND_SEAL")),
    (r"\b(PUMP|IMPELLER|CASING)\b", ("MP", "PUMP", "PUMP")),
    (r"\b(BEARING|BALL\s+BEARING|ROLLER\s+BEARING|BUSH)\b", ("MP", "BEAR", "BEARING")),
    (r"\b(FITTING|ELBOW|TEE|REDUCER|COUPLING|NIPPLE|UNION)\b", ("MP", "FITG", "PIPE_FITTING")),
    (r"\b(FAN|BLOWER|IMPELLER)\b", ("MP", "FAN", "FAN_AND_BLOWER")),
    (r"\b(FILTER|STRAINER|CARTRIDGE)\b", ("MP", "FILT", "FILTER")),
    (r"\b(COMPRESSOR)\b", ("MP", "COMP", "COMPRESSOR")),

    # Fasteners & Hardware
    (r"\b(BOLT|STUD|HEX\s+BOLT)\b", ("FH", "BOLT", "BOLT")),
    (r"\b(NUT|HEX\s+NUT|LOCK\s+NUT)\b", ("FH", "NUT", "NUT")),
    (r"\b(SCREW|MACHINE\s+SCREW)\b", ("FH", "SCRW", "SCREW")),
    (r"\b(WASHER|SPRING\s+WASHER|FLAT\s+WASHER)\b", ("FH", "WSHR", "WASHER")),

    # Instrumentation
    (r"\b(TRANSMITTER|GAUGE|PRESSURE\s+GAUGE|SENSOR|RTD|THERMOCOUPLE|FLOWMETER)\b", ("IN", "INST", "INSTRUMENTATION")),
]

NOISE_PATTERNS = [
    r"\bROHS\s+DEVICE\b.*",
    r"\bOEM\s+TAPE\b.*",
    r"\bOEM\s+PACKAGING\b.*",
    r"\bOEM\s+TUBE\s+PACKAGING\b.*",
    r"\bDATE\s*CODE\b.*",
    r"\bDATE-CODE\b.*",
    r"\bTHE\s+BIDDER\s+SHOULD\b.*",
    r"\bPLANT\s+STD\s*:?\s*[\w\.\-]+",
    r"\bDRG\s*(?:NO)?\s*:?\s*[\w\.\-]+",
    r"\bSIE(?:MENS)?\s+REF\d?\s*:?\s*[\w\.\-]+",
    r"\bREF\s*(?:NO)?\s*:?\s*[\w\.\-]+",
    r"\bOEM\s*:?\s*[\w\/\-]+",
    r"\bTYPE\s*:?\s*[\w\.\-]+",
    r"\bDESCRIPTION\s+NOT\s+EXPOSED\b",
]

# ----------------------------------------------------------------------
# 2. NORMALIZATION & PREPROCESSING
# ----------------------------------------------------------------------
def normalize_text(text: str) -> str:
    """Cleans raw CPSE description and standardizes technical tokens."""
    if not isinstance(text, str):
        return ""
    clean = text.upper().replace("|", " ")

    for p in NOISE_PATTERNS:
        clean = re.sub(p, " ", clean, flags=re.IGNORECASE)

    replacements = [
        (r"\bRES\b", "RESISTOR"),
        (r"\bCNCTR\b", "CONNECTOR"),
        (r"\bSW\b", "SWITCH"),
        (r"\bTRANSFMR\b", "TRANSFORMER"),
        (r"\bXFMR\b", "TRANSFORMER"),
        (r"\bSOC\b", "SOCKET"),
        (r"\bFEML\b", "FEMALE"),
        (r"\bDBL\b", "DOUBLE"),
        (r"\bSTRT\b", "STRAIGHT"),
        (r"\bRTAGL\b", "RIGHT_ANGLED"),
        (r"\bRTA\b", "RIGHT_ANGLED"),
        (r"\bRIGHT\s+ANGLED?\b", "RIGHT_ANGLED"),
        (r"\bFLT\s+CBL\b", "FLAT_CABLE"),
        (r"\bMTL\s+FLM\b", "METAL_FILM"),
        (r"\bMF\b", "METAL_FILM"),
        (r"\bMTL\s+OXD\b", "METAL_OXIDE"),
        (r"\bWW\b", "WIREWOUND"),
        (r"\bTHK\s+FLM\b", "THICK_FILM"),
        (r"\bCER\s+COMP\b", "CERAMIC_COMPOSITION"),
        (r"\bSMT\b", "SMD"),
        (r"\bTH\b", "THROUGH_HOLE"),
        (r"\b0\.25W\b", "0.25W"),
        (r"\b1/4W\b", "0.25W"),
        (r"\b1/2W\b", "0.5W"),
        (r"\b0\.5W\b", "0.5W"),
        (r"\b(\d+(?:\.\d+)?)\s*WATT\b", r"\1W"),
        (r"\b(\d+(?:\.\d+)?)\s*KOHM\b", r"\1K"),
        (r"\b(\d+(?:\.\d+)?)\s*MOHM\b", r"\1M"),
        (r"\b(\d+(?:\.\d+)?)\s*OHM\b", r"\1R"),
    ]
    for pattern, repl in replacements:
        clean = re.sub(pattern, repl, clean)

    clean = re.sub(r"[^\w\.\-\/%\:\+]", " ", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


# ----------------------------------------------------------------------
# 3. GRANULAR PARAMETRIC EXTRACTION
# ----------------------------------------------------------------------
def extract_category(norm_text: str):
    for pattern, (dom, cat, name) in CATEGORY_RULES:
        if re.search(pattern, norm_text, re.IGNORECASE):
            return dom, cat, name
    return "GN", "GEN", "GENERAL_MATERIAL"


def extract_attributes(norm_text: str, category: str) -> dict:
    attrs = {
        "Sub_Type": "STANDARD",
        "Primary_Rating": "UNSPECIFIED",
        "Secondary_Rating": "UNSPECIFIED",
        "Tolerance": "UNSPECIFIED",
        "Package_Mounting": "UNSPECIFIED",
        "Pins_Poles": "UNSPECIFIED",
        "Voltage_Current": "UNSPECIFIED",
        "Material_Grade": "UNSPECIFIED",
    }

    # Universal Mounting / Package (standardize SMD case codes)
    case_code_match = re.search(r"\b(0402|0603|0805|1206|2512|TO-?220|TO-?3|TO-?100|DIP\s*\d*|SOIC)\b", norm_text)
    if case_code_match:
        attrs["Package_Mounting"] = case_code_match.group(1).replace(" ", "")
    else:
        pkg_match = re.search(r"\b(SMD|AXIAL|THROUGH_HOLE|RIGHT_ANGLED|STRAIGHT)\b", norm_text)
        if pkg_match:
            attrs["Package_Mounting"] = pkg_match.group(1)

    # Universal Pins / Poles (handles 32-PIN, 32 PIN, 32 POLE, 32P)
    pins_match = re.search(r"\b(\d+)[\-\s]*(?:PIN|POLE|P|WAY)\b", norm_text)
    if pins_match:
        attrs["Pins_Poles"] = f"{pins_match.group(1)}P"

    # Category Specific Fine-Grained Extractions
    if category == "RESISTOR":
        val_match = re.search(r"\b(\d+(?:\.\d+)?[RKM]|\d+R\d+|\d+\s*OHM)\b", norm_text)
        if val_match:
            attrs["Primary_Rating"] = val_match.group(1).replace(" ", "")

        pwr_match = re.search(r"\b(\d+(?:\.\d+)?\s*W(?:ATT)?)\b", norm_text)
        if pwr_match:
            attrs["Secondary_Rating"] = pwr_match.group(1).replace(" ", "")

        tol_match = re.search(r"\b(\d+(?:\.\d+)?%)\b", norm_text)
        if tol_match:
            attrs["Tolerance"] = tol_match.group(1)

        if "METAL_FILM" in norm_text:
            attrs["Sub_Type"] = "METAL_FILM"
        elif "THICK_FILM" in norm_text:
            attrs["Sub_Type"] = "THICK_FILM"
        elif "WIREWOUND" in norm_text:
            attrs["Sub_Type"] = "WIREWOUND"
        elif "CERAMIC_COMPOSITION" in norm_text or "CARBON" in norm_text:
            attrs["Sub_Type"] = "CARBON_OR_CERAMIC"
        elif "VARISTOR" in norm_text or "MOV" in norm_text:
            attrs["Sub_Type"] = "VARISTOR_MOV"
        elif "POT" in norm_text or "TRIMPOT" in norm_text:
            attrs["Sub_Type"] = "POTENTIOMETER"

    elif category == "INTEGRATED_CIRCUIT":
        chip_match = re.search(
            r"\b(74[A-Z0-9]+|LM\d+[A-Z0-9]*|AD\d+[A-Z0-9]*|MC\d+[A-Z0-9]*|MAX\d+[A-Z0-9]*|TL\d+[A-Z0-9]*|CD\d+[A-Z0-9]*|NE\d+[A-Z0-9]*)\b",
            norm_text,
            re.IGNORECASE,
        )
        if chip_match:
            attrs["Primary_Rating"] = chip_match.group(1).upper()

        if "NAND" in norm_text:
            attrs["Sub_Type"] = "NAND_GATE"
        elif "AND" in norm_text:
            attrs["Sub_Type"] = "AND_GATE"
        elif "OR" in norm_text:
            attrs["Sub_Type"] = "OR_GATE"
        elif "COMPARATOR" in norm_text:
            attrs["Sub_Type"] = "COMPARATOR"
        elif "VOLT REG" in norm_text or "REGULATOR" in norm_text:
            attrs["Sub_Type"] = "VOLTAGE_REGULATOR"
        elif "DAC" in norm_text:
            attrs["Sub_Type"] = "DAC"
        elif "MULTIPLIER" in norm_text:
            attrs["Sub_Type"] = "MULTIPLIER"
        elif "OP-AMP" in norm_text or "AMPLIFIER" in norm_text:
            attrs["Sub_Type"] = "OP_AMP"

    elif category == "CONNECTOR":
        if "EURO" in norm_text:
            attrs["Sub_Type"] = "EURO_CONNECTOR"
        elif "D-SUB" in norm_text or "DSUB" in norm_text:
            attrs["Sub_Type"] = "D_SUB"
        elif "HEADER" in norm_text:
            attrs["Sub_Type"] = "PIN_HEADER"
        elif "IDC" in norm_text:
            attrs["Sub_Type"] = "IDC"
        elif "JACK" in norm_text or "SOCKET" in norm_text:
            attrs["Sub_Type"] = "TEST_JACK"

        if "MALE" in norm_text:
            attrs["Material_Grade"] = "MALE"
        elif "FEMALE" in norm_text:
            attrs["Material_Grade"] = "FEMALE"

        dim_match = re.search(r"\b(\d+(?:\.\d+)?\s*MM)\b", norm_text)
        if dim_match:
            attrs["Primary_Rating"] = dim_match.group(1).replace(" ", "")

    elif category == "RELAY":
        coil_match = re.search(r"\b(\d+\s*V(?:DC|AC)?)\b", norm_text)
        if coil_match:
            attrs["Primary_Rating"] = f"COIL_{coil_match.group(1).replace(' ', '')}"
        cur_match = re.search(r"\b(\d+\s*A)\b", norm_text)
        if cur_match:
            attrs["Secondary_Rating"] = f"CONTACT_{cur_match.group(1).replace(' ', '')}"
        if "1CO" in norm_text or "1 C/O" in norm_text:
            attrs["Sub_Type"] = "1CO"
        elif "2CO" in norm_text or "2 C/O" in norm_text:
            attrs["Sub_Type"] = "2CO"
        elif "DPDT" in norm_text:
            attrs["Sub_Type"] = "DPDT"
        elif "SPDT" in norm_text:
            attrs["Sub_Type"] = "SPDT"

    elif category == "SWITCH":
        if "DIL" in norm_text:
            attrs["Sub_Type"] = "DIL_SWITCH"
        elif "DPDT" in norm_text:
            attrs["Sub_Type"] = "DPDT"
        elif "ROTARY" in norm_text:
            attrs["Sub_Type"] = "ROTARY"

        sw_rating = re.search(r"\b(\d+(?:\.\d+)?\s*[AM]?[VA]?(?:C|DC)?)\b", norm_text)
        if sw_rating:
            attrs["Voltage_Current"] = sw_rating.group(1).replace(" ", "")

    elif category == "FUSE":
        if "HRC" in norm_text:
            attrs["Sub_Type"] = "HRC_FUSE"
        elif "SEMICONDUCTOR" in norm_text:
            attrs["Sub_Type"] = "SEMICONDUCTOR_FUSE"

        cur_match = re.search(r"\b(\d+\s*A)\b", norm_text)
        volt_match = re.search(r"\b(\d+\s*V)\b", norm_text)
        if cur_match:
            attrs["Primary_Rating"] = cur_match.group(1).replace(" ", "")
        if volt_match:
            attrs["Secondary_Rating"] = volt_match.group(1).replace(" ", "")

    elif category == "POWER_CONVERTER":
        attrs["Sub_Type"] = "DC_DC_CONVERTER"
        pwr_match = re.search(r"\b(\d+\s*W)\b", norm_text)
        if pwr_match:
            attrs["Primary_Rating"] = pwr_match.group(1).replace(" ", "")
        volt_match = re.search(r"(\d+V(?:DC)?\s*[\/\-]\s*\d+V(?:DC)?)", norm_text)
        if volt_match:
            attrs["Voltage_Current"] = volt_match.group(1).replace(" ", "")

    elif category in ("PIPE", "VALVE", "FLANGE", "PIPE_FITTING"):
        dim_match = re.search(r"\b(\d+(?:\.\d+)?\s*(?:MM|NB|IN|INCH))\b", norm_text)
        if dim_match:
            attrs["Primary_Rating"] = dim_match.group(1).replace(" ", "")
        sch_match = re.search(r"\b(SCH\s*\d+|CLASS\s*\d+|PN\s*\d+)\b", norm_text)
        if sch_match:
            attrs["Secondary_Rating"] = sch_match.group(1).replace(" ", "")
        mat_match = re.search(r"\b(SS\s*\d+|SS|CS|MS|CI|DI|GI|PVC|ASTM\s*[A-Z]?\d+)\b", norm_text)
        if mat_match:
            attrs["Material_Grade"] = mat_match.group(1).replace(" ", "")

    return attrs


# ----------------------------------------------------------------------
# 4. CANONICAL KEY & STANDARDIZED DESCRIPTION
# ----------------------------------------------------------------------
def generate_canonical_key(domain: str, cat_code: str, attrs: dict) -> str:
    """Deterministic engineering fingerprint for national functional grouping."""
    parts = [
        domain,
        cat_code,
        attrs["Sub_Type"],
        attrs["Primary_Rating"],
        attrs["Secondary_Rating"],
        attrs["Tolerance"],
        attrs["Package_Mounting"],
        attrs["Pins_Poles"],
        attrs["Material_Grade"],
    ]
    return "|".join(parts)


def generate_standardized_description(cat_name: str, attrs: dict) -> str:
    """One Nation – One Description format."""
    tokens = [cat_name]
    if attrs["Sub_Type"] != "STANDARD":
        tokens.append(attrs["Sub_Type"].replace("_", " "))
    if attrs["Primary_Rating"] != "UNSPECIFIED":
        tokens.append(attrs["Primary_Rating"])
    if attrs["Secondary_Rating"] != "UNSPECIFIED":
        tokens.append(attrs["Secondary_Rating"])
    if attrs["Tolerance"] != "UNSPECIFIED":
        tokens.append(f"TOL {attrs['Tolerance']}")
    if attrs["Pins_Poles"] != "UNSPECIFIED":
        tokens.append(attrs["Pins_Poles"])
    if attrs["Package_Mounting"] != "UNSPECIFIED":
        tokens.append(f"PKG {attrs['Package_Mounting']}")
    if attrs["Material_Grade"] != "UNSPECIFIED":
        tokens.append(attrs["Material_Grade"])
    return ", ".join(tokens)


# ----------------------------------------------------------------------
# 5. REGISTRY & CNMC ASSIGNMENT
# ----------------------------------------------------------------------
def load_registry(filepath: Path = REGISTRY_FILE) -> dict:
    if filepath.exists():
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"metadata": {"standard": "CNMC-SIH26", "version": "2.0"}, "registry": {}}


def save_registry(registry_data: dict, filepath: Path = REGISTRY_FILE):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(registry_data, f, indent=2, ensure_ascii=False)


def assign_cnmc(canonical_key: str, domain: str, cat_code: str, registry_data: dict) -> tuple[str, bool]:
    """
    Format: CNMC-<DOMAIN>-<CATEGORY>-<6_DIGIT_SERIAL>
    e.g. CNMC-EE-RES-000042
    """
    reg = registry_data["registry"]
    if canonical_key in reg:
        return reg[canonical_key]["cnmc"], False

    prefix = f"CNMC-{domain}-{cat_code}"
    existing_serials = []
    for entry in reg.values():
        code = entry.get("cnmc", "")
        if code.startswith(prefix):
            m = re.search(r"-(\d{6})$", code)
            if m:
                existing_serials.append(int(m.group(1)))

    next_serial = max(existing_serials, default=0) + 1
    cnmc_code = f"{prefix}-{next_serial:06d}"

    reg[canonical_key] = {
        "cnmc": cnmc_code,
        "domain": domain,
        "category": cat_code,
        "canonical_key": canonical_key,
        "mapped_cpse_count": 0,
    }
    return cnmc_code, True


# ----------------------------------------------------------------------
# 6. RUNTIME CODE GENERATION FUNCTION (FOR API & CLI)
# ----------------------------------------------------------------------
def generate_cnmc_for_material(
    description: str,
    cpse: str = "EXTERNAL_CPSE",
    legacy_code: str = "NEW_ITEM",
    save_to_master: bool = False,
) -> dict:
    """
    Core function called to generate or look up the Common National Material Code (CNMC)
    for ANY input material description in real time.
    """
    registry_data = load_registry()

    norm = normalize_text(description)
    dom, cat, name = extract_category(norm)
    attrs = extract_attributes(norm, name)
    canonical_key = generate_canonical_key(dom, cat, attrs)
    std_desc = generate_standardized_description(name, attrs)

    # Check registry or mint new
    cnmc_code, is_new = assign_cnmc(canonical_key, dom, cat, registry_data)

    # Find existing matching materials from unified_material_master.csv if exists
    other_matches = []
    if OUTPUT_FILE.exists():
        try:
            master_df = pd.read_csv(OUTPUT_FILE)
            matches = master_df[master_df["CNMC"] == cnmc_code]
            for _, r in matches.head(10).iterrows():
                other_matches.append({
                    "cpse": str(r.get("CPSE", "")),
                    "legacy_code": str(r.get("Legacy_Material_Code", "")),
                    "original_description": str(r.get("Original_Description", "")),
                })
        except Exception:
            pass

    if save_to_master:
        save_registry(registry_data)

    return {
        "cnmc": cnmc_code,
        "standardized_description": std_desc,
        "domain": DOMAINS.get(dom, dom),
        "domain_code": dom,
        "category": name,
        "category_code": cat,
        "canonical_key": canonical_key,
        "extracted_attributes": attrs,
        "normalized_description": norm,
        "input_description": description,
        "cpse": cpse,
        "legacy_code": legacy_code,
        "status": "NEW_CNMC_GENERATED" if is_new else "AUTO_MAPPED_TO_EXISTING_CNMC",
        "is_existing_cluster": not is_new,
        "matched_existing_materials": other_matches,
    }


# ----------------------------------------------------------------------
# 7. CROSS-CPSE DEMO GENERATION
# ----------------------------------------------------------------------
def generate_cross_cpse_demo(registry_data: dict) -> pd.DataFrame:
    cross_cpse_samples = [
        {"CPSE": "BHEL", "Legacy_Code": "DV0692411534", "Desc": "Res MF SMD 100K 0.25W 1% 1206 | RES MF SMD 100K 1% 0.25W 50PPM 1206"},
        {"CPSE": "IOCL", "Legacy_Code": "IOCL-RES-10482", "Desc": "RESISTOR METAL FILM 100K 1/4W 1% SMD 1206 OEM:YAGEO"},
        {"CPSE": "ONGC", "Legacy_Code": "ONGC-E-883912", "Desc": "RES SMD 100KOHM 0.25 WATT 1% PKG 1206 ROHS"},
        {"CPSE": "NTPC", "Legacy_Code": "NTPC-INST-5510", "Desc": "RESISTOR MF 100K 0.25W 1% SMD 1206 (SPARE)"},
        {"CPSE": "BHEL", "Legacy_Code": "CN9068352105", "Desc": "CNCTR EURO MALE 32 POLE STRT | SLDR/FASTON | CNCTR MALE 32 POLE | TYPE :0906.032.2905"},
        {"CPSE": "NTPC", "Legacy_Code": "NTPC-ELEC-4821", "Desc": "32-PIN MALE EURO CONNECTOR STRAIGHT FASTON SOLDER"},
        {"CPSE": "GAIL", "Legacy_Code": "GAIL-C-229014", "Desc": "EURO CONNECTOR MALE 32 POLE STRT TYPE 0906"},
        {"CPSE": "BHEL", "Legacy_Code": "CN9073130018", "Desc": "FUSE HRC 50A 800V821 CP URD 36.55 QSP | FUSE HRC 50A 800V"},
        {"CPSE": "IOCL", "Legacy_Code": "IOCL-FUSE-994", "Desc": "HRC FUSE 50A 800V BOLTED TYPE CP URD"},
        {"CPSE": "ONGC", "Legacy_Code": "ONGC-P-44109", "Desc": "50A 800V HRC FUSE LINK 36.55 QSP"},
        {"CPSE": "BHEL", "Legacy_Code": "CN9076364044", "Desc": "RELAY 24VDC I C/0V | RATED SWITCHING VOLTAGE: 240VAC | CONTACT RATING: 8A"},
        {"CPSE": "NTPC", "Legacy_Code": "NTPC-REL-3108", "Desc": "RELAY 1CO 8A COIL 24VDC 240VAC CONTACT"},
        {"CPSE": "IOCL", "Legacy_Code": "IOCL-PIP-5501", "Desc": "PIPE SEAMLESS CS 50NB SCH 40 ASTM A106 GR B"},
        {"CPSE": "ONGC", "Legacy_Code": "ONGC-DR-8812", "Desc": "CARBON STEEL SEAMLESS PIPE 50NB SCH40 A106"},
        {"CPSE": "GAIL", "Legacy_Code": "GAIL-PIP-1029", "Desc": "CS PIPE 50NB SCH 40 ASTM A106"},
    ]

    records = []
    for item in cross_cpse_samples:
        norm = normalize_text(item["Desc"])
        dom, cat, name = extract_category(norm)
        attrs = extract_attributes(norm, name)
        ckey = generate_canonical_key(dom, cat, attrs)
        sdesc = generate_standardized_description(name, attrs)
        cnmc, is_new = assign_cnmc(ckey, dom, cat, registry_data)

        records.append({
            "CNMC": cnmc,
            "CPSE": item["CPSE"],
            "Legacy_Material_Code": item["Legacy_Code"],
            "Domain": DOMAINS.get(dom, dom),
            "Category": name,
            "Standardized_National_Description": sdesc,
            "Original_Description": item["Desc"],
            "Mapping_Status": "CROSS_CPSE_AUTO_MAPPED",
        })

    demo_df = pd.DataFrame(records)
    demo_df.to_csv(CROSS_CPSE_DEMO_FILE, index=False, encoding="utf-8-sig")
    return demo_df


# ----------------------------------------------------------------------
# 8. BATCH PIPELINE EXECUTION
# ----------------------------------------------------------------------
def run_cnmc_pipeline(input_csv: Path = BHEL_INPUT_FILE):
    logger.info("============================================================")
    logger.info("STARTING SAMAAN NATIONAL CNMC GENERATION ENGINE")
    logger.info("============================================================")

    registry_data = load_registry(REGISTRY_FILE)

    logger.info(f"Loading master catalog: {input_csv}")
    df = pd.read_csv(input_csv)
    df = df[~df["Material_Description"].str.contains("Description not exposed", na=False)].reset_index(drop=True)
    logger.info(f"Processing {len(df)} materials...")

    processed = []
    for _, row in df.iterrows():
        raw_desc = str(row.get("Material_Description", ""))
        cpse = str(row.get("CPSE", "BHEL"))
        code = str(row.get("Material_Code", ""))

        norm = normalize_text(raw_desc)
        dom, cat, name = extract_category(norm)
        attrs = extract_attributes(norm, name)
        ckey = generate_canonical_key(dom, cat, attrs)
        sdesc = generate_standardized_description(name, attrs)
        cnmc, is_new = assign_cnmc(ckey, dom, cat, registry_data)
        registry_data["registry"][ckey]["mapped_cpse_count"] += 1

        status = "NEW_CNMC_GENERATED" if is_new else "AUTO_MAPPED_TO_EXISTING_CNMC"

        processed.append({
            "CNMC": cnmc,
            "CPSE": cpse,
            "Legacy_Material_Code": code,
            "Domain": DOMAINS.get(dom, dom),
            "Category": name,
            "Standardized_National_Description": sdesc,
            "Original_Description": raw_desc,
            "Normalized_Description": norm,
            "Sub_Type": attrs["Sub_Type"],
            "Primary_Rating": attrs["Primary_Rating"],
            "Secondary_Rating": attrs["Secondary_Rating"],
            "Tolerance": attrs["Tolerance"],
            "Package_Mounting": attrs["Package_Mounting"],
            "Pins_Poles": attrs["Pins_Poles"],
            "Voltage_Current": attrs["Voltage_Current"],
            "Canonical_Key": ckey,
            "Mapping_Status": status,
        })

    out_df = pd.DataFrame(processed)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    generate_cross_cpse_demo(registry_data)
    save_registry(registry_data, REGISTRY_FILE)

    cnmc_counts = out_df["CNMC"].value_counts()
    multi_cnmcs = cnmc_counts[cnmc_counts > 1].index.tolist()
    clusters_df = out_df[out_df["CNMC"].isin(multi_cnmcs)].sort_values(by=["CNMC", "Legacy_Material_Code"])
    clusters_df.to_csv(CLUSTERS_FILE, index=False, encoding="utf-8-sig")

    logger.info("============================================================")
    logger.info("NATIONAL CNMC GENERATION COMPLETE")
    logger.info("============================================================")
    logger.info(f"Total CPSE legacy materials processed : {len(out_df)}")
    logger.info(f"Unique Common National Codes (CNMC)  : {out_df['CNMC'].nunique()}")
    logger.info(f"Number of multi-item clusters        : {len(multi_cnmcs)}")
    logger.info(f"Legacy items merged into clusters    : {len(clusters_df)}")
    logger.info(f"Output Master Table saved to: {OUTPUT_FILE}")
    logger.info("============================================================")

    return out_df, clusters_df


# ----------------------------------------------------------------------
# 9. CLI ENTRY POINT
# ----------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Common National Material Code (CNMC)")
    parser.add_argument("--desc", type=str, help="Raw material description to generate CNMC for")
    parser.add_argument("--cpse", type=str, default="CPSE_USER", help="CPSE enterprise name (e.g. BHEL, ONGC, IOCL)")
    parser.add_argument("--code", type=str, default="LEGACY_001", help="Legacy ERP Material Code")
    parser.add_argument("--batch", type=str, help="Path to batch CSV file with Material_Description column")

    args = parser.parse_args()

    if args.desc:
        result = generate_cnmc_for_material(args.desc, cpse=args.cpse, legacy_code=args.code)
        print("\n" + "=" * 60)
        print("COMMON NATIONAL MATERIAL CODE (CNMC) RESULT")
        print("=" * 60)
        print(f"Generated CNMC          : {result['cnmc']}")
        print(f"Standardized Description: {result['standardized_description']}")
        print(f"Domain                  : {result['domain']}")
        print(f"Category                : {result['category']}")
        print(f"Canonical Identity Key  : {result['canonical_key']}")
        print(f"Mapping Status          : {result['status']}")
        if result["matched_existing_materials"]:
            print(f"\nExisting CPSE Materials Mapped to this Same CNMC ({len(result['matched_existing_materials'])}):")
            for m in result["matched_existing_materials"][:5]:
                print(f"  - [{m['cpse']} | {m['legacy_code']}]: {m['original_description'][:70]}")
        print("=" * 60 + "\n")
    elif args.batch:
        run_cnmc_pipeline(Path(args.batch))
    else:
        # Default full regeneration on BHEL data
        run_cnmc_pipeline()
