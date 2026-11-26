# Overrides, scoping, observers and testing

## Overrides

Any provider can be overridden on a `ProviderScope` or `ProviderContainer` through `overrides:`. Typical uses are tests, environments and dependency injection.

```dart
ProviderScope(
  overrides: [
    apiProvider.overrideWithValue(FakeApi()),                // replace with a fixed value
    configProvider.overrideWith((ref) => Config.staging()),  // replace the initializer
    userProvider.overrideWithValue(AsyncValue.data(fakeUser)), // Future/StreamProvider (back in 3.x)
    counterProvider.overrideWithBuild((ref, self) => 42),    // Notifier: replace build() only, keep methods
    todoListProvider.overrideWith(FakeTodoList.new),         // Notifier: replace the whole notifier
    userByIdProvider('1').overrideWith((ref) => fakeUser),   // one family member
    userByIdProvider.overrideWith((ref, id) => User(id: id)), // every family member
  ],
  child: const MyApp(),
);
```

Dependency injection: declare a provider that must be overridden, and override it at startup.

```dart
final prefsProvider = Provider<SharedPreferences>((ref) => throw UnimplementedError());

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final prefs = await SharedPreferences.getInstance();
  runApp(ProviderScope(
    overrides: [prefsProvider.overrideWithValue(prefs)],
    child: const MyApp(),
  ));
}
```

## Scoping

Scoping means overriding a provider in a nested `ProviderScope`, so one subtree sees a different value (e.g. the current list item). The docs warn the feature is complex and may be reworked. Prefer families or constructor parameters, and use scoping only when it clearly pays off.

- **Opt in with `dependencies`.** A provider must declare `dependencies` before it can be scoped: `dependencies: []` for the root scoped provider.
- **Declare what you watch.** Any provider that watches a scoped provider must list it in its own `dependencies`.
- **Read it under the scope.** Only widgets below the nested `ProviderScope` see the override.

Choose one variant, and keep manual and generated declarations in separate files.

Manual:

```dart
final currentItemIdProvider = Provider<String>(
  (ref) => throw UnimplementedError(),
  dependencies: const [],
);
final currentItemProvider = FutureProvider<Item>(
  (ref) => fetchItem(ref.watch(currentItemIdProvider)),
  dependencies: [currentItemIdProvider],
);
```

Generated:

```dart
@Riverpod(dependencies: [])
String currentItemId(Ref ref) => throw UnimplementedError();

@Riverpod(dependencies: [currentItemId])
Future<Item> currentItem(Ref ref) => fetchItem(ref.watch(currentItemIdProvider));
```

Setting the scope (the same for both):

```dart
ListView.builder(
  itemBuilder: (context, i) => ProviderScope(
    overrides: [currentItemIdProvider.overrideWithValue(ids[i])],
    child: const ItemTile(), // ItemTile watches currentItemProvider
  ),
);
```

With code generation and `riverpod_lint`, scoping is checked statically. Widgets that use a scoped provider are annotated `@Dependencies([currentItemId])`, and the lint flags any usage that has no override above it.

## ProviderObserver

```dart
final class Logger extends ProviderObserver {
  @override
  void didUpdateProvider(ProviderObserverContext context, Object? previousValue, Object? newValue) {
    debugPrint('${context.provider.name ?? context.provider}: $newValue (mutation: ${context.mutation})');
  }

  @override
  void providerDidFail(ProviderObserverContext context, Object error, StackTrace stackTrace) {
    if (error is ProviderException) return; // a dependency failed; already reported
    reportError(error, stackTrace);
  }
}

ProviderScope(observers: [Logger()], child: const MyApp());
```

- **3.x observer methods take a `ProviderObserverContext`** (which holds the container, provider and mutation) instead of separate `provider`/`container` parameters.
- **Other hooks:** `didAddProvider` and `didDisposeProvider`.
- **Mutated-in-place state** (mutating a list, then `ref.notifyListeners()`) reports the same object as both `previousValue` and `newValue`.

## Unit tests

```dart
test('cart adds items', () async {
  final container = ProviderContainer.test(
    overrides: [cartRepoProvider.overrideWithValue(FakeCartRepo())],
    retry: (_, _) => null, // fail fast instead of retrying
  );

  // Keep auto-dispose providers alive for the test with a listener.
  final sub = container.listen(cartProvider, (_, _) {});

  await container.read(cartProvider.future);
  await container.read(cartProvider.notifier).add(item);

  expect(sub.read().value, [item]);
});
```

- **Use `ProviderContainer.test()`** (it is disposed automatically) and create a new container per test. Never share one. It replaces the hand-written 2.x `createContainer` helper.
- **Listen to auto-dispose providers rather than only `read`ing them,** or their state can be disposed mid-test. Use `container.listen(...)` and `sub.read()`.
- **Await async providers with `expectLater(container.read(p.future), completion(x))`,** or with `throwsA(...)`. Remember that errors read through `.future` are wrapped in `ProviderException`.
- **Record changes:** `container.listen(p, (prev, next) => log.add(next))`, then assert on `log`. You can also verify with mocktail or mockito.
- **`retry: (_, _) => null` is optional,** but makes failure tests deterministic.

## Widget tests

```dart
testWidgets('shows user', (tester) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [userProvider.overrideWithValue(const AsyncValue.data(User(name: 'Ada')))],
      child: const MaterialApp(home: ProfilePage()),
    ),
  );
  await tester.pump();
  expect(find.text('Ada'), findsOneWidget);

  // Read or modify providers from the test.
  final container = tester.container();
  expect(container.read(userProvider).value?.name, 'Ada');
});
```

## Mocking notifiers

Prefer mocking the dependency (a repository or API client) and keeping the real notifier. If you need different initial state, use `overrideWithBuild`. If you must mock the notifier itself, the mock has to extend the notifier base class; implementing it alone breaks it:

Manual:

```dart
class MockCounter extends Notifier<int> with Mock implements Counter {}
```

Generated (the mock must live in the same Dart library as `Counter`, i.e. the file or its part files, because `_$Counter` is library-private):

```dart
class MockCounter extends _$Counter with Mock implements Counter {}
```

Using the mock (the same for both):

```dart
final container = ProviderContainer.test(
  overrides: [counterProvider.overrideWith(MockCounter.new)],
);
```
