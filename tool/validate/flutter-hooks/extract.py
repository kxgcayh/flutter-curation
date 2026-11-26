"""Turn every ```dart block of skills/flutter-hooks into a compilable fixture.

A block that declares top-level classes/functions is written as a library.
A block of bare statements is wrapped in a HookWidget.build (it may `return`
a widget itself). See validate.json for skips, tests and cross-fixture imports.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKILL = ROOT.parents[2] / "skills" / "flutter-hooks"
FENCE = re.compile(r"^```dart\s*\n(.*?)^```\s*$", re.M | re.S)
KEYWORDS = r"(?!(?:return|final|var|const|await|if|for|while|switch|late)\b)"
DECL = re.compile(
    r"^(?:(?:abstract|sealed|final|base) )*(?:class|mixin|extension|enum|typedef) "
    # a return type (word, generic or record), then the name: `int f(`, `(bool, X) useY(`
    r"|^(?:\([^)]*\)|" + KEYWORDS + r"[A-Za-z_][\w<>?,]*)\s+[A-Za-z_]\w*\s*(?:<[^>]*>)?\(",
    re.M,
)
# A bare statement at column 0 (a call like `useEffect(`, or `return`/`if`/`for`)
# means the block is a build-method fragment, even if it also has local functions.
STATEMENT = re.compile(r"^(?:[a-z_]\w*\s*(?:<[^>]*>)?\(|(?:return|if|for|switch)\b)", re.M)
IMPORTS = [
    "import 'dart:async';",
    "import 'package:flutter/material.dart';",
    "import 'package:flutter_hooks/flutter_hooks.dart';",
    "import 'stubs.dart';",
]
HEADER = "// ignore_for_file: unused_import, unused_local_variable, unused_element, unused_field, dead_code, avoid_print, deprecated_member_use"


def fixtures():
    for source in sorted(SKILL.rglob("*.md")):
        text = source.read_text()
        for n, m in enumerate(FENCE.finditer(text), 1):
            yield source, f"{source.stem}__{n}", text.count("\n", 0, m.start()) + 1, m[1].rstrip()


IMPORT = re.compile(r"(?ms)^import\s+'[^']+'[^;]*;")


def split_imports(code):
    """Whole import directives (including multi-line `hide`/`show`) and the rest."""
    imports = [re.sub(r"\s+", " ", m) for m in IMPORT.findall(code)]
    return imports, IMPORT.sub("", code).strip()


def resolved(package):
    lock = ROOT / "pubspec.lock"
    return lock.exists() and re.search(rf"(?m)^  {re.escape(package)}:$", lock.read_text()) is not None


def render(name, code, config):
    own_imports, body = split_imports(code)
    extra = [f"import '{dep}.dart';" for dep in config.get("imports", {}).get(name, [])]
    is_test = name in config.get("tests", [])
    # A block with its own imports gets only those (plus stubs), so a default
    # import can't mask a wrong or missing one.
    base = ["import 'stubs.dart';"] if own_imports else IMPORTS
    imports = list(dict.fromkeys(own_imports + base + extra))
    if is_test:
        imports = [i.replace("'stubs.dart'", "'../lib/stubs.dart'") for i in imports]
        imports = [re.sub(r"import '(\w[\w-]*__\d+)\.dart';", r"import '../lib/\1.dart';", i) for i in imports]
        if not any("package:test/" in i or "package:flutter_test/" in i for i in imports):
            imports.append("import 'package:flutter_test/flutter_test.dart';")
    if (DECL.search(body) and not STATEMENT.search(body)) or is_test:
        wrapped = body
    else:
        tail = "" if re.search(r"(?m)^return ", body) else "\n    return const SizedBox();"
        indented = "\n".join("    " + l if l else l for l in body.splitlines())
        wrapped = (f"class _Fragment extends HookWidget {{\n  const _Fragment();\n\n"
                   f"  @override\n  Widget build(BuildContext context) {{\n{indented}{tail}\n  }}\n}}")
    return "\n".join([HEADER, *imports, "", wrapped, ""])


def main():
    config = json.loads((ROOT / "validate.json").read_text())
    for d in ("lib", "test"):
        (ROOT / d).mkdir(exist_ok=True)
        for old in (ROOT / d).glob("*__*.dart"):
            old.unlink()
    rows, written = [], 0
    for source, name, line, code in fixtures():
        rel = f"{source.relative_to(SKILL)}:{line}"
        if name in config.get("skip", {}):
            rows.append({"fixture": name, "source": rel, "skipped": config["skip"][name]})
            continue
        needs = config.get("needs_package", {}).get(name)
        if needs and not resolved(needs):
            rows.append({"fixture": name, "source": rel, "skipped": f"{needs} doesn't resolve on this SDK"})
            continue
        path = ROOT / ("test" if name in config.get("tests", []) else "lib") / f"{name}.dart"
        path.write_text(f"// Extracted from {rel}\n" + render(name, code, config))
        rows.append({"fixture": str(path.relative_to(ROOT)), "source": rel})
        written += 1
    (ROOT / "manifest.json").write_text(json.dumps(rows, indent=2) + "\n")
    print(f"Extracted {len(rows)} fences into {written} fixtures ({len(rows) - written} skipped).")


if __name__ == "__main__":
    main()
