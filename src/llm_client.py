"""Anthropic LLM client for PCRbase extraction — Haiku 4.5 for cost.

Auth: uses the Hermes credential pool OAuth token (~/.hermes/auth.json,
provider 'anthropic'), with the oauth beta header. No raw API key is present on
this machine; OAuth subscription tokens expose claude-haiku-4-5. Picks the
highest-priority entry with last_status=='ok' and a non-expired access_token.

If you later add a raw ANTHROPIC_API_KEY env var, it takes precedence (simpler).
"""
import os, json, time, urllib.request, urllib.error

MODEL = "claude-haiku-4-5"
AUTH_JSON = os.path.expanduser("~/.hermes/auth.json")
API_URL = "https://api.anthropic.com/v1/messages"


def _load_oauth_token():
    """Return a usable anthropic OAuth access_token from the Hermes pool."""
    with open(AUTH_JSON) as f:
        auth = json.load(f)
    pool = auth.get("credential_pool", {}).get("anthropic", [])
    now_ms = time.time() * 1000
    candidates = [e for e in pool
                  if e.get("access_token")
                  and e.get("last_status") == "ok"
                  and (e.get("expires_at_ms") or 0) > now_ms + 60_000]
    candidates.sort(key=lambda e: e.get("priority", 999))
    if not candidates:
        # fall back to any entry with a token (may be expired; will error clearly)
        candidates = [e for e in pool if e.get("access_token")]
    if not candidates:
        raise RuntimeError("No usable anthropic OAuth token in ~/.hermes/auth.json")
    return candidates[0]["access_token"]


def _headers():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        return {"x-api-key": api_key, "anthropic-version": "2023-06-01",
                "content-type": "application/json"}
    tok = _load_oauth_token()
    return {"authorization": f"Bearer {tok}", "anthropic-version": "2023-06-01",
            "anthropic-beta": "oauth-2025-04-20", "content-type": "application/json"}


def call(messages, system=None, max_tokens=1500, temperature=0, model=MODEL, tries=4):
    body = {"model": model, "max_tokens": max_tokens, "temperature": temperature,
            "messages": messages}
    if system:
        body["system"] = system
    data = json.dumps(body).encode()
    last_err = None
    for i in range(tries):
        try:
            req = urllib.request.Request(API_URL, data=data, method="POST")
            for k, v in _headers().items():
                req.add_header(k, v)
            with urllib.request.urlopen(req, timeout=90) as r:
                d = json.load(r)
            return "".join(b.get("text", "") for b in d.get("content", []))
        except urllib.error.HTTPError as ex:
            last_err = f"HTTP {ex.code}: {ex.read().decode()[:200]}"
            if ex.code in (429, 500, 502, 503, 529):
                time.sleep(2 * (i + 1)); continue
            break
        except (urllib.error.URLError, TimeoutError) as ex:
            last_err = str(ex); time.sleep(2 * (i + 1))
    raise RuntimeError(f"LLM call failed: {last_err}")


if __name__ == "__main__":
    print(call([{"role": "user", "content": "Reply with exactly: PCRBASE_LLM_OK"}], max_tokens=20))
