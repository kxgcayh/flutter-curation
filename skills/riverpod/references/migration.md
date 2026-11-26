# Migration

## Riverpod 2.x → 3.x

Upgrade carefully: some changes are behavioural, not compile errors. Work through this checklist:

| 2.x | 3.x | Action |
| --- | --- | --- |
| `AutoDisposeNotifier`, `AutoDisposeProvider`, `AutoDisposeRef`, ... | unified `Notifier`, `Provider`, `Ref` | Case-sensitive replace of `AutoDispose` with nothing. Behaviour is unchanged. |
| `FamilyNotifier<T, Arg>` with `build(Arg arg)` | `Notifier<T>` with constructor `Foo(this.arg)` and `build()` | Same for `FamilyAsyncNotifier` and `FamilyStreamNotifier`. Codegen keeps parameters on `build`. |
| `FooRef ref` (generated Ref subclasses), `Ref<T>` | `Ref ref` | Replace in every `@riverpod` function. |
| `ref.state`, `ref.listenSelf`, `ref.future` on Ref | `state`, `listenSelf`, `future` on Notifier | Convert the functional provider into a Notifier class. |
| `StateProvider`, `StateNotifierProvider` | moved to the matching package's `legacy.dart` (`riverpod`, `flutter_riverpod` or `hooks_riverpod`) | Change the import now; plan a rewrite to `Notifier`. |
| `ChangeNotifierProvider` | Flutter-only: `package:flutter_riverpod/legacy.dart` or `package:hooks_riverpod/legacy.dart` | Same. |
| `AsyncValue.valueOrNull` | `AsyncValue.value` | Global replace. The old `value` (which threw on error) is gone; use `requireValue` where you want a throw. |
| `ProviderObserver.didUpdateProvider(provider, prev, next, container)` | `didUpdateProvider(ProviderObserverContext context, prev, next)` | Same for every observer method. |
| errors rethrown as-is | a throwing read or failed `.future` usually wraps them in `ProviderException` (import it from `misc.dart`); since 3.5, disposal before the first value can complete `.future` with `ProviderDisposedException` | Update `try/catch`: `on ProviderException catch (e) { e.exception ... }`. `AsyncValue.error` is unchanged. |
| no retry | automatic retry (up to 10 retries after the first attempt, with backoff) | Decide per app: keep it, customise it, or disable with `retry: (_, _) => null` on `ProviderScope`. |
| listeners always active | out-of-view widgets (`TickerMode` false) pause their listeners | Streams and polling stop on covered routes. Wrap in `TickerMode(enabled: true)` if something must keep running. |
| mixed `==`/`identical` filtering | everything filters with `==` | Stream events equal to the previous one are dropped. Override `updateShouldNotify` if needed. |
| using a disposed `Ref` was silently allowed | throws `UnmountedRefException` | Add `if (!ref.mounted) return;` after `await`s in notifiers and providers. |
| custom `createContainer()` test helper | `ProviderContainer.test()` | Global replace. |
| — | `overrideWithBuild`, `Future/StreamProvider.overrideWithValue`, `tester.container()` | New test utilities. |

## From StateNotifier

```dart
// Before
class Counter extends StateNotifier<int> {
  Counter(this.ref) : super(0);
  final Ref ref;
  void increment() => state++;
}
final counterProvider = StateNotifierProvider<Counter, int>((ref) => Counter(ref));

// After
class Counter extends Notifier<int> {
  @override
  int build() => 0;          // initial state lives in build
  void increment() => state++;
}
final counterProvider = NotifierProvider<Counter, int>(Counter.new);
```

- **Initial state goes in `build()`, not `super(...)`.** `ref` is a built-in property, so don't pass it in.
- **`build()` can `ref.watch` dependencies,** and the notifier rebuilds when they change. A StateNotifier had to be recreated for that.
- **Async state:** a `StateNotifier<AsyncValue<T>>` that loaded in its constructor becomes an `AsyncNotifier<T>` whose `build()` returns `Future<T>`. Loading and error states come for free.
- **Replace `dispose()` with `ref.onDispose(...)` in `build()`,** and `mounted` with `ref.mounted`.
- **`.addListener`/`.stream` → `ref.listen` or `container.listen`.** `debugState` in tests → read the provider.
- **Modifiers are explicit:** `NotifierProvider.autoDispose`/`.family`, or `@riverpod`, which is auto-dispose by default.

## From StateProvider

```dart
// Before
final filterProvider = StateProvider<Filter>((ref) => Filter.all);
ref.read(filterProvider.notifier).state = Filter.done;

// After
final filterProvider = NotifierProvider<FilterNotifier, Filter>(FilterNotifier.new);
class FilterNotifier extends Notifier<Filter> {
  @override
  Filter build() => Filter.all;
  void set(Filter value) => state = value;
}
ref.read(filterProvider.notifier).set(Filter.done);
```

## From ChangeNotifier / ChangeNotifierProvider

- **Fields become immutable state.** Several mutable fields plus `notifyListeners()` become one immutable state class (Freezed, or a class with `copyWith`) held by a `Notifier`/`AsyncNotifier`.
- **Hand-tracked flags go away.** Manual `isLoading`/`error` fields become `AsyncNotifier` + `AsyncValue`. For a side effect's loading state, use a mutation (experimental).
- **Async initialisation moves into `build()`** instead of being called from the UI.
- **Migrate gradually:** first move the existing `ChangeNotifier` behind a legacy `ChangeNotifierProvider` (`package:flutter_riverpod/legacy.dart`), then convert it into a Notifier one class at a time.

## From package:provider

- **Both packages can run side by side** (`ProviderScope` plus provider's `MultiProvider`), so migrate one provider at a time. Start with leaves, the providers that depend on nothing.
- **`context.watch<T>()` / `context.read<T>()` → `ref.watch(tProvider)` / `ref.read(...)`** in a `ConsumerWidget`.
- **`ProxyProvider` → a provider that `ref.watch`es its dependencies.** This needs no special API.
- **Lazy by default:** provider's `lazy: false` becomes the eager-initialisation widget pattern (see flutter-and-hooks.md).
- **Providers aren't looked up by type,** so several providers of the same type are fine.

## Riverpod ≤ 1.x

Code still using `ScopedReader`, `watch(provider)` as a function parameter, `ProviderReference` or 0.x syntax must first be brought to the 2.x API, then to 3.x. Don't copy "after" snippets from the 0.13→0.14 or 0.14→1.0 guides into new code: those APIs are obsolete.
