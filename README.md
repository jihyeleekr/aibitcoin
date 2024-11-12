# AI Bitcoin Trader

This project is an automated Bitcoin trading bot developed in Python, utilizing the Alpaca API for live trading data and order execution. It incorporates machine learning and sentiment analysis to make informed trading decisions based on recent chart data, the order book, and social sentiment gathered from YouTube and news sources.

---

## Features

- **Automated Bitcoin Trading**: Leverages Alpaca's API for real-time trading data and order execution.
- **Sentiment Analysis**: Integrates data from YouTube transcripts (in Korean) and news to gauge market sentiment.
- **Fear and Greed Index**: Considers market sentiment indicators for buy/sell decisions.
- **Trading Methodology**: Inspired by 'Wonyyotti's' trading strategies, with an emphasis on adapting to volatile market conditions.
- **Data Visualization**: Uses Streamlit and Plotly to visualize trading data.
- **Database Logging**: SQLite database logs trades, performance metrics, and reflections on trades.

---

## Setup

### Prerequisites

- **Python 3.8+**
- **[Alpaca API](https://alpaca.markets/) account and API keys**
- **[OpenAI API](https://openai.com/api/) key** for sentiment analysis
- **Selenium** for browser automation (optional for Alpaca login)

### Installation

1. **Clone the repository**:
    ```
    git clone https://github.com/jihyeleekr/aibitcoin.git
    cd aibitcoin
    ```

2. **Set up a virtual environment** (recommended):
    ```
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install dependencies**:
    ```
    pip install -r requirements.txt
    ```

4. **Configure API keys** by creating an `.env` file in the root directory:
    ```
    ALPACA_API_KEY=your_alpaca_api_key
    ALPACA_SECRET_KEY=your_alpaca_secret_key
    OPENAI_API_KEY=your_openai_api_key
    ```

### Useage

To start the trading bot, run:

```
python autotrade.py
```

### Data Visualization
Visualize trades and performance with Streamlit:

```
streamlit run streamlit_app.py
```
link: http://localhost:8501/
### Contributing
Contributions are welcome! Please fork the repository and submit a pull request with a clear description of changes.

