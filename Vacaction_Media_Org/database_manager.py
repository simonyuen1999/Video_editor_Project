
import sqlite3

''' Database Manager for Media and Journal Entries '''
''' PREVIOUS design without zh info in the DB '''

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
    """ Create media and journal tables if they don't exist """
    try:
        cursor = conn.cursor()
        
        # Create media table
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
        
        # Create journal table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS journal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                time_range TEXT,
                comment TEXT,
                city_en TEXT,
                city_zh TEXT,
                country_en TEXT,
                country_zh TEXT,
                latitude REAL,
                longitude REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

# Journal Table Management Functions

def insert_journal_entry(conn, entry):
    """ Insert a new journal entry into the journal table """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO journal (date, time_range, comment, city_en, city_zh, 
                                country_en, country_zh, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            entry["date"],
            entry.get("time_range"),
            entry.get("comment"),
            entry.get("city_en"),
            entry.get("city_zh"),
            entry.get("country_en"),
            entry.get("country_zh"),
            entry.get("latitude"),
            entry.get("longitude")
        ))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Error inserting journal entry: {e}")
    return None

def get_journal_entries(conn, date_from=None, date_to=None):
    """ Retrieve journal entries, optionally filtered by date range """
    try:
        cursor = conn.cursor()
        if date_from and date_to:
            cursor.execute("""
                SELECT * FROM journal 
                WHERE date >= ? AND date <= ? 
                ORDER BY date DESC, id DESC;
            """, (date_from, date_to))
        elif date_from:
            cursor.execute("""
                SELECT * FROM journal 
                WHERE date >= ? 
                ORDER BY date DESC, id DESC;
            """, (date_from,))
        else:
            cursor.execute("SELECT * FROM journal ORDER BY date DESC, id DESC;")
        
        rows = cursor.fetchall()
        return rows
    except sqlite3.Error as e:
        print(f"Error retrieving journal entries: {e}")
    return []

def get_journal_entry_by_id(conn, entry_id):
    """ Retrieve a specific journal entry by ID """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM journal WHERE id = ?;", (entry_id,))
        row = cursor.fetchone()
        return row
    except sqlite3.Error as e:
        print(f"Error retrieving journal entry: {e}")
    return None

def update_journal_entry(conn, entry_id, entry):
    """ Update an existing journal entry """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE journal 
            SET date = ?, time_range = ?, comment = ?, city_en = ?, city_zh = ?,
                country_en = ?, country_zh = ?, latitude = ?, longitude = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
        """, (
            entry["date"],
            entry.get("time_range"),
            entry.get("comment"),
            entry.get("city_en"),
            entry.get("city_zh"),
            entry.get("country_en"),
            entry.get("country_zh"),
            entry.get("latitude"),
            entry.get("longitude"),
            entry_id
        ))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error updating journal entry: {e}")
    return False

def delete_journal_entry(conn, entry_id):
    """ Delete a journal entry by ID """
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM journal WHERE id = ?;", (entry_id,))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error deleting journal entry: {e}")
    return False

def get_journal_entries_by_date(conn, date):
    """ Retrieve all journal entries for a specific date """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM journal 
            WHERE date = ? 
            ORDER BY time_range, id;
        """, (date,))
        rows = cursor.fetchall()
        return rows
    except sqlite3.Error as e:
        print(f"Error retrieving journal entries for date: {e}")
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

        # Example journal usage:
        sample_journal_entry = {
            "date": "2023-10-27",
            "time_range": "09:00-12:00",
            "comment": "Morning hike in Griffith Park. Beautiful weather and great views of the city.",
            "city_en": "Los Angeles",
            "city_zh": "洛杉矶",
            "country_en": "United States", 
            "country_zh": "美国",
            "latitude": 34.1362,
            "longitude": -118.2942
        }
        
        journal_id = insert_journal_entry(conn, sample_journal_entry)
        if journal_id:
            print(f"\nInserted journal entry with ID: {journal_id}")

        print("\nAll journal entries:")
        journal_entries = get_journal_entries(conn)
        for entry in journal_entries:
            print(entry)

        conn.close()


