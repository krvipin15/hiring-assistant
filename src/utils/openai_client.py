#!/usr/bin/env python3
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(verbose=True)

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=os.environ.get("OPENAI_API_KEY"),
)

completion = client.chat.completions.create(
  model="openai/gpt-oss-20b:free",
  messages=[
    {
      "role": "user",
      "content": "What is the meaning of life?"
    }
  ]
)
print(completion.choices[0].message.content)
