# Migration

## StatefulWidget → HookWidget

| `StatefulWidget` code | Hook equivalent |
| --- | --- |
| `State` field holding UI state + `setState` | `useState` |
| field that must not rebuild (timer, cache, flag) | `useRef` |
| `initState` setup + `dispose` cleanup | `useEffect(() { ...; return cleanup; }, const [])` |
| `didUpdateWidget` reacting to `widget.x` | `useEffect(..., [x])`, or `useValueChanged(x, ...)` |
| `late final controller = XController()` + `dispose()` | the matching controller hook (`useTextEditingController`, `useScrollController`, ...) |
| `SingleTickerProviderStateMixin` + `AnimationController` | `useAnimationController()` |
| `FutureBuilder` / `StreamBuilder` | `useFuture` / `useStream` (with `useMemoized`) |
| `AutomaticKeepAliveClientMixin` | `useAutomaticKeepAlive()` |
| `WidgetsBindingObserver.didChangeAppLifecycleState` | `useOnAppLifecycleStateChange` |
| `mounted` after `await` | `context.mounted` |

Before:

```dart
class SearchField extends StatefulWidget {
  const SearchField({required this.onQuery, super.key});
  final ValueChanged<String> onQuery;

  @override
  State<SearchField> createState() => _SearchFieldState();
}

class _SearchFieldState extends State<SearchField> {
  final _controller = TextEditingController();
  Timer? _debounce;

  @override
  void dispose() {
    _debounce?.cancel();
    _controller.dispose();
    super.dispose();
  }

  void _changed(String value) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 300), () => widget.onQuery(value));
  }

  @override
  Widget build(BuildContext context) =>
      TextField(controller: _controller, onChanged: _changed);
}
```

After:

```dart
class SearchField extends HookWidget {
  const SearchField({required this.onQuery, super.key});
  final ValueChanged<String> onQuery;

  @override
  Widget build(BuildContext context) {
    final controller = useTextEditingController();
    final debounce = useRef<Timer?>(null);
    // Always call the latest callback, like `widget.onQuery` did.
    final latestOnQuery = useRef(onQuery);
    latestOnQuery.value = onQuery;
    useEffect(() => () => debounce.value?.cancel(), const []);

    return TextField(
      controller: controller,
      onChanged: (value) {
        debounce.value?.cancel();
        debounce.value = Timer(const Duration(milliseconds: 300), () {
          latestOnQuery.value(value);
        });
      },
    );
  }
}
```

The class name and constructor are unchanged. The timer still starts from a user edit and fires outside `build`, as before (import `dart:async` for `Timer`). Avoid the tempting alternative that pairs `useDebounced` with `useEffect` to call `onQuery`. It fires an unwanted initial empty query, reacts to programmatic text changes, and calls the parent during build, which can assert.

- **Keep the widget's public API (constructor, parameters) unchanged** so callers don't need edits.
- **Use `StatefulHookWidget`** when you need both hooks and a `State`, e.g. to keep a mixin that has no hook equivalent.
- **Use `HookBuilder`** to add hooks to one subtree of an existing widget without converting the whole class.

## Upgrading to flutter_hooks 0.21.4 (Flutter 3.47+)

1. Bump the Flutter SDK. 0.21.4 requires Flutter ≥ 3.47.0 and Dart ^3.6.0.
2. If the project uses `useTabController`, `useSearchController` or `useCarouselController`, add `material_hooks`. For `useCupertinoTabController`, add `cupertino_hooks`. Both are 0.1.0, need Flutter ≥ 3.47.0 and Dart ^3.13.0, and depend on flutter_hooks 0.21.4 exactly. They also bring `material_ui` ^1.10.0 / `cupertino_ui` ^1.1.6.
3. Hide the deprecated copies from the `flutter_hooks` import and import the new package (see controllers.md). The call sites stay the same.
4. Replace `useExpansionTileController` with `useExpansibleController` (deprecated since 0.21.3).
5. Replace `useIsMounted()` checks with `context.mounted`, and `Hook.use(x)` with `use(x)`.

`useSingleTickerProvider` (and so `useAnimationController`) now follows `TickerMode.getValuesNotifier`, and respects `TickerMode.forceFrames` in 0.21.4. Animations under `TickerMode(enabled: false)` pause, the same as with `SingleTickerProviderStateMixin`.
