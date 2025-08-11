#!/usr/bin/env python3
"""
Example demonstrating PrimeMinister JSON API usage.
This shows how to use PrimeMinister programmatically with structured JSON responses.
"""

import asyncio
import json
from primeminister import PrimeMinister


async def basic_json_example():
    """Basic example of using the JSON API."""
    print("🏛️ PrimeMinister JSON API Example\n")

    # Initialize PrimeMinister
    pm = PrimeMinister()

    # Ask a question and get structured JSON response
    question = "What's the most important skill for a software developer?"
    print(f"❓ Question: {question}\n")

    try:
        # Get the JSON response (same structure as logs)
        response_data = await pm.process_request_json(question)

        # Display key information
        print("📊 Response Summary:")
        print(f"   Mode: {response_data['mode']}")
        print(f"   Council Members: {response_data['metadata']['responding_members']}")
        print(f"   Votes Cast: {response_data['metadata']['total_votes_cast']}")
        print(f"   Tie Broken: {response_data['metadata']['tie_broken_by_pm']}")

        print(f"\n🏛️ Prime Minister's Decision:")
        print(f"   {response_data['final_result'][:200]}...")

        print(f"\n💭 Council Responses ({len(response_data['council_responses'])}):")
        for response in response_data['council_responses']:
            if not response['has_error']:
                member_name = response['council_member']
                response_text = response['response'][:100] + "..."
                print(f"   • {member_name}: {response_text}")

        print(f"\n🗳️ Voting Results:")
        for voter, chosen_responses in response_data['votes'].items():
            print(f"   • {voter}: {len(chosen_responses)} vote(s)")

        # Show that the response can be serialized to JSON
        print(f"\n📝 JSON Structure (first 500 chars):")
        json_str = json.dumps(response_data, indent=2, ensure_ascii=False)
        print(f"   {json_str[:500]}...")
        print(f"   Total JSON size: {len(json_str)} characters")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure you have set up your OpenAI API key in the configuration.")


async def advisor_mode_example():
    """Example using advisor mode with JSON output."""
    print("\n" + "="*70)
    print("🎯 Advisor Mode JSON Example\n")

    # Initialize PrimeMinister in advisor mode
    pm = PrimeMinister(mode_override='advisor')

    question = "How should I structure a large Python project?"
    print(f"❓ Question: {question}\n")

    try:
        response_data = await pm.process_request_json(question)

        print("📊 Advisor Response Summary:")
        print(f"   Mode: {response_data['mode']}")
        print(f"   Advisory Council: {response_data['metadata']['responding_members']} members")
        print(f"   Voting Members: {response_data['metadata']['voting_members']} (advisor mode)")

        print(f"\n🏛️ Prime Minister's Synthesis:")
        print(f"   {response_data['final_result'][:300]}...")

        print(f"\n💡 Advisor Insights:")
        for response in response_data['council_responses']:
            if not response['has_error']:
                member_name = response['council_member']
                response_text = response['response'][:80] + "..."
                print(f"   • {member_name}: {response_text}")

    except Exception as e:
        print(f"❌ Error: {e}")


def web_api_example():
    """Example of how this could be used in a web API."""
    print("\n" + "="*70)
    print("🌐 Web API Integration Example\n")

    example_code = '''
from flask import Flask, jsonify, request
from primeminister import PrimeMinister
import asyncio

app = Flask(__name__)

@app.route('/ask', methods=['POST'])
def ask_question():
    """Endpoint for asking questions to the PrimeMinister council."""
    data = request.get_json()
    question = data.get('question')
    mode = data.get('mode', 'council')  # 'council' or 'advisor'

    async def get_response():
        pm = PrimeMinister(mode_override=mode)
        return await pm.process_request_json(question)

    # Run the async function
    response_data = asyncio.run(get_response())

    # Return the complete JSON response
    return jsonify(response_data)

@app.route('/ask-simple', methods=['POST'])
def ask_simple():
    """Simplified endpoint returning just the decision."""
    data = request.get_json()
    question = data.get('question')

    async def get_decision():
        pm = PrimeMinister()
        response_data = await pm.process_request_json(question)
        return {
            'question': question,
            'decision': response_data['final_result'],
            'mode': response_data['mode'],
            'session_id': response_data['session_uuid']
        }

    result = asyncio.run(get_decision())
    return jsonify(result)
'''

    print("Flask Web API Example:")
    print(example_code)


async def main():
    """Run all examples."""
    await basic_json_example()
    await advisor_mode_example()
    web_api_example()

    print("\n" + "="*70)
    print("✅ Examples completed!")
    print("\nTo try these features:")
    print("   CLI JSON: primeminister --json 'Your question here'")
    print("   Advisor:  primeminister --mode advisor --json 'Your question'")
    print("   Python:   Use PrimeMinister().process_request_json() as shown above")


if __name__ == '__main__':
    asyncio.run(main())