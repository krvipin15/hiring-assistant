#!/usr/bin/env python3

"""
Prompts Manager that generates conversation prompts for the Hiring Assistant Chatbot.
 - Greeting, information gathering, tech-stack declaration, technical question generation (3-5 Qs),
   context handling, fallback, graceful exit, and secure handling of "reveal answers" requests.
 - Includes few-shot examples where they improve clarity.
"""

from typing import Dict, List

class PromptsManager:
    # Conversation-ending keywords the chatbot must recognize (checked by the app logic)
    EXIT_KEYWORDS: List[str] = ["exit", "quit", "cancel", "bye", "goodbye", "stop"]

    def __init__(self) -> None:
        """Initialize PromptsManager."""
        # Keep any reusable pieces centralized
        self.validation_hints = {
            "email": "Please provide an email in the format name@domain.com.",
            "phone_number": "Please provide your phone number including country code (e.g., +91 0123456789).",
            "experience_years": "Enter a whole number representing years of experience (e.g., 0, 1, 3, 5).",
            "current_location": "Please provide your current location (e.g., city, country)."
        }

    def get_greeting_prompt(self) -> str:
        """Greeting prompt: welcomes, explains purpose, sets expectations, lists exit keywords, asks name."""
        return f"""\
            CONTEXT: This is the first message shown to a candidate interacting with TalentScout's hiring assistant.
            INSTRUCTIONS:
            - Greet the candidate warmly and professionally.
            - Briefly explain the assistant's purpose: an initial screening that collects basic details and asks tailored technical questions.
            - State an estimated duration for this initial screening (10-20 minutes) and mention the candidate can stop at any time using the exit keywords listed.
            - Ask for the candidate's full name to begin.
            - Keep tone friendly, professional, and concise.
            EXIT KEYWORDS: {', '.join(self.EXIT_KEYWORDS)}
            OUTPUT FORMAT: One short welcoming paragraph followed by a single direct question asking for the candidate's full name.
            FEW-SHOT EXAMPLES:
            - Example 1: Hello and welcome to TalentScout! I'm here to run a short initial screening to collect a few details \
                and ask some technical questions tailored to your skills. This should take about 10-15 minutes. If you want to \
                end at any time, type one of these words: exit, quit, cancel, bye, goodbye, stop. To start, what's your full name?
            - Example 2: Hi there — glad you joined TalentScout's hiring assistant. I'll collect some basic information and then \
                ask 3–5 technical questions based on your tech stack; the whole process takes roughly 10–20 minutes. To stop anytime, \
                use: exit, quit, cancel, bye, goodbye, stop. What's your full name?
            """

    def get_information_gathering_prompt(self, field_name: str, current_info: Dict | None = None) -> str:
        """
        Builds a focused prompt to request a specific field.
        - Instructs: be brief, don't re-ask fields already present in current_info.
        - Provides validation guidance when applicable.
        """
        already_have = ""
        if current_info and field_name in current_info:
            already_have = (
                f"NOTE: The system already has a value for '{field_name}'. Do NOT ask for it again."
            )

        validation = ""
        if field_name in self.validation_hints:
            validation = f"Validation hint: {self.validation_hints[field_name]}"

        # Provide a few-shot example mapping field -> short question
        examples = {
            "full_name": "What's your full name?",
            "email": "What's your email address?",
            "phone_number": "What's your phone number?",
            "experience_years": "How many years of professional experience do you have?",
            "desired_positions": "Which position(s) are you applying for or interested in?",
            "current_location": "What city and country are you currently located in?",
            "tech_stack": "Please list the programming languages, frameworks, databases, and tools you are proficient in (comma separated)."
        }
        example_q = examples.get(field_name, f"Could you please provide your {field_name}?")

        return f"""\
            CONTEXT: Collect the single field '{field_name}' from the candidate during initial screening.
            INSTRUCTIONS:
            - Ask for '{field_name}' in one direct, conversational sentence.
            - Be brief and professional.
            - If {field_name} is already known, do NOT re-ask (see note below).
            - If the previous answer was invalid, acknowledge the correction need briefly and re-request in a corrected format.
            {already_have}
            {validation}
            OUTPUT FORMAT: A single clear question asking for the {field_name}.
            EXAMPLE:
            - {example_q}
            """

    def get_transition_prompt(self, tech_stack: str, experience_years: int) -> str:
        """Transition: acknowledges info collection and explains the technical assessment next steps."""
        return f"""\
            CONTEXT: Candidate provided {experience_years} years of experience and listed these technologies: {tech_stack}.
            INSTRUCTIONS:
            - Acknowledge completion of information gathering (brief).
            - Explain that you'll now ask technical questions tailored to their tech stack.
            - Set expectations (number of questions: 3-5, type: mix of conceptual + applied; time: a few minutes).
            - Encourage the candidate and be professional.
            - Do not repeat their full tech stack back verbatim; summarize briefly ("technologies you listed").
            OUTPUT FORMAT: A short transition paragraph and an introductory sentence announcing the first technical question.
            EXAMPLE: Great — thanks for that information. I'll now ask 3–5 technical questions based on the technologies you listed to better understand your experience level. Let's begin with the first question:
            """

    def get_question_generation_prompt(self, tech_stack: str, experience_years: int) -> str:
        """
        Generate 3-5 technical interview questions.
        - Theoretical questions and no coding tasks.
        - Matches difficulty to experience level.
        - Covers multiple items from the tech stack.
        - Avoids yes/no questions.
        - Includes one short few-shot mapping example to show expected specificity.
        """
        difficulty = ("junior" if experience_years < 2 else "mid-level" if experience_years < 5 else "senior")

        # Few-shot examples (input -> expected JSON output)
        few_shot = """\
            FEW-SHOT:
            Input: tech_stack = "Python, Django, PostgreSQL"; experience_years = 3
            Expected output (JSON array only):
            [
            "Explain how Django's ORM handles relationships and give an example of when you'd use select_related versus prefetch_related.",
            "How would you design and optimize a SQL query in PostgreSQL that joins three tables to minimize read time? Provide the main strategies you would use.",
            "Describe how you would implement authentication and session management in a Django app intended for production."
            ]
            """

        return f"""\
            CONTEXT: Generate technical interview questions for a candidate with {experience_years} years ({difficulty}) who listed: {tech_stack}.
            INSTRUCTIONS:
            - Produce between 3 and 5 well-crafted technical questions (no fewer, no more).
            - Cover different technologies from the provided tech_stack where possible.
            - Match question depth to the {difficulty} level.
            - Mix theory and practical/problem-solving; questions must require more than yes/no answers.
            - Do NOT include answer keys, hints, or scoring rubrics in the output.
            - CRITICALLY: Return ONLY a JSON array of question strings and nothing else (no surrounding text, no commentary).
            {few_shot}
            OUTPUT: The assistant's response must be exactly a JSON array of strings (e.g., [\"Q1\",\"Q2\",\"Q3\"])."""

    def get_end_conversation_prompt(self) -> str:
        """Concluding prompt: thanks, next steps, timeline, contact info."""
        return """\
            CONTEXT: The initial screening is complete.
            INSTRUCTIONS:
            - Thank the candidate for their time.
            - Briefly state what happens next (review by hiring team).
            - Provide a realistic timeline (e.g., 2-3 business days).
            - Give a contact or support note ("if you have questions, contact...") — leave the actual contact tokenized for the application to inject.
            - End positively and professionally.
            OUTPUT FORMAT: A short concluding paragraph mentioning next steps and timeline.
            EXAMPLE: Thank you for completing the initial screening. Our hiring team will review your responses and get back to you within 2-3 business days with next steps. If you have any questions, please contact our recruiting team (contact info provided on the Careers page). Have a great day!
            """

    def get_acknowledgement_prompt(self, user_response: str, field_name: str = "") -> str:
        """Brief, friendly acknowledgement without repeating the user's response."""
        return f"""\
            CONTEXT: Candidate provided a value for {field_name}.
            INSTRUCTIONS:
            - Acknowledge briefly and positively.
            - Do NOT repeat the candidate's exact response back.
            - Keep it short and conversational.
            OUTPUT FORMAT: One short acknowledgement sentence.
            EXAMPLE: Got it — thanks!"""

    def get_fallback_prompt(self, user_input: str, current_context: str) -> str:
        """
        Robust fallback for unclear input.
        - Politely say the input wasn't understood.
        - Rephrase the original question or provide the exact data needed.
        - If the user asked to see 'answers' (attempt to reveal model's test/expected answers), refuse and redirect.
        """
        # The fallback contains two flows: generic unclear input and explicit "reveal answers" refusal instruction.
        return f"""\
            CONTEXT: The candidate provided: \"{user_input}\" while we were trying to {current_context}.
            INSTRUCTIONS:
            - If the user's message appears unrelated or unclear, say you didn't understand and restate what specific information is needed (one short sentence).
            - Provide a corrected short example of the expected response or re-ask the question.
            - If the candidate attempts to 'reveal' or 'see' the correct answers to the technical questions (i.e., requests model's internal answers or a solution key), DO NOT provide them. Instead:
                * Briefly refuse: explain that answer keys or model solution texts are not shared to preserve assessment integrity.
                * Offer a safe alternative: offer constructive feedback, hints, or suggest the candidate ask for clarification on a specific question they answered.
            - Keep tone polite and non-judgmental.
            OUTPUT FORMAT: A single short clarification OR a refusal + alternative if the user asked to reveal answers.
            EXAMPLES:
            - Unclear input: I'm sorry — I didn't quite get that. Could you please tell me your current city and country (e.g., 'Bengaluru, India')?
            - Attempt to reveal answers: I can't share official answer keys or solution texts from the assessment. If you'd like, \
                I can give constructive feedback on one of your answers or clarify what the question was asking. Which question would you like feedback on?
            """

    def get_graceful_exit_prompt(self) -> str:
        """Short polite goodbye that notes saved info and next steps."""
        return """\
            CONTEXT: Candidate used an exit keyword and wants to end the conversation.
            INSTRUCTIONS:
            - Thank them for their time and note that any collected information is saved.
            - Mention that the hiring team will follow up if applicable.
            - Keep it brief and professional.
            OUTPUT FORMAT: One or two short sentences.
            EXAMPLE: Thank you for your time — your information has been saved. Our recruiting team will review it and contact you if there are next steps. Goodbye!
            """

    def get_validation_error_prompt(self, field_name: str) -> str:
        """Prompt for asking the candidate to correct an invalid field entry."""
        hint = self.validation_hints.get(field_name, f"Please provide a valid {field_name}.")
        return f"""\
            CONTEXT: Candidate provided invalid '{field_name}' and must be asked to correct it.
            INSTRUCTIONS:
            - Explain the issue briefly and provide the expected format or range.
            - Re-ask the field in one short sentence.
            OUTPUT FORMAT: One short validation message + the re-request.
            EXAMPLE: {hint}
            """
