#!/usr/bin/env python3
"""
Geographic Translation Editor
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import os
import re
import urllib.parse
import threading
import json
import time
import webbrowser
import argparse
import sys
import sqlite3
from typing import List, Dict, Optional

# Try to import requests, fall back to urllib if not available
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    HAS_REQUESTS = False

class GeoTranslationEditor:
    def __init__(self, root, db_path="media_organizer.db"):
        self.root = root
        self.root.title("Geographic Translation Editor - Database Mode")
        
        # Store the database path and initialize translation CSV file path
        self.city_csv_file = None
        self.list_file = None  # Add variable to track selected list file
        self.db_path = db_path
        
        # Set initial window size
        initial_width = 1200
        initial_height = 700
        self.root.geometry(f"{initial_width}x{initial_height}")
        
        # Set minimum window size (cannot be smaller than initial size)
        self.root.minsize(initial_width, initial_height)
        
        # Allow window to be resizable (this is the default, but being explicit)
        self.root.resizable(True, True)
        
        # Center the window on screen
        self.center_window(initial_width, initial_height)
        
        # Database connection
        self.conn = None
        self.init_database()
        
        # Data storage
        self.data: List[Dict] = []
        self.filtered_data: List[Dict] = []
        self.csv_file_path = ""
        
        # Track modifications
        self.modified = False
        
        # UI components that need to be controlled
        self.edit_all_button = None
        
        # Initialize additional city translations (loaded when CSV is selected)
        self.additional_translations = {}
        
        self.setup_ui()
        
    def center_window(self, width, height):
        """Center the window on the screen"""
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate position coordinates
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        # Set the window position
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def init_database(self):
        """Initialize database connection and ensure geo_data table exists"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Enable column name access
            
            # Ensure geo_data table exists
            cursor = self.conn.cursor()
            cursor.execute('''
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
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_geo_coords ON geo_data (latitude, longitude)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_geo_city_country ON geo_data (city_en, country_en)
            ''')
            
            self.conn.commit()
            print(f"✅ Database initialized: {self.db_path}")
            
        except sqlite3.Error as e:
            print(f"❌ Database error: {e}")
            messagebox.showerror("Database Error", f"Failed to initialize database: {e}")
    
    def load_geo_list_to_database(self, file_path):
        """Load data from selected geographic list file into the database"""
        try:
            cursor = self.conn.cursor()
            
            # Data should already be cleared by repopulate method
            
            # Load data from CSV file
            total_records = 0
            inserted_records = 0
            skipped_records = 0
            error_records = 0
            
            print(f"Loading geo data from: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                # Skip header line
                header = next(f)
                print(f"Header: {header.strip()}")
                
                for line_num, line in enumerate(f, start=2):
                    total_records += 1
                    
                    try:
                        # Parse CSV line
                        parts = line.strip().split(',')
                        if len(parts) != 12:
                            print(f"Line {line_num}: Invalid format, expected 12 fields, got {len(parts)}")
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
                            print(f"Line {line_num}: Invalid coordinates - {ve}")
                            error_records += 1
                            continue
                        
                        # Insert into geo table
                        cursor.execute('''
                            INSERT OR IGNORE INTO geo_data (
                                city_en, city_zh, region_en, region_zh, subregion_en, subregion_zh,
                                country_code, country_en, country_zh, timezone, latitude, longitude
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            city_en, city_zh, region_en, region_zh, subregion_en, subregion_zh,
                            country_code, country_en, country_zh, timezone, latitude, longitude
                        ))
                        
                        if cursor.rowcount > 0:
                            inserted_records += 1
                        else:
                            skipped_records += 1
                            
                    except Exception as parse_error:
                        print(f"Line {line_num}: Parse error - {parse_error}")
                        error_records += 1
                        
                    # Commit every 1000 records
                    if total_records % 1000 == 0:
                        self.conn.commit()
                        print(f"Processed {total_records} records...")
                
                # Final commit
                self.conn.commit()
                
            print(f"Database loading complete:")
            print(f"  Total records processed: {total_records}")
            print(f"  Records inserted: {inserted_records}")
            print(f"  Records skipped (duplicates): {skipped_records}")
            print(f"  Records with errors: {error_records}")
            
            return True
            
        except Exception as e:
            print(f"Error loading CSV to database: {e}")
            messagebox.showerror("Load Error", f"Failed to load data: {e}")
            return False
    
    def update_city_translation_in_db(self, city_en, country_en, new_city_zh, new_country_zh=None):
        """Update city Chinese translation directly in database"""
        try:
            cursor = self.conn.cursor()
            
            if new_country_zh is not None:
                # Update both city_zh and country_zh
                cursor.execute('''
                    UPDATE geo_data 
                    SET city_zh = ?, country_zh = ? 
                    WHERE city_en = ? AND country_en = ?
                ''', (new_city_zh, new_country_zh, city_en, country_en))
                
                updated_count = cursor.rowcount
                self.conn.commit()
                
                if updated_count > 0:
                    print(f"✅ Updated {updated_count} records: {city_en} ({country_en}) -> {new_city_zh} ({new_country_zh})")
                    return True
                else:
                    print(f"⚠️  No records found to update: {city_en} in {country_en}")
                    return False
            else:
                # Update only city_zh
                cursor.execute('''
                    UPDATE geo_data 
                    SET city_zh = ? 
                    WHERE city_en = ? AND country_en = ?
                ''', (new_city_zh, city_en, country_en))
                
                updated_count = cursor.rowcount
                self.conn.commit()
                
                if updated_count > 0:
                    print(f"✅ Updated {updated_count} records: {city_en} ({country_en}) -> {new_city_zh}")
                    return True
                else:
                    print(f"⚠️  No records found to update: {city_en} in {country_en}")
                    return False
                
        except sqlite3.Error as e:
            print(f"❌ Database error updating translation: {e}")
            return False
        
    def load_city_translations(self):
        """Load additional city translations from specified CSV file"""
        if not self.city_csv_file:
            print("⚠️  No translation CSV file selected")
            return
            
        city_translation_file_path = self.city_csv_file
        
        try:
            if not os.path.exists(city_translation_file_path):
                print(f"⚠️  City translation file not found: {city_translation_file_path}")
                return

            print(f"📖 Loading City translations from {city_translation_file_path}")
            
            # Clear previous translations
            self.additional_translations.clear()

            with open(city_translation_file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                
                # Validate CSV headers
                expected_headers = ['City_en', 'City_zh']
                actual_headers = csv_reader.fieldnames
                
                # Handle BOM issue in first header
                if actual_headers and actual_headers[0].startswith('\ufeff'):
                    actual_headers[0] = actual_headers[0].replace('\ufeff', '')
                
                # Check if headers match expected format
                if not actual_headers or len(actual_headers) < 2:
                    print(f"❌ Error: CSV file must have at least 2 columns")
                    print(f"   Expected headers: {expected_headers}")
                    print(f"   Found headers: {actual_headers}")
                    sys.exit(1)
                
                # Check for required headers (allowing for different order)
                has_city_en = any(header.replace('\ufeff', '') == 'City_en' for header in actual_headers)
                has_city_zh = any(header.replace('\ufeff', '') == 'City_zh' for header in actual_headers)
                
                if not has_city_en or not has_city_zh:
                    print(f"❌ Error: CSV file must contain 'City_en' and 'City_zh' columns")
                    print(f"   Expected headers: {expected_headers}")
                    print(f"   Found headers: {actual_headers}")
                    sys.exit(1)
                
                # Process rows
                count = 0
                for row in csv_reader:
                    # Handle BOM issue - first column might have \ufeff prefix
                    city_en = row.get('City_en', row.get('\ufeffCity_en', '')).strip()
                    city_zh = row.get('City_zh', '').strip()
                    
                    if city_en and city_zh:
                        self.additional_translations[city_en] = city_zh
                        count += 1

                print(f"✅ Loaded {count} City translations")
                
        except Exception as e:
            print(f"❌ Error loading City translations: {e}")
            # Don't exit on general errors, just show the message
            return
        
    def search_chinese_city_name(self, city_en, country_en):
        """Search for Chinese translation of city name using web search - returns single result for backward compatibility"""
        candidates = self.search_chinese_city_candidates(city_en, country_en)
        return candidates[0] if candidates else ""
    
    def search_chinese_city_candidates(self, city_en, country_en):
        """Search for multiple Chinese translation candidates of city name using web search"""
        candidates = []
        
        print(f"\n🚀 STARTING CHINESE TRANSLATION SEARCH for '{city_en}' in '{country_en}'")
        print("=" * 60)
        
        try:
            # First try fallback translation for common cities
            fallback_result = self.get_fallback_translation(city_en, country_en)
            if fallback_result:
                candidates.append(fallback_result)
                print(f"💾 FALLBACK DATABASE HIT: '{fallback_result}'")
            else:
                print("💾 No fallback translation found in local database")
                
                # Try some common variations if exact match not found
                print("🔄 Trying city name variations...")
                variations = self.generate_city_variations(city_en)
                for variation in variations[1:]:  # Skip the original name
                    var_result = self.get_fallback_translation(variation, country_en)
                    if var_result and var_result not in candidates:
                        candidates.append(var_result)
                        print(f"💾 VARIATION MATCH: '{variation}' -> '{var_result}'")
                        break  # Take the first successful variation
            
            # Note: Google search is temporarily disabled due to anti-bot detection
            # Google serves different content to automated requests vs browsers
            # The application now relies on the comprehensive fallback database
            print("\n🔄 NOTE: Google search temporarily disabled due to anti-bot measures")
            print("📋 Using comprehensive local database instead")
            print("💡 For cities not in database, please add them to the fallback_translation method")
            
        except Exception as e:
            print(f"❌ GENERAL SEARCH ERROR: {e}")
            import time
            import random
            
            # Create session for better connection management
            session = requests.Session()
            
            # Create search query for Google with better anti-detection
            # Use a more natural search query that's less likely to be blocked
            search_query = f"{city_en} {country_en} chinese name translation"
            encoded_query = urllib.parse.quote_plus(search_query)
            google_url = f"https://www.google.com/search?q={encoded_query}"

            print(f"\n🔍 GOOGLE SEARCH SETUP:")
            print(f"   📝 Original Query: '{search_query}'")
            print(f"   🔗 Encoded Query: '{encoded_query}'")
            print(f"   🌐 Search URL: {google_url}")
            
            # Simplified headers to avoid detection as bot
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none'
            }
            
            print(f"\n🌐 HTTP REQUEST HEADERS:")
            for key, value in headers.items():
                print(f"   {key}: {value}")
            
            # Add a small random delay to seem more human-like
            time.sleep(random.uniform(1, 3))
            
            try:
                print(f"\n⏳ Sending request to Google...")
                start_time = time.time()
                response = session.get(google_url, headers=headers, timeout=15)
                response.raise_for_status()
                end_time = time.time()
                
                print(f"✅ Response received in {end_time - start_time:.2f} seconds")
                print(f"📊 Response Status: {response.status_code}")
                print(f"� Content Type: {response.headers.get('Content-Type', 'Unknown')}")
                print(f"📄 Content Encoding: {response.headers.get('Content-Encoding', 'None')}")
                print(f"📄 Response Encoding: {response.encoding}")
                
                # Ensure proper text encoding
                if response.encoding is None:
                    response.encoding = 'utf-8'
                
                # Get the text content
                html_content = response.text
                print(f"� HTML Content Length: {len(html_content)} characters")
                
                # Check if content looks like valid HTML
                if '<html' in html_content.lower()[:1000]:
                    print("✅ Content appears to be valid HTML")
                else:
                    print("⚠️  Content may not be valid HTML")
                
                # Show first 500 characters of response for debugging
                preview = html_content[:500].replace('\n', ' ').replace('\r', '')
                print(f"\n👀 RESPONSE PREVIEW (first 500 chars):")
                print(f"   {preview}...")
                
                # Save HTML for inspection (optional debugging feature)
                try:
                    debug_filename = f"google_search_debug_{city_en}_{country_en}.html".replace(' ', '_')
                    with open(debug_filename, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    print(f"💾 HTML content saved to: {debug_filename}")
                except Exception as save_error:
                    print(f"💾 Could not save HTML debug file: {save_error}")
                
                # Extract Chinese city names from search results
                print(f"\n🏗️  STARTING EXTRACTION PROCESS...")
                web_candidates = self.extract_chinese_city_names(html_content, city_en)
                
                # If primary extraction fails, try alternative method
                if not web_candidates:
                    print("🔄 Primary extraction found nothing, trying alternative method...")
                    alt_candidates = self.extract_alternative_chinese(html_content)
                    if alt_candidates:
                        print(f"✅ Alternative method found: {alt_candidates}")
                        web_candidates = alt_candidates
                    else:
                        print("❌ Alternative method also found nothing")
                
                # Add web candidates to the list, avoiding duplicates
                print(f"\n🔄 MERGING RESULTS:")
                initial_count = len(candidates)
                for candidate in web_candidates:
                    if candidate not in candidates:
                        candidates.append(candidate)
                        print(f"   ➕ Added: '{candidate}'")
                    else:
                        print(f"   ⏩ Skipped duplicate: '{candidate}'")
                
                print(f"📈 Total candidates: {initial_count} → {len(candidates)}")
                
            except requests.RequestException as e:
                print(f"❌ SEARCH REQUEST FAILED: {e}")
                print(f"🔄 Trying alternative search approach...")
                
                # Try a simpler search without complex headers
                try:
                    simple_headers = {
                        'User-Agent': 'Mozilla/5.0 (compatible; Python-requests)'
                    }
                    simple_response = requests.get(google_url, headers=simple_headers, timeout=10)
                    if simple_response.status_code == 200:
                        print(f"✅ Alternative search succeeded")
                        html_content = simple_response.text
                        if simple_response.encoding is None:
                            simple_response.encoding = 'utf-8'
                        
                        # Save alternative HTML for inspection
                        try:
                            alt_debug_filename = f"google_search_simple_{city_en}_{country_en}.html".replace(' ', '_')
                            with open(alt_debug_filename, 'w', encoding='utf-8') as f:
                                f.write(html_content)
                            print(f"💾 Alternative HTML saved to: {alt_debug_filename}")
                        except:
                            pass
                        
                        web_candidates = self.extract_chinese_city_names(html_content, city_en)
                        
                        # Add web candidates to the list, avoiding duplicates
                        print(f"\n🔄 MERGING RESULTS:")
                        initial_count = len(candidates)
                        for candidate in web_candidates:
                            if candidate not in candidates:
                                candidates.append(candidate)
                                print(f"   ➕ Added: '{candidate}'")
                            else:
                                print(f"   ⏩ Skipped duplicate: '{candidate}'")
                        
                        print(f"📈 Total candidates: {initial_count} → {len(candidates)}")
                    else:
                        print(f"❌ Alternative search also failed with status: {simple_response.status_code}")
                        
                except Exception as alt_error:
                    print(f"❌ Alternative search failed: {alt_error}")
                    print(f"🔄 Continuing with fallback results only...")
                
        except Exception as e:
            print(f"❌ GENERAL SEARCH ERROR: {e}")
        finally:
            # Always close the session
            try:
                session.close()
                print("🔒 Session closed successfully")
            except:
                pass
            
        final_candidates = candidates[:5]  # Return top 5 candidates
        print(f"\n🎯 FINAL RESULT: {len(final_candidates)} candidates selected")
        print(f"📋 Candidates for selection box: {final_candidates}")
        print("=" * 60)
        
        return final_candidates
    
    def extract_alternative_chinese(self, html_content):
        """
        Alternative method to extract Chinese text from Google search results.
        Looks for various patterns that might contain Chinese city names.
        """
        import re
        
        # Pattern to find Chinese characters (excluding common UI text)
        chinese_pattern = r'[\u4e00-\u9fff]+'
        
        # Find all Chinese text
        chinese_matches = re.findall(chinese_pattern, html_content)
        
        # Filter out common Google UI text
        ui_filters = [
            '如果您在几秒钟内没有被重定向',
            '请点击',
            '此处',
            '搜索',
            '图片',
            '视频',
            '新闻',
            '地图',
            '购物',
            '邮箱',
            '云端硬盘',
            '日历',
            '翻译',
            '相册',
            '账号',
            '设置',
            '登录',
            '注册'
        ]
        
        # Filter matches
        valid_matches = []
        for match in chinese_matches:
            # Skip short matches (likely not city names)
            if len(match) < 2:
                continue
            
            # Skip known UI text
            if any(ui_text in match for ui_text in ui_filters):
                continue
            
            # Look for potential city patterns (city names are usually 2-4 characters)
            if 2 <= len(match) <= 6:
                valid_matches.append(match)
        
        # Remove duplicates and return
        return list(set(valid_matches))
    
    def extract_chinese_city_names(self, html_content, city_en):
        """Extract Chinese city names from HTML content with detailed logging"""
        candidates = []
        
        print(f"\n🔍 PARSING GOOGLE SEARCH RESULTS for '{city_en}'")
        print(f"📄 HTML Content Length: {len(html_content)} characters")
        
        # Check if content looks valid
        if not html_content or len(html_content) < 100:
            print(f"❌ HTML content too short or empty")
            return candidates
        
        # Check if content contains any Chinese characters at all
        chinese_count = len(re.findall(r'[\u4e00-\u9fff]', html_content))
        print(f"🀄 Total Chinese characters found in HTML: {chinese_count}")
        
        if chinese_count == 0:
            print(f"❌ No Chinese characters found in HTML content")
            # Show a sample of what we did get
            sample = html_content[:200].replace('\n', ' ').replace('\r', '')
            print(f"📝 Sample content: {sample}...")
            return candidates
        
        # Pattern for Chinese characters that could be city names
        chinese_pattern = r'[\u4e00-\u9fff]{2,6}(?:市|县|区|镇|村|城)?'
        chinese_matches = re.findall(chinese_pattern, html_content)
        
        print(f"🔤 Found {len(chinese_matches)} Chinese character sequences")
        print(f"📝 Raw matches (first 20): {chinese_matches[:20]}")
        
        # Common words to filter out
        common_words = {
            '搜索', '结果', '网页', '图片', '视频', '新闻', '地图', '更多', '设置', '工具', 
            '时间', '所有', '语言', '关于', '帮助', '隐私', '条款', '广告', '商务', '服务',
            '登录', '注册', '首页', '主页', '官网', '网站', '页面', '内容', '信息', '数据',
            '中国', '美国', '英国', '法国', '德国', '日本', '韩国', '意大利', '西班牙',
            '维基', '百科', '知道', '问答', '论坛', '社区', '博客', '微博', '新浪', '腾讯'
        }
        
        # Score candidates based on context and appearance
        candidate_scores = {}
        
        print(f"\n📊 SCORING ALGORITHM:")
        print(f"   📍 City indicators (+3): 市|县|区|镇|村|城|灣|岛|邨|閣|洲|坑|澳")
        print(f"   📏 Length preference: 2-4 chars (+2), 5-6 chars (+1)")
        print(f"   🔄 Frequency bonus: +1 for each additional occurrence (max +3)")
        print(f"   📍 Proximity bonus: +5 if within 200 chars of '{city_en}'")
        
        for match in chinese_matches:
            if (len(match) >= 2 and len(match) <= 8 and 
                match not in common_words):
                
                # Score based on various factors
                score = 0
                score_details = []
                
                # Prefer names ending with city indicators''
                if match.endswith(('市', '县', '区', '镇', '村', '城', '灣', '岛', '邨', '閣', '洲', '坑', '澳')):
                    score += 3
                    score_details.append("city_indicator(+3)")
                
                # Prefer shorter names (more likely to be city names)
                if len(match) <= 4:
                    score += 2
                    score_details.append("short_length(+2)")
                elif len(match) <= 6:
                    score += 1
                    score_details.append("medium_length(+1)")
                
                # Boost score if found multiple times
                count = html_content.count(match)
                frequency_bonus = min(count - 1, 3)
                if frequency_bonus > 0:
                    score += frequency_bonus
                    score_details.append(f"frequency({count}x, +{frequency_bonus})")
                
                # Check if it appears near the English city name
                proximity_bonus = 0
                if city_en.lower() in html_content.lower():
                    city_index = html_content.lower().find(city_en.lower())
                    match_indices = [m.start() for m in re.finditer(re.escape(match), html_content)]
                    for match_index in match_indices:
                        distance = abs(match_index - city_index)
                        if distance < 200:  # Within 200 characters
                            proximity_bonus = 5
                            score_details.append(f"proximity(dist={distance}, +5)")
                            break
                
                score += proximity_bonus
                
                if match in candidate_scores:
                    candidate_scores[match] = max(candidate_scores[match], score)
                else:
                    candidate_scores[match] = score
                
                # Log detailed scoring for potential city names
                if score > 1:  # Only log candidates with decent scores
                    print(f"   🏙️  '{match}' → Score: {score} ({', '.join(score_details)})")
        
        # Sort by score and return top candidates
        sorted_candidates = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)
        
        print(f"\n🏆 TOP CANDIDATES (sorted by score):")
        for i, (candidate, score) in enumerate(sorted_candidates[:10], 1):
            if score > 0:  # Only include candidates with positive scores
                candidates.append(candidate)
                print(f"   {i}. '{candidate}' (Score: {score})")
        
        print(f"\n✅ FINAL SELECTION: {len(candidates)} candidates ready for display")
        print(f"🎯 Selected candidates: {candidates}")
        print("=" * 60)
        
        return candidates
    
    def generate_city_variations(self, city_en):
        """Generate common variations of city names for better matching"""
        variations = [city_en]
        
        # Add variations without common prefixes/suffixes
        if city_en.startswith("New "):
            variations.append(city_en[4:])
        if city_en.startswith("San "):
            variations.append(city_en[4:])
        if city_en.startswith("Los "):
            variations.append(city_en[4:])
        if city_en.endswith(" City"):
            variations.append(city_en[:-5])
        
        # Add common alternate spellings
        alternates = {
            "St.": "Saint",
            "Saint": "St.",
            "Mt.": "Mount",
            "Mount": "Mt."
        }
        
        for old, new in alternates.items():
            if old in city_en:
                variations.append(city_en.replace(old, new))
        
        return variations
    
    def get_fallback_translation(self, city_en, country_en):
        """Provide fallback translations for common cities"""
        # Common city translations
        city_translations = {
            # China
            'Beijing': '北京',
            'Shanghai': '上海', 
            'Guangzhou': '广州',
            'Shenzhen': '深圳',
            'Chengdu': '成都',
            'Hangzhou': '杭州',
            'Wuhan': '武汉',
            'Xi\'an': '西安',
            'Nanjing': '南京',
            'Chongqing': '重庆',
            'Tianjin': '天津',
            'Suzhou': '苏州',
            'Qingdao': '青岛',
            'Dalian': '大连',
            'Zhengzhou': '郑州',
            'Changsha': '长沙',
            'Ningbo': '宁波',
            'Shenyang': '沈阳',
            'Harbin': '哈尔滨',
            'Fuzhou': '福州',
            'Xiamen': '厦门',
            'Jinan': '济南',
            'Kunming': '昆明',
            'Urumqi': '乌鲁木齐',
            'Lhasa': '拉萨',
            'Foshan': '佛山',
            'Zhuhai': '珠海',
            'Dongguan': '東莞',
            'Hengqin': '橫琴',
            'Zhuhai': '珠海',
            'Lutao': '路氹',
            'Taipa': '氹仔',
            'Shantou': '汕头',
            'Zhongshan': '中山',
            'Taishan': '台山',
            'Huizhou': '惠州',
            'Nanning': '南宁',
            'Taiyuan': '太原',
            'Hefei': '合肥',
            'Changchun': '长春',
            'Shijiazhuang': '石家庄',
            'Tangshan': '唐山',
            'Yantai': '烟台',
            'Zibo': '淄博',
            'Weifang': '潍坊',
            'Jinhua': '金华',
            'Wuxi': '无锡',
            'Xuzhou': '徐州',
            'Baotou': '包头',
            'Guiyang': '贵阳',
            'Nanchang': '南昌',
            'Lanzhou': '兰州',
            'Hohhot': '呼和浩特',
            'Jilin': '吉林',
            'Yinchuan': '银川',
            'Haikou': '海口',
            'Zhanjiang': '湛江',
            'Maoming': '茂名',
            'Sanya': '三亚',
            'Haikou': '海口',
            # Singapore
            'Singapore': '新加坡',
            'Sentosa': '圣淘沙',
            # Macau
            'Macau': '澳门',
            'Cotai': '路氹城',
            # Taiwan
            'Taipei': '台北',
            'Kaohsiung': '高雄',
            'Taichung': '台中',
            'Tainan': '台南',
            'Hsinchu': '新竹',
            # Hong Kong
            'Hong Kong': '香港',
            'Kowloon': '九龙',
            'New Territories': '新界',

            # Canada
            'Toronto': '多伦多',
            'Vancouver': '温哥华',
            'Montreal': '蒙特利尔',
            'Calgary': '卡尔加里',
            'Ottawa': '渥太华',
            'Edmonton': '埃德蒙顿',
            'Quebec City': '魁北克市',
            'Winnipeg': '温尼伯',
            'Halifax': '哈利法克斯',
            'Victoria': '维多利亚',
            'Saskatoon': '萨斯卡通',
            'Regina': '里贾纳',
            'St. John\'s': '圣约翰斯',
            'Markham': '万锦',
            'Mississauga': '密西沙加',
            'Brampton': '布兰普顿',
            'Surrey': '素里',
            'Richmond': '列治文',
            'Burnaby': '本拿比',
            'Langley': '兰里',

            # Japan
            'Tokyo': '东京',
            'Osaka': '大阪',
            'Kyoto': '京都',
            'Yokohama': '横滨',
            'Kobe': '神户',
            'Nagoya': '名古屋',
            'Hiroshima': '广岛',
            'Sendai': '仙台',
            
            # South Korea
            'Seoul': '首尔',
            'Busan': '釜山',
            'Incheon': '仁川',
            'Daegu': '大邱',
            'Daejeon': '大田',
            'Gwangju': '光州',
            
            # Thailand
            'Bangkok': '曼谷',
            'Chiang Mai': '清迈',
            'Phuket': '普吉',
            'Pattaya': '芭提雅',
            
            # Malaysia
            'Kuala Lumpur': '吉隆坡',
            'Penang': '槟城',
            'Johor Bahru': '新山',
            
            # Singapore
            'Singapore': '新加坡',
            
            # Indonesia
            'Jakarta': '雅加达',
            'Bali': '巴厘岛',
            'Surabaya': '泗水',
            
            # Philippines
            'Manila': '马尼拉',
            'Cebu': '宿务',
            
            # Vietnam
            'Ho Chi Minh City': '胡志明市',
            'Hanoi': '河内',
            'Da Nang': '岘港',
        }
        
        # First check the built-in translations
        result = city_translations.get(city_en, "")
        
        # If not found in built-in translations, check additional translations from HK CSV
        if not result and hasattr(self, 'additional_translations'):
            result = self.additional_translations.get(city_en, "")
            
        return result
        
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Database loading section
        db_frame = ttk.LabelFrame(main_frame, text="Database Operations", padding="5")
        db_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        db_frame.columnconfigure(1, weight=1)
        
        ttk.Button(db_frame, text="Load City info from Database", command=self.load_csv_data).grid(row=0, column=0, padx=(0, 10))

        ttk.Button(db_frame, text="Repopulate DB from List", command=self.repopulate_database_with_selected_list).grid(row=0, column=1, padx=(10, 0))

        ttk.Button(db_frame, text="Select List File for DB repopulation", command=self.select_list_file).grid(row=1, column=0, padx=(0, 10), pady=(5, 0))

        self.list_file_var = tk.StringVar()
        self.list_file_var.set("No list file selected. Example: geo_chinese.list")
        self.list_status_label = ttk.Label(db_frame, textvariable=self.list_file_var, foreground="gray")
        self.list_status_label.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=(5, 0))
        
        # Translation CSV file section
        csv_frame = ttk.LabelFrame(main_frame, text="Translation Helper CSV", padding="5")
        csv_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        csv_frame.columnconfigure(1, weight=1)
        
        ttk.Button(csv_frame, text="Select City Translation CSV File", command=self.select_translation_csv).grid(row=0, column=0, padx=(0, 10))
        
        self.csv_file_var = tk.StringVar()
        self.csv_file_var.set("No translation CSV loaded, Example: HK_City_en_translated.csv (CSV format: City_en, City_zh)")
        self.csv_status_label = ttk.Label(csv_frame, textvariable=self.csv_file_var, foreground="gray")
        self.csv_status_label.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
        
        # Filter section
        filter_frame = ttk.LabelFrame(main_frame, text="Filters", padding="5")
        filter_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        filter_frame.columnconfigure(1, weight=1)
        
        ttk.Label(filter_frame, text="Country (English):").grid(row=0, column=0, padx=(0, 10))
        
        self.country_filter_var = tk.StringVar()
        self.country_combobox = ttk.Combobox(filter_frame, textvariable=self.country_filter_var, state="readonly")
        self.country_combobox.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        self.country_combobox.bind('<<ComboboxSelected>>', self.apply_filter)
        
        ttk.Button(filter_frame, text="Clear Filter", command=self.clear_filter).grid(row=0, column=2)
        
        # Data table section
        table_frame = ttk.LabelFrame(main_frame, text="Geographic Data", padding="5")
        table_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        # Treeview for data display
        columns = ("city_en", "city_zh", "country_en", "country_zh")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        # Define column headings and widths
        self.tree.heading("city_en", text="City (English)")
        self.tree.heading("city_zh", text="City (Chinese)")
        self.tree.heading("country_en", text="Country (English)")
        self.tree.heading("country_zh", text="Country (Chinese)")
        
        self.tree.column("city_en", width=200, minwidth=150)
        self.tree.column("city_zh", width=200, minwidth=150)
        self.tree.column("country_en", width=150, minwidth=100)
        self.tree.column("country_zh", width=150, minwidth=100)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid the treeview and scrollbars
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Bind double-click event for editing
        self.tree.bind("<Double-1>", self.edit_selected_item)
        
        # Control buttons section
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=4, column=0, columnspan=2, pady=(0, 10))

        ttk.Button(control_frame, text="Edit Selected City (selected on double-click)", command=self.edit_selected_item).pack(side=tk.LEFT, padx=(0, 10))
        self.edit_all_button = ttk.Button(control_frame, text="📝 Edit ALL with CSV File", command=self.edit_all_cities, state="disabled")
        self.edit_all_button.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="💾 Database Info", command=self.save_changes).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="Export current view (city_en, city_zh, country_en, country_zh) to CSV", command=self.export_csv).pack(side=tk.LEFT)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Click 'Reload from Database' to start")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E))
    
    def load_csv_file(self):
        """Load CSV file through file dialog"""
        file_path = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("List files", "*.list"), ("All files", "*.*")],
            initialdir="/Users/syuen/Video_editor_Project/Vacaction_Media_Org/"
        )
        
        if file_path:
            self.csv_file_path = file_path
            self.load_csv_data()
    
    def load_csv_data(self):
        """Load data from database geo_data table"""
        print("ℹ️  Reloading geographic data from database...")
        try:
            self.data.clear()
            
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT city_en, city_zh, country_en, country_zh, 
                       region_en, region_zh, latitude, longitude
                FROM geo_data 
                ORDER BY country_en, city_en
            ''')
            
            rows = cursor.fetchall()
            
            for row in rows:
                # Create the data structure with original_row for compatibility
                # Use try/except for optional columns since sqlite3.Row doesn't have get() method
                try:
                    region_en = row['region_en'] if row['region_en'] else ''
                except (IndexError, KeyError):
                    region_en = ''
                    
                try:
                    region_zh = row['region_zh'] if row['region_zh'] else ''
                except (IndexError, KeyError):
                    region_zh = ''
                    
                try:
                    latitude = float(row['latitude']) if row['latitude'] else 0.0
                except (IndexError, KeyError, ValueError):
                    latitude = 0.0
                    
                try:
                    longitude = float(row['longitude']) if row['longitude'] else 0.0
                except (IndexError, KeyError, ValueError):
                    longitude = 0.0
                
                data_item = {
                    'city_en': row['city_en'],
                    'city_zh': row['city_zh'],
                    'country_en': row['country_en'],
                    'country_zh': row['country_zh'],
                    'region_en': region_en,
                    'region_zh': region_zh,
                    'latitude': latitude,
                    'longitude': longitude,
                }
                
                # Add original_row structure for edit dialog compatibility
                data_item['original_row'] = {
                    'City_en': row['city_en'],
                    'City_zn': row['city_zh'],
                    'Country_en': row['country_en'],
                    'Country_zn': row['country_zh'],
                    'Region_en': region_en,
                    'Region_zn': region_zh,
                    'Latitude': latitude,
                    'Longitude': longitude,
                }
                
                self.data.append(data_item)
            
            self.populate_country_filter()
            self.apply_filter()
            self.status_var.set(f"Loaded {len(self.data)} records from database")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error loading data from database: {e}")
            self.status_var.set(f"Error loading data: {e}")
    
    def select_translation_csv(self):
        """Select CSV file for translation assistance"""
        file_path = filedialog.askopenfilename(
            title="Select Translation CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir="/Users/syuen/Video_editor_Project/Vacaction_Media_Org/"
        )
        
        if file_path:
            # Validate CSV file format
            if self.validate_translation_csv(file_path):
                self.city_csv_file = file_path
                self.load_city_translations()
                filename = os.path.basename(file_path)
                self.csv_file_var.set(f"Loaded: {filename} ({len(self.additional_translations)} translations)")
                self.csv_status_label.config(foreground="green")
            else:
                self.csv_file_var.set("Invalid CSV format - must have City_en, City_zh columns")
                self.csv_status_label.config(foreground="red")
    
    def validate_translation_csv(self, file_path):
        """Validate that CSV file has the required City_en, City_zh columns"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                headers = csv_reader.fieldnames
                
                if not headers:
                    return False
                
                # Handle BOM issue in first header
                if headers[0].startswith('\ufeff'):
                    headers[0] = headers[0].replace('\ufeff', '')
                
                # Check for required headers
                has_city_en = 'City_en' in headers
                has_city_zh = 'City_zh' in headers
                
                return has_city_en and has_city_zh
                
        except Exception as e:
            print(f"Error validating CSV: {e}")
            return False
    
    def count_cities_in_list_file(self, file_path):
        """Count the number of cities in a geographic list file"""
        try:
            city_count = 0
            with open(file_path, 'r', encoding='utf-8') as f:
                # Skip header line
                next(f)
                
                for line in f:
                    line = line.strip()
                    if line:  # Skip empty lines
                        city_count += 1
                        
            return city_count
            
        except Exception as e:
            print(f"Error counting cities in list file: {e}")
            return 0
    
    def select_list_file(self):
        """Select list file for database repopulation"""
        file_path = filedialog.askopenfilename(
            title="Select List File for DB repopulation",
            filetypes=[("List files", "*.list"), ("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir="/Users/syuen/Video_editor_Project/Vacaction_Media_Org/"
        )
        
        if file_path:
            # Validate list file format
            if self.validate_geo_list_format(file_path):
                self.list_file = file_path
                filename = os.path.basename(file_path)
                city_count = self.count_cities_in_list_file(file_path)
                self.list_file_var.set(f"Loaded: {filename} ({city_count} Cities)")
                self.list_status_label.config(foreground="green")
                print(f"✅ List file validated and selected: {filename} ({city_count} cities)")
            else:
                self.list_file_var.set("Invalid list format - check data scheme")
                self.list_status_label.config(foreground="red")
                print(f"❌ Invalid list file format: {os.path.basename(file_path)}")
    
    def repopulate_database_with_selected_list(self):
        """Repopulate database with data from previously selected list file"""
        if not self.list_file:
            messagebox.showwarning("No List File", "Please select a list file first using 'Select List File for DB repopulation' button.")
            return
            
        if not os.path.exists(self.list_file):
            messagebox.showerror("File Not Found", f"Selected list file not found: {os.path.basename(self.list_file)}")
            return
        
        result = messagebox.askyesno(
            "Repopulate Confirmation", 
            f"This will clear all existing geographic data and repopulate from:\n{os.path.basename(self.list_file)}\n\nContinue?"
        )
        
        if result:
            try:
                cursor = self.conn.cursor()
                cursor.execute('DELETE FROM geo_data')
                self.conn.commit()
                
                if self.load_geo_list_to_database(self.list_file):
                    self.load_csv_data()  # Refresh the displayed data
                    messagebox.showinfo("Success", "Database repopulated successfully!")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to repopulate database: {e}")
    

    def validate_geo_list_format(self, file_path):
        """Validate that the geographic list file has the correct format"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                header = next(f).strip()
                expected_fields = ['City_en', 'City_zn', 'Region_en', 'Region_zn', 'Subregion_en', 'Subregion_zn', 
                                 'CountryCode', 'Country_en', 'Country_zn', 'TimeZone', 'Latitude', 'Longitude']
                
                header_fields = [field.strip() for field in header.split(',')]
                return header_fields == expected_fields
                
        except Exception as e:
            print(f"Error validating geographic list format: {e}")
            return False
    
    def populate_country_filter(self):
        """Populate the country filter combobox"""
        countries = sorted(set(item['country_en'] for item in self.data if item['country_en']))
        self.country_combobox['values'] = ['All Countries'] + countries
        self.country_combobox.set('All Countries')
    
    def apply_filter(self, event=None):
        """Apply country filter to the data"""
        selected_country = self.country_filter_var.get()
        
        if selected_country == 'All Countries' or not selected_country:
            # When "All Countries" is selected, no need to sort - keep original order
            self.filtered_data = self.data.copy()
            # Disable Edit All button for "All Countries"
            if self.edit_all_button:
                self.edit_all_button.config(state="disabled")
        else:
            # When a specific country is selected, filter and sort by city name
            self.filtered_data = [item for item in self.data if item['country_en'] == selected_country]
            # Sort by city (English) name
            self.filtered_data.sort(key=lambda x: x['city_en'].lower())
            # Enable Edit All button when a specific country is selected
            if self.edit_all_button:
                self.edit_all_button.config(state="normal")
        
        self.refresh_table()
    
    def clear_filter(self):
        """Clear all filters"""
        self.country_combobox.set('All Countries')
        self.apply_filter()
    
    def refresh_table(self):
        """Refresh the table with filtered data"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add filtered data
        for item in self.filtered_data:
            self.tree.insert('', 'end', values=(
                item['city_en'],
                item['city_zh'],
                item['country_en'],
                item['country_zh']
            ))
        
        self.status_var.set(f"Showing {len(self.filtered_data)} of {len(self.data)} records")
    
    def edit_all_cities(self):
        """Auto-edit all cities in the current filtered list using fallback translations"""
        if not self.filtered_data:
            messagebox.showwarning("No Data", "No cities to edit. Please select a country first.")
            return
        
        # Get current country selection for context
        selected_country = self.country_filter_var.get()
        if selected_country == 'All Countries' or not selected_country:
            messagebox.showwarning("No Country Selected", "Please select a specific country before using Edit All.")
            return
        
        # Confirm with user
        response = messagebox.askyesno(
            "Confirm Edit All",
            f"This will automatically update Chinese translations for all {len(self.filtered_data)} cities in {selected_country} using the local database.\n\n"
            f"Only cities with different translations will be updated.\n\n"
            f"Do you want to continue?"
        )
        
        if not response:
            return
        
        # Track changes
        updated_count = 0
        processed_count = 0
        
        # Show progress dialog
        progress_dialog = tk.Toplevel(self.root)
        progress_dialog.title("Processing Cities...")
        progress_dialog.geometry("400x150")
        progress_dialog.transient(self.root)
        progress_dialog.grab_set()
        
        # Center the dialog
        progress_dialog.update_idletasks()
        x = (progress_dialog.winfo_screenwidth() - progress_dialog.winfo_width()) // 2
        y = (progress_dialog.winfo_screenheight() - progress_dialog.winfo_height()) // 2
        progress_dialog.geometry(f"+{x}+{y}")
        
        progress_label = ttk.Label(progress_dialog, text="Processing cities...")
        progress_label.pack(pady=10)
        
        progress_bar = ttk.Progressbar(progress_dialog, mode='determinate', maximum=len(self.filtered_data))
        progress_bar.pack(pady=10, padx=20, fill=tk.X)
        
        # Update function
        def update_progress(current, city_name):
            progress_bar['value'] = current
            progress_label.config(text=f"Processing: {city_name} ({current}/{len(self.filtered_data)})")
            progress_dialog.update()
        
        try:
            # Process each city in filtered data
            for i, data_item in enumerate(self.filtered_data):
                city_en = data_item.get('city_en', '').strip()
                current_city_zh = data_item.get('city_zh', '').strip()
                country_en = data_item.get('country_en', '').strip()
                
                processed_count += 1
                update_progress(processed_count, city_en)
                
                if city_en:
                    # Get suggested translation from fallback database
                    suggested_translation = self.get_fallback_translation(city_en, country_en)
                    
                    if suggested_translation and suggested_translation != current_city_zh:
                        # Update database directly
                        success = self.update_city_translation_in_db(
                            city_en, 
                            country_en, 
                            suggested_translation, 
                            data_item.get('country_zh', '')
                        )
                        
                        if success:
                            # Update the translation in both data and filtered_data
                            data_item['city_zh'] = suggested_translation
                            
                            # Also find and update in main data list
                            for main_item in self.data:
                                if (main_item.get('city_en') == city_en and 
                                    main_item.get('country_en') == country_en):
                                    main_item['city_zh'] = suggested_translation
                                    break
                            
                            updated_count += 1
            
            # Close progress dialog
            progress_dialog.destroy()
            
            # Mark as modified and refresh display
            if updated_count > 0:
                self.modified = True
                self.refresh_table()
                messagebox.showinfo(
                    "Edit All Complete",
                    f"Successfully updated {updated_count} out of {processed_count} cities.\n\n"
                    f"All changes have been automatically saved to the database."
                )
                self.status_var.set(f"✅ Updated {updated_count} cities - Auto-saved to database")
            else:
                messagebox.showinfo(
                    "No Updates Needed",
                    f"All {processed_count} cities already have correct translations or no translations were found in the database."
                )
                
        except Exception as e:
            progress_dialog.destroy()
            messagebox.showerror("Error", f"An error occurred during processing: {str(e)}")
    
    def edit_selected_item(self, event=None):
        """Edit the selected item"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an item to edit.")
            return
        
        item_id = selection[0]
        values = self.tree.item(item_id, 'values')
        
        if not values:
            return
        
        # Find the corresponding data item
        city_en, city_zh, country_en, country_zh = values
        data_item = None
        
        for item in self.filtered_data:
            if (item['city_en'] == city_en and 
                item['country_en'] == country_en):
                data_item = item
                break
        
        if data_item:
            self.show_edit_dialog(data_item, item_id)
    
    def show_edit_dialog(self, data_item, tree_item_id):
        """Show edit dialog for the selected item"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Translation")
        
        # Set initial dialog size (make it larger to accommodate selection box)
        dialog_width = 600
        dialog_height = 450
        dialog.geometry(f"{dialog_width}x{dialog_height}")
        
        # Set minimum size for dialog
        dialog.minsize(500, 350)
        
        # Make dialog resizable
        dialog.resizable(True, True)
        
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog_width // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog_height // 2)
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights for responsive layout
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=0)
        main_frame.columnconfigure(3, weight=0)
        
        # Form fields
        ttk.Label(main_frame, text="City (English):").grid(row=0, column=0, sticky=tk.W, pady=(0, 5), padx=(0, 10))
        city_en_var = tk.StringVar(value=data_item['city_en'])
        city_en_entry = ttk.Entry(main_frame, textvariable=city_en_var, state="readonly")
        city_en_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 5), columnspan=3)
        
        ttk.Label(main_frame, text="City (Chinese):").grid(row=1, column=0, sticky=tk.W, pady=(0, 5), padx=(0, 10))
        city_zh_var = tk.StringVar(value=data_item['city_zh'])
        city_zh_entry = ttk.Entry(main_frame, textvariable=city_zh_var)
        city_zh_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Auto-search button
        search_button = ttk.Button(main_frame, text="🔍 Auto Search", width=12)
        search_button.grid(row=1, column=2, sticky=tk.W, pady=(0, 5), padx=(5, 0))
        
        # Search button to open Google search
        demo_button = ttk.Button(main_frame, text="🔍 Google", width=8)
        demo_button.grid(row=1, column=3, sticky=tk.W, pady=(0, 5), padx=(5, 0))
        
        ttk.Label(main_frame, text="Country (English):").grid(row=2, column=0, sticky=tk.W, pady=(0, 5), padx=(0, 10))
        country_en_var = tk.StringVar(value=data_item['country_en'])
        ttk.Entry(main_frame, textvariable=country_en_var, state="readonly").grid(row=2, column=1, sticky=(tk.W, tk.E), pady=(0, 5), columnspan=3)
        
        ttk.Label(main_frame, text="Country (Chinese):").grid(row=3, column=0, sticky=tk.W, pady=(0, 5), padx=(0, 10))
        country_zh_var = tk.StringVar(value=data_item['country_zh'])
        country_zh_entry = ttk.Entry(main_frame, textvariable=country_zh_var)
        country_zh_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=(0, 5), columnspan=3)
        
        # Search results selection box
        ttk.Label(main_frame, text="Search Results:").grid(row=4, column=0, sticky=tk.W, pady=(5, 5), padx=(0, 10))
        
        # Frame for search results listbox and scrollbar
        search_frame = ttk.Frame(main_frame)
        search_frame.grid(row=4, column=1, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 5))
        search_frame.columnconfigure(0, weight=1)
        search_frame.rowconfigure(0, weight=1)
        
        # Listbox for search results with scrollbar
        search_listbox = tk.Listbox(search_frame, height=6, selectmode=tk.SINGLE)
        search_scrollbar = ttk.Scrollbar(search_frame, orient=tk.VERTICAL, command=search_listbox.yview)
        search_listbox.config(yscrollcommand=search_scrollbar.set)
        
        search_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        search_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Initially hidden
        search_frame.grid_remove()
        
        # Button to use selected result
        use_selected_button = ttk.Button(main_frame, text="📥 Use Selected", state="disabled")
        use_selected_button.grid(row=5, column=1, columnspan=3, sticky=tk.W, pady=(5, 5))
        use_selected_button.grid_remove()  # Initially hidden
        
        # Status label for search feedback
        status_label = ttk.Label(main_frame, text="", foreground="blue")
        status_label.grid(row=6, column=0, columnspan=4, pady=(5, 10))
        
        # Focus on the editable field
        city_zh_entry.focus()
        
        # Auto-search functionality using fallback translations
        def perform_auto_search():
            """Suggest Chinese city name using fallback translation database"""
            search_button.config(text="⏳ Searching...", state="disabled")
            status_label.config(text="Looking up translation in local database...", foreground="blue")
            
            # Clear previous results
            search_listbox.delete(0, tk.END)
            search_frame.grid_remove()
            use_selected_button.grid_remove()
            use_selected_button.config(state="disabled")
            
            dialog.update()
            
            try:
                # Get current city and country
                city_en = city_en_var.get().strip()
                country_en = country_en_var.get().strip()
                
                if not city_en:
                    status_label.config(text="❌ No city name to search for", foreground="red")
                    search_button.config(text="🔍 Auto Search", state="normal")
                    return
                
                # Use fallback translation to get suggestion
                suggested_translation = self.get_fallback_translation(city_en, country_en)
                
                if suggested_translation:
                    # Add the suggestion to the listbox
                    display_text = f"1. {suggested_translation} (Database)"
                    search_listbox.insert(tk.END, display_text)
                    
                    # Try variations if exact match not found
                    variations = self.generate_city_variations(city_en)
                    for variation in variations[1:]:  # Skip the original name
                        var_result = self.get_fallback_translation(variation, country_en)
                        if var_result and var_result != suggested_translation:
                            display_text = f"{search_listbox.size() + 1}. {var_result} (Variation: {variation})"
                            search_listbox.insert(tk.END, display_text)
                    
                    # Show the search results
                    search_frame.grid()
                    use_selected_button.grid()
                    
                    # Enable the use button when selection changes
                    def on_selection_change(event):
                        selection = search_listbox.curselection()
                        if selection:
                            use_selected_button.config(state="normal")
                        else:
                            use_selected_button.config(state="disabled")
                    
                    def on_double_click(event):
                        """Auto-apply on double-click"""
                        use_selected_result()
                    
                    search_listbox.bind('<<ListboxSelect>>', on_selection_change)
                    search_listbox.bind('<Double-Button-1>', on_double_click)
                    
                    # Auto-select and apply first suggestion
                    current_value = city_zh_var.get().strip()
                    if not current_value or current_value == city_en:
                        search_listbox.selection_set(0)
                        search_listbox.event_generate('<<ListboxSelect>>')
                        # Auto-apply first suggestion
                        city_zh_var.set(suggested_translation)
                        status_label.config(text=f"✅ Suggested translation applied: {suggested_translation}", foreground="green")
                    else:
                        search_listbox.selection_set(0)
                        search_listbox.event_generate('<<ListboxSelect>>')
                        status_label.config(text=f"✅ Found suggestion: {suggested_translation}. Click 'Use Selected' to apply.", foreground="green")
                else:
                    status_label.config(text=f"❌ No translation found for '{city_en}' in local database", foreground="red")
                
                search_button.config(text="🔍 Auto Search", state="normal")
                
            except Exception as e:
                status_label.config(text=f"❌ Search error: {str(e)}", foreground="red")
                search_button.config(text="🔍 Auto Search", state="normal")
        
        def use_selected_result():
            """Use the selected search result"""
            selection = search_listbox.curselection()
            if selection:
                selected_text = search_listbox.get(selection[0])
                # Extract just the Chinese name (remove the number prefix and source info)
                if '. ' in selected_text:
                    chinese_part = selected_text.split('. ', 1)[1]
                    # Remove source info like "(Database)" or "(Variation: ...)"
                    if ' (' in chinese_part:
                        chinese_name = chinese_part.split(' (')[0]
                    else:
                        chinese_name = chinese_part
                else:
                    chinese_name = selected_text
                
                city_zh_var.set(chinese_name)
                status_label.config(text=f"✅ Applied: {chinese_name}", foreground="green")
        
        def open_google_search():
            """Open Google search for the city in default browser"""
            city_en = city_en_var.get().strip()
            country_en = country_en_var.get().strip()
            
            if not city_en:
                status_label.config(text="❌ No city name to search", foreground="red")
                return
            
            # Create Google search query (same as Auto Search)
            search_query = f'{country_en} {city_en} 中文 翻译'
            encoded_query = urllib.parse.quote_plus(search_query)
            google_url = f"https://www.google.com/search?q={encoded_query}&hl=zh-CN&lr=lang_zh"
            
            try:
                # Update status to show what we're opening
                status_label.config(text=f"🔍 Opening Google search for '{search_query}'", foreground="blue")
                
                print(f"Opening Google search URL: {google_url}")
                
                # Open the URL in the default browser
                webbrowser.open(google_url)
                
                # Update status to confirm
                status_label.config(text=f"✅ Opened Google search: {search_query}", foreground="green")

            except Exception as e:
                status_label.config(text=f"❌ Failed to open browser: {str(e)}", foreground="red")
        
        # Bind functions to buttons
        search_button.config(command=perform_auto_search)
        use_selected_button.config(command=use_selected_result)
        demo_button.config(command=open_google_search)
        
        # Auto-search on dialog open if city_zh is empty or same as city_en
        if not data_item['city_zh'].strip() or data_item['city_zh'].strip() == data_item['city_en'].strip():
            dialog.after(100, perform_auto_search)  # Small delay to let dialog fully load
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=4, pady=(15, 0))
        
        def save_changes():
            new_city_zh = city_zh_var.get().strip()
            new_country_zh = country_zh_var.get().strip()
            
            city_changed = new_city_zh != data_item['city_zh']
            country_changed = new_country_zh != data_item['country_zh']
            
            if city_changed or country_changed:
                # Update database directly - single call for both fields
                final_city_zh = new_city_zh if city_changed else data_item['city_zh']
                final_country_zh = new_country_zh if country_changed else data_item['country_zh']
                
                success = self.update_city_translation_in_db(
                    data_item['city_en'], 
                    data_item['country_en'], 
                    final_city_zh, 
                    final_country_zh
                )
                
                if success:
                    # Update normalized data
                    if city_changed:
                        data_item['city_zh'] = new_city_zh
                        
                        # Update original row data - find the correct field name
                        city_zh_field = None
                        for field in ['City_zn', 'city_zh', 'City_zh']:
                            if field in data_item['original_row']:
                                city_zh_field = field
                                break
                        if city_zh_field:
                            data_item['original_row'][city_zh_field] = new_city_zh
                    
                    if country_changed:
                        data_item['country_zh'] = new_country_zh
                        
                        # Update original row data - find the correct field name
                        country_zh_field = None
                        for field in ['Country_zn', 'country_zh', 'Country_zh']:
                            if field in data_item['original_row']:
                                country_zh_field = field
                                break
                        if country_zh_field:
                            data_item['original_row'][country_zh_field] = new_country_zh
                    
                    # Update tree view
                    self.tree.item(tree_item_id, values=(
                        data_item['city_en'],
                        data_item['city_zh'],
                        data_item['country_en'],
                        data_item['country_zh']
                    ))
                    
                    self.status_var.set("✅ Changes saved to database")
                else:
                    messagebox.showerror("Database Error", "Failed to update translation in database")
                    return
                
            dialog.destroy()
        
        def cancel_changes():
            dialog.destroy()
        
        ttk.Button(button_frame, text="Save", command=save_changes).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=cancel_changes).pack(side=tk.LEFT)
        
        # Bind Enter key to save
        dialog.bind('<Return>', lambda e: save_changes())
        dialog.bind('<Escape>', lambda e: cancel_changes())
    
    def save_changes(self):
        """Database mode - changes are automatically saved"""
        messagebox.showinfo("Database Mode", 
                           "All changes are automatically saved to the database.\n"
                           "No manual save is required.")
        self.status_var.set("✅ All changes auto-saved to database")
    
    def export_csv(self):
        """Export filtered data to a new CSV file"""
        if not self.filtered_data:
            messagebox.showwarning("No Data", "No data to export.")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Export CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(['City_en', 'City_zh', 'Country_en', 'Country_zh'])
                    
                    for item in self.filtered_data:
                        writer.writerow([
                            item['city_en'],
                            item['city_zh'],
                            item['country_en'],
                            item['country_zh']
                        ])
                
                messagebox.showinfo("Success", f"Data exported to {file_path}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export data:\n{str(e)}")

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Geographic City name Translation (city_en to city_zh) Editor - Database Version",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python Tk_geo_translation_editor.py
  python Tk_geo_translation_editor.py --db-path /path/to/database.db

  This tool now works directly with the SQLite database geo_data table.
  All changes are automatically saved to the database.
  Translation CSV files can be selected through the GUI.

  Default database path: media_organizer.db
          """
    )
    
    parser.add_argument(
        '--db-path',
        default='media_organizer.db',
        help='Path to the SQLite database file (default: media_organizer.db)'
    )
    
    args = parser.parse_args()
    
    # Create and run the GUI application
    root = tk.Tk()
    app = GeoTranslationEditor(root, db_path=args.db_path)
    root.mainloop()

if __name__ == "__main__":
    main()