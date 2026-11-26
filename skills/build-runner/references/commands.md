# Commands and flags

Run every command from the package root as `dart run build_runner <command>`. Use `dart run build_runner help <command>` to list the flags of the resolved version.

## Commands

| Command | Does |
| --- | --- |
| `build` | one build of the current package, then exit |
| `watch` | build, then rebuild whenever inputs or `build.yaml` change; leave it running in a terminal while you edit |
| `clean` | delete the build cache in `.dart_tool/build`; the next build starts from scratch. `clean --workspace` clears a workspace build's cache |
| `stop` (2.14+) | stop a running `watch` or `serve` in this package (`--workspace`: in the whole workspace); a build in progress finishes first |
| `test` | build, then run `dart test` with the generated files. Arguments after `--` go to the test runner. For Flutter apps, run `build` and then `flutter test` instead |
| `serve` | build and serve web directories on a local port (web packages and `webdev`) |
| `run` | build, then run a Dart script |
| `daemon` | for IDE and tool integrations; not for interactive use |

Since 2.14, a second command waits for a running one ("Waiting for already-running build_runner"). Starting a `build` while `watch` is running closes the watch after its current build. `daemon` uses its own locking.

## Build flags (`build`, `watch`, `test`, `serve`, `run`)

| Flag | Use |
| --- | --- |
| `--only-check` (2.16+) | write nothing; compare expected outputs with the files on disk, log differences, fail if any. For CI |
| `--keep-modified-outputs` (2.16+) | keep hand edits to generated files (the pre-2.16 behaviour) |
| `--build-filter=<glob>` | build only matching outputs, e.g. `--build-filter='lib/models/*.dart'`. Repeat to OR filters. `package:` URIs refer to another package's `lib/`, and `asset:` URIs (2.14+) to its root |
| `-c <name>` / `--config <name>` | read `build.<name>.yaml` instead of `build.yaml`, e.g. a CI-only configuration |
| `--define=<builder>=<option>=<value>` | set a builder option from the command line, overriding `build.yaml`. Values are parsed as JSON, with the raw string as a fallback |
| `-r` / `--release` | use builders' `release_options` instead of `dev_options` |
| `-o <dir>` / `--output <dir>` | also copy the fully built package to a directory (`web:deploy` maps one top-level folder) |
| `--workspace` (`build`, `watch`; 2.11+, stable in 2.14) | build every package of the pub workspace together, with one `.dart_tool` at the workspace root |
| `-v` / `--verbose` | show what builders log, and why steps re-run |
| `--force-jit` / `--force-aot` | choose how builders are compiled. AOT is the default since 2.14, falling back to JIT for builders that use `dart:mirrors` |
| `--dart-jit-vm-arg=<arg>` | pass a VM flag to the builder process (debugging, below) |
| `--enable-experiment=<name>` | enable a Dart language experiment for builders and their analysis |

Removed flags still parse but do nothing: `-d` / `--delete-conflicting-outputs` (since 2.7), `--low-resources-mode`, `--log-performance` and `--track-performance` (since 2.15).

## Debugging a builder

Builders run in a child process. To attach a debugger, force JIT and pass the VM flags through:

```sh
dart run build_runner build --force-jit \
  --dart-jit-vm-arg=--observe --dart-jit-vm-arg=--pause-isolates-on-start
```

The process prints a DevTools URL; in VS Code use "Debug: Attach to Dart Process" with it. On Linux, `--dart-aot-perf` (with `--force-aot`) records a `perf` profile.
