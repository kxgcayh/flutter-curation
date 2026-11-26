"""Extract fenced Dart snippets into isolated Flutter analyzer fixtures."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKILL = ROOT.parents[2] / "skills" / "riverpod"
FENCE = re.compile(r"^\x60{3}dart\s*\n(.*?)^\x60{3}\s*$", re.M | re.S)

ALIAS = {
    "async-and-performance": "async",
    "code-generation": "codegen",
    "flutter-and-hooks": "flutter",
    "lifecycle-and-caching": "lifecycle",
    "providers-and-refs": "refs",
    "scopes-and-testing": "scopes",
}
SKIP = {
    ("codegen", 2): "Standalone annotation options have no declaration to annotate",
}
WRAP = {
    ("SKILL", 3): ("Widget demo(WidgetRef ref)", ""),
    ("async", 1): ("Widget demo(WidgetRef ref)", "Separate alternative return statements"),
    ("async", 2): ("Widget demo(WidgetRef ref)", "Supply orders and showProgress"),
    ("async", 3): ("Widget demo(WidgetRef ref)", ""),
    ("async", 8): ("void demo(WidgetRef ref)", ""),
    ("flutter", 6): ("void demo(WidgetRef ref, String id)", "Intentional bad behavior example"),
    ("flutter", 7): ("void demo(WidgetRef ref, String id)", ""),
    ("flutter", 8): ("Widget demo(WidgetRef ref, String id)", ""),
    ("lifecycle", 8): ("void demo(Ref ref)", ""),
    ("refs", 6): ("void demo(WidgetRef ref, BuildContext context)", ""),
    ("refs", 8): ("Future<void> demo(WidgetRef ref) async", ""),
    ("scopes", 1): ("Widget demo()", "Provide dependencies as stubs"),
    ("scopes", 5): ("Widget demo()", ""),
}
TESTS = {("scopes", 7), ("scopes", 8), ("scopes", 11)}
ASYNC_USER = "final userProvider = FutureProvider<User>((ref) async => const User());"
SYNC_USER = "final userProvider = Provider<User?>((ref) => null);"

def wrap(code, signature):
    return signature + " {\n" + code + "\n}\n"

def render(key, code):
    note, extra = [], ""
    if key in WRAP:
        signature, explanation = WRAP[key]
        note.append("wrapped")
        if explanation:
            note.append(explanation)
        if key == ("async", 1):
            code = code.replace("// Or the callback form", "}\n\nWidget demoWhen(WidgetRef ref) {\n  final orders = ref.watch(ordersProvider);\n// Or the callback form")
        if key == ("async", 2):
            code = "final orders = ref.watch(ordersProvider);\n" + code
        if key == ("async", 3):
            code = "return " + code.rstrip() + ";"
        if key in {("scopes", 1), ("scopes", 5)}:
            code = "return " + code
        if key == ("flutter", 8):
            parent, editor = code.split("// DetailEditor", 1)
            code = parent + "}\n\nvoid editor(Detail initial) {\n// DetailEditor" + editor
            note.append("separated parent and editor fragments")
        code = wrap(code, signature)

    if key == ("async", 4):
        counter = iter(range(1, 4))
        code = re.sub(r"(?m)^((?:ProviderScope|ProviderContainer)\(.*\);)$",
                      lambda m: wrap(m[1], f"void usage{next(counter)}()"), code)
        note.append("wrapped standalone constructor calls")
    if key == ("async", 5):
        extra = "Duration? retry(int count, Object error) => null;"
    if key in {("codegen", 4), ("codegen", 5), ("lifecycle", 7)}:
        code = re.sub(r"(?m)^ref\.watch\(.*?;\s*$", lambda m: wrap(m[0], "void demo(Ref ref)"), code)
        note.append("wrapped usage line")
    if key == ("scopes", 6):
        code = re.sub(r"(?m)^ProviderScope\(", "Widget demo() => ProviderScope(", code)
        note.append("wrapped widget expression")
    if key in {("SKILL", 3), ("async", 9), ("scopes", 1), ("scopes", 8)}:
        extra = ASYNC_USER
    if key == ("async", 8):
        extra = "final userProvider = Provider<User>((ref) => const User());"
    if key in {("lifecycle", 9), ("lifecycle", 10)}:
        extra = SYNC_USER
    if key == ("lifecycle", 8):
        extra = "final userProvider = FutureProvider.family<User, String>((ref, id) async => User(id: id));"
    if key == ("lifecycle", 6):
        code = "class TodoDemo extends Notifier<List<Todo>> {\n@override\nList<Todo> build() => [];\n" + code + "\n}"
        note.append("wrapped in notifier")
    if key == ("refs", 5):
        sync, async_code = code.split("// Async: optimistic")
        code = ("class SyncDemo extends Notifier<List<Item>> {\n@override\nList<Item> build() => [];\n" + sync + "}\n"
                "class AsyncDemo extends AsyncNotifier<List<Item>> {\n@override\nFuture<List<Item>> build() async => [];\n"
                "// Async: optimistic" + async_code + "\n}")
        note.append("wrapped in separate sync and async notifiers")
    if key in {("scopes", 7), ("scopes", 9), ("scopes", 11)}:
        extra = {
            7: "import '../lib/providers-and-refs__3.dart' show cartProvider;",
            9: "",
            11: "import '../lib/scopes-and-testing__9.dart' show MockCounter;",
        }[key[1]]
    if key in {("scopes", 7), ("scopes", 8)}:
        code = wrap(code, "void main()")
        note.append("wrapped test registration in main")
    if key == ("scopes", 11):
        code = "void main() { test('mock override', () {\n" + code + "\n}); }"
        note.append("wrapped in test")
    if key == ("scopes", 5):
        extra = "import 'scopes-and-testing__3.dart' show currentItemIdProvider;"
    if key == ("scopes", 10):
        extra = "@riverpod\nclass Counter extends _$Counter { @override int build() => 0; }"
        note.append("added generated Counter in the same library")
    return code, extra, note

def write(path, key, code, source, line):
    code, extra, note = render(key, code)
    imports = re.findall(r"(?m)^import .*?;[^\n]*", code + "\n" + extra)
    code = re.sub(r"(?m)^(import|part) .*?;[^\n]*\n?", "", code)
    extra = re.sub(r"(?m)^import .*?;[^\n]*\n?", "", extra)
    if key == ("codegen", 1):
        note.append("mapped original part directive to fixture basename")
    prefixes = [
        "import 'dart:async';",
        "import 'package:flutter/material.dart';",
        "import 'package:hooks_riverpod/hooks_riverpod.dart';",
        "import 'package:flutter_hooks/flutter_hooks.dart';",
        "import 'package:riverpod_annotation/riverpod_annotation.dart';",
        "import 'package:http/http.dart' as http;",
        "import 'package:mocktail/mocktail.dart';",
        "import 'package:shared_preferences/shared_preferences.dart';",
        "import 'package:flutter_riverpod/legacy.dart';",
        "import 'package:riverpod_skill_validation/stubs.dart';",
    ]
    if key in TESTS:
        prefixes.append("import 'package:flutter_test/flutter_test.dart';")
    if any("package:flutter_riverpod/flutter_riverpod.dart" in line for line in imports):
        prefixes.remove("import 'package:hooks_riverpod/hooks_riverpod.dart';")
    if key == ("scopes", 10):
        prefixes[-1] = "import 'package:riverpod_skill_validation/stubs.dart' hide Counter;"
    parts = f"part '{path.stem}.g.dart';\n" if re.search(r"@riverpod\b|@Riverpod\(", code + extra) else ""
    path.write_text(f"// Extracted from {source}:{line}\n// ignore_for_file: unused_import, unused_local_variable, unused_element, unnecessary_import\n"
                    + "\n".join(dict.fromkeys(prefixes + imports)) + "\n" + parts + "\n" + extra + "\n" + code)
    return note

def main():
    manifest = ROOT / "manifest.json"
    old_paths = {path for row in json.loads(manifest.read_text()) for path in row["paths"]} if manifest.exists() else set()
    rows = []
    for source in sorted(SKILL.rglob("*.md")):
        source_text = source.read_text()
        for number, match in enumerate(FENCE.finditer(source_text), 1):
            name = source.stem
            key = ALIAS.get(name, name), number
            line = source_text.count("\n", 0, match.start()) + 1
            rel = str(source.relative_to(SKILL))
            code = match[1].strip()
            notes = []
            paths = []
            if key in SKIP:
                notes.append(SKIP[key])
            else:
                parts = [("", code)]
                if key[0] == "migration":
                    before, after = code.split("// After", 1)
                    parts = [("_before", before), ("_after", after)]
                    notes.append("split legacy and modern variants")
                    if number == 2:
                        parts = [(suffix, re.sub(r"(?m)^ref\.read.*?;\s*$", lambda m: wrap(m[0], "void demo(Ref ref)"), snippet))
                                 for suffix, snippet in parts]
                        notes.append("wrapped usage lines")
                for suffix, snippet in parts:
                    directory = "test" if key in TESTS else "lib"
                    path = ROOT / directory / f"{name}__{number}{suffix}.dart"
                    notes.extend(write(path, key, snippet, rel, line))
                    paths.append(str(path.relative_to(ROOT)))
            rows.append(dict(source=rel, line=line, number=number, paths=paths, notes=notes))
    new_paths = {path for row in rows for path in row["paths"]}
    for stale in old_paths - new_paths:
        path = ROOT / stale
        if path.parent in {ROOT / "lib", ROOT / "test"} and path.is_file() and path.read_text().startswith("// Extracted from "):
            path.unlink()
    manifest.write_text(json.dumps(rows, indent=2) + "\n")
    print(f"Extracted {len(rows)} fences into {sum(len(row['paths']) for row in rows)} fixtures.")

if __name__ == "__main__":
    main()
