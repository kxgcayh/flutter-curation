#!/usr/bin/env python3
"""Fast repository checks (stdlib only). Run from anywhere: python3 tool/check.py"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_MANIFESTS = [
    ".claude-plugin/plugin.json",
    ".codex-plugin/plugin.json",
    ".cursor-plugin/plugin.json",
    ".antigravity-plugin/plugin.json",
]
OTHER_JSON = [".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json", ".agents/skills.json", "skills.sh.json"]
REQUIRED_METADATA = ["version", "docs-read", "docs-source", "validated-against"]
DOCS = ["README.md", "AGENTS.md", "CONTRIBUTING.md", "CHANGELOG.md", "CODE_OF_CONDUCT.md"]

errors = []


def error(msg):
    errors.append(msg)


def load_json(rel):
    try:
        return json.loads((ROOT / rel).read_text())
    except FileNotFoundError:
        error(f"{rel}: missing")
    except json.JSONDecodeError as e:
        error(f"{rel}: invalid JSON ({e})")
    return None


def front_matter(text):
    """Minimal YAML front matter parser: top-level `key: value` plus one nested map."""
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    data, parent = {}, None
    for line in m.group(1).splitlines():
        if not line.strip():
            continue
        nested = re.match(r"^  ([\w-]+):\s*(.*)$", line)
        top = re.match(r"^([\w-]+):\s*(.*)$", line)
        if nested and parent is not None:
            data[parent][nested.group(1)] = nested.group(2).strip().strip('"')
        elif top:
            key, value = top.group(1), top.group(2).strip()
            if value:
                data[key], parent = value.strip('"'), None
            else:
                data[key], parent = {}, key
    return data


def slug(heading):
    return re.sub(r"[^a-z0-9 _-]", "", heading.strip().lower()).replace(" ", "-")


def check_markdown(path):
    text = path.read_text()
    rel = path.relative_to(ROOT)
    if len(re.findall(r"(?m)^\s*```", text)) % 2:
        error(f"{rel}: unclosed code fence")
    prose = re.sub(r"(?ms)^\s*```.*?^\s*```", "", text)
    for target in re.findall(r"\]\(([^)\s]+)\)", prose):
        if re.match(r"^(https?:|mailto:|<)", target):
            continue
        file_part, _, anchor = target.partition("#")
        dest = (path.parent / file_part).resolve() if file_part else path
        if not dest.exists():
            error(f"{rel}: broken link {target}")
        elif anchor and dest.suffix == ".md":
            if anchor not in {slug(h) for h in re.findall(r"(?m)^#+ (.+)$", dest.read_text())}:
                error(f"{rel}: broken anchor {target}")


def main():
    manifests = {rel: load_json(rel) for rel in PLUGIN_MANIFESTS}
    for rel in OTHER_JSON:
        load_json(rel)

    valid = {k: v for k, v in manifests.items() if v}
    for field in ("name", "version", "license"):
        values = {rel: m.get(field) for rel, m in valid.items()}
        if len(set(values.values())) > 1:
            error(f"manifest '{field}' differs: {values}")
    version = next((m.get("version") for m in valid.values()), None)

    changelog = (ROOT / "CHANGELOG.md").read_text() if (ROOT / "CHANGELOG.md").exists() else ""
    if version and not re.search(rf"(?m)^## \[(?:{re.escape(version)}|Unreleased)\]", changelog):
        error(f"CHANGELOG.md: no '## [{version}]' or '## [Unreleased]' section for manifest version {version}")

    skills = sorted(p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md"))
    if not skills:
        error("skills/: no skills found")
    readme = (ROOT / "README.md").read_text()
    grouped = {s for g in (load_json("skills.sh.json") or {}).get("groupings", []) for s in g.get("skills", [])}

    for name in skills:
        path = ROOT / "skills" / name / "SKILL.md"
        fm = front_matter(path.read_text())
        rel = path.relative_to(ROOT)
        if fm is None:
            error(f"{rel}: missing front matter")
            continue
        if fm.get("name") != name:
            error(f"{rel}: front matter name '{fm.get('name')}' must match folder '{name}'")
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name):
            error(f"{rel}: folder name must be lowercase letters, digits and hyphens")
        desc = fm.get("description", "")
        if not desc:
            error(f"{rel}: missing description")
        elif len(desc) > 1024:
            error(f"{rel}: description is {len(desc)} characters (max 1024)")
        meta = fm.get("metadata") if isinstance(fm.get("metadata"), dict) else {}
        for key in REQUIRED_METADATA:
            if not meta.get(key):
                error(f"{rel}: metadata.{key} is missing")
        if meta.get("docs-read") and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", meta["docs-read"]):
            error(f"{rel}: metadata.docs-read must be YYYY-MM-DD")
        if f"](skills/{name}/SKILL.md)" not in readme:
            error(f"README.md: '{name}' missing from the Available skills table")
        if name not in grouped:
            error(f"skills.sh.json: '{name}' is not in any grouping")
        for md in sorted((ROOT / "skills" / name).rglob("*.md")):
            check_markdown(md)

    for unknown in sorted(grouped - set(skills)):
        error(f"skills.sh.json: lists '{unknown}', but skills/{unknown}/SKILL.md doesn't exist")
    for rel in DOCS:
        if (ROOT / rel).exists():
            check_markdown(ROOT / rel)

    if errors:
        print(f"{len(errors)} problem(s):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print(f"ok: {len(skills)} skill(s), {len(valid)} plugin manifests at version {version}")


if __name__ == "__main__":
    main()
