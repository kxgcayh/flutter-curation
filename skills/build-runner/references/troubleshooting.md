# Troubleshooting

Read the log from the top: lines starting `W` are warnings and `E` errors, and each names the builder and input file. Add `-v` to see what builders log.

## Version solving

Every builder depends on `analyzer`, and so does build_runner (directly since 2.8). `pub get` must find a single analyzer version that they all accept, together with the SDK. So adding or upgrading one generator can fail to resolve, or quietly hold back the others.

- **Read pub's explanation to the end.** It names the chain, e.g. `build_runner >=2.16.2 depends on analyzer ^14.3.0 ... analyzer >=13.1.0 <14.6.0 depends on meta ^1.18.3 and every version of flutter from sdk depends on meta 1.18.0`.
- **Flutter pins `meta`** (and a few other packages), which caps analyzer and therefore build_runner. On Flutter 3.44 a Flutter app resolves analyzer 13.0.0 and build_runner 2.15.1. The fix is a newer Flutter SDK, not a dependency override.
- **To see what's held back and why,** run `dart pub outdated`. Upgrade generators together with `flutter pub upgrade --major-versions <a> <b>`, or with `flutter pub add 'dev:<builder>:^x.y.z'`, which prints the reason when it fails.
- **Don't fix clashes with `dependency_overrides` on `analyzer`.** A generator compiled against an analyzer API it doesn't support fails at build time instead, usually with a long compile error.
- **Annotation packages move with their generators:** `json_annotation` with `json_serializable`, `freezed_annotation` with `freezed`, `riverpod_annotation` with `riverpod_generator`. Upgrade each pair together.

## The build fails before reading your code

The log shows a compile error in `.dart_tool/build/entrypoint/build.dart`, or in a builder package's own source, before any `json_serializable on ...` lines. That's a version mismatch between packages in the lock file, not a problem in your code.

- **Example:** `go_router_builder` ≤ 4.5.0 together with `source_helper` 1.4.0 fails with a `qualifiedName` clash. Fix it with go_router_builder 4.5.2+, or pin `source_helper: '<1.4.0'` in `dev_dependencies` when the SDK can't resolve the newer builder.
- **Look for a fixed release first:** check the failing package's changelog and issue tracker for the error text.
- **After changing versions,** run `dart run build_runner build`; the builders recompile automatically. Use `clean` only if the error persists.

## Generator errors (`E` lines naming your file)

These are real problems in the annotated code, reported by the generator. For example, json_serializable can't serialize a `Stream` field:

```text
E json_serializable on lib/models/person.dart:
  Could not generate `fromJson` code for `s`.
  To support the type `Stream` you can:
  * Use `JsonConverter`
```

Fix the source the message points to, then rebuild.

The build exits non-zero, and the failing file's generated part is **deleted**, not kept. So the analyzer then reports undefined `_$...` names in that file too. Those follow-on errors go away with the fix.

## Generated code is missing or stale

| Symptom | Fix |
| --- | --- |
| `_$XFromJson isn't defined` / `Undefined name '_$...'` after an edit | the build hasn't run; run `build` or check `watch` |
| `must be included as a part directive` | add `part '<file>.g.dart';` to the annotated file, matching its file name |
| `Target of URI hasn't been generated: 'x.g.dart'` | same as above, or the builder skipped the file: check `generate_for` |
| Generated file kept old content (before 2.16) | a hand edit survived: run `clean`, then `build` |
| Outputs left behind after deleting a source | build again: build_runner deletes outputs whose inputs are gone |
| Builder seems to ignore its options | wrong key: the log says `Ignoring options for unknown builder`; see the [builder keys](build-yaml.md#builder-keys) |
| A generated file is reported as conflicting | nothing to do: since 2.7 conflicting files are always deleted and rewritten |

## Slow builds

- **Limit inputs with `generate_for`** for each builder ([build-yaml.md](build-yaml.md#restrict-which-files-a-builder-reads)). By default, every builder reads every Dart file.
- **Keep `watch` running** instead of repeating `build`. Incremental builds reuse the analysis state and are much faster.
- **Upgrade build_runner** when the SDK allows: 2.13 and 2.14 sped up incremental builds by 2–4×, and 2.14+ AOT-compiles builders.
- **The first build after a builder change compiles builders,** about 10–20 s with AOT on a laptop. That's a one-off cost, not a per-file cost.
- **Use `--build-filter`** while working on one area: `dart run build_runner build --build-filter='lib/feature/**'`.
- **Split a large app into packages** of a pub workspace, so each builds only its own files. Since 2.14, `--workspace` builds them all with one process.

## Watch and locking (2.14+)

- **"Waiting for already-running build_runner"** means another command holds the lock, usually a `watch` in another terminal or the IDE. Run `dart run build_runner stop`, or let the new command take over: it closes the watch after its current build.
- **`watch` picks up `build.yaml` changes** without restarting (2.9+). Changing builder versions in `pubspec.yaml` recompiles the builders.

## Last resort

```sh
dart run build_runner clean
dart run build_runner build
```

`clean` deletes `.dart_tool/build`, so the next build is a full one. If the problem persists after `clean`, it's in the code or the versions, not in the cache.
