#!/usr/bin/env python3
"""Compile every Dart code block in a skill against the packages pub resolves.

Usage: python3 tool/validate/run.py [skill ...]   (default: every skill with a
tool/validate/<skill>/extract.py). Uses the `flutter` and `dart` on PATH.

For each skill it runs `flutter pub get`, extracts the snippets, runs
build_runner and `dart analyze`, then the smoke tests listed in validate.json.
Analyzer errors in a fixture listed under "requires" are expected (and
ignored) when the resolved package is older than "min". validate.json
"commands" run after the tests, when the resolved package is at least "min";
with "stale_file", that file is edited first and the command must fail
without rewriting it.
A skill whose extract.py writes cases/<name>/ projects (build-runner) gets
each case built with build_runner (failing on warnings not matched by
"allowed_warnings") and analyzed.
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

    for command in config.get("commands", []):
        have = versions.get(command["package"]) or resolved(lock, command["package"])
        if not have or version_tuple(have) < version_tuple(command["min"]):
            print(f"skipped   {' '.join(command['cmd'])}  (needs {command['package']} {command['min']}; resolved {have})")
            continue
        stale = skill_dir / command["stale_file"] if command.get("stale_file") else None
        original = stale.read_bytes() if stale else None
        if stale:
            # Make one output stale; the command must fail and must not rewrite it.
            stale.write_bytes(original + b"\n// stale edit\n")
            mutated = stale.read_bytes()
        try:
            r = run(command["cmd"], skill_dir)
            passed = (r.returncode != 0) if stale else (r.returncode == 0)
            if stale and stale.read_bytes() != mutated:
                print(f"changed   {command['stale_file']} was rewritten")
                passed = False
        finally:
            if stale:
                stale.write_bytes(original)
        if passed:
            print(f"ok        {command['reason']}")
        else:
            print(f"FAILED    {command['reason']} (exit {r.returncode})\n{r.stdout[-3000:]}{r.stderr[-2000:]}")
            fail = True

    for case in sorted((skill_dir / "cases").glob("*/")):
        fail |= not build_case(case, config)

    print(f"{skill_dir.name}: {'FAILED' if fail else 'ok'}")
    return not fail


def build_case(case, config):
    """Build one cases/<name>/ project and analyze it; warnings fail unless allowed."""
    if run(["flutter", "pub", "get", "--offline"], case).returncode:
        r = run(["flutter", "pub", "get"], case)
        if r.returncode:
            print(r.stdout[-2000:], r.stderr[-2000:])
            return False
    r = run(["dart", "run", "build_runner", "build"], case)
    out = r.stdout + r.stderr
    # A warning is its `W ` line plus the indented lines up to the next status line.
    warnings = re.findall(r"(?ms)^W .*?(?=^(?:[WE] |  \d+s |  Built|  Failed)|\Z)", out)
    unexpected = [w for w in warnings if not any(a in w for a in config.get("allowed_warnings", []))]
    ok = r.returncode == 0 and not unexpected
    for w in unexpected:
        print(f"warning   {case.name}: {w.strip()}")
    if r.returncode:
        print(out[-3000:])
    a = run(["dart", "analyze", "--format", "machine", "lib"], case)
    reported = False
    for line in (a.stdout + a.stderr).splitlines():
        parts = line.split("|")
        if len(parts) >= 8 and parts[0] in ("ERROR", "WARNING"):
            print(f"{parts[0]:7}   {case.name}: {Path(parts[3]).name}:{parts[4]}  {parts[7]}")
            ok, reported = False, True
    # A non-zero exit with no parsed ERROR/WARNING (e.g. an analyzer crash) must fail too.
    if a.returncode and not reported:
        print(f"analyze   {case.name}: exit {a.returncode}\n{(a.stdout + a.stderr)[-2000:]}")
        ok = False
    print(f"case      {case.name}: {'ok' if ok else 'FAILED'}")
    return ok


def main():
    skills = sys.argv[1:] or sorted(p.parent.name for p in HERE.glob("*/extract.py"))
    results = [validate(HERE / s) for s in skills]
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
