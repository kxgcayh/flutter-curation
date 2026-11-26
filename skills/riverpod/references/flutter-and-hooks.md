# Flutter setup, consumers and hooks

## Install

Pick one row:

| Setup | Commands |
| --- | --- |
| Flutter | `flutter pub add flutter_riverpod` |
| Flutter + hooks | `flutter pub add hooks_riverpod flutter_hooks` |
| Flutter + codegen | `flutter pub add flutter_riverpod riverpod_annotation dev:riverpod_generator dev:build_runner` |
| Flutter + hooks + codegen | `flutter pub add hooks_riverpod flutter_hooks riverpod_annotation dev:riverpod_generator dev:build_runner` |
| Dart only | `dart pub add riverpod` (+ `riverpod_annotation dev:riverpod_generator dev:build_runner` for codegen) |

For an existing project, use the versions in `pubspec.lock`. For a new project, let pub resolve versions compatible with the installed SDK, then confirm you got Riverpod 3.x (and generator 4.x, if used).

Some APIs are newer than 3.0. For example, `container.allProviders(family:)` needs 3.3.2 or later. Check the resolved version before using recently added APIs.

- **`hooks_riverpod` doesn't export `flutter_hooks`:** add both packages.
- **Import only one Riverpod library per file:** `flutter_riverpod`, `hooks_riverpod` or `riverpod`.

### riverpod_lint

`riverpod_lint` 3.1.0+ is installed as an analysis_server_plugin, in `analysis_options.yaml` (not `dev_dependencies`). Pick the version that matches the project's Dart SDK:

| Dart SDK | riverpod_lint |
| --- | --- |
| 3.8 – 3.9 | `3.1.0` |
| 3.10 – 3.11 | `3.1.4` |
| 3.12 | `3.1.8` |
| 3.13+ | `3.2.0` (latest as of 2026-11) |

```yaml
plugins:
  riverpod_lint: 3.1.0 # Dart 3.8 / Flutter 3.32; see the table above
```

Each lint release depends on one exact Riverpod version (3.1.0 → riverpod 3.1.0, 3.2.0 → riverpod 3.5.0). Prefer the row that matches your SDK rather than the newest release. Versions before 3.1.0 used `custom_lint` in `dev_dependencies` instead.

It catches missing scoped dependencies, unstable family parameters, an unused `ref.refresh` result and more. It also adds IDE refactors such as "Convert to ConsumerWidget".

## ProviderScope

```dart
void main() {
  runApp(const ProviderScope(child: MyApp()));
}
```

- **Wrap the root of the app in one `ProviderScope`.** Nested scopes are only for scoping (see scopes-and-testing.md).
- **App-wide options:** `ProviderScope(overrides: [...], observers: [...], retry: ...)`.
- **To read providers before `runApp`** (e.g. warm up storage), create the container yourself:

```dart
Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final container = ProviderContainer();
  await container.read(storageProvider.future);
  runApp(UncontrolledProviderScope(container: container, child: const MyApp()));
}
```

- **`UncontrolledProviderScope` doesn't dispose the container you pass it.** Whoever creates it must dispose it when the app or test tears down.
- **Reading once in `main` doesn't keep an auto-dispose provider alive.** Use the eager-init widget below so something keeps watching it.

## Consumer widgets

| Instead of | Use | Ref |
| --- | --- | --- |
| `StatelessWidget` | `ConsumerWidget` | `build(BuildContext context, WidgetRef ref)` |
| `StatefulWidget` / `State` | `ConsumerStatefulWidget` / `ConsumerState` | `this.ref`, usable in all lifecycle methods |
| a builder | `Consumer(builder: (context, ref, child) => ...)` | builder parameter; rebuilds only that subtree |
| `HookWidget` | `HookConsumerWidget` (hooks_riverpod) | `build(context, ref)` + hooks |
| `StatefulWidget` + hooks | `StatefulHookConsumerWidget` | |
| `HookBuilder` + `Consumer` | `HookConsumer(builder: (context, ref, child) => ...)` | |

- **Default to `ConsumerWidget`.** Use `ConsumerStatefulWidget` when you need `State` (controllers without hooks, `initState` work).
- **`context.watch` doesn't exist.** Riverpod needs a `Ref` so it can track listeners for auto-dispose.
- **Use `Consumer` deep in a large widget** to limit what rebuilds.

```dart
class _SearchState extends ConsumerState<Search> {
  @override
  void initState() {
    super.initState();
    // Listening outside build => listenManual. The subscription closes
    // automatically when the widget is disposed. Keep the returned
    // ProviderSubscription only if you need to close it early.
    ref.listenManual(resultsProvider, (prev, next) {
      // handle the change
    });
  }

  @override
  Widget build(BuildContext context) => Text('${ref.watch(queryProvider)}');
}
```

- **Don't initialise providers from `initState`** (`ref.read(p).init()`). Providers initialise themselves in their initializer or `build()`. If the setup depends on a user action, do it in the callback that navigates (e.g. `onPressed`).
- **After an `await` in a callback,** check `if (!context.mounted) return;` before using `ref`. Otherwise you get "Using ref when a widget is about to or has been unmounted is unsafe".

## Eager initialization

Providers are lazy. To start one at launch, watch it in a small widget under `ProviderScope` that returns `child`:

```dart
class EagerInit extends ConsumerWidget {
  const EagerInit({required this.child, super.key});
  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final config = ref.watch(remoteConfigProvider);
    return switch (config) {
      AsyncError(:final error) => ErrorScreen(error),
      AsyncData() => child,
      _ => const SplashScreen(),
    };
  }
}

// MyApp: return EagerInit(child: MaterialApp.router(...));
```

- **Only `EagerInit` rebuilds.** Because `child` is created by the parent, it is unaffected.
- **Widgets below can use `ref.watch(remoteConfigProvider).requireValue`** instead of handling loading and error again.
- **Put `EagerInit` in `MyApp`, not `main`,** so widget tests get the same behaviour.

## Hooks with Riverpod

Hooks (flutter_hooks) are for local widget state; providers are for shared app state. For hooks themselves (every `use*` hook, `keys`, custom hooks), see the `flutter-hooks` skill. The Riverpod docs advise newcomers not to start with hooks. Use them when the project already does.

Rules of hooks:

- **Call hooks only in the `build` of a `HookWidget` or `HookConsumerWidget`** (or a `HookBuilder`/`HookConsumer` builder). Never in callbacks.
- **Never call hooks conditionally or in loops.** Call the same hooks in the same order on every build.
- **Write custom hooks as functions named `useX`** that call other hooks.

```dart
class EditProfile extends HookConsumerWidget {
  const EditProfile({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final profile = ref.watch(profileProvider).requireValue;
    final name = useTextEditingController(text: profile.name);
    final saving = useState(false);

    return Column(children: [
      TextField(controller: name),
      ElevatedButton(
        onPressed: saving.value
            ? null
            : () async {
                saving.value = true;
                try {
                  await ref.read(profileProvider.notifier).rename(name.text);
                } catch (error) {
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Save failed: $error')),
                    );
                  }
                } finally {
                  if (context.mounted) saving.value = false;
                }
              },
        child: const Text('Save'),
      ),
    ]);
  }
}
```

### Pitfall: copying provider data into hook state

Don't keep a provider's value in `useState`/`useRef` as the source of truth. The copy goes stale when the provider refreshes (after a purchase, an invalidate or a dependency change), and the UI keeps using the old data.

Bad (`detail` never updates after the provider refreshes):

```dart
final detail = useState(ref.read(detailProvider(id)).value);
```

Good (watch the provider directly):

```dart
final detail = ref.watch(detailProvider(id));
```

For an editable draft (a form that starts from provider data), mount a dedicated editor widget only after the data has loaded, key it by the entity's id, and initialise its local fields once. Reset the draft only on an explicit reset or when the entity changes. Don't re-sync on every provider update, or a background refresh will overwrite what the user is typing:

```dart
// Parent
final detail = ref.watch(detailProvider(id));
return switch (detail) {
  AsyncValue(:final value?) => DetailEditor(key: ValueKey(value.id), initial: value),
  AsyncValue(:final error?) => ErrorView(error),
  _ => const CircularProgressIndicator(),
};

// DetailEditor (HookConsumerWidget): initialise once from `initial`.
final title = useTextEditingController(text: initial.title);
```

After a write that changes server data, refresh and await it before using the result: `await ref.refresh(detailProvider(id).future);`.

`useRef` is fine for values that must not trigger rebuilds and aren't derived from providers, such as de-duplication sets for event streams or timers.
