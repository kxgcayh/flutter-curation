# Async state, retry, cancellation and rebuild control

## AsyncValue

`AsyncValue<T>` is sealed, with three subtypes: `AsyncData`, `AsyncError` and `AsyncLoading`.

```dart
final orders = ref.watch(ordersProvider);

// Pattern matching on subtypes: the simplest form, but a dependency reload
// (AsyncLoading) shows the spinner. To keep data on screen, see below.
return switch (orders) {
  AsyncData(:final value) => OrderList(value),
  AsyncError(:final error, :final stackTrace) => ErrorView(error, stackTrace),
  _ => const Center(child: CircularProgressIndicator()),
};

// Or the callback form
return orders.when(
  data: OrderList.new,
  error: (e, st) => ErrorView(e, st),
  loading: () => const Center(child: CircularProgressIndicator()),
);
```

| Member | Meaning |
| --- | --- |
| `value` | data or `null` (3.x renamed `valueOrNull` to `value`; the old throwing `value` is gone) |
| `requireValue` | data, or throws; use it only when the data is guaranteed (eager init, after `await p.future`) |
| `hasValue` / `hasError` / `error` / `stackTrace` | inspect without matching |
| `isLoading` | a load is in progress (first load, refresh or reload) |
| `isRefreshing` | forced refresh (`refresh`/`invalidate`) with previous data or error; the value is still an `AsyncData`/`AsyncError` subtype |
| `isReloading` | reload because a watched dependency changed; the value is an `AsyncLoading` that still carries the previous data in `value` |
| `isFromCache` | the value came from offline persistence (experimental) |
| `AsyncLoading(progress: 0.5)` | optional progress reporting from a notifier |

- **Refresh and reload match different subtypes:**
  - A forced refresh (`refresh`/`invalidate`) with previous data or error still matches `AsyncData` or `AsyncError`, with `isLoading == true` and `isRefreshing` set.
  - A dependency reload matches `AsyncLoading` with `isReloading` set, but `value` still holds the previous data.
  - An initial load with no prior state sets neither flag.
- **Keep previous data on screen during both,** and show a loading fallback only when no data or error is visible:

```dart
return switch (orders) {
  AsyncValue(:final value?) => Stack(children: [
      OrderList(value),
      if (orders.isLoading) const LinearProgressIndicator(), // refresh or reload
    ]),
  AsyncValue(:final error?) => ErrorView(error, orders.stackTrace),
  _ => const Center(child: CircularProgressIndicator()), // first load
};
```

- **Handle the first load explicitly.** Before any data exists, `value` is `null` and `requireValue` throws. Write the loading/empty branch for that case; don't assume data is there.
- **Inside providers, prefer `await ref.watch(other.future)`** to get data rather than matching on `AsyncValue`.
- **In notifier methods,** `state = await AsyncValue.guard(() => work())` turns exceptions into `AsyncError`.

## Pull-to-refresh

```dart
RefreshIndicator(
  onRefresh: () => ref.refresh(ordersProvider.future),
  child: ListView(...), // must be scrollable, even when empty or in an error state
)
```

`onRefresh` must return a Future that completes when the refresh is done, which is why it refreshes `.future`.

## Automatic retry (3.x)

- **Defaults:** a provider that throws during computation is retried up to 10 times, with exponential backoff from 200 ms to 6.4 s.
- **Not retried:** `Error`s (bugs) and `ProviderException`s (the failure came from a dependency, which retries itself).
- **`await ref.watch(p.future)` waits through retries** and completes once the provider succeeds or the retries run out.

```dart
Duration? retry(int retryCount, Object error) {
  if (retryCount >= 5) return null;              // stop
  if (error is ProviderException) return null;   // dependency failed, not us
  if (error is AuthException) return null;       // not transient
  return Duration(milliseconds: 200 * (1 << retryCount));
}

// globally
ProviderScope(retry: retry, child: MyApp());
ProviderContainer(retry: retry);

// per provider (manual)
final todoListProvider = NotifierProvider<TodoList, List<Todo>>(TodoList.new, retry: retry);

// disable everywhere
ProviderScope(retry: (_, _) => null, child: MyApp());
```

Per provider, with code generation:

```dart
@Riverpod(retry: retry)
class TodoList extends _$TodoList {
  @override
  List<Todo> build() => [];
}
```

- **Disable retry for non-idempotent work, 4xx-style errors or tests** where retries hide failures or slow them down.
- **The default policy skips `ProviderException`,** so dependents don't retry a failed dependency by default. A custom policy should keep that guard unless you mean to change it.

## Cancel and debounce

Both rely on `ref.onDispose`, which fires when the user leaves the screen (auto-dispose) or when the provider recomputes (refresh, or a new search query).

```dart
extension DebounceAndCancel on Ref {
  /// Waits [duration], then returns a client that is closed when the provider is disposed.
  Future<http.Client> debouncedClient([Duration duration = const Duration(milliseconds: 500)]) async {
    var disposed = false;
    onDispose(() => disposed = true);
    await Future<void>.delayed(duration);
    if (disposed) throw Exception('Cancelled'); // safe: Riverpod ignores errors after dispose
    final client = http.Client();
    onDispose(client.close); // cancels the in-flight request
    return client;
  }
}

@riverpod
Future<List<Result>> search(Ref ref, String query) async {
  final client = await ref.debouncedClient();
  final res = await client.get(Uri.https('api.example.com', '/search', {'q': query}));
  return parseResults(res.body);
}
```

- **Leaving a page cancels only with auto-dispose on,** because that's what disposes the provider when the last listener leaves. Explicit invalidation, recomputation and container disposal also run the cleanup.
- **With Dio,** pass a `CancelToken` and call `ref.onDispose(token.cancel)`.

## Reducing rebuilds

Benchmark first: `ref.watch` is cheap, and these tools add complexity.

- **Derive state in a provider.** A provider that returns a `bool` computed from another provider only notifies when the `bool` changes:

```dart
@riverpod
bool hasUnread(Ref ref) => ref.watch(inboxProvider).any((m) => !m.read);
```

- **Use `select` to watch one field:**

```dart
final name = ref.watch(userProvider.select((u) => u.name));
```

  Call `select` once per field you need. The selected value must be immutable (a mutated `List` won't trigger a rebuild).

- **Use `selectAsync` inside async providers:**

```dart
@riverpod
Future<List<Post>> myPosts(Ref ref) async {
  final userId = await ref.watch(userProvider.selectAsync((u) => u.id));
  return ref.watch(apiProvider).posts(userId);
}
```

- **Updates are filtered by `==`.** Data classes with value equality (Freezed, records, `Equatable`) avoid needless notifications. Classes without it notify on every new instance.
- **Use a `Consumer` around the small part of a big widget** that depends on a provider.
- **Don't swap `ref.watch` for `ref.read`** as an optimisation.
