# Testing and migration

## Widget tests

Build a fresh `GoRouter` in each test (a top-level router keeps its state between tests), then drive it with `router.go` or by tapping:

```dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

GoRouter buildTestRouter({String initialLocation = '/'}) => GoRouter(
      initialLocation: initialLocation,
      routes: [
        GoRoute(
          path: '/',
          builder: (context, state) => Scaffold(
            body: TextButton(onPressed: () => context.go('/items/7'), child: const Text('open')),
          ),
          routes: [
            GoRoute(
              path: 'items/:id',
              builder: (context, state) => Text('item ${state.pathParameters['id']}'),
            ),
          ],
        ),
      ],
    );

void main() {
  testWidgets('tapping opens the item', (tester) async {
    final router = buildTestRouter();
    addTearDown(router.dispose);
    await tester.pumpWidget(MaterialApp.router(routerConfig: router));

    await tester.tap(find.text('open'));
    await tester.pumpAndSettle();

    expect(find.text('item 7'), findsOneWidget);
    expect(router.routerDelegate.currentConfiguration.uri.toString(), '/items/7');
  });

  testWidgets('initial location starts on the item', (tester) async {
    final router = buildTestRouter(initialLocation: '/items/9');
    addTearDown(router.dispose);
    await tester.pumpWidget(MaterialApp.router(routerConfig: router));
    await tester.pumpAndSettle();
    expect(find.text('item 9'), findsOneWidget);
  });
}
```

- **Test redirects** by building the router with a fake auth `Listenable`. Flip its state, `pumpAndSettle()`, and assert the visible screen and the current URI.
- **Read the location after `go`** from `router.routerDelegate.currentConfiguration.uri` (as above).
- **After an imperative `push`,** assert the visible widget and the `GoRouterState.uri` it received instead. `currentConfiguration.uri` is the configuration URI, which can stay at the underlying location after a push. `router.routeInformationProvider.value.uri` is what Flutter reports to the platform.
- **`initialLocation` tests the route bootstrap,** not Android or iOS link association. To simulate a platform deep link, set the initial route information explicitly.
- **Dispose each test router** (`addTearDown(router.dispose)`).
- **For screens that call `context.go` or `context.push`,** pump them inside `MaterialApp.router` with a small test router; a bare `MaterialApp` has no `GoRouter`.

## From Navigator 1.0

| Navigator 1.0 | go_router |
| --- | --- |
| `MaterialApp(routes: {...}, initialRoute:)` | `MaterialApp.router(routerConfig: GoRouter(routes: [...], initialLocation:))` |
| `Navigator.pushNamed(context, '/details', arguments: x)` | `context.go('/details/${x.id}')` (or `push`, with `extra:` for in-memory objects) |
| `onGenerateRoute` parsing | `GoRoute(path: '/details/:id')` + `state.pathParameters` |
| `Navigator.pop(context, result)` | `context.pop(result)` |
| `WillPopScope` | `PopScope`, or `GoRoute(onExit:)` |

Migrate gradually. Start with a single `/` route for the existing home screen. `Navigator.push` calls keep working (without deep links) until you replace them with routes.

## Breaking versions

| Version | Change | What to do |
| --- | --- | --- |
| 18.0 | migrated to `material_ui` / `cupertino_ui`; needs Flutter 3.44 / Dart 3.12 | upgrade Flutter; match the project's UI imports |
| 17.0 | navigation inside `ShellRoute` notifies the root `GoRouter` observers by default; new `notifyRootObserver` | dedupe analytics, or set `notifyRootObserver: false` |
| 16.0 | `GoRouteData` changes: typed routes use a generated mixin, with `.go/.push/.location` on the route | upgrade `go_router_builder` (≥ 3.0; 4.0+ makes the mixin public: `with $XRoute`, while 3.x used `with _$XRoute`), add the mixins, re-run `build_runner` |
| 15.0 | URLs are case-sensitive | fix links with the wrong case, or set `caseSensitive: false` on specific routes |
| 14.0 | `onExit` takes `(BuildContext context, GoRouterState state)` | add the `state` parameter |

Older majors (≤ 13) renamed `GoRouterState` fields (`location`/`subloc` → `uri`/`matchedLocation`; `params`/`queryParams` → `pathParameters`/`uri.queryParameters`) and changed `extra` handling. Search for those names when upgrading old code, and follow each major's migration guide linked from the go_router changelog.

Before upgrading, check the SKILL.md version table: the newest go_router your Flutter SDK can resolve may be older than 18.
