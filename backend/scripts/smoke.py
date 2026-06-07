"""Quick UTF-8-clean check of API replies (console-encoding-independent)."""
import json
import httpx

B = "http://localhost:8000"
out = []

tpls = httpx.get(f"{B}/api/catalog/templates").json()
out.append(f"templates: {len(tpls)} | first: {tpls[0]['name']} / {tpls[0]['tagline']}")

tok = httpx.post(f"{B}/api/auth/login", json={"email": "demo@nexus.ai", "password": "demo12345"}).json()["token"]
H = {"Authorization": f"Bearer {tok}"}

agents = httpx.get(f"{B}/api/agents", headers=H).json()
a = agents[0]
out.append(f"agent: {a['name']} | {a['description']}")

for msg in ["Привет!", "Сколько стоит ноутбук?", "Доставите в Казань?", "Хочу оператора, жалоба"]:
    r = httpx.post(f"{B}/api/agents/{a['id']}/playground", json={"message": msg}, headers=H).json()
    out.append(f"Q: {msg}\n   A: {r['reply']}\n   needs_human={r['needs_human']}")

with open("scripts/smoke_out.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("written")
