#!/usr/bin/env python3

"""
Prompts Manager for the TalentScout Hiring Assistant Chatbot
"""

from typing import Dict

class PromptsManager:
    def __init__(self) -> None:
        pass

    def get_greeting_prompt(self) -> str:
        """Core Conversation Prompt #1: Greeting"""
        return """\
            CONTEXT: You are a hiring assistant chatbot for TalentScout, a technology recruitment agency. This is the start of an initial candidate screening conversation.

            INSTRUCTIONS:
            - Welcome the candidate warmly and professionally
            - Explain your purpose and what the process involves
            - Set expectations for the conversation duration
            - Ask for their name to begin information collection
            - Keep the tone friendly but professional

            OUTPUT FORMAT: A welcoming message followed by a request for their name.

            EXAMPLE:
            Hello! Welcome to TalentScout's hiring assistant. I'm here to help with your initial screening process for technology positions.
            I'll need to collect some basic information about you and then ask a few technical questions based on your expertise. This should take about 10-15 minutes.
            Let's start - what's your full name?"""

    def get_information_gathering_prompt(self, field_name: str, current_info: Dict = None) -> str:
        """Core Conversation Prompt #2: Information Gathering"""
        context = f"CONTEXT: You are collecting the '{field_name}' information from a candidate during initial screening.\
              This is part of a structured information gathering process."

        instructions = f"""\
            INSTRUCTIONS:
            - Ask for the {field_name} in a conversational, natural way
            - Be brief and direct
            - If this is a follow-up after validation error, acknowledge the correction needed
            - Maintain professional but friendly tone"""

        output_format = f"OUTPUT FORMAT: A single, clear question asking for {field_name}."

        field_examples = {
            "email": "What's your email address?",
            "phone_number": "What's your phone number?",
            "current_location": "What's your current location (city, country)?",
            "experience_years": "How many years of professional experience do you have?",
            "desired_positions": "What position(s) are you interested in?",
            "tech_stack": "Please list your technical skills - programming languages, frameworks, databases, and tools you're proficient in:"
        }

        example = f"EXAMPLE:\n{field_examples.get(field_name, f'Could you please provide your {field_name}?')}"

        return f"{context}\n\n{instructions}\n\n{output_format}\n\n{example}"

    def get_transition_prompt(self, tech_stack: str, experience_years: int) -> str:
        """Core Conversation Prompt #3: Transition to Technical Assessment"""
        return f"""\
            CONTEXT: You have finished collecting candidate information. The candidate has {experience_years} years of experience and listed these technologies: {tech_stack}. Now transitioning to technical questions.

            INSTRUCTIONS:
            - Acknowledge completion of information gathering
            - Explain what happens next (technical questions)
            - Set expectations for the technical assessment
            - Be encouraging and professional

            OUTPUT FORMAT: A transition message explaining the next phase.

            EXAMPLE:
            Perfect! Thank you for providing all that information.
            I'll now ask you some technical questions based on your skills and experience level. These questions will help us better understand your expertise in the technologies you mentioned.
            Let's begin with the first question..."""

    def get_technical_question_generation_prompt(self, tech_stack: str, experience_years: int) -> str:
        """Core Conversation Prompt #4: Technical Question Generation"""
        difficulty_level = "junior" if experience_years < 2 else "mid-level" if experience_years < 5 else "senior"
        return f"""\
            CONTEXT: Generate technical interview questions for a candidate with {experience_years} years of experience ({difficulty_level} level) who listed these technologies: {tech_stack}

            INSTRUCTIONS:
            - Generate exactly 3-5 relevant technical questions
            - Match difficulty to experience level: {difficulty_level}
            - Cover different technologies from their stack
            - Mix theoretical knowledge and practical application
            - Questions should be clear and specific
            - Avoid yes/no questions
            - Each question should assess real understanding

            OUTPUT FORMAT: Return ONLY a JSON array of question strings, nothing else.

            EXAMPLE:
            [
            "Explain the difference between SQL and NoSQL databases and when you would choose each.",
            "How would you handle authentication in a React application?",
            "What are the key principles of RESTful API design?"
            ]"""

    def get_end_conversation_prompt(self) -> str:
        """Core Conversation Prompt #5: End Conversation"""
        return """\
            CONTEXT: The technical assessment is complete. All questions have been answered. Time to conclude the conversation professionally.

            INSTRUCTIONS:
            - Thank the candidate for their time and responses
            - Explain what happens next in the process
            - Provide timeline expectations
            - End on a positive, professional note
            - Include contact information for questions

            OUTPUT FORMAT: A concluding message with next steps.

            EXAMPLE:
            Thank you for completing our initial screening!
            I've collected all your information and technical responses. Our hiring team will review your profile and get back to you within 2-3 business days with next steps.
            If you have any questions in the meantime, feel free to contact us directly. Have a great day!"""

    def get_acknowledgement_prompt(self, user_response: str, field_name: str = "") -> str:
        """Situational Prompt #6: Acknowledgement"""
        return f"""\
            CONTEXT: The candidate just provided: "{user_response}" for {field_name}. You need to acknowledge their response before moving to the next question.

            INSTRUCTIONS:
            - Provide a brief, natural acknowledgement
            - Keep it conversational and positive
            - Don't repeat their information back
            - Make it feel human-like

            OUTPUT FORMAT: A brief acknowledgement phrase.

            EXAMPLE: Got it, thank you."""

    def get_fallback_prompt(self, user_input: str, current_context: str) -> str:
        """Situational Prompt #7: Fallback for unclear input"""
        return f"""\
            CONTEXT: The candidate provided unclear input: "{user_input}" when we were trying to {current_context}. You need to redirect them back on track.

            INSTRUCTIONS:
            - Politely indicate you didn't understand
            - Clarify what information you need
            - Rephrase the original question
            - Be helpful, not judgmental
            - Keep it brief

            OUTPUT FORMAT: A clarification message with the repeated question.

            EXAMPLE: I'm sorry, I didn't quite understand. Could we go back to the question about...?"""

    def get_graceful_exit_prompt(self) -> str:
        """Situational Prompt #8: Graceful Exit"""
        return """\
            CONTEXT: The candidate has indicated they want to end the conversation by using an exit keyword.

            INSTRUCTIONS:
            - Thank them for their time
            - Mention that information will be saved if any was collected
            - Provide a positive closing
            - Keep it brief and professional

            OUTPUT FORMAT: A polite goodbye message.

            EXAMPLE: Thank you for your time! Your information has been saved and our team will be in touch. Goodbye!"""

    def get_validation_error_prompt(self, field_name: str) -> str:
        """Handle validation errors for specific fields"""
        error_messages = {
            "email": "Please provide a valid email address format (e.g., name@domain.com).",
            "phone_number": "Please provide a valid phone number.",
            "experience_years": "Please enter a valid number of years (0-50)."
        }

        return f"""\
            CONTEXT: The candidate provided invalid {field_name}. You need to ask them to correct it.

            INSTRUCTIONS:
            - Politely explain the issue
            - Ask for the correct format
            - Be helpful and specific about what's needed

            OUTPUT FORMAT: An error message with format guidance.

            EXAMPLE: {error_messages.get(field_name, f"Please provide valid {field_name} information.")}"""
