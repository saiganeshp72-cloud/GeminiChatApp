# hello_world/chat.py
# hello_world/chatApp.py
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

MODEL = "models/gemini-2.5-pro"   # or "models/gemini-2.5-flash"

print("Chat with Gemini. Type 'exit' to quit.\n")

history = []  # list of {"role": "user"|"model", "parts": [{"text": "..."}]}

try:
    while True:
        user = input("You: ").strip()
        if not user:
            continue
        if user.lower() in {"exit", "quit"}:
            break

        # Add user turn (parts must be dicts)
        history.append({"role": "user", "parts": [{"text": user}]})

        # Send full history
        resp = client.models.generate_content(
            model=MODEL,
            contents=history
        )

        answer = (resp.text or "").strip()
        print("Gemini:", answer, "\n")

        # Add model turn
        history.append({"role": "model", "parts": [{"text": answer}]})

except KeyboardInterrupt:
    print("\nExiting...")
