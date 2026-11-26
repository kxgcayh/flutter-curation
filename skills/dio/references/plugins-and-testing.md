# Plugins and testing

## Cookies (dio_cookie_manager)

```dart
import 'package:cookie_jar/cookie_jar.dart';
import 'package:dio/dio.dart';
import 'package:dio_cookie_manager/dio_cookie_manager.dart';

Future<Dio> createCookieDio(String appDocumentsPath) async {
  final jar = PersistCookieJar(storage: FileStorage('$appDocumentsPath/.cookies/'));
  return Dio()..interceptors.add(CookieManager(jar));
}
```

- **`CookieJar()`** keeps cookies in memory. **`PersistCookieJar`** writes them to disk. `FileStorage` creates its folder when it can, but the location must be writable: get it from `path_provider` (`getApplicationDocumentsDirectory()`). Keep persisted session cookies out of shared storage.
- **Logout:** call `jar.deleteAll()`.
- **Native only:** on the web the browser manages cookies (see `withCredentials` in adapters-and-security.md), and `CookieManager` doesn't apply.

## Using package:http clients (dio_compatibility_layer)

```dart
import 'package:dio/dio.dart';
import 'package:dio_compatibility_layer/dio_compatibility_layer.dart';
import 'package:http/http.dart' as http;

Dio dioOverHttpClient(http.Client client) =>
    Dio()..httpClientAdapter = ConversionLayerAdapter(client);
```

This is useful to reuse an existing `http.Client`, e.g. `cronet_http` / `cupertino_http` clients, or a `MockClient`. Closing the adapter closes the client. Cancelling a dio request doesn't stop the underlying `send`, so don't treat a cancelled Future as proof the transport stopped.

## Testing

Inject the `Dio` (constructor parameter, provider or DI) rather than creating it inside the class under test. Then fake the network at the adapter level, which keeps your interceptors, options and error handling in the test.

```dart
import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:test/test.dart';

class FakeAdapter implements HttpClientAdapter {
  FakeAdapter(this.handler);
  final ResponseBody Function(RequestOptions options) handler;
  final requests = <RequestOptions>[];

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    requests.add(options);
    return handler(options);
  }

  @override
  void close({bool force = false}) {}
}

ResponseBody jsonBody(Object data, int status) => ResponseBody.fromString(
      jsonEncode(data),
      status,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      },
    );

void main() {
  test('parses todos', () async {
    final adapter = FakeAdapter((options) => jsonBody([{'id': 1}], 200));
    final dio = Dio(BaseOptions(baseUrl: 'https://api.test/'))..httpClientAdapter = adapter;

    final response = await dio.get<List<dynamic>>('todos');

    expect(response.data, [{'id': 1}]);
    expect(adapter.requests.single.path, 'todos');
  });

  test('404 surfaces as badResponse', () async {
    final dio = Dio()..httpClientAdapter = FakeAdapter((_) => jsonBody({'message': 'nope'}, 404));

    await expectLater(
      dio.get<dynamic>('https://api.test/missing'),
      throwsA(isA<DioException>()
          .having((e) => e.type, 'type', DioExceptionType.badResponse)
          .having((e) => e.response?.statusCode, 'status', 404)),
    );
  });
}
```

- **Set the content-type header** on fake JSON bodies (`Headers.jsonContentType`), or dio returns a `String` instead of decoded JSON.
- **To simulate network failures,** `throw DioException.connectionError(requestOptions: options, reason: 'offline')` (or `DioException.connectionTimeout(...)`) from `fetch`.
- **For simpler cases,** an interceptor that calls `handler.resolve(Response(requestOptions: options, data: fake))` in `onRequest` works, but it skips the transformer and status validation.
- **Community packages** such as `http_mock_adapter` give a fluent API for the same adapter approach.
- **Test the risky paths yourself:** a fake adapter on the VM doesn't cover your retry re-entry, request replay, TLS timing or browser behaviour. Write tests for each (e.g. 3 concurrent 401s → exactly one refresh).
- **Repositories:** mocking the `Dio` object itself (mocktail `class MockDio extends Mock implements Dio {}`) works when you only need to stub `get`/`post`. You lose interceptor and error-mapping coverage, though.

## Other plugins

The dio plugin list includes `dio_smart_retry` (retries with backoff), `dio_cache_interceptor` (HTTP caching), `pretty_dio_logger` / `talker_dio_logger` (logging), `sentry_dio` (tracing) and `dio_image_provider`. They're community packages: check each one's version and SDK constraints before adding it.
