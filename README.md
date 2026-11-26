# Flutter Curation

Curated agent skills for popular Flutter packages.

Agents often write Flutter code against outdated APIs: Riverpod 2.x syntax in a 3.x project, legacy providers, or examples that no longer compile. Each skill here teaches an agent how one package works today: which API to pick, the rules that prevent common bugs, and what changed between versions. Each skill has a short `SKILL.md` with detailed reference files that the agent loads only when a task needs them.

The skills work in Claude Code, Codex, Cursor, Antigravity and any agent that supports [Agent Skills](https://skills.sh).

## Installation

### Claude Code

```
/plugin marketplace add kxgcayh/flutter-curation
/plugin install flutter-curation@flutter-curation
```

### Codex

Add this repository as a marketplace, then install the plugin:

```sh
codex plugin marketplace add kxgcayh/flutter-curation
codex plugin add flutter-curation@flutter-curation
```

Check it with `codex plugin list`, which should show `installed, enabled`. To use the skill without a plugin, copy the folder instead:

```sh
git clone https://github.com/kxgcayh/flutter-curation.git
mkdir -p ~/.agents/skills
cp -R flutter-curation/skills/riverpod ~/.agents/skills/
```

### Cursor

Add this repository as a Cursor plugin. It ships `.cursor-plugin/plugin.json`, which points at `skills/`.

### Antigravity (agy CLI and IDE)

Install the plugin from GitHub. It goes into `~/.gemini/config/plugins/` and loads in both the CLI and the IDE:

```sh
agy plugin install https://github.com/kxgcayh/flutter-curation
```

`agy plugin install` needs the full HTTPS URL; the `owner/repo` shorthand doesn't work. Antigravity can't add this repo as a marketplace. Alternatively, use skills.sh below, which installs to `.agents/skills/` in a project, or `~/.gemini/config/skills/` with `-g`.

### skills.sh

```sh
npx skills add kxgcayh/flutter-curation      # this project
npx skills add kxgcayh/flutter-curation -g   # all projects
```

### Manual

Copy any folder under [`skills/`](skills/) into your agent's skills directory, for example `.claude/skills/` or `.agents/skills/` in a project.

## Available skills

| Skill | Description | Example prompt |
| --- | --- | --- |
| [riverpod](skills/riverpod/SKILL.md) | Write, review, debug or migrate Riverpod 3.x code (`riverpod`, `flutter_riverpod`, `hooks_riverpod`, `riverpod_generator`). Covers providers and notifiers, `ref.watch`/`read`/`listen`, `AsyncValue`, auto-dispose and families, overrides and testing, and migration from Riverpod 2.x, StateNotifier, ChangeNotifier or package:provider. | Migrate this StateNotifier to an AsyncNotifier and add a unit test for it |

## Compatibility

Skills target the current major version of each package, and say when an API needs a newer minor release. The project's Dart SDK decides which release it can install. For example, Flutter 3.32 (Dart 3.8) can use at most Riverpod 3.3.2, or 3.1.0 with code generation. See the riverpod skill's [version compatibility table](skills/riverpod/SKILL.md#version-compatibility).

## How skills are made

1. Each skill is written from the package's official documentation, and keeps the upstream syntax for both manual and code-generated variants.
2. Every Dart code block is compiled against the latest published packages, with `build_runner` and `dart analyze`, and against the oldest Flutter SDK the skill supports. CI repeats this on every pull request and weekly (see `tool/validate/`).
3. Behaviour claims (lifecycles, error handling, retry, version-gated APIs) are checked against the package's own test suite and changelog.
4. Mistakes found in upstream docs are corrected in the skill, not copied.

Each skill's front matter records when its docs were read (`metadata.docs-read`) and which versions it was validated against. [CHANGELOG.md](CHANGELOG.md) keeps the history per release.

## Contributing

Bug reports, skill requests and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Code of Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## License

[MIT](LICENSE)
