import sqlite3
import pandas as pd
from data import process_results

DB_NAME = 'results.db'

def get_db():
    # Establish SQLite database connection
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Initialize database tables if needed
    conn = get_db()
    cur = conn.cursor()
    # Create students table schema
    cur.execute("""CREATE TABLE IF NOT EXISTS students (
        roll_no INTEGER PRIMARY KEY, name TEXT NOT NULL, class INTEGER, father_name TEXT,
        total INTEGER, percentage REAL, grade TEXT, result TEXT)""")
    # Create subjects table schema
    cur.execute("""CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE)""")
    # Create results table schema
    cur.execute("""CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT, roll_no INTEGER, subject_id INTEGER, marks INTEGER,
        FOREIGN KEY(roll_no) REFERENCES students(roll_no),
        FOREIGN KEY(subject_id) REFERENCES subjects(id))""")
    conn.commit()
    conn.close()

def save_results_to_db(df):
    # Exit early if dataframe is empty
    if df is None or df.empty:
        print("No data to save!")
        return

    NON_SUBJECTS = ['roll_no', 'name', 'class', 'father_name', 'total', 'percentage', 'grade', 'result']
    # Extract dynamic subject column names
    SUBJECTS = [c for c in df.columns if c not in NON_SUBJECTS]
    print(f"Real subjects found: {SUBJECTS}")

    init_db()
    conn = get_db()
    cur = conn.cursor()

    # Iterate through each row in dataframe
    for _, row in df.iterrows():
        roll_no = int(float(row['roll_no']))
        name = str(row['name'])
        clas = int(float(row['class'])) if 'class' in df.columns and pd.notna(row['class']) else 0
        father = str(row['father_name']) if 'father_name' in df.columns else ""
        total = int(float(row['total'])) if 'total' in df.columns else 0
        perc = float(row['percentage']) if 'percentage' in df.columns else 0
        grade = str(row['grade']) if 'grade' in df.columns else ""
        result = str(row['result']) if 'result' in df.columns else ""
       
        # Insert or update student record
        cur.execute("""INSERT OR REPLACE INTO students 
            (roll_no, name, class, father_name, total, percentage, grade, result) 
            VALUES (?,?,?,?,?,?,?,?)""", 
            (roll_no, name, clas, father, total, perc, grade, result))

        # Loop through each subject column
        for sub in SUBJECTS:
            marks_val = row[sub]
            # Skip missing subject marks
            if pd.isna(marks_val) or str(marks_val).strip() == '':
                continue
            marks = int(float(marks_val))
            subject_name = sub.capitalize()
            # Insert new subject if not exists
            cur.execute("INSERT OR IGNORE INTO subjects (name) VALUES (?)", (subject_name,))
            # Fetch subject primary key ID
            cur.execute("SELECT id FROM subjects WHERE name=?", (subject_name,))
            sub_id = cur.fetchone()[0]
            # Remove old result entry for student
            cur.execute("DELETE FROM results WHERE roll_no=? AND subject_id=?", (roll_no, sub_id))
            # Insert current subject mark entry
            cur.execute("INSERT INTO results (roll_no, subject_id, marks) VALUES (?,?,?)", (roll_no, sub_id, marks))

    conn.commit()
    conn.close()
    print(f"✅ Saved {len(df)} students successfully!")