# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

Each release records, per skill, **when the package's official documentation was read** and **which package versions the skill was validated against**. A skill is only as current as its sources: if a package has released since the date below, check its changelog for anything the skill doesn't cover yet.

## [Unreleased]

## [0.5.0] - 2026-11-26

### Added

- **`build-runner` skill:** `SKILL.md` plus 4 references (commands, build.yaml, troubleshooting, CI and source control). It includes:
  - flags and behaviour per build_runner version: `-d` ignored since 2.7, AOT builders and `stop` in 2.14, `--only-check` and auto-reverted hand edits in 2.16
  - which version Flutter apps actually resolve: Flutter pins `meta`, so a Flutter app on Flutter 3.44 (and 3.32) gets build_runner 2.15.1, while a pure Dart package on the same SDK gets 2.17.1. On Flutter 3.50 apps get 2.17.1, so `--only-check` is available (confirmed in CI)
  - `build.yaml`: builder keys, `generate_for`, options, `global_options`, the `combining_builder` (`ignore_for_file`, `preamble`, generating into `lib/generated/`), extra sources, `-c` configs
  - troubleshooting from reproduced runs: missing `part` directives, unknown builder keys, generator errors deleting the failed part, version-solving chains
  - CI checks with `--only-check`, or `git diff` before 2.16; generators ignoring `formatter: page_width`; publishing ignored generated files with `.pubignore`; `--workspace`
- **Validation of `build.yaml` blocks:** each one is built in its own project, failing on build_runner warnings, and the output is analyzed. `run.py` gained `commands` and `cases/` support.

### Changed

- **`riverpod` and `go-router`:** link to the build-runner skill for build configuration, version conflicts and CI.

### Sources

| Skill | Docs read | Sources | Validated against |
| --- | --- | --- | --- |
| `build-runner` | 2026-11-26 | [dart-lang/build](https://github.com/dart-lang/build/tree/e790ce1) at `e790ce1` (2026-11-24): build_runner README, CHANGELOG, `lib/src/build_runner_command_line.dart`; build_config README, `docs/build_yaml_format.md`. [dart-lang/source_gen](https://github.com/dart-lang/source_gen/tree/cf5b53f) at `cf5b53f` (2026-11-20): README, `build.yaml`, CHANGELOG. pub.dev version metadata for build_runner and the main builders; Flutter's pinned `meta` per release tag | build_runner 2.17.1 + json_serializable 6.15.2 on Flutter 3.50.1 (CI: `--only-check` clean and stale checks pass); 2.15.1 + 6.15.2 on Flutter 3.44.9; 2.15.1 + 6.11.2 on Flutter 3.32.8. All 6 `build.yaml` cases build without unexpected warnings and analyze clean, and the smoke test passes on each |

## [0.4.0] - 2026-11-26

### Added

- **`go-router` skill:** `SKILL.md` plus 7 references (configuration, navigation, redirects and guards, shells, deep links and web, type-safe routes, testing and migration). It includes:
  - a version table per Flutter SDK, from pub.dev
  - `go` vs `push`, and auth redirects with `refreshListenable`
  - `onEnter` guards (`Allow` / `Block`) and their order relative to `redirect`
  - `StatefulShellRoute` tabs, and full-screen routes above shells
  - current App Links / universal links setup (Flutter's built-in handler is on by default since 3.27), and the `flutter_web_plugins` dependency for `usePathUrlStrategy`
  - the go_router_builder 4.x public mixin, and breaking versions 14 → 18
  - a known build failure: go_router_builder ≤ 4.5.0 with `source_helper` 1.4.0 on Flutter 3.38–3.46, and its fix

### Sources

| Skill | Docs read | Sources | Validated against |
| --- | --- | --- | --- |
| `go-router` | 2026-11-26 | [flutter/packages](https://github.com/flutter/packages/tree/da586f5/packages/go_router) at `da586f5` (2026-11-25): go_router README, 12 `doc/` topics, `lib/src`, examples, tests, CHANGELOG; pub.dev constraints for go_router, go_router_builder, material_ui, cupertino_ui; docs.flutter.dev deep-linking (2026-11-23), set-up-app-links and set-up-universal-links (2026-11-10), url-strategies (2026-07-21) | go_router 18.1.4 + go_router_builder 4.5.3 on Flutter 3.50.1 (CI, no pin needed); 18.1.4 + builder 4.5.0 on Flutter 3.44.9 (with `source_helper <1.4.0`); 17.0.0 + builder 4.1.2 on Flutter 3.32.8. All 22 blocks compile, including generated type-safe routes, and 2 widget tests pass on each |

## [0.3.0] - 2026-11-26

### Added

- **`dio` skill:** `SKILL.md` plus 6 references (requests and responses, interceptors, errors and cancellation, adapters and security, plugins and testing, migration). It covers the shared `Dio` setup, interceptor handler rules, a `QueuedInterceptor` token-refresh example with a separate replay client, `DioException` mapping, cancellation, certificate pinning, testing with a fake `HttpClientAdapter`, and replacing the APIs deprecated before dio 6.0.

### Changed

- **README:** install steps for every agent (including Cursor and skills.sh flags), plus accurate validation and compatibility claims.
- **CONTRIBUTING:** setup prerequisites, what `tool/check.py` checks, a `validate.json` reference and the version rules.
- **CODE_OF_CONDUCT:** scope, a private reporting contact, and enforcement.
- **Validation tooling:** extractors add `flutter_test` only when a test doesn't import its own test package. `tool/validate/dio/` adds hand-written behaviour tests for the token-refresh interceptor.

### Sources

| Skill | Docs read | Sources | Validated against |
| --- | --- | --- | --- |
| `dio` | 2026-11-26 | [cfug/dio](https://github.com/cfug/dio/tree/f1bef46) at `f1bef46` (2026-10-19): dio README, migration guide, plugin docs, `lib/src`, tests, examples, plugin READMEs and sources, compatibility policy | dio 5.11.1, dio_cookie_manager 3.5.0, dio_http2_adapter 2.9.0, dio_compatibility_layer 0.1.1 on Flutter 3.44.9 (native_dio_adapter 1.8.0) and 3.32.8 (native_dio_adapter 1.7.0): 23 of 24 blocks compile (the skipped one is the intentional dio 4.x "Before" example). 5 tests pass, including behaviour tests for the token-refresh interceptor: 3 concurrent 401s refresh exactly once, a failing replay ends with an error instead of hanging, and the token isn't sent to other origins |

## [0.2.0] - 2026-11-26

### Added

- **`flutter-hooks` skill:** `SKILL.md` plus 5 references (primitives, async and Listenables, controllers, custom hooks, migration). It covers the rules of hooks, how `keys` decide re-runs, controller lifecycles, and the flutter_hooks 0.21.4 move of Material/Cupertino controller hooks to `material_hooks` / `cupertino_hooks`.
- **CI:** the repository check (`tool/check.py`) runs on pull requests and on pushes to `main`.
- **CI:** snippet validation (`tool/validate/run.py`) runs when pull requests or pushes to `main` change skills, the validation tooling or its workflow, plus weekly and on manual dispatch. It analyzes the eligible fixtures and runs the selected smoke tests on the latest stable Flutter and on Flutter 3.32.8.

### Changed

- **`riverpod` skill:** its hooks section now points to the `flutter-hooks` skill. It was re-validated in CI on Flutter 3.50.1 (Riverpod 3.5.0) and 3.32.8 (Riverpod 3.1.0).
- **Validation tooling:** `run.py` reports each skill's own packages, runs `build_runner` only for skills that use it, and adds optional dependencies when the SDK can resolve them. The fixture extractor in `tool/validate/flutter-hooks` works out the wrapping itself rather than relying on per-block wrappers.

### Sources

| Skill | Docs read | Sources | Validated against |
| --- | --- | --- | --- |
| `flutter-hooks` | 2026-11-26 | [rrousselGit/flutter_hooks](https://github.com/rrousselGit/flutter_hooks/tree/1c47821/packages/flutter_hooks) at `1c47821` (2026-11-06): README, `lib/src` dartdoc, 45 test files, CHANGELOG; pub.dev for flutter_hooks, material_hooks, cupertino_hooks | flutter_hooks 0.21.4 with material_hooks / cupertino_hooks 0.1.0 on Flutter 3.50.1 (all 30 blocks compile); flutter_hooks 0.21.3+1 on Flutter 3.44.9 and 3.32.8 (28 of 30 compile; the 2 split-package import blocks need Flutter 3.47+). The `useToggle` smoke test passes on all three |

## [0.1.0] - 2026-11-26

First release.

### Added

- **`riverpod` skill:** `SKILL.md` plus 8 references covering providers and refs, Flutter setup and hooks, code generation, lifecycle and caching, async state, retry and performance, scoping and testing, migration, and the experimental mutation and persistence APIs.
- **Version compatibility table:** the newest Riverpod, riverpod_generator, riverpod_annotation and riverpod_lint for each Dart SDK, from 3.8 (Flutter 3.32) to 3.13+.
- **Plugin manifests** for Claude Code (with marketplace), Codex, Cursor and Antigravity, plus `.agents/` and `skills.sh.json`.
- README, CONTRIBUTING, CODE_OF_CONDUCT and an MIT license.
- **Install checks:** the Codex and Antigravity installs were tested. The Claude Code and Antigravity manifest validators passed.

### Sources

| Skill | Docs read | Sources | Validated against |
| --- | --- | --- | --- |
| `riverpod` | 2026-11-26 | [riverpod.dev/docs](https://riverpod.dev/docs), 32 English pages; [rrousselGit/riverpod](https://github.com/rrousselGit/riverpod) at [`a16873f`](https://github.com/rrousselGit/riverpod/tree/a16873f97a1eefd07e14506cb96fcd350c9e62e8) (2026-11-17): example apps, package test suites, changelogs | riverpod / flutter_riverpod / hooks_riverpod 3.5.0, riverpod_annotation 4.0.8, riverpod_generator 4.0.10 on Flutter 3.44.9 (Dart 3.12.2); riverpod 3.1.0 + riverpod_generator 4.0.0+1 on Flutter 3.32.8 (Dart 3.8.1) |

### Validation

- **`riverpod`:** 57 of 58 Dart code blocks compile with `build_runner` and `dart analyze` on the latest packages. The remaining block is a list of annotation options with nothing to compile. On Flutter 3.32.8, the one failing block is the documented 3.3.2+ `allProviders(family:)` example.
- **Behaviour claims:** checked against the package test suites at `a16873f`. 27 are confirmed by a specific test; the 2 that were contradicted were fixed before release.
- **Upstream doc errors corrected rather than copied:**
  - a retry function returning a non-nullable `Duration`
  - `valueOrNull` in 3.x code
  - mismatched manual and generated examples on the motivation and testing pages

[Unreleased]: https://github.com/kxgcayh/flutter-curation/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/kxgcayh/flutter-curation/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/kxgcayh/flutter-curation/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/kxgcayh/flutter-curation/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/kxgcayh/flutter-curation/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/kxgcayh/flutter-curation/releases/tag/v0.1.0
