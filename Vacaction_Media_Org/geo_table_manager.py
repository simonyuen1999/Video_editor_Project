#!/usr/bin/env python3
"""
Geo Table Management Utility

This script provides utilities for managing the geo_data table in the media organizer database.
It can populate the table from geo_chinese_.list file and perform various geo table operations.

Usage examples:
    python geo_table_manager.py --populate                 # Populate geo table
    python geo_table_manager.py --count                    # Show record count
    python geo_table_manager.py --sample 20                # Show sample records
    python geo_table_manager.py --clear                    # Clear all geo data
    python geo_table_manager.py --stats                    # Show table statistics
"""

import os
import sys
import argparse
import logging
import sqlite3
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class GeoTableManager:
    def __init__(self, db_path='media_organizer.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._connect()
        self._ensure_table_exists()

    def _connect(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            logging.info(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            logging.error(f"Database connection error: {e}")
            sys.exit(1)

    def _ensure_table_exists(self):
        """Ensure the geo_data table exists."""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS geo_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    city_en TEXT NOT NULL,
                    city_zh TEXT NOT NULL,
                    region_en TEXT,
                    region_zh TEXT,
                    subregion_en TEXT,
                    subregion_zh TEXT,
                    country_code TEXT NOT NULL,
                    country_en TEXT NOT NULL,
                    country_zh TEXT NOT NULL,
                    timezone TEXT,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(city_en, country_en, latitude, longitude)
                )
            ''')
            
            # Create indexes for faster lookups
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_geo_coords ON geo_data (latitude, longitude)
            ''')
            
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_geo_city_country ON geo_data (city_en, country_en)
            ''')
            
            self.conn.commit()
            logging.debug("Geo table ensured to exist")
            
        except sqlite3.Error as e:
            logging.error(f"Error creating geo table: {e}")
            sys.exit(1)

    def populate_from_file(self, geo_file_path='geo_chinese_.list'):
        """Populate geo table from geo_chinese_.list file."""
        if not os.path.exists(geo_file_path):
            logging.error(f"Geo file not found: {geo_file_path}")
            return False

        logging.info(f"Reading geo data from: {geo_file_path}")
        
        total_records = 0
        inserted_records = 0
        skipped_records = 0
        error_records = 0

        try:
            with open(geo_file_path, 'r', encoding='utf-8') as f:
                # Skip header line
                header = next(f)
                logging.info(f"Header: {header.strip()}")
                
                for line_num, line in enumerate(f, start=2):
                    total_records += 1
                    
                    try:
                        # Parse CSV line
                        parts = line.strip().split(',')
                        if len(parts) != 12:
                            logging.warning(f"Line {line_num}: Invalid format, expected 12 fields, got {len(parts)}")
                            error_records += 1
                            continue
                        
                        city_en = parts[0].strip()
                        city_zh = parts[1].strip()
                        region_en = parts[2].strip()
                        region_zh = parts[3].strip()
                        subregion_en = parts[4].strip()
                        subregion_zh = parts[5].strip()
                        country_code = parts[6].strip()
                        country_en = parts[7].strip()
                        country_zh = parts[8].strip()
                        timezone = parts[9].strip()
                        
                        try:
                            latitude = float(parts[10].strip())
                            longitude = float(parts[11].strip())
                        except ValueError as ve:
                            logging.error(f"Line {line_num}: Invalid coordinates - {ve}")
                            error_records += 1
                            continue
                        
                        # Insert into geo table
                        try:
                            self.cursor.execute('''
                                INSERT OR IGNORE INTO geo_data (
                                    city_en, city_zh, region_en, region_zh, subregion_en, subregion_zh,
                                    country_code, country_en, country_zh, timezone, latitude, longitude
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                city_en, city_zh, region_en, region_zh, subregion_en, subregion_zh,
                                country_code, country_en, country_zh, timezone, latitude, longitude
                            ))
                            
                            if self.cursor.rowcount > 0:
                                inserted_records += 1
                            else:
                                skipped_records += 1
                                
                        except sqlite3.Error as db_error:
                            logging.error(f"Line {line_num}: Database error - {db_error}")
                            error_records += 1
                            
                    except Exception as parse_error:
                        logging.error(f"Line {line_num}: Parse error - {parse_error}")
                        error_records += 1
                        
                    # Commit every 1000 records
                    if total_records % 1000 == 0:
                        self.conn.commit()
                        logging.info(f"Processed {total_records} records...")
                
                # Final commit
                self.conn.commit()
                
        except Exception as file_error:
            logging.error(f"Error reading geo file: {file_error}")
            return False
            
        # Print summary
        print("=" * 60)
        print("GEO TABLE POPULATION SUMMARY")
        print("=" * 60)
        print(f"File processed: {geo_file_path}")
        print(f"Total records processed: {total_records}")
        print(f"Records inserted: {inserted_records}")
        print(f"Records skipped (duplicates): {skipped_records}")
        print(f"Records with errors: {error_records}")
        print("=" * 60)
        
        return True

    def get_count(self):
        """Get count of records in geo table."""
        try:
            self.cursor.execute('SELECT COUNT(*) FROM geo_data')
            count = self.cursor.fetchone()[0]
            return count
        except sqlite3.Error as e:
            logging.error(f"Error getting count: {e}")
            return 0

    def clear_table(self):
        """Clear all data from geo table."""
        try:
            self.cursor.execute('DELETE FROM geo_data')
            self.conn.commit()
            logging.info("Geo table cleared successfully")
            return True
        except sqlite3.Error as e:
            logging.error(f"Error clearing table: {e}")
            return False

    def get_sample(self, limit=10):
        """Get sample records from geo table."""
        try:
            self.cursor.execute('''
                SELECT city_en, city_zh, country_en, country_zh, latitude, longitude 
                FROM geo_data 
                ORDER BY city_en 
                LIMIT ?
            ''', (limit,))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Error getting sample: {e}")
            return []

    def get_statistics(self):
        """Get table statistics."""
        try:
            # Total count
            self.cursor.execute('SELECT COUNT(*) FROM geo_data')
            total_count = self.cursor.fetchone()[0]
            
            # Countries count
            self.cursor.execute('SELECT COUNT(DISTINCT country_en) FROM geo_data')
            countries_count = self.cursor.fetchone()[0]
            
            # Cities count
            self.cursor.execute('SELECT COUNT(DISTINCT city_en) FROM geo_data')
            cities_count = self.cursor.fetchone()[0]
            
            # Top countries by city count
            self.cursor.execute('''
                SELECT country_en, country_zh, COUNT(*) as city_count 
                FROM geo_data 
                GROUP BY country_en, country_zh 
                ORDER BY city_count DESC 
                LIMIT 10
            ''')
            top_countries = self.cursor.fetchall()
            
            return {
                'total_records': total_count,
                'unique_countries': countries_count,
                'unique_cities': cities_count,
                'top_countries': top_countries
            }
            
        except sqlite3.Error as e:
            logging.error(f"Error getting statistics: {e}")
            return None

    def close(self):
        if self.conn:
            self.conn.close()

def main():
    parser = argparse.ArgumentParser(
        description="Geo Table Management Utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s --populate                    # Populate from default geo file
    %(prog)s --populate --file custom.list # Populate from custom geo file  
    %(prog)s --count                       # Show record count
    %(prog)s --sample 20                   # Show 20 sample records
    %(prog)s --clear                       # Clear all geo data
    %(prog)s --stats                       # Show detailed statistics
        """
    )
    
    parser.add_argument('--populate', action='store_true', 
                       help='Populate geo table from geo file')
    parser.add_argument('--file', default='geo_chinese_.list',
                       help='Geo file path (default: geo_chinese_.list)')
    parser.add_argument('--count', action='store_true',
                       help='Show record count in geo table')
    parser.add_argument('--sample', type=int, metavar='N',
                       help='Show N sample records from geo table')
    parser.add_argument('--clear', action='store_true',
                       help='Clear all records from geo table')
    parser.add_argument('--stats', action='store_true',
                       help='Show detailed table statistics')
    parser.add_argument('--db', default='media_organizer.db',
                       help='Database path (default: media_organizer.db)')
    
    args = parser.parse_args()
    
    # Check if any action is specified
    if not any([args.populate, args.count, args.sample, args.clear, args.stats]):
        parser.print_help()
        sys.exit(1)
    
    manager = GeoTableManager(args.db)
    
    try:
        if args.populate:
            print(f"Populating geo table from: {args.file}")
            if args.clear:
                print("Clearing existing data first...")
                manager.clear_table()
            
            success = manager.populate_from_file(args.file)
            if success:
                print("✓ Geo table populated successfully")
            else:
                print("✗ Failed to populate geo table")
                sys.exit(1)
        
        if args.count:
            count = manager.get_count()
            print(f"Geo table contains {count:,} records")
        
        if args.sample:
            sample_data = manager.get_sample(args.sample)
            if sample_data:
                print(f"\nSample geo records (showing {len(sample_data)}):")
                print("-" * 80)
                for i, (city_en, city_zh, country_en, country_zh, lat, lon) in enumerate(sample_data, 1):
                    print(f"{i:3d}. {city_en:<20} ({city_zh:<15}) in {country_en:<15} ({country_zh:<10}) at {lat:8.4f}, {lon:9.4f}")
            else:
                print("No sample data available")
        
        if args.clear:
            if not args.populate:  # Don't ask again if already clearing for populate
                confirm = input("Are you sure you want to clear all geo data? (yes/no): ")
                if confirm.lower() != 'yes':
                    print("Operation cancelled")
                    sys.exit(0)
                
            if manager.clear_table():
                print("✓ Geo table cleared successfully")
            else:
                print("✗ Failed to clear geo table")
        
        if args.stats:
            stats = manager.get_statistics()
            if stats:
                print("\nGEO TABLE STATISTICS")
                print("=" * 50)
                print(f"Total records: {stats['total_records']:,}")
                print(f"Unique countries: {stats['unique_countries']:,}")
                print(f"Unique cities: {stats['unique_cities']:,}")
                
                if stats['top_countries']:
                    print(f"\nTop countries by city count:")
                    print("-" * 40)
                    for country_en, country_zh, count in stats['top_countries']:
                        print(f"{count:4d} cities in {country_en} ({country_zh})")
            else:
                print("Unable to retrieve statistics")
                
    finally:
        manager.close()

if __name__ == "__main__":
    main()