"""
Response Generator Demo

Demonstrates Story 1.5: Response Generation Assistant features:
- Writing style analysis from sent emails
- Response generation in three lengths (Brief/Standard/Detailed)
- Four tone options (Professional/Friendly/Formal/Casual)
- Eight scenario templates
- Thread context incorporation
- Performance metrics

Requirements:
- Ollama must be running
- Llama 3.1 8B or Mistral 7B model must be available

Usage:
    python examples/response_generator_demo.py
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mailmind.core.ollama_manager import OllamaManager
from src.mailmind.core.email_preprocessor import EmailPreprocessor
from src.mailmind.core.writing_style_analyzer import WritingStyleAnalyzer
from src.mailmind.core.response_generator import ResponseGenerator
from src.mailmind.utils.config import load_config, get_ollama_config


def print_section(title):
    """Print section header."""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70 + "\n")


def print_subsection(title):
    """Print subsection header."""
    print("\n" + "-" * 70)
    print(title)
    print("-" * 70 + "\n")


def demo_1_writing_style_analysis():
    """Demo 1: Writing Style Analysis from Sent Emails."""
    print_section("DEMO 1: Writing Style Analysis")

    print("Analyzing writing style from sent emails...\n")

    # Sample sent emails
    sent_emails = [
        {
            'body': 'Hi John,\n\nThanks for reaching out about the project. I\'ll review the documentation and get back to you by end of week.\n\nThanks,\nAlice',
            'subject': 'Re: Project Documentation'
        },
        {
            'body': 'Hi Sarah,\n\nI can attend the meeting on Tuesday at 2pm. Looking forward to discussing the roadmap.\n\nBest,\nAlice',
            'subject': 'Re: Q4 Planning Meeting'
        },
        {
            'body': 'Hi Team,\n\nPlease review the attached proposal and let me know if you have any questions.\n\nThanks,\nAlice',
            'subject': 'Marketing Proposal Review'
        },
        {
            'body': 'Hi Mike,\n\nThanks for the update! The presentation looks great. I appreciate all your hard work on this.\n\nBest,\nAlice',
            'subject': 'Re: Client Presentation'
        },
        {
            'body': 'Hi Lisa,\n\nI wanted to follow up on our conversation from last week. Are you available for a quick call tomorrow?\n\nThanks,\nAlice',
            'subject': 'Follow-up: Strategy Discussion'
        },
    ]

    # Analyze style
    analyzer = WritingStyleAnalyzer(db_path='data/demo.db')
    profile = analyzer.analyze_sent_emails(sent_emails, profile_name='alice')

    print(f"✓ Writing style profile created from {profile['sample_size']} emails\n")
    print(f"Profile Details:")
    print(f"  Greeting Style: {profile['greeting_style']}")
    print(f"  Closing Style: {profile['closing_style']}")
    print(f"  Formality Level: {profile['formality_level']:.2f} (0.0=casual, 1.0=formal)")
    print(f"  Avg Sentence Length: {profile['avg_sentence_length']} words")

    if profile['common_phrases']:
        print(f"  Common Phrases: {', '.join(profile['common_phrases'][:3])}")

    print(f"\nTone Markers:")
    for marker, value in profile['tone_markers'].items():
        print(f"  {marker.capitalize()}: {value:.2f}")


def demo_2_response_lengths(ollama, preprocessor):
    """Demo 2: Response Generation in Three Lengths."""
    print_section("DEMO 2: Response Lengths (Brief / Standard / Detailed)")

    # Sample incoming email
    incoming_email = {
        'from': 'john.smith@company.com',
        'from_name': 'John Smith',
        'subject': 'Team Meeting Next Week',
        'body': '''Hi Alice,

I wanted to schedule a team meeting for next Tuesday at 2pm to discuss the Q4 roadmap and upcoming priorities.

Would you be available?

Thanks,
John''',
        'date': '2025-10-13T10:00:00Z',
        'message_id': 'meeting_001'
    }

    email = preprocessor.preprocess_email(incoming_email)
    generator = ResponseGenerator(ollama, db_path='data/demo.db')

    print("Original Email:")
    print(f"  From: {incoming_email['from_name']}")
    print(f"  Subject: {incoming_email['subject']}")
    print(f"\n  Body:\n{incoming_email['body']}\n")

    # Generate responses in all three lengths
    for length in ['Brief', 'Standard', 'Detailed']:
        print_subsection(f"{length} Response")

        start = time.time()
        result = generator.generate_response(email, length=length, tone='Professional')
        duration = time.time() - start

        print(f"Generated in {duration:.2f}s ({result['processing_time_ms']}ms)")
        print(f"Word count: {result['word_count']}")
        print(f"\nResponse:\n{result['response_text']}\n")

        # Performance evaluation
        targets = {'Brief': 3.0, 'Standard': 5.0, 'Detailed': 10.0}
        if duration < targets[length]:
            print(f"✓ Performance: EXCELLENT (under {targets[length]}s target)")
        elif duration < targets[length] * 1.5:
            print(f"✓ Performance: GOOD (acceptable range)")
        else:
            print(f"⚠ Performance: Slower than expected")


def demo_3_tone_variations(ollama, preprocessor):
    """Demo 3: Tone Variations (Professional / Friendly / Formal / Casual)."""
    print_section("DEMO 3: Tone Variations")

    incoming_email = {
        'from': 'colleague@company.com',
        'from_name': 'Sam Colleague',
        'subject': 'Quick Question',
        'body': '''Hi Alice,

Do you have time for a quick chat about the API changes? I'm a bit confused about the new endpoints.

Thanks!
Sam''',
        'date': '2025-10-13T14:00:00Z',
        'message_id': 'question_001'
    }

    email = preprocessor.preprocess_email(incoming_email)
    generator = ResponseGenerator(ollama, db_path='data/demo.db')

    print("Original Email:")
    print(f"  From: {incoming_email['from_name']}")
    print(f"  Subject: {incoming_email['subject']}")

    # Generate responses in all four tones
    for tone in ['Professional', 'Friendly', 'Formal', 'Casual']:
        print_subsection(f"{tone} Tone")

        result = generator.generate_response(email, length='Brief', tone=tone)

        print(f"Response:\n{result['response_text']}\n")


def demo_4_scenario_templates(ollama, preprocessor):
    """Demo 4: Scenario Templates."""
    print_section("DEMO 4: Scenario Templates")

    generator = ResponseGenerator(ollama, db_path='data/demo.db')

    # Template 1: Meeting Acceptance
    print_subsection("Template: Meeting Acceptance")

    meeting_email = preprocessor.preprocess_email({
        'from': 'manager@company.com',
        'subject': 'Budget Review Meeting',
        'body': 'Hi Alice, Can you join us for the budget review meeting on Friday at 3pm?',
        'date': '2025-10-13T12:00:00Z',
        'message_id': 'template_001'
    })

    result = generator.generate_response(
        meeting_email,
        length='Brief',
        tone='Professional',
        template='Meeting Acceptance'
    )

    print(f"Response:\n{result['response_text']}\n")

    # Template 2: Status Update
    print_subsection("Template: Status Update")

    status_email = preprocessor.preprocess_email({
        'from': 'manager@company.com',
        'subject': 'Project Status Check',
        'body': 'Hi Alice, Could you provide a quick status update on the email assistant project?',
        'date': '2025-10-13T13:00:00Z',
        'message_id': 'template_002'
    })

    result = generator.generate_response(
        status_email,
        length='Standard',
        tone='Professional',
        template='Status Update'
    )

    print(f"Response:\n{result['response_text']}\n")

    # Template 3: Thank You
    print_subsection("Template: Thank You")

    thank_you_email = preprocessor.preprocess_email({
        'from': 'colleague@company.com',
        'subject': 'Great presentation!',
        'body': 'Alice, your presentation yesterday was excellent. Thanks for putting that together!',
        'date': '2025-10-13T09:00:00Z',
        'message_id': 'template_003'
    })

    result = generator.generate_response(
        thank_you_email,
        length='Brief',
        tone='Friendly',
        template='Thank You'
    )

    print(f"Response:\n{result['response_text']}\n")


def demo_5_thread_context(ollama, preprocessor):
    """Demo 5: Thread Context Incorporation."""
    print_section("DEMO 5: Thread Context Incorporation")

    # Create a thread of emails
    thread = [
        preprocessor.preprocess_email({
            'from': 'alice@company.com',
            'subject': 'Budget Planning',
            'body': 'Hi team, we need to finalize the Q4 budget by next week.',
            'date': '2025-10-10T10:00:00Z',
            'message_id': 'thread_001'
        }),
        preprocessor.preprocess_email({
            'from': 'bob@company.com',
            'subject': 'Re: Budget Planning',
            'body': 'Alice, can we schedule a meeting to review the numbers?',
            'date': '2025-10-11T14:00:00Z',
            'message_id': 'thread_002'
        }),
        preprocessor.preprocess_email({
            'from': 'alice@company.com',
            'subject': 'Re: Budget Planning',
            'body': 'Sure Bob, how about Tuesday at 2pm?',
            'date': '2025-10-11T15:00:00Z',
            'message_id': 'thread_003'
        })
    ]

    current_email = preprocessor.preprocess_email({
        'from': 'charlie@company.com',
        'subject': 'Re: Budget Planning',
        'body': 'I have some concerns about the marketing allocation. Can we discuss this in the meeting?',
        'date': '2025-10-12T11:00:00Z',
        'message_id': 'thread_004'
    })

    print("Email Thread:")
    for i, msg in enumerate(thread):
        print(f"  {i+1}. From: {msg['metadata']['from']} - {msg['content']['body'][:50]}...")

    print(f"\n  4. Current Email: {current_email['metadata']['from']} - {current_email['content']['body'][:60]}...\n")

    generator = ResponseGenerator(ollama, db_path='data/demo.db')

    print("Generating response with thread context...\n")

    result = generator.generate_response(
        current_email,
        length='Standard',
        tone='Professional',
        thread_context=thread
    )

    print(f"Response:\n{result['response_text']}\n")
    print(f"✓ Response incorporates context from {len(thread)} previous messages")


def demo_6_response_metrics(ollama, preprocessor):
    """Demo 6: Response Metrics Tracking."""
    print_section("DEMO 6: Response Metrics Tracking")

    generator = ResponseGenerator(ollama, db_path='data/demo.db')

    print("Generating sample responses to populate metrics...\n")

    # Generate a few responses
    sample_email = preprocessor.preprocess_email({
        'from': 'test@company.com',
        'subject': 'Test',
        'body': 'This is a test email for metrics demonstration.',
        'date': '2025-10-13T16:00:00Z',
        'message_id': 'metrics_test'
    })

    for length in ['Brief', 'Standard']:
        for tone in ['Professional', 'Friendly']:
            generator.generate_response(sample_email, length=length, tone=tone)

    # Get metrics
    metrics = generator.get_response_metrics(days=1)

    print("Response Generation Metrics (Last 24 hours):\n")
    print(f"Total Responses Generated: {metrics['total_generated']}")

    if 'by_length' in metrics:
        print(f"\nBreakdown by Length:")
        for length, stats in metrics['by_length'].items():
            print(f"  {length}: {stats['count']} responses, avg {stats['avg_time_ms']:.0f}ms")

    if metrics.get('acceptance_rate_percent'):
        print(f"\nAcceptance Rate: {metrics['acceptance_rate_percent']:.1f}%")

    if metrics.get('avg_edit_percentage'):
        print(f"Average Edit Percentage: {metrics['avg_edit_percentage']:.1f}%")


def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("MAILMIND RESPONSE GENERATOR DEMO")
    print("Story 1.5: Response Generation Assistant")
    print("=" * 70)

    try:
        # Initialize Ollama
        print("\nInitializing Ollama...")
        config = load_config()
        ollama_config = get_ollama_config(config)
        ollama = OllamaManager(ollama_config)
        ollama.initialize()
        print(f"✓ Ollama ready: {ollama.current_model}\n")

        # Initialize preprocessor
        preprocessor = EmailPreprocessor()

        # Run demos
        demo_1_writing_style_analysis()

        input("\nPress Enter to continue to Demo 2 (Response Lengths)...")
        demo_2_response_lengths(ollama, preprocessor)

        input("\nPress Enter to continue to Demo 3 (Tone Variations)...")
        demo_3_tone_variations(ollama, preprocessor)

        input("\nPress Enter to continue to Demo 4 (Scenario Templates)...")
        demo_4_scenario_templates(ollama, preprocessor)

        input("\nPress Enter to continue to Demo 5 (Thread Context)...")
        demo_5_thread_context(ollama, preprocessor)

        input("\nPress Enter to continue to Demo 6 (Response Metrics)...")
        demo_6_response_metrics(ollama, preprocessor)

        print_section("DEMO COMPLETE")
        print("✓ All demos completed successfully!")
        print("\nKey Features Demonstrated:")
        print("  1. Writing style analysis from sent emails")
        print("  2. Three response lengths (Brief/Standard/Detailed)")
        print("  3. Four tone options (Professional/Friendly/Formal/Casual)")
        print("  4. Eight scenario templates")
        print("  5. Thread context incorporation")
        print("  6. Response metrics tracking")
        print("\nNext Steps:")
        print("  - Review generated responses in data/demo.db")
        print("  - Try integration with real email data")
        print("  - Explore additional customization options")

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Ensure Ollama is running: ollama serve")
        print("  2. Ensure model is available: ollama pull llama3.1:8b-instruct-q4_K_M")
        print("  3. Check logs for detailed error messages")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
