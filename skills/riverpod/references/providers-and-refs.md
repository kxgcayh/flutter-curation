# Providers and Refs

## Provider anatomy

A provider is a memoised function: it is computed on first read and cached until something invalidates it. It holds no state itself; the state lives in the `ProviderContainer`.

Each example below comes in two variants. Choose one, and keep manual and generated declarations in separate files.

Manual:

```dart
final configProvider = Provider<Config>((ref) => Config.fromEnv());

final userProvider = FutureProvider<User>((ref) async {
  final api = ref.watch(apiProvider);
  return api.fetchUser();
});

final ticksProvider = StreamProvider<int>(
  (ref) => Stream.periodic(const Duration(seconds: 1), (i) => i),
);
```

Generated:

```dart
@riverpod
Config config(Ref ref) => Config.fromEnv();

@riverpod
Future<User> user(Ref ref) async {
  final api = ref.watch(apiProvider);
  return api.fetchUser();
}

@riverpod
Stream<int> ticks(Ref ref) => Stream.periodic(const Duration(seconds: 1), (i) => i);
```

- **You can declare many providers of the same type:** `cityProvider` and `countryProvider` can both return `String`. Type-based lookup like package:provider's does not exist.
- **Give manual providers a debug name** with `name: 'MyProvider'` if observers or logs need one. Generated providers are named automatically.

## Notifiers

A Notifier is a provider whose state can be changed from outside through its public methods.

Manual:

```dart
final cartProvider = AsyncNotifierProvider<Cart, List<Item>>(Cart.new);

class Cart extends AsyncNotifier<List<Item>> {
  @override
  Future<List<Item>> build() => ref.watch(cartRepoProvider).load();

  Future<void> add(Item item) async {
    // Capture the ref: if the notifier rebuilds mid-operation, this ref unmounts.
    final operationRef = ref;
    final repo = operationRef.read(cartRepoProvider);
    // Read the current data BEFORE setting AsyncLoading. Awaiting `future` after
    // that point waits for the state this method has yet to produce, and hangs.
    final previous = await future;
    if (!operationRef.mounted) return;
    state = const AsyncLoading();
    final next = await AsyncValue.guard(() async {
      await repo.add(item);
      return [...previous, item];
    });
    if (!operationRef.mounted) return;
    state = next;
  }
}
```

Generated (same methods, different declaration):

```dart
@riverpod
class Cart extends _$Cart {
  @override
  Future<List<Item>> build() => ref.watch(cartRepoProvider).load();

  // add(...) is identical to the manual version.
}
```

This example assumes writes don't overlap. If two `add` calls can run at once, queue them or disable the button while one is pending (a mutation does this for you, see experimental.md).

Rules:

- **`build()` initialises the state** and re-runs whenever a watched dependency changes. Never call it yourself, and never put logic in the constructor.
- **Read dependencies with `ref.watch` in `build()`.** In methods, use `ref.read`, because a method runs once and has nothing to rebuild.
- **`state` is the current value.** For async notifiers, `future` is a Future of the next settled value, so `await future` gets the data inside a method.
- **Inside methods,** capture `final operationRef = ref;` at the start, and check `operationRef.mounted` after each `await` before writing `state`.
- **Never `await future` after setting `state = AsyncLoading()` in the same method:** the future waits for the state you are about to produce.
- **Widgets call methods with** `ref.read(cartProvider.notifier).add(item)`. Never `watch` the `.notifier` just to call methods.
- **To return something to the caller** (for example a created entity's id), make the method return it. A method may also throw; callers handle the error.
- **`listenSelf((prev, next) {...})`** is available on notifiers, for example to log or persist.
- **`updateShouldNotify(prev, next)`** can be overridden on a notifier when `==` filtering is wrong for the state type.

### State update patterns

```dart
// Sync list
void toggle(String id) {
  state = [
    for (final t in state)
      if (t.id == id) t.copyWith(done: !t.done) else t,
  ];
}

// Async: optimistic update with rollback
Future<void> remove(String id) async {
  final operationRef = ref;
  final previous = await future;
  if (!operationRef.mounted) return;
  state = AsyncData(previous.where((t) => t.id != id).toList());
  try {
    await operationRef.read(apiProvider).delete(id);
  } catch (e, st) {
    if (operationRef.mounted) state = AsyncData(previous);
    Error.throwWithStackTrace(e, st);
  }
}

// Async: just refetch after a write
Future<void> rename(String name) async {
  final operationRef = ref;
  await operationRef.read(apiProvider).rename(name);
  if (!operationRef.mounted) return;
  operationRef.invalidateSelf();
  await future;
}
```

## Getting a Ref

| Where | How |
| --- | --- |
| Functional provider | `(ref) { ... }` / `Foo foo(Ref ref)` |
| Notifier | the `ref` property |
| Widget | `ConsumerWidget.build(context, ref)`, `ConsumerState.ref`, `Consumer(builder: (context, ref, child) => ...)`, `HookConsumerWidget` |
| Pure Dart | `ProviderContainer` has the same `read`/`listen`/`invalidate`/`refresh` methods |

- **`Ref` and `WidgetRef` are deliberately separate types** with no shared interface. Don't write helpers that accept either one. Move the logic into a Notifier and call it from the widget.
- **Passing a `WidgetRef` into a function** called from a widget is fine. Don't store it.

## watch, read, listen

| API | Use for | Where |
| --- | --- | --- |
| `ref.watch(p)` | reading state and rebuilding on change | `build` of widgets, providers and notifiers |
| `ref.read(p)` | a one-off read in response to an event | callbacks and notifier methods |
| `ref.listen(p, (prev, next) {...})` | side effects on change | provider/notifier `build`, widget `build` |
| `ref.listenManual(p, cb)` | listening outside `build` | widget lifecycle methods such as `initState`; returns `ProviderSubscription<T>`, closed automatically when the widget is disposed |

```dart
ref.listen<AsyncValue<void>>(checkoutProvider, (prev, next) {
  if (next case AsyncError(:final error)) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$error')));
  }
});
```

- **Provider `Ref.listen`** returns a `ProviderSubscription<T>` with `pause()`, `resume()` and `close()`. It accepts `fireImmediately`, `onError` and `weak`. A weak listener neither initialises its target nor keeps it alive.
- **Widget `WidgetRef.listen`** returns `void` and accepts `onError`. Use `WidgetRef.listenManual` to register in lifecycle methods, or when you need to cancel early.
- **Don't use `read` to optimise.** It silently desynchronises the UI when the provider changes later. Use `select` instead.

## invalidate vs refresh

- **`ref.invalidate(p)`** marks the provider dirty. It recomputes on its next read, or at the next frame if something is listening. If nobody listens, it is disposed.
- **`ref.refresh(p)`** is `invalidate` + `read`: it recomputes immediately and returns the new value. Use the return value (a lint warns if you don't), e.g. `onRefresh: () => ref.refresh(p.future)`.
- **`ref.invalidateSelf()`** works inside a provider or notifier.
- **Families:** `ref.invalidate(userProvider)` invalidates every argument, while `ref.invalidate(userProvider('42'))` invalidates one.

## Ref lifecycle callbacks

| Callback | Fires when |
| --- | --- |
| `ref.onDispose(cb)` | the state is destroyed (recompute, invalidate or auto-dispose) |
| `ref.onCancel(cb)` | the last listener is removed (the provider is paused) |
| `ref.onResume(cb)` | a listener comes back after `onCancel` |
| `ref.onAddListener` / `ref.onRemoveListener` | each listener change |

- **Register as many callbacks as you need,** e.g. one `onDispose` per resource.
- **Each callback returns a function** that unregisters it.
- **Never modify providers inside `onDispose`.**

```dart
@riverpod
Stream<Message> chat(Ref ref, String roomId) {
  final socket = ChatSocket.connect(roomId);
  ref.onDispose(socket.close);
  return socket.messages;
}
```

## Errors

- **A provider that throws exposes `AsyncError`** if it's async; a sync one rethrows on read.
- **In 3.x, errors read through `ref.read`, `ref.watch` or `.future` are wrapped in `ProviderException`.** To catch a specific type:

```dart
try {
  await ref.read(orderProvider.future);
} on ProviderException catch (e) {
  if (e.exception is NotFoundException) { /* ... */ } else { rethrow; }
}
```

- **`AsyncValue.error`, `ref.listen(onError:)` and `ProviderObserver`** still receive the original error, so `if (value.error is NotFoundException)` keeps working.
