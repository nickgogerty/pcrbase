#!/usr/bin/env python3
"""Drift guard: every COMET target in map_comet.MAPPING must exist in the shared
registry vendored from comet-carbonsig. Run: python test/test_comet_mapping.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "comet"))

from map_comet import MAPPING, validate_mapping  # noqa: E402
from validate_curies import load_registry, is_valid  # noqa: E402

FAILS: list[str] = []


def check(name: str, cond: bool) -> None:
    print(("PASS" if cond else "FAIL") + f"  {name}")
    if not cond:
        FAILS.append(name)


def main() -> int:
    allow = load_registry()
    check("vendored registry present and non-trivial", len(allow) > 200)

    # No COMET target may be absent from the registry.
    invalid = validate_mapping()
    check(f"all COMET targets in registry (offenders: {invalid})", invalid == [])

    # The new PCR terms resolve to the comet-pcr extension namespace.
    for ck in ["id.operator", "cutoff.mass", "scenario.rsl", "alloc.cff", "lcia.ef_indicators"]:
        target = MAPPING[ck][0]
        check(f"{ck} -> comet-pcr ({target})", target.startswith("comet-pcr:"))

    # The three historical bugs are gone.
    targets = {t for (t, *_r) in MAPPING.values()}
    check("no comet-core: targets remain", not any(t.startswith("comet-core:") for t in targets))
    check("no bare comet:FunctionalUnit", "comet:FunctionalUnit" not in targets)
    check("biogenic uses correct case (comet-pcf:BiogenicCarbon)", "comet-pcf:BiogenicCarbon" in targets)

    # GeographyScope now points at the real L2 home.
    check("id.geography -> comet-ef:GeographyScope", MAPPING["id.geography"][0] == "comet-ef:GeographyScope")

    # Existing-COMET 'exact' targets really are exact registry members.
    for ck, (t, _k, status, _r) in MAPPING.items():
        if status == "exact" and t.split(":", 1)[0].startswith("comet"):
            check(f"exact target in registry: {ck} ({t})", is_valid(t, allow))

    print(f"\n{'ALL PASS' if not FAILS else str(len(FAILS)) + ' FAILED: ' + ', '.join(FAILS)}")
    return 0 if not FAILS else 1


if __name__ == "__main__":
    raise SystemExit(main())
