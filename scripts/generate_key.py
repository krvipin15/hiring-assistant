#!/usr/bin/env python3
"""
Generate a random, unique encryption key and optionally write it to .env file.

- Uses 32 random bytes encoded with URL-safe base64 (Fernet-compatible).
- By default, prints the key to stdout.
- With --write, inserts or updates ENCRYPTION_KEY in .env (creates the file if missing).
- Respects existing keys unless --force is provided.

Usage:
  python3 scripts/generate_key.py                  # print key only
  python3 scripts/generate_key.py --write          # write/update .env safely
  python3 scripts/generate_key.py --write --force  # overwrite if exists
"""

import os
import re
import base64
import secrets
import argparse
from pathlib import Path

# Environment variable and file configuration
ENV_VAR_NAME = "ENCRYPTION_KEY"
ENV_FILE = Path(".env")

def generate_key() -> str:
    """Generate a random encryption key."""
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii")

def read_env(path: Path) -> str:
    """Read the .env file and return its content."""
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")

def write_env(path: Path, content: str) -> None:
    """Write content to the .env file."""
    path.write_text(content, encoding="utf-8")
    return None

def insert_env_var(content: str, key: str, value: str) -> str:
    """Insert or update an environment variable in the .env content."""
    pattern = re.compile(rf"^(?:\s*export\s+)?{re.escape(key)}=.*$", re.MULTILINE)
    line = f"{key}={value}"
    if pattern.search(content):
        return pattern.sub(line, content, count=1)
    # Ensure single trailing newline and append
    if content and not content.endswith("\n"):
        content += "\n"
    return content + line + "\n"

def main() -> None:
    """Main entry point for the script."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Generate and manage encryption key")
    parser.add_argument("--write", action="store_true", help="Write/update key in .env")
    parser.add_argument("--force", action="store_true", help="Overwrite existing key in .env")
    args = parser.parse_args()

    # Generate a new encryption key
    key = generate_key()
    print(key)

    if not args.write:
        return

    # Read the existing .env content
    env_content = read_env(ENV_FILE)

    # If key exists and not forcing, do nothing to avoid accidental rotation
    existing_match = re.search(rf"^(?:\s*export\s+)?{re.escape(ENV_VAR_NAME)}=(.+)$", env_content, re.MULTILINE)
    if existing_match and not args.force:
        print(f"{ENV_VAR_NAME} already present in {ENV_FILE}. Use --force to overwrite.")
        return

    # Insert the new key into the .env content
    new_content = insert_env_var(env_content, ENV_VAR_NAME, key)

    # If OPENAI_API_KEY / DATABASE_URL placeholders are missing, keep users productive by hinting
    # but do not auto-insert credentials.
    if "OPENAI_API_KEY=" not in new_content:
        new_content += "OPENAI_API_KEY=\n"
    if "DATABASE_URL=" not in new_content:
        new_content += "DATABASE_URL=sqlite:///candidates.db\n"

    # Ensure file permissions are restrictive on POSIX systems (Linux), ignored for Windows
    if not ENV_FILE.exists():
        os.umask(0)
        with open(ENV_FILE, "w", encoding="utf-8") as f:
            f.write(new_content)
        try:
            os.chmod(ENV_FILE, 0o600)
        except Exception:
            pass
    else:
        write_env(ENV_FILE, new_content)

    print(f"Wrote {ENV_VAR_NAME} to {ENV_FILE}{' (overwritten)' if existing_match else ''}.")

if __name__ == "__main__":
    main()
