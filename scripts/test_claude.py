"""
Quick sanity check that the Anthropic API key works and Claude responds.
Not part of the pipeline — just a hello-world.
"""
import os
from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables from .env file
load_dotenv()

# Initialize the client — it reads ANTHROPIC_API_KEY from environment
client = Anthropic()

# Send a tiny test message
response = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=100,
    messages=[
        {"role": "user", "content": "Say 'hello from Claude' in exactly five words."}
    ]
)

# Print Claude's response
print("Claude replied:")
print(response.content[0].text)
print()
print(f"Tokens used: {response.usage.input_tokens} input, {response.usage.output_tokens} output")