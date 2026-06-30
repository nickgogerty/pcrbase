#!/usr/bin/env python3
"""Python reference validator — checks COMET CURIEs against the shared registry.

Consumed by CarbonSigProductHub/pcrbase. Vendor `registry/comet-curies.json`
into the consumer (or point --registry at it) and call `validate_curies(...)`.

A CURIE is valid if it is an exact member of the registry, or (when
allow_property_base=True) its class base — the part before the first '.' in the
local name — is a member. The latter permits referencing a property of a known
class without enumerating every property.

CLI:
  python tools/validate_curies.py comet-pcf:FunctionalUnit comet-pcr:PCRDocument
  echo '["comet:Process","comet-bogus:X"]' | python tools/validate_curies.py -
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

DEFAULT_REGISTRY = Path(__file__).resolve().parent / "comet-registry.json"


def load_registry(path: Path | None = None) -> set[str]:
    p = path or DEFAULT_REGISTRY
    data = json.loads(Path(p).read_text())
    # Include all extension pending lists (comet_pcr_pending, comet_pj_pending, etc.)
    allow: set[str] = set(data["comet_published"]) | set(data["comet_pcr_pending"])
    for key, val in data.items():
        if key.endswith("_pending") and isinstance(val, list):
            allow.update(val)
    return allow


def class_base(curie: str) -> str:
    """comet-pcf:FunctionalUnit.referenceFlow -> comet-pcf:FunctionalUnit"""
    if ":" not in curie:
        return curie
    prefix, local = curie.split(":", 1)
    return f"{prefix}:{local.split('.', 1)[0]}"


def is_valid(curie: str, allow: set[str], allow_property_base: bool = True) -> bool:
    if curie in allow:
        return True
    if allow_property_base and class_base(curie) in allow:
        return True
    return False


def validate_curies(
    curies: list[str],
    allow: set[str] | None = None,
    allow_property_base: bool = True,
) -> dict[str, list[str]]:
    """Return {'valid': [...], 'invalid': [...]} (None CURIEs are ignored)."""
    allow = allow if allow is not None else load_registry()
    valid, invalid = [], []
    for c in curies:
        if c is None:
            continue
        (valid if is_valid(c, allow, allow_property_base) else invalid).append(c)
    return {"valid": valid, "invalid": invalid}


def main() -> int:
    args = sys.argv[1:]
    if args == ["-"]:
        curies = json.loads(sys.stdin.read())
    elif args:
        curies = args
    else:
        print("usage: validate_curies.py <curie> [curie ...] | -", file=sys.stderr)
        return 2

    result = validate_curies(curies)
    for c in result["valid"]:
        print(f"✓ {c}")
    for c in result["invalid"]:
        print(f"✗ {c}  (not in COMET registry)", file=sys.stderr)
    return 0 if not result["invalid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
