---
name: flutter-hooks
description: Write, review, debug or migrate Flutter widget lifecycle code that uses flutter_hooks (HookWidget, HookBuilder, useState, useEffect, useMemoized, useRef, useFuture, useStream, useTextEditingController, useAnimationController and other use* hooks). Use for custom hooks, hook ordering and keys, local widget state, controllers, animations, Futures and streams, or converting StatefulWidget code to hooks. In hooks_riverpod widgets, use this skill for local hook behaviour and the riverpod skill for providers and WidgetRef.
metadata:
  version: "0.2.0"
  docs-read: "2026-11-26"
  docs-source: "github.com/rrousselGit/flutter_hooks@1c47821 (2026-11-06): packages/flutter_hooks README, lib/src dartdoc, tests, CHANGELOG"
  validated-against: "source reviewed against flutter_hooks 0.21.4; fixtures compiled with 0.21.3+1 on Flutter 3.44.9 and 3.32.8, and with 0.21.4 on the latest stable Flutter in CI"
---

# flutter_hooks

Hooks are reusable pieces of widget lifecycle logic (`initState` / `didUpdateWidget` / `dispose`) that you call inside `build`. They replace most `StatefulWidget` boilerplate for local, ephemeral state: controllers, animations, focus, subscriptions and form fields.

## Step 1: inspect the project

Read `pubspec.yaml` and `pubspec.lock`:

| Found | Meaning |
| --- | --- |
| `flutter_hooks` | Use `HookWidget` / `StatefulHookWidget` / `HookBuilder` |
| `hooks_riverpod` | Use `HookConsumerWidget` (or `HookConsumer`) when a widget needs both hooks and a `ref`, and `StatefulHookConsumerWidget` if it also needs a `State`. Providers themselves: see the `riverpod` skill |
| `flutter_hooks` 0.21.4+ | Tab, Search, Carousel and Cupertino tab controller hooks are deprecated: use `material_hooks` / `cupertino_hooks` |
| `material_ui` / `cupertino_ui` imports | The project uses the split UI packages. Match its imports, but check the Flutter version in `pubspec.lock` / `flutter --version` rather than inferring it |
| No hooks package | Don't add hooks unless asked: a `StatefulWidget` is fine |

### Version compatibility

| flutter_hooks | Requires | Material / Cupertino controller hooks |
| --- | --- | --- |
| 0.21.2 | Flutter ≥ 3.21.0-13.0.pre.4 | in `flutter_hooks` |
| 0.21.3, 0.21.3+1 | Flutter ≥ 3.32.0 | in `flutter_hooks` |
| 0.21.4 | Flutter ≥ 3.47.0, Dart ^3.6.0 | deprecated in `flutter_hooks`; use `material_hooks` / `cupertino_hooks` 0.1.0 (Flutter ≥ 3.47.0, Dart ^3.13.0; pins flutter_hooks 0.21.4 exactly) |

## The rules of hooks

1. **Call hooks only inside `build`** of a `HookWidget`, `StatefulHookWidget`, `HookConsumerWidget` or a `HookBuilder` / `HookConsumer` builder, or inside another hook function. Never call them in callbacks, `initState` or async code.
2. **Call the same hooks in the same order on every build.** No hooks inside `if`, loops, `switch` or after an early `return`. Hooks are matched by position.
3. **Name custom hooks `useX`,** and build them from other hooks.
4. **Use hooks for local, ephemeral UI state only.** Shared or business state belongs in a state-management solution (Riverpod, Bloc, ...).

```dart
class Counter extends HookWidget {
  const Counter({super.key});

  @override
  Widget build(BuildContext context) {
    final count = useState(0);
    return TextButton(
      onPressed: () => count.value++,
      child: Text('Tapped ${count.value} times'),
    );
  }
}
```

## Keys decide when a hook re-runs

Many hooks take `keys` (a `List<Object?>`). Omitted keys use each hook's default: for `useEffect`, `null` means "every build", while `useMemoized` and `useCallback` default to `const []`. Key lists of equal length are compared element by element with `==` against the previous build (NaN matches NaN; `0.0` and `-0.0` differ). Switching between `null` and a list replaces the hook's state:

| `keys` | `useEffect` | `useMemoized` / `useCallback` | controller hooks (`keys:`) |
| --- | --- | --- | --- |
| omitted | runs on **every** build | computed **once** | created once |
| `const []` | runs once | once | created once |
| `[a, b]` | re-runs when `a` or `b` changes | recomputed when they change | disposed and recreated when they change |

- **Keys need stable `==`.** A new `List`/`Map` literal or a non-`==` object *as a key* changes on every build, so the effect re-runs, or the controller is recreated, every time. Pass a fresh list of stable values, or a const list. Mutating a reused key list in place doesn't trigger anything.
- **The default for `useEffect` is the opposite of `useMemoized`.** Pass explicit keys when an effect should run only on specific changes: `const []` for "once", or the inputs it depends on.

## Common mistakes

- **Creating a Future or Stream inline:** `useFuture(api.load())` calls `load()` on every build. Create it with `useMemoized(() => api.load(), [id])`, then pass it to `useFuture`.
- **Expecting initial arguments to update:** `useState(initial)`, `useTextEditingController(text: x)` and `useAnimationController(initialValue:, lowerBound:, upperBound:)` read their initial values only on the first build. To start over for a new entity, pass `keys: [id]` to the controller hook, or key the widget by the id. Don't push model updates into a controller from `useEffect`; that overwrites the user's edits (see controllers.md).
- **Copying shared state into `useState`/`useRef`:** the copy goes stale. Read the source directly (e.g. `ref.watch(provider)` in a `HookConsumerWidget`).
- **Using `useValueNotifier` for UI state:** it does **not** rebuild the widget. Use `useState`, or listen with `useValueListenable`.
- **Using `useIsMounted` after an `await`:** it's deprecated. Use `if (!context.mounted) return;`.
- **Calling `Hook.use(...)`:** deprecated. Call the top-level `use(...)`.
- **Using `useExpansionTileController`:** deprecated since 0.21.3. Use `useExpansibleController`.

## Choosing a hook

| Need | Hook |
| --- | --- |
| Local value that rebuilds the widget | `useState` |
| Side effect / subscription with cleanup | `useEffect` |
| Cache an object or a Future | `useMemoized` (`useCallback` for functions) |
| Mutable value that must not rebuild | `useRef` |
| Await a Future / listen to a Stream | `useFuture`, `useStream`, `useOnStreamChange` |
| Listen to a `Listenable` / `ValueListenable` | `useListenable`, `useValueListenable`, `useListenableSelector`, `useOnListenableChange` |
| Text field, focus, scroll, page | `useTextEditingController`, `useFocusNode`, `useScrollController`, `usePageController` |
| Animation | `useAnimationController` + a transition widget or `AnimatedBuilder` for localized updates; `useAnimation` only when the whole build needs each value (`useSingleTickerProvider` for a custom controller) |
| Debounce a value (search box) | `useDebounced` |
| React to a value change / keep the previous value | `useValueChanged`, `usePrevious` |
| App lifecycle / brightness | `useAppLifecycleState`, `useOnAppLifecycleStateChange`, `usePlatformBrightness` |
| Complex local state machine | `useReducer` |

## References (load the one the task needs)

| Task | Read |
| --- | --- |
| `useState`, `useEffect`, `useMemoized`, `useRef`, `useCallback`, `useValueChanged`, `usePrevious`, `useReducer` | [primitives.md](references/primitives.md) |
| Futures, streams, `Listenable`s, debouncing | [async-and-listenables.md](references/async-and-listenables.md) |
| Text, focus, scroll, animation, lifecycle and Material/Cupertino controller hooks | [controllers.md](references/controllers.md) |
| Writing custom hooks (function and `Hook` class), testing hooks, hot reload | [custom-hooks.md](references/custom-hooks.md) |
| Converting a `StatefulWidget` to hooks; migrating to 0.21.4 | [migration.md](references/migration.md) |
