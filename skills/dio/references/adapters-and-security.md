# Adapters, proxies and certificates

An `HttpClientAdapter` performs the actual HTTP call. `Dio()` picks the platform default:
- `IOHttpClientAdapter` (`package:dio/io.dart`, `dart:io` `HttpClient`) on mobile and desktop
- `BrowserHttpClientAdapter` (`package:dio/browser.dart`, from the bundled `dio_web_adapter`) on the web

`HttpClientAdapter()` builds the right one for the current platform.

| Adapter | Package | Use when |
| --- | --- | --- |
| `IOHttpClientAdapter` | `dio` (`dio/io.dart`) | default on native; proxies, pinning, `HttpClient` tuning |
| `BrowserHttpClientAdapter` | `dio` (`dio/browser.dart`) | web (automatic). `withCredentials` for cookies on cross-origin requests |
| `NativeAdapter` | `native_dio_adapter` (1.8: Flutter ≥ 3.35.6; 1.7: Flutter ≥ 3.13) | use the OS HTTP stack (`cupertino_http` / `cronet_http`): system VPN and proxy, HTTP/3, platform TLS |
| `Http2Adapter` | `dio_http2_adapter` (Dart ≥ 3.0) | HTTP/2 with connection reuse |
| `ConversionLayerAdapter` | `dio_compatibility_layer` | run dio on top of a `package:http` `Client`. Closing the adapter closes the client. Cancelling a dio request doesn't stop the underlying `send` |

- **Importing `dio/io.dart` breaks web builds** (it depends on `dart:io`). Keep adapter setup in a native-only file, or use conditional imports.
- **Custom adapters** must `implements HttpClientAdapter`, not extend it. They implement `fetch(options, requestStream, cancelFuture)` and `close({force})`.

## Configuring dart:io (proxy, timeouts, client tuning)

```dart
// Native only.
import 'dart:io';

import 'package:dio/dio.dart';
import 'package:dio/io.dart';

void useProxy(Dio dio) {
  dio.httpClientAdapter = IOHttpClientAdapter(
    createHttpClient: () {
      final client = HttpClient();
      client.findProxy = (uri) => 'PROXY localhost:8888'; // must be reachable from the device
      client.idleTimeout = const Duration(seconds: 15);
      return client; // must return a client
    },
  );
}
```

`onHttpClientCreate: (client) { ... }` is the deprecated form. Use `createHttpClient: () => ...`. The web can't set a proxy.

## Certificates and pinning

Keep the platform's TLS chain and hostname validation **on**. The handshake is the only point that stops a request before any data is sent.

**Private CA:** add its certificate to the trust store at handshake time. Ship the certificate with the app or through a trusted configuration channel; don't fetch it from the server you're trying to verify.

```dart
// Native only.
import 'dart:io';

import 'package:dio/dio.dart';
import 'package:dio/io.dart';

void trustPrivateCa(Dio dio, List<int> caPemBytes) {
  dio.httpClientAdapter = IOHttpClientAdapter(
    createHttpClient: () {
      final context = SecurityContext(withTrustedRoots: true)
        ..setTrustedCertificatesBytes(caPemBytes);
      return HttpClient(context: context);
    },
  );
}
```

**`IOHttpClientAdapter(validateCertificate:)`** is an *extra* check on the leaf certificate of a connection that the handshake has already accepted. It runs **after** dio has sent the headers and body and received the response, so it **can't stop credentials or request data from reaching that peer**. A mismatch then surfaces as `DioExceptionType.badCertificate`. Use it as defence in depth alongside normal validation, never instead of it:

```dart
// Native only.
import 'package:crypto/crypto.dart';
import 'package:dio/dio.dart';
import 'package:dio/io.dart';

/// SHA-256 of the LEAF certificate's DER bytes (a certificate fingerprint, not a public-key pin).
const expectedLeafSha256 = <String>{
  'ee5ce1dfa7a53657c545c62b65802e4272878dabd65c0aadcf85783ebb0b4d5c', // current
  // add the next certificate's fingerprint before rotating
};

void checkLeafCertificate(Dio dio) {
  dio.httpClientAdapter = IOHttpClientAdapter(
    // No createHttpClient override: normal chain + hostname validation stays on.
    validateCertificate: (cert, host, port) {
      if (host != 'api.example.com') return true; // only pin the host you own
      if (cert == null) return false;
      return expectedLeafSha256.contains(sha256.convert(cert.der).toString());
    },
  );
}
```

- **Pinning that must protect request data** (e.g. against a user-installed root CA) needs a check *before* HTTP data is sent. Use platform policy, via `NativeAdapter` with Android network security config pins or iOS App Transport Security settings, or an adapter that pins during the handshake.
- **A fingerprint read from the live endpoint** (`openssl s_client ... | openssl x509 -noout -fingerprint -sha256`) isn't independent proof of trust. Get the expected value from your own certificate or key management, pin a backup, and plan rotation before the certificate expires.
- **Never install an accept-all certificate callback** (`badCertificateCallback = (_, __, ___) => true`) on a client that sends credentials, not even together with `validateCertificate`. It accepts every certificate at the handshake, so the request is sent before your check runs.

## NativeAdapter

```dart
import 'package:dio/dio.dart';
import 'package:dio/io.dart';
import 'package:native_dio_adapter/native_dio_adapter.dart';

void useNativeStack(Dio dio) {
  dio.httpClientAdapter = NativeAdapter(
    // Android devices whose Cronet providers are all disabled (e.g. emulators without
    // Google Play) would otherwise fail every request.
    createFallbackAdapter: (error, stackTrace) => IOHttpClientAdapter(),
  );
}
```

`NativeAdapter` uses `cupertino_http` on iOS/macOS and `cronet_http` on Android, and the Dart stack elsewhere.
- **The OS handles transport:** system proxy and VPN, HTTP/3, redirects and TLS policy (pin there). `IOHttpClientAdapter` settings don't apply.
- **The Android fallback is narrow:** it's chosen lazily, only for a recognised Cronet-provider initialisation failure, not for arbitrary HTTP or TLS errors.

## HTTP/2

```dart
import 'package:dio/dio.dart';
import 'package:dio_http2_adapter/dio_http2_adapter.dart';

Dio createHttp2Dio() => Dio(BaseOptions(baseUrl: 'https://api.example.com/'))
  ..httpClientAdapter = Http2Adapter(
    ConnectionManager(idleTimeout: const Duration(seconds: 15)),
  );
```

HTTP/2 lowercases all header names, so `preserveHeaderCase` has no effect.

## Web and CORS

- **The browser enforces CORS.** Non-simple requests (custom headers, JSON bodies, `PUT`/`DELETE`) trigger a preflight `OPTIONS` that the **server** must answer. A failure surfaces as `connectionError` / `unknown` with no `response`. Fix it on the server, or proxy it; client code can't disable CORS.
- **The web has no proxy or certificate APIs,** and `preserveHeaderCase` doesn't apply.
- **Cookies on cross-origin requests:** credentials default to `false`. Enable them on the adapter (below), or per request with `Options(extra: {'withCredentials': true})`. The server must allow your specific origin and credentials, and browser cookie policy still applies.

```dart
import 'package:dio/browser.dart';
import 'package:dio/dio.dart';

void sendCookiesCrossOrigin(Dio dio) {
  dio.httpClientAdapter = BrowserHttpClientAdapter(withCredentials: true);
}
```
