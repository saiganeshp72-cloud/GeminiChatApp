import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

print("genai:", genai.__version__)
print("client using:", client._api_version if hasattr(client, "_api_version") else "v1beta (implicit)")
print("Models visible to this key:")
for m in client.models.list():
    print("-", m.name)
