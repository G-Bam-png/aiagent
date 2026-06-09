import json
import httpx

B = "https://nexus-agents.onrender.com"
out = []
try:
    tok = httpx.post(B + "/api/auth/login",
                     json={"email": "demo@nexus.ai", "password": "demo12345"}, timeout=40).json()["token"]
    d = httpx.get(B + "/api/diag/llm", headers={"Authorization": f"Bearer {tok}"}, timeout=90).json()
    out.append("resolved_provider: " + str(d.get("resolved_provider")))
    out.append("openai_key_set: " + str(d.get("openai_key_set")))
    out.append("ok(any): " + str(d.get("ok")))
    out.append("providers: " + json.dumps(d.get("providers"), ensure_ascii=False, indent=1))
    out.append("effective_reply: " + str(d.get("effective_reply")))
except Exception as e:
    out.append(f"ERROR: {type(e).__name__}: {e}")
with open("scripts/check2_out.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("done")
