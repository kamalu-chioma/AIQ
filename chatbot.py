import os
import requests
import openai
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# ✅ Load environment variables
load_dotenv()
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
openai.api_key = os.getenv("OPENAI_API_KEY")

# ✅ Fetch Crypto Data from CoinGecko API (Primary Source)
def get_crypto_data(crypto_name):
    """
    Fetches real-time cryptocurrency data from CoinGecko API.
    Falls back to CoinDesk web scraping if CoinGecko fails.
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
                "24h_change": f"{crypto_data['usd_24h_change']:.2f}%"
            }
        else:
            print(f"CoinGecko failed for {crypto_name}. Falling back to CoinDesk.")
            return fetch_coin_info_from_web(crypto_name)

    except Exception as e:
        print(f"❌ CoinGecko API Error: {e}")
        return fetch_coin_info_from_web(crypto_name)

# ✅ Scrape CoinDesk for Crypto Price (Fallback)
def fetch_coin_info_from_web(coin_name):
    """
    Uses Selenium to scrape CoinDesk for cryptocurrency price when CoinGecko API fails.
    """
    try:
        # Configure Selenium WebDriver (Headless Mode)
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        # CoinDesk Price URL
        url = f"https://www.coindesk.com/price/{coin_name.lower()}"
        driver.get(url)

        time.sleep(3)  # Allow time for page to load

        try:
            price_element = driver.find_element(By.XPATH, '//div[contains(@class, "price-large")]')
            price = price_element.text
        except Exception as e:
            print(f"❌ Error finding price element on CoinDesk: {e}")
            price = "Price not found"

        driver.quit()

        return {
            "price": price,
            "source": "CoinDesk"
        }

    except Exception as e:
        print(f"❌ CoinDesk Scraping Error: {e}")
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
def get_ai_response(user_message, coin_data=None):
    """
    Generates an AI-driven response based on the user's query.
    If real-time data is available, it is included in the response.
    """
    try:
        if coin_data:
            ai_prompt = f"""
            You are a cryptocurrency expert providing **real-time insights**.

            **Crypto Update:**
            - **Price:** {coin_data['price']}
            - **Market Cap:** {coin_data.get('market_cap', 'N/A')}
            - **24h Volume:** {coin_data.get('24h_volume', 'N/A')}
            - **24h Change:** {coin_data.get('24h_change', 'N/A')}

            **User Query:** {user_message}

            **Guidelines:**
            - Provide **clear, confident, and actionable** responses.
            - Always **use real-time data** when available.
            - Avoid saying "I cannot fetch live data"; always provide the most recent available information.
            """
        else:
            ai_prompt = f"""
            You are an expert crypto assistant. Provide professional insights based on the latest data.

            **User Query:** {user_message}
            """

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert in cryptocurrency markets."},
                {"role": "user", "content": ai_prompt}
            ]
        )

        return response.choices[0].message.content.strip()

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
    if "price of" in user_message.lower():
        asset = user_message.lower().split("price of")[-1].strip()
        crypto_data = get_crypto_data(asset)

        if crypto_data:
            return f"📈 **{asset.upper()} Price:** {crypto_data['price']}\n" \
                   f"💰 **Market Cap:** {crypto_data.get('market_cap', 'N/A')}\n" \
                   f"🔄 **24h Volume:** {crypto_data.get('24h_volume', 'N/A')}\n" \
                   f"📊 **24h Change:** {crypto_data.get('24h_change', 'N/A')}"

    if any(keyword in user_message.lower() for keyword in ["trending cryptos", "top cryptos", "most sold cryptos"]):
        trending_coins = get_trending_cryptos()
        return f"🔥 **Trending Cryptos Today:** {', '.join(trending_coins)}"

    return get_ai_response(user_message)
