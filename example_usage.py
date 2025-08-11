#!/usr/bin/env python3
"""
Example usage of PrimeMinister programmatically.
"""

import asyncio
import os
from primeminister import PrimeMinister


async def example_usage():
    """Example of using PrimeMinister programmatically."""

    # Note: You need to set your OpenAI API key first
    # Either in the config file or as an environment variable

    try:
        # Initialize PrimeMinister
        pm = PrimeMinister()

        # Show council summary
        print("Council Summary:")
        summary = pm.get_council_summary()
        for member in summary['members']:
            print(f"  - {member['personality'].split(' - ')[0]}")
        print()

        # Example question
        question = "Should I learn Python or JavaScript first as a beginner programmer?"

        print(f"Question: {question}")
        print("Consulting the council...\n")

        # Process the request
        decision, session_data = await pm.process_request(question)

        # Display results
        print("="*60)
        print("PRIME MINISTER'S DECISION")
        print("="*60)
        print(decision)
        print()

        # Show voting results
        if session_data.get('votes'):
            print("Voting Results:")
            for personality, voters in session_data['votes'].items():
                name = personality.split(' - ')[0] if ' - ' in personality else personality[:30]
                print(f"  {name}: {len(voters)} vote(s)")

    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure to:")
        print("1. Set your OpenAI API key in the config file")
        print("2. Run 'primeminister --config' to see config location")
        print("3. Install required dependencies: pip install -e src/")


if __name__ == "__main__":
    asyncio.run(example_usage())