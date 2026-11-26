// Minimal app-specific symbols the skill's snippets refer to.
import 'package:dio/dio.dart';

final dio = Dio();

class Session {
  String? accessToken;
}

final session = Session();
