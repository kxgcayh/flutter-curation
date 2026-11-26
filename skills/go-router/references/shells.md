# Shell routes (nested navigation)

| | `ShellRoute` | `StatefulShellRoute.indexedStack` |
| --- | --- | --- |
| What it gives | one nested `Navigator` inside a shared frame | one `Navigator` **per branch** (tab), kept alive in an `IndexedStack` |
| Switching sections | one nested stack; no independent per-tab history | each branch keeps its own stack and state |
| Typical use | a shared app bar or drawer, a wizard frame | bottom navigation, navigation rails, tabs |

## StatefulShellRoute for bottom navigation

```dart
final rootNavigatorKey = GlobalKey<NavigatorState>();

final shellRouter = GoRouter(
  navigatorKey: rootNavigatorKey,
  initialLocation: '/home',
  routes: [
    StatefulShellRoute.indexedStack(
      builder: (context, state, navigationShell) => ScaffoldWithNavBar(navigationShell: navigationShell),
      branches: [
        StatefulShellBranch(routes: [
          GoRoute(
            path: '/home',
            builder: (context, state) => const HomeScreen(),
            routes: [
              // Stays inside the shell: the nav bar remains visible.
              GoRoute(path: 'details', builder: (context, state) => const DetailsScreen()),
            ],
          ),
        ]),
        StatefulShellBranch(routes: [
          GoRoute(path: '/settings', builder: (context, state) => const SettingsScreen()),
        ]),
      ],
    ),
    // Full-screen, above the shell (no nav bar).
    GoRoute(
      path: '/player',
      parentNavigatorKey: rootNavigatorKey,
      builder: (context, state) => const PlayerScreen(),
    ),
  ],
);

class ScaffoldWithNavBar extends StatelessWidget {
  const ScaffoldWithNavBar({required this.navigationShell, super.key});
  final StatefulNavigationShell navigationShell;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: navigationShell,
      bottomNavigationBar: NavigationBar(
        selectedIndex: navigationShell.currentIndex,
        onDestinationSelected: (index) => navigationShell.goBranch(
          index,
          // Tapping the active tab again returns to its root.
          initialLocation: index == navigationShell.currentIndex,
        ),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home), label: 'Home'),
          NavigationDestination(icon: Icon(Icons.settings), label: 'Settings'),
        ],
      ),
    );
  }
}
```

- **Routes go on the branches,** not on the `StatefulShellRoute` itself. Each branch needs at least one route; its first route is the branch's default location.
- **`navigationShell.goBranch(index)`** restores that branch's last location. With `initialLocation: true`, it navigates to the branch's configured `initialLocation`, or to its first eligible `GoRoute` when none is set.
- **Switch branches with `goBranch`,** not `context.go(...)`, when you want to keep each tab's stack. A `go` to a location inside another branch works too, but replaces that branch's stack.
- **`StatefulShellBranch` options:**
  - `navigatorKey:` for an explicit navigator key per branch
  - `initialLocation:` to choose the branch's default location
  - `preload: true` to build the branch before it's first opened
  - `observers:` for per-branch navigator observers
  - `restorationScopeId:` for state restoration
- **Derive tabs from `navigationShell.route.branches`** instead of hard-coding the count, if they're configured dynamically.

## Navigator keys and full-screen routes

- **`GoRouter(navigatorKey:)`** is the root navigator. Give a route `parentNavigatorKey: rootNavigatorKey` to show it above every shell: full-screen players, login, modal flows.
- **A route without `parentNavigatorKey`** is placed in the nearest enclosing shell navigator. Set `parentNavigatorKey` only to the root navigator or an ancestor shell's navigator, never to an unrelated branch.
- **Inside a shell,** `Navigator.of(context)` finds the shell's navigator. Use `Navigator.of(context, rootNavigator: true)` for dialogs that must cover the shell.

## ShellRoute

```dart
final frameRouter = GoRouter(
  initialLocation: '/inbox',
  routes: [
    ShellRoute(
      builder: (context, state, child) => Scaffold(
        appBar: AppBar(title: const Text('Mail')),
        body: child, // the nested Navigator
      ),
      routes: [
        GoRoute(path: '/inbox', builder: (context, state) => const InboxScreen()),
        GoRoute(path: '/sent', builder: (context, state) => const SentScreen()),
      ],
    ),
  ],
);
```

## Observers (17.0+)

Since 17.0, navigation inside shells also notifies the `GoRouter`'s root observers: `notifyRootObserver` defaults to `true` on both `ShellRoute` and `StatefulShellRoute`. Root analytics observers therefore see shell navigation. Adding local `observers:` to a shell or branch does **not** stop that forwarding; set `notifyRootObserver: false` explicitly where duplicate analytics matter.
