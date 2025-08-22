import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet, InvalidToken

# Load environment variables
load_dotenv()

# Class for managing encryption and decryption
class EncryptionManager:
    def __init__(self) -> None:
        key = os.getenv("ENCRYPTION_KEY")
        if not key:
            raise ValueError("ENCRYPTION_KEY not found in environment variables")

        try:
            self.cipher_suite = Fernet(key.encode())
        except Exception as e:
            raise ValueError("Invalid ENCRYPTION_KEY format. Must be a 32-byte base64 URL-safe string.") from e

    def encrypt(self, text: str | None) -> str:
        """Encrypt text and return base64 encoded string."""
        if not text:
            return ""

        encrypted_text = self.cipher_suite.encrypt(text.encode())
        return encrypted_text.decode()

    def decrypt(self, encrypted_text: str | None) -> str:
        """Decrypt base64 encoded string and return original text."""
        if not encrypted_text:
            return ""

        try:
            decrypted_text = self.cipher_suite.decrypt(encrypted_text.encode())
            return decrypted_text.decode()
        except InvalidToken:
            raise ValueError("Invalid or corrupted encrypted text. Decryption failed.")

# Example usage
if __name__ == "__main__":
    manager = EncryptionManager()
    original_text = "Hello, World!"
    encrypted = manager.encrypt(original_text)
    decrypted = manager.decrypt(encrypted)

    print(f"Original: {original_text}")
    print(f"Encrypted: {encrypted}")
    print(f"Decrypted: {decrypted}")
