"""Turn the build.yaml blocks of skills/build-runner into build cases.

Every ```yaml block that starts with `targets:` or `global_options:` becomes
cases/<reference>__<n>/: a copy of this fixture (pubspec.yaml and lib/) with the
block as its build.yaml. run.py builds each case, fails on unexpected build_runner
warnings, and analyzes the result. validate.json "case_files" replaces fixture
files in a case with a ```dart block of the skill (e.g. a `part` that points to
another folder). Other fences (shell, CI YAML, log output) aren't compiled.
"""
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKILL = ROOT.parents[2] / "skills" / "build-runner"
FENCE = re.compile(r"^```(\w*)\s*\n(.*?)^```\s*$", re.M | re.S)
BUILD_CONFIG = re.compile(r"\A(?:\s*#.*\n)*(?:targets|global_options):", re.M)


def fences():
    for source in sorted(SKILL.rglob("*.md")):
        text = source.read_text()
        for n, m in enumerate(FENCE.finditer(text), 1):
            yield source, f"{source.stem}__{n}", text.count("\n", 0, m.start()) + 1, m[1], m[2]


def main():
    config = json.loads((ROOT / "validate.json").read_text())
    case_files = config.get("case_files", {})
    blocks = {name: (lang, code) for _, name, _, lang, code in fences()}
    # Fence ids are positional, so a renumbered fence must break loudly, not drop a snippet.
    for case_id, files in case_files.items():
        lang, code = blocks.get(case_id, (None, ""))
        if lang != "yaml" or not BUILD_CONFIG.match(code):
            raise SystemExit(f"validate.json case_files: {case_id} isn't a build.yaml block")
        for f in files:
            if blocks.get(f["block"], (None,))[0] != "dart":
                raise SystemExit(f"validate.json case_files: {f['block']} (for {case_id}) isn't a dart block")
    used_dart = set()

    cases = ROOT / "cases"
    shutil.rmtree(cases, ignore_errors=True)
    rows = []
    for source, name, line, lang, code in fences():
        rel = f"{source.relative_to(SKILL)}:{line}"
        if lang == "yaml" and BUILD_CONFIG.match(code):
            case = cases / name
            shutil.copytree(ROOT / "lib", case / "lib", ignore=shutil.ignore_patterns("*.g.dart"))
            shutil.copy(ROOT / "pubspec.yaml", case / "pubspec.yaml")
            (case / "build.yaml").write_text(code)
            # Its own (empty) options, so the fixture's `exclude: cases/**` doesn't apply.
            (case / "analysis_options.yaml").write_text("")
            for f in case_files.get(name, []):
                (case / f["path"]).write_text(f"// Extracted from {f['block']}\n" + blocks[f["block"]][1])
                used_dart.add(f["block"])
            rows.append({"case": str(case.relative_to(ROOT)), "source": rel})
    unused = [name for name, (lang, _) in blocks.items() if lang == "dart" and name not in used_dart]
    if unused:
        raise SystemExit(f"dart blocks not used by any case in validate.json case_files: {', '.join(unused)}")
    (ROOT / "manifest.json").write_text(json.dumps(rows, indent=2) + "\n")
    print(f"Extracted {len(rows)} build.yaml cases.")


if __name__ == "__main__":
    main()
