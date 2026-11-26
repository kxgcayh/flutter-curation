// Minimal app-specific symbols the skill's snippets refer to.
import 'package:flutter/widgets.dart';

class _Stub extends StatelessWidget {
  const _Stub();
  @override
  Widget build(BuildContext context) => const SizedBox();
}

class HomeScreen extends _Stub { const HomeScreen(); }
class SettingsScreen extends _Stub { const SettingsScreen(); }
class DetailsScreen extends _Stub { const DetailsScreen(); }
class TabScreen extends _Stub { const TabScreen(); }
class BetaScreen extends _Stub { const BetaScreen(); }
class LoginScreen extends _Stub { const LoginScreen(); }
class AccountScreen extends _Stub { const AccountScreen(); }
class AdminScreen extends _Stub { const AdminScreen(); }
class PlayerScreen extends _Stub { const PlayerScreen(); }
class InboxScreen extends _Stub { const InboxScreen(); }
class SentScreen extends _Stub { const SentScreen(); }
class EditScreen extends _Stub { const EditScreen(); }
class App extends _Stub { const App(); }
class ItemScreen extends _Stub { const ItemScreen({required this.id, this.initial}); final String id; final Item? initial; }
class UserScreen extends _Stub { const UserScreen({required this.userId}); final String userId; }
class PostsScreen extends _Stub { const PostsScreen({required this.userId, required this.sort}); final String userId; final String sort; }
class OrderScreen extends _Stub { const OrderScreen({required this.id}); final int id; }
class NotFoundScreen extends _Stub { const NotFoundScreen({this.message}); final String? message; }
class SongScreen extends _Stub { const SongScreen({required this.id, required this.autoplay}); final int id; final bool autoplay; }

class Item {
  const Item(this.id);
  final String id;
}

bool isSignedIn() => false;
bool currentUserIsAdmin() => false;
