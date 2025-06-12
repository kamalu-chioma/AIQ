from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from dotenv import load_dotenv
import os
import requests
import threading
import time
import openai
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ✅ Load environment variables
load_dotenv()
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
openai.api_key = os.getenv("OPENAI_API_KEY")

# ✅ Flask App Setup
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/main')
def main():
    return render_template('main.html')

# ✅ Function to fetch real-time crypto price from CoinGecko
def get_crypto_data(crypto_name):
    try:
        url = f"{COINGECKO_API_URL}/simple/price"
        params = {
            "ids": crypto_name.lower(),
            "vs_currencies": "usd",
            "include_market_cap": "true",
            "include_24hr_vol": "true",
            "include_24hr_change": "true"
        }
        response = requests.get(url, params=params)
        data = response.json()

        if crypto_name.lower() in data:
            crypto_data = data[crypto_name.lower()]
            return {
                "price": f"${crypto_data['usd']:,.2f}",
                "market_cap": f"${crypto_data['usd_market_cap']:,.2f}",
                "24h_volume": f"${crypto_data['usd_24h_vol']:,.2f}",
                "24h_change": f"{crypto_data['usd_24h_change']:.2f}%"
            }
        else:
            print(f"CoinGecko failed for {crypto_name}, falling back to Google Search.")
            return fetch_coin_info_from_web(crypto_name)

    except Exception as e:
        print(f"❌ Error fetching data from CoinGecko: {e}")
        return fetch_coin_info_from_web(crypto_name)

# ✅ Function to scrape Google Search for crypto price (Fallback)
def fetch_coin_info_from_web(coin_name):
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        search_url = f"https://www.google.com/search?q={coin_name}+price+in+usd"
        driver.get(search_url)

        time.sleep(2)  # Allow time for page to load

        try:
            price_element = driver.find_element(By.XPATH, "//div[@class='BNeawe iBp4i AP7Wnd']")
            price = price_element.text
        except Exception as e:
            print(f"❌ Error finding price element: {e}")
            price = "Price not found"

        driver.quit()

        return {
            "price": price,
            "source": "Google Search"
        }

    except Exception as e:
        print(f"❌ Error scraping data from Google: {e}")
        return None

# ✅ Function to fetch trending cryptos from CoinGecko
def get_trending_cryptos():
    try:
        url = f"{COINGECKO_API_URL}/search/trending"
        response = requests.get(url)
        data = response.json()

        trending_coins = [coin["item"]["name"] for coin in data["coins"]]
        return trending_coins
    except Exception as e:
        print(f"❌ Error fetching trending coins: {e}")
        return []

# ✅ AI-Powered Crypto Chat Response
def get_ai_response(user_message, coin_data=None):
    try:
        if coin_data:
            ai_prompt = f"""
            You are an expert cryptocurrency assistant. You provide **real-time and insightful** market updates.
            
            **Today's Crypto Update:**
            - **Price:** {coin_data['price']}
            - **Market Cap:** {coin_data.get('market_cap', 'N/A')}
            - **24h Volume:** {coin_data.get('24h_volume', 'N/A')}
            - **24h Change:** {coin_data.get('24h_change', 'N/A')}

            **User Query:** {user_message}

            **Guidelines:**
            - **Provide direct and clear responses.**
            - **Never say "I can't fetch real-time data"**; always use the latest available information.
            - **Be confident and authoritative** in responses.
            """
        else:
            ai_prompt = f"""
            You are a cryptocurrency expert. Provide professional insights based on the latest data.

            **User Query:** {user_message}
            """

        
        chat_history = request.json.get("history", [])  # Retrieve past messages from request
        chat_history.append({"role": "user", "content": user_message})  # Append new message
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert in cryptocurrency markets."}
            ] + chat_history  # Include full chat history
        )


        # response = openai.chat.completions.create(
        #     model="gpt-3.5-turbo",
        #     messages=[
        #         {"role": "system", "content": "You are an expert in cryptocurrency markets."},
        #         {"role": "user", "content": ai_prompt}
        #     ]
        # )

        return response.choices[0].message.content.strip()

    except openai.OpenAIError as e:
        return f"❌ OpenAI API Error: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

# ✅ Chat Route for AI-Powered Crypto Responses
@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    print(f"🟢 Received Message: {user_message}")

    if "price of" in user_message.lower():
        asset = user_message.lower().split("price of")[-1].strip()
        crypto_data = get_crypto_data(asset)

        if crypto_data:
            return jsonify({"response": f"📈 **{asset.upper()} Price:** {crypto_data['price']}\n"
                                        f"💰 **Market Cap:** {crypto_data.get('market_cap', 'N/A')}\n"
                                        f"🔄 **24h Volume:** {crypto_data.get('24h_volume', 'N/A')}\n"
                                        f"📊 **24h Change:** {crypto_data.get('24h_change', 'N/A')}"})


    if any(keyword in user_message.lower() for keyword in ["trending cryptos", "top cryptos", "most sold cryptos"]):
        trending_coins = get_trending_cryptos()
        return jsonify({"response": f"🔥 **Trending Cryptos Today:** {', '.join(trending_coins)}"})

    # ✅ Web search: explicit or smart trigger
    search_keywords = ["latest", "news", "update", "regulation", "happening", "event", "report", "headline"]
    if user_message.lower().startswith("search ") or any(k in user_message.lower() for k in search_keywords):
        from chatbot import search_google
        query = user_message.replace("search", "").strip()
        return jsonify({"response": search_google(query)})

        # Forecast and price prediction queries
    if any(phrase in user_lower for phrase in [
        "predict price of",
        "price forecast for",
        "expected price of",
        "future price of",
        "price prediction for",
        "where is", "headed",
        "is", "going up", "going down"
    ]):
        forecast_keywords = ["predict price of", "price forecast for", "expected price of",
                             "future price of", "price prediction for"]
        query = user_message
        for keyword in forecast_keywords:
            if keyword in user_lower:
                query = user_message.lower().replace(keyword, "").strip() + " crypto price prediction"
                break
        return search_google(query)

    # Explicit "price of" or "what is the price of" query — direct fallback to search
    if user_lower.startswith("price of "):
        query = user_message[9:].strip() + " price today"
        return search_google(query)

    if user_lower.startswith("what is the price of "):
        query = user_message[22:].strip() + " price today"
        return search_google(query)

    if user_lower.startswith("price "):
        query = user_message[6:].strip() + " price today"
        return search_google(query)




    ai_response = get_ai_response(user_message)
    print(f" Bot Response: {ai_response}") 
    return jsonify({"response": ai_response})

# ✅ Real-time Price Updates Every 10 Seconds
def live_price_updates():
    while True:
        btc_data = get_crypto_data("bitcoin")
        eth_data = get_crypto_data("ethereum")

        socketio.emit("price_update", {
            "bitcoin": btc_data,
            "ethereum": eth_data
        })

        time.sleep(10)

# ✅ Start Background Thread for Live Updates
if __name__ == '__main__':
    threading.Thread(target=live_price_updates, daemon=True).start()
    socketio.run(app, debug=True)
