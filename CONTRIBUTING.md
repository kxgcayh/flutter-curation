# Contributing to Flutter Curation

Thanks for helping improve these skills. Bug reports, skill requests and pull requests are all welcome.

Use public issues for technical problems. Remove tokens, personal information and private code from anything you share. For conduct concerns, use the private route in the [Code of Conduct](CODE_OF_CONDUCT.md).

## Reporting a problem with a skill

[File an issue][issue] and include:

1. **The model and its version,** as shown in the agent.
2. **The agent and its version:** Claude Code, Codex, Cursor, Antigravity, ...
3. **A minimal prompt** that shows the problem.
4. **The skill and reference files the agent loaded,** and a redacted excerpt of its output.
5. **Versions:** the package versions from `pubspec.lock`, and the output of `flutter --version`. Many problems are version-specific.

## Requesting a skill

Check the [open issues][issue] first, and react to or comment on an existing request. Otherwise, open an issue that names the package and describes the tasks agents get wrong today.

## Adding or changing a skill

### Layout

```
skills/<package>/
├── SKILL.md            # short entry point: setup checks, core rules, index of references
└── references/
    └── <topic>.md      # depth, loaded only when a task needs it
```

`src/` is optional local research (crawled docs, upstream checkouts, notes). It isn't a release input, and you don't need it to validate a skill. Keep your local `src/` out of commits, for example with `.git/info/exclude`.

### SKILL.md front matter

```yaml
---
name: <package>          # must match the folder name; lowercase letters, digits and hyphens
description: <what the skill does and when to use it, 1–1024 characters>
metadata:
  version: "0.3.0"       # the repository release that introduces or last revised this skill
  docs-read: "YYYY-MM-DD" # when the package's official docs were last read
  docs-source: "<doc URLs, plus repo@commit if you used examples or tests>"
  validated-against: "<package versions and Flutter SDKs the snippets compiled on>"
---
```

Update these fields whenever the sources or validation change. Copy the source revision and validation environment into the next release's **Sources** table in [CHANGELOG.md](CHANGELOG.md). The rows of past releases describe the tagged release, so leave them as they are.

The description decides when an agent loads the skill. Name the package and the tasks it covers. Avoid generic words that would trigger it for unrelated work.

### Writing guidelines

- **Keep `SKILL.md` short** (roughly under 150 lines), and put detail in `references/`. Link every reference from a table in `SKILL.md`.
- **Tell the agent to inspect the project first** (`pubspec.yaml`, `pubspec.lock`) and to match its existing style.
- **Show both variants** where a package has code generation, in separate blocks labelled "Manual" and "Generated". Never put both declarations in one block.
- **State minimum versions** for any API newer than the package's first release in that major version, and give a fallback.
- **Write distilled guidance, not copies of the upstream docs.** Correct upstream mistakes instead of repeating them.

## Validation

### Setup

Use Python 3, and a Flutter SDK (with its bundled Dart) on your `PATH`; check both with `flutter --version` and `dart --version`. CI uses the latest stable Flutter and Flutter 3.32.8. FVM is optional: to use one of its SDKs, put that version's `bin/` folder first on your `PATH`.

From the repository root:

```sh
python3 tool/check.py               # repository checks (seconds)
python3 tool/validate/run.py        # every validation project (minutes)
python3 tool/validate/run.py dio    # one validation project
```

### What tool/check.py checks

`tool/check.py` checks that:
- all JSON files parse
- the four plugin manifests agree on `name`, `version` and `license`
- each `SKILL.md` has valid front matter (name pattern, description length, the required `metadata` keys)
- each skill is registered in the README and `skills.sh.json`
- `CHANGELOG.md` has a section for the manifest version, or `Unreleased`
- inline relative links and anchors resolve, and no file has an odd number of ```` ``` ```` fences

It doesn't check external or reference-style links, compare `metadata` with the changelog's Sources tables, or verify behaviour claims. For those, cite upstream evidence (a doc page, a test in the package's repository, or its changelog) in your PR description, and review any skipped or expected diagnostics.

### A skill's validation project

Each skill has a small Flutter project in `tool/validate/<skill>/`:

| File | Purpose |
| --- | --- |
| `pubspec.yaml` | the packages the examples need, with major-version ranges only, so each SDK resolves its own newest compatible release |
| `extract.py` | writes each ```` ```dart ```` block to `lib/` or `test/` as a fixture (`<reference>__<n>.dart`). Reuse an existing extractor |
| `lib/stubs.dart` | only the app-specific symbols the examples refer to |
| `validate.json` | configuration (below) |

Generated fixtures, `manifest.json` and lock files are gitignored; keep them out of commits. Run the project on both CI SDKs, and put the resolved versions, skips and smoke-test results in your PR.

`validate.json` keys. The runner (`tool/validate/run.py`) implements some keys and the extractor others:

| Key | Used by | Meaning |
| --- | --- | --- |
| `report` | runner | packages whose resolved versions are printed and used for `requires` |
| `optional_dependencies` | runner | packages to try `flutter pub add` for. The run continues if one can't be added on this SDK, and `pubspec.yaml` is restored afterwards |
| `smoke_tests` | runner | test files (relative paths) to run with `flutter test`: extracted fixtures or hand-written tests |
| `requires` | runner | `{fixture path: {package, min, reason}}`: diagnostics in that file are expected when the resolved package is older than `min`. The file is still extracted and analyzed |
| `skip` | extractor | `{fixture id: reason}`: don't extract this block (e.g. an intentional old-API example) |
| `needs_package` | extractor | `{fixture id: package}`: skip the block when that package isn't in the lock file |
| `tests` | extractor | fixture ids to write to `test/` with test imports (listing them here doesn't run them; add them to `smoke_tests` too) |
| `imports` | extractor | `{fixture id: [other fixture ids]}` for blocks that use declarations from another block |

Fixture ids are numbered by position, so update `validate.json` when you add, remove or reorder code blocks.

## PR checklist

- [ ] Skill folder name matches `name` in its front matter
- [ ] Added or updated the row in the README's **Available skills** table
- [ ] Added the skill to a grouping in `skills.sh.json`
- [ ] Set the changed skill's `metadata.version` to the release that will ship it; leave unchanged skills at the release that last revised them
- [ ] Updated the skill's `metadata` (`docs-read`, `docs-source`, `validated-against`)
- [ ] Added an entry under `## [Unreleased]` in `CHANGELOG.md`, with a Sources row for any skill whose docs you re-read
- [ ] Described the validation you ran (package and SDK versions)

When preparing a release, set all four plugin manifests (`.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/`, `.antigravity-plugin/`) to the new bundle version.

## Code of Conduct

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md).

[issue]: https://github.com/kxgcayh/flutter-curation/issues
