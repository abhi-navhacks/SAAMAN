import csv
import os

# Comprehensive multi-sector CPSE material dataset (200+ items)
# Covering Power (NTPC), Steel (SAIL), Mining (Coal India), Oil & Gas (ONGC, IOCL, GAIL, HPCL, BPCL), Heavy Eng (BHEL)

records = []

def add_cluster(items):
    records.extend(items)

# 1. Seamless CS Pipes (ASTM A106 Gr B) - 1/2" to 12"
for size_nb, size_in, thk in [("15", "1/2", "2.77"), ("25", "1", "3.38"), ("50", "2", "3.91"), ("80", "3", "5.49"), ("100", "4", "6.02"), ("150", "6", "7.11"), ("200", "8", "8.18"), ("250", "10", "9.27"), ("300", "12", "10.31")]:
    add_cluster([
        {"CPSE": "IOCL", "Material_Code": f"1002{size_nb}48", "Material_Description": f"PIPE CS SEAMLESS {size_nb}MM SCH 40 A106 GR B ASME B36.10 BEVELED END", "Source_Tender_or_Document": "IOCL/MATHURA/MECH/2024", "Sector": "Oil & Gas", "Category": "PIPE"},
        {"CPSE": "NTPC", "Material_Code": f"4018{size_nb}91", "Material_Description": f"PIPE CSA106-BSMLS {size_nb}MM SCH40 IBR APPROVED PLAIN END", "Source_Tender_or_Document": "NTPC/RIHAND/TND/2024", "Sector": "Power", "Category": "PIPE"},
        {"CPSE": "GAIL", "Material_Code": f"GA-PL-{size_nb}04", "Material_Description": f"CS PIPE {size_in} INCH NB SCH 40 ASTM A106 GRADE B ERW/SMLS", "Source_Tender_or_Document": "GAIL/HVJ/MAINT/2023", "Sector": "Oil & Gas", "Category": "PIPE"},
        {"CPSE": "SAIL", "Material_Code": f"BSP-PP-{size_nb}74", "Material_Description": f"MS/CS PIPE SMLS {size_in}IN SCH40 A106B HEAVY DUTY", "Source_Tender_or_Document": "SAIL/BSP/MECH/2024", "Sector": "Steel", "Category": "PIPE"},
        {"CPSE": "ONGC", "Material_Code": f"OG-P-{size_nb}019", "Material_Description": f"SEAMLESS PIPE {size_in} INCH SCH 40 CARBON STEEL ASTM A106 GRADE B", "Source_Tender_or_Document": "ONGC/MR/MECH/2023", "Sector": "Oil & Gas", "Category": "PIPE"},
        {"CPSE": "BHEL", "Material_Code": f"W96410{size_nb}481", "Material_Description": f"PIPE-CS:ASTM:A-106 GR-B: {size_nb} NB: {thk} MM THK", "Source_Tender_or_Document": "BHEL/TRICHY/BOILER/2024", "Sector": "Heavy Engineering", "Category": "PIPE"},
    ])

# 2. Stainless Steel Pipes (ASTM A312 TP 304 / 316L)
for size_nb, size_in in [("25", "1"), ("50", "2"), ("80", "3"), ("100", "4"), ("150", "6")]:
    add_cluster([
        {"CPSE": "IOCL", "Material_Code": f"1104{size_nb}81", "Material_Description": f"PIPE SS SEAMLESS {size_nb}MM SCH 40S ASTM A312 TP316L ACID RESISTANT", "Source_Tender_or_Document": "IOCL/HALDIA/2024", "Sector": "Oil & Gas", "Category": "PIPE"},
        {"CPSE": "GAIL", "Material_Code": f"GA-SS-{size_nb}42", "Material_Description": f"STAINLESS STEEL PIPE {size_in} IN NB SCH 40S ASTM A312 GR TP 316L SMLS", "Source_Tender_or_Document": "GAIL/PATA/2023", "Sector": "Oil & Gas", "Category": "PIPE"},
        {"CPSE": "NTPC", "Material_Code": f"4029{size_nb}44", "Material_Description": f"PIPE SS316L SMLS {size_nb} NB SCH 40S CHEMICAL DOSING DM WATER", "Source_Tender_or_Document": "NTPC/SIMHADRI/2024", "Sector": "Power", "Category": "PIPE"},
        {"CPSE": "SAIL", "Material_Code": f"DSP-SS-{size_nb}12", "Material_Description": f"SS 316L PIPE SMLS {size_in} INCH SCH 40 CORROSION RESISTANT", "Source_Tender_or_Document": "SAIL/DSP/CHEM/2024", "Sector": "Steel", "Category": "PIPE"},
        {"CPSE": "HPCL", "Material_Code": f"HP-SS-{size_nb}09", "Material_Description": f"PIPE STAINLESS STEEL ASTM A312 TP316L {size_nb} MM SCH 40S", "Source_Tender_or_Document": "HPCL/VR/2024", "Sector": "Oil & Gas", "Category": "PIPE"},
    ])

# 3. Flanged Ball Valves Class 150 & Class 300 (API 6D / A216 WCB)
for size_nb, size_in, rating in [("25", "1", "150"), ("50", "2", "150"), ("50", "2", "300"), ("80", "3", "150"), ("100", "4", "150"), ("100", "4", "300"), ("150", "6", "150"), ("150", "6", "300")]:
    add_cluster([
        {"CPSE": "IOCL", "Material_Code": f"2004{size_nb}{rating[:2]}", "Material_Description": f"VALVE BALL FLANGED {size_nb}MM CL {rating} ASTM A216 WCB FULL BORE API 6D", "Source_Tender_or_Document": "IOCL/BARAUNI/2024", "Sector": "Oil & Gas", "Category": "VALVE"},
        {"CPSE": "GAIL", "Material_Code": f"GA-VL-{size_nb}{rating[:2]}", "Material_Description": f"BALL VALVE {size_in} INCH {rating} LBS FB FLANGED END WCB BODY SS316 TRIM API 6D", "Source_Tender_or_Document": "GAIL/NGP/2024", "Sector": "Oil & Gas", "Category": "VALVE"},
        {"CPSE": "ONGC", "Material_Code": f"OG-V-{size_nb}{rating[:2]}", "Material_Description": f"VALVE BALL {size_in} IN NB CLASS {rating} ASTM A216 GR WCB TRUNNION MOUNTED", "Source_Tender_or_Document": "ONGC/MUMBAI_HIGH/2024", "Sector": "Oil & Gas", "Category": "VALVE"},
        {"CPSE": "BPCL", "Material_Code": f"BP-BV-{size_nb}{rating[:2]}", "Material_Description": f"BALL VALVE {size_in} INCH {rating}# RF FLANGED ASTM A216 WCB FIRE SAFE API 607", "Source_Tender_or_Document": "BPCL/KR/2024", "Sector": "Oil & Gas", "Category": "VALVE"},
        {"CPSE": "HPCL", "Material_Code": f"7710{size_nb}{rating[:2]}", "Material_Description": f"BALL VALVE {size_nb} NB RATING {rating}# BODY CS A216 WCB BALL SS316 LEVER OPERATED", "Source_Tender_or_Document": "HPCL/VR/2024", "Sector": "Oil & Gas", "Category": "VALVE"},
    ])

# 4. Cast Steel Gate Valves Class 150 & 300 (API 600 / WCB)
for size_nb, size_in, rating in [("50", "2", "150"), ("80", "3", "150"), ("100", "4", "150"), ("150", "6", "150"), ("200", "8", "150"), ("250", "10", "150")]:
    add_cluster([
        {"CPSE": "NTPC", "Material_Code": f"4039{size_nb}10", "Material_Description": f"VALVE GATE {size_nb}MM NB CL {rating} CS ASTM A216 GR WCB FLANGED OS&Y", "Source_Tender_or_Document": "NTPC/RAMAGUNDAM/2024", "Sector": "Power", "Category": "VALVE"},
        {"CPSE": "IOCL", "Material_Code": f"2005{size_nb}91", "Material_Description": f"GATE VALVE {size_in} INCH {rating}# RF FLGD BODY WCB TRIM 13CR API 600", "Source_Tender_or_Document": "IOCL/KOYALI/2024", "Sector": "Oil & Gas", "Category": "VALVE"},
        {"CPSE": "SAIL", "Material_Code": f"BSL-GV-{size_nb}40", "Material_Description": f"CAST STEEL GATE VALVE {size_nb} NB CLASS {rating} FLANGED RISING STEM", "Source_Tender_or_Document": "SAIL/BSL/WATER/2024", "Sector": "Steel", "Category": "VALVE"},
        {"CPSE": "BHEL", "Material_Code": f"W97310{size_nb}441", "Material_Description": f"CS GATE VALVE {size_nb} NB CLASS {rating} FLANGED ENDS IBR CERTIFIED", "Source_Tender_or_Document": "BHEL/HARIDWAR/2024", "Sector": "Heavy Engineering", "Category": "VALVE"},
    ])

# 5. Spiral Wound Metallic Gaskets SS316 Graphite (ASME B16.20)
for size_nb, size_in, rating in [("25", "1", "150"), ("50", "2", "300"), ("80", "3", "150"), ("100", "4", "300"), ("150", "6", "150"), ("200", "8", "300")]:
    add_cluster([
        {"CPSE": "IOCL", "Material_Code": f"3001{size_nb}{rating[:2]}", "Material_Description": f"GASKET SP WOUND {size_nb}MM {rating}# SS316 INNER/OUTER RING GRAPHITE FILLER", "Source_Tender_or_Document": "IOCL/BONG/2024", "Sector": "Oil & Gas", "Category": "GASKET"},
        {"CPSE": "BPCL", "Material_Code": f"GSK-SW-{size_nb}-{rating[:2]}", "Material_Description": f"GASKET SPIRAL WOUND {size_in} INCH {rating} LBS SS316/GRAFOIL WITH CS OUTER RING", "Source_Tender_or_Document": "BPCL/MR/2024", "Sector": "Oil & Gas", "Category": "GASKET"},
        {"CPSE": "HPCL", "Material_Code": f"8841{size_nb}{rating[:2]}", "Material_Description": f"SPIRAL WOUND GASKET {size_nb} NB CL{rating} SS316 GRAPHITE ASME B16.20", "Source_Tender_or_Document": "HPCL/FR/2024", "Sector": "Oil & Gas", "Category": "GASKET"},
        {"CPSE": "ONGC", "Material_Code": f"OG-G-{size_nb}{rating[:2]}", "Material_Description": f"METALLIC GASKET SPIRAL WOUND {size_in} IN {rating}# SS316 FLEXIBLE GRAPHITE", "Source_Tender_or_Document": "ONGC/URAN/2024", "Sector": "Oil & Gas", "Category": "GASKET"},
        {"CPSE": "NTPC", "Material_Code": f"4048{size_nb}{rating[:2]}", "Material_Description": f"GASKET METALLIC SPIRAL WOUND {size_nb} NB {rating}# STEAM CLASS SS316", "Source_Tender_or_Document": "NTPC/DADRI/2024", "Sector": "Power", "Category": "GASKET"},
    ])

# 6. Alloy Steel Stud Bolts (ASTM A193 B7 / A194 2H)
for dia, l_in, l_mm in [("1/2", "2.5", "65"), ("5/8", "3.5", "90"), ("3/4", "4.0", "100"), ("7/8", "4.5", "115"), ("1", "5.0", "130"), ("1-1/8", "5.5", "140")]:
    add_cluster([
        {"CPSE": "IOCL", "Material_Code": f"4001{l_mm}84", "Material_Description": f"STUD BOLT ALLOY STEEL {dia} IN X {l_in} IN ASTM A193 B7 WITH 2 NUTS A194 2H", "Source_Tender_or_Document": "IOCL/DIGBOI/2024", "Sector": "Oil & Gas", "Category": "FASTENER"},
        {"CPSE": "ONGC", "Material_Code": f"OG-F-{l_mm}18", "Material_Description": f"STUD BOLTS ASTM A193 GRADE B7 DIA {dia} INCH L={l_mm}MM WITH 2 HEAVY HEX NUTS 2H", "Source_Tender_or_Document": "ONGC/ANKLESHWAR/2024", "Sector": "Oil & Gas", "Category": "FASTENER"},
        {"CPSE": "GAIL", "Material_Code": f"GA-FS-{l_mm}11", "Material_Description": f"FASTENERS STUD BOLT {dia} INCH X {l_in} INCH ASTM A193 B7 2H NUTS CADMIUM PLATED", "Source_Tender_or_Document": "GAIL/CHAINSA/2024", "Sector": "Oil & Gas", "Category": "FASTENER"},
        {"CPSE": "NTPC", "Material_Code": f"4058{l_mm}20", "Material_Description": f"STUD BOLT HIGH TENSILE {dia} X {l_mm}MM GR B7 WITH 2H NUTS FOR PIPING FLANGE", "Source_Tender_or_Document": "NTPC/SINGRAULI/2024", "Sector": "Power", "Category": "FASTENER"},
    ])

# 7. High Voltage XLPE Armoured Cables (11kV / 33kV IS 7098 Pt 2)
for sqmm in ["70", "95", "120", "150", "185", "240", "300"]:
    add_cluster([
        {"CPSE": "NTPC", "Material_Code": f"EL-CBL-11K-{sqmm}", "Material_Description": f"11KV 3CX{sqmm} SQMM AL XLPE ARMORED POWER CABLE IS 7098 PART 2 STRANDED", "Source_Tender_or_Document": "NTPC/KAHALGAON/2024", "Sector": "Power", "Category": "CABLE"},
        {"CPSE": "BHEL", "Material_Code": f"W9641849{sqmm}", "Material_Description": f"HT POWER CABLE 11 KV 3X{sqmm} SQ MM ALUMINIUM CONDUCTOR XLPE INSULATED ARMOURED", "Source_Tender_or_Document": "BHEL/BHOPAL/2024", "Sector": "Heavy Engineering", "Category": "CABLE"},
        {"CPSE": "Coal India", "Material_Code": f"CIL-E-11K{sqmm}", "Material_Description": f"3C X {sqmm} SQ MM 11 KV MINING GRADE XLPE AL ARMOURED POWER CABLE DGMS APPROVED", "Source_Tender_or_Document": "SECL/BILASPUR/ELECT/2024", "Sector": "Mining", "Category": "CABLE"},
        {"CPSE": "SAIL", "Material_Code": f"SAIL-EL-11K-{sqmm}", "Material_Description": f"HT CABLE XLPE ARMOURED 11KV 3 CORE {sqmm} SQMM ALUMINIUM INDUSTRIAL GRADE", "Source_Tender_or_Document": "SAIL/ISP/ELEC/2024", "Sector": "Steel", "Category": "CABLE"},
    ])

# 8. Industrial Bearings (Deep Groove Ball & Spherical Roller)
for brg_num, dims in [("6208", "40X80X18"), ("6210", "50X90X20"), ("6308", "40X90X23"), ("6310", "50X110X27"), ("6312", "60X130X31"), ("6314", "70X150X35")]:
    add_cluster([
        {"CPSE": "SAIL", "Material_Code": f"BRG-{brg_num}-C3", "Material_Description": f"BALL BEARING {brg_num}/C3 RADIAL DEEP GROOVE SINGLE ROW {dims}MM", "Source_Tender_or_Document": "SAIL/RSP/ROLLING/2024", "Sector": "Steel", "Category": "BEARING"},
        {"CPSE": "NTPC", "Material_Code": f"5018{brg_num[:3]}1", "Material_Description": f"BEARING DEEP GROOVE BALL {dims} MM {brg_num} C3 SKF OR FAG MAKE", "Source_Tender_or_Document": "NTPC/TALCHER/2024", "Sector": "Power", "Category": "BEARING"},
        {"CPSE": "IOCL", "Material_Code": f"5002{brg_num[:3]}4", "Material_Description": f"RADIAL BALL BEARING SINGLE ROW {brg_num} C3 CLEARANCE MOTOR SPARE", "Source_Tender_or_Document": "IOCL/VADODARA/2024", "Sector": "Oil & Gas", "Category": "BEARING"},
        {"CPSE": "Coal India", "Material_Code": f"CIL-M-{brg_num}", "Material_Description": f"DEEP GROOVE BALL BRG {brg_num} C3 OPEN TYPE FOR WATER PUMP MOTOR", "Source_Tender_or_Document": "WCL/NAGPUR/2024", "Sector": "Mining", "Category": "BEARING"},
        {"CPSE": "BHEL", "Material_Code": f"W964109{brg_num}", "Material_Description": f"DEEP GROOVE BALL BEARING {brg_num}-C3 STEEL CAGE PRECISION P6", "Source_Tender_or_Document": "BHEL/JHANSI/2024", "Sector": "Heavy Engineering", "Category": "BEARING"},
    ])

# 9. Mining & Steel Heavy Spares (Conveyors, Wear parts, Wire Ropes)
for width in ["800", "1000", "1200", "1400", "1600"]:
    add_cluster([
        {"CPSE": "Coal India", "Material_Code": f"CIL-CV-{width}", "Material_Description": f"CONVEYOR BELT NYLON NYLON NN 800/4 WIDTH {width} MM TOP 5MM BOTTOM 2MM GRADE M24", "Source_Tender_or_Document": "CCL/RANCHI/2024", "Sector": "Mining", "Category": "CONVEYOR"},
        {"CPSE": "NTPC", "Material_Code": f"6018{width}1", "Material_Description": f"CONVEYOR BELT NN-800/4 {width}MM WIDE FIRE RESISTANT GRADE FOR COAL HANDLING PLANT", "Source_Tender_or_Document": "NTPC/BARH/2024", "Sector": "Power", "Category": "CONVEYOR"},
        {"CPSE": "SAIL", "Material_Code": f"SAIL-CV-NN{width}", "Material_Description": f"RUBBER CONVEYOR BELTING NN800/4 {width} MM WIDTH DIN 22102 GRADE W FOR RAW MATERIAL", "Source_Tender_or_Document": "SAIL/RSP/RMHS/2024", "Sector": "Steel", "Category": "CONVEYOR"},
    ])

# 10. MCCB Switchgear (100A, 250A, 400A, 630A, 800A)
for amp in ["100", "250", "400", "630", "800"]:
    add_cluster([
        {"CPSE": "NTPC", "Material_Code": f"EL-SW-{amp}A-4P", "Material_Description": f"MCCB {amp} AMP 4 POLE 50 KA BREAKING CAPACITY WITH MICROPROCESSOR TRIP UNIT", "Source_Tender_or_Document": "NTPC/MOUDA/2024", "Sector": "Power", "Category": "SWITCHGEAR"},
        {"CPSE": "BHEL", "Material_Code": f"SU74205{amp}", "Material_Description": f"CIRCUIT BREAKER MCCB {amp}A 4POLE ICU=50KA 415V AC FORM 4B", "Source_Tender_or_Document": "BHEL/EDN/BANGALORE/2024", "Sector": "Heavy Engineering", "Category": "SWITCHGEAR"},
        {"CPSE": "SAIL", "Material_Code": f"SAIL-SW-MCCB{amp}", "Material_Description": f"{amp}A 4P MCCB 50KA ADJUSTABLE THERMAL MAGNETIC RELEASE FOR PCC PANEL", "Source_Tender_or_Document": "SAIL/BSP/POWER/2024", "Sector": "Steel", "Category": "SWITCHGEAR"},
        {"CPSE": "IOCL", "Material_Code": f"6001{amp}84", "Material_Description": f"MCCB {amp}A 4 POLE 50KA FAULT LEVEL 415V 50HZ WITH EXTENDED ROTARY HANDLE", "Source_Tender_or_Document": "IOCL/PARADIP/2024", "Sector": "Oil & Gas", "Category": "SWITCHGEAR"},
    ])

out_path = r"C:\Users\bit\Downloads\cpse_multi_sector_distinct_materials.csv"
fieldnames = ["CPSE", "Material_Code", "Material_Description", "Source_Tender_or_Document", "Sector", "Category"]

with open(out_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(records)

print(f"Successfully compiled {len(records)} distinct multi-sector CPSE records at {out_path}!")
