import pandas as pd

def process_results(path):
    try:
        df = pd.read_csv(path)
    except Exception as e:
        raise ValueError(f"Cannot read CSV file: {e}")

    # Clean columns: roll_no stays roll_no, Math stays math
    df.columns = df.columns.str.strip().str.lower()
    
    # FIX 1: Don't use FIXED_COLS = 4. Detect by NAME, not position
    FIXED = ['roll_no', 'name', 'class', 'father_name']
    all_cols = df.columns.tolist()
    SUBJECTS = [c for c in all_cols if c not in FIXED]
    
    if len(SUBJECTS) == 0:
        raise ValueError(f"No subjects found. Your columns are: {all_cols}")

    required = ["roll_no", "name"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}. Your columns are: {all_cols}")

    # Validation (your code - keep same)
    if df["roll_no"].isnull().any() or (df["roll_no"].astype(str).str.strip() == "").any():
        raise ValueError("Empty roll_no found")

    if df["name"].isnull().any() or (df["name"].astype(str).str.strip() == "").any():
        raise ValueError("Empty name found")

    errors = []
    for subject in SUBJECTS:
        if df[subject].isnull().all():
            errors.append(f"Subject '{subject}' column is completely empty")
            continue
        for idx, value in df[subject].items():
            row_num = idx + 2
            if pd.isna(value) or str(value).strip() == "":
                errors.append(f"Row {row_num}: '{subject}' is empty for roll_no {df.loc[idx, 'roll_no']}")
                continue
            try:
                num = float(str(value).strip())
            except ValueError:
                errors.append(f"Row {row_num}: '{subject}' has text '{value}' instead of number")
                continue
            if num < 0 or num > 100:
                errors.append(f"Row {row_num}: '{subject}' has invalid marks {num}")
    if errors:
        raise ValueError("CSV Validation Failed:\n" + "\n".join(errors[:15]))

    # Calculate
    df[SUBJECTS] = df[SUBJECTS].apply(pd.to_numeric, errors="coerce")
    df["total"] = df[SUBJECTS].sum(axis=1)
    total_marks = len(SUBJECTS) * 100
    df["percentage"] = (df["total"] / total_marks * 100).round(2)
    df["grade"] = df["percentage"].apply(get_grade)
    df["result"] = df[SUBJECTS].min(axis=1).apply(lambda m: "Pass" if m >= 40 else "Fail")
    df["rank"] = df["total"].rank(ascending=False, method="min").astype(int)

    return df

def get_grade(p):
    if p >= 90: return "A+"
    if p >= 80: return "A"
    if p >= 70: return "B"
    if p >= 60: return "C"
    if p >= 40: return "D"
    return "F"