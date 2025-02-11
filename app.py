from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from chatbot import get_ai_response, get_crypto_data, get_trending_cryptos, fetch_coin_info_from_web
import threading
import time
import os
from dotenv import load_dotenv

# ✅ Load Environment Variables
load_dotenv()

# ✅ API Keys (If required for other services like OpenAI)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ✅ Flask App Setup
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/main')
def main():
    return render_template('main.html')

@app.route('/')
def index():
    return render_template('index.html')

# Function to scrape live updates about a coin from the web
def fetch_coin_info_from_web(crypto_name):
    try:
        # General search for the coin's latest news and trends
        search_url = f"https://www.google.com/search?q={crypto_name}+crypto+latest+news"
        response = requests.get(search_url, headers={'User-Agent': 'Mozilla/5.0'})
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Scrape the latest news or relevant articles
            articles = soup.find_all('div', class_='BVG0Nb')  # Class for news snippet in Google Search
            latest_news = ""
            
            for article in articles[:3]:  # Limit to top 3 latest news articles
                title = article.get_text()
                link = article.find('a')['href']
                latest_news += f"📰 {title}\nRead more: {link}\n\n"

            if latest_news:
                return f"📚 **Latest Updates on {crypto_name.upper()}**:\n{latest_news}"
            else:
                return f"❌ Unable to fetch latest updates from the web for {crypto_name.upper()}."
        else:
            return f"❌ Unable to access Google News for {crypto_name.upper()}. Try again later."
    except Exception as e:
        print(f"Error fetching coin info from the web: {e}")
        return "❌ Error retrieving coin information."

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    # ✅ Debugging
    print(f"🟢 Received Message: {user_message}")

    # ✅ Handling Crypto Price Queries
    if "price of" in user_message.lower():
        asset = user_message.lower().split("price of")[-1].strip()

        # Try to fetch live data from CoinGecko first
        crypto_data = get_crypto_data(asset)
        
        # If data is available, send it; otherwise, fall back to CoinDesk scraping
        if crypto_data:
            return jsonify({"response": f"📈 **{asset.upper()} Price:** ${crypto_data['price']}\n"
                                        f"💰 **Market Cap:** ${crypto_data['market_cap']}\n"
                                        f"🔄 **24h Volume:** ${crypto_data['24h_volume']}\n"
                                        f"📊 **24h Change:** {crypto_data['24h_change']}%"})
        else:
            # Fallback: Search the web for coin details if live data isn't available
            coin_info = fetch_coin_info_from_web(asset)
            return jsonify({"response": coin_info})

    # ✅ Fetching Trending Cryptos
    if any(keyword in user_message.lower() for keyword in ["trending cryptos", "top cryptos", "most sold cryptos"]):
        trending_coins = get_trending_cryptos()
        return jsonify({"response": f"🔥 **Trending Cryptos Today:** {', '.join(trending_coins)}"})

    # ✅ Handling follow-up questions and more detailed responses
    ai_prompt = f"""
    You are an AI financial assistant with expertise in cryptocurrency markets.
    
    **User Query:** {user_message}

    **Guidelines for Response:**
    - If they ask about prices, fetch from live market data or web scraping if necessary.
    - If they ask about trending cryptos, list the most popular ones from CoinGecko.
    - If they ask for portfolio suggestions, offer general advice based on market trends.
    - If they ask for trading strategies, provide neutral and educational guidance.
    - Always keep the conversation informative and educational.
    """
    ai_response = get_ai_response(ai_prompt)

    print(f"🤖 Bot Response: {ai_response}")  # ✅ Debugging
    return jsonify({"response": ai_response})

# ✅ Live Price Updates - Fetch Every 10 Seconds
def live_price_updates():
    while True:
        # Fetch real-time prices of top cryptocurrencies (Bitcoin and Ethereum for example)
        btc_data = get_crypto_data("bitcoin")
        eth_data = get_crypto_data("ethereum")

        socketio.emit("price_update", {
            "bitcoin": btc_data,
            "ethereum": eth_data
        })

        time.sleep(10)

if __name__ == '__main__':
    threading.Thread(target=live_price_updates, daemon=True).start()
    socketio.run(app, debug=True)
