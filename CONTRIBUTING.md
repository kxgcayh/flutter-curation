# Contributing to Flutter Curation

Thanks for helping improve these skills. Bug reports, skill requests and pull requests are all welcome.

## Reporting a problem with a skill

[File an issue][issue] and include:

1. **The model:** for example Claude Opus 5.5, GPT-6.2 or Gemini 3.1 Pro.
2. **The agent:** for example Claude Code, Codex, Cursor or Gemini CLI.
3. **Logs:** the prompt you used and the steps the agent took, including which skill and reference files it loaded and the code it produced.

Also give the package version from your `pubspec.lock` and your Flutter/Dart version (`flutter --version`), since many bugs are version-specific.

## Requesting a skill

Check the [open issues][issue] first, and add a 👍 or a comment if the package is already requested. Otherwise, open an issue that names the package and describes tasks agents get wrong today.

## Adding or changing a skill

### Layout

```
skills/<package>/
├── SKILL.md            # short entry point: setup checks, core rules, index of references
└── references/
    └── <topic>.md      # depth, loaded only when a task needs it
```

### SKILL.md front matter

```yaml
---
name: <package>          # must match the folder name; lowercase letters, digits and hyphens
description: <what the skill does and when to use it, under 1024 characters>
metadata:
  version: "0.1.0"       # the repo release this skill ships in
  docs-read: "YYYY-MM-DD" # when the package's official docs were last read
  docs-source: "<doc URLs, plus repo@commit if you used examples or tests>"
  validated-against: "<package versions and Flutter SDK the snippets compiled on>"
---
```

Update `docs-read`, `docs-source` and `validated-against` whenever you re-read the docs or re-validate. The same values go in the release's **Sources** table in [CHANGELOG.md](CHANGELOG.md).

The description decides when an agent loads the skill. Name the package and the tasks it covers. Avoid generic words that would trigger it for unrelated work.

### Writing guidelines

- **Keep `SKILL.md` short** (roughly under 150 lines), and put detail in `references/`. Link every reference from a table in `SKILL.md`.
- **Tell the agent to inspect the project first** (`pubspec.yaml`, `pubspec.lock`) and to match its existing style.
- **Show both variants** where a package has code generation, in separate blocks labelled "Manual" and "Generated". Never put both declarations in one block.
- **State minimum versions** for any API newer than the package's first release in that major version, and give a fallback.
- **Write distilled guidance, not copies of the upstream docs.** Correct upstream mistakes instead of repeating them.

### Validation before opening a PR

- **Every Dart code block compiles** against the latest published package (`dart run build_runner build` and `dart analyze` with no issues), using only minimal stubs for app-specific types. Fragments may be wrapped in a function or widget for compiling.
- **If the skill names an oldest supported SDK, compile there too.**
- **Behaviour claims are backed:** cite the upstream doc page, a test in the package's repository, or the changelog in your PR description.
- **Every relative link resolves,** and every code fence is closed.

### PR checklist

- [ ] Skill folder name matches `name` in its front matter
- [ ] Added or updated the row in the README's **Available skills** table
- [ ] Added the skill to a grouping in `skills.sh.json`
- [ ] Bumped `version` the same way in `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, `.cursor-plugin/plugin.json` and `.antigravity-plugin/plugin.json`
- [ ] Updated the skill's `metadata` (`docs-read`, `docs-source`, `validated-against`)
- [ ] Added an entry under `## [Unreleased]` in `CHANGELOG.md`, with the sources row for any skill whose docs you re-read
- [ ] Described the validation you ran (package and SDK versions)

## Code of Conduct

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md).

[issue]: https://github.com/kxgcayh/flutter-curation/issues
