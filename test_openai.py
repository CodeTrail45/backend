import os
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

response = openai.ChatCompletion.create(
    model="gpt-4",  # Use the chat model you want, e.g., gpt-3.5-turbo or gpt-4
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, AI! what is 2+2"}
    ]
)

# Print the response
print(response['choices'][0]['message']['content'].strip())
