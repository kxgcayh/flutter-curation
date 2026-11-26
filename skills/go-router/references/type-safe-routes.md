# Type-safe routes (go_router_builder)

`go_router_builder` generates the route table and typed navigation helpers from annotated classes. It checks typed navigation calls and route declarations at compile time. Inputs from deep links are still runtime input: they must parse and pass validation (throw or redirect on bad values).

```sh
flutter pub add go_router
flutter pub add dev:go_router_builder dev:build_runner
dart run build_runner build   # or: watch
```

```dart
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

part 'routes.g.dart';

@TypedGoRoute<HomeRoute>(
  path: '/',
  routes: [
    TypedGoRoute<SongRoute>(path: 'songs/:id'),
  ],
)
class HomeRoute extends GoRouteData with $HomeRoute {
  const HomeRoute();

  @override
  Widget build(BuildContext context, GoRouterState state) => const HomeScreen();
}

class SongRoute extends GoRouteData with $SongRoute {
  const SongRoute({required this.id, this.autoplay = false});

  final int id; // parsed from the path for you
  final bool autoplay; // becomes ?autoplay=true

  @override
  Widget build(BuildContext context, GoRouterState state) => SongScreen(id: id, autoplay: autoplay);
}

final typedRouter = GoRouter(routes: $appRoutes); // generated list of top-level routes

void playSong(BuildContext context) {
  const SongRoute(id: 2, autoplay: true).go(context); // or .push(context) / .location
}
```

- **The mixin is required** with go_router ≥ 16:
  - go_router_builder **4.0+** generates a public mixin: `class XRoute extends GoRouteData with $XRoute`
  - go_router_builder **3.x** generated the private `with _$XRoute`, which go_router's own type-safe topic still shows

  Match the builder version in `pubspec.lock`. Older code that calls `.go(context)` through a generated extension, without the mixin, must be updated.
- **Generated helpers on each route object:** `location`, `go`, `push`, `pushReplacement` and `replace`.
- **Constructor fields map automatically:**
  - path parameters (`:id`) map by name, and types like `int`, `double`, `bool`, enums and `DateTime` are parsed for you
  - other fields become query parameters
  - a field named `$extra` carries `extra`
- **Rename or customise query parameters** with `@TypedQueryParameter(...)` on the constructor parameter. go_router added `name` in 17.1, and `encoder` / `decoder` / `compare` in 17.2. Check that the project's builder version generates them, and inspect the generated output.
- **Shells:** `@TypedShellRoute` / `@TypedStatefulShellRoute` with `ShellRouteData` / `StatefulShellRouteData`.
- **Overrides:** a `GoRouteData` can override `redirect`, `onExit` and `buildPage` (for transitions). `hasOverriddenOnExit` (17.3+) is an option on the generated route-data helper (`$route`), not a parameter of your `onExit` override. Check the generated code before relying on it.
- **Never edit `*.g.dart` by hand.** Re-run `build_runner` after changing annotated classes. For `build.yaml`, version conflicts and CI checks, use the build-runner skill.
- **Builder version vs Flutter:** go_router_builder 4.5.3 needs Flutter 3.47; on Flutter 3.38–3.44, pub resolves 4.5.0. See the version table in SKILL.md.
- **Known build failure:** when the resolved builder defines its own `ExecutableElement.qualifiedName` (go_router_builder ≤ 4.5.0) and `source_helper` 1.4.0 is also resolved, `build_runner` fails before reading your routes. The error is *"The property 'qualifiedName' is defined in multiple extensions for 'ExecutableElement'"*. This was reproduced with Flutter 3.44.9, go_router_builder 4.5.0, analyzer 13.0.0 and source_helper 1.4.0. It depends on the resolved pair, not on the Flutter version alone: an older lock file with source_helper 1.3.x builds fine. Fix it either way:
  - add `source_helper: '<1.4.0'` under `dev_dependencies`, then re-resolve and rebuild
  - upgrade to Flutter 3.47+ and go_router_builder ≥ 4.5.2, which uses the shared helper from `source_helper` 1.4
