# Configuration

## The route tree

```dart
final router = GoRouter(
  initialLocation: '/', // shown when the app starts without a deep link
  debugLogDiagnostics: true, // enable route diagnostics; gate with kDebugMode, and mind sensitive URL data
  routes: [
    GoRoute(
      path: '/',
      builder: (context, state) => const HomeScreen(),
      routes: [
        GoRoute(
          path: 'users/:userId', // -> /users/42
          builder: (context, state) => UserScreen(userId: state.pathParameters['userId']!),
          routes: [
            GoRoute(
              path: 'posts', // -> /users/42/posts?sort=new
              builder: (context, state) => PostsScreen(
                userId: state.pathParameters['userId']!,
                sort: state.uri.queryParameters['sort'] ?? 'top',
              ),
            ),
          ],
        ),
      ],
    ),
    GoRoute(path: '/settings', builder: (context, state) => const SettingsScreen()),
  ],
);
```

- **Make sure the startup location matches a route.** Define `/` whenever `/` can be requested.
- **A route has a `builder`** (returns a widget), **a `pageBuilder`** (returns a `Page`, for transitions or dialogs), **or only a `redirect`.** A redirect-only route must always redirect successfully.
- **Route declaration fragments** in these references belong inside your existing `routes` list.
- **A child route is pushed above its parent,** so `/users/42/posts` builds `HomeScreen`, `UserScreen` and `PostsScreen`, and the back button walks up the URL.
- **A sibling at the top level replaces the stack.** Put a screen at the top level when it shouldn't sit above Home.

## GoRouterState

Every builder and redirect receives a `GoRouterState`. In a widget below the route, use `GoRouterState.of(context)`.

| Field | Meaning |
| --- | --- |
| `uri` | the full location, including the query (`uri.queryParameters`, `uri.queryParametersAll`) |
| `matchedLocation` | the location matched up to this route (no query) |
| `pathParameters` | `Map<String, String>` of the `:params` |
| `extra` | the object passed with `go`/`push` (see navigation.md) |
| `name`, `path`, `fullPath` | this route's name and path template. Route-specific fields can be `null` (e.g. in error states or shell builders), so in a `pageBuilder` use the `state` it's given |
| `error` | the `GoException` when building an error page |
| `pageKey` | a stable key for this page |
| `topRoute` | the deepest matched `GoRoute` |
| `metadata` | route metadata (17.5+) |

## Parameters

- **Path parameters (`:id`) are required segments.** Values are decoded strings. Parse and validate them, because users can type any URL:

```dart
GoRoute(
  path: '/orders/:orderId',
  redirect: (context, state) =>
      int.tryParse(state.pathParameters['orderId']!) == null ? '/orders' : null,
  builder: (context, state) => OrderScreen(id: int.parse(state.pathParameters['orderId']!)),
),
```

The redirect target (`/orders`) must itself be a configured route.

- **Regex constraints** (documented in 17.5, fixed for nested groups in 18.1.3): `path: r'/users/:id(\d+)'` matches only digits, so other values fall through to other routes, or to the error page.
- **Query parameters are optional:** `state.uri.queryParameters['q']`, and `queryParametersAll` for repeated keys. Build URLs with `Uri`:

```dart
void openSearch(BuildContext context, String query) {
  context.go(Uri(path: '/search', queryParameters: {'q': query, 'page': '1'}).toString());
}
```

## Named routes

```dart
GoRoute(name: 'user', path: '/users/:userId', builder: (context, state) => UserScreen(userId: state.pathParameters['userId']!)),
```

```dart
void openUser(BuildContext context) {
  context.goNamed('user', pathParameters: {'userId': '42'}, queryParameters: {'tab': 'posts'});
  final location = context.namedLocation('user', pathParameters: {'userId': '42'}); // '/users/42'
  debugPrint(location);
}
```

- **Names must be unique** across the whole tree. Name lookup is case-sensitive, independently of `GoRoute.caseSensitive`.
- **`pathParameters` values are `String`s:** `{'userId': 42}` doesn't compile, so convert with `'$id'`.
- **Names survive path changes,** so use them, or type-safe routes, rather than hard-coded strings in large apps.

## Transitions

```dart
GoRoute(
  path: '/details',
  pageBuilder: (context, state) => CustomTransitionPage(
    key: state.pageKey,
    child: const DetailsScreen(),
    transitionsBuilder: (context, animation, secondaryAnimation, child) =>
        FadeTransition(opacity: animation, child: child),
  ),
),
GoRoute(
  path: '/tab',
  pageBuilder: (context, state) => NoTransitionPage(key: state.pageKey, child: const TabScreen()),
),
```

Pass `key: state.pageKey` so the page keeps its identity across rebuilds. `MaterialPage` / `CupertinoPage` work in `pageBuilder` too.

## Route metadata (17.5+)

`GoRoute(metadata: {'title': 'Orders', 'requiresAuth': true})` attaches data that child routes inherit and can override. Read it from `GoRouterState.metadata`, e.g. in a top-level redirect that checks `requiresAuth`.

## Routes that change at runtime

```dart
final routingConfig = ValueNotifier(
  RoutingConfig(routes: [GoRoute(path: '/', builder: (_, __) => const HomeScreen())]),
);
final dynamicRouter = GoRouter.routingConfig(routingConfig: routingConfig);

void enableBeta() {
  routingConfig.value = RoutingConfig(routes: [
    GoRoute(path: '/', builder: (_, __) => const HomeScreen()),
    GoRoute(path: '/beta', builder: (_, __) => const BetaScreen()),
  ]);
}
```

Assigning a new `RoutingConfig` re-parses the current location against the new routes. Use redirects for access policy, and reserve `RoutingConfig` for a set of routes that genuinely changes.
