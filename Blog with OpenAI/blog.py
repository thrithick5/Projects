import openai
import os

client = openai.OpenAI(api_key=os.getenv('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'))

def generate_blog(paragraph_topic):
    try:
        response = client.chat_aompletions.create(
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

