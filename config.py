import os
import openai
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()

# ✅ Set OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

# ✅ Validate API Key
if not openai.api_key:
    raise ValueError("❌ Error: Missing OpenAI API Key! Please check your .env file.")

# ✅ System prompt for bot behavior
SYSTEM_PROMPT = (
    "You are AIQ, a confident, expert assistant in cryptocurrency markets.\n"
    "You provide clear, concise, data-driven analysis.\n"
    "When applicable, incorporate real-time search data (prefixed with 🔍) and expand with professional insight.\n"
    "Avoid vague disclaimers, do not include asterisks, and avoid repeating user input.\n"
    "Respond with formatting: headlines, bullet points, and short paragraphs when helpful."
)

# ✅ AI Response Function with Dynamic Data Handling
def get_ai_response(user_message, chat_history=[], coin_data=None):
    try:
        # Optional crypto data handling
        if coin_data:
            user_message = (
                f"User is requesting insights based on live market data:\n"
                f"- Price: {coin_data.get('price', 'N/A')}\n"
                f"- Market Cap: {coin_data.get('market_cap', 'N/A')}\n"
                f"- 24h Volume: {coin_data.get('24h_volume', 'N/A')}\n"
                f"- 24h Change: {coin_data.get('24h_change', 'N/A')}\n\n"
                f"Query: {user_message}"
            )

        chat_history.append({"role": "user", "content": user_message})

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + chat_history
        )

        ai_response = response.choices[0].message.content.strip()
        chat_history.append({"role": "assistant", "content": ai_response})
        return ai_response, chat_history

    except openai.OpenAIError as e:
        return f"❌ OpenAI API Error: {str(e)}", chat_history
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}", chat_history
