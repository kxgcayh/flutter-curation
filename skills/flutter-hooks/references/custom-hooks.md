# Custom hooks

## Function hooks (the usual way)

A custom hook is a function named `useX` that calls other hooks. It follows the same rules: call it unconditionally, in the same order, from `build` or from another hook.

```dart
/// Toggles between true and false; returns the current value and a toggle.
(bool, VoidCallback) useToggle([bool initial = false]) {
  final state = useState(initial);
  final toggle = useCallback(() => state.value = !state.value, [state]);
  return (state.value, toggle);
}

/// Logs the value whenever it changes.
ValueNotifier<T> useLoggedState<T>(T initial) {
  final result = useState<T>(initial);
  useValueChanged<T, void>(result.value, (oldValue, _) {
    debugPrint('$oldValue -> ${result.value}');
  });
  return result;
}

/// A periodic tick that is cancelled when the widget goes away or [interval] changes.
int useTicker(Duration interval) {
  final ticks = useState(0);
  useEffect(() {
    final timer = Timer.periodic(interval, (_) => ticks.value++);
    return timer.cancel;
  }, [interval]);
  return ticks.value;
}
```

- **Return what callers need:** a value, a record, or a small class. Don't return the internal `ValueNotifier` unless callers should be able to write to it.
- **Put cleanup in the hooks you compose** (`useEffect`'s return value, or controller hooks), never in the caller.

## Class hooks (for full lifecycle control)

Write a `Hook` subclass when a function hook can't express the lifecycle, for example when you need to compare against the previous configuration. Hide it behind a function:

```dart
Duration useTimeAlive() => use(const _TimeAliveHook());

class _TimeAliveHook extends Hook<Duration> {
  const _TimeAliveHook();

  @override
  _TimeAliveHookState createState() => _TimeAliveHookState();
}

class _TimeAliveHookState extends HookState<Duration, _TimeAliveHook> {
  late final DateTime _start;

  @override
  void initHook() {
    super.initHook();
    _start = DateTime.now();
  }

  @override
  Duration build(BuildContext context) => DateTime.now().difference(_start);

  @override
  void dispose() {
    debugPrint('alive for ${DateTime.now().difference(_start)}');
    super.dispose();
  }
}
```

| `HookState` member | Equivalent / purpose |
| --- | --- |
| `initHook()` | `State.initState` |
| `build(context)` | runs on every widget build and returns the hook's value |
| `didUpdateHook(oldHook)` | `State.didUpdateWidget`: compare `hook` with `oldHook` |
| `deactivate()` / `dispose()` | the same as on `State` |
| `reassemble()` | hot reload |
| `setState(fn)` | marks the widget for rebuild |
| `hook`, `context` | the current `Hook` configuration and the widget's `BuildContext` |
| `shouldRebuild()` / `markMayNeedRebuild()` | advanced: lets a hook skip a rebuild that it requested |

- **Use the top-level `use(...)`.** `Hook.use(...)` is deprecated.
- **Pass `keys` to `super(keys: ...)`** in the `Hook` constructor, so a key change disposes the old state and creates a new one.

## Testing hooks

Test hooks through a widget. Wrap the hook in a `HookBuilder` and capture its value:

```dart
void main() {
  testWidgets('useToggle flips', (tester) async {
    late bool value;
    late VoidCallback toggle;

    await tester.pumpWidget(HookBuilder(builder: (context) {
      (value, toggle) = useToggle();
      return const SizedBox();
    }));
    expect(value, isFalse);

    toggle();
    await tester.pump();
    expect(value, isTrue);
  });
}
```

- **Rebuild with new arguments** by pumping a new `HookBuilder` in the same place. The hook's state is kept, as it would be in an app.
- **Trigger disposal** with `await tester.pumpWidget(const SizedBox())`, then check that cleanup ran.

## Hot reload

Hot reload preserves compatible hooks by position. Structural edits that change the sequence of hooks (adding, removing or reordering) can recreate the hooks after the affected position. Editing a hook's arguments usually keeps its state, unless its keys or identity change.
