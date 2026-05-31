#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from urllib.request import urlopen


SOURCE_URL = "https://github.com/itdoginfo/allow-domains/raw/refs/heads/main/Categories/geoblock.lst"
EXCLUDED_DOMAINS = {"usher.ttvnw.net", "gql.twitch.tv"}
OUTPUT_LIST = "geoblock.lst"
OUTPUT_JSON = "geoblock.json"
OUTPUT_SRS = "geoblock.srs"


def fetch_source(url: str) -> str:
    with urlopen(url, timeout=60) as response:
        return response.read().decode("utf-8")


def build_domains(source_text: str) -> list[str]:
    domains: list[str] = []
    previous_blank = False

    for raw_line in source_text.splitlines():
        line = raw_line.strip()
        if not line:
            if domains and not previous_blank:
                domains.append("")
                previous_blank = True
            continue

        if line in EXCLUDED_DOMAINS:
            continue

        domains.append(line)
        previous_blank = False

    while domains and domains[-1] == "":
        domains.pop()

    return domains


def write_list_file(path: Path, domains: list[str]) -> None:
    path.write_text("\n".join(domains) + "\n", encoding="utf-8")


def write_json_file(path: Path, domains: list[str]) -> None:
    rule_domains = [domain for domain in domains if domain]
    payload = {
        "version": 3,
        "rules": [
            {
                "domain_suffix": rule_domains,
            }
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def compile_rule_set(repo_root: Path, json_path: Path, output_path: Path) -> None:
    sing_box = os.environ.get("SING_BOX") or shutil.which("sing-box")
    if not sing_box:
        raise RuntimeError("sing-box binary not found. Set SING_BOX or add sing-box to PATH.")

    subprocess.run(
        [sing_box, "rule-set", "compile", "--output", str(output_path), str(json_path)],
        cwd=repo_root,
        check=True,
    )


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    source_text = fetch_source(SOURCE_URL)
    domains = build_domains(source_text)

    write_list_file(repo_root / OUTPUT_LIST, domains)
    write_json_file(repo_root / OUTPUT_JSON, domains)
    compile_rule_set(repo_root, repo_root / OUTPUT_JSON, repo_root / OUTPUT_SRS)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())