# Skill validation

`run.py` compiles every Dart code block of a skill against the packages that `flutter pub get` resolves for the Flutter SDK on your PATH:

```sh
python3 tool/validate/run.py            # all skills
python3 tool/validate/run.py riverpod   # one skill
```

Each `<skill>/` folder is a small Flutter project:

| File | Purpose |
| --- | --- |
| `extract.py` | writes each code block to `lib/` or `test/` as `<reference>__<n>.dart`, wrapping fragments in a function where needed |
| `lib/stubs.dart` | minimal app types (`Todo`, `User`, `apiProvider`, ...) the snippets refer to |
| `pubspec.yaml` | major-version ranges only, so each SDK resolves its own newest compatible release |
| `validate.json` | `smoke_tests` to execute, and `requires`: fixtures expected to fail below a package version |

`build-runner/` is different: its skill is mostly YAML. `extract.py` turns each `build.yaml` block into `cases/<reference>__<n>/`, a copy of the fixture with that block as its `build.yaml`. `run.py` builds each case, fails on build_runner warnings not listed in `allowed_warnings` (an unknown builder key, a missing `part`), and analyzes the output. `commands` adds `build_runner build --only-check` where build_runner 2.16+ resolves.

Generated fixtures, `cases/`, `manifest.json` and `pubspec.lock` are gitignored.
