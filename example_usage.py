#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ejemplo Práctico: Cómo usar todas las features avanzadas

Este script demuestra diferentes casos de uso del sistema.
"""

import sys
from advanced_features import (
    analyze_hype_vs_substance,
    analyze_competition,
    generate_video_titles,
    calculate_content_score,
    comprehensive_topic_analysis
)


def example_1_quick_hype_check():
    """
    Caso 1: Check rápido de hype para un titular
    """
    print("\n" + "="*70)
    print("📊 EJEMPLO 1: Quick Hype Check")
    print("="*70)
    
    title = "AI Will Replace All Programmers by 2025"
    content = """
    Industry experts predict that AI coding assistants will completely
    replace human programmers very soon. This revolutionary change is
    coming and will transform everything!!!
    """
    
    result = analyze_hype_vs_substance(title, content)
    
    print(f"\n📰 Title: {title}")
    print(f"\n🎭 Verdict: {result['verdict'].upper()}")
    print(f"   Substance: {result['substance_score']:.1f}/10")
    print(f"   Hype: {result['hype_score']:.1f}/10")
    
    if result['red_flags']:
        print(f"\n🚩 Red Flags:")
        for flag in result['red_flags']:
            print(f"   - {flag}")
    
    print(f"\n💭 Reasoning: {result['reasoning']}")


def example_2_find_content_gaps():
    """
    Caso 2: Encontrar gaps de contenido en un tema
    """
    print("\n" + "="*70)
    print("🎯 EJEMPLO 2: Find Content Gaps")
    print("="*70)
    
    topic = "Claude 3.5 Sonnet vs GPT-4 Comparison"
    
    result = analyze_competition(topic)
    
    print(f"\n🔍 Topic: {topic}")
    print(f"\n📊 Saturation: {result['saturation_level'].upper()}")
    print(f"   Competition Score: {result['competition_score']:.1f}/10")
    
    print(f"\n💡 Unique Angles:")
    for i, angle in enumerate(result['unique_angles'], 1):
        print(f"   {i}. {angle}")
    
    print(f"\n🎯 Gap Opportunities:")
    for i, gap in enumerate(result['gap_opportunities'], 1):
        print(f"   {i}. {gap}")
    
    print(f"\n✅ Recommendation: {result['recommendation']}")


def example_3_generate_viral_titles():
    """
    Caso 3: Generar títulos virales para un tema
    """
    print("\n" + "="*70)
    print("✏️ EJEMPLO 3: Generate Viral Titles")
    print("="*70)
    
    topic = "OpenAI Releases GPT-5 with Video Understanding"
    
    result = generate_video_titles(topic)
    
    print(f"\n📹 Topic: {topic}")
    print(f"\n🏆 Top Title Ideas:")
    
    for i, title_data in enumerate(result['titles'][:3], 1):
        print(f"\n{i}. \"{title_data['title']}\"")
        print(f"   Viral Potential: {title_data['viral_potential']}/10")
        print(f"   Hook: {title_data['hook']}")
    
    print(f"\n🎨 Thumbnail Ideas:")
    for i, idea in enumerate(result['thumbnail_ideas'], 1):
        print(f"   {i}. {idea}")


def example_4_intelligent_scoring():
    """
    Caso 4: Scoring inteligente de múltiples temas
    """
    print("\n" + "="*70)
    print("📊 EJEMPLO 4: Intelligent Scoring")
    print("="*70)
    
    topics = [
        ("New AI Chip from NVIDIA", 0.85),
        ("Another ChatGPT Tutorial", 0.20),
        ("Breakthrough in Quantum AI", 0.95),
    ]
    
    print("\n🎯 Comparing Topics:\n")
    
    results = []
    for topic, novelty in topics:
        score = calculate_content_score(
            topic=topic,
            novelty_score=novelty,
            timing_factor=1.0
        )
        results.append((topic, score))
        
        priority_emoji = {'high': '🔥', 'medium': '👍', 'low': '⏸️'}[score['priority']]
        
        print(f"{priority_emoji} {topic}")
        print(f"   Score: {score['final_score']:.1f}/100")
        print(f"   Priority: {score['priority'].upper()}")
        print(f"   Breakdown: Novelty={score['breakdown']['novelty']:.1f}, "
              f"Substance={score['breakdown']['substance']:.1f}, "
              f"Opportunity={score['breakdown']['opportunity']:.1f}")
        print(f"   → {score['recommendation']}")
        print()
    
    # Ordenar por score
    results.sort(key=lambda x: x[1]['final_score'], reverse=True)
    
    print(f"🏆 Best Topic: {results[0][0]}")


def example_5_comprehensive_analysis():
    """
    Caso 5: Análisis completo de un tema
    """
    print("\n" + "="*70)
    print("🔬 EJEMPLO 5: Comprehensive Analysis")
    print("="*70)
    
    topic = "Meta Releases Llama 4 with 100B Parameters"
    content = """
    Meta AI announced Llama 4, a new open-source language model with 
    100 billion parameters. The model shows significant improvements 
    in code generation (+45%) and mathematical reasoning (+38%) compared 
    to Llama 3. Full model weights and research paper available on GitHub.
    Includes technical details and comprehensive benchmarks.
    """
    
    print(f"\n📰 Topic: {topic}\n")
    print("⏳ Running comprehensive analysis (this may take 10-20 seconds)...\n")
    
    result = comprehensive_topic_analysis(
        topic=topic,
        content=content,
        novelty_score=0.90,
        analyze_all=True
    )
    
    # Ya se imprime durante el análisis, solo mostramos resumen
    print("\n" + "="*70)
    print("📋 SUMMARY")
    print("="*70)
    
    print(f"\n🎯 Final Score: {result['score']['final_score']:.1f}/100")
    print(f"🏷️ Priority: {result['score']['priority'].upper()}")
    print(f"💡 {result['score']['recommendation']}")
    
    if result.get('hype_analysis'):
        print(f"\n📊 Hype vs Substance: {result['hype_analysis']['verdict'].upper()}")
        print(f"   Substance: {result['hype_analysis']['substance_score']:.1f}/10")
    
    if result.get('competition'):
        print(f"\n🎯 Competition: {result['competition']['saturation_level'].upper()}")
    
    if result.get('titles') and result['titles']['titles']:
        print(f"\n✏️ Best Title: \"{result['titles']['titles'][0]['title']}\"")


def example_6_batch_workflow():
    """
    Caso 6: Workflow para procesar múltiples temas
    """
    print("\n" + "="*70)
    print("🔄 EJEMPLO 6: Batch Topic Processing")
    print("="*70)
    
    # Temas del día
    daily_topics = [
        "OpenAI GPT-5 Announcement",
        "Google Gemini 2.0 Pro Released",
        "Meta Open Sources New AI Model",
        "Apple Intelligence Beta Update",
        "Anthropic Claude 4 Benchmarks"
    ]
    
    print(f"\n📝 Processing {len(daily_topics)} topics...\n")
    
    scored_topics = []
    
    for topic in daily_topics:
        # Score rápido (sin análisis completo para este ejemplo)
        score = calculate_content_score(
            topic=topic,
            novelty_score=0.80,  # Asumimos novelty promedio
            timing_factor=1.0
        )
        
        scored_topics.append({
            'topic': topic,
            'score': score['final_score'],
            'priority': score['priority']
        })
    
    # Ordenar por score
    scored_topics.sort(key=lambda x: x['score'], reverse=True)
    
    print("📊 Ranked Topics:\n")
    for i, item in enumerate(scored_topics, 1):
        emoji = {'high': '🔥', 'medium': '👍', 'low': '⏸️'}[item['priority']]
        print(f"{i}. {emoji} {item['topic']}")
        print(f"   Score: {item['score']:.1f}/100 | Priority: {item['priority'].upper()}")
    
    # Identificar top priority
    high_priority = [t for t in scored_topics if t['priority'] == 'high']
    
    print(f"\n✅ {len(high_priority)} HIGH priority topics found")
    print("💡 Recommendation: Focus on these for next videos!")


def main():
    """
    Menú principal
    """
    examples = {
        '1': ('Quick Hype Check', example_1_quick_hype_check),
        '2': ('Find Content Gaps', example_2_find_content_gaps),
        '3': ('Generate Viral Titles', example_3_generate_viral_titles),
        '4': ('Intelligent Scoring', example_4_intelligent_scoring),
        '5': ('Comprehensive Analysis', example_5_comprehensive_analysis),
        '6': ('Batch Workflow', example_6_batch_workflow),
    }
    
    print("\n" + "="*70)
    print("🚀 ADVANCED FEATURES - EXAMPLES")
    print("="*70)
    print("\nChoose an example to run:\n")
    
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")
    
    print(f"  7. Run ALL examples")
    print(f"  0. Exit")
    
    choice = input("\nEnter choice (0-7): ").strip()
    
    if choice == '0':
        print("\n👋 Goodbye!\n")
        return
    
    if choice == '7':
        # Run all
        for key in sorted(examples.keys()):
            examples[key][1]()
        
        print("\n" + "="*70)
        print("✅ ALL EXAMPLES COMPLETED")
        print("="*70)
        print("\n💡 Next steps:")
        print("   1. Try these features with your own topics")
        print("   2. Generate a daily digest: python daily_digest_optimized.py")
        print("   3. Check FASE3_README.md for more details\n")
        
    elif choice in examples:
        examples[choice][1]()
        
        print("\n" + "="*70)
        print("✅ EXAMPLE COMPLETED")
        print("="*70)
        print("\n💡 Run 'python example_usage.py' again to try other examples\n")
    else:
        print("\n❌ Invalid choice\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user\n")
        sys.exit(0)