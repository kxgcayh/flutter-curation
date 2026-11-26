# Lifecycle, auto-dispose, families and caching

## When state is destroyed

1. **On recompute:** a watched dependency changed, or someone called `invalidate`/`refresh`. The old state is disposed and `onDispose` runs. This happens whether or not auto-dispose is on.
2. **On auto-dispose:** the provider has auto-dispose enabled and its listener count drops to 0. Then `onCancel` fires, Riverpod waits one frame, and if there is still no listener the provider is disposed and `onDispose` fires.

Listeners are created by `ref.watch` and `ref.listen` (and `container.listen`). **`ref.read` doesn't count,** so a provider that is only `read` can be disposed between reads.

## Enabling auto-dispose

Manual (kept alive unless you opt in):

```dart
final searchProvider = FutureProvider.autoDispose<Results>(
  (ref) => ref.watch(apiProvider).search(),
);
final labelProvider = Provider<String>(isAutoDispose: true, (ref) => 'Hello');
```

Generated (auto-dispose by default; opt out):

```dart
@Riverpod(keepAlive: true)
Future<Config> config(Ref ref) => ref.watch(apiProvider).config();
```

- **Enable auto-dispose on families.** Without it, every argument ever used stays in memory.
- **Keep alive only state that is truly app-wide:** auth, config, repositories, storage.

## Conditional keep-alive

`ref.keepAlive()` (on an auto-dispose provider) stops disposal until the returned link is closed, or until the provider recomputes:

```dart
@riverpod
Future<Product> product(Ref ref, String id) async {
  final p = await ref.watch(apiProvider).product(id);
  if (!ref.mounted) return p;
  ref.keepAlive(); // cache only successful responses
  return p;
}
```

To keep state alive for a fixed interval, measured from the `cacheFor` call:

```dart
extension CacheFor on Ref {
  void cacheFor(Duration duration) {
    final link = keepAlive();
    final timer = Timer(duration, link.close);
    onDispose(timer.cancel);
  }
}

@riverpod
Future<Feed> feed(Ref ref) async {
  ref.cacheFor(const Duration(minutes: 5));
  return ref.watch(apiProvider).feed();
}
```

A variant can use `onCancel`/`onResume` to start the timer only once nobody is listening.

## Cleanup

Register one `onDispose` per resource: controllers, sockets, timers, HTTP clients, subscriptions.

```dart
@riverpod
Stream<int> counter(Ref ref) {
  final controller = StreamController<int>();
  ref.onDispose(controller.close);
  return controller.stream;
}
```

`onDispose` callbacks must not modify other providers.

## Disposed refs and `ref.mounted`

In 3.x, using a `Ref` or Notifier after it has been disposed throws `UnmountedRefException`. This commonly happens after an `await`, if the provider was rebuilt or disposed in the meantime.

```dart
Future<void> addTodo(String title) async {
  final operationRef = ref; // capture: a rebuild mid-await unmounts this ref
  final todo = await operationRef.read(apiProvider).add(title);
  if (!operationRef.mounted) return;
  state = [...state, todo];
}
```

Inside an initializer, throwing after disposal is safe and is a common way to abort (Riverpod ignores it): `if (!ref.mounted) throw const Cancelled();`.

## Families

A family is a map from arguments to independent states.

```dart
// Manual: a single positional argument; use a record or a Freezed class for several.
final userProvider = FutureProvider.autoDispose.family<User, String>((ref, id) async {
  return ref.watch(apiProvider).user(id);
});

final userEditorProvider =
    AsyncNotifierProvider.autoDispose.family<UserEditor, User, String>(UserEditor.new);

class UserEditor extends AsyncNotifier<User> {
  UserEditor(this.id);
  final String id;

  @override
  Future<User> build() => ref.watch(apiProvider).user(id);
}

// usage
ref.watch(userProvider('42'));
```

- **Arguments are map keys and need stable `==`/`hashCode`.** `ref.watch(p([1, 2]))` creates a new state on every build. Use primitives, records, Freezed classes or const objects. `riverpod_lint` flags this (`provider_parameters`).
- **Several arguments on a manual family** go in a record: `family<Page, ({String q, int page})>` and `p((q: 'x', page: 1))`.
- **Invalidating:** `ref.invalidate(userProvider)` drops all arguments; `ref.invalidate(userProvider('42'))` drops one.
- **Enumerating live family members:** Riverpod 3.3.2+ exposes them through `ref.container.allProviders(family: userProvider)`. On earlier 3.x versions this doesn't exist. To invalidate a whole family on any 3.x version, call `ref.invalidate(userProvider)`.

```dart
// Riverpod >= 3.3.2
for (final element in ref.container.allProviders(family: userProvider)) {
  print(element.provider);
}
```

## Pausing (3.x)

- **Out of sight:** listeners in widgets where `TickerMode` is false (e.g. routes covered by another route) are paused, and the providers they use pause too. Wrap a subtree in `TickerMode(enabled: true, child: ...)` to keep it live, or `false` to force a pause.
- **Indirect use:** a provider used only by paused providers is paused.
- **During rebuilds:** old subscriptions are paused, not removed, until the rebuild completes. So watching an auto-dispose provider after an `await` no longer disposes it mid-rebuild.
- **Resuming** triggers `onResume`, so long-lived streams (websockets) can rely on `onCancel`/`onResume` to stop and restart.

## Recompute timing caveat

A watched dependency change can invalidate a provider while its widget is still listening, so the provider may rebuild before that widget is removed. If the same change also removes the screen (logout, a list item deleted), the dependent may run once more with the new value:

Before (may throw on logout, one frame before the screen is removed):

```dart
final userNameProvider = Provider((ref) => ref.watch(userProvider)!.name);
```

After (the computation is total for transient states):

```dart
final userNameProvider = Provider<String?>((ref) => ref.watch(userProvider)?.name);
```

Keep `throw` for states that are truly impossible, not for ones that are merely transient.
