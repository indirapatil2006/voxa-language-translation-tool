
import os
import sqlite3
import logging
from datetime import datetime

import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify

load_dotenv()

app = Flask(__name__)
app.logger.setLevel(logging.INFO)

# API configuration
BHASINI_API_URL = "https://mcp.bhasini.com/v1/translate"
BHASINI_API_KEY = os.getenv("BHASINI_API_KEY")
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")

DEEPL_BASE_URL = (
    "https://api-free.deepl.com"
    if DEEPL_API_KEY and DEEPL_API_KEY.endswith(":fx")
    else "https://api.deepl.com"
)

DEEPL_API_URL = f"{DEEPL_BASE_URL}/v2/translate"

DATABASE = "voxa_history.db"

# Supported language codes
INDIAN_LANGUAGES = {"en", "hi", "kn", "mr"}

DEEPL_LANGUAGES = {
    "en": "EN",
    "fr": "FR",
    "es": "ES",
    "de": "DE",
    "ja": "JA"
}

SUPPORTED_LANGUAGES = {
    "en", "hi", "kn", "mr",
    "fr", "es", "de", "ja"
}


# ---------------- DATABASE ----------------

def init_db():
    connection = sqlite3.connect(DATABASE)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS translations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_text TEXT NOT NULL,
            translated_text TEXT NOT NULL,
            source_language TEXT NOT NULL,
            target_language TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


def save_translation(text, translation, source, target):
    connection = sqlite3.connect(DATABASE)

    cursor = connection.execute("""
        INSERT INTO translations (
            source_text,
            translated_text,
            source_language,
            target_language,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        text,
        translation,
        source,
        target,
        datetime.now().strftime("%d %b %Y, %I:%M %p")
    ))

    translation_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return translation_id


# ---------------- BHASINI TRANSLATION ----------------

def translate_with_bhasini(text, source, target):
    if not BHASINI_API_KEY:
        raise RuntimeError("Bhasini API key is missing.")

    headers = {
        "Authorization": f"Bearer {BHASINI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "text": text,
        "source": source,
        "target": target
    }

    response = requests.post(
        BHASINI_API_URL,
        headers=headers,
        json=payload,
        timeout=30
    )

    response.raise_for_status()

    result = response.json()
    translation = result.get("translation")

    if not translation:
        raise RuntimeError("Bhasini returned an empty translation.")

    return translation


# ---------------- DEEPL TRANSLATION ----------------

def translate_with_deepl(text, source, target):
    if not DEEPL_API_KEY:
        raise RuntimeError("DeepL API key is missing.")

    headers = {
        "Authorization": f"DeepL-Auth-Key {DEEPL_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "text": [text],
        "target_lang": DEEPL_LANGUAGES[target]
    }

    # DeepL can detect the source language automatically.
    # Explicit source language is useful when known.
    if source != "auto":
        payload["source_lang"] = DEEPL_LANGUAGES[source]

    response = requests.post(
        DEEPL_API_URL,
        headers=headers,
        json=payload,
        timeout=30
    )

    response.raise_for_status()

    result = response.json()
    translations = result.get("translations", [])

    if not translations or not translations[0].get("text"):
        raise RuntimeError("DeepL returned an empty translation.")

    return translations[0]["text"]


# ---------------- SMART TRANSLATION ROUTING ----------------

def translate_text(text, source, target):

    if source == target:
        return text

    source_is_indian = source in INDIAN_LANGUAGES
    target_is_indian = target in INDIAN_LANGUAGES

    # Both languages belong to the Indian-language group.
    if source_is_indian and target_is_indian:
        return translate_with_bhasini(text, source, target)

    # Both languages belong to the DeepL group.
    if not source_is_indian and not target_is_indian:
        return translate_with_deepl(text, source, target)

    # Mixed groups: use English as an intermediate language.
    if source_is_indian:
        english_text = translate_with_bhasini(
            text, source, "en"
        )

        return translate_with_deepl(
            english_text, "en", target
        )

    else:
        english_text = translate_with_deepl(
            text, source, "en"
        )

        return translate_with_bhasini(
            english_text, "en", target
        )


# ---------------- HOME PAGE ----------------

@app.route("/")
def home():
    return render_template("index.html")


# ---------------- TRANSLATION ENDPOINT ----------------

@app.route("/translate", methods=["POST"])
def translate():
    try:
        data = request.get_json(silent=True) or {}

        text = (data.get("text") or "").strip()
        source = data.get("source")
        target = data.get("target")

        if not text:
            return jsonify({
                "error": "Please enter some text."
            }), 400

        if not isinstance(source, str) or not isinstance(target, str):
            return jsonify({
                "error": "Please select both languages."
            }), 400

        if source not in SUPPORTED_LANGUAGES or target not in SUPPORTED_LANGUAGES:
            return jsonify({
                "error": "Please select supported languages."
            }), 400

        if len(text) > 5000:
            return jsonify({
                "error": "Please keep your text within 5000 characters."
            }), 400

        translated_text = translate_text(text, source, target)

        history_id = save_translation(
            text,
            translated_text,
            source,
            target
        )

        return jsonify({
            "translation": translated_text,
            "history_id": history_id
        })

    except requests.Timeout:
        return jsonify({
            "error": "Translation timed out. Please try again."
        }), 504

    except requests.HTTPError as error:
        status = error.response.status_code if error.response is not None else 502

        app.logger.error("Translation API HTTP error: %s", status)

        return jsonify({
            "error": "The translation provider rejected the request. Please check your language pair or API quota."
        }), 502

    except requests.RequestException:
        app.logger.exception("Translation API connection error")

        return jsonify({
            "error": "Could not connect to the translation service. Check your internet connection."
        }), 502

    except RuntimeError as error:
        app.logger.error("Translation configuration error: %s", error)

        return jsonify({
            "error": "Translation service configuration problem. Check your API keys."
        }), 500

    except Exception:
        app.logger.exception("Unexpected translation error")

        return jsonify({
            "error": "Something went wrong. Please try again."
        }), 500


# ---------------- TRANSLATION HISTORY ----------------

@app.route("/history", methods=["GET"])
def get_history():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    rows = connection.execute("""
        SELECT *
        FROM translations
        ORDER BY id DESC
    """).fetchall()

    connection.close()

    return jsonify({
        "history": [dict(row) for row in rows]
    })


@app.route("/history/<int:translation_id>", methods=["DELETE"])
def delete_history_item(translation_id):
    connection = sqlite3.connect(DATABASE)

    cursor = connection.execute(
        "DELETE FROM translations WHERE id = ?",
        (translation_id,)
    )

    connection.commit()
    deleted = cursor.rowcount
    connection.close()

    if deleted == 0:
        return jsonify({
            "error": "History entry not found."
        }), 404

    return jsonify({
        "message": "Translation deleted successfully."
    })


@app.route("/history/clear", methods=["DELETE"])
def clear_history():
    connection = sqlite3.connect(DATABASE)

    connection.execute("DELETE FROM translations")

    connection.commit()
    connection.close()

    return jsonify({
        "message": "Translation history cleared."
    })


# ---------------- RUN APPLICATION ----------------

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
