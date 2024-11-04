import json
import alpaca
from openai import OpenAI
import helper
from pydantic import BaseModel
from datetime import datetime, timedelta
import sqlite3
import time
import pandas as pd

class TradingDecision(BaseModel):
  decision: str
  percentage : int
  reason: str

def init_db():
  conn = sqlite3. connect('bitcoin_trades.db')
  c = conn. cursor()
  c. execute('''CREATE TABLE IF NOT EXISTS trades
  (id INTEGER PRIMARY KEY AUTOINCREMENT, 
   timestamp TEXT, 
   decision TEXT, 
   percentage INTEGER, 
   reason TEXT, 
   btc_balance REAL, 
   usd_balance REAL, 
   btc_avg_buy_price REAL,
  btc_usd_price REAL,
  reflection TEXT)''')
  conn.commit()
  return conn

def log_trade(conn, decision, percentage, reason, btc_balance, usd_balance, btc_avg_buy_price, btc_usd_price, reflection):
    c = conn.cursor()
    timestamp = datetime.now().isoformat()
    c.execute('''INSERT INTO trades
                 (timestamp, decision, percentage, reason, btc_balance, usd_balance, btc_avg_buy_price, btc_usd_price, reflection)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (timestamp, decision, percentage, reason, btc_balance, usd_balance, btc_avg_buy_price, btc_usd_price, reflection))
    conn.commit()
  
def get_recent_trades(conn, days=7):
  c = conn.cursor()
  seven_days_ago = (datetime.now() - timedelta(days=days)).isoformat()
  c.execute("SELECT * FROM trades WHERE timestamp >  ? ORDER BY timestamp DESC", (seven_days_ago,))
  columns = [column[0] for column in c.description]
  return pd.DataFrame.from_records(data = c.fetchall(), columns = columns)

def get_db_connection():
   return sqlite3.connect("bitcoin_trades.db")

def calculate_performance(trades_df):
  if trades_df.empty:
    return 0
  
  initial_balance = trades_df.iloc[-1]['usd_balance'] + trades_df.iloc[-1]['btc_balance'] * trades_df[-1]['btc_usd_price']
  final_balance = trades_df.iloc[0]['usd_balance'] + trades_df.iloc[0]['btc_balance'] * trades_df.iloc[0]['btc_usd_price']

  return (final_balance - initial_balance) / initial_balance * 100

def generate_reflection(trades_df, current_market_data):
  performance = calculate_performance(trades_df)

  client = OpenAI()
  response = client.chat.completions.create(
     model = "gpt-4o",
     messages = [
       {
         "role" : "system",
         "content" : "You are an AI trading assitant takes with analyzing recent trading performance and current market conditions to generate insights and improbements for futuer tradign decisions."
       },
       {
         "role" : "user",
         "content" : f"""
          {trades_df.to_json(orient='records')}
          Current market data:
          {current_market_data}

          Overall performance in the last 7 days: {performance: .2f}%

          Please analyze this data and provide:
          1. A brief reflection on the recent trading decisions
          2. Insights on what worked well and what didn't
          3. Suggestions for imporvment in future trading decisions
          4. Any patterns or trends you notice in the market data

          Limit your response to 250 wors or less.
          """
       }
     ]
  )
  return response.choices[0].message.content

init_db()
# Cal Alpaca file
trader = alpaca.CryptoTrader()

def ai_trading():
  # 1. Bring data

  # 30 days data
  df_daily = trader.thirty_days()
  df_daily = helper.add_indicators(df_daily)

  # 24 hours data
  df_hourly = trader.last_24_hours()
  df_hourly = helper.add_indicators(df_hourly)

  # Current Balance
  balances = trader.cash_crypto_balance()

  # Orderbook
  orderbook = trader.order_book()

  # Fear and Greed Index
  fear_greed_index = helper.get_fear_and_greed_index()

  # News Headline
  headlines = helper.get_bitcoin_news()

  # Youtube Transcript
  transcript = helper.youtub_transcript("J-7tPXNz30A")

  # Chart Image
  chart_image = helper.main()

  conn = get_db_connection()

  recent_trades = get_recent_trades(conn)

  current_market_data = {
    "fear_greed_index" : fear_greed_index,
    "news_headlines" : headlines,
    "orderbook" : orderbook,
    "daily_ohlcv": df_daily.to_dict(),
    "hourly_ohlcv": df_hourly.to_dict(),
  }
  # Reflection
  reflection = generate_reflection(recent_trades, current_market_data)

  #2. Get decision from Chat GPT
  client = OpenAI()
  response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
      {
        "role": "system",
        "content": f"""You are an expert in Bitcoin investing. Analyze provided data and determine whether 
                to buy, sell, or hold Bitcoin. Use the following indicators to guide your decision: 
                
                - Technical indicators and market data, focusing on both short-term and long-term trends.
                - Recent news headlines and their potential impact on Bitcoin price.
                - The Fear and Greed Index: This index gauges market sentiment, ranging from extreme fear to extreme greed.
                  A high "greed" score may indicate overbought conditions, whereas a high "fear" score may suggest oversold
                  conditions, potentially affecting Bitcoin's price movements.
                - Overall market sentiment as a reflection of trading volume, volatility, and order book data.
                - Patterns and trends visible in the BTC/USDT chart image.
                - Recent trading performance and reflection

                Recent trading reflection:
                {reflection}
                
                An additional key factor to consider is the "Wonyyotti" trading method. Please incorporate principles from this 
                method, especially when analyzing the current market. The transcript of a recent video from Wonyyotti discussing 
                Bitcoin is provided below. (Note: The transcript is in Korean.)
                {transcript}
                Response format:
                1. A decision ("buy", "sell", or "hold").
                2. If the decision is "buy", provide a percentage (1-100) of available USD to use for buying Bitcoin.
                   If the decision is "sell," provide a percentage (1-100) of held BTC to sell.
                   If the decision is "hold," set the percentage to 0.
                3. A reason for your decision, integrating relevant data and analysis as described.

                Important: Ensure that the "percentage" is an integer between 1 and 100 for buy/sell decisions, and exactly 0 for hold decisions.
                Your percentage should reflect the strength of your conviction in the decision based on provided data.
                """
      },
      {
        "role": "user",
        "content": f"""Current investment status: {json.dumps(balances)}
                Orderbook: {json.dumps(orderbook)}
                Daily OHLCV with indicators (30 days): {df_daily.to_json()}
                Hourly OHLCV with indicators (24 hours): {df_hourly.to_json()}
                Recent news headlines: {json.dumps(headlines)}
                Fear and Greed Index: {json.dumps(fear_greed_index)}
                """
      },
      {
        "role": "user",
        "content": "Chart image included below:",
        "image_url": {
            "url": f"data:image/png;base64,{chart_image}"
        }
      }
    ],
    response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "trading_decision",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "decision": {"type": "string", "enum": ["buy", "sell", "hold"]},
                        "percentage" : {"type" : "integer"},
                        "reason": {"type": "string"}
                    },
                    "required": ["decision", "percentage", "reason"],
                    "additionalProperties": False
                }
            }
        },
        max_tokens=4095
  )
  result = TradingDecision.model_validate_json(response.choices[0].message.content)


  # 3. Based on AI's decision do actual buy/sell/hold

  print(f"### AI Decision: {result.decision.upper()} ###")
  print(f"## Reason: {result.reason} ##")

  order_excuted = False

  if result.decision == "sell":
    print(f"### Sell Order Executed: {result.percentage}% of held BTC")
    if trader.sell_market_order(result.percentage) != "BTC less than $1 or no positions found":
       order_excuted = True

  elif result.decision == "buy":
    print(f"### Buy Order Executed: {result.percentage}% of available USD")
    if trader.buy_market_order(result.percentage) != "Insufficient balance to place a buy order.":
        order_excuted = True

  elif result.decision == "hold":
    print("### Hold Order Executed ###")
    print("Hold Reason:", result.reason)
    order_excuted = True

  time.sleep(1)
  balances = trader.cash_crypto_balance()
  usd_balance = float(balances[0]['cash'])  # Assuming first entry is USD
  btc_balance = float(balances[1]['qty'])   # Assuming second entry is BTC
  btc_avg_buy_price = float(balances[1]['avg_entry_price'])
  btc_usd_price = float(balances[1]['current_price'])

  try:
    conn = get_db_connection()
    log_trade(conn, result.decision, result.percentage if order_excuted else 0, result.reason, 
                btc_balance,  usd_balance, btc_avg_buy_price, btc_usd_price, reflection)
  except sqlite3.Error as db_error:
    print(f"Database error: {db_error}")
  finally:
    conn.close()
  

# while True:
#   time.sleep(600)
ai_trading()
