import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

def get_connection():
  return sqlite3.connect('bitcoin_trades.db')

def load_data():
  conn = get_connection()
  query = "SELECT * FROM trades"
  df = pd.read_sql_query(query, conn)
  conn.close()
  return df

def main():
  st.title("Bitcoin Trades Viewer")

  df = load_data()

  st.header("Basic Statistics")
  st.write(f"Total number of trades:{len(df)}")
  st.write(f"First trade data: {df['timestamp'].min()}")
  st.write(f"Last trade data: {df['timestamp'].max()}")

  # 거래 내역
  st.header("Trade History")
  st.dataframe(df)

  # 거래 분포
  st.header("Trade Decision Distrubution")
  decision_counts = df['decision'].value_counts()
  fig = px.pie(values=decision_counts.values, names=decision_counts.index, title="Trade Decisions")
  st.plotly_chart(fig)

  # BTC 잔액 변화
  st.header('BTC Balance Over Time')
  fig = px.line(df, x='timestamp', y='btc_balance', title = 'BTC Balance')
  st.plotly_chart(fig)

  # USD 잔액 변화
  st.header('USD Balance Over Time')
  fig = px.line(df, x="timestamp", y = "usd_balance", title="USD Balance")
  st.plotly_chart(fig)

  # BTC 가격 변화
  st.header('BTC Price Over Time')
  fig = px.line(df, x='timestamp', y = "btc_usd_price", title="BTC Price (USD)")
  st.plotly_chart(fig)

if __name__ == "__main__":
  main()


