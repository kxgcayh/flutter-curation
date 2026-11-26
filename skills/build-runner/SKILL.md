---
name: build-runner
description: Run, configure, debug and check Dart and Flutter code generation with build_runner (dart run build_runner build/watch/clean/stop, build.yaml targets, generate_for, builder options, global_options, source_gen combining_builder, part '*.g.dart' directives, generated files in source control, --only-check CI checks, pub workspaces, slow or failing builds, analyzer version conflicts). Use whenever a project uses json_serializable, freezed, riverpod_generator, go_router_builder, mockito or another build_runner builder and generated files are missing, stale, failing or need configuring. Use the riverpod and go-router skills for what to annotate; this skill covers running and configuring the build.
metadata:
  version: "0.5.0"
  docs-read: "2026-11-26"
  docs-source: "github.com/dart-lang/build@e790ce1 (2026-11-24): build_runner README, CHANGELOG, lib/src/build_runner_command_line.dart; build_config README, docs/build_yaml_format.md; github.com/dart-lang/source_gen@cf5b53f (2026-11-20): README, build.yaml, CHANGELOG; pub.dev version metadata"
  validated-against: "build_runner 2.15.1 + json_serializable 6.15.2 on Flutter 3.44.9; 2.15.1 + 6.11.2 on Flutter 3.32.8; 2.17.1 in a pure Dart package on Dart 3.12"
---

# build_runner

`build_runner` runs code generators (*builders*) such as json_serializable, freezed, riverpod_generator, go_router_builder and mockito. They read your annotated code and write files such as `*.g.dart`, `*.freezed.dart` and `*.mocks.dart`. You run it from the terminal; it isn't called from app code.

## Step 1: inspect the project

| Look at | Why |
| --- | --- |
| `pubspec.lock` → `build_runner` version | flags and behaviour differ by version (table below) |
| `dev_dependencies` | which builders run; each needs its annotation package in `dependencies` |
| `build.yaml` in the package root (and `build.*.yaml`) | existing builder config: edit it, don't add a second file |
| `resolution: workspace` in `pubspec.yaml` | a pub workspace: consider `--workspace` (2.11+) |
| `.gitignore`, CI scripts | whether generated files are committed, and how CI checks them |
| `analysis_options.yaml` | whether generated files are excluded from analysis |

### What the resolved version gives you

| build_runner | Change |
| --- | --- |
| 2.7+ | conflicting outputs are always deleted; `-d` / `--delete-conflicting-outputs` does nothing (later versions warn that it was removed) |
| 2.14+ | builders are AOT-compiled by default (JIT fallback for `dart:mirrors`); `stop` command; a second command waits for the running one; `--workspace` stable (experimental since 2.11) |
| 2.15 | `--low-resources-mode`, `--log-performance`, `--track-performance` removed |
| 2.16+ | a build reverts hand edits to generated files; `--only-check` for CI; `--keep-modified-outputs` |
| 2.17+ | builders can opt in to add or remove their own `part` directive (source_gen builders such as json_serializable don't yet) |

**Which version you get depends on the SDK, and on Flutter's pinned `meta`.** build_runner 2.15.2+ needs Dart 3.11 and analyzer ≥ 13.3; 2.16.2+ needs analyzer ≥ 14.3. A Flutter app on Flutter 3.44 resolves **2.15.1**: Flutter pins `meta` 1.18.0, which caps analyzer at 13.0.0. A pure Dart package on the same SDK resolves 2.17.1. Flutter 3.32 also gets 2.15.1. So don't assume `--only-check` exists: read the lock file, or run `dart run build_runner build --help`.

## Commands

```sh
dart run build_runner build        # one build, then exit
dart run build_runner watch        # rebuild on every save; keep it running while editing
dart run build_runner clean        # delete build_runner's cache (.dart_tool/build)
dart run build_runner stop         # stop a running watch/serve (2.14+)
dart run build_runner build --only-check   # CI: fail if generated files are stale (2.16+)
```

Run them from the package root (the folder with `pubspec.yaml`). Use `dart run build_runner`; `flutter pub run build_runner` is the old spelling. More flags are in [commands.md](references/commands.md).

## Core rules

1. **Every generated part needs its `part` directive,** in the file that has the annotation: `part 'person.g.dart';` in `person.dart`. Without it the build warns that `person.g.dart must be included as a part directive` and your library can't see the generated code. Libraries such as `*.mocks.dart` are imported, not `part`-ed.
2. **Never hand-edit generated files.** Change the annotated source and rebuild. Since 2.16 a build reverts the edits anyway. Before 2.16, edits survive until the input changes or you run `clean`.
3. **After editing annotated code, rebuild** (or check that `watch` is running) before running `dart analyze` or tests. Errors such as `_$PersonFromJson isn't defined` usually mean "not generated yet", not wrong code.
4. **Don't add `--delete-conflicting-outputs` / `-d`.** Since 2.7 it does nothing. If outputs conflict, build_runner deletes and rewrites them itself.
5. **Configure builders in `build.yaml`,** keyed by builder name (`json_serializable`, `freezed`, `riverpod_generator`, `go_router_builder`, `mockito:mockBuilder`, `source_gen:combining_builder`). Use `generate_for` to limit which files a builder reads. See [build-yaml.md](references/build-yaml.md).
6. **Keep annotation and generator versions in step,** with caret constraints, not `any`. A generator can warn when your annotation package's lower bound is older than it supports (json_serializable: `The version constraint "any" on json_annotation allows versions before 4.12.0 which is not allowed`).
7. **`.dart_tool/` is never committed.** Committing `*.g.dart` is the project's choice; packages published to pub must include their generated files. See [ci-and-source-control.md](references/ci-and-source-control.md).
8. **`build.yaml` controls generation, not analysis.** To silence lints in generated code, use the `combining_builder` `ignore_for_file` option, or the analyzer's `exclude`.

## When a build fails

| Symptom | Likely cause | Where |
| --- | --- | --- |
| `version solving failed` adding a builder | analyzer constraint clash between builders, or Flutter's pinned `meta` | [troubleshooting.md](references/troubleshooting.md#version-solving) |
| Error compiling builders, before any of your files are read | incompatible builder/helper versions in the lock file | [troubleshooting.md](references/troubleshooting.md#the-build-fails-before-reading-your-code) |
| `must be included as a part directive` | missing or misspelled `part` | rule 1 |
| `Ignoring options for unknown builder` | wrong builder key in `build.yaml` | [build-yaml.md](references/build-yaml.md#builder-keys) |
| Builds are slow | the builder reads every file; no `generate_for` | [troubleshooting.md](references/troubleshooting.md#slow-builds) |
| Command hangs at "Waiting for already-running build_runner" | another `watch`/`serve` holds the lock (2.14+) | `dart run build_runner stop` |

## References (load the one the task needs)

| Task | Read |
| --- | --- |
| Every command and flag: `--build-filter`, `--define`, `--release`, `-c`, `--workspace`, `--output`, debugging builders | [commands.md](references/commands.md) |
| `build.yaml`: targets, `generate_for`, options, `global_options`, `combining_builder`, output folders, ordering, precedence | [build-yaml.md](references/build-yaml.md) |
| Version solving, builder compile errors, stale or missing outputs, slow builds, watch problems | [troubleshooting.md](references/troubleshooting.md) |
| Committing generated files, CI checks, publishing, analysis settings, monorepos | [ci-and-source-control.md](references/ci-and-source-control.md) |
