import sqlite3

def create_sample_database():
    # Connect to SQLite database (creates it if it doesn't exist)
    conn = sqlite3.connect("company.db")
    cursor = conn.cursor()

    # Create a sample employees table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            salary INTEGER NOT NULL,
            hire_date TEXT NOT NULL
        )
    """)

    # Insert sample data
    sample_data = [
        ("Alice Smith", "Engineering", 95000, "2021-06-15"),
        ("Bob Jones", "Marketing", 65000, "2022-01-10"),
        ("Charlie Brown", "Engineering", 110000, "2020-11-05"),
        ("Diana Prince", "HR", 72000, "2023-03-20"),
        ("Evan Wright", "Marketing", 68000, "2023-07-11"),
        ("Fiona Gallagher", "Sales", 85000, "2019-09-01")
    ]
    
    cursor.executemany("""
        INSERT OR IGNORE INTO employees (name, department, salary, hire_date)
        VALUES (?, ?, ?, ?)
    """, sample_data)

    conn.commit()
    conn.close()
    print("Database 'company.db' created successfully with sample data!")

if __name__ == "__main__":
    create_sample_database()