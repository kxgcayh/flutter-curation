#!/usr/bin/env python3
"""Compile every Dart code block in a skill against the packages pub resolves.

Usage: python3 tool/validate/run.py [skill ...]   (default: every skill with a
tool/validate/<skill>/extract.py). Uses the `flutter` and `dart` on PATH.

For each skill it runs `flutter pub get`, extracts the snippets, runs
build_runner and `dart analyze`, then the smoke tests listed in validate.json.
Analyzer errors in a fixture listed under "requires" are expected (and
ignored) when the resolved package is older than "min".
"""
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run(cmd, cwd):
    print(f"$ {' '.join(cmd)}", flush=True)
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def version_tuple(v):
    return tuple(int(x) for x in re.findall(r"\d+", v.split("+")[0].split("-")[0])[:3])


def resolved(lock_text, package):
    m = re.search(rf"\n  {re.escape(package)}:\n(?:    .*\n)*?    version: \"([^\"]+)\"", lock_text)
    return m.group(1) if m else None


def validate(skill_dir):
    config = json.loads((skill_dir / "validate.json").read_text())

    steps = [["flutter", "pub", "get"], ["python3", "extract.py"]]
    if re.search(r"(?m)^\s+build_runner:", (skill_dir / "pubspec.yaml").read_text()):
        steps.append(["dart", "run", "build_runner", "build"])
    pubspec = skill_dir / "pubspec.yaml"
    original_pubspec = pubspec.read_text()
    try:
        r = run(steps[0], skill_dir)
        if r.returncode:
            print(r.stdout[-4000:], r.stderr[-4000:])
            return False
        # Packages that only resolve on newer SDKs; skipped quietly when they don't.
        for package in config.get("optional_dependencies", []):
            added = run(["flutter", "pub", "add", package], skill_dir).returncode == 0
            print(f"optional  {package}: {'added' if added else 'not available on this SDK'}")
        for cmd in steps[1:]:
            r = run(cmd, skill_dir)
            if r.returncode:
                print(r.stdout[-4000:], r.stderr[-4000:])
                return False
            if cmd[1] == "extract.py":
                print(r.stdout.strip())
        return analyze_and_test(skill_dir, config)
    finally:
        pubspec.write_text(original_pubspec)


def analyze_and_test(skill_dir, config):
    fail = False

    lock = (skill_dir / "pubspec.lock").read_text()
    report = config.get("report", ["riverpod", "flutter_riverpod", "riverpod_generator", "riverpod_annotation"])
    versions = {p: resolved(lock, p) for p in report}
    print("resolved:", ", ".join(f"{k} {v}" for k, v in versions.items()))

    r = run(["dart", "analyze", "--format", "machine"], skill_dir)
    issues = [line.split("|") for line in (r.stdout + r.stderr).splitlines() if line.count("|") >= 7]
    for parts in issues:
        severity, path, line, message = parts[0], parts[3], parts[4], parts[7]
        rel = str(Path(path).resolve().relative_to(skill_dir)) if path.startswith("/") else path
        req = config.get("requires", {}).get(rel)
        if req and versions.get(req["package"]) and version_tuple(versions[req["package"]]) < version_tuple(req["min"]):
            print(f"expected  {rel}:{line}  ({req['reason']}; resolved {req['package']} {versions[req['package']]})")
            continue
        print(f"{severity:7}   {rel}:{line}  {message}")
        if severity in ("ERROR", "WARNING"):
            fail = True

    tests = config.get("smoke_tests", [])
    if tests:
        r = run(["flutter", "test", *tests], skill_dir)
        print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-2000:])
        fail |= r.returncode != 0

    print(f"{skill_dir.name}: {'FAILED' if fail else 'ok'}")
    return not fail


def main():
    skills = sys.argv[1:] or sorted(p.parent.name for p in HERE.glob("*/extract.py"))
    results = [validate(HERE / s) for s in skills]
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
