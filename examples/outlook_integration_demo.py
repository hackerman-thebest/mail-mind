"""
Outlook Integration Demo

This script demonstrates the complete Outlook integration functionality
including connection, email fetching, actions, and multi-account support.

Usage:
    python examples/outlook_integration_demo.py

Requirements:
    - Windows OS with Microsoft Outlook installed and running
    - At least one email account configured in Outlook
    - pywin32 package installed
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mailmind.integrations import (
    OutlookConnector,
    OutlookNotInstalledException,
    OutlookNotRunningException,
    OutlookConnectionError
)


def demo_1_connection():
    """Demo 1: Connection and Detection"""
    print("\n" + "="*70)
    print("DEMO 1: Connection and Detection")
    print("="*70)

    # Check if Outlook is installed
    if OutlookConnector.detect_outlook_installed():
        print("✓ Outlook is installed")
    else:
        print("✗ Outlook is NOT installed")
        return

    # Check if Outlook is running
    if OutlookConnector.is_outlook_running():
        print("✓ Outlook is running")
    else:
        print("✗ Outlook is NOT running - please start Outlook")
        return

    # Connect to Outlook
    connector = OutlookConnector()
    try:
        if connector.connect():
            print(f"✓ Connected to Outlook")
            print(f"  Status: {connector.connection_state}")
            connector.disconnect()
    except Exception as e:
        print(f"✗ Connection failed: {e}")


def demo_2_multi_account():
    """Demo 2: Multi-Account Support"""
    print("\n" + "="*70)
    print("DEMO 2: Multi-Account Support")
    print("="*70)

    with OutlookConnector() as connector:
        accounts = connector.get_accounts()
        print(f"\nFound {len(accounts)} email account(s):")
        for i, account in enumerate(accounts, 1):
            print(f"  {i}. {account.display_name} <{account.email_address}>")
            print(f"     Type: {account.account_type}")


def demo_3_fetch_emails():
    """Demo 3: Fetch Emails with Pagination"""
    print("\n" + "="*70)
    print("DEMO 3: Fetch Emails with Pagination")
    print("="*70)

    with OutlookConnector() as connector:
        # Fetch first 10 emails from Inbox
        print("\nFetching first 10 emails from Inbox...")
        emails = connector.fetch_emails("Inbox", limit=10, offset=0)

        print(f"\nRetrieved {len(emails)} emails:")
        for i, email in enumerate(emails, 1):
            status = "📩" if email.is_unread else "📧"
            print(f"\n{i}. {status} {email.subject}")
            print(f"   From: {email.sender_name} <{email.sender_email}>")
            print(f"   Date: {email.received_time.strftime('%Y-%m-%d %H:%M')}")
            print(f"   Importance: {email.importance.name}")
            if email.has_attachments:
                print(f"   Attachments: {len(email.attachments)}")
                for att in email.attachments:
                    print(f"     - {att.filename} ({att.size} bytes)")


def demo_4_email_properties():
    """Demo 4: Email Property Extraction"""
    print("\n" + "="*70)
    print("DEMO 4: Email Property Extraction")
    print("="*70)

    with OutlookConnector() as connector:
        emails = connector.fetch_emails("Inbox", limit=1)

        if emails:
            email = emails[0]
            print(f"\nDetailed properties for: {email.subject}\n")
            print(f"Entry ID: {email.entry_id[:40]}...")
            print(f"Subject: {email.subject}")
            print(f"From: {email.sender_name} <{email.sender_email}>")
            print(f"To: {', '.join(email.to_recipients) if email.to_recipients else '(none)'}")
            print(f"Received: {email.received_time}")
            print(f"Message Class: {email.message_class}")
            print(f"Importance: {email.importance.name}")
            print(f"Flag Status: {email.flag_status.name}")
            print(f"Unread: {email.is_unread}")
            print(f"Has Attachments: {email.has_attachments}")

            if email.conversation_id:
                print(f"Conversation ID: {email.conversation_id}")
            if email.conversation_topic:
                print(f"Conversation Topic: {email.conversation_topic}")

            # Show body preview
            body_preview = email.body[:200].replace('\n', ' ').replace('\r', '')
            if len(email.body) > 200:
                body_preview += "..."
            print(f"\nBody Preview: {body_preview}")

            # Convert to dict for EmailPreprocessor
            email_dict = email.to_dict()
            print(f"\nEmail can be converted to dict with {len(email_dict)} keys for preprocessing")


def demo_5_email_actions():
    """Demo 5: Email Actions (Read-Only Demo)"""
    print("\n" + "="*70)
    print("DEMO 5: Email Actions (Read-Only Demo)")
    print("="*70)

    with OutlookConnector() as connector:
        emails = connector.fetch_emails("Inbox", limit=5)

        if emails:
            print(f"\nFound {len(emails)} emails in Inbox")
            print("\nAvailable actions:")
            print("  - Mark as read/unread")
            print("  - Move to folder")
            print("  - Create reply draft")
            print("  - Delete email")

            # Example code (not executed to avoid modifying actual emails)
            print("\nExample code:")
            print("  connector.mark_as_read(email.entry_id, is_read=True)")
            print("  connector.move_email(email.entry_id, 'Archive')")
            print("  draft_id = connector.create_reply_draft(email.entry_id)")
            print("  connector.delete_email(email.entry_id)")

            print("\n⚠️  Note: Actions not executed in demo to preserve your emails")


def demo_6_folder_navigation():
    """Demo 6: Folder Navigation"""
    print("\n" + "="*70)
    print("DEMO 6: Folder Navigation")
    print("="*70)

    with OutlookConnector() as connector:
        # Test standard folders
        standard_folders = ["Inbox", "Sent Items", "Drafts", "Deleted Items"]

        print("\nAccessing standard folders:")
        for folder_name in standard_folders:
            try:
                folder = connector.get_folder(folder_name)
                emails = connector.fetch_emails(folder_name, limit=1)
                print(f"  ✓ {folder_name}: Accessible (sample: {len(emails)} email(s) fetched)")
            except Exception as e:
                print(f"  ✗ {folder_name}: {e}")


def demo_7_performance():
    """Demo 7: Performance Metrics"""
    print("\n" + "="*70)
    print("DEMO 7: Performance Metrics")
    print("="*70)

    import time

    with OutlookConnector() as connector:
        # Test pagination performance
        limits = [10, 25, 50]

        print("\nPagination performance tests:")
        for limit in limits:
            start = time.time()
            emails = connector.fetch_emails("Inbox", limit=limit)
            elapsed = time.time() - start

            print(f"  Fetch {limit:2d} emails: {elapsed:.3f}s ({len(emails)} retrieved)")

            # Performance target: <500ms for 50 emails
            if limit == 50:
                if elapsed < 0.5:
                    print(f"    ✓ Meets performance target (<500ms)")
                else:
                    print(f"    ⚠ Exceeds target (target: <500ms, actual: {elapsed*1000:.0f}ms)")


def main():
    """Run all demos"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "Outlook Integration Demo" + " "*29 + "║")
    print("╚" + "="*68 + "╝")

    try:
        # Check prerequisites
        if not OutlookConnector.detect_outlook_installed():
            print("\n✗ ERROR: Microsoft Outlook is not installed")
            print("  This demo requires Outlook to be installed on Windows")
            return

        if not OutlookConnector.is_outlook_running():
            print("\n✗ ERROR: Outlook is not running")
            print("  Please start Microsoft Outlook and run this demo again")
            return

        # Run demos
        demo_1_connection()
        demo_2_multi_account()
        demo_3_fetch_emails()
        demo_4_email_properties()
        demo_5_email_actions()
        demo_6_folder_navigation()
        demo_7_performance()

        print("\n" + "="*70)
        print("✓ All demos completed successfully!")
        print("="*70 + "\n")

    except OutlookNotInstalledException as e:
        print(f"\n✗ ERROR: {e}")
    except OutlookNotRunningException as e:
        print(f"\n✗ ERROR: {e}")
    except OutlookConnectionError as e:
        print(f"\n✗ ERROR: {e}")
    except KeyboardInterrupt:
        print("\n\n✗ Demo interrupted by user")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
