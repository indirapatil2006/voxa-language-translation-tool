import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("DEEPL_API_KEY")

if not api_key:
    print("ERROR: DeepL API key not found in .env")
    raise SystemExit(1)

# Select the correct endpoint for the key type
base_url = (
    "https://api-free.deepl.com"
    if api_key.endswith(":fx")
    else "https://api.deepl.com"
)

url = f"{base_url}/v2/translate"

headers = {
    "Authorization": f"DeepL-Auth-Key {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "text": ["Good morning"],
    "source_lang": "EN",
    "target_lang": "FR"
}

try:
    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=30
    )

    print("HTTP Status:", response.status_code)

    if response.ok:
        result = response.json()
        print("Translation:", result["translations"][0]["text"])
        print("DeepL connection successful!")
    else:
        print("API Error:", response.text)

except requests.RequestException as error:
    print("Connection failed:", error)
