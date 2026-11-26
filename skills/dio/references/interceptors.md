# Interceptors

Interceptors run in the order they were added: `onRequest` before the request is sent, `onResponse` for accepted responses, `onError` for any `DioException` (including statuses rejected by `validateStatus`).

## Handler rules

Each callback must complete its handler **once**, by calling `next`, `resolve` or `reject`, and then return immediately.

- **A normal return without completing the handler** leaves the request pending forever, unless it's cancelled.
- **In current dio,** a synchronous throw, or a failure of the `Future` the callback returns before it completes the handler, is routed as an error. dio 5.9.1 fixed this for queued synchronous throws; 5.10 fixed it for returned async throws, queue cancellation and queued reject forwarding.
- **Failures in detached async work** (an un-awaited Future), or after the handler completed, aren't routed. They surface in the callback's zone.

| Callback | `handler.next(x)` | `handler.resolve(response, [bool])` | `handler.reject(error, [bool])` |
| --- | --- | --- | --- |
| `onRequest(options, handler)` | continue to the next interceptor, then send | finish with this response (no network). Passing `true` enters the response stage from the start | fail now. Passing `true` enters the error stage from the start |
| `onResponse(response, handler)` | continue | finish with this response, skipping the later interceptors | turn it into an error. Passing `true` runs the error stage |
| `onError(error, handler)` | continue to the next `onError` | **recover**: the caller receives this response as a success | fail with this error. Passing `true` continues through the remaining error interceptors |

The optional `bool` (`callFollowingResponseInterceptor` / `callFollowingErrorInterceptor`) is **positional**: `handler.resolve(response, true)`.

```dart
class AuthHeaderInterceptor extends Interceptor {
  AuthHeaderInterceptor({required this.apiOrigin, required this.readToken});

  /// e.g. 'https://api.example.com' — the only origin that may receive the token.
  final String apiOrigin;
  final String? Function() readToken;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final token = readToken();
    // Absolute URLs bypass baseUrl: never send the bearer token to another origin.
    if (options.uri.origin == apiOrigin && token != null && token.isNotEmpty) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }
}

void installAuth(Dio dio, String? Function() readToken) {
  dio.interceptors.add(AuthHeaderInterceptor(apiOrigin: 'https://api.example.com', readToken: readToken));
}
```

- **Use `InterceptorsWrapper(onRequest:, onResponse:, onError:)`** for small inline interceptors.
- **Async work in a callback:** `await` it inside a `try`/`catch`, complete the handler in every branch, and `return` right after.
- **Pass data between interceptors** in `options.extra` (e.g. `extra['skipAuth'] = true`).
- **Keep cross-origin redirects away from authenticated requests,** unless you control how `Authorization` is forwarded.

## Logging

`LogInterceptor` logs URLs and request/response headers by default. Its default printer only prints in debug mode (behind an `assert`), but replacing it with `debugPrint` removes that gate. Logs can therefore leak `Authorization`, cookies, query strings and bodies.

- **Log only allowlisted fields:** method, route template, status, latency. Do it in debug builds only.
- **Never log** `Authorization` or cookie headers, bodies, query strings, or unredacted exception text, in any environment.
- **Add the diagnostic interceptor last,** so it sees the final request, and make it redact.

```dart
class SafeLogInterceptor extends Interceptor {
  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    assert(() {
      final o = response.requestOptions;
      print('${o.method} ${o.uri.path} -> ${response.statusCode}');
      return true;
    }());
    handler.next(response);
  }
}
```

## Interceptor vs QueuedInterceptor

`Interceptor` callbacks run concurrently: ten parallel requests enter `onError` ten times at once. `QueuedInterceptor` (and `QueuedInterceptorsWrapper`) processes calls one at a time, with **separate queues** for `onRequest`, `onResponse` and `onError`. Use it when a callback reads or writes shared state, like a token refresh.

Because the queues are per callback, an `onError` that waits for a request **sent through the same client** can deadlock. If that request fails, its error joins the same `onError` queue, behind the call that is waiting for it. So replay refreshed requests through a separate client, as shown below.

## Token refresh on 401

This corrects the upstream `queued_interceptor_crsftoken` example. That example crashes on errors without a response (`error.response!`), returns the original 401 instead of the retried response, and retries through the same client.

It uses three clients:
- **the app client,** with this interceptor
- **a refresh client** with no auth interceptors, so a 401 from the refresh endpoint can't recurse
- **a replay client** with the app's base URL and transport, but **without** this interceptor or any other retry logic

```dart
class AuthSession {
  int id = 0; // bump on sign-in / sign-out so stale refreshes are discarded
  String? accessToken;
  String? refreshToken;

  void clear() {
    id++;
    accessToken = null;
    refreshToken = null;
  }
}

class RefreshTokenInterceptor extends QueuedInterceptor {
  RefreshTokenInterceptor({
    required this.apiOrigin,
    required this.session,
    required this.refreshDio,
    required this.replayDio,
  });

  final String apiOrigin;
  final AuthSession session;
  final Dio refreshDio;
  final Dio replayDio;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final token = session.accessToken;
    if (options.uri.origin == apiOrigin && token != null && token.isNotEmpty) {
      options.headers['Authorization'] = 'Bearer $token';
      options.extra['authSession'] = session.id; // this interceptor attached a token
    }
    handler.next(options);
  }

  @override
  Future<void> onError(DioException err, ErrorInterceptorHandler handler) async {
    final original = err.requestOptions;
    final sentSession = original.extra['authSession'];
    if (err.response?.statusCode != 401 ||
        sentSession == null || // we didn't attach a token: not ours to refresh
        sentSession != session.id || // signed out / switched account meanwhile
        original.extra['retried'] == true ||
        (original.cancelToken?.isCancelled ?? false) ||
        original.data is Stream) {
      // a consumed stream body can't be replayed
      return handler.next(err);
    }

    // Another queued request may already have refreshed: compare the token it was sent with.
    if (original.headers['Authorization'] == 'Bearer ${session.accessToken}') {
      try {
        final refreshed = await refreshDio.post<Map<String, dynamic>>(
          'auth/refresh',
          data: {'refreshToken': session.refreshToken},
        );
        final token = refreshed.data?['accessToken'];
        if (token is! String || token.isEmpty) return handler.next(err);
        if (session.id != sentSession) return handler.next(err); // session ended during refresh
        session.accessToken = token;
      } on DioException catch (refreshError) {
        // Only a definitive "refresh token invalid" ends the session; keep it on transient failures.
        final status = refreshError.response?.statusCode;
        if ((status == 400 || status == 401) && session.id == sentSession) session.clear();
        // Keep the original request, and attach why the refresh failed.
        return handler.next(err.copyWith(error: refreshError, message: 'Token refresh failed'));
      }
    }

    final accessToken = session.accessToken;
    if (accessToken == null || accessToken.isEmpty) return handler.next(err);

    final body = original.data;
    final retry = original.copyWith(
      data: body is FormData ? body.clone() : body, // FormData can be sent only once
      headers: {...original.headers, 'Authorization': 'Bearer $accessToken'},
      extra: {...original.extra, 'retried': true},
    );
    try {
      final response = await replayDio.fetch<dynamic>(retry);
      return handler.resolve(response); // recover: the caller gets the replayed response
    } on DioException catch (failure) {
      return handler.next(failure);
    }
  }
}
```

- **`handler.resolve(response)`** is the right way to recover. It ends the error stage and gives the caller the replayed response.
- **The replay client runs its own interceptor chain.** Give it the same logging and headers you need, but not this interceptor.
- **`FormData.clone()` only works when every file part can be re-read** (`fromFile`, `fromBytes`, or a `fromStream` factory that returns a fresh stream). Raw stream bodies aren't replayed.
- **If you need same-client replay,** use a plain `Interceptor` instead, with a shared in-flight refresh `Future` per session, and keep the one-retry marker.
- **On a definitive refresh failure,** sign the user out upstream, e.g. through a session provider. Don't loop.

## Retrying transient failures

For retries with backoff on timeouts, connection errors and 5xx, prefer the `dio_smart_retry` plugin (listed in the dio plugin docs) over a hand-rolled loop. Either way:
- **Retry only when the endpoint is idempotent,** or honours an idempotency key you send. A timeout can happen *after* the server processed the request.
- **Rebuild the payload** for each attempt.
- **Respect cancellation and `Retry-After`,** and cap the attempts.

## Caching and mocking

Interceptors can answer from a cache, or with fake data, by calling `handler.resolve(Response(requestOptions: options, data: cached))` in `onRequest`. For production HTTP caching, see `dio_cache_interceptor`. For tests, a fake `HttpClientAdapter` is cleaner (see plugins-and-testing.md).
