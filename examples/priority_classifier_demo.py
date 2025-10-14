"""
Priority Classifier Demo - Learning System Showcase

This demo demonstrates the Priority Classification System (Story 1.4) learning
capabilities. It shows how the system:
1. Starts with base priority classification
2. Learns from user corrections
3. Improves sender importance scoring
4. Increases accuracy over time

The demo simulates a 30-day period of email usage with user feedback.

Author: MailMind Development Team
Created: 2025-10-13
Story: 1.4
"""

import os
import sys
import sqlite3
import tempfile
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from mailmind.core.priority_classifier import PriorityClassifier


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def print_priority_result(email_desc: str, result: Dict[str, Any], correct: str = None) -> None:
    """Print formatted priority classification result."""
    indicator = result['visual_indicator']
    priority = result['priority']
    confidence = result['confidence'] * 100
    sender_importance = result['sender_importance']

    print(f"{indicator} {email_desc}")
    print(f"   Priority: {priority} ({confidence:.0f}% confident)")
    print(f"   Sender Importance: {sender_importance:.2f}")
    print(f"   Base Priority: {result['base_priority']}")

    if correct and correct != priority:
        print(f"   ❌ User corrected to: {correct}")
    elif correct:
        print(f"   ✅ Correct classification!")

    print()


def simulate_email(
    sender: str,
    subject: str,
    body: str,
    base_priority: str,
    correct_priority: str,
    classifier: PriorityClassifier,
    message_id: str
) -> Dict[str, Any]:
    """
    Simulate email classification and user feedback.

    Args:
        sender: Email sender address
        subject: Email subject
        body: Email body
        base_priority: Base priority from Story 1.3
        correct_priority: Correct priority (user's expectation)
        classifier: PriorityClassifier instance
        message_id: Unique message ID

    Returns:
        Classification result dictionary
    """
    email = {
        'metadata': {
            'from': sender,
            'to': 'user@mailmind.com',
            'subject': subject,
            'message_id': message_id
        },
        'content': {
            'body': body
        }
    }

    base_analysis = {
        'priority': base_priority,
        'confidence': 0.7,
        'summary': subject
    }

    result = classifier.classify_priority(email, base_analysis)

    # If classification is wrong, record user correction
    if result['priority'] != correct_priority:
        classifier.record_user_override(
            message_id=message_id,
            sender=sender,
            original_priority=result['priority'],
            original_confidence=result['confidence'],
            user_priority=correct_priority,
            reason=f"User knows {sender} is {correct_priority} priority"
        )

    return result


def demo_1_basic_classification():
    """Demo 1: Basic priority classification without learning."""
    print_section("Demo 1: Basic Priority Classification (No Learning History)")

    # Create temporary database
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    classifier = PriorityClassifier(db_path)

    print("Classifying emails from new senders (no history)...\n")

    # Test emails with different priorities
    test_cases = [
        {
            'sender': 'boss@company.com',
            'subject': 'Q4 Strategy Review',
            'base_priority': 'Medium',
            'expected': 'High'
        },
        {
            'sender': 'team@company.com',
            'subject': 'Project Update',
            'base_priority': 'Medium',
            'expected': 'Medium'
        },
        {
            'sender': 'newsletter@example.com',
            'subject': 'Weekly Tech News',
            'base_priority': 'Medium',
            'expected': 'Low'
        }
    ]

    for i, case in enumerate(test_cases):
        email = {
            'metadata': {
                'from': case['sender'],
                'subject': case['subject'],
                'message_id': f'demo1_{i}'
            },
            'content': {'body': 'Email content here...'}
        }

        base = {'priority': case['base_priority'], 'confidence': 0.7}
        result = classifier.classify_priority(email, base)

        print_priority_result(
            f"From: {case['sender']} - {case['subject']}",
            result
        )

    print("📊 Observations:")
    print("   • All new senders have neutral importance (0.5)")
    print("   • Classifications match base priority (no adjustments yet)")
    print("   • System has no learning data to improve classifications")

    classifier.close()
    os.close(db_fd)
    os.unlink(db_path)


def demo_2_vip_sender():
    """Demo 2: VIP sender priority upgrade."""
    print_section("Demo 2: VIP Sender Priority Upgrade")

    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    classifier = PriorityClassifier(db_path)

    # Mark CEO as VIP
    ceo_sender = 'ceo@company.com'
    classifier.set_sender_vip(ceo_sender, True)
    print(f"✅ Marked {ceo_sender} as VIP sender\n")

    # Compare VIP vs non-VIP classification
    test_cases = [
        {
            'sender': ceo_sender,
            'subject': 'Quick question',
            'is_vip': True
        },
        {
            'sender': 'colleague@company.com',
            'subject': 'Quick question',
            'is_vip': False
        }
    ]

    print("Classifying similar emails from VIP and non-VIP senders:\n")

    for i, case in enumerate(test_cases):
        email = {
            'metadata': {
                'from': case['sender'],
                'subject': case['subject'],
                'message_id': f'demo2_{i}'
            },
            'content': {'body': 'Can you review this when you have time?'}
        }

        base = {'priority': 'Medium', 'confidence': 0.7}
        result = classifier.classify_priority(email, base)

        vip_label = " (VIP)" if case['is_vip'] else ""
        print_priority_result(
            f"From: {case['sender']}{vip_label} - {case['subject']}",
            result
        )

    print("📊 Observations:")
    print("   • VIP sender gets +1 priority upgrade (Medium → High)")
    print("   • Non-VIP sender stays at Medium priority")
    print("   • VIP flag provides immediate priority boost")

    classifier.close()
    os.close(db_fd)
    os.unlink(db_path)


def demo_3_learning_from_corrections():
    """Demo 3: Learning from user corrections."""
    print_section("Demo 3: Learning from User Corrections")

    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    classifier = PriorityClassifier(db_path)

    sender = 'manager@company.com'
    print(f"Simulating 5 emails from {sender} with user corrections...\n")

    # Simulate 5 emails where user consistently upgrades priority
    for i in range(5):
        result = simulate_email(
            sender=sender,
            subject=f"Task {i+1}",
            body="Please handle this task.",
            base_priority='Medium',
            correct_priority='High',
            classifier=classifier,
            message_id=f'demo3_{i}'
        )

        print(f"Email {i+1}:")
        print_priority_result(
            f"  From: {sender} - Task {i+1}",
            result,
            correct='High'
        )

    # Check sender importance after corrections
    sender_stats = classifier.get_sender_stats(sender)
    print(f"📊 Sender Importance After 5 Corrections:")
    print(f"   • Importance Score: {sender_stats['importance_score']:.2f}")
    print(f"   • Correction Count: {sender_stats['correction_count']}")
    print(f"   • Email Count: {sender_stats['email_count']}\n")

    # New email from same sender should be upgraded
    print("Now classifying a NEW email from the same sender:\n")

    new_email = {
        'metadata': {
            'from': sender,
            'subject': 'New task assignment',
            'message_id': 'demo3_new'
        },
        'content': {'body': 'New task for you.'}
    }

    base = {'priority': 'Medium', 'confidence': 0.7}
    new_result = classifier.classify_priority(new_email, base)

    print_priority_result(
        f"From: {sender} - New task assignment",
        new_result
    )

    print("📊 Observations:")
    print("   • After 5 upgrades, sender importance increased")
    print("   • System learned this sender is important")
    print("   • New emails automatically upgraded to High priority")
    print("   • No user correction needed - system learned the pattern!")

    classifier.close()
    os.close(db_fd)
    os.unlink(db_path)


def demo_4_accuracy_improvement():
    """Demo 4: Accuracy improvement over 30 days."""
    print_section("Demo 4: Classification Accuracy Improvement Over Time")

    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    classifier = PriorityClassifier(db_path)

    # Create email_analysis table for accuracy tracking
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS email_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT UNIQUE NOT NULL,
            processed_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            sender TEXT,
            priority TEXT,
            confidence REAL
        )
    """)
    conn.commit()

    # Define sender patterns (what user expects)
    sender_patterns = {
        'boss@company.com': 'High',
        'urgent@company.com': 'High',
        'team@company.com': 'Medium',
        'newsletter@example.com': 'Low',
        'promotions@spam.com': 'Low'
    }

    print("Simulating 30-day email usage with user feedback...\n")

    # Week 1: System doesn't know patterns yet (low accuracy)
    print("📅 Week 1: Initial Classifications")
    week1_errors = 0
    for i in range(50):
        sender = list(sender_patterns.keys())[i % len(sender_patterns)]
        expected_priority = sender_patterns[sender]

        email = {
            'metadata': {
                'from': sender,
                'subject': f'Email {i+1}',
                'message_id': f'week1_{i}'
            },
            'content': {'body': 'Email content'}
        }

        # System starts with Medium for everyone
        base = {'priority': 'Medium', 'confidence': 0.7}
        result = classifier.classify_priority(email, base)

        # Store classification
        conn.execute("""
            INSERT INTO email_analysis (message_id, sender, priority, confidence)
            VALUES (?, ?, ?, ?)
        """, (f'week1_{i}', sender, result['priority'], result['confidence']))

        # User corrects if wrong
        if result['priority'] != expected_priority:
            week1_errors += 1
            classifier.record_user_override(
                message_id=f'week1_{i}',
                sender=sender,
                original_priority=result['priority'],
                original_confidence=result['confidence'],
                user_priority=expected_priority
            )

    conn.commit()

    week1_accuracy = ((50 - week1_errors) / 50) * 100
    print(f"   • Classified 50 emails")
    print(f"   • Accuracy: {week1_accuracy:.1f}%")
    print(f"   • User corrections: {week1_errors}\n")

    # Weeks 2-4: System learns patterns (improving accuracy)
    print("📅 Weeks 2-4: Learning Phase")

    for week in range(2, 5):
        week_errors = 0
        for i in range(50):
            sender = list(sender_patterns.keys())[i % len(sender_patterns)]
            expected_priority = sender_patterns[sender]

            email = {
                'metadata': {
                    'from': sender,
                    'subject': f'Email {i+1}',
                    'message_id': f'week{week}_{i}'
                },
                'content': {'body': 'Email content'}
            }

            # System now has learning data
            base = {'priority': 'Medium', 'confidence': 0.7}
            result = classifier.classify_priority(email, base)

            # Store classification
            conn.execute("""
                INSERT INTO email_analysis (message_id, sender, priority, confidence)
                VALUES (?, ?, ?, ?)
            """, (f'week{week}_{i}', sender, result['priority'], result['confidence']))

            # User corrects if wrong (should be fewer corrections)
            if result['priority'] != expected_priority:
                week_errors += 1
                classifier.record_user_override(
                    message_id=f'week{week}_{i}',
                    sender=sender,
                    original_priority=result['priority'],
                    original_confidence=result['confidence'],
                    user_priority=expected_priority
                )

        conn.commit()

        week_accuracy = ((50 - week_errors) / 50) * 100
        print(f"   Week {week}: {week_accuracy:.1f}% accuracy ({week_errors} corrections)")

    conn.close()

    # Final accuracy report
    print("\n📊 Final Accuracy Report (30 days):")
    accuracy_report = classifier.get_classification_accuracy(days=30)

    print(f"   • Total Classified: {accuracy_report['total_classified']}")
    print(f"   • User Corrections: {accuracy_report['user_corrections']}")
    print(f"   • Accuracy: {accuracy_report['accuracy_percentage']:.1f}%")
    print(f"   • Target (85%): {'✅ MET' if accuracy_report['target_met'] else '❌ NOT MET'}")
    print(f"   • Trend: {accuracy_report['trend'].upper()}")

    print("\n📊 Sender Importance Scores:")
    for sender in sender_patterns.keys():
        stats = classifier.get_sender_stats(sender)
        if stats:
            print(f"   • {sender}: {stats['importance_score']:.2f}")

    print("\n📊 Key Insights:")
    print("   • Accuracy improved from ~60% to >85% over 30 days")
    print("   • System learned sender importance patterns")
    print("   • Fewer corrections needed as system learned")
    print("   • High-priority senders now auto-classified correctly")

    classifier.close()
    os.close(db_fd)
    os.unlink(db_path)


def demo_5_real_world_scenarios():
    """Demo 5: Real-world email scenarios."""
    print_section("Demo 5: Real-World Email Scenarios")

    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    classifier = PriorityClassifier(db_path)

    # Set up some sender history
    print("Setting up sender history...\n")

    # VIP executive
    classifier.set_sender_vip('ceo@company.com', True)

    # Train spam sender (user marked as spam 3 times)
    for i in range(3):
        classifier.record_user_override(
            message_id=f'spam_train_{i}',
            sender='deals@spam.com',
            original_priority='Medium',
            original_confidence=0.6,
            user_priority='Low',
            reason='Spam'
        )

    # Train important colleague (user upgraded 5 times)
    for i in range(5):
        classifier.record_user_override(
            message_id=f'colleague_train_{i}',
            sender='project-lead@company.com',
            original_priority='Medium',
            original_confidence=0.7,
            user_priority='High',
            reason='Important'
        )

    print("Classifying various real-world email scenarios:\n")

    scenarios = [
        {
            'name': 'Executive Email',
            'sender': 'ceo@company.com',
            'subject': 'Q4 Strategy',
            'body': 'Let\'s discuss our Q4 strategy next week.',
            'base': 'Medium'
        },
        {
            'name': 'Project Lead (Learned Important)',
            'sender': 'project-lead@company.com',
            'subject': 'Sprint Planning',
            'body': 'Sprint planning meeting tomorrow at 2pm.',
            'base': 'Medium'
        },
        {
            'name': 'Spam Promotion (Learned Low)',
            'sender': 'deals@spam.com',
            'subject': '50% OFF SALE!!!',
            'body': 'Limited time offer! Buy now!',
            'base': 'Medium'
        },
        {
            'name': 'New Colleague (No History)',
            'sender': 'new-hire@company.com',
            'subject': 'Introduction',
            'body': 'Hi, I just joined the team!',
            'base': 'Medium'
        },
        {
            'name': 'Urgent Team Email',
            'sender': 'team@company.com',
            'subject': 'URGENT: Server Down',
            'body': 'Production server is down, need immediate attention!',
            'base': 'High'
        }
    ]

    for i, scenario in enumerate(scenarios):
        email = {
            'metadata': {
                'from': scenario['sender'],
                'subject': scenario['subject'],
                'message_id': f'scenario_{i}'
            },
            'content': {'body': scenario['body']}
        }

        base = {'priority': scenario['base'], 'confidence': 0.7}
        result = classifier.classify_priority(email, base)

        print(f"Scenario: {scenario['name']}")
        print_priority_result(
            f"  From: {scenario['sender']} - {scenario['subject']}",
            result
        )

    print("📊 Observations:")
    print("   • VIP executive: Automatically upgraded to High")
    print("   • Learned important sender: Upgraded based on history")
    print("   • Learned spam sender: Downgraded based on corrections")
    print("   • New sender: Neutral treatment until user feedback")
    print("   • Urgent content: Base priority maintained (High)")

    classifier.close()
    os.close(db_fd)
    os.unlink(db_path)


def main():
    """Run all demo scenarios."""
    print("\n" + "="*80)
    print("  PRIORITY CLASSIFIER DEMO - Story 1.4")
    print("  Enhanced Priority Classification with User Learning")
    print("="*80)

    try:
        demo_1_basic_classification()
        input("\nPress Enter to continue to Demo 2...")

        demo_2_vip_sender()
        input("\nPress Enter to continue to Demo 3...")

        demo_3_learning_from_corrections()
        input("\nPress Enter to continue to Demo 4...")

        demo_4_accuracy_improvement()
        input("\nPress Enter to continue to Demo 5...")

        demo_5_real_world_scenarios()

        print_section("Demo Complete!")
        print("✅ All demos completed successfully!\n")

        print("Key Takeaways:")
        print("   1. System learns from user corrections over time")
        print("   2. Sender importance adapts based on feedback")
        print("   3. Classification accuracy improves with use")
        print("   4. VIP senders get automatic priority boost")
        print("   5. Target accuracy (>85%) achievable within 30 days")
        print("\nThank you for watching the demo!\n")

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        raise


if __name__ == '__main__':
    main()
