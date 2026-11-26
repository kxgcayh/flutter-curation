# CI, source control and publishing

## Commit generated files, or not

The project chooses; follow what it already does.

| | Committed `*.g.dart` | Ignored `*.g.dart` |
| --- | --- | --- |
| Fresh clone | builds and runs straight away | needs `dart run build_runner build` first |
| Code review | generated diffs are visible | smaller diffs |
| CI | check that they're up to date | generate them before analyze and test |
| `.gitignore` | `.dart_tool/` | `.dart_tool/` plus `*.g.dart`, `*.freezed.dart`, `*.mocks.dart` |

`.dart_tool/` (including `.dart_tool/build`) is always ignored. It's build_runner's private cache.

## CI: generated files are committed

Check that nobody forgot to rebuild. With build_runner 2.16+:

```sh
dart run build_runner build --only-check
```

It writes nothing, logs each stale or missing file, and exits 1 on any difference. Before 2.16, which is what Flutter apps on Flutter 3.44 and older resolve, rebuild and compare with git:

```sh
dart run build_runner build
git diff --exit-code
test -z "$(git status --porcelain)"
```

The `git status` line also catches new, untracked generated files.

## CI: generated files are ignored

Generate before anything reads the code:

```yaml
# .github/workflows/ci.yml (steps)
- uses: subosito/flutter-action@v2
  with:
    channel: stable
- run: flutter pub get
- run: dart run build_runner build
- run: dart analyze
- run: flutter test
```

Cache `~/.pub-cache` if pub get is slow; `.dart_tool/build` doesn't need caching for a one-off CI build.

## Formatting checks

Generators format their output at the default 80-column width. They ignore `formatter: page_width` in `analysis_options.yaml`. With a wider page width, `dart format --set-exit-if-changed .` then fails on generated files. Leave them out of the format check:

```sh
git ls-files -z -- '*.dart' ':!:*.g.dart' ':!:*.freezed.dart' ':!:*.mocks.dart' \
  | xargs -0 dart format --output=none --set-exit-if-changed
```

The `:!:` pathspecs drop generated files, and `-z` / `-0` keep paths with spaces intact. If generated files are ignored by git, `git ls-files` doesn't list them anyway.

## Analysis

- **Lints in generated code:** most generators already write `// ignore_for_file:` lines. To add more, use the `combining_builder` `ignore_for_file` option ([build-yaml.md](build-yaml.md#the-shared-gdart-file)).
- **`analyzer: exclude: ['**/*.g.dart']`** in `analysis_options.yaml` hides everything the analyzer reports in those files. Prefer `ignore_for_file: type=lint`, which keeps errors visible.

## Publishing a package

Users of a published package can't run its builders. So **publish the generated files**:
- **Generated parts sit next to their sources** (`combining_builder` writes with `build_to: source`), so they're published like any other file, unless they're ignored.
- **If `.gitignore` ignores them,** `dart pub publish` leaves them out too. Add a `.pubignore` to the package root: when it exists, pub uses it instead of `.gitignore` for that folder. Copy the other ignore rules into it.
- **Run `dart pub publish --dry-run`** and check that the generated files are listed.

A package that ships a `build.yaml` with builder config should also depend on `build_config`, so its users get a compatible config parser.

## Pub workspaces and monorepos

- **`dart run build_runner build --workspace`** (2.11+, stable since 2.14) builds every workspace package with one process, and one `.dart_tool` at the workspace root.
- **Per-package options** come from each package's own `build.yaml`. `global_options` come from the `build.yaml` at the workspace root.
- **Without `--workspace`,** run the command in each package that has builders (e.g. `melos exec --depends-on=build_runner -- dart run build_runner build`).
- **Switching between workspace and per-package builds** triggers a full rebuild (2.15.1+).
