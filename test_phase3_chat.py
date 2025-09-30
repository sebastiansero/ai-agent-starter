#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test de integración Fase 3 con el chatbot
"""

import os
os.environ.setdefault('OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))

from agent import Agent

print("="*70)
print("TESTING PHASE 3 INTEGRATION WITH CHATBOT")
print("="*70)

agent = Agent(max_steps=8)

# Test 1: Daily Digest
print("\n[Test 1] Daily Digest Command")
print("-" * 70)
try:
    result = agent.run("Dame el daily digest de noticias de IA")
    print(f"✅ Result preview:\n{result[:500]}...")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Analyze Topic
print("\n[Test 2] Analyze Topic Command")
print("-" * 70)
try:
    result = agent.run("Analiza el tema 'Claude Sonnet 4.5' y dime si vale la pena hacer un video")
    print(f"✅ Result preview:\n{result[:500]}...")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Generate Titles
print("\n[Test 3] Generate Titles Command")
print("-" * 70)
try:
    result = agent.run("Genera títulos virales para un video sobre 'GPT-5 Release'")
    print(f"✅ Result preview:\n{result[:500]}...")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 4: Hype Analysis  
print("\n[Test 4] Hype Analysis Command")
print("-" * 70)
try:
    result = agent.run("Analiza si 'AI will replace all developers by 2025' es hype o tiene sustancia")
    print(f"✅ Result preview:\n{result[:500]}...")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*70)
print("TESTING COMPLETE")
print("="*70)