import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("BHASINI_API_KEY")

if not api_key:
    print("ERROR: API key not found. Check your .env file.")
    raise SystemExit(1)

url = "https://mcp.bhasini.com/v1/translate"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "text": "How are you?",
    "source": "en",
    "target": "hi"
}

try:
    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=30
    )

    print("HTTP Status:", response.status_code)
    print("API Response:", response.text)

    response.raise_for_status()

    result = response.json()
    print("\nTranslated text:", result.get("translation"))
    print("Credits remaining:", result.get("creditsLeft"))

except requests.RequestException as error:
    print("API connection failed:", error)

except ValueError:
    print("The API returned an invalid JSON response.")
