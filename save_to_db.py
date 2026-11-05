import sqlite3  # built-in Python tool for SQLite databases
import pandas as pd  # used here to check for empty (NaN) values
from data import process_results  # imported but not used in this file

DB_NAME = 'results.db'  # name of the database file

def get_db():  # opens and returns a database connection
    conn = sqlite3.connect(DB_NAME)  # connect to the file (creates it if missing)
    conn.row_factory = sqlite3.Row  # rows can be read by column name, like row['name']
    return conn  # give the connection to the caller

def init_db():  # creates the three tables if they don't exist
    conn = get_db()  # open the database
    cur = conn.cursor()  # cursor is used to run SQL commands
    # students table: one row per student, roll_no is the unique ID
    # NOTE: the last column has no name (" INTEGER"), which will cause an SQL error
    cur.execute("""CREATE TABLE IF NOT EXISTS students (
        roll_no INTEGER PRIMARY KEY, name TEXT NOT NULL, class INTEGER, father_name TEXT,
        total INTEGER, percentage REAL, grade TEXT, result TEXT,  INTEGER)""")
    # subjects table: one row per subject name, no duplicates allowed
    cur.execute("""CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE)""")
    # results table: marks of each student in each subject, links the two tables above
    cur.execute("""CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT, roll_no INTEGER, subject_id INTEGER, marks INTEGER,
        FOREIGN KEY(roll_no) REFERENCES students(roll_no),
        FOREIGN KEY(subject_id) REFERENCES subjects(id))""")
    conn.commit()  # save the table changes
    conn.close()  # close the connection

def save_results_to_db(df):  # saves the processed table into the database
    if df is None or df.empty:  # nothing was given, or the table has no rows
        print("No data to save!")  # tell the developer in the console
        return  # stop here

    # FIX 2: Exclude computed columns + father_name from subjects
    # columns that are NOT subjects
    NON_SUBJECTS = ['roll_no', 'name', 'class', 'father_name', 'total', 'percentage', 'grade', 'result']
    SUBJECTS = [c for c in df.columns if c not in NON_SUBJECTS]  # everything else is a subject
    print(f"Real subjects found: {SUBJECTS}")  # show the subjects in the console

    init_db()  # make sure the tables exist
    conn = get_db()  # open the database
    cur = conn.cursor()  # cursor to run SQL

    for _, row in df.iterrows():  # go through each student row one by one
        roll_no = int(float(row['roll_no']))  # roll number as a whole number
        name = str(row['name'])  # student name as text
        # class as a number, or 0 if the column or value is missing
        clas = int(float(row['class'])) if 'class' in df.columns and pd.notna(row['class']) else 0
        father = str(row['father_name']) if 'father_name' in df.columns else ""  # father name, or empty
        total = int(float(row['total'])) if 'total' in df.columns else 0  # total marks, or 0
        perc = float(row['percentage']) if 'percentage' in df.columns else 0  # percentage, or 0
        grade = str(row['grade']) if 'grade' in df.columns else ""  # grade letter, or empty
        result = str(row['result']) if 'result' in df.columns else ""  # Pass/Fail, or empty
       
        # 1. Save student WITH total/percentage/grade
        # INSERT OR REPLACE overwrites the student if the roll_no already exists
        # NOTE: 9 "?" placeholders but only 8 columns and 8 values, which will cause an error
        cur.execute("""INSERT OR REPLACE INTO students 
            (roll_no, name, class, father_name, total, percentage, grade, result) 
            VALUES (?,?,?,?,?,?,?,?,?)""", 
            (roll_no, name, clas, father, total, perc, grade, result))

        # 2. Save each subject
        for sub in SUBJECTS:  # go through every subject column
            marks_val = row[sub]  # this student's mark in the subject
            if pd.isna(marks_val) or str(marks_val).strip() == '':  # mark is blank
                continue  # skip it
            marks = int(float(marks_val))  # marks as a whole number
            subject_name = sub.capitalize()  # "math" becomes "Math"
            cur.execute("INSERT OR IGNORE INTO subjects (name) VALUES (?)", (subject_name,))  # add subject if new
            cur.execute("SELECT id FROM subjects WHERE name=?", (subject_name,))  # find the subject's ID
            sub_id = cur.fetchone()[0]  # take the ID from the result
            cur.execute("DELETE FROM results WHERE roll_no=? AND subject_id=?", (roll_no, sub_id))  # remove old mark to avoid duplicates
            cur.execute("INSERT INTO results (roll_no, subject_id, marks) VALUES (?,?,?)", (roll_no, sub_id, marks))  # save the new mark

    conn.commit()  # save all changes to the file
    conn.close()  # close the connection
    print(f"✅ Saved {len(df)} students successfully!")  # confirm in the console