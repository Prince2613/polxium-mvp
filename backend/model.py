import numpy as np
import pandas as pd
from sklearn.svm import SVR
from sklearn.preprocessing import MinMaxScaler


def interpret_rsi(rsi_value: float) -> dict:
    """
    Translates RSI number into plain English signal.
    This is your weather analogy in code —
    the number becomes a human readable condition.
    """
    if rsi_value >= 70:
        return {
            "label": "OVERBOUGHT",
            "value": rsi_value,
            "signal": "bearish",
            "explanation": (
                f"RSI is at {rsi_value} — stock has been bought "
                f"aggressively. Historically above 70 precedes "
                f"a pullback. Buying pressure may be exhausting."
            ),
            "severity": "caution"
        }
    elif rsi_value <= 30:
        return {
            "label": "OVERSOLD",
            "value": rsi_value,
            "signal": "bullish",
            "explanation": (
                f"RSI is at {rsi_value} — stock has been sold "
                f"heavily. Below 30 often signals a potential "
                f"bounce as selling pressure may be exhausting."
            ),
            "severity": "opportunity"
        }
    elif rsi_value >= 60:
        return {
            "label": "STRONG",
            "value": rsi_value,
            "signal": "bullish",
            "explanation": (
                f"RSI at {rsi_value} — momentum is strong "
                f"but not yet in danger zone. Buyers are "
                f"in control. Watch if it approaches 70."
            ),
            "severity": "neutral"
        }
    elif rsi_value <= 40:
        return {
            "label": "WEAK",
            "value": rsi_value,
            "signal": "bearish",
            "explanation": (
                f"RSI at {rsi_value} — momentum is weak. "
                f"Sellers have more control. Not yet oversold "
                f"but worth watching closely."
            ),
            "severity": "neutral"
        }
    else:
        return {
            "label": "NEUTRAL",
            "value": rsi_value,
            "signal": "neutral",
            "explanation": (
                f"RSI at {rsi_value} — balanced momentum. "
                f"Neither overbought nor oversold. "
                f"No strong directional signal currently."
            ),
            "severity": "neutral"
        }


def interpret_macd(
    macd_value: float,
    signal_value: float,
    histogram: float
) -> dict:
    """
    Translates MACD into plain English.
    The crossover is the most important signal.
    """
    above_signal = macd_value > signal_value
    histogram_growing = histogram > 0

    if above_signal and histogram_growing:
        return {
            "label": "BULLISH MOMENTUM",
            "signal": "bullish",
            "explanation": (
                "MACD is above its signal line and momentum "
                "is growing. Short term trend is stronger than "
                "long term — buyers currently in control."
            ),
            "severity": "positive"
        }
    elif above_signal and not histogram_growing:
        return {
            "label": "WEAKENING BULLISH",
            "signal": "neutral",
            "explanation": (
                "MACD is above signal line but momentum is "
                "slowing. Upward trend may be losing strength. "
                "Watch for a potential crossover downward."
            ),
            "severity": "caution"
        }
    elif not above_signal and not histogram_growing:
        return {
            "label": "BEARISH MOMENTUM",
            "signal": "bearish",
            "explanation": (
                "MACD is below its signal line and momentum "
                "is falling. Short term trend is weaker than "
                "long term — sellers currently in control."
            ),
            "severity": "caution"
        }
    else:
        return {
            "label": "WEAKENING BEARISH",
            "signal": "neutral",
            "explanation": (
                "MACD is below signal line but downward "
                "momentum is slowing. Bearish trend may be "
                "losing strength. Watch for potential recovery."
            ),
            "severity": "neutral"
        }


def interpret_bollinger(
    current_price: float,
    upper: float,
    middle: float,
    lower: float,
    percent_b: float,
    bandwidth: float
) -> dict:
    """
    Translates Bollinger Bands position into plain English.
    Uses your exact weather analogy thinking.
    """
    # Squeeze detection — low bandwidth means
    # volatility is compressed, big move coming
    is_squeeze = bandwidth < 5.0

    if percent_b >= 1.0:
        return {
            "label": "ABOVE UPPER BAND",
            "signal": "bearish",
            "explanation": (
                f"Price is above the upper Bollinger Band. "
                f"This is statistically unusual — price is "
                f"trading outside its normal range. "
                f"High probability of returning to middle band "
                f"at {middle}."
            ),
            "severity": "caution"
        }
    elif percent_b >= 0.8:
        return {
            "label": "NEAR UPPER BAND",
            "signal": "bearish",
            "explanation": (
                f"Price is approaching the upper band. "
                f"Stock is in the high zone of its recent "
                f"range. Resistance likely near {upper}."
            ),
            "severity": "caution"
        }
    elif percent_b <= 0.0:
        return {
            "label": "BELOW LOWER BAND",
            "signal": "bullish",
            "explanation": (
                f"Price is below the lower Bollinger Band. "
                f"Statistically unusual on the downside. "
                f"Potential for bounce back toward middle "
                f"band at {middle}."
            ),
            "severity": "opportunity"
        }
    elif percent_b <= 0.2:
        return {
            "label": "NEAR LOWER BAND",
            "signal": "bullish",
            "explanation": (
                f"Price is near the lower band. Stock is "
                f"in the low zone of its recent range. "
                f"Support likely near {lower}."
            ),
            "severity": "neutral"
        }
    elif is_squeeze:
        return {
            "label": "BAND SQUEEZE",
            "signal": "neutral",
            "explanation": (
                "Bollinger Bands are unusually tight. "
                "Volatility is very low right now. "
                "Historically this precedes a large move "
                "in either direction. Direction unclear."
            ),
            "severity": "watch"
        }
    else:
        return {
            "label": "MIDDLE RANGE",
            "signal": "neutral",
            "explanation": (
                f"Price is in the middle of its Bollinger "
                f"Band range. No extreme reading. "
                f"Band middle at {middle}."
            ),
            "severity": "neutral"
        }


def generate_overall_verdict(
    rsi_signal: str,
    macd_signal: str,
    bb_signal: str
) -> dict:
    """
    Combines all three signals into one verdict.
    This is your weather forecast final summary —
    sun + clouds + wind = probability of rain.
    """
    signals = [rsi_signal, macd_signal, bb_signal]
    bullish_count = signals.count("bullish")
    bearish_count = signals.count("bearish")

    if bullish_count >= 2:
        return {
            "verdict": "BULLISH",
            "color": "green",
            "score": 70 + (bullish_count * 10),
            "summary": (
                f"{bullish_count} of 3 indicators showing "
                f"positive signals. Conditions look relatively "
                f"favorable based on current technical picture."
            )
        }
    elif bearish_count >= 2:
        return {
            "verdict": "CAUTION",
            "color": "red",
            "score": 30 - (bearish_count * 5),
            "summary": (
                f"{bearish_count} of 3 indicators showing "
                f"warning signals. Current technical conditions "
                f"suggest elevated risk."
            )
        }
    else:
        return {
            "verdict": "NEUTRAL",
            "color": "yellow",
            "score": 50,
            "summary": (
                "Mixed signals across indicators. No clear "
                "directional bias currently. Monitor for "
                "confluence before drawing conclusions."
            )
        }


def run_svr_model(df: pd.DataFrame) -> dict | None:
    """
    Runs SVR pattern detection.
    Returns actual, predicted, stable lines for chart.
    """
    df = df.copy()
    df['Day'] = range(len(df))

    df['MA7'] = df['Close'].rolling(window=7).mean()
    df['MA21'] = df['Close'].rolling(window=21).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['Return'] = df['Close'].pct_change()
    df['Volatility'] = df['Return'].rolling(window=7).std()
    df = df.dropna()

    if len(df) < 60:
        return None

    features = ['Day', 'MA7', 'MA21', 'Volatility']
    X = df[features].values
    y = df['Close'].values

    scaler_X = MinMaxScaler()
    scaler_y = MinMaxScaler()
    X_scaled = scaler_X.fit_transform(X)
    y_scaled = scaler_y.fit_transform(
        y.reshape(-1, 1)
    ).ravel()

    split = int(len(X_scaled) * 0.8)
    model = SVR(kernel='rbf', C=100, gamma=0.1, epsilon=0.1)
    model.fit(X_scaled[:split], y_scaled[:split])

    y_pred = scaler_y.inverse_transform(
        model.predict(X_scaled).reshape(-1, 1)
    ).ravel()

    stable = df['MA50'].values

    return {
        "dates": df['Date'].astype(str).tolist(),
        "actual": y.tolist(),
        "predicted": y_pred.tolist(),
        "stable": stable.tolist(),
        "train_size": split
    }


def generate_full_insights(df: pd.DataFrame) -> dict:
    """
    Master function.
    Takes the full dataframe with all indicators
    and generates complete insight package.
    This is what the API returns to the frontend.
    """
    # Get latest values
    latest = df.iloc[-1]

    rsi_val = float(latest['RSI'])
    macd_val = float(latest['MACD'])
    signal_val = float(latest['MACD_Signal'])
    histogram_val = float(latest['MACD_Histogram'])
    price = float(latest['Close'])
    bb_upper = float(latest['BB_Upper'])
    bb_middle = float(latest['BB_Middle'])
    bb_lower = float(latest['BB_Lower'])
    percent_b = float(latest['BB_PercentB'])
    bandwidth = float(latest['BB_Bandwidth'])

    # Generate individual signals
    rsi_insight = interpret_rsi(rsi_val)
    macd_insight = interpret_macd(macd_val, signal_val, histogram_val)
    bb_insight = interpret_bollinger(
        price, bb_upper, bb_middle,
        bb_lower, percent_b, bandwidth
    )

    # Generate overall verdict
    verdict = generate_overall_verdict(
        rsi_insight['signal'],
        macd_insight['signal'],
        bb_insight['signal']
    )

    # Run SVR for chart data
    chart_data = run_svr_model(df)

    return {
        "current_price": round(price, 2),
        "verdict": verdict,
        "indicators": {
            "rsi": rsi_insight,
            "macd": macd_insight,
            "bollinger": bb_insight
        },
        "chart": chart_data,
        "raw": {
            "dates": df['Date'].tolist(),
            "open": df['Open'].tolist(),
            "high": df['High'].tolist(),
            "low": df['Low'].tolist(),
            "close": df['Close'].tolist(),
            "volume": df['Volume'].tolist(),
            "bb_upper": df['BB_Upper'].tolist(),
            "bb_middle": df['BB_Middle'].tolist(),
            "bb_lower": df['BB_Lower'].tolist(),
        }
    }