"""
Sanity check that the Gemini API key works and Gemini responds.
Not part of the pipeline — just a hello-world.
"""
import os
from dotenv import load_dotenv
from google import genai

# Load environment variables from .env file
load_dotenv()

# Initialize the client — it reads GEMINI_API_KEY from environment
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# Send a tiny test message
response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents="Say 'hello from Gemini' in exactly five words."
)

# Print Gemini's response
print("Gemini replied:")
print(response.text)
print()
print(f"Tokens used: {response.usage_metadata.prompt_token_count} input, "
      f"{response.usage_metadata.candidates_token_count} output")