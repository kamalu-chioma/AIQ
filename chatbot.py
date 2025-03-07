import os
import requests
import openai
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ✅ Load environment variables
load_dotenv()
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
openai.api_key = os.getenv("OPENAI_API_KEY")

# ✅ Fetch Crypto Data from CoinGecko API (Primary Source)
def get_crypto_data(crypto_name):
    """
    Fetches real-time cryptocurrency data from CoinGecko API.
    If CoinGecko fails, it falls back to CoinDesk scraping.
    If CoinDesk also fails, it scrapes Google Search.
    """
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
                "24h_change": f"{crypto_data['usd_24h_change']:.2f}%",
                "source": "CoinGecko"
            }
        else:
            print(f"❌ CoinGecko API failed for {crypto_name}. Trying CoinDesk...")
            return fetch_coin_info_from_web(crypto_name)

    except Exception as e:
        print(f"❌ CoinGecko API Error: {e}")
        return fetch_coin_info_from_web(crypto_name)

# ✅ Scrape CoinDesk for Crypto Price (First Fallback)
def fetch_coin_info_from_web(coin_name):
    """
    Uses Selenium to scrape CoinDesk for cryptocurrency price when CoinGecko API fails.
    If CoinDesk also fails, it falls back to Google Search.
    """
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        url = f"https://www.coindesk.com/price/{coin_name.lower()}"
        driver.get(url)

        time.sleep(3)  # Allow time for the page to load

        try:
            price_element = driver.find_element(By.XPATH, '//div[contains(@class, "price-large")]')
            price = price_element.text
        except Exception as e:
            print(f"❌ Error finding price element on CoinDesk: {e}")
            price = None

        driver.quit()

        if price:
            return {
                "price": price,
                "source": "CoinDesk"
            }
        else:
            print(f"❌ CoinDesk failed for {coin_name}. Trying Google Search...")
            return fetch_price_from_google(coin_name)

    except Exception as e:
        print(f"❌ CoinDesk Scraping Error: {e}")
        return fetch_price_from_google(coin_name)

# ✅ Scrape Google Search for Crypto Price (Final Fallback)
def fetch_price_from_google(coin_name):
    """
    Uses Selenium to scrape Google Search for cryptocurrency price when both CoinGecko and CoinDesk fail.
    """
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        search_url = f"https://www.google.com/search?q={coin_name}+price+in+usd"
        driver.get(search_url)

        time.sleep(3)  # Allow time for the page to load

        try:
            price_element = driver.find_element(By.XPATH, "//div[@class='BNeawe iBp4i AP7Wnd']")
            price = price_element.text
        except Exception as e:
            print(f"❌ Error finding price element on Google Search: {e}")
            price = "Price not found"

        driver.quit()

        return {
            "price": price,
            "source": "Google Search"
        }

    except Exception as e:
        print(f"❌ Google Scraping Error: {e}")
        return None

# ✅ Fetch Trending Cryptos from CoinGecko
def get_trending_cryptos():
    """
    Fetches a list of trending cryptocurrencies from CoinGecko.
    """
    try:
        url = f"{COINGECKO_API_URL}/search/trending"
        response = requests.get(url)
        data = response.json()

        trending_coins = [coin["item"]["name"] for coin in data["coins"]]
        return trending_coins
    except Exception as e:
        print(f"❌ Error fetching trending cryptos: {e}")
        return []

# ✅ AI-Powered Crypto Response Generator
def get_ai_response(user_message, chat_history=[]):
    """
    Generates an AI-driven response based on the user's query.
    If real-time data is available, it is included in the response.
    """
    try:
        chat_history.append({"role": "user", "content": user_message})  # Append latest message

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

# ✅ Main Function to Handle Chatbot Queries
def handle_chat_query(user_message):
    """
    Handles chatbot queries by determining if it's a price query, 
    a trending crypto request, or an AI-based response.
    """
    if "history" not in globals():
        global history
        history = []  # Initialize history if not already set

    if "price of" in user_message.lower():
        asset = user_message.lower().split("price of")[-1].strip()
        crypto_data = get_crypto_data(asset)

        if crypto_data:
            return f"📈 **{asset.upper()} Price (Source: {crypto_data['source']}):** {crypto_data['price']}\n" \
                   f"💰 **Market Cap:** {crypto_data.get('market_cap', 'N/A')}\n" \
                   f"🔄 **24h Volume:** {crypto_data.get('24h_volume', 'N/A')}\n" \
                   f"📊 **24h Change:** {crypto_data.get('24h_change', 'N/A')}"

    if any(keyword in user_message.lower() for keyword in ["trending cryptos", "top cryptos", "most sold cryptos"]):
        trending_coins = get_trending_cryptos()
        return f"🔥 **Trending Cryptos Today:** {', '.join(trending_coins)}"

    ai_response, history = get_ai_response(user_message, history)
    return ai_response
