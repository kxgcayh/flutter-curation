// Hand-written behaviour test for the RefreshTokenInterceptor printed in
// skills/dio/references/interceptors.md (extracted to lib/interceptors__3.dart).
import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:test/test.dart';

import '../lib/interceptors__3.dart';

class FakeAdapter implements HttpClientAdapter {
  FakeAdapter(this.handle);
  final Future<ResponseBody> Function(RequestOptions o) handle;
  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<Uint8List>? s, Future<void>? c) => handle(o);
  @override
  void close({bool force = false}) {}
}

ResponseBody json(Object data, int status) => ResponseBody.fromString(jsonEncode(data), status,
    headers: {Headers.contentTypeHeader: [Headers.jsonContentType]});

void main() {
  const base = 'https://api.example.com/';
  late AuthSession session;
  late int refreshCalls;

  setUp(() {
    session = AuthSession()
      ..accessToken = 'old'
      ..refreshToken = 'r1';
    refreshCalls = 0;
  });

  Dio refreshDio() => Dio(BaseOptions(baseUrl: base))
    ..httpClientAdapter = FakeAdapter((o) async {
      refreshCalls++;
      await Future<void>.delayed(const Duration(milliseconds: 20));
      return json({'accessToken': 'new'}, 200);
    });

  Dio appDio(Dio replay) {
    final dio = Dio(BaseOptions(baseUrl: base))
      ..httpClientAdapter = FakeAdapter((o) async {
        final ok = o.headers['Authorization'] == 'Bearer new';
        return json(ok ? {'path': o.path} : {'error': 'expired'}, ok ? 200 : 401);
      });
    dio.interceptors.add(RefreshTokenInterceptor(
      apiOrigin: 'https://api.example.com',
      session: session,
      refreshDio: refreshDio(),
      replayDio: replay,
    ));
    return dio;
  }

  test('3 concurrent 401s refresh exactly once and all succeed', () async {
    final replay = Dio(BaseOptions(baseUrl: base))
      ..httpClientAdapter = FakeAdapter((o) async => json({'path': o.path, 'replayed': true}, 200));
    final dio = appDio(replay);
    final results = await Future.wait([dio.get('a'), dio.get('b'), dio.get('c')])
        .timeout(const Duration(seconds: 5));
    expect(refreshCalls, 1);
    expect(results.map((r) => r.statusCode), everyElement(200));
    expect(results.map((r) => (r.data as Map)['path']), ['a', 'b', 'c']);
  });

  test('a replay that fails again completes with an error instead of hanging', () async {
    final replay = Dio(BaseOptions(baseUrl: base))
      ..httpClientAdapter = FakeAdapter((o) async => json({'error': 'still'}, 401));
    final dio = appDio(replay);
    await expectLater(
      dio.get('a').timeout(const Duration(seconds: 5)),
      throwsA(isA<DioException>().having((e) => e.response?.statusCode, 'status', 401)),
    );
    expect(refreshCalls, 1);
  });

  test('tokens are not sent to other origins', () async {
    String? sentAuth;
    final dio = Dio()
      ..httpClientAdapter = FakeAdapter((o) async {
        sentAuth = o.headers['Authorization'] as String?;
        return json({}, 200);
      });
    dio.interceptors.add(RefreshTokenInterceptor(
        apiOrigin: 'https://api.example.com', session: session, refreshDio: refreshDio(), replayDio: Dio()));
    await dio.get('https://evil.example.org/x');
    expect(sentAuth, isNull);
  });
}
