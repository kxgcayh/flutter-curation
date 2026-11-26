# Primitive hooks

## useState

```dart
final count = useState(0); // ValueNotifier<int>
void increment() => count.value++; // rebuilds the widget when called
```

Pass functions like this as event handlers (`onPressed: increment`). During `build` itself, derive values; never write to state there.

- **Returns a `ValueNotifier<T>`.** Setting `.value` rebuilds the widget only when the new value differs from the old one (`ValueNotifier` compares with `==`).
- **The argument is read only on the first build.** Later builds ignore it, so `useState(widget.initial)` doesn't follow changes to `widget.initial`.
- **Assign a new object; don't mutate in place.** Mutating a list in place doesn't notify:

```dart
final items = useState(<String>[]);
void addItem() => items.value = [...items.value, 'new']; // rebuilds
```

## useEffect

```dart
useEffect(() {
  final sub = stream.listen(onEvent);
  return sub.cancel; // cleanup on effect replacement or widget disposal
}, [stream]);
```

| `keys` | When the effect runs |
| --- | --- |
| omitted (`null`) | synchronously on **every** build |
| `const []` | once, on the first build |
| `[a, b]` | on the first build, then whenever `a` or `b` changes (`==`) |

- **Cleanup order depends on the keys.** With omitted keys, the previous cleanup runs before the effect runs again. When keys **change**, the new effect starts during build, and the old cleanup runs at the end of that build, so for a moment both are active. If overlap is wrong (e.g. two subscriptions to the same socket), manage the replacement yourself. For stream listeners, use `useOnStreamChange`.
- **The effect runs synchronously during `build`.** Don't call `setState` / `.value =` directly inside it: that can mark dependent widgets dirty during build and assert, especially when the change reaches an ancestor or sibling. Schedule the change instead (`WidgetsBinding.instance.addPostFrameCallback`), or derive the value without state.
- **Return `null`** when there's nothing to clean up.
- **Async work:** start it inside the effect and guard against the widget being gone:

```dart
final result = useState<String?>(null);
useEffect(() {
  var cancelled = false;
  api.fetch(id).then((value) {
    if (!cancelled) result.value = value;
  });
  return () => cancelled = true;
}, [id]);
```

  For simple loading, `useFuture` + `useMemoized` is shorter (see async-and-listenables.md).

## useMemoized

```dart
final future = useMemoized(() => api.fetchUser(userId), [userId]);
final formatter = useMemoized(() => NumberFormatter(locale), [locale]);
```

- **The builder runs on the first build, then again only when `keys` change.** With no keys, it runs once.
- **It doesn't dispose anything.** If the object needs disposing, add `useEffect(() => obj.dispose, [obj])`, or use the dedicated controller hook.

## useCallback

```dart
final onSubmit = useCallback(() => submit(form.value), [form.value]);
```

This is sugar for `useMemoized(() => callback, keys)`. Use it to keep a stable function identity, for example when a child widget compares callbacks. Plain closures are fine otherwise.

## useRef

```dart
final timer = useRef<Timer?>(null);
useEffect(() => () => timer.value?.cancel(), const []); // cancel on unmount
final seenIds = useRef(<String>{});

void start() {
  timer.value?.cancel();
  timer.value = Timer(const Duration(seconds: 1), tick);
}
```

- **Changing `.value` never rebuilds the widget.**
- **Use it for:** timers, de-duplication sets, the latest callback, and other values that must survive rebuilds without being UI state.
- **Don't keep a copy of shared or provider state in it,** because the copy goes stale.

## useValueChanged and usePrevious

```dart
// Runs the callback when `color` changes, but not on the first build.
useValueChanged<Color, void>(color, (oldColor, _) {
  controller.forward(from: 0);
});

final previousPage = usePrevious(page); // value from the previous build (null on the first)
```

`useValueChanged` returns the callback's latest result, so it can also interpolate between values.

## useReducer

```dart
sealed class CounterAction {}
class Increment extends CounterAction {}
class Reset extends CounterAction {}

int counterReducer(int state, CounterAction? action) => switch (action) {
      Increment() => state + 1,
      Reset() => 0,
      null => state,
    };

class ReducerCounter extends HookWidget {
  const ReducerCounter({super.key});

  @override
  Widget build(BuildContext context) {
    final store = useReducer<int, CounterAction?>(
      counterReducer,
      initialState: 0,
      initialAction: null,
    );
    return TextButton(
      onPressed: () => store.dispatch(Increment()),
      child: Text('${store.state}'),
    );
  }
}
```

The reducer runs immediately on the first build with `initialAction`. Use it when several related values change together. For anything shared across screens, use app-level state management instead.

## useContext

`useContext()` returns the `BuildContext` of the widget being built. It's for custom hooks that need it, such as `Theme.of(useContext())`. Inside `build`, use the `context` parameter.
