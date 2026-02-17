import openai
import os
from dotenv import load_dotenv

load_dotenv()

# Expect the API key to be stored in the .env file as OPENAI_API_KEY
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY not found in environment. Add it to your .env file.")

client = openai.OpenAI(api_key=api_key)

def generate_blog(paragraph_topic):
    try:
        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Write a paragraph about the following topic: {paragraph_topic}"}
            ],
            max_tokens=400,
            temperature=0.3
        )
        
        retrieve_blog=response.choices[0].message.content.strip()
        return retrieve_blog

    except openai.OpenAIError as e:
        return f"Error: {e}"

if __name__ == "__main__":
    print(generate_blog('Why NYC is better than your city.'))

