# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

Each release records, per skill, **when the package's official documentation was read** and **which package versions the skill was validated against**. A skill is only as current as its sources: if a package has released since the date below, check its changelog for anything the skill doesn't cover yet.

## [Unreleased]

### Added

- **`flutter-hooks` skill:** `SKILL.md` plus 5 references (primitives, async and Listenables, controllers, custom hooks, migration). It covers the rules of hooks, how `keys` decide re-runs, controller lifecycles, and the flutter_hooks 0.21.4 move of Material/Cupertino controller hooks to `material_hooks` / `cupertino_hooks`.
- **CI:** `check` runs `tool/check.py` on every PR and push. It covers manifest JSON and version sync, `SKILL.md` front matter and `metadata`, registration in the README and `skills.sh.json`, a changelog entry for the version, and links and code fences.
- **CI:** `validate-skills` runs `tool/validate/run.py` on PRs that touch `skills/` or `tool/validate/`, and weekly. It compiles every Dart code block and runs the smoke tests on the latest stable Flutter and on Flutter 3.32.8.

### Sources

| Skill | Docs read | Sources | Validated against |
| --- | --- | --- | --- |
| `flutter-hooks` | 2026-11-26 | [rrousselGit/flutter_hooks](https://github.com/rrousselGit/flutter_hooks/tree/1c47821/packages/flutter_hooks) at `1c47821` (2026-11-06): README, `lib/src` dartdoc, 45 test files, CHANGELOG; pub.dev for flutter_hooks, material_hooks, cupertino_hooks | flutter_hooks 0.21.3+1 on Flutter 3.44.9 and 3.32.8 (28 of 29 blocks compile; 1 smoke test passes); 0.21.4 is compiled by CI on the latest stable Flutter |

## [0.1.0] - 2026-11-26

First release.

### Added

- **`riverpod` skill:** `SKILL.md` plus 8 references covering providers and refs, Flutter setup and hooks, code generation, lifecycle and caching, async state, retry and performance, scoping and testing, migration, and the experimental mutation and persistence APIs.
- **Version compatibility table:** the newest Riverpod, riverpod_generator, riverpod_annotation and riverpod_lint for each Dart SDK, from 3.8 (Flutter 3.32) to 3.13+.
- **Plugin manifests** for Claude Code (with marketplace), Codex, Cursor and Antigravity, plus `.agents/` and `skills.sh.json`.
- README, CONTRIBUTING, CODE_OF_CONDUCT and an MIT license.
- **Install checks:** the GitHub install was tested with `codex plugin marketplace add` + `codex plugin add` (installed, enabled, skill present) and with `agy plugin install`. The manifests pass `claude plugin validate` and `agy plugin validate`.

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

[Unreleased]: https://github.com/kxgcayh/flutter-curation/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/kxgcayh/flutter-curation/releases/tag/v0.1.0
