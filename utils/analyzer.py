"""
analyzer.py  —  Flexible medical report value extractor
Handles many PDF formats: "Test : value unit", "Test  value  unit", tables, etc.
"""

import re
from utils.reference_ranges import REFERENCE_RANGES

# ─────────────────────────────────────────────────────────────────────────────
# PATTERN ALIASES
# Each key maps to many common ways labs write that test name in a PDF
# ─────────────────────────────────────────────────────────────────────────────
TEST_ALIASES = {
    "Hemoglobin": [
        r"h[ae]moglobin",
        r"hb(?!\w)",
        r"hgb",
    ],
    "WBC": [
        r"wbc",
        r"white\s*blood\s*cell",
        r"total\s*leucocyte\s*count",
        r"tlc",
        r"total\s*wbc",
    ],
    "Platelets": [
        r"platelet",
        r"plt(?!\w)",
        r"thrombocyte",
    ],
    "Creatinine": [
        r"creatinine",
        r"creat(?!\w)",
        r"s\.?\s*creatinine",
        r"serum\s*creatinine",
    ],
    "Cholesterol": [
        r"total\s*cholesterol",
        r"cholesterol\s*total",
        r"cholesterol(?!\s*[,:(]?\s*(?:ldl|hdl|vldl))",
    ],
    "Triglycerides": [
        r"triglyceride",
        r"tg(?!\w)",
        r"triacylglycerol",
    ],
    "HDL": [
        r"hdl[\s\-]*cholesterol",
        r"hdl[\s\-]*c(?!\w)",
        r"hdl(?!\w)",
        r"high\s*density\s*lipoprotein",
    ],
    "LDL": [
        r"ldl[\s\-]*cholesterol",
        r"ldl[\s\-]*c(?!\w)",
        r"ldl(?!\w)",
        r"low\s*density\s*lipoprotein",
    ],
    "Glucose Fasting": [
        r"glucose[\s,]*fasting",
        r"fasting[\s]*blood[\s]*sugar",
        r"fasting[\s]*glucose",
        r"\bfbs\b",
        r"\bfpg\b",
    ],
    "Glucose (PP)": [
        r"glucose\s*\(?pp\)?",
        r"post[\s\-]*prandial[\s]*glucose",
        r"pp[\s]*blood[\s]*sugar",
        r"\bppbs\b",
        r"2\s*hr[\s]*pp",
    ],
    "Random Blood Sugar": [
        r"random[\s]*blood[\s]*sugar",
        r"\brbs\b",
        r"random[\s]*glucose",
        r"casual[\s]*blood[\s]*sugar",
    ],
    "INR": [
        r"\binr\b",
        r"international\s*normalized\s*ratio",
        r"inr\s*value",
        r"pt[\s]*inr",
    ],
    "Urea": [
        r"blood\s*urea",
        r"\burea\b",
        r"bun\b",
        r"blood\s*urea\s*nitrogen",
    ],
    "Uric Acid": [
        r"uric\s*acid",
        r"s\.?\s*uric\s*acid",
    ],
    "SGPT": [
        r"sgpt",
        r"\balt\b",
        r"alanine\s*aminotransferase",
        r"alanine\s*transaminase",
    ],
    "SGOT": [
        r"sgot",
        r"\bast\b",
        r"aspartate\s*aminotransferase",
        r"aspartate\s*transaminase",
    ],
    "TSH": [
        r"\btsh\b",
        r"thyroid\s*stimulating\s*hormone",
        r"thyrotropin",
    ],
    "T3": [
        r"\bt3\b",
        r"triiodothyronine",
        r"total\s*t3",
    ],
    "T4": [
        r"\bt4\b",
        r"thyroxine",
        r"total\s*t4",
    ],
    "HbA1c": [
        r"hba1c",
        r"hb\s*a1c",
        r"glycated\s*hemo",
        r"glycosylated\s*hemo",
        r"a1c",
    ],
    "Sodium": [
        r"\bsodium\b",
        r"\bna\+?\b",
        r"serum\s*sodium",
    ],
    "Potassium": [
        r"\bpotassium\b",
        r"\bk\+?\b",
        r"serum\s*potassium",
    ],
    "Calcium": [
        r"\bcalcium\b",
        r"\bca\+?\b",
        r"serum\s*calcium",
    ],
    "Vitamin D": [
        r"vitamin\s*d",
        r"25[\s\-]*oh[\s\-]*vitamin",
        r"25\s*hydroxy\s*vitamin",
        r"vit\.?\s*d",
    ],
    "Vitamin B12": [
        r"vitamin\s*b[\s\-]*12",
        r"vit\.?\s*b[\s\-]*12",
        r"cobalamin",
        r"cyanocobalamin",
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# VALUE EXTRACTOR — reads a numeric value from the line after the test name
# ─────────────────────────────────────────────────────────────────────────────
def _extract_value(line: str) -> float | None:
    """
    Extract the most likely medical value from a line.
    """

    nums = re.findall(r'\d+(?:\.\d+)?', line)

    if not nums:
        return None

    values = []

    for n in nums:
        try:
            values.append(float(n))
        except:
            pass

    if not values:
        return None

    for v in values:
        if 0.01 <= v <= 10000:
            return v

    return None


# ─────────────────────────────────────────────────────────────────────────────
# STATUS CHECKER
# ─────────────────────────────────────────────────────────────────────────────
def _get_status(test, value):

    if test == "INR":

        if value < 2:
            return "Low INR 🟡"

        elif value <= 3:
            return "Therapeutic Range ✅"

        else:
            return "High INR 🔴"

    elif test == "Glucose Fasting":

        if value < 70:
            return "Low Blood Sugar"

        elif value <= 99:
            return "Normal ✅"

        elif value <= 125:
            return "Pre-Diabetes ⚠"

        else:
            return "Diabetes Risk 🔴"

    elif test == "Glucose (PP)":

        if value < 140:
            return "Normal ✅"

        elif value <= 199:
            return "Pre-Diabetes ⚠"

        else:
            return "Diabetes Risk 🔴"

    elif test == "Random Blood Sugar":

        if value < 70:
            return "Low"

        elif value <= 140:
            return "Normal ✅"

        elif value <= 200:
            return "Pre-Diabetes ⚠"

        else:
            return "Diabetes Risk 🔴"

    elif test == "HbA1c":

        if value < 5.7:
            return "Normal ✅"

        elif value < 6.5:
            return "Pre-Diabetes ⚠"

        else:
            return "Diabetes 🔴"

    if test in REFERENCE_RANGES:

        low, high = REFERENCE_RANGES[test]

        if value < low:
            return "Low ⬇"

        elif value > high:
            return "High ⬆"

        else:
            return "Normal ✅"

    return "Unknown"
def get_doctor_comment(test, value):

    if test == "INR":

        if value < 2:
            return "INR is below therapeutic range. Risk of clot formation."

        elif value <= 3:
            return "INR is within therapeutic range."

        else:
            return "INR is above therapeutic range. Risk of bleeding."

    elif test == "Glucose Fasting":

        if value <= 99:
            return "Fasting glucose is within normal range."

        elif value <= 125:
            return "Prediabetic fasting glucose detected. Lifestyle modification advised."

        else:
            return "Diabetic range fasting glucose. Medical consultation recommended."

    elif test == "Glucose (PP)":

        if value < 140:
            return "Post meal glucose is normal." 

        elif value <= 199:
            return "Post meal glucose is elevated. Prediabetes risk."

        else:
            return "Post meal glucose is in diabetic range."

    elif test == "Random Blood Sugar":

        if value <= 140:
            return "Random blood sugar is normal."

        elif value <= 200:
            return "Random blood sugar is elevated."

        else:
            return "Random blood sugar suggests diabetes."

    elif test == "Creatinine":

        if value > 1.3:
            return "Creatinine is elevated. Kidney function monitoring advised."

        return "Creatinine is within normal range."

    elif test == "Hemoglobin":

        if value < 13:
            return "Hemoglobin is low. Possible anemia."

        return "Hemoglobin is within normal range."

    return "Report analyzed successfully."
# ─────────────────────────────────────────────────────────────────────────────
# MAIN FUNCTION
# ─────────────────────────────────────────────────────────────────────────────
def analyze_report(text: str) -> dict:
    """
    Scan the full extracted text for any known test names.
    Returns dict: { test_name: { value, status, unit } }
    """
    report = {}
    lines  = text.splitlines()

    for test_name, aliases in TEST_ALIASES.items():
        # Build one big regex from all aliases for this test
        combined = "(?:" + "|".join(aliases) + ")"
        pattern  = re.compile(combined, re.IGNORECASE)

        for i, line in enumerate(lines):
            if not pattern.search(line):
                continue

            print("\n======================")
            print("TEST :", test_name)
            print("LINE :", line)
            print("======================")

            # Try to find the value on the same line first
            value = _extract_value(line)

            # If not found on same line, check the next 1-2 lines
            if value is None and i + 1 < len(lines):
                value = _extract_value(lines[i + 1])
            if value is None and i + 2 < len(lines):
                value = _extract_value(lines[i + 2])

            if value is not None:
                print("\nFOUND:", test_name)
                print("LINE :", line)
                print("VALUE:", value)
                
                status = _get_status(test_name, value)

                # Extract unit if present
                unit_match = re.search(
                    r'\b(mg/dL|g/dL|g/L|mmol/L|mIU/L|IU/L|µIU/mL|ng/mL|pg/mL|%|cells/µL|/µL|cumm|fL)\b',
                    line + (lines[i+1] if i+1 < len(lines) else ""),
                    re.IGNORECASE
                )
                unit = unit_match.group(1) if unit_match else ""

                print("\nFOUND:", test_name)
                print("LINE :", line)
                print("VALUE:", value)

                report[test_name] = {
                    "value": value,
                    "status": status,
                    "comment": get_doctor_comment(test_name, value),
                    "unit": unit,
}
                break   # found this test, move to next

    return report
