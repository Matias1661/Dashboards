import os, json, urllib.request, base64

print("Python OK")
print("GH_TOKEN set:", bool(os.environ.get("GH_TOKEN")))
print("ANTHROPIC_API_KEY set:", bool(os.environ.get("ANTHROPIC_API_KEY")))

token = os.environ["GH_TOKEN"]
req = urllib.request.Request(
    "https://api.github.com/repos/Matias1661/Dashboards/contents/hevy_data.json",
    headers={"Authorization": f"token {token}"}
)
with urllib.request.urlopen(req) as r:
    data = json.loads(r.read())
    content = json.loads(base64.b64decode(data["content"]))
    print("hevy_data.json OK, workouts:", len(content.get("workouts", [])))

print("All checks passed")
