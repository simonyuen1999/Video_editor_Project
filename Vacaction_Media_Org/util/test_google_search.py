#!/usr/bin/env python3
"""
Test Google search URL generation for cities
"""

import urllib.parse
import webbrowser

def test_google_search_urls():
    """Test Google search URL generation for various cities"""
    
    test_cities = [
        ("Tokyo", "Japan"),
        ("New York", "United States"),
        ("Los Angeles", "United States"),
        ("London", "United Kingdom"),
        ("Paris", "France"),
        ("Hong Kong", "China"),
        ("Singapore", "Singapore")
    ]
    
    print("🔍 Google Search URL Generation Test")
    print("=" * 50)
    
    for city_en, country_en in test_cities:
        # Create Google search query (same as used in the application)
        search_query = f"{city_en} {country_en} 中文名"
        encoded_query = urllib.parse.quote_plus(search_query)
        google_url = f"https://www.google.com/search?q={encoded_query}"
        
        print(f"\n🏙️  {city_en}, {country_en}")
        print(f"   📝 Query: '{search_query}'")
        print(f"   🔗 URL: {google_url}")
        
    print(f"\n✅ Google search URL generation test complete!")
    print(f"📌 The app now opens Google search with Chinese name queries")

def demo_open_google_search():
    """Demo opening Google search for a specific city"""
    city_en = "Tokyo"
    country_en = "Japan"
    
    search_query = f"{city_en} {country_en} 中文名"
    encoded_query = urllib.parse.quote_plus(search_query)
    google_url = f"https://www.google.com/search?q={encoded_query}"
    
    print(f"\n🚀 DEMO: Opening Google search for {city_en}, {country_en}")
    print(f"🔗 URL: {google_url}")
    
    try:
        webbrowser.open(google_url)
        print(f"✅ Successfully opened Google search")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_google_search_urls()
    
    # Uncomment to actually open a Google search
    # demo_open_google_search()