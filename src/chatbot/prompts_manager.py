#!/usr/bin/env python3
"""
This module defines the PromptsManager class, which centralizes and generates structured prompt templates for a hiring assistant chatbot.
It provides methods to create context-aware, professional, and user-friendly prompts for various stages of the candidate screening process,
including greetings, information gathering, validation, technical question generation, acknowledgements, and conversation closure.
The prompts are designed to ensure consistency, clarity, and adherence to best practices in candidate communication.

Functions:
    - get_greeting_prompt() -> str: Returns a greeting prompt for the candidate.
    - get_fallback_prompt(user_input: str, current_context: str) -> str: Returns a fallback prompt for unclear or unexpected user input.
    - get_information_gathering_prompt() -> str: Returns a prompt for gathering candidate information.
    - get_validation_prompt(field_name: str) -> str: Returns a validation prompt for a specific field.
    - get_technical_question_prompt() -> str: Returns a prompt for generating technical questions.
    - get_acknowledgement_prompt() -> str: Returns a prompt for acknowledging candidate responses.
    - get_conversation_closure_prompt() -> str: Returns a prompt for closing the conversation.
"""

from typing import Dict

class PromptsManager:
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
            - Briefly explain the assistant's purpose: an initial screening that collects basic details \
                and asks tailored technical questions.
            - State an estimated duration for this initial screening (10-20 minutes) and mention the candidate \
                can stop at any time using the exit keywords listed.
            - Ask for the candidate's full name to begin.
            - Keep tone friendly, professional, and concise.
            OUTPUT FORMAT: One short welcoming paragraph followed by a single direct question asking for the candidate's full name.
            FEW-SHOT EXAMPLES:
            - Example 1: Hello and welcome to TalentScout! I'm here to run a short initial screening to collect a few details \
                and ask some technical questions tailored to your skills. This should take about 10-15 minutes. If you want to \
                end at any time, type one of these words: exit, quit, cancel, bye, goodbye, stop. To start, what's your full name?
            - Example 2: Hi there — glad you joined TalentScout's hiring assistant. I'll collect some basic information and then \
                ask 3–5 technical questions based on your tech stack; the whole process takes roughly 10–20 minutes. To stop anytime, \
                use: exit, quit, cancel, bye, goodbye, stop. What's your full name?
            """

    def get_fallback_prompt(self, user_input: str, current_context: str) -> str:
        """
        Provide meaningful responses when the chatbot does not understand the user input
        or when unexpected inputs are received. It should not deviate from the Purpose.
        """
        return f"""\
            CONTEXT: The candidate provided: \"{user_input}\" while we were trying to {current_context}.
            INSTRUCTIONS:
            - If the input is unclear or unrelated, politely acknowledge that it wasn’t understood.
            - Restate what specific information is needed in one short sentence.
            - Offer a short corrected example of the expected response OR re-ask the original question.
            - If the user requests to 'reveal answers' or access solution keys:
                * Refuse politely, explaining that official answers cannot be shared to protect assessment integrity.
                * Instead, provide safe alternatives:
                    - Offer constructive feedback,
                    - Give helpful hints, or
                    - Suggest they ask for clarification on a specific question they attempted.
            - Always maintain a polite, professional, and non-judgmental tone.
            OUTPUT FORMAT:
            - A single short clarification if input is unclear/unexpected.
            - A refusal + alternative if input is an attempt to reveal answers.
            EXAMPLES:
            - Unclear input: I'm sorry — I didn’t understand that. Could you please share your current city and \
                country (e.g., 'Bengaluru, India')?
            - Attempt to reveal answers: I can’t provide official answer keys or solutions. But I can give you feedback \
                on one of your answers or clarify what the question was asking. Which question would you like help with?
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
            "tech_stack": "Please list the programming languages, frameworks, databases, and \
                tools you are proficient in (comma separated)."
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
            EXAMPLE: Great — thanks for that information. I'll now ask 3–5 technical questions based on the technologies \
                you listed to better understand your experience level. Let's begin with the first question:
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
            "Explain how Django's ORM handles relationships and give an example of when you'd use \
                select_related versus prefetch_related.",
            "How would you design and optimize a SQL query in PostgreSQL that joins three tables to minimize read time? \
                Provide the main strategies you would use.",
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

    def get_end_conversation_prompt(self) -> str:
        """Concluding prompt: thanks, next steps, timeline, contact info."""
        return """\
            CONTEXT: The initial screening is complete.
            INSTRUCTIONS:
            - Thank the candidate for their time.
            - Briefly state what happens next (review by hiring team).
            - Provide a realistic timeline (e.g., 2-3 business days).
            - Give a contact or support note ("if you have questions, contact...") — leave the actual contact tokenized \
                for the application to inject.
            - End positively and professionally.
            OUTPUT FORMAT: A short concluding paragraph mentioning next steps and timeline.
            EXAMPLE: Thank you for completing the initial screening. Our hiring team will review your responses and get \
                back to you within 2-3 business days with next steps. If you have any questions, please contact our recruiting \
                team (contact info provided on the Careers page). Have a great day!
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
            EXAMPLE: Thank you for your time — your information has been saved. Our recruiting team will review it and contact you \
                if there are next steps. Goodbye!
            """
