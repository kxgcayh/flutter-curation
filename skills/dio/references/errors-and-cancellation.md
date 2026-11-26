# Errors and cancellation

## DioException

Request-pipeline failures surface as a `DioException`. `DioError` is a deprecated alias, and `catch (e)` on `Exception` hides the useful fields.

Not everything goes through it: API misuse, argument validation, and errors while you consume a streamed body later can throw outside that wrapper. A response may be absent. Error bodies are kept by default, but a decoding failure can prevent a usable body, or even the `badResponse` result.

| Field | Meaning |
| --- | --- |
| `type` | a `DioExceptionType` (below) |
| `response` | the server's response, **only** when one arrived (`badResponse`, sometimes `badCertificate`). `null` otherwise |
| `requestOptions` | the request that failed (path, headers, `extra`) |
| `error` / `stackTrace` | the underlying error (`SocketException`, `HandshakeException`, ...), mostly for `unknown` / `connectionError` |
| `message` | a human-readable description, for logs (not UI) |

| `DioExceptionType` | When | Typical handling |
| --- | --- | --- |
| `connectionTimeout` | couldn't connect within `connectTimeout` | "Check your connection", retry (idempotent requests only) |
| `sendTimeout` | upload exceeded `sendTimeout` | retry, or a smaller payload |
| `receiveTimeout` | the server was too slow between chunks | retry only if idempotent: the server may already have processed the request |
| `transformTimeout` | decoding exceeded `transformTimeout` | report a bug or a size issue |
| `badCertificate` | TLS validation or pinning failed | don't retry; security error |
| `badResponse` | a status outside `validateStatus` (non-2xx by default) | read `response.statusCode` and `response.data` |
| `cancel` | the request was cancelled via `CancelToken` | usually ignore silently |
| `connectionError` | DNS, refused connection, socket closed | offline handling, retry |
| `unknown` | anything else; inspect `error` | log, generic message |

```dart
sealed class ApiFailure {
  const ApiFailure();
}
class Offline extends ApiFailure { const Offline(); }
class Cancelled extends ApiFailure { const Cancelled(); }
class ServerError extends ApiFailure {
  const ServerError(this.statusCode, this.message);
  final int? statusCode;
  final String? message;
}
class Unexpected extends ApiFailure {
  const Unexpected(this.error);
  final Object? error;
}

ApiFailure mapDioException(DioException e) {
  switch (e.type) {
    case DioExceptionType.cancel:
      return const Cancelled();
    case DioExceptionType.connectionTimeout:
    case DioExceptionType.receiveTimeout:
    case DioExceptionType.sendTimeout:
    case DioExceptionType.connectionError:
      return const Offline();
    case DioExceptionType.badResponse:
      final data = e.response?.data;
      final raw = data is Map ? data['message'] : null;
      final message = raw is String ? raw : null; // error bodies may be HTML, text or another shape
      return ServerError(e.response?.statusCode, message);
    case DioExceptionType.badCertificate:
    case DioExceptionType.transformTimeout:
    case DioExceptionType.unknown:
      return Unexpected(e.error ?? e);
  }
}

Future<Map<String, dynamic>?> loadProfile() async {
  try {
    final response = await dio.get<Map<String, dynamic>>('me');
    return response.data;
  } on DioException catch (e) {
    final failure = mapDioException(e);
    if (failure is Cancelled) return null;
    throw failure; // let the UI layer show a message
  }
}
```

- **Map errors once,** in a repository or API layer, into app-level failures. Don't spread `DioException` checks through the UI.
- **Read `e.response?.data`** for the server's error body. It's kept by default (`receiveDataWhenStatusError: true`).
- **A `switch` on `DioExceptionType`** is exhaustive. When dio adds a type, the compiler points you to the handling to update.
- **Throwing your own `DioException`** in interceptors or adapters: use the named constructors (`DioException.badResponse(statusCode:, requestOptions:, response:)`, `DioException.connectionError(requestOptions:, reason:)`, `DioException.requestCancelled(...)`, ...), or `DioException(requestOptions:, error:, type:)`. Fields are final; use `copyWith` to change the message.

## validateStatus

```dart
// Treat 404 as a normal result for this call only.
final response = await dio.get<Map<String, dynamic>>(
  'users/42',
  options: Options(
    validateStatus: (status) => status != null && ((status >= 200 && status < 300) || status == 404),
  ),
);
if (response.statusCode == 404) {
  print('not found');
}
```

`validateStatus` controls which statuses are accepted, not how the body is typed: a 404 body may be HTML or text, so decode it deliberately (or request `ResponseType.plain`). Widen `validateStatus` only per request, and only where the code checks `statusCode` itself. Setting `validateStatus: (_) => true` globally turns every server error into a "success" that callers silently mis-parse.

## Cancellation

```dart
final token = CancelToken();

Future<void> search(String query) async {
  try {
    final response = await dio.get<List<dynamic>>('search', queryParameters: {'q': query}, cancelToken: token);
    print(response.data);
  } on DioException catch (e) {
    if (CancelToken.isCancel(e)) return; // cancelled: not an error for the user
    rethrow;
  }
}

void onLeaveScreen() => token.cancel('screen closed');
```

- **One token can cancel many requests.** Pass the same token to every request of a screen or feature.
- **A cancelled token stays cancelled** (`token.isCancelled`). Create a new `CancelToken` for the next batch, for example when a search query changes.
- **`token.whenCancel`** is a Future that completes with the cancel exception, useful for custom adapters.
- **With Riverpod:** create the token inside the provider and call `ref.onDispose(token.cancel)`. With hooks, call `useEffect(() => token.cancel, [token])`.
