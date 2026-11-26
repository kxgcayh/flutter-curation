# build.yaml

`build.yaml` sits next to `pubspec.yaml`. It configures the builders applied to this package: which files they read, and their options. Builders are applied automatically once they're in `dev_dependencies`; you don't need a `build.yaml` to use them.

## Builder keys

A builder is named `<package>:<builder>`, shortened to `<package>` when the two match. Older files use `|` instead of `:`; both work.

| Package | Key | Output |
| --- | --- | --- |
| json_serializable | `json_serializable` | part `*.g.dart` |
| freezed | `freezed` | part `*.freezed.dart` |
| riverpod_generator | `riverpod_generator` | part `*.g.dart` |
| go_router_builder | `go_router_builder` | part `*.g.dart` |
| mockito | `mockito:mockBuilder` | library `*.mocks.dart` (imported) |
| source_gen (shared `.g.dart`) | `source_gen:combining_builder` | merges every `*.g.part` piece into one `*.g.dart` |

json_serializable, riverpod_generator and go_router_builder each write a hidden `.g.part` piece. `source_gen:combining_builder` merges them into the single `*.g.dart` file, so one `part 'x.g.dart';` serves all three.

A misspelled key isn't an error: the build only warns `Ignoring options for unknown builder ...` and uses the defaults.

## Restrict which files a builder reads

```yaml
targets:
  $default:
    builders:
      json_serializable:
        generate_for:
          include:
            - lib/models/**
          exclude:
            - lib/models/legacy/**
```

- **`$default` is the package's own target.** Most apps need only this one.
- **`generate_for`** takes an `include` / `exclude` map, or a plain list of globs that are all includes (`generate_for: [lib/models/**]`). It's the main fix for slow builds: by default each builder reads every Dart file in the package.
- **To turn a builder off** for this package, set `enabled: false` under its key.

## Builder options

Options are builder-specific: check the builder's README. They go under `options:`, with optional `dev_options:` / `release_options:` that apply in dev builds (the default) and `--release` builds.

```yaml
targets:
  $default:
    builders:
      json_serializable:
        options:
          explicit_to_json: true
          field_rename: snake
          include_if_null: false
```

## The shared `.g.dart` file

`source_gen:combining_builder` takes options for the merged file:

```yaml
targets:
  $default:
    builders:
      source_gen:combining_builder:
        options:
          ignore_for_file:
            - type=lint
          preamble: |
            // Generated from annotated sources. Run `dart run build_runner build`.
```

- **`ignore_for_file`** adds `// ignore_for_file:` lines to every generated part. `type=lint` silences all lints but still reports errors and warnings.
- **`preamble`** is text written after the header. `header` (source_gen 4.2+) replaces the default `// GENERATED CODE - DO NOT MODIFY BY HAND` line.
- **Add `source_gen` to `dev_dependencies`** when you configure it: its options are part of source_gen's public API.

## Generate into another folder

```yaml
targets:
  $default:
    builders:
      source_gen:combining_builder:
        options:
          build_extensions:
            '^lib/{{}}.dart': 'lib/generated/{{}}.g.dart'
```

`{{}}` captures the path, so `lib/models/person.dart` writes `lib/generated/models/person.g.dart`. The `part` directive must point there, relative to the source file:

```dart
import 'package:json_annotation/json_annotation.dart';

part '../generated/models/person.g.dart';

@JsonSerializable()
class Person {
  Person({required this.name});

  factory Person.fromJson(Map<String, dynamic> json) => _$PersonFromJson(json);

  final String name;

  Map<String, dynamic> toJson() => _$PersonToJson(this);
}
```

Builders that write their own files, such as `freezed` (`*.freezed.dart`) and `mockito:mockBuilder`, don't go through `combining_builder`. Check their README: mockito takes its own `build_extensions` option.

## Options for every package: `global_options`

```yaml
global_options:
  json_serializable:
    options:
      explicit_to_json: true
```

`global_options` override target options, and can also set `runs_before:` to order builders. You'll rarely need that: builders that read each other's outputs declare their own order.

## Precedence, lowest to highest

1. the builder's defaults (plain, then by mode)
2. target options (plain, then `dev_options` / `release_options`)
3. `global_options` (plain, then by mode)
4. `--define` on the command line

## Extra source folders

Builders only read the standard folders: `lib/`, `bin/`, `test/`, `integration_test/`, `tool/`, `web/`, `example/`, `benchmark/`, `assets/` and `node/`, plus `pubspec.yaml` and a few root files. To include another folder, list every source glob on `$default`, keeping `pubspec.*` and `$package$`:

```yaml
targets:
  $default:
    sources:
      - lib/**
      - test/**
      - schemas/**
      - pubspec.*
      - $package$
```

## Several configurations

`dart run build_runner build -c ci` reads `build.ci.yaml` instead of `build.yaml`. It's a whole replacement, not an overlay.

Defining your own builders (`builders:`, `auto_apply`, `build_extensions`, `triggers`) belongs to builder authors: see the build_config README and `docs/writing_builders.md` in `dart-lang/build`.
