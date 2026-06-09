import json, urllib.request, urllib.error, base64, re, time, os
from datetime import datetime, timezone

REPO        = "Matias1661/Dashboards"
GH_TOKEN    = os.environ["GH_TOKEN"]
ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]

def gh_get(path):
    req = urllib.request.Request(
        "https://api.github.com/repos/" + REPO + "/contents/" + path,
        headers={"Authorization": "token " + GH_TOKEN, "Accept": "application/vnd.github+json"}
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def gh_put(path, content_bytes, sha, message):
    payload = json.dumps({
        "message": message,
        "content": base64.b64encode(content_bytes).decode(),
        "sha": sha
    }).encode()
    for attempt in range(5):
        try:
            req = urllib.request.Request(
                "https://api.github.com/repos/" + REPO + "/contents/" + path,
                data=payload, method="PUT",
                headers={"Authorization": "token " + GH_TOKEN, "Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if attempt == 4: raise
            time.sleep(2 ** attempt)

# Fetch data
renpho = json.loads(base64.b64decode(gh_get("renpho_data.json")["content"]))
hevy   = json.loads(base64.b64decode(gh_get("hevy_data.json")["content"]))
bp     = json.loads(base64.b64decode(gh_get("bp_data.json")["content"]))

# Summaries
measurements = renpho.get("measurements", [])
last8 = measurements[-8:] if len(measurements) >= 8 else measurements
renpho_summary = [
    {"date": r["date"], "weight": r["weight"],
     "skeletal_muscle": round(r["skeletal_muscle"], 2),
     "body_fat": r["body_fat"], "visceral_fat": r["visceral_fat"]}
    for r in last8
]

workouts = hevy.get("workouts", [])
hevy_summary = []
for w in workouts[-8:]:
    vol = sum(
        (s.get("weight_kg") or 0) * (s.get("reps") or 0)
        for ex in w.get("exercises", [])
        for s in ex.get("sets", [])
        if s.get("type") != "warmup"
    )
    hevy_summary.append({
        "date": w["start_time"][:10],
        "title": w.get("title", ""),
        "volume_kg": round(vol),
        "sets": sum(1 for ex in w.get("exercises", [])
                    for s in ex.get("sets", []) if s.get("type") != "warmup")
    })

bp_nocafe = [r for r in bp.get("readings", []) if r.get("tipo") == "nocafe"][-10:]

cycle_start = "2026-03-23"
tamo_start  = "2026-05-14"
today_utc   = datetime.now(timezone.utc)
today_str   = today_utc.strftime("%-d %b %Y")

# Build prompt using string concatenation to avoid f-string/JSON conflicts
prompt = (
    "Eres el agente de analisis del Plan Karat, ciclo de 20 semanas iniciado el " + cycle_start + ".\n\n"
    "PROTOCOLO ACTIVO: Sem 11+: Testo 3cm/sem + Masteron 1cm/sem + Tamoxifeno. "
    "Sem 14-16: Testo + Tamoxifeno. PCT Sem 17-19: HCG + SERMs.\n"
    "Tamoxifeno iniciado: " + tamo_start + "\n"
    "Baseline ciclo: peso 86.20 kg / musculo 59.22 kg / GC 27.7%\n\n"
    "DATOS RENPHO (ultimas mediciones):\n" + json.dumps(renpho_summary) + "\n\n"
    "DATOS HEVY (ultimas sesiones, volumen excluye warmup):\n" + json.dumps(hevy_summary) + "\n\n"
    "TENSION ARTERIAL nocafe (ultimas lecturas):\n" + json.dumps(bp_nocafe) + "\n\n"
    "Genera un analisis conciso en HTML puro (sin etiquetas html/body/head).\n"
    "Estructura exacta:\n\n"
    '<p style="font-weight:600;color:var(--text);margin-bottom:10px">Semana XX - ' + today_str + '</p>\n\n'
    '<p style="margin-bottom:10px"><span style="font-weight:600;color:var(--text);border-bottom:1px solid var(--border2);display:inline-block;margin-bottom:3px">Composicion corporal</span><br>\n'
    "[analisis composicion: ultimas metricas, deltas vs baseline, tendencia]</p>\n\n"
    '<p style="margin-bottom:10px"><span style="font-weight:600;color:var(--text);border-bottom:1px solid var(--border2);display:inline-block;margin-bottom:3px">Entrenamiento</span><br>\n'
    "[analisis entrenamiento: volumen, frecuencia, tendencia]</p>\n\n"
    '<p style="margin-bottom:10px"><span style="font-weight:600;color:var(--text);border-bottom:1px solid var(--border2);display:inline-block;margin-bottom:3px">Tension arterial</span><br>\n'
    "[analisis TA: media reciente, tendencia, alertas si sistolica nocafe >130 sostenida]</p>\n\n"
    '<p style="margin-bottom:6px"><span style="font-weight:600;color:var(--text);border-bottom:1px solid var(--border2);display:inline-block;margin-bottom:3px">Recomendaciones</span><br>\n'
    "1. [accion concreta]<br>\n2. [accion concreta]<br>\n3. [accion concreta]<br>\n4. [accion concreta]</p>\n\n"
    '<p style="margin-bottom:0;padding-top:8px;border-top:1px solid var(--border2);color:var(--text3);font-size:11px">'
    'Para actualizar este analisis, escribe <strong style="color:var(--text2)">Analizar Dashboard</strong> en el chat con Claude.</p>\n\n'
    "Reglas:\n"
    "- Solo HTML puro, sin markdown ni bloques de codigo\n"
    "- Datos concretos (cifras, fechas), sin frases genericas\n"
    "- Calcula semana del ciclo desde " + cycle_start + " hasta hoy\n"
    "- Deltas siempre vs baseline indicado arriba\n"
    "- Tono directo, sin emojis\n"
)

# Call Anthropic API — build payload separately to avoid encoding issues
api_payload = json.dumps({
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 1500,
    "messages": [{"role": "user", "content": prompt}]
}, ensure_ascii=False).encode("utf-8")

api_req = urllib.request.Request(
    "https://api.anthropic.com/v1/messages",
    data=api_payload, method="POST",
    headers={
        "x-api-key": ANTHROPIC_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json; charset=utf-8"
    }
)
try:
    with urllib.request.urlopen(api_req) as r:
        api_resp = json.loads(r.read())
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8", errors="replace")
    print("Anthropic API error", e.code, ":", body[:500])
    raise

analysis_html = api_resp["content"][0]["text"].strip()

# Inject into dashboard
dash_resp = gh_get("plan_karat_dashboard.html")
dash_sha  = dash_resp["sha"]
dash_html = base64.b64decode(dash_resp["content"]).decode("utf-8")

date_str = today_utc.strftime("%-d %b %Y").lower()
months = {"jan":"ene","feb":"feb","mar":"mar","apr":"abr","may":"may",
          "jun":"jun","jul":"jul","aug":"ago","sep":"sep","oct":"oct",
          "nov":"nov","dec":"dic"}
for en, es in months.items():
    date_str = date_str.replace(en, es)
date_label = "Actualizado: " + date_str

dash_html = re.sub(
    r'(<span[^>]*id="claudeAnalysisDate"[^>]*>)[^<]*(</span>)',
    r'\g<1>' + date_label + r'\g<2>',
    dash_html
)
dash_html = re.sub(
    r'(<div[^>]*id="claudeAnalysisBody"[^>]*>).*?(</div>)',
    lambda m: m.group(1) + analysis_html + m.group(2),
    dash_html,
    flags=re.DOTALL
)

gh_put(
    "plan_karat_dashboard.html",
    dash_html.encode("utf-8"),
    dash_sha,
    "Auto-analisis dashboard " + date_label + " [skip ci]"
)
print("Done. Injected analysis dated: " + date_label)
