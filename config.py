import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_ai_response(user_message):
    """
    Generates AI response using the latest OpenAI API syntax.
    """
    if not openai.api_key:
        return "❌ Error: Missing OpenAI API Key!"

    try:
        response = openai.chat.completions.create(  # ✅ Correct API Syntax
            model="gpt-3.5-turbo",  # Or use ""
            messages=[
                {"role": "system", "content": "You are a helpful AI chatbot answering only questions related to crypto and trading cryptos, use the coingekco api or realtime check https://www.coingecko.com/ to fetch real time data and help users as much as you can."},
                {"role": "user", "content": user_message}
            ]
        )

        return response.choices[0].message.content.strip()

    except openai.OpenAIError as e:
        return f"❌ OpenAI API Error: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"
