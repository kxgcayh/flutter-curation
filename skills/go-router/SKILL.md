---
name: go-router
description: Set up, write, review, debug or migrate Flutter navigation that uses go_router (GoRouter, GoRoute, MaterialApp.router, context.go/push/pop, path and query parameters, named routes, redirect, onEnter guards, refreshListenable auth redirects, ShellRoute, StatefulShellRoute tabs, deep links with App Links and universal links, web URL strategy, transitions, state restoration, go_router_builder type-safe routes). Use for go_router navigation, typed routes, route guards, shell navigator state and platform links, and for upgrading go_router across breaking versions 14 to 18. Use the riverpod skill for auth-state ownership, flutter-hooks for widget lifecycles, and dio for HTTP authentication and token refresh.
metadata:
  version: "0.4.0"
  docs-read: "2026-11-26"
  docs-source: "github.com/flutter/packages@da586f5 (2026-11-25): packages/go_router README, doc/*.md topics, lib/src, example/, test/, CHANGELOG; docs.flutter.dev deep-linking, set-up-app-links, set-up-universal-links, url-strategies (updated 2026-07 to 2026-11)"
  validated-against: "go_router 18.1.4 + go_router_builder 4.5.0 on Flutter 3.44.9 (with source_helper <1.4.0); go_router 17.0.0 + go_router_builder 4.1.2 on Flutter 3.32.8"
---

# go_router

go_router is the Flutter team's URL-based router. It's built on the Router API (`MaterialApp.router`), so the current location is always a URL. That gives you deep links, browser history and redirects without hand-written `Navigator` stacks.

## Step 1: inspect the project

Read `pubspec.yaml` / `pubspec.lock`, and find the existing `GoRouter`:

| Found | Meaning |
| --- | --- |
| `go_router` 18.x | Flutter ≥ 3.44. go_router uses `material_ui` / `cupertino_ui`; match the project's UI imports |
| `go_router` 15–17 | URLs are case-sensitive (15+); `onEnter` exists from 16.3; see the version table |
| `go_router` < 14, or `GoRouteData` classes without a generated mixin | Old API: read [testing-and-migration.md](references/testing-and-migration.md) |
| `go_router_builder` + `@TypedGoRoute` | Type-safe routes: keep using them ([type-safe-routes.md](references/type-safe-routes.md)) |
| An existing `GoRouter` (top-level, provider, DI) | Add routes to it; never create a second router |
| `app_links` / `uni_links` handling links | Flutter's built-in deep-link handler must be turned off (see [deep-links-and-web.md](references/deep-links-and-web.md)) |

### Version compatibility

Newest go_router releases per Flutter SDK, from pub.dev:

| Flutter | go_router | go_router_builder |
| --- | --- | --- |
| 3.32 | 17.0.0 | 4.1.2 |
| 3.35 | 17.2.3 | 4.3.0 |
| 3.38 – 3.41 | 17.5.0 | 4.5.0 |
| 3.44 | 18.1.4 | 4.5.0 |
| 3.47+ | 18.1.4 | 4.5.3 |

If a fresh `pub get` resolves `go_router_builder` ≤ 4.5.0 together with `source_helper` 1.4.0, which is likely on Flutter 3.38–3.46, `build_runner` fails before reading your routes. Pin `source_helper: '<1.4.0'` (see [type-safe-routes.md](references/type-safe-routes.md)).

APIs in this skill that need newer releases:
- `onEnter`: 16.3+
- reliable `onEnter` `then` callbacks with `refreshListenable`: 17.2+
- `BlockedInitialNavigationException`: 17.4+
- route `metadata`: 17.5+
- regex path parameters: documented in 17.5, with the nested-group parsing fix in 18.1.3
- `clipBehavior` on shells: 18.1+

The examples import `package:flutter/material.dart` (the import style the older validated SDKs need). Match the app's own imports when it uses the split `material_ui` / `cupertino_ui` packages.

## Minimal setup

```dart
final router = GoRouter(
  routes: [
    GoRoute(
      path: '/',
      builder: (context, state) => const HomeScreen(),
      routes: [
        GoRoute(
          name: 'item',
          path: 'items/:id', // child paths have no leading '/'
          builder: (context, state) => ItemScreen(id: state.pathParameters['id']!),
        ),
      ],
    ),
  ],
);

class App extends StatelessWidget {
  const App({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp.router(routerConfig: router);
}
```

- **Create the router once:** a top-level `final`, or a long-lived object (a provider, or app state). Don't create it inside `build`, which resets navigation on every rebuild.
- **By convention, top-level paths are absolute (`/x`) and child paths relative (`x`).** Children stack on top of their parent: `/items/42` shows `ItemScreen` above `HomeScreen`, with a back button. Make sure the app's startup location matches a route, and define a `/` route if `/` can be requested.
- **Parameters are strings:** `state.pathParameters['id']` and `state.uri.queryParameters['q']`. Parse and validate them; they come from the URL.
- **URLs are case-sensitive** (since 15.0): `/Home` doesn't match `/home`. Pass `caseSensitive: false` on a `GoRoute` to change that.

## Core rules

1. **`context.go(location)` replaces the stack** with the screens the URL describes. **`context.push(location)`** adds one screen on top, and its `Future<T?>` completes with the value passed to `context.pop(value)`. By default a `push` doesn't change the browser URL, so prefer `go` for anything shareable. Pushed stacks aren't reproduced by a copied URL or a deep link.
2. **Navigate by name** (`context.goNamed('item', pathParameters: {'id': '42'})`) only for routes that declare `name:`. Unknown names throw. `pathParameters` values must be `String`s.
3. **Use a `redirect` for "where should this user be?" logic** (auth, onboarding). Keep it synchronous-fast, return `null` to stay, and pass `refreshListenable:` so redirects re-run when auth changes. Use `onEnter` to block or allow a navigation itself. See [redirects-and-guards.md](references/redirects-and-guards.md).
4. **Use `StatefulShellRoute.indexedStack` for bottom navigation or rails whose tabs keep their own stacks,** and `ShellRoute` for a shared frame without per-tab state. See [shells.md](references/shells.md).
5. **`extra` is an in-memory hint,** not part of the URL. JSON-compatible values survive browser history and state restoration; custom objects need an `extraCodec`. Never make it the only input: put the id in the path, and load by id when `extra` is missing or doesn't match.
6. **Handle bad URLs** with exactly one of `onException`, `errorBuilder` or `errorPageBuilder`. A `GoException` means an unmatched URL, a redirect failure or loop, or another navigation error. A `GoError` or `AssertionError` means misconfiguration, so fix the code.
7. **Use `PopScope`, not `WillPopScope`,** to intercept back navigation. Use `GoRoute(onExit:)` to confirm leaving a route.
8. **Don't mix `Navigator.push` routes into URL flows.** Pages pushed with `Navigator` aren't deep-linkable, and they disappear on the next `go`. Use them only for transient UI (dialogs, sheets).

## Choosing an API

| Need | Use |
| --- | --- |
| Screen reachable by URL | `GoRoute(path:)` |
| Data in the URL | path parameter (`:id`) or query parameter (`state.uri.queryParameters`) |
| Return a result from a screen | `await context.push<T>(...)` + `context.pop(result)` |
| Swap the current screen without growing the stack | `context.replace` / `context.pushReplacement` |
| Login wall or onboarding | top-level `redirect` + `refreshListenable` |
| Cancel a navigation (e.g. block `/login` when signed in) | `onEnter` returning `Block.stop()` / `Block.then(...)` |
| Tabs with independent stacks | `StatefulShellRoute.indexedStack` + `navigationShell.goBranch(i)` |
| Full-screen route above a shell | `GoRoute(parentNavigatorKey: rootNavigatorKey)` |
| Custom or no transition | `pageBuilder:` returning `CustomTransitionPage` / `NoTransitionPage` |
| Compile-time-checked routes | `go_router_builder` (`@TypedGoRoute`, `GoRouteData` with the generated `$XRoute` mixin) |
| Routes that change at runtime (feature flags, login state) | `GoRouter.routingConfig(routingConfig: ValueNotifier<RoutingConfig>)` |

## References (load the one the task needs)

| Task | Read |
| --- | --- |
| Route tree, parameters, names, regex params, transitions, dynamic config, logging | [configuration.md](references/configuration.md) |
| `go` / `push` / `replace` / `pop`, results, `extra`, Navigator interop, `onExit`, `PopScope` | [navigation.md](references/navigation.md) |
| `redirect`, `refreshListenable`, `onEnter`, auth flows, error handling | [redirects-and-guards.md](references/redirects-and-guards.md) |
| `ShellRoute`, `StatefulShellRoute`, navigator keys, full-screen routes | [shells.md](references/shells.md) |
| Android App Links, iOS universal links, web URL strategy, state restoration | [deep-links-and-web.md](references/deep-links-and-web.md) |
| `go_router_builder` type-safe routes | [type-safe-routes.md](references/type-safe-routes.md) |
| Widget tests for routes; migrating from `Navigator` and across go_router 14 → 18 | [testing-and-migration.md](references/testing-and-migration.md) |
