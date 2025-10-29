from flask import Blueprint, request, jsonify
import sqlite3
import sys
import os

journal_bp = Blueprint('journal', __name__)

def get_db_connection():
    """Get database connection using the same database as the web application"""
    # Use the same database path as defined in main.py
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'media_organizer.db')
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None

def get_timezone_offset_sql():
    """Get SQLite timezone offset modifier from config"""
    conn = get_db_connection()
    if not conn:
        return '+8 hours'  # Default fallback
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM config WHERE key = 'offsetTime'")
        result = cursor.fetchone()
        offset_time = result[0] if result else '+08:00'
        conn.close()
        
        # Convert offset like '+08:00' to SQLite modifier like '+8 hours'
        if offset_time.startswith('+') or offset_time.startswith('-'):
            sign = offset_time[0]
            hours = int(offset_time[1:3])
            minutes = int(offset_time[4:6])
            if minutes == 0:
                return f'{sign}{hours} hours'
            else:
                total_hours = hours + (minutes / 60.0)
                return f'{sign}{total_hours} hours'
        return '+8 hours'  # Default fallback
    except:
        if conn:
            conn.close()
        return '+8 hours'  # Default fallback
    """Convert offset like '+08:00' to SQLite datetime modifier like '+8 hours'"""
    try:
        # Parse offset like '+08:00' or '-04:00'
        if offset_time.startswith('+') or offset_time.startswith('-'):
            sign = offset_time[0]
            hours = int(offset_time[1:3])
            minutes = int(offset_time[4:6])
            
            # Convert to total hours (including fractional for minutes)
            total_hours = hours + (minutes / 60.0)
            
            # Create SQLite modifier
            if minutes == 0:
                return f'{sign}{hours} hours'
            else:
                return f'{sign}{total_hours} hours'
        return '+8 hours'  # Default fallback
    except:
        return '+8 hours'  # Default fallback

def ensure_journal_table():
    """Ensure the journal table exists in the database"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
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
        return True
    except sqlite3.Error as e:
        print(f"Error creating journal table: {e}")
        return False
    finally:
        conn.close()

@journal_bp.route('/api/journal/entries', methods=['GET'])
def get_all_journal_entries():
    """Get all journal entries, optionally filtered by date range"""
    try:
        ensure_journal_table()  # Make sure table exists
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Get timezone offset and convert to SQLite modifier
        sqlite_offset = get_timezone_offset_sql()
        print(f"🕐 Using timezone offset SQLite modifier: {sqlite_offset}")
        
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        cursor = conn.cursor()
        
        if date_from and date_to:
            cursor.execute(f"""
                SELECT j.*, 
                       COALESCE(m.media_count, 0) as media_count
                FROM journal j
                LEFT JOIN (
                    SELECT DATE(creation_time, '{sqlite_offset}') as date, COUNT(*) as media_count
                    FROM media_files 
                    WHERE creation_time IS NOT NULL
                    GROUP BY DATE(creation_time, '{sqlite_offset}')
                ) m ON j.date = m.date
                WHERE j.date >= ? AND j.date <= ? 
                ORDER BY j.date ASC, j.id ASC
            """, (date_from, date_to))
        elif date_from:
            cursor.execute(f"""
                SELECT j.*, 
                       COALESCE(m.media_count, 0) as media_count
                FROM journal j
                LEFT JOIN (
                    SELECT DATE(creation_time, '{sqlite_offset}') as date, COUNT(*) as media_count
                    FROM media_files 
                    WHERE creation_time IS NOT NULL
                    GROUP BY DATE(creation_time, '{sqlite_offset}')
                ) m ON j.date = m.date
                WHERE j.date >= ? 
                ORDER BY j.date ASC, j.id ASC
            """, (date_from,))
        else:
            cursor.execute(f"""
                SELECT j.*, 
                       COALESCE(m.media_count, 0) as media_count
                FROM journal j
                LEFT JOIN (
                    SELECT DATE(creation_time, '{sqlite_offset}') as date, COUNT(*) as media_count
                    FROM media_files 
                    WHERE creation_time IS NOT NULL
                    GROUP BY DATE(creation_time, '{sqlite_offset}')
                ) m ON j.date = m.date
                ORDER BY j.date ASC, j.id ASC
            """)
        
        rows = cursor.fetchall()
        conn.close()
        
        # Convert rows to dictionaries
        entries = []
        for row in rows:
            entry = {
                'id': row['id'],
                'date': row['date'],
                'time_range': row['time_range'],
                'comment': row['comment'],
                'city_en': row['city_en'],
                'city_zh': row['city_zh'],
                'country_en': row['country_en'],
                'country_zh': row['country_zh'],
                'latitude': row['latitude'],
                'longitude': row['longitude'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at'],
                'media_count': row['media_count']
            }
            entries.append(entry)
        
        return jsonify(entries)
    
    except Exception as e:
        print(f"Error getting journal entries: {e}")
        return jsonify({'error': 'Failed to retrieve journal entries'}), 500

@journal_bp.route('/api/journal/entries', methods=['POST'])
def create_journal_entry():
    """Create a new journal entry"""
    try:
        data = request.get_json()
        
        if not data or not data.get('date'):
            return jsonify({'error': 'Date is required'}), 400
        
        ensure_journal_table()  # Make sure table exists
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO journal (date, time_range, comment, city_en, city_zh, 
                                country_en, country_zh, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['date'],
            data.get('time_range'),
            data.get('comment'),
            data.get('city_en'),
            data.get('city_zh'),
            data.get('country_en'),
            data.get('country_zh'),
            data.get('latitude'),
            data.get('longitude')
        ))
        
        entry_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'id': entry_id, 'message': 'Journal entry created successfully'}), 201
    
    except Exception as e:
        print(f"Error creating journal entry: {e}")
        return jsonify({'error': 'Failed to create journal entry'}), 500

@journal_bp.route('/api/journal/entries/<int:entry_id>', methods=['GET'])
def get_journal_entry(entry_id):
    """Get a specific journal entry by ID"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM journal WHERE id = ?", (entry_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            entry = {
                'id': row['id'],
                'date': row['date'],
                'time_range': row['time_range'],
                'comment': row['comment'],
                'city_en': row['city_en'],
                'city_zh': row['city_zh'],
                'country_en': row['country_en'],
                'country_zh': row['country_zh'],
                'latitude': row['latitude'],
                'longitude': row['longitude'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }
            return jsonify(entry)
        else:
            return jsonify({'error': 'Journal entry not found'}), 404
    
    except Exception as e:
        print(f"Error getting journal entry: {e}")
        return jsonify({'error': 'Failed to retrieve journal entry'}), 500

@journal_bp.route('/api/journal/entries/<int:entry_id>', methods=['PUT'])
def update_journal_entry_route(entry_id):
    """Update an existing journal entry"""
    try:
        data = request.get_json()
        
        if not data or not data.get('date'):
            return jsonify({'error': 'Date is required'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE journal 
            SET date = ?, time_range = ?, comment = ?, city_en = ?, city_zh = ?,
                country_en = ?, country_zh = ?, latitude = ?, longitude = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            data['date'],
            data.get('time_range'),
            data.get('comment'),
            data.get('city_en'),
            data.get('city_zh'),
            data.get('country_en'),
            data.get('country_zh'),
            data.get('latitude'),
            data.get('longitude'),
            entry_id
        ))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if success:
            return jsonify({'message': 'Journal entry updated successfully'})
        else:
            return jsonify({'error': 'Journal entry not found or update failed'}), 404
    
    except Exception as e:
        print(f"Error updating journal entry: {e}")
        return jsonify({'error': 'Failed to update journal entry'}), 500

@journal_bp.route('/api/journal/sync', methods=['POST'])
def sync_with_media_dates():
    """Sync journal table with unique dates from media files"""
    try:
        ensure_journal_table()  # Make sure table exists
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Get timezone offset SQLite modifier
        sqlite_offset = get_timezone_offset_sql()
        print(f"🕐 SYNC: Using timezone offset SQLite modifier: {sqlite_offset}")
        
        cursor = conn.cursor()
        
        # Get unique dates from media files using timezone-aware date extraction
        cursor.execute(f"""
            SELECT DISTINCT DATE(creation_time, '{sqlite_offset}') as date 
            FROM media_files 
            WHERE creation_time IS NOT NULL 
            AND DATE(creation_time, '{sqlite_offset}') IS NOT NULL
            ORDER BY date DESC
        """)
        
        media_dates = [row[0] for row in cursor.fetchall()]
        
        if not media_dates:
            conn.close()
            return jsonify({'added_entries': 0, 'message': 'No media dates found'})
        
        # Get existing journal dates
        cursor.execute("SELECT DISTINCT date FROM journal")
        existing_journal_dates = {row[0] for row in cursor.fetchall()}
        
        # Find dates that need to be added to journal
        dates_to_add = [date for date in media_dates if date and date not in existing_journal_dates]
        
        # Insert missing dates into journal table
        added_count = 0
        for date in dates_to_add:
            if not date:  # Skip None or empty dates
                continue
            try:
                cursor.execute("""
                    INSERT INTO journal (date) VALUES (?)
                """, (date,))
                added_count += 1
            except sqlite3.Error as e:
                print(f"Error inserting date {date}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'added_entries': added_count,
            'total_media_dates': len(media_dates),
            'existing_journal_dates': len(existing_journal_dates),
            'message': f'Successfully added {added_count} new journal entries'
        })
    
    except Exception as e:
        print(f"Error syncing with media dates: {e}")
        return jsonify({'error': 'Failed to sync with media dates'}), 500

@journal_bp.route('/api/journal/dates', methods=['GET'])
def get_media_dates():
    """Get all unique dates from media files for reference"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT DATE(creation_time) as date, COUNT(*) as media_count
            FROM media_files 
            WHERE creation_time IS NOT NULL 
            GROUP BY DATE(creation_time)
            ORDER BY date DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        dates = [{'date': row[0], 'media_count': row[1]} for row in rows]
        
        return jsonify(dates)
    
    except Exception as e:
        print(f"Error getting media dates: {e}")
        return jsonify({'error': 'Failed to retrieve media dates'}), 500

@journal_bp.route('/api/journal/debug/<date>', methods=['GET'])
def debug_media_count_for_date(date):
    """Debug endpoint to show detailed media count calculation for a specific date"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Get timezone offset SQLite modifier
        sqlite_offset = get_timezone_offset_sql()
        
        cursor = conn.cursor()
        
        print(f"🔍 DEBUG: Investigating media count for date: {date}")
        print(f"🕐 Using timezone offset SQLite modifier: {sqlite_offset}")
        
        # 1. Get all media files with their creation_time and both raw and timezone-aware dates
        cursor.execute(f"""
            SELECT id, filename, creation_time, 
                   DATE(creation_time) as raw_date,
                   DATE(creation_time, '{sqlite_offset}') as timezone_aware_date,
                   filepath
            FROM media_files 
            WHERE creation_time IS NOT NULL
            ORDER BY creation_time
        """)
        all_files = cursor.fetchall()
        
        # 2. Filter files for the specific date (using timezone-aware date)
        target_date_files = []
        for file_row in all_files:
            if file_row[4] == date:  # timezone_aware_date matches
                target_date_files.append(file_row)
        
        # 3. Get the exact SQL query result used in journal (timezone-aware)
        cursor.execute(f"""
            SELECT DATE(creation_time, '{sqlite_offset}') as date, COUNT(*) as media_count
            FROM media_files 
            WHERE creation_time IS NOT NULL AND DATE(creation_time, '{sqlite_offset}') = ?
            GROUP BY DATE(creation_time, '{sqlite_offset}')
        """, (date,))
        
        sql_result = cursor.fetchone()
        
        # 4. Show timezone examples
        cursor.execute(f"""
            SELECT DISTINCT creation_time, 
                   DATE(creation_time) as raw_date,
                   DATE(creation_time, '{sqlite_offset}') as timezone_aware_date
            FROM media_files 
            WHERE DATE(creation_time, '{sqlite_offset}') = ?
            LIMIT 5
        """, (date,))
        
        sample_times = cursor.fetchall()
        
        conn.close()
        
        debug_info = {
            'requested_date': date,
            'timezone_config': {
                'sqlite_modifier': sqlite_offset
            },
            'sql_query_result': {
                'date': sql_result[0] if sql_result else None,
                'count': sql_result[1] if sql_result else 0
            },
            'manual_count': len(target_date_files),
            'files_found': [
                {
                    'id': f[0],
                    'filename': f[1], 
                    'creation_time': f[2],
                    'raw_date': f[3],
                    'timezone_aware_date': f[4],
                    'filepath': f[5]
                }
                for f in target_date_files
            ],
            'sample_creation_times': [
                {
                    'creation_time': t[0],
                    'raw_date': t[1], 
                    'timezone_aware_date': t[2]
                }
                for t in sample_times
            ],
            'total_files_in_db': len(all_files),
            'debug_explanation': {
                'DATE_function': f"SQLite DATE() function with '{sqlite_offset}' modifier for timezone-aware date extraction",
                'timezone_handling': f"Using configured timezone offset to convert timestamps to local dates",
                'count_logic': "COUNT(*) counts all rows where timezone-aware DATE() matches the target date"
            }
        }
        
        print(f"📊 DEBUG RESULT for {date} (timezone-aware):")
        print(f"  SQL COUNT: {debug_info['sql_query_result']['count']}")
        print(f"  Manual COUNT: {debug_info['manual_count']}")
        print(f"  Files found: {len(target_date_files)}")
        for i, f in enumerate(target_date_files, 1):
            print(f"    {i}. {f[1]} | {f[2]} -> raw: {f[3]}, tz-aware: {f[4]}")
        
        return jsonify(debug_info)
        
    except Exception as e:
        print(f"Error in debug endpoint: {e}")
        return jsonify({'error': str(e)}), 500