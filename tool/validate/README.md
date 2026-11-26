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

Generated fixtures, `manifest.json` and `pubspec.lock` are gitignored.
