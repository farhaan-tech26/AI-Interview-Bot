import sqlite3


DATABASE = "database/interview.db"


def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def create_tables():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interviews (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            category TEXT NOT NULL,

            difficulty TEXT NOT NULL,

            total_score REAL DEFAULT 0,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS answers (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            interview_id INTEGER,

            question TEXT,

            answer TEXT,

            feedback TEXT,

            score REAL,

            FOREIGN KEY(interview_id)
            REFERENCES interviews(id)

        )
    """)


    connection.commit()

    connection.close()