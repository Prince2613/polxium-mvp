from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import requests
import os

# Load environment variables from .env file
# WHY: Keeps API keys out of code
# Safe to push to GitHub after this
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str
    context: str


# Currency mapping for major exchanges
# WHY: Indian stocks use ₹, US stocks use $
# Without this everything shows ₹ which is wrong
CURRENCY_MAP = {
    "INR": "₹",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
}


def get_currency_symbol(currency: str) -> str:
    return CURRENCY_MAP.get(currency, currency + " ")


@app.get("/")
def home():
    return {"message": "Polxium v2 running"}


@app.get("/insights/{symbol}")
def insights(symbol: str, period: str = "1y"):
    """
    Main route. Returns everything frontend needs.
    Handles Indian and global stocks automatically.
    """
    from backend.data import get_full_analysis_data, get_company_info
    from backend.model import generate_full_insights

    symbol = symbol.upper().strip()

    # Smart symbol resolution
    # Try in this order:
    # 1. As typed (handles TSLA, AAPL, etc directly)
    # 2. With .NS suffix (Indian NSE stocks)
    # 3. With .BO suffix (Indian BSE stocks)
    resolved_symbol = None
    df = None

    attempts = []

    # If already has exchange suffix use directly
    if "." in symbol:
        attempts = [symbol]
    else:
        # Try global first for known US stocks
        # Then try Indian exchanges
        attempts = [symbol, symbol + ".NS", symbol + ".BO"]

    for attempt in attempts:
        df = get_full_analysis_data(attempt, period)
        if df is not None:
            resolved_symbol = attempt
            break

    if df is None or resolved_symbol is None:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for {symbol}. Check the symbol and try again."
        )

    # Get company info using resolved symbol
    info = get_company_info(resolved_symbol)

    # Generate full analysis
    result = generate_full_insights(df)

    # Add currency symbol based on company currency
    currency = "INR"
    if info and info.get("currency"):
        currency = info["currency"]

    result["company"] = info
    result["currency_symbol"] = get_currency_symbol(currency)
    result["resolved_symbol"] = resolved_symbol

    return result


@app.post("/ask")
def ask_ai(req: AskRequest):
    """
    AI explanation using Groq.
    Only explains system output.
    Never predicts prices.
    Never gives financial advice.
    """
    if not GROQ_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Groq API key not configured"
        )

    prompt = f"""You are Polxium AI, a financial intelligence assistant for retail investors.

STRICT RULES:
- Only explain what the indicators and data show
- Never predict specific future prices
- Never say buy or sell
- Keep answer to maximum 3 sentences
- Use simple language
- End with: This is not financial advice.

Stock analysis context:
{req.context}

User question: {req.question}

Your answer:"""

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 200,
                "temperature": 0.4
            },
            timeout=30
        )

        if not response.ok:
            print(f"Groq error: {response.status_code} {response.text}")
            raise HTTPException(
                status_code=500,
                detail="AI service error. Try again."
            )

        data = response.json()

        # Safe extraction with full error logging
        if "choices" not in data:
            print(f"Unexpected Groq response: {data}")
            raise HTTPException(
                status_code=500,
                detail="Unexpected response from AI service"
            )

        answer = data["choices"][0]["message"]["content"].strip()

        if not answer:
            raise HTTPException(
                status_code=500,
                detail="Empty response from AI"
            )

        return {"answer": answer}

    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="AI service timed out. Try again."
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Ask error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Something went wrong. Try again."
        )