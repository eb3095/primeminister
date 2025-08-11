import asyncio
import json
import random
import uuid
from typing import Dict, List, Any, Tuple
import openai
from openai import AsyncOpenAI

from .config_manager import ConfigManager
from .logger import PrimeMinisterLogger


class CouncilMember:
    """Represents a single council member with their personality and voting capabilities."""

    def __init__(self, model: str, personality: str, voter: bool = True, silent: bool = False):
        self.model = model
        self.personality = personality
        self.is_voter = voter
        self.is_silent = silent
        self.response = ""

    def __repr__(self):
        return f"CouncilMember(personality='{self.personality[:30]}...', voter={self.is_voter}, silent={self.is_silent})"


class PrimeMinister:
    """Main class that orchestrates the council discussion and decision-making process."""

    def __init__(self, mode_override=None):
        self.config_manager = ConfigManager()
        self.logger = PrimeMinisterLogger()
        self.std_logger = self.logger.setup_standard_logging()

        # Load configuration
        self.config = self.config_manager.load_config()

        # Apply mode override if provided
        if mode_override:
            self.config["mode"] = mode_override
            self.std_logger.info("Mode overridden to: %s", mode_override)

        # Initialize async OpenAI client
        self.client = AsyncOpenAI(
            api_key=self.config.get("openai_key"),
            base_url=self.config.get("api_url", "https://api.openai.com/v1"),
        )

        # Initialize council members
        self.council = self._initialize_council()

        mode = self.config.get("mode", "council")
        self.std_logger.info(
            "PrimeMinister initialized with %d council members in %s mode", len(self.council), mode
        )

    def _initialize_council(self) -> List[CouncilMember]:
        """Initialize council members from configuration."""
        council = []

        for member_config in self.config.get("council", []):
            member = CouncilMember(
                model=member_config.get("model", self.config.get("model", "gpt-4")),
                personality=member_config.get("personality", ""),
                voter=member_config.get("voter", True),
                silent=member_config.get("silent", False),
            )
            council.append(member)

        return council

    def _build_council_prompt(self, user_prompt: str, member: CouncilMember) -> str:
        """Build the complete prompt for a council member."""
        base_prompt = self.config.get("universal_council_prompt", "")
        user_info = self._get_user_context()

        full_prompt = f"""
{base_prompt}

Your specific role and personality:
{member.personality}

User context:
{user_info}

User's question/problem:
{user_prompt}

Provide your advice based on your unique perspective and expertise.
"""
        return full_prompt.strip()

    def _get_user_context(self) -> str:
        """Get user context from configuration."""
        user_config = self.config.get("user", {})
        attributes = user_config.get("attributes", [])
        goal = user_config.get("goal", "")

        context = f"User attributes: {', '.join(attributes)}\n"
        if goal:
            context += f"User goal: {goal}"

        return context

    async def _get_council_response(self, member: CouncilMember, prompt: str) -> str:
        """Get response from a single council member."""
        try:
            full_prompt = self._build_council_prompt(prompt, member)

            response = await self.client.chat.completions.create(
                model=member.model,
                messages=[{"role": "user", "content": full_prompt}],
                temperature=self.config.get("temperature", 0.7),
                max_tokens=1000,
            )

            member.response = response.choices[0].message.content
            self.std_logger.info(
                "Received response from council member: %s", member.personality[:50]
            )
            return member.response

        except Exception as e:
            self.std_logger.error(
                "Error getting response from council member %s: %s", member.personality[:50], str(e)
            )
            member.response = f"Error: Unable to get response from this council member. ({str(e)})"
            return member.response

    async def gather_council_responses(self, prompt: str) -> List[Dict[str, Any]]:
        """Gather responses from all council members."""
        self.std_logger.info("Gathering responses from %d council members", len(self.council))

        # Get responses from all non-silent members
        tasks = []
        for member in self.council:
            if not member.is_silent:
                tasks.append(self._get_council_response(member, prompt))

        # Wait for all responses
        if tasks:
            await asyncio.gather(*tasks)

        # Prepare response data with UUIDs and check for errors
        responses = []
        error_count = 0

        for member in self.council:
            if not member.is_silent:
                is_error = member.response.startswith("Error:")
                if is_error:
                    error_count += 1

                responses.append(
                    {
                        "uuid": str(uuid.uuid4()),
                        "personality": member.personality,
                        "model": member.model,
                        "response": member.response,
                        "is_voter": member.is_voter,
                        "is_silent": member.is_silent,
                        "has_error": is_error,
                    }
                )

        # Check if too many responses failed
        total_responses = len(responses)
        if total_responses == 0:
            raise RuntimeError("No council members provided responses")

        if error_count == total_responses:
            error_msg = f"All {total_responses} council members failed to respond. First error: {responses[0]['response']}"
            self.std_logger.error(error_msg)
            raise RuntimeError(error_msg)

        if error_count > total_responses / 2:
            error_msg = f"Too many council members failed ({error_count}/{total_responses}). Cannot proceed with reliable decision-making."
            self.std_logger.error(error_msg)
            raise RuntimeError(error_msg)

        if error_count > 0:
            self.std_logger.warning(
                "Some council members failed (%d/%d), but continuing with available responses",
                error_count,
                total_responses,
            )

        return responses

    async def conduct_voting(
        self, responses: List[Dict[str, Any]], user_prompt: str
    ) -> Dict[str, List[str]]:
        """Conduct blind voting among council members."""
        self.std_logger.info("Conducting voting among council members")

        # Get voting members
        voters = [member for member in self.council if member.is_voter]

        # Get response options (non-silent responses without errors)
        response_options = [
            resp
            for resp in responses
            if not resp.get("is_silent", False) and not resp.get("has_error", False)
        ]

        if not response_options:
            error_msg = (
                "No valid responses available for voting (all responses were silent or had errors)"
            )
            self.std_logger.error(error_msg)
            raise RuntimeError(error_msg)

        # Conduct analyzed voting in parallel (each voter evaluates all responses)
        voting_tasks = []
        for voter in voters:
            voting_tasks.append(self._conduct_analyzed_vote(voter, response_options, user_prompt))

        # Execute all voting in parallel
        vote_results = await asyncio.gather(*voting_tasks)

        # Process vote results
        votes = {}
        detailed_votes = []

        for vote_result in vote_results:
            if vote_result:  # Skip None results from errors
                chosen_response = next(
                    (
                        r
                        for r in response_options
                        if r["uuid"] == vote_result["chosen_response_uuid"]
                    ),
                    None,
                )
                if chosen_response:
                    personality = chosen_response["personality"]
                    voter_name = vote_result["voter_name"]

                    # Add to simple vote tracking (for backward compatibility)
                    if personality not in votes:
                        votes[personality] = []
                    votes[personality].append(voter_name)

                    # Add to detailed vote tracking
                    detailed_votes.append(
                        {
                            "vote_uuid": vote_result["vote_uuid"],
                            "voter": voter_name,
                            "chosen_response_personality": personality,
                            "chosen_response_uuid": vote_result["chosen_response_uuid"],
                            "reasoning": vote_result["reasoning"],
                        }
                    )

        self.std_logger.info("Voting completed. Results: %s", {k: len(v) for k, v in votes.items()})

        return votes, detailed_votes

    async def _conduct_analyzed_vote(
        self, voter: "CouncilMember", response_options: List[Dict[str, Any]], user_prompt: str
    ) -> Dict[str, str]:
        """Have a council member analyze all responses and vote for the best one."""
        try:
            # Build blind voting prompt for this council member
            base_prompt = self.config.get("universal_council_prompt", "")
            user_info = self._get_user_context()

            voting_prompt = f"""
{base_prompt}

Your specific role and personality:
{voter.personality}

User context:
{user_info}

You are now voting on the best response to the user's question. You must evaluate all the responses below and choose the ONE that you think best addresses the user's question from your unique perspective.

IMPORTANT: The responses are presented anonymously to ensure unbiased evaluation. Focus only on the content quality and relevance to the user's needs.

Original user question:
{user_prompt}

Here are the responses to evaluate:

"""

            # Add all response options (BLIND - no personality names)
            for i, response in enumerate(response_options, 1):
                content = response["response"]

                voting_prompt += f"""
Option {i}:
{content}

---
"""

            voting_prompt += f"""
Based on your evaluation criteria as {voter.personality.split(' - ')[0] if ' - ' in voter.personality else voter.personality}, which response do you think is best?

Respond with ONLY the number of your choice (1-{len(response_options)}) followed by your detailed reasoning.
Example: "3 - I choose this response because it demonstrates superior logical structure, provides concrete actionable steps, and directly addresses the user's specific situation with clear evidence-based reasoning."

Your reasoning will be logged for transparency and audit purposes.
"""

            # Get the voter's choice
            response = await self.client.chat.completions.create(
                model=voter.model,
                messages=[{"role": "user", "content": voting_prompt}],
                temperature=self.config.get("temperature", 0.7),
                max_tokens=500,
            )

            vote_response = response.choices[0].message.content.strip()
            self.std_logger.info("Vote from %s: %s", voter.personality[:30], vote_response[:100])

            # Parse the voter's choice and create structured result
            vote_uuid = str(uuid.uuid4())
            voter_name = (
                voter.personality.split(" - ")[0]
                if " - " in voter.personality
                else voter.personality[:20]
            )

            try:
                # Split on first dash to separate choice from reasoning
                parts = vote_response.split("-", 1)
                choice_num = int(parts[0].strip())
                reasoning = parts[1].strip() if len(parts) > 1 else "No reasoning provided"

                if 1 <= choice_num <= len(response_options):
                    chosen_response = response_options[choice_num - 1]
                    return {
                        "vote_uuid": vote_uuid,
                        "voter_name": voter_name,
                        "chosen_response_uuid": chosen_response["uuid"],
                        "reasoning": reasoning,
                    }
                else:
                    # Fallback: choose first response
                    self.std_logger.warning(
                        "Invalid vote choice from %s, defaulting to first option",
                        voter.personality[:30],
                    )
                    return {
                        "vote_uuid": vote_uuid,
                        "voter_name": voter_name,
                        "chosen_response_uuid": response_options[0]["uuid"],
                        "reasoning": f"Fallback choice due to invalid selection: {reasoning}",
                    }

            except (ValueError, IndexError):
                # Fallback: choose first response
                self.std_logger.warning(
                    "Could not parse vote from %s, defaulting to first option",
                    voter.personality[:30],
                )
                return {
                    "vote_uuid": vote_uuid,
                    "voter_name": voter_name,
                    "chosen_response_uuid": response_options[0]["uuid"],
                    "reasoning": f"Fallback choice due to parse error: {vote_response}",
                }

        except Exception as e:
            self.std_logger.error("Error getting vote from %s: %s", voter.personality[:30], str(e))
            # Return None to indicate failure
            return None

    def _detect_tie(self, votes: Dict[str, List[str]]) -> bool:
        """Detect if there's a tie in the voting results."""
        if not votes:
            return False

        vote_counts = [len(voters) for voters in votes.values()]
        max_votes = max(vote_counts)

        # Count how many responses have the maximum vote count
        tied_responses = sum(1 for count in vote_counts if count == max_votes)

        return tied_responses > 1

    async def _prime_minister_tiebreaker(
        self, responses: List[Dict[str, Any]], votes: Dict[str, List[str]], original_prompt: str
    ) -> str:
        """Prime Minister casts the deciding vote in case of a tie."""
        self.std_logger.info("Tie detected - Prime Minister casting deciding vote")

        # Get tied responses (those with the maximum vote count)
        max_votes = max(len(voters) for voters in votes.values())
        tied_responses = [
            resp for resp in responses if len(votes.get(resp["personality"], [])) == max_votes
        ]

        # Build prompt for Prime Minister to choose between tied responses
        tie_prompt = f"""
You are the Prime Minister and there is a TIE in the council voting. You must cast the deciding vote.

Original user question:
{original_prompt}

The following responses are tied with {max_votes} vote(s) each:

"""

        for i, response in enumerate(tied_responses, 1):
            personality = response["personality"]
            voters = ", ".join(votes.get(personality, []))

            tie_prompt += f"""
Option {i} - {personality}:
{response['response']}
Voted for by: {voters}

---
"""

        tie_prompt += f"""
As Prime Minister, you must choose which response best addresses the user's question.

Respond with ONLY the number of your choice (1-{len(tied_responses)}) followed by a brief explanation of your reasoning.
Example: "2 - I choose this response because..."
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.config.get("model", "gpt-4"),
                messages=[{"role": "user", "content": tie_prompt}],
                temperature=self.config.get("temperature", 0.7),
                max_tokens=500,
            )

            pm_choice = response.choices[0].message.content.strip()
            self.std_logger.info("Prime Minister's tie-breaking choice: %s", pm_choice[:100])

            # Parse the Prime Minister's choice
            try:
                choice_num = int(pm_choice.split("-")[0].strip())
                if 1 <= choice_num <= len(tied_responses):
                    chosen_response = tied_responses[choice_num - 1]
                    chosen_personality = chosen_response["personality"]

                    # Add Prime Minister's deciding vote
                    if chosen_personality not in votes:
                        votes[chosen_personality] = []
                    votes[chosen_personality].append("Prime Minister (tie-breaker)")

                    return chosen_personality
                else:
                    # Fallback: choose first tied response
                    chosen_personality = tied_responses[0]["personality"]
                    votes[chosen_personality].append("Prime Minister (tie-breaker - fallback)")
                    return chosen_personality

            except (ValueError, IndexError):
                # Fallback: choose first tied response
                chosen_personality = tied_responses[0]["personality"]
                votes[chosen_personality].append("Prime Minister (tie-breaker - fallback)")
                return chosen_personality

        except Exception as e:
            self.std_logger.error("Error in Prime Minister tie-breaker: %s", str(e))
            # Fallback: choose first tied response
            chosen_personality = tied_responses[0]["personality"]
            votes[chosen_personality].append("Prime Minister (tie-breaker - error fallback)")
            return chosen_personality

    async def prime_minister_decision(
        self, responses: List[Dict[str, Any]], votes: Dict[str, List[str]], original_prompt: str
    ) -> str:
        """Prime Minister makes the final decision and presents it."""
        self.std_logger.info("Prime Minister making final decision")

        # Build context for Prime Minister
        pm_prompt = f"""
{self.config.get('primeminister_prompt', '')}

Original user question:
{original_prompt}

Council responses and voting results:

"""

        # Add each response with vote counts
        for response in responses:
            personality = response["personality"]
            vote_count = len(votes.get(personality, []))
            voters = ", ".join(votes.get(personality, []))

            pm_prompt += f"""
Response from {personality}:
{response['response']}
Votes received: {vote_count} ({voters})

---
"""

        pm_prompt += """
Based on the council's advice and the voting results, provide your final decision and reasoning.
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.config.get("model", "gpt-4"),
                messages=[{"role": "user", "content": pm_prompt}],
                temperature=self.config.get("temperature", 0.7),
                max_tokens=1500,
            )

            final_decision = response.choices[0].message.content
            self.std_logger.info("Prime Minister decision completed")
            return final_decision

        except Exception as e:
            self.std_logger.error("Error getting Prime Minister decision: %s", str(e))
            return f"Error: The Prime Minister was unable to make a decision. ({str(e)})"

    async def conduct_opinion_rounds(
        self, initial_responses: List[Dict[str, Any]], user_prompt: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Conduct two rounds of opinions in advisor mode.

        Round 1: Each advisor gives opinions on other advisors' initial responses
        Round 2: Original advisors respond to the opinions on their entries

        Returns:
            Tuple of (first_round_opinions, second_round_responses)
        """
        self.std_logger.info("Starting two-round opinion process using async processing")

        # Round 1: Collect opinions from each advisor on each initial response
        async def get_opinion(advisor, response):
            """Get a single opinion from an advisor on a response."""
            opinion_prompt = f"""
{self.config.get('universal_council_prompt', '')}

Original user question:
{user_prompt}

Response from {response['personality']}:
{response['response']}

As {advisor.personality}, provide your professional opinion on this response. Consider:
- Strengths and weaknesses of the approach
- Missing considerations or perspectives
- How it could be improved or extended
- Whether you agree or disagree and why

Be constructive and specific in your feedback.
"""

            try:
                api_response = await self.client.chat.completions.create(
                    model=advisor.model,
                    messages=[{"role": "user", "content": opinion_prompt}],
                    temperature=self.config.get("temperature", 0.7),
                    max_tokens=800,
                )

                opinion_content = api_response.choices[0].message.content
                opinion_uuid = str(uuid.uuid4())

                opinion = {
                    "uuid": opinion_uuid,
                    "opinion_giver": advisor.personality,
                    "opinion_giver_model": advisor.model,
                    "target_response_uuid": response["uuid"],
                    "target_advisor": response["personality"],
                    "opinion": opinion_content,
                    "has_error": False,
                }

                self.std_logger.info(
                    "Opinion collected from %s on %s's response",
                    advisor.personality,
                    response["personality"],
                )
                return opinion

            except Exception as e:
                self.std_logger.error(
                    "Error getting opinion from %s: %s", advisor.personality, str(e)
                )
                return {
                    "uuid": str(uuid.uuid4()),
                    "opinion_giver": advisor.personality,
                    "opinion_giver_model": advisor.model,
                    "target_response_uuid": response["uuid"],
                    "target_advisor": response["personality"],
                    "opinion": f"Error: Unable to provide opinion. ({str(e)})",
                    "has_error": True,
                }

        # Collect all opinion tasks for parallel execution
        opinion_tasks = []
        for advisor in self.council:
            if advisor.is_silent:
                continue
            # Each advisor gives opinions on all initial responses (except their own)
            for response in initial_responses:
                if response["personality"] == advisor.personality:
                    continue  # Skip own response
                opinion_tasks.append(get_opinion(advisor, response))

        # Execute all opinion requests in parallel
        first_round_opinions = []
        if opinion_tasks:
            first_round_opinions = await asyncio.gather(*opinion_tasks)

        # Round 2: Original advisors respond to opinions on their responses
        async def get_second_round_response(original_response, opinions_on_response):
            """Get a second round response from an advisor to opinions on their original response."""
            # Find the original advisor
            original_advisor = None
            for advisor in self.council:
                if advisor.personality == original_response["personality"]:
                    original_advisor = advisor
                    break

            if not original_advisor or original_advisor.is_silent:
                return None

            # Build prompt with all opinions
            opinions_text = ""
            for opinion in opinions_on_response:
                opinions_text += f"""
Opinion from {opinion['opinion_giver']}:
{opinion['opinion']}

---
"""

            response_prompt = f"""
{self.config.get('universal_council_prompt', '')}

Original user question:
{user_prompt}

Your original response:
{original_response['response']}

Colleagues' opinions on your response:
{opinions_text}

As {original_advisor.personality}, please provide a thoughtful response to these opinions. You may:
- Acknowledge valid points and incorporate them
- Clarify or defend aspects of your original response
- Expand on areas that colleagues highlighted
- Adjust your recommendations based on the feedback

Provide a refined perspective that takes the opinions into account.
"""

            try:
                api_response = await self.client.chat.completions.create(
                    model=original_advisor.model,
                    messages=[{"role": "user", "content": response_prompt}],
                    temperature=self.config.get("temperature", 0.7),
                    max_tokens=1000,
                )

                response_content = api_response.choices[0].message.content
                response_uuid = str(uuid.uuid4())

                second_round_response = {
                    "uuid": response_uuid,
                    "personality": original_advisor.personality,
                    "model": original_advisor.model,
                    "original_response_uuid": original_response["uuid"],
                    "response_to_opinions": response_content,
                    "opinions_considered": [op["uuid"] for op in opinions_on_response],
                    "has_error": False,
                }

                self.std_logger.info(
                    "Second round response collected from %s", original_advisor.personality
                )
                return second_round_response

            except Exception as e:
                self.std_logger.error(
                    "Error getting second round response from %s: %s",
                    original_advisor.personality,
                    str(e),
                )
                return {
                    "uuid": str(uuid.uuid4()),
                    "personality": original_advisor.personality,
                    "model": original_advisor.model,
                    "original_response_uuid": original_response["uuid"],
                    "response_to_opinions": f"Error: Unable to respond to opinions. ({str(e)})",
                    "opinions_considered": [op["uuid"] for op in opinions_on_response],
                    "has_error": True,
                }

        # Collect all second round tasks for parallel execution
        second_round_tasks = []
        for original_response in initial_responses:
            # Find all opinions on this response
            opinions_on_response = [
                op
                for op in first_round_opinions
                if op["target_response_uuid"] == original_response["uuid"] and not op["has_error"]
            ]

            if not opinions_on_response:
                continue  # No opinions to respond to

            second_round_tasks.append(
                get_second_round_response(original_response, opinions_on_response)
            )

        # Execute all second round requests in parallel
        second_round_responses = []
        if second_round_tasks:
            responses = await asyncio.gather(*second_round_tasks)
            # Filter out None responses (from silent advisors)
            second_round_responses = [r for r in responses if r is not None]

        self.std_logger.info(
            "Two-round opinion process completed: %d opinions, %d responses",
            len(first_round_opinions),
            len(second_round_responses),
        )

        return first_round_opinions, second_round_responses

    async def prime_minister_advisor_synthesis_with_opinions(
        self,
        initial_responses: List[Dict[str, Any]],
        first_round_opinions: List[Dict[str, Any]],
        second_round_responses: List[Dict[str, Any]],
        original_prompt: str,
    ) -> str:
        """Prime Minister synthesizes advisor responses with two-round opinions."""
        self.std_logger.info(
            "Prime Minister synthesizing advisor responses with two-round opinions"
        )

        # Build comprehensive context for Prime Minister synthesis
        pm_prompt = f"""
{self.config.get('primeminister_advisor_prompt', '')}

Original user question:
{original_prompt}

ROUND 1 - Initial Council Responses:
"""

        # Add initial responses
        for response in initial_responses:
            if not response.get("has_error", False):
                pm_prompt += f"""
{response['personality']}:
{response['response']}

---
"""

        pm_prompt += """
ROUND 2 - Peer Opinions on Initial Responses:
"""

        # Add first round opinions, grouped by target
        for initial_response in initial_responses:
            if initial_response.get("has_error", False):
                continue

            relevant_opinions = [
                op
                for op in first_round_opinions
                if op["target_response_uuid"] == initial_response["uuid"]
                and not op.get("has_error", False)
            ]

            if relevant_opinions:
                pm_prompt += f"""
Opinions on {initial_response['personality']}'s response:
"""
                for opinion in relevant_opinions:
                    pm_prompt += f"""
  Opinion from {opinion['opinion_giver']}:
  {opinion['opinion']}

"""

        pm_prompt += """
ROUND 3 - Original Advisors' Responses to Opinions:
"""

        # Add second round responses
        for response in second_round_responses:
            if not response.get("has_error", False):
                pm_prompt += f"""
{response['personality']}'s response to colleague opinions:
{response['response_to_opinions']}

---
"""

        pm_prompt += """
Based on this comprehensive three-round advisory process, synthesize the collective wisdom into the most helpful and well-reasoned response for the user. Consider:
- The initial diverse perspectives and their individual strengths
- The constructive peer feedback and critical analysis
- How the original advisors refined their thinking based on colleague input
- Areas of consensus and productive disagreement
- The evolution of ideas through the discussion process

Provide a final recommendation that represents the best of the collective advisory process.
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.config.get("model", "gpt-4"),
                messages=[{"role": "user", "content": pm_prompt}],
                temperature=self.config.get("temperature", 0.7),
                max_tokens=2500,
            )

            final_synthesis = response.choices[0].message.content
            self.std_logger.info("Prime Minister advisor synthesis with opinions completed")
            return final_synthesis

        except Exception as e:
            self.std_logger.error("Error in Prime Minister advisor synthesis: %s", str(e))
            return f"Error: The Prime Minister was unable to synthesize the advisory discussion. ({str(e)})"

    async def prime_minister_advisor_synthesis(
        self, responses: List[Dict[str, Any]], original_prompt: str
    ) -> str:
        """Prime Minister synthesizes advisor responses directly without voting (legacy single-round mode)."""
        self.std_logger.info("Prime Minister synthesizing advisor responses (single round)")

        # Build context for Prime Minister advisor synthesis
        pm_prompt = f"""
{self.config.get('primeminister_advisor_prompt', '')}

Original user question:
{original_prompt}

Council advisor responses:

"""

        # Add each advisor response
        for response in responses:
            if not response.get("has_error", False):
                personality = response["personality"]
                content = response["response"]

                pm_prompt += f"""
{personality}:
{content}

---
"""

        pm_prompt += """
Based on the diverse perspectives and expertise of your advisory council, synthesize their insights into the most comprehensive and helpful response for the user. Draw from the strengths of each advisor's perspective while creating a cohesive, well-reasoned final recommendation.
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.config.get("model", "gpt-4"),
                messages=[{"role": "user", "content": pm_prompt}],
                temperature=self.config.get("temperature", 0.7),
                max_tokens=2000,
            )

            final_synthesis = response.choices[0].message.content
            self.std_logger.info("Prime Minister advisor synthesis completed")
            return final_synthesis

        except Exception as e:
            self.std_logger.error("Error in Prime Minister advisor synthesis: %s", str(e))
            return f"Error: The Prime Minister was unable to synthesize the responses. ({str(e)})"

    async def process_request(self, user_prompt: str) -> Tuple[str, Dict[str, Any]]:
        """Process a complete user request through the council system."""
        # Generate UUIDs for this session
        session_uuid = str(uuid.uuid4())
        question_uuid = str(uuid.uuid4())

        self.std_logger.info(
            "Processing new request (session: %s): %s", session_uuid, user_prompt[:100]
        )

        try:
            # Step 1: Gather council responses
            responses = await self.gather_council_responses(user_prompt)

            # Check mode to determine next steps
            mode = self.config.get("mode", "council")

            if mode == "advisor":
                # Advisor mode: Two-round opinion system, then PM synthesis
                self.std_logger.info("Running in advisor mode with two-round opinions")
                votes = {}
                detailed_votes = []
                tie_broken = False

                # Conduct two rounds of opinions using async processing
                first_round_opinions, second_round_responses = await self.conduct_opinion_rounds(
                    responses, user_prompt
                )

                # Prime Minister synthesizes with all rounds
                final_decision = await self.prime_minister_advisor_synthesis_with_opinions(
                    responses, first_round_opinions, second_round_responses, user_prompt
                )
            else:
                # Council mode: Full voting process
                self.std_logger.info("Running in council mode - conducting voting")

                # Step 2: Conduct voting
                votes, detailed_votes = await self.conduct_voting(responses, user_prompt)

                # Step 2.5: Handle tie-breaking if necessary
                tie_broken = False
                if self._detect_tie(votes):
                    tie_winner = await self._prime_minister_tiebreaker(
                        responses, votes, user_prompt
                    )
                    tie_broken = True
                    self.std_logger.info("Tie broken by Prime Minister in favor of: %s", tie_winner)

                # Step 3: Prime Minister decision
                final_decision = await self.prime_minister_decision(responses, votes, user_prompt)

            result_uuid = str(uuid.uuid4())

            # Step 4: Log the session
            metadata = {
                "session_uuid": session_uuid,
                "question_uuid": question_uuid,
                "result_uuid": result_uuid,
                "mode": mode,
                "total_council_members": len(self.council),
                "responding_members": len(responses),
                "voting_members": (
                    len([m for m in self.council if m.is_voter]) if mode == "council" else 0
                ),
                "total_votes_cast": sum(len(v) for v in votes.values()),
                "tie_broken_by_pm": tie_broken,
                "response_uuids": [r["uuid"] for r in responses],
                "detailed_votes": detailed_votes,
            }

            # Add opinion round data for advisor mode
            if mode == "advisor":
                metadata.update(
                    {
                        "opinion_rounds_conducted": 2,
                        "first_round_opinions_count": len(first_round_opinions),
                        "second_round_responses_count": len(second_round_responses),
                        "opinion_uuids": [op["uuid"] for op in first_round_opinions],
                        "second_round_uuids": [sr["uuid"] for sr in second_round_responses],
                    }
                )

            # Pass opinion data to logger for advisor mode
            opinion_data = {}
            if mode == "advisor":
                opinion_data = {
                    "first_round_opinions": first_round_opinions,
                    "second_round_responses": second_round_responses,
                }

            self.logger.log_session(
                prompt=user_prompt,
                council_responses=responses,
                votes=votes,
                final_result=final_decision,
                metadata=metadata,
                **opinion_data,
            )

            self.std_logger.info("Request processing completed successfully")

            session_data = {"responses": responses, "votes": votes, "metadata": metadata}

            # Add opinion data for advisor mode
            if mode == "advisor":
                session_data.update(
                    {
                        "first_round_opinions": first_round_opinions,
                        "second_round_responses": second_round_responses,
                    }
                )

            return final_decision, session_data

        except Exception as e:
            self.std_logger.error(
                "Error processing request (session: %s): %s", session_uuid, str(e)
            )

            # Log the failed session with error details
            error_metadata = {
                "session_uuid": session_uuid,
                "question_uuid": question_uuid,
                "error": str(e),
                "error_type": type(e).__name__,
                "total_council_members": len(self.council),
                "failed_session": True,
            }

            # Try to log the error session (if logging fails, just continue)
            try:
                self.logger.log_session(
                    prompt=user_prompt,
                    council_responses=[],
                    votes={},
                    final_result=f"ERROR: {str(e)}",
                    metadata=error_metadata,
                )
            except Exception as log_error:
                self.std_logger.error("Failed to log error session: %s", str(log_error))

            # Return clear error message to user
            if "403" in str(e) and "gpt-4" in str(e):
                error_message = "Error: Your OpenAI account does not have access to GPT-4. Please check your API key permissions or update the model in the configuration to use 'gpt-3.5-turbo' instead."
            elif "401" in str(e):
                error_message = "Error: Invalid OpenAI API key. Please check your configuration and ensure your API key is correct."
            elif "model_not_found" in str(e):
                error_message = "Error: The specified AI model is not available. Please check your configuration and use a supported model."
            else:
                error_message = f"Error: {str(e)}"

            return error_message, {"error": True, "error_details": str(e)}

    def get_council_summary(self) -> Dict[str, Any]:
        """Get a summary of the current council configuration."""
        return {
            "total_members": len(self.council),
            "voters": len([m for m in self.council if m.is_voter]),
            "silent_members": len([m for m in self.council if m.is_silent]),
            "members": [
                {
                    "personality": (
                        member.personality.split(" - ")[0]
                        if " - " in member.personality
                        else member.personality[:30]
                    ),
                    "model": member.model,
                    "voter": member.is_voter,
                    "silent": member.is_silent,
                }
                for member in self.council
            ],
        }

    async def process_request_json(self, user_prompt: str) -> Dict[str, Any]:
        """
        Process a user request and return the complete response in JSON format.

        This method returns the same data structure that gets logged, making it
        suitable for programmatic use and web API integration.

        Args:
            user_prompt (str): The user's question or problem

        Returns:
            Dict[str, Any]: Complete session data in JSON-serializable format
        """
        final_decision, session_data = await self.process_request(user_prompt)

        # Build the complete JSON response matching the log format
        json_response = {
            "prompt": user_prompt,
            "final_result": final_decision,
            "session_uuid": session_data["metadata"]["session_uuid"],
            "question_uuid": session_data["metadata"]["question_uuid"],
            "result_uuid": session_data["metadata"]["result_uuid"],
            "mode": session_data["metadata"]["mode"],
            "council_responses": session_data["responses"],
            "votes": session_data["votes"],
            "detailed_votes": session_data["metadata"]["detailed_votes"],
            "metadata": {
                "total_council_members": session_data["metadata"]["total_council_members"],
                "responding_members": session_data["metadata"]["responding_members"],
                "voting_members": session_data["metadata"]["voting_members"],
                "total_votes_cast": session_data["metadata"]["total_votes_cast"],
                "tie_broken_by_pm": session_data["metadata"]["tie_broken_by_pm"],
                "response_uuids": session_data["metadata"]["response_uuids"],
                "timestamp": session_data["metadata"].get("timestamp"),
            },
        }

        # Add opinion data for advisor mode
        if session_data["metadata"]["mode"] == "advisor":
            json_response.update(
                {
                    "first_round_opinions": session_data.get("first_round_opinions", []),
                    "second_round_responses": session_data.get("second_round_responses", []),
                }
            )
            json_response["metadata"].update(
                {
                    "opinion_rounds_conducted": session_data["metadata"].get(
                        "opinion_rounds_conducted", 0
                    ),
                    "first_round_opinions_count": session_data["metadata"].get(
                        "first_round_opinions_count", 0
                    ),
                    "second_round_responses_count": session_data["metadata"].get(
                        "second_round_responses_count", 0
                    ),
                    "opinion_uuids": session_data["metadata"].get("opinion_uuids", []),
                    "second_round_uuids": session_data["metadata"].get("second_round_uuids", []),
                }
            )

        return json_response
