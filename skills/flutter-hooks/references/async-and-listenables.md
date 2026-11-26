# Futures, streams and Listenables

## useFuture

```dart
class UserName extends HookWidget {
  const UserName({required this.userId, super.key});
  final String userId;

  @override
  Widget build(BuildContext context) {
    // Create the Future once per userId. Never call fetch() inline in useFuture.
    final future = useMemoized(() => fetchUserName(userId), [userId]);
    final snapshot = useFuture(future);

    if (snapshot.hasError) return Text('Error: ${snapshot.error}');
    if (!snapshot.hasData) return const CircularProgressIndicator();
    return Text(snapshot.requireData);
  }
}
```

- **Returns an `AsyncSnapshot<T>`,** the same as `FutureBuilder` (`connectionState`, `data`, `error`, `hasData`, `requireData`).
- **`useFuture(fetch())` without `useMemoized` re-runs the request on every build,** because every build passes a new Future.
- **`preserveState: true` (the default)** keeps the previous data, and the previous error, while a new Future (e.g. a new `userId`) is pending. Passing `null` keeps them too. Pass `false` to reset to `initialData` on every change.
- **Pass `initialData:`** to show a value before the Future completes. Changing only `initialData` later is ignored.
- **Check `connectionState` as well as `hasData`** when you show loading or empty states, because preserved data can belong to the previous Future.
- **Replacing a Future only suppresses its late result.** It doesn't cancel the request.
- **To refresh,** change a key of the `useMemoized`. A refresh counter works:

```dart
final refresh = useState(0);
final future = useMemoized(() => fetchUserName(userId), [userId, refresh.value]);
// onPressed: () => refresh.value++
```

## useStream

```dart
final stream = useMemoized(() => chat.messages(roomId), [roomId]);
final snapshot = useStream(stream, initialData: const <Message>[]);
```

The same rules as `useFuture` apply: memoise the stream, and `preserveState` defaults to `true`. The subscription is cancelled when the stream changes or the widget is disposed.

## useOnStreamChange

Listen to a stream for side effects, without rebuilding:

```dart
useOnStreamChange<Notice>(
  notices,
  onData: (notice) => ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(content: Text(notice.text)),
  ),
  onError: (error, stack) => debugPrint('$error'),
);
```

It returns the `StreamSubscription` (or `null` when the stream is `null`) and cancels it automatically.

## useStreamController

```dart
final controller = useStreamController<String>(); // closed automatically on dispose
```

Pass `keys:` to recreate it, plus `sync`, `onListen` and `onCancel` to configure it.

## Listenables

| Hook | Rebuilds the widget? | Use for |
| --- | --- | --- |
| `useListenable(listenable)` | yes, on every notification | `ChangeNotifier`, `Animation`, controllers |
| `useValueListenable(valueListenable)` | yes, and returns `.value` | reading a `ValueListenable` |
| `useListenableSelector(listenable, () => selected)` | on notifications from the listenable, only when `selected` changes (`==`). Parent rebuilds still rebuild it | expensive widgets that care about one derived, immutable value |
| `useOnListenableChange(listenable, callback)` | no | side effects on change |
| `useValueNotifier(initial)` | **no**: it only creates and disposes the notifier | state passed to children that listen themselves |

```dart
class SubmitField extends HookWidget {
  const SubmitField({super.key});

  @override
  Widget build(BuildContext context) {
    final text = useTextEditingController();
    // Rebuild only when emptiness flips, not on every keystroke.
    final isEmpty = useListenableSelector(text, () => text.text.isEmpty);

    return Column(children: [
      TextField(controller: text),
      ElevatedButton(
        onPressed: isEmpty ? null : () => debugPrint(text.text),
        child: const Text('Submit'),
      ),
    ]);
  }
}
```

`useListenable` returns the listenable itself, so `useListenable(controller).value` works for `ValueListenable`s.

## Debouncing

```dart
class SearchBox extends HookWidget {
  const SearchBox({super.key});

  @override
  Widget build(BuildContext context) {
    final query = useTextEditingController();
    final typed = useValueListenable(query).text;
    final debounced = useDebounced(typed, const Duration(milliseconds: 400));

    final results = useMemoized(
      () => debounced == null || debounced.isEmpty ? null : search(debounced),
      [debounced],
    );
    // preserveState: false, so clearing the box doesn't keep the old results.
    final snapshot = useFuture(results, preserveState: false);
    // Hide results that belong to an older query while the next debounce waits.
    final showResults = typed.isNotEmpty && typed == debounced;

    return Column(children: [
      TextField(controller: query),
      if (showResults && snapshot.hasError)
        Text('Search failed: ${snapshot.error}')
      else if (showResults && snapshot.hasData)
        Text('${snapshot.requireData.length} results'),
    ]);
  }
}
```

`useDebounced(value, timeout)` returns `null` until the first timeout elapses. After that it returns the last value that stayed unchanged for `timeout`. Changing either the value or the timeout restarts the timer, the previous debounced value stays current while it waits, and the timer is cancelled on dispose.
