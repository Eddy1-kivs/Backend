import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load API key from environment
API_KEY = os.getenv('AISTUDIO_API_KEY')

def generate_topic(skill, subject):
    prompt = f"Generate a test topic that involves {skill} in the context of {subject} and also include a well paraphrased question"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={API_KEY}"

    # JSON data to be sent in the request body
    data = {
        'contents': [
            {
                'parts': [
                    {
                        'text': prompt
                    }
                ]
            }
        ]
    }

    # Send the request with JSON data
    response = requests.post(url, json=data)

    # Check if the request was successful
    if response.status_code == 200:
        # Access the generated content from the first candidate topic
        candidate = response.json()['candidates'][0]
        content = candidate['content']
        parts = content['parts']
        generated_text = parts[0]['text']
        return generated_text
    else:
        # Handle error
        print("Error:", response.text)
        return None
