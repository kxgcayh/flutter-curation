---
name: dio
description: Write, review, debug or migrate Dart and Flutter HTTP code that uses dio or its adapters and plugins (Dio, BaseOptions, Options, interceptors, QueuedInterceptor, DioException, CancelToken, FormData, MultipartFile, downloads, HttpClientAdapter, certificate checks, dio_cookie_manager, dio_http2_adapter, native_dio_adapter, dio_web_adapter, dio_compatibility_layer). Use for API clients, auth token refresh, error mapping, retries, mocking dio in tests, configuring the Dio behind a retrofit client, and upgrading from dio 4.x or replacing APIs deprecated before 6.0. For provider or widget lifetimes, combine with the riverpod or flutter-hooks skills.
metadata:
  version: "0.3.0"
  docs-read: "2026-11-26"
  docs-source: "github.com/cfug/dio@f1bef46 (2026-10-19): dio README, doc/migration_guide.md, doc/plugins.md, lib/src, tests, examples, plugin READMEs and sources, COMPATIBILITY_POLICY.md"
  validated-against: "dio 5.11.1, dio_cookie_manager 3.5.0, dio_http2_adapter 2.9.0, dio_compatibility_layer 0.1.1 on Flutter 3.44.9 (native_dio_adapter 1.8.0) and 3.32.8 (native_dio_adapter 1.7.0)"
---

# dio

dio is an HTTP client for Dart and Flutter. It adds interceptors, global configuration, `FormData`, cancellation, timeouts and pluggable transport adapters on top of `dart:io` (and on top of the browser on the web).

## Step 1: inspect the project

Read `pubspec.yaml` / `pubspec.lock`, and find where the project creates its `Dio`:

| Found | Meaning |
| --- | --- |
| `dio` 5.x | Current API. This skill targets 5.x |
| `dio` 4.x, or `DioError`, `DioErrorType`, `DefaultHttpClientAdapter`, int timeouts | Old code: read [migration.md](references/migration.md) before editing |
| `dio_cookie_manager`, `dio_http2_adapter`, `native_dio_adapter`, `dio_compatibility_layer` | Plugins: see [adapters-and-security.md](references/adapters-and-security.md) and [plugins-and-testing.md](references/plugins-and-testing.md) |
| An existing `Dio` factory, provider or service | Reuse it. Don't create another instance with its own config |
| `retrofit` (or another dio-based generator) | Keep the API declarations there; inject the configured `Dio` into the generated client's constructor or factory |

Core `dio` supports Dart ≥ 2.18, so the SDK rarely limits it. Plugins do: `dio_web_adapter` 2.x needs Dart 3.3, `dio_http2_adapter` needs Dart 3.0, and `native_dio_adapter` 1.8 needs Flutter ≥ 3.35.6 (1.7 works on Flutter ≥ 3.13).

## One configured instance

```dart
final dio = Dio(
  BaseOptions(
    baseUrl: 'https://api.example.com/v1/',
    connectTimeout: const Duration(seconds: 10),
    receiveTimeout: const Duration(seconds: 20),
    headers: {'Accept': 'application/json'},
  ),
);

Future<List<Map<String, dynamic>>> fetchTodos() async {
  final response = await dio.get<List<dynamic>>('todos', queryParameters: {'limit': 20});
  return response.data!.cast<Map<String, dynamic>>();
}
```

- **Create one `Dio` per backend and share it** (a singleton, provider or DI). Base URL, timeouts, headers and interceptors live there.
- **`dio.clone()` shares** the options, interceptor objects, adapter and transformer by default. Pass copied `options:` and an independent `httpClientAdapter:` if the clients mutate or close separately. For calls that must bypass interceptors (e.g. token refresh), create a separate `Dio`.
- **`baseUrl` + paths:** dio concatenates `baseUrl` and the relative path, then normalises the result. It doesn't do URI reference resolution. Use a trailing `/` on the base and no leading `/` on the path (`'todos'`), and check the resulting URI when bases are nested. An absolute `http:`/`https:` path bypasses `baseUrl`, so scope auth headers to your origin.
- **Pass query values in `queryParameters`,** rather than concatenating them into the path (which skips encoding).
- **Type the response:** `dio.get<Map<String, dynamic>>(...)`, or `<List<dynamic>>`, `<String>` with `ResponseType.plain`, `<List<int>>` with `ResponseType.bytes`. JSON is decoded automatically when the response's content type is JSON.

## Core rules

1. **Catch `DioException`** (not `DioError`, deprecated) and branch on `e.type`. `e.response` is `null` for timeouts, connection and certificate errors: always null-check it. See [errors-and-cancellation.md](references/errors-and-cancellation.md).
2. **By default, only 2xx is success.** Other statuses throw `DioException` with `type == DioExceptionType.badResponse`. Change that with `validateStatus` only when the caller really handles those statuses.
3. **Interceptors complete their handler exactly once** (`next`, `resolve` or `reject`) on every path, then return. A callback that returns without completing it leaves the request hanging. Logging goes last, is debug-only, and never prints `Authorization`, cookies or bodies (see [interceptors.md](references/interceptors.md)).
4. **Use `QueuedInterceptor` for anything stateful,** like token refresh, so concurrent requests don't all refresh at once.
5. **Build a new `FormData` / `MultipartFile` for every request,** retries included. Reusing one throws "Cannot finalize". `formData.clone()` exists for this.
6. **Timeouts are `Duration`s.** A per-call `null` inherits the base value, and `Duration.zero` means no dio timeout. `connectTimeout` covers connecting, `sendTimeout` the upload, and `receiveTimeout` the wait for headers and then each idle gap between chunks (on IO).
7. **Cancel with a `CancelToken`** and detect it with `CancelToken.isCancel(e)`. Pass one token to every request of a screen, and cancel it in `dispose`.
8. **Never disable certificate checks** (`badCertificateCallback => true`) on a client that sends credentials. `validateCertificate` runs *after* the request is sent, so it's an extra check, not protection. See [adapters-and-security.md](references/adapters-and-security.md).
9. **Close a `Dio` you own** when you're done with it (`dio.close()`), e.g. short-lived clients in CLIs and tests.

## Deprecated APIs (removed in 6.0.0)

| Old | Use |
| --- | --- |
| `DioError`, `DioErrorType` | `DioException`, `DioExceptionType` |
| `DioErrorType.response` / `.connectTimeout` / `.other` | `.badResponse` / `.connectionTimeout` / `.unknown` |
| `DefaultHttpClientAdapter` | `IOHttpClientAdapter` (or the platform-neutral `HttpClientAdapter()`) |
| `IOHttpClientAdapter(onHttpClientCreate: (client) => ...)` | `IOHttpClientAdapter(createHttpClient: () => HttpClient()..)` |
| `DefaultTransformer` | `BackgroundTransformer` (or keep the default `FusedTransformer`) |
| `MultipartFile(stream, length)` | `MultipartFile.fromStream(() => stream, length)` |

## References (load the one the task needs)

| Task | Read |
| --- | --- |
| Options, timeouts, response types, JSON vs form-urlencoded, `FormData` and uploads, downloads, progress, streams, transformers | [requests-and-responses.md](references/requests-and-responses.md) |
| Interceptors, handler rules, `QueuedInterceptor`, auth headers, token refresh, retry | [interceptors.md](references/interceptors.md) |
| `DioException` types, user-facing error mapping, `validateStatus`, cancellation | [errors-and-cancellation.md](references/errors-and-cancellation.md) |
| Adapters (IO, browser, native, HTTP/2), proxies, certificate pinning, web and CORS | [adapters-and-security.md](references/adapters-and-security.md) |
| Cookies, `package:http` bridge, mocking dio in unit and widget tests | [plugins-and-testing.md](references/plugins-and-testing.md) |
| dio 4.x → 5.x, replacing deprecated APIs before 6.0 | [migration.md](references/migration.md) |
