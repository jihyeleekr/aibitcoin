import os
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load API keys from .env file
load_dotenv()

class CryptoTrader:

  def __init__(self):
      self.headers = {
          "accept": "application/json",
          "APCA-API-KEY-ID": os.getenv("APCA_API_KEY_ID"),
          "APCA-API-SECRET-KEY": os.getenv("APCA_API_SECRET_KEY")
      }

  def cash_crypto_balance(self):
      balance = []
      try:
          cash = requests.get(os.getenv("BASE_URL"), headers=self.headers)
          cash = cash.json()

          keys_to_keep = [
              'status', 'crypto_status', 'currency', 'buying_power', 
              'cash', 'portfolio_value', 'shorting_enabled', 
              'equity', 'long_market_value', 'position_market_value'
          ]
          filtered_data = {key: value for key, value in cash.items() if key in keys_to_keep}
          balance.append(filtered_data)

          cryptos = requests.get(os.getenv("POS_URL"), headers=self.headers)
          cryptos = cryptos.json()

          if isinstance(cryptos, list):
              for crypto in cryptos:
                  if crypto["symbol"] == "BTCUSD":
                      keys_to_keep = [
                          'symbol', 'qty', 'avg_entry_price', 
                          'side', 'market_value', 'current_price'
                      ]
                      filtered_data = {key: value for key, value in crypto.items() if key in keys_to_keep}
                      balance.append(filtered_data)
                      break
              else:
                  print("No positions found.")
                  return balance
          else:
              print("Unexpected response format: expected a list.")
              return balance

      except requests.RequestException as e:
          print("Error fetching data:", e)
          return balance
      return balance
    
  def data_history(self, symbol="BTC/USD", time=None, start=None, end=None):
    if "/" in symbol:
        symbol = symbol.replace("/", "%2F")
    url = (
        "https://data.alpaca.markets/v1beta3/crypto/us/bars?symbols={symbol}&timeframe={time}&start={start}&end={end}&limit=1000&sort=asc"
    ).format(symbol=symbol, time=time, start=start, end=end)

    try:
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()  # Check if the request was successful
        data = response.json()
    except requests.RequestException as e:
        print("Error fetching historical data:", e)
        return []

    keys_to_keep = ['c', 'h', 'l', 'o', 't', 'v']
    filtered_bars = [
        {key: bar[key] for key in keys_to_keep} for bar in data.get('bars', {}).get('BTC/USD', [])
    ]
    return json.dumps(filtered_bars, indent=4)

  def last_thirty_days(self, symbol = "BTC/USD", time = "1D"):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    start_str = start_date.strftime('%Y-%m-%dT00:00:00Z')
    end_str = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    return self.data_history(symbol=symbol, time=time, start=start_str, end=end_str)

  def last_24_hours(self, symbol="BTC/USD", time="1H"):  
    end_date = datetime.now()
    start_date = end_date - timedelta(hours=24)
    start_str = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    end_str = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    return self.data_history(symbol=symbol, time=time, start=start_str, end=end_str)

  def get_crypto_positions(self):
    response = requests.get(os.getenv("POS_URL"), headers=self.headers)
    positions = response.json()

    if isinstance(positions, list) and positions:
        for position in positions:
            if 'qty' in position:
                return float(position['qty'])
    else:
        print("Unexpected response format: expected a list or no positions found.")
        return None

  def get_balance(self): 
    response = requests.get(os.getenv("BASE_URL"), headers=self.headers)
    account_info = response.json()

    if 'portfolio_value' in account_info:
        return float(account_info['portfolio_value'])
    else:
        print("Portfolio value not found in account info.")
        return None
  
  def order_book(self):
    response = requests.get(os.getenv("ORDERBOOK_URL"), headers=self.headers)
    return response.json()

  def sell_market_order(self, percentage):
    qty = self.get_crypto_positions()
    data = self.order_book()
    latest_ask_price = data.get('orderbooks', {}).get('BTC/USD', {}).get('a', [{}])[0].get('p')

    if qty is not None and latest_ask_price and qty * latest_ask_price > 1:
        sell_amount = qty * (percentage / 100)
        if sell_amount * latest_ask_price > 200000:
            sell_amount = 200000 / latest_ask_price
        payload = {
            "side": "sell",
            "type": "market",
            "time_in_force": "ioc",
            "symbol": "BTC/USD",
            "qty": str(sell_amount)
        }
        response = requests.post(os.getenv("ORDER_URL"), json=payload, headers=self.headers)
        print(response.text)
    else:
        print("BTC less than $1 or no positions found.")

  def buy_market_order(self, percentage):
    balance = self.get_balance()
    if balance and balance > 1:
        notional_amount = min(balance * (percentage / 100), 200000)
        payload = {
            "side": "buy",
            "type": "market",
            "time_in_force": "ioc",
            "symbol": "BTC/USD",
            "notional": str(notional_amount)
        }
        response = requests.post(os.getenv("ORDER_URL"), json=payload, headers=self.headers)
        print(f"### Buy Order Executed: {percentage}% available USD")
        print(response.text)
    else:
        print("Insufficient balance to place a buy order.")
