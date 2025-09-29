#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test rápido del digest diario SIN batch processing
(Para testing rápido - batch tarda minutos)
"""

from dotenv import load_dotenv
load_dotenv()

print("\n" + "="*70)
print("🧪 QUICK DIGEST TEST (without batch)")
print("="*70)
print("\nThis is a fast test - skips batch processing for speed")
print("Full digest with batch: python daily_digest_optimized.py\n")

from daily_digest_optimized import generate_daily_digest

# Generar digest sin batch (mucho más rápido para testing)
result = generate_daily_digest(
    hours_back=48,  # Últimas 48 horas para tener más contenido
    max_topics=10,   # Solo top 10
    use_batch=False,  # Skip batch para velocidad
    save_to_file=True
)

print("\n" + "="*70)
print("📄 DIGEST PREVIEW")
print("="*70)
print(result['digest'][:800])
print("\n... (truncated)")
print("\n" + "="*70)
print(f"✅ Full digest saved to: {result['filepath']}")
print(f"\n📊 Quick Stats:")
print(f"   - Topics analyzed: {result['stats']['topics_analyzed']}")
print(f"   - Novel topics found: {result['stats']['novel_topics_found']}")
print(f"   - Time: {result['stats']['time_elapsed']:.1f}s")
print("="*70)
print("\n💡 To run with batch processing (50% cheaper):")
print("   python daily_digest_optimized.py")
print()