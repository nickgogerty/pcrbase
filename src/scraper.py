"""Lightweight web scraper helpers for PCRbase research.
Firecrawl key in ~/.hermes/.env is CORRUPTED (contains 'npx -y fir...' not an
fc- token), so we use:
  1. Jina AI Reader (r.jina.ai) — free, no-auth, JS-rendering, returns markdown
  2. plain requests fallback for static pages
No API key required.
"""
import requests, time, urllib.parse

UA = {"User-Agent": "Mozilla/5.0 (PCRbase research)"}

def jina(url, timeout=45, tries=3):
    """Fetch a URL via Jina Reader -> markdown. Handles JS-rendered pages."""
    target = "https://r.jina.ai/" + url
    for i in range(tries):
        try:
            r = requests.get(target, headers=UA, timeout=timeout)
            if r.status_code == 200 and len(r.text) > 50:
                return r.text
        except requests.RequestException:
            pass
        time.sleep(2 * (i + 1))
    return None

def jina_search(query, timeout=45):
    """Jina search endpoint (s.jina.ai) -> markdown list of results. No auth."""
    url = "https://s.jina.ai/" + urllib.parse.quote(query)
    try:
        r = requests.get(url, headers=UA, timeout=timeout)
        if r.status_code == 200:
            return r.text
    except requests.RequestException:
        pass
    return None

def plain(url, timeout=30):
    try:
        r = requests.get(url, headers=UA, timeout=timeout)
        if r.status_code == 200:
            return r.text
    except requests.RequestException:
        pass
    return None

if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "jina"
    arg = sys.argv[2] if len(sys.argv) > 2 else "https://example.com"
    fn = {"jina": jina, "search": jina_search, "plain": plain}[mode]
    out = fn(arg)
    print(out[:2000] if out else "FAILED")
