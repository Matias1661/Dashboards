import os, json, urllib.request, urllib.error

print("Testing Anthropic API connectivity...")
api_key = os.environ.get("ANTHROPIC_API_KEY", "")
print("Key length:", len(api_key))

payload = json.dumps({
    "model": "claude-haiku-20240307",
    "max_tokens": 10,
    "messages": [{"role": "user", "content": "Say hi"}]
}).encode()

req = urllib.request.Request(
    "https://api.anthropic.com/v1/messages",
    data=payload, method="POST",
    headers={
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
)
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())
        print("API response:", data["content"][0]["text"])
        print("Anthropic API: REACHABLE")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"HTTP {e.code}: {body[:300]}")
except Exception as e:
    print(f"Connection error: {type(e).__name__}: {e}")
