# PrimeMinister 🏛️

An AI CLI tool that uses a council of AI personalities with different perspectives to provide well-rounded advice and decision-making support.

This is intended to act as your own personal think tank where you can emulate personas of your choice, real or not, to act as a governing council
and provide meaningful and effective advice.

## Overview

PrimeMinister creates a "council" of AI advisors, each with distinct personalities and expertise areas. When you ask a question or present a problem:

**Council Mode (default):**
1. **Council Consultation** - Each council member provides their unique perspective
2. **Blind Voting** - Each council member evaluates ALL responses anonymously and votes for the best one
3. **Tie-Breaking** - If there's a voting tie, the Prime Minister casts the deciding vote
4. **Prime Minister Decision** - The Prime Minister evaluates all responses and votes to provide the final answer

**Advisor Mode:**
1. **Initial Responses** - Each advisor provides their perspective on your question
2. **Peer Review** - Each advisor reviews and provides constructive opinions on colleagues' responses
3. **Refinement** - Original advisors respond to peer feedback, refining their positions
4. **Prime Minister Synthesis** - The Prime Minister analyzes all rounds to create the final recommendation

## Features

- 🤖 **Multiple AI Perspectives** - Get advice from different AI "personalities"
- 🗳️ **Blind Voting** - Council members analyze responses anonymously to prevent bias (Council Mode)
- 💬 **Two-Round Opinions** - Peer review and refinement process (Advisor Mode)
- ⚖️ **Intelligent Tie-Breaking** - Prime Minister resolves voting ties with reasoned decisions
- 🎯 **Dual Operating Modes** - Council voting or multi-round advisor synthesis
- 📊 **Transparent Process** - See all responses, votes, opinions, and reasoning
- 🔍 **UUID Tracking** - Complete audit trail with unique identifiers for all interactions
- 📝 **Session Logging** - JSON-formatted logs with monthly rotation
- 🔌 **JSON API** - Programmatic access with structured responses
- ⚙️ **Flexible Configuration** - Customizable council members and personalities
- 🐧 **Cross-Platform** - Works on Linux, macOS, and Windows
- 📋 **Interactive & Batch Modes** - Use interactively or with single commands

## Installation

```bash
# Clone the repository
git clone https://github.com/eb3095/primeminister.git
cd primeminister

# Install the package
pip install -e src/

# Or install from PyPI (when published)
pip install primeminister
```

## Quick Start

1. **Set your OpenAI API key:**
   ```bash
   primeminister --config
   ```

2. **Ask a question:**
   ```bash
   primeminister "How should I approach learning a new programming language?"
   ```

3. **Try advisor mode:**
   ```bash
   primeminister --mode advisor "What's the best way to debug complex issues?"
   ```

## Usage

### Command Line Options

```bash
# Interactive mode (default: council)
primeminister

# Single question
primeminister "How should I learn Python?"

# Use advisor mode (two-round opinion system)
primeminister --mode advisor "Question?"

# Output response in JSON format
primeminister --json "Question?"

# Combine modes and JSON output
primeminister --mode advisor --json "Question?"

# Show configuration
primeminister --config

# Show recent sessions
primeminister --history
primeminister --history 20  # Show last 20 sessions
```

### JSON Output

Use the `--json` flag to get structured JSON responses suitable for programmatic use:

```bash
primeminister --json "Should I use React or Vue?"
```

**JSON Response Structure:**
```json
{
  "prompt": "Should I use React or Vue?",
  "final_result": "After careful consideration...",
  "session_uuid": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "question_uuid": "b2c3d4e5-f6a7-8901-2345-67890abcdef1",
  "result_uuid": "d4e5f6a7-b8c9-0123-4567-890abcdef123",
  "mode": "council",
  "council_responses": [
    {
      "uuid": "c3d4e5f6-a7b8-9012-3456-7890abcdef12",
      "council_member": "The Pragmatist",
      "response": "Consider the practical aspects...",
      "has_error": false
    }
  ],
  "votes": {
    "The Pragmatist": ["c3d4e5f6-a7b8-9012-3456-7890abcdef12"]
  },
  "detailed_votes": [
    {
      "vote_uuid": "e5f6a7b8-c9d0-1234-5678-90abcdef1234",
      "voter_name": "The Judge",
      "chosen_response_uuid": "c3d4e5f6-a7b8-9012-3456-7890abcdef12",
      "reasoning": "This response provides the most practical approach..."
    }
  ],
  "metadata": {
    "total_council_members": 10,
    "responding_members": 5,
    "voting_members": 5,
    "total_votes_cast": 5,
    "tie_broken_by_pm": false,
    "response_uuids": ["c3d4e5f6-a7b8-9012-3456-7890abcdef12"],
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

## Programmatic Usage

### Python API

```python
import asyncio
from primeminister import PrimeMinister

async def main():
    pm = PrimeMinister()

    # Get structured response for programmatic use
    response_data = await pm.process_request_json("How should I optimize my code?")

    # Access the final decision
    print("Decision:", response_data['final_result'])

    # Access individual council responses
    for response in response_data['council_responses']:
        print(f"{response['council_member']}: {response['response'][:100]}...")

    # Access voting results
    for vote in response_data['detailed_votes']:
        print(f"Vote from {vote['voter_name']}: {vote['reasoning'][:50]}...")

# Run the async function
asyncio.run(main())
```

### Web Integration

The JSON response format matches the log structure exactly, making it perfect for web APIs:

```python
from flask import Flask, jsonify, request
from primeminister import PrimeMinister
import asyncio

app = Flask(__name__)

@app.route('/ask', methods=['POST'])
async def ask_question():
    data = request.get_json()
    question = data.get('question')
    mode = data.get('mode', 'council')  # 'council' or 'advisor'

    pm = PrimeMinister(mode_override=mode)
    response_data = await pm.process_request_json(question)

    return jsonify(response_data)
```

## Configuration

### Configuration Locations

- **Linux**: `/etc/primeminister/config.json` (with fallback to module path)
- **Other OS**: `<module_path>/primeminister/config.json`

### Council Configuration

The system uses a **bicameral structure**:
- **Advisory Council** - Provides responses (`voter: false`, `silent: false`)
- **Silent Voting Jury** - Evaluates responses (`voter: true`, `silent: true`)

Example council member:
```json
{
  "model": "gpt-4",
  "personality": "The Pragmatist - You focus on practical, real-world solutions and implementation details.",
  "voter": false,
  "silent": false
}
```

### Operation Modes

Set the default mode in config.json:
```json
{
  "mode": "council",  // or "advisor"
  "primeminister_prompt": "You are the Prime Minister...",
  "primeminister_advisor_prompt": "You are the Prime Minister in advisor mode..."
}
```

## Default Council Structure

### Advisory Council (Responders)
1. **The Pragmatist** - Focuses on practical, implementable solutions
2. **The Visionary** - Thinks long-term and considers innovative possibilities
3. **The Skeptic** - Identifies risks and challenges assumptions
4. **The Diplomat** - Considers human factors and stakeholder needs
5. **The Analyst** - Provides data-driven, systematic analysis

### Silent Voting Jury (Evaluators)
1. **The Judge** - Evaluates overall quality and completeness
2. **The Pragmatic Evaluator** - Assesses practical feasibility
3. **The Clarity Assessor** - Judges communication effectiveness
4. **The Completeness Reviewer** - Ensures comprehensive coverage
5. **The Relevance Checker** - Validates alignment with the question

## Logging and Audit Trail

Sessions are automatically logged in JSON format:

- **Linux**: `/var/log/primeminister/YYYY-MM.json`
- **Other OS**: `./logs/YYYY-MM.json`

Each log entry includes:
- Original prompt with question UUID
- All council responses with individual UUIDs
- Voting results with response tracking
- Final Prime Minister decision with result UUID
- Complete session metadata with audit trail

### Blind Voting System

To ensure unbiased evaluation, council members vote on responses without knowing which member wrote each response:

**What Council Members See When Voting:**
```
Here are the responses to evaluate:

Option 1:
Consider the practical implementation steps and resource requirements...

Option 2:
Think about the long-term implications and future opportunities...

Option 3:
Be aware of potential risks and unintended consequences...
```

**What's Tracked Internally (UUIDs in logs only):**
- Session UUID: `a1b2c3d4-e5f6-7890-1234-567890abcdef`
- Question UUID: `b2c3d4e5-f6a7-8901-2345-67890abcdef1`
- Response UUIDs: `c3d4e5f6-a7b8-9012-3456-7890abcdef12` (for each response)
- Vote UUIDs: `e5f6a7b8-c9d0-1234-5678-90abcdef1234` (for each vote)
- Result UUID: `d4e5f6a7-b8c9-0123-4567-890abcdef123`

This prevents council members from being influenced by who wrote each response, ensuring votes are based purely on content quality and relevance.

### Two-Round Opinion System (Advisor Mode)

In advisor mode, PrimeMinister uses a sophisticated three-round discussion process:

**Round 1 - Initial Responses:**
Each advisor provides their perspective on your question based on their unique personality and expertise.

**Round 2 - Peer Review:**
Each advisor reviews their colleagues' responses and provides constructive opinions, considering:
- Strengths and weaknesses of each approach
- Missing considerations or perspectives
- How responses could be improved or extended
- Areas of agreement or disagreement

**Round 3 - Refinement:**
Original advisors respond to the peer feedback they received, allowing them to:
- Acknowledge valid points and incorporate feedback
- Clarify or defend aspects of their original response
- Expand on areas that colleagues highlighted
- Adjust recommendations based on the discussion

**Final Synthesis:**
The Prime Minister analyzes all three rounds to create a comprehensive recommendation that incorporates:
- The diverse initial perspectives and their individual strengths
- The constructive peer feedback and critical analysis
- How advisors refined their thinking based on colleague input
- Areas of consensus and productive disagreement
- The evolution of ideas through the discussion process

**UUID Tracking:**
Every opinion and response in the system has a unique identifier for complete traceability:
- Opinion UUIDs: Track each peer review comment
- Response UUIDs: Track each advisor's refined response
- Full audit trail: Complete session metadata with opinion round statistics

## Example Sessions

### Council Mode (Voting)
```
🤔 Your question: Should I use React or Vue for my new project?

⏳ Consulting the council...

════════════════════════════════════════════════════════════════════════════════
🏛️  PRIME MINISTER'S DECISION
════════════════════════════════════════════════════════════════════════════════

After careful consideration of my council's advice, I recommend React for your new project.

The Pragmatist correctly points out React's superior job market and ecosystem maturity,
while The Analyst's performance comparison shows React's optimization capabilities.
Although Vue offers simplicity, React's long-term benefits outweigh the initial learning curve.

Key factors in this decision:
- Larger talent pool for hiring
- More extensive third-party library ecosystem
- Better long-term career prospects
- Strong corporate backing and community support

📊 Voting Results:
   • The Pragmatist: 2 vote(s)
   • The Visionary: 1 vote(s)
   • The Analyst: 2 vote(s) ⚖️
   ⚖️ Tie was broken by Prime Minister's deciding vote
```

### Advisor Mode (Two-Round Opinion System)
```
🤔 Your question: What's the best debugging strategy?

⏳ Consulting the council...
⏳ Conducting opinion rounds...

════════════════════════════════════════════════════════════════════════════════
🏛️  PRIME MINISTER'S SYNTHESIS
════════════════════════════════════════════════════════════════════════════════

After three rounds of collaborative discussion among my advisory council, here's a refined debugging strategy:

**Systematic Approach (The Analyst):**
- Start with reproducing the issue consistently
- Use logging and breakpoints strategically
- Isolate variables and test assumptions

**Practical Implementation (The Pragmatist):**
- Use proper debugging tools for your environment
- Document your findings and solutions
- Create test cases to prevent regression

**Risk Mitigation (The Skeptic):**
- Don't assume the obvious cause is correct
- Consider edge cases and boundary conditions
- Validate fixes thoroughly before deployment

This synthesis combines systematic methodology with practical tools and risk awareness for effective debugging.

ℹ️  Direct synthesis from advisory council (no voting)
```

## Development

### Project Structure
```
primeminister/
├── src/
│   ├── primeminister/
│   │   ├── __init__.py
│   │   ├── cli.py           # Command-line interface
│   │   ├── core.py          # Main PrimeMinister class
│   │   ├── config_manager.py # Configuration management
│   │   ├── logger.py        # JSON logging system
│   │   └── config.json      # Default configuration
│   ├── setup.py
│   └── requirements.txt
├── README.md
└── Makefile
```

### Building and Testing
```bash
# Install in development mode
make install-dev

# Run tests (when implemented)
make test

# Build distribution
make build

# Clean build artifacts
make clean
```

## Requirements

- Python 3.8+
- OpenAI API key
- Internet connection for API calls

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Roadmap

- [ ] Add support for other AI providers (Anthropic, local models)
- [ ] Implement custom council member creation via CLI
- [ ] Add web interface
- [ ] Plugin system for specialized council members
- [ ] Integration with popular development tools
- [ ] Advanced voting algorithms
- [ ] Session replay and analysis features
- [ ] Real-time streaming responses
- [ ] Multi-language support

## Support

- 📫 Email: ebennerit@gmail.com
- 🐛 Issues: [GitHub Issues](https://github.com/eb3095/primeminister/issues)
- 📖 Documentation: [GitHub Wiki](https://github.com/eb3095/primeminister/wiki)