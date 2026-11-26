# Migration

## dio 4.x → 5.x

| 4.x | 5.x |
| --- | --- |
| `connectTimeout: 5000` (int ms) | `connectTimeout: const Duration(seconds: 5)` (also `sendTimeout`, `receiveTimeout`) |
| `DefaultHttpClientAdapter()` | `IOHttpClientAdapter()` (`package:dio/io.dart`), or the platform-neutral `HttpClientAdapter()` |
| `class MyAdapter extends HttpClientAdapter` | `class MyAdapter implements HttpClientAdapter` |
| `(dio.httpClientAdapter as DefaultHttpClientAdapter).onHttpClientCreate = (client) {...}` | `dio.httpClientAdapter = IOHttpClientAdapter(createHttpClient: () => HttpClient()...)` |
| `DioError` / `DioErrorType` | `DioException` / `DioExceptionType` (the 5.x names; the old ones are deprecated aliases) |
| `DioErrorType.response` | `DioExceptionType.badResponse` |
| `DioErrorType.connectTimeout` | `DioExceptionType.connectionTimeout` |
| `DioErrorType.other` | `DioExceptionType.unknown` (plus new `badCertificate`, `connectionError`, `transformTimeout`) |
| `error.message = '...'` (mutable fields) | `error.copyWith(message: '...')` (fields are final; named constructors like `DioException.badResponse`) |
| everything from `package:dio/dio.dart` | platform classes moved: `package:dio/io.dart` (native), `package:dio/browser.dart` (web) |
| `get(path, queryParameters:)` | `get` and `getUri` also accept `data:` |

Before:

```dart
final dio = Dio(BaseOptions(connectTimeout: 5000, receiveTimeout: 10000));

void handle(DioError e) {
  if (e.type == DioErrorType.response) print(e.response?.statusCode);
}
```

After:

```dart
final dio = Dio(
  BaseOptions(
    connectTimeout: const Duration(seconds: 5),
    receiveTimeout: const Duration(seconds: 10),
  ),
);

void handle(DioException e) {
  if (e.type == DioExceptionType.badResponse) print(e.response?.statusCode);
}
```

### From 3.x or earlier

Code with `dio.lock()`, `dio.resolve()` / `dio.reject()` in interceptors, or callback-style interceptors predates 4.0. In 4.x+, interceptor callbacks receive a `handler`, and serialising work uses `QueuedInterceptor` (see interceptors.md). Rewrite these interceptors; don't port them line by line.

## Before dio 6.0: replace deprecated APIs

These still compile in 5.x with deprecation warnings, and 6.0 removes them:

| Deprecated | Replacement |
| --- | --- |
| `DioError`, `DioErrorType` | `DioException`, `DioExceptionType` |
| `DefaultHttpClientAdapter` | `IOHttpClientAdapter` |
| `IOHttpClientAdapter(onHttpClientCreate:)`, the `OnHttpClientCreate` typedef | `createHttpClient:`, the `CreateHttpClient` typedef |
| `DefaultTransformer` | `BackgroundTransformer`, or the default `FusedTransformer` |
| `MultipartFile(stream, length)` | `MultipartFile.fromStream(() => stream, length)` (cloneable for retries) |

Run `dart fix --dry-run` first, then `dart fix --apply`: dio ships `fix_data` for several of these renames (`DioError`, `DefaultHttpClientAdapter`, `DefaultTransformer`, `OnHttpClientCreate` / `onHttpClientCreate`). Then search for the remaining names and run `dart analyze`. A rename can't turn a `MultipartFile(stream, length)` argument into a factory that creates a fresh stream, so fix those by hand.

Examples in this skill target dio 5.11.x (`DioExceptionType.transformTimeout`, `dio.query`). The sealed-class error mapping needs Dart 3.
