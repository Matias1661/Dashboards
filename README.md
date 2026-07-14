# Dashboards

Sistema personal de seguimiento de salud y entrenamiento. Un único dashboard HTML estático publicado en GitHub Pages, alimentado por datos que se actualizan automáticamente mediante GitHub Actions.

## Qué es

`training_dashboard.html` es el dashboard activo (el único). Consolida composición corporal (Renpho), entrenamiento (Hevy + histórico Jefit) y tensión arterial en una sola vista, con análisis generado bajo demanda.

URL pública: https://matias1661.github.io/Dashboards/training_dashboard.html

## Flujo de datos

```
Hevy API ─────────┐
Renpho (Notion) ───┼──> GitHub Actions ──> JSONs en el repo ──> training_dashboard.html
Notion (TA) ───────┘
```

Workflows programados (horarios en UTC):

| Workflow | Horarios | Fuente |
|---|---|---|
| `fetch_hevy.yml` | 05:00 y 21:00 | Hevy API |
| `fetch_renpho.yml` | 05:30 y 22:30 | Notion (datos Renpho) |
| `fetch_bp.yml` | 06:00 y 20:00 | Notion (base de datos TA) |

Cada workflow escribe su JSON correspondiente vía GitHub Contents API (PUT), no mediante `git push`, para evitar condiciones de carrera entre ejecuciones simultáneas.

## Archivos del repo

| Archivo | Contenido |
|---|---|
| `training_dashboard.html` | Dashboard único y activo |
| `hevy_data.json` | Entrenamientos desde Hevy (activo desde 25/05/2026) |
| `renpho_data.json` | Composición corporal (peso, músculo, grasa, agua, visceral) |
| `bp_data.json` | Tensión arterial y pulso |
| `jefit_data.json` | Histórico de entrenamientos de Jefit |

> **Importante:** `jefit_data.json` es un archivo estático e irremplazable (594 entrenamientos, mayo 2014–mayo 2026). La importación histórica a Hevy vía CSV falló, por lo que este es el único registro de esos datos. No borrar ni regenerar.
