"""
Email Analysis Pipeline Demo

Demonstrates the complete email analysis pipeline for Story 1.3:
Raw Email → Preprocessing → LLM Analysis → Structured Results → Caching

Integration: OllamaManager (1.1) + EmailPreprocessor (1.2) + EmailAnalysisEngine (1.3)
"""

import sys
import os
import json
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.mailmind.core.ollama_manager import OllamaManager
from src.mailmind.core.email_analysis_engine import EmailAnalysisEngine
from src.mailmind.utils.config import load_config, get_ollama_config


def demo_single_email_analysis():
    """Demo: Analyze a single email end-to-end."""
    print("=" * 70)
    print("DEMO 1: Single Email Analysis")
    print("=" * 70)

    # Sample urgent email
    email = {
        'from': 'alice@company.com (Alice Smith - CFO)',
        'subject': 'URGENT: Q4 Budget Overrun - Action Required',
        'body': '''Hi team,

I've just reviewed the Q4 financials and we're tracking 12% over budget - this is critical.

We need to:
1. Review all pending expenses immediately
2. Identify cost reduction opportunities
3. Schedule an emergency budget meeting this week

Please send your department's spending analysis by Friday COB. This is top priority.

The board meeting is next Tuesday and we need concrete numbers.

Thanks,
Alice

--
Alice Smith
Chief Financial Officer
Acme Corporation
Phone: 555-1234
alice@company.com''',
        'date': '2025-10-13T09:15:00Z',
        'message_id': 'msg_urgent_budget_001'
    }

    # Initialize components
    print("\n1. Initializing Ollama...")
    config = load_config()
    ollama_config = get_ollama_config(config)
    ollama = OllamaManager(ollama_config)

    success, message = ollama.initialize()
    if not success:
        print(f"❌ Ollama initialization failed: {message}")
        return

    print(f"✓ Ollama ready: {ollama.current_model}")

    # Create analysis engine
    print("\n2. Creating Email Analysis Engine...")
    engine = EmailAnalysisEngine(ollama, db_path='data/demo_mailmind.db')
    print("✓ Engine ready")

    # Analyze email
    print("\n3. Analyzing email...")
    print(f"   From: {email['from']}")
    print(f"   Subject: {email['subject']}")

    start_time = time.time()
    analysis = engine.analyze_email(email)
    elapsed = time.time() - start_time

    print(f"\n✓ Analysis complete in {elapsed:.2f}s")

    # Display results
    print("\n" + "=" * 70)
    print("ANALYSIS RESULTS")
    print("=" * 70)

    print(f"\n🔴 Priority: {analysis['priority']} (confidence: {analysis['confidence']:.2f})")
    print(f"\n📊 Sentiment: {analysis['sentiment']}")

    print(f"\n📝 Summary:")
    print(f"   {analysis['summary']}")

    if analysis['tags']:
        print(f"\n🏷️  Tags: {', '.join(analysis['tags'])}")

    if analysis['action_items']:
        print(f"\n✅ Action Items:")
        for i, action in enumerate(analysis['action_items'], 1):
            print(f"   {i}. {action}")

    print(f"\n⚡ Performance:")
    print(f"   Processing time: {analysis['processing_time_ms']}ms")
    print(f"   Tokens/second: {analysis.get('tokens_per_second', 0):.1f}")
    print(f"   Model: {analysis['model_version']}")
    print(f"   Cache hit: {analysis['cache_hit']}")

    print()


def demo_cache_performance():
    """Demo: Show caching performance (2nd analysis should be instant)."""
    print("=" * 70)
    print("DEMO 2: Cache Performance")
    print("=" * 70)

    email = {
        'from': 'bob@company.com',
        'subject': 'Project Status Update',
        'body': 'The project is on track. We delivered Sprint 3 on time.',
        'date': '2025-10-13T10:00:00Z',
        'message_id': 'msg_project_status_001'
    }

    # Initialize
    config = load_config()
    ollama_config = get_ollama_config(config)
    ollama = OllamaManager(ollama_config)
    ollama.initialize()

    engine = EmailAnalysisEngine(ollama, db_path='data/demo_mailmind.db')

    # First analysis (cache miss)
    print("\n1. First analysis (cache miss)...")
    start1 = time.time()
    result1 = engine.analyze_email(email)
    time1 = (time.time() - start1) * 1000

    print(f"   Time: {time1:.0f}ms")
    print(f"   Cache hit: {result1['cache_hit']}")
    print(f"   Priority: {result1['priority']}")

    # Second analysis (cache hit)
    print("\n2. Second analysis (cache hit)...")
    start2 = time.time()
    result2 = engine.analyze_email(email)
    time2 = (time.time() - start2) * 1000

    print(f"   Time: {time2:.0f}ms")
    print(f"   Cache hit: {result2['cache_hit']}")
    print(f"   Priority: {result2['priority']}")

    # Show speedup
    speedup = time1 / time2 if time2 > 0 else 0
    print(f"\n⚡ Speedup: {speedup:.1f}x faster ({time1:.0f}ms → {time2:.0f}ms)")

    print()


def demo_batch_processing():
    """Demo: Batch process multiple emails."""
    print("=" * 70)
    print("DEMO 3: Batch Processing")
    print("=" * 70)

    emails = [
        {
            'from': 'marketing@company.com',
            'subject': 'Weekly Newsletter - October Edition',
            'body': 'Check out our latest products and services. Limited time offer!',
            'message_id': 'msg_newsletter_001'
        },
        {
            'from': 'manager@company.com',
            'subject': 'Team Meeting Tomorrow',
            'body': 'Reminder: Team standup meeting tomorrow at 10 AM in conference room B.',
            'message_id': 'msg_meeting_001'
        },
        {
            'from': 'client@external.com',
            'subject': 'Contract Review Needed ASAP',
            'body': 'Can you please review and sign the contract by end of day? This is blocking our Q4 launch.',
            'message_id': 'msg_contract_001'
        },
        {
            'from': 'support@company.com',
            'subject': 'Ticket #12345 Resolved',
            'body': 'Your support ticket has been resolved. Please let us know if you need further assistance.',
            'message_id': 'msg_support_001'
        },
        {
            'from': 'ceo@company.com',
            'subject': 'All Hands Meeting - Q4 Strategy',
            'body': 'Important: All hands meeting next Friday to discuss Q4 strategy and goals. Attendance is mandatory.',
            'message_id': 'msg_allhands_001'
        }
    ]

    # Initialize
    config = load_config()
    ollama_config = get_ollama_config(config)
    ollama = OllamaManager(ollama_config)
    ollama.initialize()

    engine = EmailAnalysisEngine(ollama, db_path='data/demo_mailmind.db')

    # Progress callback
    def progress(current, total, result):
        print(f"   [{current}/{total}] {result['priority']:6} - {result.get('subject', 'Unknown')[:40]}")

    print(f"\nProcessing {len(emails)} emails...\n")

    start_time = time.time()
    results = engine.analyze_batch(emails, callback=progress)
    elapsed = time.time() - start_time

    # Summary
    print(f"\n✓ Batch complete in {elapsed:.1f}s")
    print(f"   Throughput: {len(emails) / elapsed * 60:.1f} emails/minute")

    # Priority distribution
    high = sum(1 for r in results if r['priority'] == 'High')
    medium = sum(1 for r in results if r['priority'] == 'Medium')
    low = sum(1 for r in results if r['priority'] == 'Low')

    print(f"\n📊 Priority Distribution:")
    print(f"   🔴 High: {high}")
    print(f"   🟡 Medium: {medium}")
    print(f"   🔵 Low: {low}")

    print()


def demo_progressive_disclosure():
    """Demo: Show progressive disclosure pattern."""
    print("=" * 70)
    print("DEMO 4: Progressive Disclosure Pattern")
    print("=" * 70)

    email = {
        'from': 'executive@company.com',
        'subject': 'CRITICAL: Security Incident Response Needed',
        'body': '''Team,

We've detected a potential security incident affecting our production systems.

Immediate actions required:
1. Isolate affected systems
2. Begin forensic analysis
3. Notify security team
4. Prepare incident report

This is a P0 incident. Please respond within 15 minutes.

-Security Team''',
        'message_id': 'msg_security_001'
    }

    # Initialize
    config = load_config()
    ollama_config = get_ollama_config(config)
    ollama = OllamaManager(ollama_config)
    ollama.initialize()

    engine = EmailAnalysisEngine(ollama, db_path='data/demo_mailmind.db')

    # Preprocess email
    preprocessed = engine.preprocessor.preprocess_email(email)

    # Phase 1: Quick priority (<500ms)
    print("\n⚡ Phase 1: Quick Priority (<500ms)")
    start = time.time()
    quick_priority = engine._quick_priority_heuristic(preprocessed)
    phase1_time = (time.time() - start) * 1000

    print(f"   🔴 Priority: {quick_priority}")
    print(f"   Time: {phase1_time:.1f}ms")

    # Phase 2+3: Full LLM analysis (<2-3s)
    print("\n🧠 Phase 2+3: Full Analysis (<2-3s)")
    start = time.time()
    analysis = engine.analyze_email(email)
    phase23_time = (time.time() - start) * 1000

    print(f"   📝 Summary: {analysis['summary'][:60]}...")
    print(f"   🏷️  Tags: {', '.join(analysis['tags'][:3])}")
    print(f"   Time: {phase23_time:.1f}ms")

    print(f"\n✓ Total perceived latency: {phase1_time:.1f}ms (instant priority)")
    print(f"   User sees priority immediately, then details appear")

    print()


def demo_statistics():
    """Demo: Show analysis statistics."""
    print("=" * 70)
    print("DEMO 5: Analysis Statistics")
    print("=" * 70)

    # Initialize
    config = load_config()
    ollama_config = get_ollama_config(config)
    ollama = OllamaManager(ollama_config)
    ollama.initialize()

    engine = EmailAnalysisEngine(ollama, db_path='data/demo_mailmind.db')

    print("\nRetrieving statistics...")
    stats = engine.get_analysis_stats()

    if stats.get('total_analyses', 0) == 0:
        print("\n⚠️  No analyses in database yet. Run other demos first.")
        print()
        return

    print(f"\n📊 Overall Statistics:")
    print(f"   Total analyses: {stats['total_analyses']}")
    print(f"   Cache hit rate: {stats['cache_hit_rate_percent']:.1f}%")
    print(f"   Avg processing time: {stats['avg_processing_time_ms']:.0f}ms")
    print(f"   Avg tokens/second: {stats['avg_tokens_per_second']:.1f}")

    if stats.get('priority_distribution'):
        print(f"\n🎯 Priority Distribution:")
        for priority, count in stats['priority_distribution'].items():
            percent = (count / stats['total_analyses'] * 100) if stats['total_analyses'] > 0 else 0
            emoji = {'High': '🔴', 'Medium': '🟡', 'Low': '🔵'}.get(priority, '⚪')
            print(f"   {emoji} {priority}: {count} ({percent:.1f}%)")

    print()


def demo_complete_pipeline():
    """Demo: Show complete pipeline from raw email to analysis."""
    print("=" * 70)
    print("DEMO 6: Complete Pipeline Visualization")
    print("=" * 70)

    email = {
        'from': 'partner@external.com (Sarah Johnson)',
        'subject': 'Re: Partnership Proposal - Next Steps',
        'body_html': '''
            <html>
                <body>
                    <p>Hi there,</p>
                    <p>Thanks for the detailed proposal. I've reviewed it with our team and we're
                    very interested in moving forward.</p>
                    <p>Can we schedule a call next week to discuss the timeline and pricing?
                    We're targeting a Q1 launch.</p>
                    <p>Best regards,<br/>Sarah</p>
                    --
                    <p>Sarah Johnson<br/>
                    VP of Partnerships<br/>
                    TechCorp Inc.</p>
                </body>
            </html>
        ''',
        'attachments': [
            {'filename': 'proposal_review.pdf', 'size': 1500000}
        ],
        'date': '2025-10-13T14:30:00Z',
        'message_id': 'msg_partnership_001',
        'in_reply_to': 'msg_partnership_000',
        'references': 'msg_partnership_000'
    }

    # Initialize
    config = load_config()
    ollama_config = get_ollama_config(config)
    ollama = OllamaManager(ollama_config)
    ollama.initialize()

    engine = EmailAnalysisEngine(ollama, db_path='data/demo_mailmind.db')

    print("\n📧 Raw Email Input:")
    print(f"   From: {email['from']}")
    print(f"   Subject: {email['subject']}")
    print(f"   Format: HTML with attachment")

    print("\n↓ [Step 1: Email Preprocessing]")
    print("   - Parse HTML → plain text")
    print("   - Extract metadata")
    print("   - Strip signature")
    print("   - Handle attachments")

    print("\n↓ [Step 2: Check Cache]")
    print("   - Query: message_id = 'msg_partnership_001'")

    print("\n↓ [Step 3: LLM Analysis]")
    print("   - Build structured prompt")
    print("   - Call OllamaManager.generate()")
    print("   - Parse JSON response")

    print("\n↓ [Step 4: Store in Cache]")
    print("   - Save to email_analysis table")
    print("   - Log performance metrics")

    # Run actual analysis
    print("\n🚀 Running pipeline...")
    start_time = time.time()
    analysis = engine.analyze_email(email)
    elapsed = time.time() - start_time

    print(f"\n✓ Pipeline complete in {elapsed:.2f}s\n")

    # Show final output
    print("=" * 70)
    print("FINAL ANALYSIS OUTPUT")
    print("=" * 70)
    print(json.dumps(analysis, indent=2))
    print()


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║  EMAIL ANALYSIS ENGINE DEMO (Story 1.3)                          ║")
    print("║  Integration: Ollama (1.1) + Preprocessing (1.2) + Analysis (1.3)║")
    print("╚" + "=" * 68 + "╝")
    print()

    demos = [
        ("Single Email Analysis", demo_single_email_analysis),
        ("Cache Performance", demo_cache_performance),
        ("Batch Processing", demo_batch_processing),
        ("Progressive Disclosure", demo_progressive_disclosure),
        ("Analysis Statistics", demo_statistics),
        ("Complete Pipeline", demo_complete_pipeline)
    ]

    # Check if Ollama is available
    try:
        config = load_config()
        ollama_config = get_ollama_config(config)
        ollama = OllamaManager(ollama_config)
        success, message = ollama.initialize()

        if not success:
            print("❌ Error: Ollama not available")
            print(f"   {message}")
            print("\nPlease ensure:")
            print("1. Ollama is installed and running")
            print("2. Model is downloaded: ollama pull llama3.1:8b-instruct-q4_K_M")
            return

    except Exception as e:
        print(f"❌ Error initializing: {e}")
        return

    # Run demos
    for name, demo_func in demos:
        try:
            demo_func()
        except KeyboardInterrupt:
            print("\n\n⚠️  Demo interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Demo '{name}' failed: {e}")
            import traceback
            traceback.print_exc()
            print()

    print("=" * 70)
    print("All demos completed!")
    print("=" * 70)
    print("\nDatabase location: data/demo_mailmind.db")
    print("Check the database for cached analyses and performance metrics.")
    print()


if __name__ == '__main__':
    main()
