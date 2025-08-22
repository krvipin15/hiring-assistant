#!/usr/bin/env python3

"""
This module manages the conversation flow for the TalentScout hiring assistant chatbot.
Responsible for handling user inputs, maintaining conversation state, and coordinating with other components.
"""

import os
import json
from openai import OpenAI
from typing import Tuple, List
from prompts_manager import PromptsManager
from src.database.database_manager import DatabaseManager
from src.utils.data_validator import validate_email, validate_phone

class ConversationState:
    GREETING = "greeting"
    COLLECTING_INFO = "collecting_info"
    TECH_TRANSITION = "tech_transition"
    TECHNICAL_QUESTIONS = "technical_questions"
    ENDED = "ended"

class ConversationManager:
    def __init__(self):
        # Initialize OpenAI client with OpenRouter
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )

        self.prompts_manager = PromptsManager()
        self.db_manager = DatabaseManager()

        # Conversation state
        self.state = ConversationState.GREETING
        self.candidate_data = {}
        self.technical_responses = {}
        self.current_questions = []
        self.current_question_index = 0

        # Information collection flow
        self.info_fields = [
            "name", "email", "phone_number", "current_location",
            "experience_years", "desired_positions", "tech_stack"
        ]
        self.current_field_index = 0
        self.awaiting_field = None

    def process_message(self, user_input: str) -> Tuple[str, bool]:
        """Main message processing logic"""

        # Check for exit keywords first
        if self._is_exit_keyword(user_input):
            return self._handle_graceful_exit()

        if self.state == ConversationState.GREETING:
            return self._handle_greeting()

        elif self.state == ConversationState.COLLECTING_INFO:
            return self._handle_info_collection(user_input)

        elif self.state == ConversationState.TECH_TRANSITION:
            return self._handle_tech_transition()

        elif self.state == ConversationState.TECHNICAL_QUESTIONS:
            return self._handle_technical_questions(user_input)

        return self._handle_fallback(user_input, "continue our conversation")

    def _handle_greeting(self) -> Tuple[str, bool]:
        """Handle initial greeting"""
        self.state = ConversationState.COLLECTING_INFO
        self.awaiting_field = self.info_fields[0]  # Start with name
        return self._get_ai_response(self.prompts_manager.get_greeting_prompt()), False

    def _handle_info_collection(self, user_input: str) -> Tuple[str, bool]:
        """Handle information collection phase"""
        if self.awaiting_field:
            # Store the response for current field
            if self._validate_and_store_field(self.awaiting_field, user_input):
                # Move to next field
                self.current_field_index += 1

                if self.current_field_index >= len(self.info_fields):
                    # All info collected, transition to tech questions
                    self.state = ConversationState.TECH_TRANSITION
                    return self._handle_tech_transition()
                else:
                    # Ask for next field
                    self.awaiting_field = self.info_fields[self.current_field_index]

                    # Get acknowledgment + next question
                    ack_prompt = self.prompts_manager.get_acknowledgement_prompt(user_input, self.awaiting_field)
                    ack = self._get_ai_response(ack_prompt)

                    info_prompt = self.prompts_manager.get_information_gathering_prompt(self.awaiting_field)
                    question = self._get_ai_response(info_prompt)

                    return f"{ack}\n\n{question}", False
            else:
                # Validation failed, ask again
                error_prompt = self.prompts_manager.get_validation_error_prompt(self.awaiting_field)
                return self._get_ai_response(error_prompt), False

        return self._handle_fallback(user_input, f"get your {self.awaiting_field}")

    def _handle_tech_transition(self) -> Tuple[str, bool]:
        """Handle transition to technical questions"""
        tech_stack = self.candidate_data.get("tech_stack", "")
        experience_years = int(self.candidate_data.get("experience_years", 0))

        # Generate technical questions
        self.current_questions = self._generate_technical_questions(tech_stack, experience_years)

        if self.current_questions:
            self.state = ConversationState.TECHNICAL_QUESTIONS
            self.current_question_index = 0

            # Get transition message
            transition_prompt = self.prompts_manager.get_transition_prompt(tech_stack, experience_years)
            transition_msg = self._get_ai_response(transition_prompt)

            # Add first question
            first_question = self.current_questions[0]
            return f"{transition_msg}\n\n{first_question}", False
        else:
            # No questions generated, end conversation
            return self._handle_end_conversation()

    def _handle_technical_questions(self, user_input: str) -> Tuple[str, bool]:
        """Handle technical Q&A phase"""
        # Store current answer
        current_question = self.current_questions[self.current_question_index]
        self.technical_responses[f"question_{self.current_question_index}"] = {
            "question": current_question,
            "answer": user_input
        }

        self.current_question_index += 1

        if self.current_question_index < len(self.current_questions):
            # More questions available
            ack_prompt = self.prompts_manager.get_acknowledgement_prompt(user_input, "technical question")
            ack = self._get_ai_response(ack_prompt)

            next_question = self.current_questions[self.current_question_index]
            return f"{ack}\n\n{next_question}", False
        else:
            # All questions answered
            return self._handle_end_conversation()

    def _handle_end_conversation(self) -> Tuple[str, bool]:
        """Handle conversation ending"""
        self._save_candidate_data()
        self.state = ConversationState.ENDED

        end_prompt = self.prompts_manager.get_end_conversation_prompt()
        return self._get_ai_response(end_prompt), True

    def _handle_graceful_exit(self) -> Tuple[str, bool]:
        """Handle user-initiated exit"""
        self._save_candidate_data()

        exit_prompt = self.prompts_manager.get_graceful_exit_prompt()
        return self._get_ai_response(exit_prompt), True

    def _handle_fallback(self, user_input: str, context: str) -> Tuple[str, bool]:
        """Handle unclear or unexpected input"""
        fallback_prompt = self.prompts_manager.get_fallback_prompt(user_input, context)
        return self._get_ai_response(fallback_prompt), False

    def _validate_and_store_field(self, field_name: str, value: str) -> bool:
        """Validate field input and store if valid"""
        value = value.strip()

        if field_name == "email" and not validate_email(value):
            return False
        elif field_name == "phone_number" and not validate_phone(value):
            return False
        elif field_name == "experience_years":
            try:
                years = int(value)
                if not (0 <= years <= 50):
                    return False
                value = str(years)
            except ValueError:
                return False
        elif not value:  # Empty value check for other fields
            return False

        self.candidate_data[field_name] = value
        return True

    def _generate_technical_questions(self, tech_stack: str, experience_years: int) -> List[str]:
        """Generate technical questions using AI"""
        try:
            question_prompt = self.prompts_manager.get_technical_question_generation_prompt(tech_stack, experience_years)

            completion = self.client.chat.completions.create(
                model="openai/gpt-oss-20b:free",
                messages=[{"role": "user", "content": question_prompt}],
                temperature=0.7,
                max_tokens=400
            )

            response_text = completion.choices[0].message.content.strip()

            # Parse JSON response
            try:
                questions = json.loads(response_text)
                return questions if isinstance(questions, list) else []
            except json.JSONDecodeError:
                # Fallback: try to extract questions from text
                lines = [line.strip() for line in response_text.split('\n') if line.strip()]
                questions = []
                for line in lines:
                    # Remove numbering if present
                    if line[0:2] in ['1.', '2.', '3.', '4.', '5.']:
                        questions.append(line[2:].strip())
                    elif line.startswith('"') and line.endswith('"'):
                        questions.append(line[1:-1])
                    elif line:
                        questions.append(line)
                return questions[:5]

        except Exception as e:
            print(f"Error generating questions: {e}")
            return self._get_fallback_questions(experience_years)

    def _get_fallback_questions(self, experience_years: int) -> List[str]:
        """Fallback questions if AI generation fails"""
        if experience_years < 2:
            return [
                "What are the basic principles of object-oriented programming?",
                "Explain the difference between a list and a tuple in Python.",
                "What is version control and why is it important?"
            ]
        elif experience_years < 5:
            return [
                "How would you optimize a slow database query?",
                "Explain the concept of RESTful APIs and their benefits.",
                "What are some common security vulnerabilities in web applications?"
            ]
        else:
            return [
                "How would you design a scalable microservices architecture?",
                "Explain different caching strategies and when to use each.",
                "How would you handle a system that needs to process millions of requests?"
            ]

    def _get_ai_response(self, prompt: str) -> str:
        """Get AI response for a given prompt"""
        try:
            completion = self.client.chat.completions.create(
                model="openai/gpt-oss-20b:free",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error getting AI response: {e}")
            return "I apologize, but I'm having trouble processing that right now. Could you please try again?"

    def _is_exit_keyword(self, user_input: str) -> bool:
        """Check if user input contains exit keywords"""
        exit_keywords = ["quit", "exit", "bye", "goodbye", "stop", "end"]
        return any(keyword in user_input.lower() for keyword in exit_keywords)

    def _save_candidate_data(self):
        """Save candidate data to database"""
        if self.candidate_data:
            self.db_manager.save_candidate(self.candidate_data, self.technical_responses)
