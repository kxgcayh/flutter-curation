// Minimal app-specific symbols the skill's snippets refer to.
import 'dart:async';

import 'package:flutter/widgets.dart';

class Message {}

class Notice {
  final String text = '';
}

class User {
  final String name = '';
}

class Api {
  Future<String> fetch(String id) async => id;
  Future<User> fetchUser(String id) async => User();
}

class Chat {
  Stream<List<Message>> messages(String roomId) => const Stream.empty();
}

class NumberFormatter {
  NumberFormatter(this.locale);
  final String locale;
}

final api = Api();
final chat = Chat();
const userId = 'u1';
const id = 'u1';
const roomId = 'r1';
const locale = 'en';
const serverName = 'server';
const page = 0;
const color = Color(0xFF000000);
final stream = Stream<int>.empty();
final notices = Stream<Notice>.empty();
final form = ValueNotifier<String>('');
late final AnimationController controller;

Future<String> fetchUserName(String userId) async => userId;
Future<List<String>> search(String query) async => [query];
void onEvent(int event) {}
void submit(String value) {}
void tick() {}
void refreshData() {}
const recordId = 'r1';
