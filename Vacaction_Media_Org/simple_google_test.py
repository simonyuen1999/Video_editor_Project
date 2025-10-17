#!/usr/bin/env python3
"""
Simple test to debug Google search response decompression
"""

import requests
import time

def test_google_search():
    print("Testing Google search with proper compression handling...")
    
    # Use the same URL as our main script
    url = "https://www.google.com/search?q=Tokyo+Japan+chinese+name+translation"
    
    # Simple headers to avoid being flagged as bot
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate',  # Remove 'br' to avoid Brotli issues
        'Connection': 'keep-alive'
    }
    
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"\nResponse status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Content-Encoding: {response.headers.get('Content-Encoding')}")
        print(f"Content-Length: {len(response.content)} bytes")
        print(f"Text length: {len(response.text)} characters")
        
        # Check if we can see HTML structure
        text_content = response.text
        print(f"\nFirst 500 characters:")
        print(repr(text_content[:500]))
        
        # Check for Google-specific content
        if '<html' in text_content:
            print("\n✅ Valid HTML detected")
        else:
            print("\n❌ Not valid HTML")
            
        if 'google' in text_content.lower():
            print("✅ Google content detected")
        else:
            print("❌ No Google content detected")
            
        # Look for Chinese characters
        import re
        chinese_matches = re.findall(r'[\u4e00-\u9fff]+', text_content)
        print(f"\nChinese characters found: {len(chinese_matches)}")
        if chinese_matches:
            print(f"First 10 matches: {chinese_matches[:10]}")
        
        # Save for inspection
        with open('simple_test_google.html', 'w', encoding='utf-8') as f:
            f.write(text_content)
        print(f"\nSaved to: simple_test_google.html")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_google_search()