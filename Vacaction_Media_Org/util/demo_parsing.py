#!/usr/bin/env python3
"""
Demo script to show how the Google Search Auto-Translation parsing works
"""

import re
import requests
import urllib.parse
import time

def demonstrate_parsing():
    """Demonstrate the complete Google search and parsing process"""
    
    # Example search
    city_en = "Tokyo"
    country_en = "Japan"
    
    print("🚀 AUTO SEARCH GOOGLE PARSING DEMONSTRATION")
    print("=" * 60)
    print(f"🎯 Target: {city_en}, {country_en}")
    
    # Step 1: Create search query
    search_query = f"{country_en} {city_en} 中文名"
    encoded_query = urllib.parse.quote_plus(search_query)
    search_url = f"https://www.google.com/search?q={encoded_query}"
    
    print(f"\n📝 STEP 1: SEARCH QUERY CONSTRUCTION")
    print(f"   Original: '{search_query}'")
    print(f"   Encoded:  '{encoded_query}'")
    print(f"   URL:      {search_url}")
    
    # Step 2: HTTP Headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    
    print(f"\n🌐 STEP 2: HTTP REQUEST SETUP")
    print(f"   User-Agent: {headers['User-Agent'][:50]}...")
    print(f"   Accept-Language: {headers['Accept-Language']}")
    
    try:
        # Step 3: Make request
        print(f"\n⏳ STEP 3: MAKING GOOGLE SEARCH REQUEST...")
        start_time = time.time()
        response = requests.get(search_url, headers=headers, timeout=10)
        end_time = time.time()
        
        print(f"   ✅ Response received in {end_time - start_time:.2f}s")
        print(f"   📊 Status: {response.status_code}")
        print(f"   📄 Size: {len(response.text):,} characters")
        
        # Step 4: Extract Chinese characters
        print(f"\n🔍 STEP 4: EXTRACTING CHINESE CHARACTERS")
        chinese_pattern = r'[\u4e00-\u9fff]{2,6}(?:市|县|区|镇|村|城)?'
        chinese_matches = re.findall(chinese_pattern, response.text)
        
        print(f"   🔤 Pattern: {chinese_pattern}")
        print(f"   📊 Found: {len(chinese_matches)} Chinese sequences")
        print(f"   📋 First 20: {chinese_matches[:20]}")
        
        # Step 5: Filter and score
        print(f"\n⚖️  STEP 5: FILTERING & SCORING")
        
        common_words = {
            '搜索', '结果', '网页', '图片', '视频', '新闻', '地图', '更多', '设置', '工具', 
            '时间', '所有', '语言', '关于', '帮助', '隐私', '条款', '广告', '商务', '服务',
        }
        
        candidate_scores = {}
        
        for match in chinese_matches:
            if len(match) >= 2 and len(match) <= 8 and match not in common_words:
                score = 0
                score_details = []
                
                # City indicator bonus
                if match.endswith(('市', '县', '区', '镇', '村', '城')):
                    score += 3
                    score_details.append("city_indicator(+3)")
                
                # Length bonus
                if len(match) <= 4:
                    score += 2
                    score_details.append("short(+2)")
                elif len(match) <= 6:
                    score += 1
                    score_details.append("medium(+1)")
                
                # Frequency bonus
                count = response.text.count(match)
                freq_bonus = min(count - 1, 3)
                if freq_bonus > 0:
                    score += freq_bonus
                    score_details.append(f"freq({count}x,+{freq_bonus})")
                
                # Proximity bonus
                if city_en.lower() in response.text.lower():
                    city_index = response.text.lower().find(city_en.lower())
                    match_indices = [m.start() for m in re.finditer(re.escape(match), response.text)]
                    for match_index in match_indices:
                        distance = abs(match_index - city_index)
                        if distance < 200:
                            score += 5
                            score_details.append(f"proximity({distance}chars,+5)")
                            break
                
                if score > 1:  # Only track significant candidates
                    candidate_scores[match] = score
                    print(f"   🏙️  '{match}' → {score} ({', '.join(score_details)})")
        
        # Step 6: Sort and select top candidates
        print(f"\n🏆 STEP 6: FINAL RANKING")
        sorted_candidates = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)
        
        top_candidates = []
        for i, (candidate, score) in enumerate(sorted_candidates[:5], 1):
            top_candidates.append(candidate)
            print(f"   {i}. '{candidate}' (Score: {score})")
        
        print(f"\n✅ FINAL RESULT: {top_candidates}")
        print(f"📋 These would appear in the selection box for user choice")
        
        # Step 7: Show some actual HTML content for debugging
        print(f"\n👀 STEP 7: HTML CONTENT SAMPLE")
        # Find a section with Chinese characters
        lines = response.text.split('\n')
        chinese_lines = [line for line in lines if re.search(r'[\u4e00-\u9fff]', line)]
        
        if chinese_lines:
            print("   📄 Lines containing Chinese characters:")
            for i, line in enumerate(chinese_lines[:5], 1):
                clean_line = re.sub(r'<[^>]+>', '', line).strip()
                if clean_line and len(clean_line) < 100:
                    print(f"   {i}. {clean_line}")
        
        return top_candidates
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return []

if __name__ == "__main__":
    candidates = demonstrate_parsing()
    
    print(f"\n" + "=" * 60)
    print("🎯 SUMMARY: Auto Search Process")
    print("1. 🔍 Construct Google search query with Chinese keywords")
    print("2. 🌐 Send HTTP request with browser-like headers")
    print("3. 📄 Parse HTML response for Chinese character patterns")
    print("4. ⚖️  Score candidates based on multiple factors")
    print("5. 🏆 Rank and return top 5 candidates")
    print("6. 📋 Display in selection box for user choice")
    print(f"Final candidates: {candidates}")