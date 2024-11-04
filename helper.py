import os
import json
import ta
from ta.utils import dropna
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from youtube_transcript_api import YouTubeTranscriptApi
import time
import logging
import base64

# Indicators
def add_indicators(df):
  df = json.loads(df)
  df = pd.DataFrame(df)

  df = dropna(df)

  # BollingerBands
  indicator_bb = ta.volatility.BollingerBands(close=df['c'], window=20, window_dev=2)
  df['bb_bbm'] = indicator_bb.bollinger_mavg()
  df['bb_bbh'] = indicator_bb.bollinger_hband()
  df['bb_bbl'] = indicator_bb.bollinger_lband()

  # RSI
  df['rsi'] = ta.momentum.RSIIndicator(close=df['c'], window=14).rsi()

  # MACD
  macd = ta.trend.MACD(close=df['c'])
  df['macd'] = macd.macd()
  df['macd_signal'] = macd.macd_signal()
  df['macd_diff'] = macd.macd_diff()

  # Trend (SMA/EMA)
  df['sma_20'] = ta.trend.SMAIndicator(close=df['c'], window=20).sma_indicator()
  df['ema_12'] = ta.trend.EMAIndicator(close=df['c'], window=12).ema_indicator()

  return df

# Fear and Greed Index

def get_fear_and_greed_index():
  url = "https://api.alternative.me/fng/"
  response = requests.get(url)
  if response.status_code == 200:
    data = response.json()
    return data['data'][0]

  else:
    print(f"failed to fetch Fear and Greed Index. Status code: {response.status_code}")
    return None

# BTC News
def get_bitcoin_news():
    serpapi_key = os.getenv("SERPAPI_API_KEY")
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_news",
        # News info 
        "q": "Bitcoin cryptocurrency",
        "api_key": serpapi_key
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        news_results = data.get("news_results", [])
        headlines = []
        for item in news_results:
            headlines.append({
                "title": item.get("title", ""),
                "date": item.get("date", "")
            })

        return headlines[:5]  # Moved outside of the loop
    except requests.RequestException as e:
        print(f"Error fetching news: {e}")
        return []
    
# BTC/USDT Chart Image
# ------------------------
# Logging settings
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_chrome_options():
    chrome_options = Options()

    # Add arguments for full screen mode
    chrome_options.add_argument("--start-maximized")  # Maximize for Windows/Linux
    chrome_options.add_argument("--kiosk")  # Full screen mode for macOS
    
    # Additional window size settings for macOS
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Additional useful options
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-notifications")  # Disable notifications
    chrome_options.add_argument("--disable-infobars")  # Disable infobars
    chrome_options.add_argument("--disable-popup-blocking")  # Disable popup blocking
    
    return chrome_options

def create_driver():
    logger.info("Setting up ChromeDriver...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=setup_chrome_options())
    return driver

def click_indicators(driver):
    try:
        indicator_xpath = "/html/body/div[1]/div[2]/div[3]/span/div/div/div[1]/div/div/cq-menu[3]"
        
        # Wait for the indicator menu to be clickable and click it
        indicator_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, indicator_xpath))
        )
        indicator_element.click()
        logger.info("Indicator menu opened")

        # Define the XPath for the Bollinger Bands option
        bollinger_band_xpath = "/html/body/div[1]/div[2]/div[3]/span/div/div/div[1]/div/div/cq-menu[3]/cq-menu-dropdown/cq-scroll/cq-studies/cq-studies-content/cq-item[15]"
        
        # Wait for the Bollinger Band element to be present in the DOM
        bollinger_band_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, bollinger_band_xpath))
        )
        
        # Scroll the element into view using JavaScript
        bollinger_band_element.click()
       
        logger.info("Bollinger Bands selected")

    except Exception as e:
        logger.error(f"Error clicking indicator button: {e}")
        
    
def click_menu_and_select_1hour(driver):
    try:
        logger.info("Waiting for menu button to be clickable...")

        menu_xpath = "/html/body/div[1]/div[2]/div[3]/span/div/div/div[1]/div/div/cq-menu[1]/span/cq-clickable"

        element = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, menu_xpath))
        )
        element.click() 
        logger.info("Waiting for 1 hour button to be clickable...")
        
        # Wait for the 1-hour button to be present
        one_hour_button_xpath = "/html/body/div[1]/div[2]/div[3]/span/div/div/div[1]/div/div/cq-menu[1]/cq-menu-dropdown/cq-item[8]"
        
        # Wait for the button to be visible and clickable
        element = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, one_hour_button_xpath))
        )

        element.click()
        logger.info("1 hour selected")
        

    except Exception as e:
        logger.error(f"Error clicking 1 hour button: {e}")
    

def capture_full_page_screenshot(driver, url, filename):
    try:
        logger.info(f"Loading {url}...")
        driver.get(url)
        
        # Wait for page load
        WebDriverWait(driver, 10).until(
            lambda x: x.execute_script("return document.readyState") == "complete"
        )

        # Wait for chart to load
        time.sleep(5)

        click_indicators(driver)
        click_menu_and_select_1hour(driver)
      
        # Wait for UI updates to complete
        time.sleep(3)

        # Save screenshot directly to file
        driver.save_screenshot(filename)
        logger.info(f"Screenshot saved as: {filename}")

        # Now handle the base64 encoding
        with open(filename, 'rb') as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return encoded_string

    except Exception as e:
        logger.error(f"Error capturing screenshot: {e}")
        raise
    
def main():
    url = "https://upbit.com/full_chart?code=CRIX.UPBIT.USDT-BTC"
    filename = "BTC_USDT_Chart.png"
    driver = None

    try:
        driver = create_driver()
        return capture_full_page_screenshot(driver, url, filename)

    except Exception as e:
        logger.error(f"Main execution error: {e}")

    finally:
        if driver:
            driver.quit()

def youtub_transcript(vedio_id):
    transcript = YouTubeTranscriptApi.get_transcript(vedio_id, languages=['ko'])

    text = " ".join(entry["text"] for entry in transcript)

    return text