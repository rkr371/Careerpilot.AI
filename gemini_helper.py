import google.generativeai as genai
import os
import threading
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")


def _generate_with_timeout(prompt: str, timeout_seconds: int = 30):
    """Runs Gemini generation in a worker thread and returns text or raises TimeoutError."""
    result = {"text": None, "error": None}

    def worker():
        try:
            response = model.generate_content(prompt)
            result["text"] = getattr(response, "text", None)
        except Exception as e:
            result["error"] = e

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    t.join(timeout_seconds)

    if t.is_alive():
        raise TimeoutError(f"Gemini request timed out after {timeout_seconds}s")

    if result["error"] is not None:
        raise result["error"]

    return result["text"]


def ask_gemini(prompt):
    """Calls Gemini and returns generated text.

    This function never raises; it returns a user-friendly error string.
    """
    # Prevent the Flask request from hanging forever
    timeout_seconds = int(os.getenv("GEMINI_TIMEOUT_SECONDS", "30"))

    # One retry for transient failures
    for attempt in range(2):
        try:
            # Logging before Gemini generation
            print(f"[GeminiHelper] Prompt generated successfully. chars={len(prompt or '')}")

            text = _generate_with_timeout(prompt, timeout_seconds=timeout_seconds)

            # Logging after Gemini generation
            print("[GeminiHelper] Gemini request sent")
            print(f"[GeminiHelper] Gemini response received. chars={(len(text) if text else 0)}")

            if not text or not str(text).strip():
                return (
                    "Gemini returned an empty response. "
                    "Please check the API key/model access and try again."
                )
            return text
        except TimeoutError:
            if attempt == 0:
                continue
            return (
                "Gemini request timed out. "
                "Please try again in a moment (or shorten input)."
            )
        except Exception as e:
            if attempt == 0:
                continue
            # User-friendly error
            return (
                "Gemini request failed due to an internal error. "
                "Please try again later."
            )


