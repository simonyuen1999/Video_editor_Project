#!/usr/bin/env python3
"""
Debug Google Search Response
Test script to debug the Google search response and identify encoding issues
"""

import requests
import urllib.parse
import re

def test_google_search_response():
    """Test Google search response and debug any issues"""
    
    city_en = "Ka Lung Court"
    country_en = "Hong Kong"
    search_query = f'"{city_en}" "{country_en}" 中文 翻译'
    encoded_query = urllib.parse.quote_plus(search_query)
    google_url = f"https://www.google.com/search?q={encoded_query}&hl=zh-CN&lr=lang_zh"
    
    print("🧪 GOOGLE SEARCH RESPONSE DEBUG TEST")
    print("=" * 50)
    print(f"🎯 Testing: {city_en}, {country_en}")
    print(f"📝 Query: '{search_query}'")
    print(f"🔗 URL: {google_url}")
    
    # Test different header configurations
    header_configs = [
        {
            "name": "Full Headers",
            "headers": {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Charset': 'utf-8',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none'
            }
        },
        {
            "name": "Simple Headers",
            "headers": {
                'User-Agent': 'Mozilla/5.0 (compatible; Python-requests)'
            }
        },
        {
            "name": "Minimal Headers",
            "headers": {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        }
    ]
    
    for config in header_configs:
        print(f"\n📋 Testing with {config['name']}:")
        print(f"   Headers: {config['headers']}")
        
        try:
            response = requests.get(google_url, headers=config['headers'], timeout=10)
            print(f"   📊 Status: {response.status_code}")
            print(f"   🔤 Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
            print(f"   📄 Content-Encoding: {response.headers.get('Content-Encoding', 'None')}")
            print(f"   📄 Response Encoding: {response.encoding}")
            
            if response.status_code == 200:
                # Check content
                content = response.text
                print(f"   📏 Content Length: {len(content)} chars")
                
                # Check for Chinese characters
                chinese_chars = re.findall(r'[\u4e00-\u9fff]', content)
                print(f"   🀄 Chinese Characters: {len(chinese_chars)} found")
                
                # Check if it looks like HTML
                if '<html' in content.lower()[:1000]:
                    print(f"   ✅ Valid HTML detected")
                else:
                    print(f"   ❌ Invalid or unusual content")
                
                # Show sample
                sample = content[:200].replace('\n', ' ').replace('\r', '')
                print(f"   📝 Sample: {sample}...")
                
                # Save debug file
                debug_filename = f"debug_{config['name'].replace(' ', '_')}_{city_en}_{country_en}.html"
                try:
                    with open(debug_filename, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"   💾 Saved: {debug_filename}")
                except Exception as e:
                    print(f"   ❌ Save failed: {e}")
                
                # Try to find some Chinese city names
                chinese_pattern = r'[\u4e00-\u9fff]{2,6}(?:市|县|区|镇|村|城)?'
                matches = re.findall(chinese_pattern, content)
                unique_matches = list(set(matches))[:10]  # First 10 unique matches
                print(f"   🏙️  Sample Chinese matches: {unique_matches}")
                
            else:
                print(f"   ❌ Failed with status: {response.status_code}")
                
        except Exception as e:
            print(f"   💥 Exception: {e}")
    
    print(f"\n✅ Debug test complete!")
    print(f"📋 Check the saved HTML files to see what Google is returning")

if __name__ == "__main__":
    test_google_search_response()