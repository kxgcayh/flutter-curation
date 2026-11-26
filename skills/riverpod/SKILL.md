---
name: riverpod
description: Write, review, debug or migrate Riverpod 3.x code in Flutter and Dart. Use for riverpod, flutter_riverpod, hooks_riverpod, riverpod_generator and @riverpod code, including Notifier/AsyncNotifier, ref.watch/read/listen, provider lifecycles and auto-dispose, AsyncValue, ProviderScope overrides, testing providers, and migrating to Riverpod 3 from Riverpod 2.x, StateNotifier, ChangeNotifier or package:provider.
---

# Riverpod 3.x

Riverpod is a reactive cache and dependency-injection framework for Dart and Flutter. Providers declare how state is computed. A `ProviderContainer` (a `ProviderScope` in Flutter) stores that state. `Ref` and `WidgetRef` read and listen to it.

## Step 1: inspect the project before writing code

Read `pubspec.yaml` (and `pubspec.lock` when present) and match the project's existing style:

| Found | Meaning |
| --- | --- |
| `flutter_riverpod` | Flutter widget integration, no hooks |
| `hooks_riverpod` + `flutter_hooks` | Flutter app with hooks: use `HookConsumerWidget` |
| `riverpod` only | Pure Dart (CLI/server): use `ProviderContainer` |
| `riverpod_annotation` + `riverpod_generator` + `build_runner` | Code generation: write `@riverpod` providers and keep `part '<file>.g.dart';` |
| riverpod `< 3.0` in the lock file | 2.x project: read [migration.md](references/migration.md) before changing APIs |
| `riverpod_lint` in `analysis_options.yaml` | Lints active: keep code statically analysable |

- **Follow the project's syntax.** If it uses code generation, write `@riverpod`. If not, write manual providers. Don't add code generation on your own: the Riverpod docs recommend it only when a project already runs `build_runner` for other packages (Freezed, json_serializable).
- **New project, no preference given:** for Flutter, use manual syntax with `flutter_riverpod`. For pure Dart, use `riverpod`. Consider adding the optional `riverpod_lint` plugin. Setup details are in [flutter-and-hooks.md](references/flutter-and-hooks.md).
- **After editing `@riverpod` code,** run `dart run build_runner build` (or check that `watch` is running). Never hand-edit `.g.dart` files.

## Step 2: choose the provider

|  | Sync | Future | Stream |
| --- | --- | --- | --- |
| Read-only (functional) | `Provider` | `FutureProvider` | `StreamProvider` |
| Modifiable (notifier) | `NotifierProvider` | `AsyncNotifierProvider` | `StreamNotifierProvider` |

- **Read-only:** use a function provider when the value is derived and widgets never change it directly.
- **Notifier:** use one when the UI calls methods to change the state, e.g. `ref.read(todoListProvider.notifier).add(todo)`.
- **Code generation picks the type** from the return type: `T`, `Future<T>` or `Stream<T>`, written as a function or as a class with `build()`.
- **Not in 3.x code:** never write new `StateProvider`, `StateNotifierProvider` or `ChangeNotifierProvider`. Use `Notifier` instead. They survive only for older code: `StateProvider` and `StateNotifierProvider` under the matching package's `legacy.dart`; `ChangeNotifierProvider` is Flutter-only, under `package:flutter_riverpod/legacy.dart` or `package:hooks_riverpod/legacy.dart`.

Choose one variant, and keep manual and generated declarations in separate files.

Manual:

```dart
final todoListProvider = NotifierProvider<TodoList, List<Todo>>(TodoList.new);

class TodoList extends Notifier<List<Todo>> {
  @override
  List<Todo> build() => [];

  void add(Todo todo) => state = [...state, todo];
}
```

Generated (this declares `todoListProvider`):

```dart
@riverpod
class TodoList extends _$TodoList {
  @override
  List<Todo> build() => [];

  void add(Todo todo) => state = [...state, todo];
}
```

Details are in [providers-and-refs.md](references/providers-and-refs.md) and [code-generation.md](references/code-generation.md).

## Core rules

1. **Declare providers as top-level `final` variables** (or `@riverpod` top-level functions and classes). Never create providers inside classes, widgets or functions.
2. **Use `ref.watch` in `build`** (in widgets and in providers) to read state and rebuild when it changes. This is the default choice.
3. **Use `ref.read` only in callbacks** such as `onPressed` and notifier methods. Never use it in `build` to "avoid rebuilds". Use `select` for that.
4. **Use `ref.listen` for side effects** such as dialogs, snackbars, navigation and logging. In widgets, call it inside `build`. Outside `build` (e.g. `initState`), use `ref.listenManual`.
5. **Put logic in a Notifier's `build()`,** never in its constructor: `ref` and `state` don't exist yet at that point. Never call `build()` yourself.
6. **Keep state immutable:** assign a new value with `state = [...state, x]` or `copyWith`. Mutating in place does not notify listeners, because 3.x filters updates with `==`.
7. **Don't run write operations in a provider's initializer** (form submits, POST requests). Providers represent reads. Use a Notifier method, or a mutation (experimental).
8. **Don't store ephemeral UI state in providers:** form fields, the selected tab, animations and `TextEditingController`s belong in the widget (`StatefulWidget` or hooks).
9. **Check `ref.mounted` after every `await`** in providers and notifiers before touching `ref` or `state`. In notifier methods, capture `final operationRef = ref;` first and check `operationRef.mounted`. A disposed `Ref` throws `UnmountedRefException`. In widgets, check `context.mounted` before using `ref` after an `await`.
10. **Family parameters need stable `==`/`hashCode`.** Use primitives, records, Freezed or `==`-overriding classes, never a fresh `List` or `Map` literal. Enable auto-dispose on families.
11. **Start the app with `ProviderScope`:** `runApp(const ProviderScope(child: MyApp()))`. Pure Dart uses `ProviderContainer`, and must `dispose()` it.
12. **Reset dependent state by watching its source.** There is no "reset all providers". For logout, make user-dependent providers `ref.watch` the auth/user provider.

## AsyncValue quick reference

`FutureProvider`, `StreamProvider` and async notifiers expose `AsyncValue<T>`, which is sealed:

```dart
final user = ref.watch(userProvider);
return switch (user) {
  // Matches whenever data exists, including during refresh and reload.
  AsyncValue(:final value?) => Text(value.name),
  AsyncValue(:final error?) => Text('Error: $error'),
  _ => const CircularProgressIndicator(), // first load
};
```

- **A forced refresh can still match `AsyncData`,** with `isLoading == true`. A dependency reload matches `AsyncLoading` but may still carry the previous data in `value`. Check `value` and `isLoading` instead of relying on the subtype alone.
- **`value` is nullable** (it replaced 2.x `valueOrNull`). `requireValue` throws if there's no data; use it only when the value is guaranteed, for example after eager initialization.
- **`await ref.watch(p.future)`** inside a provider gets the value itself. `ref.refresh(p.future)` returns a Future, which suits `RefreshIndicator.onRefresh`.
- **In notifier methods:** set `state = const AsyncLoading();`, then `state = await AsyncValue.guard(() => repo.save(x));`.

More is in [async-and-performance.md](references/async-and-performance.md).

## Behaviour that changed in 3.0 (often missed)

- **Failing providers retry automatically:** up to 10 times, with backoff from 200 ms to 6.4 s. `Error`s and `ProviderException`s are not retried. Customise it with `retry:` on the provider or on the `ProviderScope`.
- **When a provider computation fails, a throwing read or its failed `.future` usually wraps the original error in `ProviderException`.** Reading an async provider itself gives an `AsyncValue` whose `error` holds the original failure. Since Riverpod 3.5, disposing a provider before it emits can complete `.future` directly with `ProviderDisposedException`. `ProviderException` is imported from `package:flutter_riverpod/misc.dart` (or `hooks_riverpod/` or `riverpod/`). `ref.listen(onError:)` and observers also receive the original error.
- **Listeners in widgets that aren't visible are paused** (this follows `TickerMode`), and so are providers used only by paused providers.
- **All providers filter updates with `==`.** Override `updateShouldNotify` on a Notifier to change that.
- **Interfaces were merged:** there is one `Ref` with no type parameter (no `FooRef` subclasses), no `AutoDispose*` classes and no `Family*` notifier classes.

## References (load the one the task needs)

| Task | Read |
| --- | --- |
| Provider types, Notifier patterns, watch/read/listen, invalidate/refresh, Ref lifecycle | [providers-and-refs.md](references/providers-and-refs.md) |
| Install, `ProviderScope`, consumer widgets, hooks, eager initialization | [flutter-and-hooks.md](references/flutter-and-hooks.md) |
| `@riverpod` syntax, generated names, parameters, build_runner | [code-generation.md](references/code-generation.md) |
| Auto-dispose, `keepAlive`, families, caching, cleanup | [lifecycle-and-caching.md](references/lifecycle-and-caching.md) |
| AsyncValue UI, pull-to-refresh, retry, debounce/cancel, `select` | [async-and-performance.md](references/async-and-performance.md) |
| Overrides, scoping, observers, unit and widget tests | [scopes-and-testing.md](references/scopes-and-testing.md) |
| Riverpod 2.x → 3.x, StateNotifier, ChangeNotifier, package:provider | [migration.md](references/migration.md) |
| Mutations and offline persistence (experimental APIs) | [experimental.md](references/experimental.md) |
