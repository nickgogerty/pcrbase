#!/usr/bin/env python3
"""Refresh the vendored COMET registry + validator from the source of truth
(CarbonSigProductHub/comet-carbonsig). Requires the `gh` CLI (authenticated).

  python comet/sync_registry.py

The vendored copies are committed so tests/CI run offline; re-run this when
COMET or the comet-pcr extension changes.
"""
from __future__ import annotations

import base64
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC_REPO = "CarbonSigProductHub/comet-carbonsig"
FILES = {
    "registry/comet-curies.json": HERE / "comet-registry.json",
    "tools/validate_curies.py": HERE / "validate_curies.py",
}


def fetch(path: str) -> bytes:
    out = subprocess.run(
        ["gh", "api", f"repos/{SRC_REPO}/contents/{path}", "--jq", ".content"],
        capture_output=True, text=True, check=True,
    ).stdout
    return base64.b64decode(out)


def main() -> int:
    for src, dest in FILES.items():
        data = fetch(src)
        # Keep the local vendored-header + DEFAULT_REGISTRY patch on the validator:
        # only the registry JSON is overwritten verbatim; the validator is refreshed
        # but its DEFAULT_REGISTRY path is re-pointed at the sibling JSON.
        if dest.suffix == ".py":
            text = data.decode()
            text = text.replace(
                'Path(__file__).resolve().parent.parent / "registry" / "comet-curies.json"',
                'Path(__file__).resolve().parent / "comet-registry.json"',
            )
            dest.write_text(text)
        else:
            dest.write_bytes(data)
        print(f"synced {src} -> {dest.relative_to(HERE.parent)}")
    counts = json.loads((HERE / "comet-registry.json").read_text())["counts"]
    print(f"registry counts: {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
