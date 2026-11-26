# Code generation (riverpod_generator)

Code generation is optional. Use it when the project already depends on `riverpod_annotation` + `riverpod_generator`, or the user asks for it. The Riverpod docs recommend it mainly for projects that already run `build_runner` (Freezed, json_serializable), because generation is slow.

## File setup

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart'; // or hooks_riverpod / riverpod
import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'todo_list.g.dart'; // must match this file's name

@riverpod
class TodoList extends _$TodoList {
  @override
  List<Todo> build() => [];
}
```

```sh
dart run build_runner watch   # during development
dart run build_runner build   # one-off, e.g. in CI or after an edit
```

- **Never edit `*.g.dart` by hand.** If generated code is missing or stale, re-run the build.
- **Analyzer errors like `_$TodoList isn't defined` or `todoListProvider isn't defined`** usually mean the build hasn't run, or the `part` directive is wrong.
- **For `build.yaml` options, slow builds, version conflicts between generators, and CI checks,** use the build-runner skill.

## Declarations

| You write | Generated provider kind |
| --- | --- |
| `@riverpod T foo(Ref ref)` | `Provider<T>` |
| `@riverpod Future<T> foo(Ref ref) async` | `FutureProvider<T>` |
| `@riverpod Stream<T> foo(Ref ref)` | `StreamProvider<T>` |
| `@riverpod class Foo extends _$Foo { T build() }` | `NotifierProvider` |
| `... Future<T> build()` | `AsyncNotifierProvider` |
| `... Stream<T> build()` | `StreamNotifierProvider` |

- **The first parameter of a functional provider is always `Ref ref`.** 3.x has no `FooRef` types; replace any you find with `Ref`.
- **A class provider must extend `_$ClassName`** and override `build`.
- **`FutureOr<T>` works too.** An `async` function becomes an `AsyncValue` provider that handles loading and error for you.

## Generated names

- **A function `fooBar` generates `fooBarProvider`.**
- **A class: by default the generator strips a trailing `Notifier` before appending `Provider`.** `TodoList` and `TodoListNotifier` both generate `todoListProvider`. A project's `build.yaml` can configure custom naming, so check it (or the generated `.g.dart`) if a name doesn't resolve.
- **The notifier itself is reached through `fooProvider.notifier`.**

## Annotation options

Each line is a separate annotation option. Place one above its provider declaration.

```dart
@Riverpod(keepAlive: true)          // disable auto-dispose (it is ON by default with codegen)
@Riverpod(dependencies: [])         // mark as scopable (see scopes-and-testing.md)
@Riverpod(dependencies: [currentItemId]) // depends on a scoped provider
@Riverpod(retry: myRetry)           // per-provider retry policy (top-level function)
```

```dart
import 'package:flutter_riverpod/misc.dart' show ProviderException; // or hooks_riverpod/ or riverpod/

Duration? myRetry(int retryCount, Object error) {
  if (retryCount >= 5 || error is ProviderException) return null;
  return Duration(milliseconds: 200 * (1 << retryCount));
}
```

The retry function must return `Duration?`: `null` stops retrying.

## Auto-dispose differs from manual syntax

- **Code generation: auto-dispose is on by default.** Opt out with `@Riverpod(keepAlive: true)`.
- **Manual: providers are kept alive by default.** Opt in with `Provider.autoDispose(...)` or `isAutoDispose: true`.

Converting between the two syntaxes therefore changes lifecycle behaviour unless you set it explicitly. A manual `FutureProvider` with no modifier corresponds to `@Riverpod(keepAlive: true)`, not to plain `@riverpod`.

## Parameters (families)

Any parameters after `ref` (or on `build`) turn the provider into a family. They can be positional, named, optional or defaulted:

```dart
@riverpod
Future<List<Post>> posts(Ref ref, {required String userId, int page = 1}) async {
  return ref.watch(apiProvider).posts(userId, page: page);
}

// usage
ref.watch(postsProvider(userId: '42', page: 2));

@riverpod
class PostEditor extends _$PostEditor {
  @override
  Future<Post> build(String postId) => ref.watch(apiProvider).post(postId);

  Future<void> publish() async {
    // build parameters are exposed as getters on the generated base class
    await ref.read(apiProvider).publish(postId);
  }
}
```

- **Arguments must have stable `==`/`hashCode`,** the same as with manual families.
- **Generics are supported:**

```dart
@riverpod
T multiply<T extends num>(Ref ref, T a, T b) => (a * b) as T;

ref.watch(multiplyProvider<int>(2, 3));
```

## Manual ↔ generated equivalents

| Manual | Generated |
| --- | --- |
| `Provider.autoDispose<String>((ref) => 'foo')` | `@riverpod String example(Ref ref) => 'foo';` |
| `FutureProvider.autoDispose.family<User, int>((ref, id) async {...})` | `@riverpod Future<User> user(Ref ref, int id) async {...}` |
| `NotifierProvider.autoDispose<Counter, int>(Counter.new)` + `class Counter extends Notifier<int>` | `@riverpod class Counter extends _$Counter { int build() => 0; }` |
| `AsyncNotifierProvider.family<Editor, Post, String>(Editor.new)` + `Editor(this.postId)` constructor | `@Riverpod(keepAlive: true) class Editor extends _$Editor { Future<Post> build(String postId) ... }` |

Manual family notifiers take the argument through the constructor (`Editor(this.postId)`), with a parameterless `build()`. Generated notifiers declare it on `build(...)` instead.

## Limitations

- **Providers can't be `static` members** with code generation; they must be top-level.
- **Generated notifiers can't be mocked from another file:** the mock must extend `_$ClassName`, which is library-private. Put the mock in the same Dart library (the file or one of its `part` files), or prefer `overrideWithBuild`/`overrideWith` (see scopes-and-testing.md).
