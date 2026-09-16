import sqlite3

DATABASE = "database.db"

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS beneficiaries(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                national_id TEXT UNIQUE
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS medicines(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                stock_quantity INTEGER NOT NULL DEFAULT 0
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS beneficiary_medicines(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                beneficiary_id INTEGER NOT NULL,
                medicine_id INTEGER NOT NULL,
                monthly_quantity INTEGER NOT NULL,

                FOREIGN KEY (beneficiary_id) REFERENCES beneficiaries(id),
                FOREIGN KEY (medicine_id) REFERENCES medicines(id)
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dispenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                beneficiary_id INTEGER NOT NULL,
                dispense_year INTEGER NOT NULL,
                dispense_month INTEGER NOT NULL,
                dispense_day INTEGER,

                UNIQUE(beneficiary_id, dispense_month, dispense_year),
                FOREIGN KEY (beneficiary_id) REFERENCES beneficiaries(id)
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dispense_items(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dispense_id INTEGER NOT NULL,
                medicine_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,

                FOREIGN KEY (dispense_id) REFERENCES dispenses(id),
                FOREIGN KEY (medicine_id) REFERENCES medicines(id)
            )
        """)

        conn.commit()
