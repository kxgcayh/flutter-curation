# Flutter Curation

Agent skills for Riverpod 3.x, Flutter Hooks and Dio 5.x.

Agents often write Flutter code against outdated APIs: Riverpod 2.x syntax in a 3.x project, legacy providers, or examples that no longer compile. Each skill teaches an agent how one package works today: which API to pick, the rules that prevent common bugs, and what changed between versions. Each skill has a short `SKILL.md`, plus reference files that the agent loads only when a task needs them.

The skill folders follow the [Agent Skills specification](https://agentskills.io/specification). This repository also includes plugin manifests for Claude Code, Codex, Cursor and Antigravity.

## Installation

These commands install the skills from GitHub's default branch. The current release is listed on the [releases page](https://github.com/kxgcayh/flutter-curation/releases).

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

Check it with `codex plugin list`, which should show `installed, enabled`.

### Cursor

From the Cursor project, install the skills with skills.sh:

```sh
npx skills add kxgcayh/flutter-curation -a cursor
```

To test the plugin locally, copy it to `~/.cursor/plugins/local/flutter-curation/`, including `.cursor-plugin/plugin.json` and `skills/`. Then reload Cursor and check **Customize**. Local plugin imports must be enabled.

### Antigravity

Install with the Antigravity CLI (`agy`), then confirm with `agy plugin list`:

```sh
agy plugin install https://github.com/kxgcayh/flutter-curation
```

To install individual skills instead, use `npx skills add kxgcayh/flutter-curation -a antigravity`. Add `-g` to install for the current user.

### skills.sh

Requires Node.js and `npx`. Run it from the target project:

```sh
npx skills add kxgcayh/flutter-curation                    # this project
npx skills add kxgcayh/flutter-curation --skill riverpod   # one skill
npx skills add kxgcayh/flutter-curation -g                 # current user, all projects
```

Use `-a <agent>` to choose the agent.

### Manual

Copy a whole folder under [`skills/`](skills/), including its `SKILL.md` and `references/`, into the target project's skills directory: for example `.claude/skills/` for Claude Code, or `.agents/skills/` for Codex.

```sh
git clone https://github.com/kxgcayh/flutter-curation.git
mkdir -p .agents/skills
cp -R flutter-curation/skills/riverpod .agents/skills/
```

## Available skills

| Skill | Description | Example prompt |
| --- | --- | --- |
| [riverpod](skills/riverpod/SKILL.md) | Write, review, debug or migrate Riverpod 3.x code (`riverpod`, `flutter_riverpod`, `hooks_riverpod`, `riverpod_generator`). Covers providers and notifiers, `ref.watch`/`read`/`listen`, `AsyncValue`, auto-dispose and families, overrides and testing, and migration from Riverpod 2.x, StateNotifier, ChangeNotifier or package:provider. | Migrate this StateNotifier to an AsyncNotifier and add a unit test for it |
| [flutter-hooks](skills/flutter-hooks/SKILL.md) | Write, review or refactor widgets that use `flutter_hooks` (`HookWidget`, `useState`, `useEffect`, `useMemoized`, `useFuture`, controller and animation hooks), write custom hooks, or convert a `StatefulWidget` to hooks. Covers the rules of hooks, how `keys` decide re-runs, and the 0.21.4 move of Material/Cupertino hooks to `material_hooks`/`cupertino_hooks`. | Convert this StatefulWidget with a TextEditingController and an AnimationController to a HookWidget |
| [dio](skills/dio/SKILL.md) | Write, review, debug or migrate HTTP code that uses `dio` and its plugins: shared `Dio` setup, interceptors and `QueuedInterceptor` token refresh, `DioException` handling, cancellation, uploads and downloads, adapters, certificate checks, and tests that fake the adapter. Covers dio 4.x → 5.x and the APIs deprecated before 6.0. | Add a dio interceptor that refreshes the access token on 401 and retries the request once |

## Compatibility

Each skill documents the package version it targets, and the version gates for the APIs it shows. Check your project's SDK and `pubspec.lock` before using those APIs. For example, Flutter 3.32 (Dart 3.8) can use at most Riverpod 3.3.2, or 3.1.0 with code generation; see the Riverpod skill's [version compatibility table](skills/riverpod/SKILL.md#version-compatibility).

## How skills are made

1. **Sources:** each skill distils the package's official documentation, implementation source, release notes and targeted upstream tests. Where a package supports both handwritten and generated APIs, the skill shows both when that's useful.
2. **Validation:** a validator extracts the skill's Dart code blocks, supplies minimal app stubs, runs code generation where configured, analyzes the results and runs selected smoke tests. It uses the package versions that resolve on the chosen Flutter SDK, and records any examples it skips or expects to fail on older versions.
3. **CI** validates changes to skills and validation tooling on the latest stable Flutter and on Flutter 3.32.8, and also runs weekly. Contributors check behaviour claims against upstream evidence.
4. **Corrections:** mistakes found in upstream docs are corrected in the skill, not copied.

Each skill's front matter records when its docs were read (`metadata.docs-read`) and what it was validated against. [CHANGELOG.md](CHANGELOG.md) keeps the history per release.

## Contributing

Bug reports, skill requests and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Code of Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## License

[MIT](LICENSE)
