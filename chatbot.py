import os
import requests
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import openai

# Load environment variables
load_dotenv()
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
openai.api_key = os.getenv("OPENAI_API_KEY")

# Function to fetch crypto data from CoinGecko
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
                "price": crypto_data["usd"],
                "market_cap": crypto_data["usd_market_cap"],
                "24h_volume": crypto_data["usd_24h_vol"],
                "24h_change": crypto_data["usd_24h_change"]
            }
        return None
    except Exception as e:
        print(f"Error fetching data for {crypto_name} from CoinGecko: {e}")
        return None

# Function to scrape CoinDesk for Bitcoin price if CoinGecko fails
def fetch_coin_info_from_web(coin_name):
    try:
        # Setup Selenium WebDriver (Headless Chrome)
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        # Use CoinDesk URL for Bitcoin (or any other coin URL if required)
        url = f"https://www.coindesk.com/price/{coin_name.lower()}"
        driver.get(url)

        # Scrape the price (find the relevant element using the class or ID)
        price_element = driver.find_element(By.CLASS_NAME, "price-class")  # Replace with actual class
        price = price_element.text

        # Scraping the description (can be modified as needed)
        description_element = driver.find_element(By.CLASS_NAME, "description-class")  # Replace with actual class
        description = description_element.text

        driver.quit()

        return {
            "price": price,
            "description": description
        }
    except Exception as e:
        print(f"Error fetching data from CoinDesk: {e}")
        return None

# Function to fetch trending coins from CoinGecko
def get_trending_cryptos():
    try:
        url = f"{COINGECKO_API_URL}/search/trending"
        response = requests.get(url)
        data = response.json()

        trending_coins = [coin["item"]["name"] for coin in data["coins"]]
        return trending_coins
    except Exception as e:
        print(f"Error fetching trending coins: {e}")
        return []

# Function to generate AI response using OpenAI API
def get_ai_response(user_message):
    """
    Generates a response based on user message.
    Uses OpenAI GPT to generate responses about crypto.
    """
    try:
        response = openai.chat.completions.create(  # ✅ Correct API Syntax
            model="gpt-3.5-turbo",  # Or use "gpt-3.5-turbo" model
            messages=[
                {"role": "system", "content": "You are a helpful AI chatbot answering only questions related to crypto and trading cryptos, use the coingecko api or realtime check https://www.coingecko.com/ to fetch real time data and help users as much as you can."},
                {"role": "user", "content": user_message}
            ]
        )

        return response.choices[0].message.content.strip()

    except openai.OpenAIError as e:
        return f"❌ OpenAI API Error: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"
