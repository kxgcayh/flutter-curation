# Navigation

| Call | Effect | URL / browser history |
| --- | --- | --- |
| `context.go('/a/b')` | replaces the stack with the screens matched by `/a/b` | updates the URL; works with deep links and refresh |
| `context.push('/a/b')` | pushes the matched top screen above the current stack. Returns `Future<T?>` | by default the browser URL **doesn't** change. A copied URL doesn't reproduce the stack, though history or restoration state can |
| `context.pushReplacement('/x')` | replaces the top page with a new one (new page key, new transition) | |
| `context.replace('/x')` | replaces the top match and normally reuses its page key. State is kept only when Flutter can update the same page and widget identity. Replacing the only match can produce a newly matched stack | |
| `context.pop([result])` | pops the top page and completes the pending `push` Future with `result` | |
| `context.canPop()` | whether there's a page to pop | |
| `context.goNamed`, `pushNamed`, `pushReplacementNamed`, `replaceNamed`, `namedLocation` | the same, using route names | |

All of these are `BuildContext` extensions over `GoRouter.of(context)`. Outside widgets, call them on the router instance (`router.go('/x')`).

The global opt-in `GoRouter.optionURLReflectsImperativeAPIs = true` makes `push` and friends update the URL too. Test browser history behaviour on the web before relying on it.

## go vs push

```dart
// Navigation that should be reproducible from the URL: go.
TextButton(onPressed: () => context.go('/orders/42'), child: const Text('Open order'));
```

```dart
// A picker that returns a value: push + pop.
Future<void> pickColor(BuildContext context) async {
  final picked = await context.push<String>('/color-picker');
  if (!context.mounted) return;
  if (picked != null) debugPrint('picked $picked');
}

// In the picker screen:
void choose(BuildContext context, String color) => context.pop(color);
```

- **Imperative pushes and browser history interact poorly.** Prefer `go` for anything shareable or primary on the web.
- **After `await context.push(...)`,** check `context.mounted` before using the context.
- **`go` to a location whose parent isn't on the stack builds the parents too** (from the route tree). `push` doesn't.

## Passing data

| Data | How |
| --- | --- |
| an id or simple value | path parameter (`/items/:id`) or query parameter (`?tab=reviews`) |
| an object already in memory (to avoid a refetch) | `extra:` **plus** a fallback: load by id when `extra` is `null` (deep link, refresh) |

```dart
GoRoute(
  path: '/items/:id',
  builder: (context, state) {
    final id = state.pathParameters['id']!;
    final extra = state.extra;
    // Use extra only as a hint that matches the URL; ItemScreen loads by id when initial is null.
    return ItemScreen(id: id, initial: extra is Item && extra.id == id ? extra : null);
  },
),
```

```dart
void openItem(BuildContext context, Item item) =>
    context.go(Uri(pathSegments: ['', 'items', item.id]).toString(), extra: item); // encodes the id safely
```

A fresh URL may not carry `extra`, while a restoration or history entry can still hold a serialisable one. That's why the builder checks that it matches the id.

- **`extra` doesn't go in the URL.** The browser stores it serialised in history state, and state restoration saves it too. JSON-compatible values (maps, lists, strings, numbers) work with the default serializer. For custom objects that must survive, give `GoRouter(extraCodec:)` a `Codec<Object?, Object?>`; otherwise they're dropped.
- **Never rely on `extra` for required data.**

## Leaving a route: PopScope and onExit

```dart
GoRoute(
  path: '/edit',
  builder: (context, state) => const EditScreen(),
  onExit: (context, state) async {
    final leave = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Discard changes?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Stay')),
          TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('Discard')),
        ],
      ),
    );
    return leave ?? false; // false keeps the route
  },
),
```

- **`onExit(context, state)`** returns `FutureOr<bool>` (it has had two parameters since 14.0). It's called when the route is removed, by a pop or a declarative stack change such as `go`, not on every navigation.
- **`PopScope` (`canPop`, `onPopInvokedWithResult`)** handles the system back gesture on a single screen. In the callback, check `didPop`. `WillPopScope` doesn't work with Router-based navigation.
- **`context.canPop()`** only reports whether the navigator has something to pop. It doesn't promise that `PopScope` or an async `onExit` will allow it.

## Navigator interop

`Navigator.of(context).push(MaterialPageRoute(...))` still works:
- **Pages pushed this way aren't deep-linkable.** These pageless routes are removed when the page-backed route beneath them is removed (e.g. on the next `go`).
- **Dialogs and bottom sheets** (`showDialog`, `showModalBottomSheet`) are fine to show this way.
- **Inside a shell,** a `Navigator.push` from a shell screen lands inside that shell's navigator. See shells.md for placing routes above a shell.

## Links and history

- **Real links on the web:** `url_launcher`'s `Link` gives a browser anchor. For an internal route it behaves like `go`, but don't assume it calls go_router directly.
- **Skip a browser history entry:** wrap the call with `Router.neglect(context, () => context.go('/x'))`.
- **Skip history for the whole app:** `GoRouter(routerNeglect: true)`.
