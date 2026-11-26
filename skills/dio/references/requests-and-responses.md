# Requests and responses

## BaseOptions vs Options

`BaseOptions` (on the `Dio`) sets defaults for every request. `Options` (per call) overrides them for one request. They're merged into the `RequestOptions` that interceptors and adapters see:
- **Scalar fields:** a non-null per-call value wins.
- **`headers`:** merged case-insensitively.
- **`queryParameters` and `extra`:** merged by key, with the per-call values winning.

```dart
final response = await dio.post<Map<String, dynamic>>(
  'orders',
  data: {'item': 'book', 'qty': 1},
  options: Options(
    headers: {'Idempotency-Key': 'order-123'},
    receiveTimeout: const Duration(seconds: 60),
    extra: {'retry': false}, // free-form data for interceptors
  ),
);
```

| Option | Meaning |
| --- | --- |
| `method` | set by `get`/`post`/...; use `request()` + `Options(method:)` for others |
| `baseUrl` (BaseOptions only) | prefix for relative paths |
| `connectTimeout` | time to open the connection (also settable per call via `Options(connectTimeout:)`) |
| `sendTimeout` | time to send the request body |
| `receiveTimeout` | on IO: time waiting for the response headers after sending, then the maximum idle gap between chunks (not the total download time) |
| `transformTimeout` | time for the background decode path; doesn't bound every custom or synchronous transformer. Best-effort on web |
| `headers` | case-insensitive; `preserveHeaderCase: true` keeps the casing (not on web XHR or HTTP/2) |
| `contentType` | request content type; by default it's implied from the data |
| `responseType` | `json` (default), `plain`, `bytes`, `stream` |
| `validateStatus` | which statuses count as success (default: 200–299) |
| `receiveDataWhenStatusError` | keep the body on error responses (default `true`), for reading API error messages |
| `followRedirects`, `maxRedirects` | defaults `true`, `5` |
| `listFormat` | how lists encode in query strings and form bodies: `multi` (default), `multiCompatible` (bracketed keys, `a[]=1&a[]=2`), `csv`, `ssv`, `tsv`, `pipes` |
| `extra` | per-request data for interceptors and transformers (not sent) |

Timeouts: a per-call `null` inherits the base value, while `Duration.zero` means "no dio timeout". Platform and OS timeouts still apply either way. The phases above are for the IO adapter; browser and native adapters can measure them differently.

## Request bodies

| `data` | Sent as |
| --- | --- |
| `Map` / `List` | JSON (`application/json`), set by the default imply-content-type interceptor |
| a model object | convert it first (`model.toJson()`), or set a JSON `contentType` explicitly |
| `String` | sent unchanged; set `contentType` yourself unless it's JSON |
| `FormData` | `multipart/form-data` |
| `Map` with `contentType: Headers.formUrlEncodedContentType` | `application/x-www-form-urlencoded` |
| `Stream<List<int>>` | streamed bytes; set `Headers.contentLengthHeader` for progress |

```dart
// Form-urlencoded login
await dio.post(
  'login',
  data: {'username': 'ada', 'password': 'secret'},
  options: Options(contentType: Headers.formUrlEncodedContentType),
);

// QUERY method (safe and idempotent like GET, with a body): dio 5.11.0+, and the server must support it
await dio.query('search', data: {'filter': {'name': 'dio'}});
```

## Uploads with FormData

```dart
Future<void> uploadAvatar(String userId, String path) async {
  final form = FormData.fromMap({
    'userId': userId,
    'avatar': await MultipartFile.fromFile(path, filename: 'avatar.jpg'),
  });
  await dio.post(
    'avatars',
    data: form,
    onSendProgress: (sent, total) => print('${(sent / total * 100).round()}%'),
  );
}
```

- **Build a new `FormData` for every request,** including retries, because a `FormData` can be sent only once ("Cannot finalize"). For a retry interceptor, send `form.clone()`, or rebuild the form from its source data.
- **File constructors:** `MultipartFile.fromFile` (async) and `fromFileSync` need native file access (not on web). `fromBytes` and `fromString` work everywhere. `fromStream(() => stream, length)` must return a **fresh** stream on every call, so the file can be re-sent. The bare `MultipartFile(stream, length)` constructor is deprecated.
- **Lists in `FormData.fromMap`** are named according to `listFormat` (the default `multiCompatible` for `FormData` gives `files[]`), and naming also depends on whether the entries are files. To repeat the same key without brackets, build it by hand:

```dart
final form = FormData();
form.files.addAll([
  MapEntry('files', await MultipartFile.fromFile('a.txt')),
  MapEntry('files', await MultipartFile.fromFile('b.txt')),
]);
```

- **Upload progress needs a known length.** `FormData` and file uploads provide one; for a raw stream, set `Headers.contentLengthHeader`.

## Response types

```dart
final json = await dio.get<Map<String, dynamic>>('me'); // decoded JSON
final text = await dio.get<String>('robots.txt', options: Options(responseType: ResponseType.plain));
final bytes = await dio.get<List<int>>('logo.png', options: Options(responseType: ResponseType.bytes));
final stream = await dio.get<ResponseBody>('big.csv', options: Options(responseType: ResponseType.stream));
await for (final chunk in stream.data!.stream) {
  print(chunk.length);
}
```

The `Response` holds `data`, `statusCode`, `statusMessage`, `headers` (`response.headers.value('etag')`), `requestOptions`, `redirects`, `isRedirect` and `extra`. `Response.extra` and `RequestOptions.extra` are unrelated maps.

## Downloads

```dart
Future<void> downloadReport(String dir, CancelToken token) async {
  await dio.download(
    'reports/2026.pdf',
    '$dir/2026.pdf', // or (Headers headers) => '<path>' to choose the name from headers
    cancelToken: token,
    deleteOnError: true, // default: remove the partial file on failure
    onReceiveProgress: (received, total) {
      if (total > 0) print('${(received / total * 100).toStringAsFixed(0)}%');
    },
  );
}
```

- **`total` is `-1`** on IO when the length is unknown: no `content-length`, or a compressed body with the default `lengthHeader`. Treat `total <= 0` as indeterminate progress.
- **Resuming isn't automatic.** `fileAccessMode: FileAccessMode.append` only appends bytes. To resume safely:
  - send a `Range` header
  - check for HTTP **206**, a matching `Content-Range`, and an unchanged validator (`ETag` / `Last-Modified`) before appending
  - restart from scratch if you get a full 200
  - set `deleteOnError: false` deliberately, because the default `true` removes the partial file
- **On the web,** the bytes are buffered in memory and the save path is only the browser's suggested filename. CORS applies, `append` throws `UnsupportedError`, and progress comes from browser events.

## Transformers (response decoding)

- **dio's default is `FusedTransformer(contentLengthIsolateThreshold: 50 * 1024)`.** It decodes UTF-8 JSON in a single fast pass, and on IO switches to a background isolate when the content length (or buffered size) is ≥ 50 KiB.
- **A bare `FusedTransformer()`** defaults to `-1`, which always parses on the current isolate.
- **A custom `responseDecoder`** bypasses the fast path.
- **The web** has no background isolate for this path.
- **Automatic JSON decoding** needs `ResponseType.json` plus a JSON content type. Use `plain`, `bytes` or `stream` to handle the body yourself.
- **Expensive model mapping** after decoding is your own work: profile it, and on native move it off the UI isolate with `Isolate.run` or Flutter's `compute`.
- **`DefaultTransformer` is deprecated** (it's an alias of `SyncTransformer`).
- **A custom `Transformer`** is rarely needed. To map JSON to models, do it after the request, or in a repository layer.
