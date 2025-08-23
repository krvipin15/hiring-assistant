#!/usr/bin/env python3
import os
import json
from openai import OpenAI
from typing import Tuple, List, Optional
from chatbot.prompts_manager import PromptsManager
from src.database.database_manager import DatabaseManager
from src.security.encryption_handler import EncryptionManager
from src.utils.data_validator import validate_email, validate_phone, validate_location


class ConversationState:
    GREETING = "greeting"
    COLLECTING_INFO = "collecting_info"
    TECH_TRANSITION = "tech_transition"
    TECHNICAL_QUESTIONS = "technical_questions"
    ENDED = "ended"
    CLOSED = "closed"


class ConversationManager:
    EXIT_KEYWORDS = ["quit", "exit", "bye", "goodbye", "stop", "cancel", "end"]

    def __init__(self):
        # Initialize OpenAI client (keeps your existing OpenRouter pattern)
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )

        self.prompts_manager = PromptsManager()
        self.db_manager = DatabaseManager()
        self.encryption = EncryptionManager()

        # Conversation state
        self.state = ConversationState.GREETING
        self.candidate_data: dict = {}
        self.technical_responses: dict = {}
        self.current_questions: List[str] = []
        self.current_question_index: int = 0

        # Info collection flow
        self.info_fields = [
            "name", "email", "phone_number", "current_location",
            "experience_years", "desired_positions", "tech_stack"
        ]
        self.current_field_index = 0
        self.awaiting_field: Optional[str] = None

    # ---------------------------
    # Public entry: process input
    # ---------------------------
    def process_message(self, user_input: str) -> Tuple[str, bool]:
        """
        Main entry point for incoming user messages.
        Returns (assistant_message, finished_flag)
        finished_flag True means conversation ended (closed) or user exited.
        """
        user_input = (user_input or "").strip()

        # Immediate exit detection (highest precedence)
        if self._is_exit_keyword(user_input):
            return self._handle_graceful_exit()

        # Always check for "reveal answers" or other off-track requests first using fallback prompt
        if self._is_reveal_request(user_input) or self._is_unwanted_behavior(user_input):
            # Provide the fallback refusal/redirect immediately
            fallback = self.prompts_manager.get_fallback_prompt(user_input, "continue our conversation")
            return self._get_ai_response(fallback), False

        # State dispatch
        if self.state == ConversationState.GREETING:
            return self._handle_greeting()

        if self.state == ConversationState.COLLECTING_INFO:
            return self._handle_info_collection(user_input)

        if self.state == ConversationState.TECH_TRANSITION:
            return self._handle_tech_transition()

        if self.state == ConversationState.TECHNICAL_QUESTIONS:
            return self._handle_technical_questions(user_input)

        if self.state == ConversationState.ENDED:
            # Candidate has been told the session is complete and is expected to exit.
            # If they don't send an exit keyword, keep reminding/invite them to exit.
            end_msg = self.prompts_manager.get_end_conversation_prompt()
            return self._get_ai_response(end_msg), False

        # If state UNKNOWN or CLOSED, fallback
        fallback = self.prompts_manager.get_fallback_prompt(user_input, "continue our conversation")
        return self._get_ai_response(fallback), False

    # ---------------------------
    # State handlers
    # ---------------------------
    def _handle_greeting(self) -> Tuple[str, bool]:
        """Send greeting prompt and begin collecting info (ask first field)."""
        self.state = ConversationState.COLLECTING_INFO
        self.current_field_index = 0
        self.awaiting_field = self.info_fields[self.current_field_index]

        greeting_prompt = self.prompts_manager.get_greeting_prompt()
        # The greeting prompt asks for name; return it directly
        return self._get_ai_response(greeting_prompt), False

    def _handle_info_collection(self, user_input: str) -> Tuple[str, bool]:
        """
        Process the user's answer for the current awaiting field.
        Validate using data_validator; on success acknowledge and ask next; on failure send validation error prompt.
        """
        # If for some reason there's no awaiting field, start it
        if not self.awaiting_field:
            self.current_field_index = 0
            self.awaiting_field = self.info_fields[0]

        field = self.awaiting_field

        # Validate and store
        valid = self._validate_and_store_field(field, user_input)
        if valid:
            # Acknowledge
            ack_prompt = self.prompts_manager.get_acknowledgement_prompt(user_input, field)
            ack_msg = self._get_ai_response(ack_prompt)

            # Move to next field
            self.current_field_index += 1
            if self.current_field_index >= len(self.info_fields):
                # All info collected -> transition to technical questions
                self.awaiting_field = None
                self.state = ConversationState.TECH_TRANSITION
                transition_msg = self._get_ai_response(
                    self.prompts_manager.get_transition_prompt(
                        self.candidate_data.get("tech_stack", ""),
                        int(self.candidate_data.get("experience_years", "0"))
                    )
                )
                # We'll generate questions in the transition handler; return transition message now and let handler continue next turn
                return f"{ack_msg}\n\n{transition_msg}", False
            else:
                # Ask next info field
                self.awaiting_field = self.info_fields[self.current_field_index]
                info_prompt_text = self.prompts_manager.get_information_gathering_prompt(self.awaiting_field)
                info_question = self._get_ai_response(info_prompt_text)
                return f"{ack_msg}\n\n{info_question}", False
        else:
            # Validation failed: return validation error prompt
            error_prompt = self.prompts_manager.get_validation_error_prompt(field)
            return self._get_ai_response(error_prompt), False

    def _handle_tech_transition(self) -> Tuple[str, bool]:
        """
        Generate technical questions and begin the Q&A loop.
        """
        tech_stack = self.candidate_data.get("tech_stack", "")
        try:
            questions = self._generate_technical_questions(tech_stack, int(self.candidate_data.get("experience_years", 0)))
        except Exception as e:
            # If generation fails, use fallback: tell user we can't generate questions and end session politely
            fallback = self.prompts_manager.get_fallback_prompt(str(e), "generate technical questions")
            return self._get_ai_response(fallback), False

        if not questions:
            # No questions produced; inform candidate and move to end state
            end_prompt = self.prompts_manager.get_end_conversation_prompt()
            self.state = ConversationState.ENDED
            return self._get_ai_response(end_prompt), False

        # Save questions and start asking one-by-one
        self.current_questions = questions
        self.current_question_index = 0
        self.state = ConversationState.TECHNICAL_QUESTIONS

        # First question is asked immediately (transition prompt already sent previously)
        first_q = self.current_questions[0]
        return first_q, False

    def _handle_technical_questions(self, user_input: str) -> Tuple[str, bool]:
        """
        Store the user's answer to the current question, acknowledge, then ask the next question.
        After the last question, send end-of-session prompt (get_end_conversation_prompt) and set state to ENDED.
        """
        # store answer for current question
        if self.current_question_index < len(self.current_questions):
            question_text = self.current_questions[self.current_question_index]
            self.technical_responses[f"q_{self.current_question_index}"] = {
                "question": question_text,
                "answer": user_input
            }
        else:
            # defensive: no current question — fallback
            fallback = self.prompts_manager.get_fallback_prompt(user_input, "answer the current technical question")
            return self._get_ai_response(fallback), False

        # Acknowledge
        ack_prompt = self.prompts_manager.get_acknowledgement_prompt(user_input, "technical question")
        ack_text = self._get_ai_response(ack_prompt)

        # increment index and either ask next or finish
        self.current_question_index += 1
        if self.current_question_index < len(self.current_questions):
            next_q = self.current_questions[self.current_question_index]
            return f"{ack_text}\n\n{next_q}", False
        else:
            # All QA done => tell the candidate next steps and instruct them to exit when ready
            end_prompt = self.prompts_manager.get_end_conversation_prompt()
            self.state = ConversationState.ENDED
            return self._get_ai_response(end_prompt), False

    def _handle_graceful_exit(self) -> Tuple[str, bool]:
        """
        When the user decides to exit: save data (encrypted + plaintext + JSON) to DB and send graceful exit prompt.
        Returns final message and finished flag True.
        """
        # Save data to DB (encrypt relevant fields)
        try:
            self._save_candidate_data()
        except Exception as e:
            # If save fails, try to notify candidate but still return graceful exit prompt.
            print(f"Error saving candidate data: {e}")

        exit_prompt_text = self.prompts_manager.get_graceful_exit_prompt()
        exit_msg = self._get_ai_response(exit_prompt_text)
        self.state = ConversationState.CLOSED
        return exit_msg, True

    # ---------------------------
    # Utilities: validation & saving
    # ---------------------------
    def _validate_and_store_field(self, field_name: str, value: str) -> bool:
        """Validate using data_validator module and store sanitized value on success."""
        if value is None:
            return False

        value = value.strip()

        if field_name == "email":
            if not validate_email(value):
                return False
        elif field_name == "phone_number":
            if not validate_phone(value):
                return False
        elif field_name == "current_location":
            if not validate_location(value):
                return False
        elif field_name == "experience_years":
            try:
                years = int(value)
                if not (0 <= years <= 50):
                    return False
                value = str(years)
            except ValueError:
                return False
        else:
            if not value:
                return False

        # Map 'name' field to 'full_name' if required by your DB schema - keep same key for now
        self.candidate_data[field_name] = value
        return True

    def _save_candidate_data(self) -> None:
        """
        Save candidate data to the DB using DatabaseManager.save_candidate(candidate_data, technical_responses).
        Also create a local JSONL archive with plaintext + encrypted_blob + encrypted_fields for auditing/backup.
        The DB itself handles field-level encryption for phone/email/location, so we pass plaintext to it to avoid double-encryption.
        """
        if not self.candidate_data and not self.technical_responses:
            return None

        # Assemble plain payload
        payload = {
            "candidate": self.candidate_data,
            "technical_responses": self.technical_responses
        }

        # Convert to JSON string
        try:
            json_payload = json.dumps(payload, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to serialize payload to JSON: {e}")
            json_payload = "{}"

        # Create encrypted_fields map (for our local archive only) but do NOT send these to the DB to avoid double-encryption
        encrypted_fields = {}
        for k, v in self.candidate_data.items():
            try:
                encrypted_fields[k] = self.encryption.encrypt(str(v))
            except Exception as e:
                print(f"Encryption failed for field {k}: {e}")
                encrypted_fields[k] = ""

        # Encrypt full JSON blob (archive-only)
        try:
            encrypted_blob = self.encryption.encrypt(json_payload)
        except Exception as e:
            print(f"Full-payload encryption failed: {e}")
            encrypted_blob = ""

        # Save to the database (DatabaseManager expects (candidate_data, technical_responses))
        try:
            self.db_manager.save_candidate(self.candidate_data, self.technical_responses)
        except Exception as e:
            # Log but don't crash the conversation flow
            print(f"Error saving candidate to DB: {e}")

        # Append an audit/backup record to a local JSONL file (non-sensitive info is plaintext; sensitive fields stored encrypted)
        try:
            from datetime import datetime
            archive_record = {
                "timestamp": datetime.now().isoformat(),
                "plain": payload,
                "encrypted_fields": encrypted_fields,
                "encrypted_blob": encrypted_blob
            }
            archive_path = os.getenv("CANDIDATES_ARCHIVE_PATH", "candidates_archive.jsonl")
            with open(archive_path, "a", encoding="utf-8") as af:
                af.write(json.dumps(archive_record, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Failed to write local archive: {e}")

        return None

    # ---------------------------
    # AI helper / generation
    # ---------------------------
    def _generate_technical_questions(self, tech_stack: str, experience_years: int) -> List[str]:
        """
        Calls the LLM with the generation prompt and expects a JSON array output.
        If parsing fails or output is not a JSON list of strings an Exception is raised.
        """
        question_prompt = self.prompts_manager.get_question_generation_prompt(tech_stack, experience_years)

        completion = self.client.chat.completions.create(
            model="openai/gpt-oss-20b:free",
            messages=[{"role": "user", "content": question_prompt}],
            temperature=0.5,
            max_tokens=400
        )

        response_text = completion.choices[0].message.content.strip() if completion.choices[0].message.content else ""

        # We expect a pure JSON array (per prompt contract)
        try:
            parsed = json.loads(response_text)
            if isinstance(parsed, list) and all(isinstance(x, str) for x in parsed):
                # enforce 3-5 questions per your requirement; if not, raise to trigger fallback
                if 3 <= len(parsed) <= 5:
                    return parsed
                else:
                    raise ValueError("LLM did not return 3-5 questions as required.")
            else:
                raise ValueError("LLM response was not a JSON array of strings.")
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM output as JSON: {e}\nRaw output: {response_text}")

    def _get_ai_response(self, prompt: str) -> str:
        """Small wrapper to call LLM for general prompts (greeting, ack, fallback, etc.)."""
        try:
            completion = self.client.chat.completions.create(
                model="openai/gpt-oss-20b:free",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.25,
                max_tokens=300
            )
            return completion.choices[0].message.content.strip() if completion.choices[0].message.content else ""
        except Exception as e:
            print(f"AI response error: {e}")
            return "I apologize — I'm having trouble responding right now. Please try again."

    # ---------------------------
    # Safety / fallback checks
    # ---------------------------
    def _is_exit_keyword(self, user_input: str) -> bool:
        if not user_input:
            return False
        lower = user_input.lower()
        return any(k in lower for k in self.EXIT_KEYWORDS)

    def _is_reveal_request(self, user_input: str) -> bool:
        """
        Detect explicit requests to reveal answers / solution keys.
        This logic can be extended with regex or a small classifier.
        """
        if not user_input:
            return False
        lower = user_input.lower()
        reveal_terms = ["reveal", "answers", "answer key", "solution", "solutions", "show me the answers", "give me the answer", "cheat", "key"]
        return any(term in lower for term in reveal_terms)

    def _is_unwanted_behavior(self, user_input: str) -> bool:
        """
        Generic detector for obviously unrelated / abusive / unsafe content.
        Extend as needed. For now we simply treat extremely short/empty strings as 'unclear'.
        """
        if not user_input or len(user_input.strip()) == 0:
            return True
        return False
