#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test Substack feeds"""

import feedparser
from datetime import datetime, timedelta

print('🔍 Probando feeds de Substack...\n')

substacks = [
    {'name': 'Import AI', 'rss': 'https://jack-clark.net/feed/'},
    {'name': 'One Useful Thing', 'rss': 'https://www.oneusefulthing.org/feed'},
    {'name': 'Latent Space', 'rss': 'https://www.latent.space/feed'},
    {'name': "Ben's Bites", 'rss': 'https://bensbites.beehiiv.com/feed'},
    {'name': 'Simon Willison', 'rss': 'https://simonwillison.net/atom/everything/'},
]

cutoff = datetime.now() - timedelta(days=7)

for sub in substacks:
    print(f"📝 {sub['name']}:")
    try:
        feed = feedparser.parse(sub['rss'])
        
        if feed.bozo:
            print(f"   ⚠️  Error parsing: {feed.bozo_exception}")
            continue
            
        if not feed.entries:
            print(f"   ⚠️  No entries found")
            continue
            
        recent = 0
        for entry in feed.entries[:5]:
            try:
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    pub_date = datetime(*entry.updated_parsed[:6])
                else:
                    pub_date = datetime.now()
                
                if pub_date > cutoff:
                    recent += 1
                    title = entry.get('title', 'No title')[:60]
                    date_str = pub_date.strftime('%Y-%m-%d')
                    print(f"   ✅ {title}...")
                    print(f"      {date_str}")
            except Exception as e:
                print(f"   ⚠️  Error processing entry: {e}")
                
        if recent == 0:
            print(f"   ℹ️  No recent posts (last 7 days)")
        else:
            print(f"   📊 Total recent: {recent} posts")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()

print("\n✅ Test completed")