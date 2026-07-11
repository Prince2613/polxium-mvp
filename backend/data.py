import yfinance as yf
import pandas as pd
import numpy as np


def get_stock_data(symbol: str, period: str = "1y"):
    """
    Fetches historical OHLCV price data from yfinance.
    OHLCV = Open, High, Low, Close, Volume
    This is the raw material everything else builds on.
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)

        if df.empty:
            return None

        df = df.reset_index()
        df['Date'] = df['Date'].astype(str)
        df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
        df = df.round(2)

        return df

    except Exception as e:
        print(f"Data fetch error: {e}")
        return None


def get_company_info(symbol: str):
    """
    Fetches basic company details.
    Used for the About section — hidden by default in UI.
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        return {
            "name": info.get("longName", symbol),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "description": info.get("longBusinessSummary", "N/A"),
            "country": info.get("country", "N/A"),
            "currency": info.get("currency", "N/A"),
            "website": info.get("website", "N/A"),
        }

    except Exception as e:
        print(f"Company info error: {e}")
        return None


def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """
    RSI — Relative Strength Index.

    What it is:
    A momentum indicator that measures speed and
    change of price movements on a scale of 0 to 100.

    Why it exists:
    Markets tend to overreact. Prices get pushed too
    high by greed or too low by fear. RSI measures
    how extreme that push is.

    How it works:
    It compares average gains vs average losses
    over the last 14 days.
    
    Above 70 = overbought = caution, may fall
    Below 30 = oversold = possible bounce
    Between 30-70 = neutral territory
    """
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))

    return rsi.round(2)


def calculate_macd(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> dict:
    """
    MACD — Moving Average Convergence Divergence.

    What it is:
    Shows the relationship between two moving averages.
    Specifically the 12-day and 26-day exponential
    moving averages.

    Why it exists:
    It captures momentum shifts — when short term
    momentum is stronger or weaker than long term.
    This is your early warning system for trend changes.

    How it works:
    MACD Line = 12-day EMA minus 26-day EMA
    Signal Line = 9-day EMA of the MACD Line
    Histogram = MACD Line minus Signal Line

    MACD crossing above Signal = bullish momentum
    MACD crossing below Signal = bearish momentum
    """
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()

    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line

    return {
        "macd": macd_line.round(4),
        "signal": signal_line.round(4),
        "histogram": histogram.round(4)
    }


def calculate_bollinger_bands(
    close: pd.Series,
    period: int = 20,
    std_dev: int = 2
) -> dict:
    """
    Bollinger Bands.

    What it is:
    Three lines drawn around price:
    Middle = 20-day simple moving average
    Upper = Middle + 2 standard deviations
    Lower = Middle - 2 standard deviations

    Why it exists:
    Your weather analogy applies perfectly here.
    The bands are like normal temperature range for
    a city. When price goes outside that range
    something unusual is happening.

    How it works:
    When price touches upper band = unusually high
    When price touches lower band = unusually low
    Bands squeezing together = low volatility,
    big move coming
    Bands expanding = high volatility period
    """
    middle = close.rolling(window=period).mean()
    std = close.rolling(window=period).std()

    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)

    # Band width tells us volatility level
    band_width = ((upper - lower) / middle * 100)

    # Where is current price within the bands
    # 0 = at lower band, 1 = at upper band
    percent_b = (close - lower) / (upper - lower + 1e-10)

    return {
        "upper": upper.round(2),
        "middle": middle.round(2),
        "lower": lower.round(2),
        "bandwidth": band_width.round(4),
        "percent_b": percent_b.round(4)
    }


def get_full_analysis_data(symbol: str, period: str = "1y"):
    """
    Master function that fetches price data and
    calculates all indicators in one call.

    This is what the /insights route will call.
    Returns everything the frontend needs.
    """
    df = get_stock_data(symbol, period)

    if df is None:
        return None

    close = df['Close']

    # Calculate all indicators
    rsi = calculate_rsi(close)
    macd_data = calculate_macd(close)
    bb_data = calculate_bollinger_bands(close)

    # Add to dataframe
    df['RSI'] = rsi
    df['MACD'] = macd_data['macd']
    df['MACD_Signal'] = macd_data['signal']
    df['MACD_Histogram'] = macd_data['histogram']
    df['BB_Upper'] = bb_data['upper']
    df['BB_Middle'] = bb_data['middle']
    df['BB_Lower'] = bb_data['lower']
    df['BB_Bandwidth'] = bb_data['bandwidth']
    df['BB_PercentB'] = bb_data['percent_b']

    # Drop rows where indicators haven't warmed up yet
    df = df.dropna()
    df = df.reset_index(drop=True)

    return df