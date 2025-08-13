import sqlite3

DDL = [
    """
    CREATE TABLE IF NOT EXISTS providers (
        Provider_ID INTEGER PRIMARY KEY,
        Name TEXT NOT NULL,
        Type TEXT,
        Address TEXT,
        City TEXT,
        Contact TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS receivers (
        Receiver_ID INTEGER PRIMARY KEY,
        Name TEXT NOT NULL,
        Type TEXT,
        City TEXT,
        Contact TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS food_listings (
        Food_ID INTEGER PRIMARY KEY,
        Food_Name TEXT NOT NULL,
        Quantity INTEGER CHECK(Quantity >= 0),
        Expiry_Date TEXT,
        Provider_ID INTEGER,
        Provider_Type TEXT,
        Location TEXT,
        Food_Type TEXT,
        Meal_Type TEXT,
        FOREIGN KEY (Provider_ID) REFERENCES providers(Provider_ID)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS claims (
        Claim_ID INTEGER PRIMARY KEY,
        Food_ID INTEGER,
        Receiver_ID INTEGER,
        Status TEXT CHECK(Status IN ('Pending','Completed','Cancelled')),
        Timestamp TEXT,
        FOREIGN KEY (Food_ID) REFERENCES food_listings(Food_ID),
        FOREIGN KEY (Receiver_ID) REFERENCES receivers(Receiver_ID)
    );
    """
]

def create_tables(db_path="db/food_wastage.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    for stmt in DDL:
        cur.execute(stmt)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()
    print("Tables created successfully.")
