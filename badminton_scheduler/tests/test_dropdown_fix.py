#!/usr/bin/env python3
"""
Simple test to verify dropdown fixes work.
"""

import re

def test_dropdown_fixes():
    """Test that the dropdown HTML is properly formatted."""
    
    # Read the HTML file
    with open('static/static_frontend.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Test play preference dropdown
    play_pref_pattern = r'<select id="playPreference"[^>]*>(.*?)</select>'
    play_pref_match = re.search(play_pref_pattern, content, re.DOTALL)
    
    if not play_pref_match:
        print("❌ Play preference dropdown not found!")
        return False
    
    play_pref_content = play_pref_match.group(1)
    expected_options = ['either', 'drop_in', 'book_court']
    
    for option in expected_options:
        if f'value="{option}"' not in play_pref_content:
            print(f"❌ Missing option: {option}")
            return False
    
    print("✅ Play preference dropdown is properly formatted")
    
    # Test rating dropdown
    rating_pattern = r'<select id="rating"[^>]*>(.*?)</select>'
    rating_match = re.search(rating_pattern, content, re.DOTALL)
    
    if not rating_match:
        print("❌ Rating dropdown not found!")
        return False
    
    rating_content = rating_match.group(1)
    expected_ratings = ['1', '2', '3', '4', '5']
    
    for rating in expected_ratings:
        if f'value="{rating}"' not in rating_content:
            print(f"❌ Missing rating: {rating}")
            return False
    
    print("✅ Rating dropdown is properly formatted")
    
    # Check for malformed HTML (empty select tags)
    if '</select>' in content and '<select' in content:
        # Look for empty select tags
        empty_select_pattern = r'<select[^>]*></select>'
        empty_selects = re.findall(empty_select_pattern, content)
        
        if empty_selects:
            print(f"❌ Found {len(empty_selects)} empty select tags!")
            return False
    
    print("✅ No malformed select tags found")
    
    return True

if __name__ == '__main__':
    print("🧪 Testing dropdown fixes...")
    print("=" * 40)
    
    if test_dropdown_fixes():
        print("=" * 40)
        print("✅ All dropdown tests passed!")
        print("🎉 Dropdowns are working correctly!")
    else:
        print("=" * 40)
        print("❌ Some dropdown tests failed!")
        print("🔧 Please check the HTML structure!")