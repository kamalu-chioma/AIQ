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

# ✅ AI Response Function with Dynamic Data Handling
def get_ai_response(user_message, chat_history=[], coin_data=None):
    """
    Generates AI response using OpenAI's latest API syntax.
    If real-time coin data is available, it will be included in the AI prompt.
    """
    try:
        if coin_data:
            ai_prompt = f"""
            You are a cryptocurrency expert providing **real-time insights**.

            **Crypto Update (Source: {coin_data.get('source', 'Unknown')}):**
            - **Price:** {coin_data.get('price', 'N/A')}
            - **Market Cap:** {coin_data.get('market_cap', 'N/A')}
            - **24h Volume:** {coin_data.get('24h_volume', 'N/A')}
            - **24h Change:** {coin_data.get('24h_change', 'N/A')}

            **User Query:** {user_message}

            **Guidelines:**
            - Provide **clear, confident, and actionable** responses.
            - Always **use real-time data** when available.
            - Never say "I can't fetch live data"; always provide the most recent available information.
            """
        else:
            ai_prompt = f"""
            You are an expert cryptocurrency assistant. Provide professional insights based on the latest data.

            **User Query:** {user_message}
            """

        chat_history.append({"role": "user", "content": user_message})  # Append latest user message

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert in cryptocurrency markets."}
            ] + chat_history  # Include full conversation history
        )

        ai_response = response.choices[0].message.content.strip()
        chat_history.append({"role": "assistant", "content": ai_response})  # Append AI response

        return ai_response, chat_history  # Return AI response and updated history

    except openai.OpenAIError as e:
        return f"❌ OpenAI API Error: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"
