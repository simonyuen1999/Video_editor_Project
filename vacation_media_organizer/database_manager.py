
import sqlite3

DATABASE_NAME = "media_library.db"

def create_connection():
    """ Create a database connection to the SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        return conn
    except sqlite3.Error as e:
        print(e)
    return conn

def create_table(conn):
    """ Create media table if it doesn't exist """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_path TEXT NOT NULL,
                new_path TEXT NOT NULL,
                creation_date TEXT,
                creation_time TEXT,
                latitude REAL,
                longitude REAL,
                city TEXT,
                country TEXT,
                people_count INTEGER,
                activities TEXT, -- Stored as JSON string or comma-separated
                scenery TEXT,    -- Stored as JSON string or comma-separated
                talking_detected BOOLEAN
            );
        """)
        conn.commit()
    except sqlite3.Error as e:
        print(e)

def insert_media_record(conn, record):
    """ Insert a new media record into the media table """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO media (original_path, new_path, creation_date, creation_time, 
                               latitude, longitude, city, country, people_count, 
                               activities, scenery, talking_detected)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            record["original_path"],
            record["new_path"],
            record["creation_date"],
            record["creation_time"],
            record["latitude"],
            record["longitude"],
            record["city"],
            record["country"],
            record["people_count"],
            str(record["activities"]), # Convert list to string for storage
            str(record["scenery"]),    # Convert list to string for storage
            record["talking_detected"]
        ))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(e)
    return None

def get_all_media_records(conn):
    """ Retrieve all media records from the database """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM media;")
        rows = cursor.fetchall()
        return rows
    except sqlite3.Error as e:
        print(e)
    return []

if __name__ == '__main__':
    conn = create_connection()
    if conn:
        create_table(conn)
        print("Database and table created successfully.")

        # Example usage:
        sample_record = {
            "original_path": "/tmp/test_media/img.jpg",
            "new_path": "/media_library/2023/10/27/img.jpg",
            "creation_date": "2023-10-27",
            "creation_time": "10:30:00",
            "latitude": 34.0522,
            "longitude": -118.2437,
            "city": "Los Angeles",
            "country": "USA",
            "people_count": 2,
            "activities": ["walking"],
            "scenery": ["city_walk"],
            "talking_detected": False
        }
        record_id = insert_media_record(conn, sample_record)
        if record_id:
            print(f"Inserted record with ID: {record_id}")

        print("\nAll media records:")
        records = get_all_media_records(conn)
        for record in records:
            print(record)

        conn.close()


