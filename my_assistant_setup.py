import os
import openai

assistant_id = 'your-assistant-id'

client = openai.Client(api_key=os.getenv('OPENAI_API_KEY'))