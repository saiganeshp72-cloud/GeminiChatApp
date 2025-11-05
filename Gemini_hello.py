
# hello_world/Gemini_hello.py
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

resp = client.models.generate_content(
    model="gemini-2.5-pro",
    contents=["Say hi in one short sentence."]
)

print(resp.text)



