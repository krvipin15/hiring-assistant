#!/usr/bin/env python3

"""
Database module that handles candidate data storage and retrieval.
It uses SQLite for data storage and includes encryption for sensitive fields.
"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional
from src.security.encryption_handler import EncryptionManager


class DatabaseManager:
    def __init__(self, db_path: str = "candidates.db") -> None:
        self.db_path = db_path
        self.encryption_manager = EncryptionManager()
        self._create_table()

    def _create_table(self) -> None:
        """Create candidates table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date_time TEXT NOT NULL,
                    name TEXT NOT NULL,
                    phone_number TEXT NOT NULL,
                    email TEXT NOT NULL,
                    current_location TEXT NOT NULL,
                    experience_years INTEGER NOT NULL,
                    desired_positions TEXT NOT NULL,
                    tech_stack TEXT NOT NULL,
                    technical_responses_json TEXT NOT NULL
                )
            ''')
            conn.commit()
            return None

    def save_candidate(self, candidate_data: Dict[str, Any], technical_responses: Dict[str, Any]) -> None:
        """Save candidate data to database with encryption for sensitive fields."""
        try:
            encrypted_phone = self.encryption_manager.encrypt(candidate_data.get("phone_number", ""))
            encrypted_email = self.encryption_manager.encrypt(candidate_data.get("email", ""))
            encrypted_location = self.encryption_manager.encrypt(candidate_data.get("current_location", ""))

            data = (
                datetime.now().isoformat(),
                candidate_data.get("name", ""),
                encrypted_phone,
                encrypted_email,
                encrypted_location,
                int(candidate_data.get("experience_years", 0)),
                candidate_data.get("desired_positions", ""),
                candidate_data.get("tech_stack", ""),
                json.dumps(technical_responses)
            )

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO candidates
                    (date_time, name, phone_number, email, current_location, experience_years,
                     desired_positions, tech_stack, technical_responses_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', data)
                conn.commit()
                return None

        except Exception as e:
            raise RuntimeError(f"Error saving candidate: {e}") from e

    def get_candidate(self, candidate_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve and decrypt candidate data by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM candidates WHERE id = ?', (candidate_id,))
                row = cursor.fetchone()

            if row:
                return {
                    "id": row[0],
                    "date_time": row[1],
                    "name": row[2],
                    "phone_number": self.encryption_manager.decrypt(row[3]),
                    "email": self.encryption_manager.decrypt(row[4]),
                    "current_location": self.encryption_manager.decrypt(row[5]),
                    "experience_years": row[6],
                    "desired_positions": row[7],
                    "tech_stack": row[8],
                    "technical_responses": json.loads(row[9])
                }
            return None

        except Exception as e:
            raise RuntimeError(f"Error retrieving candidate {candidate_id}: {e}") from e


# Example usage
if __name__ == "__main__":
    # Initialize the database manager
    db_manager = DatabaseManager()

    # Create the candidates table
    db_manager._create_table()

    # Candidate information
    candidate_info = {
        "name": "John Doe",
        "phone_number": "+1234567890",
        "email": "john.doe@example.com",
        "current_location": "New York",
        "experience_years": 5,
        "desired_positions": "Senior Developer",
        "tech_stack": "Python, Django, React"
    }

    # Technical responses from the candidate
    technical_responses = {
        "coding_challenge": "Completed",
        "system_design": "In Progress"
    }

    # Save the candidate information
    db_manager.save_candidate(candidate_info, technical_responses)
