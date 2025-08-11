#!/usr/bin/env python3
"""
PrimeMinister CLI - An AI council decision-making tool.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from .core import PrimeMinister
from .config_manager import ConfigManager


def print_banner():
    """Print the PrimeMinister banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                        PRIME MINISTER                        ║
║                   AI Council Decision System                 ║
╚═══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_council_summary(pm: PrimeMinister):
    """Print a summary of the current council."""
    summary = pm.get_council_summary()

    print(f"\n📋 Council Summary:")
    print(f"   Total Members: {summary['total_members']}")
    print(f"   Voting Members: {summary['voters']}")
    print(f"   Silent Members: {summary['silent_members']}")

    print(f"\n👥 Council Members:")
    for i, member in enumerate(summary['members'], 1):
        status_icons = []
        if member['voter']:
            status_icons.append("🗳️")
        if member['silent']:
            status_icons.append("🤫")

        status = " ".join(status_icons) if status_icons else "💬"
        print(f"   {i}. {member['personality']} {status}")
        print(f"      Model: {member['model']}")


def format_response(decision: str, session_data: dict = None):
    """Format the final response for display."""
    # Check if this is an error response
    is_error = session_data and session_data.get('error', False)

    if is_error:
        print("\n" + "="*80)
        print("❌ ERROR")
        print("="*80)
        print(f"\n{decision}\n")
        return

    # Normal successful response
    mode = session_data.get('metadata', {}).get('mode', 'council') if session_data else 'council'

    print("\n" + "="*80)
    if mode == 'advisor':
        print("🏛️  PRIME MINISTER'S SYNTHESIS")
    else:
        print("🏛️  PRIME MINISTER'S DECISION")
    print("="*80)
    print(f"\n{decision}\n")

    # Only show voting results in council mode
    if mode == 'council' and session_data and session_data.get('votes'):
        print("📊 Voting Results:")
        votes = session_data['votes']
        for personality, voters in votes.items():
            personality_name = personality.split(' - ')[0] if ' - ' in personality else personality[:30]
            voter_names = []
            tie_breaker_vote = False

            for voter in voters:
                if "Prime Minister (tie-breaker" in voter:
                    tie_breaker_vote = True
                    voter_names.append("🏛️ PM (tie-breaker)")
                else:
                    voter_names.append(voter)

            vote_display = f"{len(voters)} vote(s)"
            if tie_breaker_vote:
                vote_display += " ⚖️"

            print(f"   • {personality_name}: {vote_display}")

        # Show tie-breaking message if applicable
        if session_data.get('metadata', {}).get('tie_broken_by_pm', False):
            print("   ⚖️ Tie was broken by Prime Minister's deciding vote")

        print()
    elif mode == 'advisor':
        print("ℹ️  Direct synthesis from advisory council (no voting)")
        print()


async def interactive_mode(mode_override=None, json_output=False):
    """Run PrimeMinister in interactive mode."""
    print_banner()

    try:
        pm = PrimeMinister(mode_override=mode_override)
        print_council_summary(pm)

        print("\n💡 Interactive Mode - Type your questions or problems below.")
        print("   Type 'quit', 'exit', or Ctrl+C to exit.\n")

        while True:
            try:
                # Get user input
                user_input = input("🤔 Your question: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!")
                    break

                print("\n⏳ Consulting the council...")

                # Process the request
                if json_output:
                    response_data = await pm.process_request_json(user_input)
                    print(json.dumps(response_data, indent=2, ensure_ascii=False))
                else:
                    decision, session_data = await pm.process_request(user_input)
                    # Display the result
                    format_response(decision, session_data)

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                print("Please try again or check your configuration.\n")

    except Exception as e:
        print(f"❌ Failed to initialize PrimeMinister: {str(e)}")
        print("Please check your configuration and try again.")
        sys.exit(1)


async def single_question_mode(question: str, mode_override=None, json_output=False):
    """Process a single question and exit."""
    try:
        pm = PrimeMinister(mode_override=mode_override)

        if json_output:
            response_data = await pm.process_request_json(question)
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
        else:
            print("⏳ Consulting the council...")
            decision, session_data = await pm.process_request(question)
            format_response(decision, session_data)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


def show_config():
    """Show current configuration."""
    try:
        config_manager = ConfigManager()
        config_path = config_manager.get_config_path()
        config = config_manager.load_config()

        print_banner()
        print(f"📁 Configuration file: {config_path}")
        print(f"🔑 API Key configured: {'Yes' if config.get('openai_key') and config['openai_key'] != 'your-openai-api-key-here' else 'No'}")
        print(f"🌐 API URL: {config.get('api_url', 'Not set')}")
        print(f"🤖 Model: {config.get('model', 'Not set')}")
        print(f"🌡️  Temperature: {config.get('temperature', 'Not set')}")

        council = config.get('council', [])
        print(f"\n👥 Council Members: {len(council)}")

        for i, member in enumerate(council, 1):
            personality = member.get('personality', 'Unknown')
            name = personality.split(' - ')[0] if ' - ' in personality else personality[:30]
            print(f"   {i}. {name}")
            print(f"      Model: {member.get('model', 'Not set')}")
            print(f"      Voter: {'Yes' if member.get('voter', True) else 'No'}")
            print(f"      Silent: {'Yes' if member.get('silent', False) else 'No'}")

        user_config = config.get('user', {})
        attributes = user_config.get('attributes', [])
        goal = user_config.get('goal', 'Not set')

        print(f"\n👤 User Profile:")
        print(f"   Attributes: {', '.join(attributes) if attributes else 'None set'}")
        print(f"   Goal: {goal}")

    except Exception as e:
        print(f"❌ Error reading configuration: {str(e)}")
        sys.exit(1)


def show_history(limit: int = 10):
    """Show recent session history."""
    try:
        from .logger import PrimeMinisterLogger

        logger = PrimeMinisterLogger()
        history = logger.get_session_history(limit)

        print_banner()
        print(f"📜 Recent Sessions (last {min(limit, len(history))} of {len(history)}):\n")

        if not history:
            print("No sessions found.")
            return

        for i, session in enumerate(reversed(history[-limit:]), 1):
            timestamp = session.get('timestamp', 'Unknown time')
            prompt = session.get('prompt', 'Unknown prompt')

            print(f"{i}. {timestamp}")
            print(f"   Question: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")

            votes = session.get('votes', {})
            if votes:
                winner = max(votes.items(), key=lambda x: len(x[1]))
                print(f"   Winner: {winner[0].split(' - ')[0] if ' - ' in winner[0] else winner[0][:30]} ({len(winner[1])} votes)")

            print()

    except Exception as e:
        print(f"❌ Error reading history: {str(e)}")
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="PrimeMinister - AI Council Decision System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  primeminister                          # Interactive mode (default: council)
  primeminister "How should I learn Python?"  # Single question
  primeminister --mode advisor "Question?"    # Use advisor mode (no voting)
  primeminister --json "Question?"       # Output response in JSON format
  primeminister --mode advisor --json "Q?"    # Advisor mode with JSON output
  primeminister --config                 # Show configuration
  primeminister --history                # Show recent sessions
        """
    )

    parser.add_argument(
        'question',
        nargs='?',
        help='Question or problem to ask the council (if not provided, enters interactive mode)'
    )

    parser.add_argument(
        '--config',
        action='store_true',
        help='Show current configuration and exit'
    )

    parser.add_argument(
        '--history',
        type=int,
        nargs='?',
        const=10,
        metavar='N',
        help='Show last N sessions (default: 10)'
    )

    parser.add_argument(
        '--mode',
        choices=['council', 'advisor'],
        help='Override decision-making mode: council (voting) or advisor (direct synthesis)'
    )

    parser.add_argument(
        '--json',
        action='store_true',
        help='Output response in JSON format (same structure as logs)'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='PrimeMinister 1.0.0'
    )

    args = parser.parse_args()

    # Handle special modes
    if args.config:
        show_config()
        return

    if args.history is not None:
        show_history(args.history)
        return

    # Handle question modes
    if args.question:
        # Single question mode
        asyncio.run(single_question_mode(args.question, mode_override=args.mode, json_output=args.json))
    else:
        # Interactive mode
        asyncio.run(interactive_mode(mode_override=args.mode, json_output=args.json))


if __name__ == '__main__':
    main()