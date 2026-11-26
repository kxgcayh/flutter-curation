# Redirects, guards and errors

## Order of evaluation

For every navigation (deep link, `go`, `push`, browser back or forward):

1. **Top-level `onEnter`** (16.3+) runs once, against the literal requested target. It returns `Allow` or `Block`. A plain `pop` doesn't call it, though a restoration can.
2. If it's allowed, the **top-level `redirect`** runs.
3. Then each matched **`GoRoute.redirect`** runs, from the top route down.

A redirect that returns a new location starts the matching again. Top-level and route-level redirects share one `redirectLimit` (default 5), and going over it raises a `GoException`. `onEnter` isn't re-run for redirect targets: `next` is always the original, pre-redirect location. A route that `onEnter` would block can therefore still be reached *through* a redirect.

## Auth redirect with refreshListenable

```dart
class AuthState extends ChangeNotifier {
  bool _signedIn = false;
  bool get signedIn => _signedIn;

  void signIn() {
    _signedIn = true;
    notifyListeners();
  }

  void signOut() {
    _signedIn = false;
    notifyListeners();
  }
}

GoRouter createRouter(AuthState auth) => GoRouter(
      refreshListenable: auth, // re-run redirects whenever auth changes
      redirect: (context, state) {
        final loggingIn = state.uri.path == '/login';
        if (!auth.signedIn) {
          if (loggingIn) return null;
          // Remember where the user was going: path + query only, never scheme/host.
          final localTarget = Uri(path: state.uri.path, query: state.uri.hasQuery ? state.uri.query : null);
          return Uri(path: '/login', queryParameters: {'from': localTarget.toString()}).toString();
        }
        if (!loggingIn) return null; // stay

        // Signed in on /login: return to `from` only if it's a known internal route.
        final from = Uri.tryParse(state.uri.queryParameters['from'] ?? '');
        const returnRoutes = {'/'}; // this example declares only '/' as a return route
        if (from == null || from.hasScheme || from.hasAuthority || !returnRoutes.contains(from.path)) {
          return '/';
        }
        return Uri(path: from.path, query: from.hasQuery ? from.query : null).toString();
      },
      routes: [
        GoRoute(path: '/', builder: (context, state) => const HomeScreen()),
        GoRoute(path: '/login', builder: (context, state) => const LoginScreen()),
      ],
    );
```

- **Return `null`** (or the current location) to stay, and a location to redirect.
- **Read auth state synchronously** in the redirect. Redirects can be `async` (`FutureOr<String?>`), but slow work stalls every navigation; load state up front instead.
- **`refreshListenable`** is any `Listenable` (`ChangeNotifier`, `ValueNotifier`, or a stream adapter). Without it, signing out doesn't move the user until the next navigation.
- **Avoid loops:** check whether you're already on the target (`loggingIn` above) before redirecting.
- **Treat the return target as untrusted input:** it can arrive in a deep link. For a larger app:
  - allowlist the internal routes you accept as return targets, and validate their parameters
  - reject absolute URIs, network-path references (`//host/...`), the login and logout routes, and invalid targets
  - keep only the query parameters the destination accepts

  Authorization still belongs on the protected data and actions; a redirect is only navigation.
- **With Riverpod,** build a long-lived router in a provider, with an auth `Listenable` owned by the same scope, and dispose both with that owner (`ref.onDispose`). Don't `ref.watch` inside the redirect, and don't recreate the `GoRouter` on auth changes. Auth-state ownership itself belongs to the riverpod skill.

**Route-level redirect** for one subtree:

```dart
GoRoute(
  path: '/admin',
  redirect: (context, state) => currentUserIsAdmin() ? null : '/',
  builder: (context, state) => const AdminScreen(),
),
```

## onEnter guards (16.3+)

`onEnter` decides whether the **requested** navigation happens at all. It receives the current and next states, and the router. Use it as a navigation veto (for example a temporary UX block), not as your access-control layer: redirect targets aren't re-checked by it.

```dart
final guardedRouter = GoRouter(
  onEnter: (context, current, next, router) {
    final path = next.uri.path;
    // Block the account area for signed-out users (match the segment, not any prefix).
    if ((path == '/account' || path.startsWith('/account/')) && !isSignedIn()) {
      return const Block.stop();
    }
    return const Allow();
  },
  redirect: (context, state) => isSignedIn() && state.uri.path == '/login' ? '/' : null,
  routes: [
    GoRoute(path: '/', builder: (context, state) => const HomeScreen()),
    GoRoute(path: '/login', builder: (context, state) => const LoginScreen()),
    GoRoute(path: '/account', builder: (context, state) => const AccountScreen()),
  ],
);
```

| Result | Effect |
| --- | --- |
| `const Allow()` | proceed (then the redirects run) |
| `Allow(then: () => ...)` | proceed. The callback runs asynchronously after the navigation is committed; errors are reported, not reverted, and the destination widget may not have built yet |
| `const Block.stop()` | cancel. Keeps the current state when there is one, and resets the redirect history |
| `Block.then(() => router.go(...))` | cancel, then schedule the follow-up callback (typically a navigation elsewhere) |

- **When to use which:** use `onEnter` for "may this requested navigation happen?", and `redirect` for "which location should be shown?". Send signed-in users away from `/login` with a `redirect` (as above), not a hard block. A hard block on a direct startup at `/login` has no previous route to stay on.
- **On a blocked deep link at startup,** with no previous route to stay on, go_router 17.4+ raises `BlockedInitialNavigationException`, a `GoException` you can handle in `onException`.
- **`then` callbacks triggered by `refreshListenable`** were sometimes lost before 17.2.

## Errors and unknown URLs

```dart
final routerWithErrors = GoRouter(
  routes: [GoRoute(path: '/', builder: (context, state) => const HomeScreen())],
  errorBuilder: (context, state) => NotFoundScreen(message: state.error?.message),
);
```

- **A `GoException`** can mean an unmatched URL, a redirect failure or loop, or another navigation error.
- **Configure at most one of** `onException`, `errorBuilder` and `errorPageBuilder` (go_router asserts this).
- **`errorBuilder` / `errorPageBuilder`** render a page for the exception, with `state.error` set.
- **`onException(context, state, router)`** lets you decide instead, such as `router.go('/')`, or ignoring the error.
- **`GoError` / `AssertionError`** mean the configuration is invalid (a missing `/` route, no builder, a top-level path without a leading `/`). Fix the code; don't catch them.
- **Without any error handler,** go_router shows a default error screen.
