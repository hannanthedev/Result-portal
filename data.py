import pandas as pd  # pandas handles table data (CSV reading, math)

def process_results(file_obj):  # reads, validates, and calculates results from CSV
    # file_obj can be the uploaded file from Flask, no need to save it
    try:  # catch any problem while reading the file
        df = pd.read_csv(file_obj)  # load the CSV into a table (df = DataFrame)
    except Exception as e:  # file is broken or not a valid CSV
        raise ValueError(f"Cannot read CSV file: {e}")  # re-raise with a clear message

    # Clean columns: roll_no stays roll_no, Math stays math
    df.columns = df.columns.str.strip().str.lower()  # remove extra spaces and make names lowercase
    
    # FIX 1: Don't use FIXED_COLS = 4. Detect by NAME, not position
    FIXED = ['roll_no', 'name', 'class', 'father_name']  # non-subject columns
    all_cols = df.columns.tolist()  # list of all column names in the file
    SUBJECTS = [c for c in all_cols if c not in FIXED]  # every other column is a subject
    
    if len(SUBJECTS) == 0:  # file has only info columns, no marks
        raise ValueError(f"No subjects found. Your columns are: {all_cols}")  # stop with an error

    required = ["roll_no", "name"]  # columns that must exist
    missing = [c for c in required if c not in df.columns]  # find which required ones are absent
    if missing:  # at least one is absent
        raise ValueError(f"Missing required columns: {missing}. Your columns are: {all_cols}")  # stop with an error

    # Validation (your code - keep same)
    # reject if any roll_no is null or blank after trimming spaces
    if df["roll_no"].isnull().any() or (df["roll_no"].astype(str).str.strip() == "").any():
        raise ValueError("Empty roll_no found")

    # reject if any name is null or blank after trimming spaces
    if df["name"].isnull().any() or (df["name"].astype(str).str.strip() == "").any():
        raise ValueError("Empty name found")

    errors = []  # collect all problems so the user sees them together
    for subject in SUBJECTS:  # check each subject column
        if df[subject].isnull().all():  # whole column has no values
            errors.append(f"Subject '{subject}' column is completely empty")  # record the problem
            continue  # skip checking its rows
        for idx, value in df[subject].items():  # go through every mark in this subject
            row_num = idx + 2  # +2 matches the Excel row (header is row 1, index starts at 0)
            if pd.isna(value) or str(value).strip() == "":  # mark is missing or blank
                errors.append(f"Row {row_num}: '{subject}' is empty for roll_no {df.loc[idx, 'roll_no']}")  # record it
                continue  # move to the next mark
            try:  # test whether the mark is a number
                num = float(str(value).strip())  # convert text to a number
            except ValueError:  # conversion failed, so it's text like "abc"
                errors.append(f"Row {row_num}: '{subject}' has text '{value}' instead of number")  # record it
                continue  # move to the next mark
            if num < 0 or num > 100:  # marks must be between 0 and 100
                errors.append(f"Row {row_num}: '{subject}' has invalid marks {num}")  # record it
    if errors:  # at least one problem was found
        raise ValueError("CSV Validation Failed:\n" + "\n".join(errors[:15]))  # show only the first 15 errors

    # Calculate
    df[SUBJECTS] = df[SUBJECTS].apply(pd.to_numeric, errors="coerce")  # turn all marks into real numbers
    df["total"] = df[SUBJECTS].sum(axis=1)  # add up marks across subjects for each student
    total_marks = len(SUBJECTS) * 100  # maximum possible marks (100 per subject)
    df["percentage"] = (df["total"] / total_marks * 100).round(2)  # percentage rounded to 2 decimals
    df["grade"] = df["percentage"].apply(get_grade)  # convert each percentage to a grade letter
    # Pass only if the lowest subject mark is 40 or more
    df["result"] = df[SUBJECTS].min(axis=1).apply(lambda m: "Pass" if m >= 40 else "Fail")


    return df  # send the finished table back to app.py

def get_grade(p):  # converts a percentage into a grade letter
    if p >= 90: return "A+"  # 90 and above
    if p >= 80: return "A"  # 80 to 89
    if p >= 70: return "B"  # 70 to 79
    if p >= 60: return "C"  # 60 to 69
    if p >= 40: return "D"  # 40 to 59
    return "F"  # below 40 means fail