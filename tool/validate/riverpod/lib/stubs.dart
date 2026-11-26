import 'package:flutter/material.dart';
import 'package:hooks_riverpod/hooks_riverpod.dart';

class Model {
  const Model({this.id = '1', this.name = '', this.title = '', this.done = false});
  final String id, name, title;
  final bool done;
  bool get read => done;
  Model copyWith({required bool done}) => Model(id: id, name: name, title: title, done: done);
  Model.fromJson(Map<String, Object?> json) : this(name: json['name'] as String);
  Map<String, Object?> toJson() => {'name': name};
}
typedef Todo = Model;
typedef User = Model;
typedef Item = Model;
typedef Post = Model;
typedef Product = Model;
typedef Results = Model;
typedef Result = Model;
typedef Feed = Model;
typedef Message = Model;
typedef Detail = Model;
class Config {
  Config.fromEnv();
  Config.staging();
}
enum Filter { all, done }
class AuthException implements Exception {}
class NotFoundException implements Exception {}
class Cancelled implements Exception { const Cancelled(); }
class Api {
  Future<User> fetchUser() async => const User();
  Future<User> user(String id) async => User(id: id);
  Future<Product> product(String id) async => Product(id: id);
  Future<List<Post>> posts(String id, {int page = 1}) async => [];
  Future<Post> post(String id) async => Post(id: id);
  Future<void> publish(String id) async {}
  Future<void> delete(String id) async {}
  Future<void> rename(String name) async {}
  Future<Todo> add(String title) async => Todo(title: title);
  Future<List<Todo>> fetchTodos() async => [];
  Future<Results> search() async => const Results();
  Future<Feed> feed() async => const Feed();
  Future<Config> config() async => Config.fromEnv();
}
class FakeApi extends Api {}
final apiProvider = Provider((ref) => Api());
class CartRepo {
  Future<List<Item>> load() async => [];
  Future<void> add(Item item) async {}
}
class FakeCartRepo extends CartRepo {}
final cartRepoProvider = Provider((ref) => CartRepo());
const item = Item();
const fakeUser = User(name: 'Ada');
final ids = ['1'];
Future<Item> fetchItem(String id) async => Item(id: id);
List<Result> parseResults(String body) => [];
void reportError(Object error, StackTrace stackTrace) {}
class ChatSocket {
  ChatSocket.connect(String id);
  Stream<Message> get messages => const Stream.empty();
  void close() {}
}
class MyApp extends StatelessWidget {
  const MyApp({super.key});
  @override
  Widget build(BuildContext context) => const SizedBox();
}
class Search extends ConsumerStatefulWidget {
  const Search({super.key});
  @override
  ConsumerState<Search> createState() => throw UnimplementedError();
}
class ItemTile extends MyApp { const ItemTile({super.key}); }
class ProfilePage extends MyApp { const ProfilePage({super.key}); }
class SplashScreen extends MyApp { const SplashScreen({super.key}); }
class ErrorScreen extends MyApp { const ErrorScreen(Object error, {super.key}); }
class OrderList extends MyApp { const OrderList(List<Item> items, {super.key}); }
class ErrorView extends MyApp { const ErrorView(Object error, [StackTrace stack = StackTrace.empty]); }
class DetailEditor extends MyApp { const DetailEditor({super.key, required Detail initial}); }
final ordersProvider = FutureProvider<List<Item>>((ref) async => []);
final resultsProvider = FutureProvider<Results>((ref) async => const Results());
final queryProvider = Provider((ref) => '');
final remoteConfigProvider = FutureProvider((ref) async => Config.fromEnv());
final checkoutProvider = FutureProvider<void>((ref) async {});
final orderProvider = FutureProvider<Item>((ref) async => const Item());
final inboxProvider = Provider<List<Message>>((ref) => []);
final detailProvider = FutureProvider.family<Detail, String>((ref, id) async => Detail(id: id));
final configProvider = Provider((ref) => Config.fromEnv());
final userByIdProvider = Provider.family<User, String>((ref, id) => User(id: id));
class Counter extends Notifier<int> {
  @override
  int build() => 0;
}
final counterProvider = NotifierProvider<Counter, int>(Counter.new);
class TodoList extends Notifier<List<Todo>> {
  @override
  List<Todo> build() => [];
  Future<Todo> add(String title) async => Todo(title: title);
}
class FakeTodoList extends TodoList {}
final todoListProvider = NotifierProvider<TodoList, List<Todo>>(TodoList.new);
class Profile extends AsyncNotifier<User> {
  @override
  Future<User> build() async => const User();
  Future<void> rename(String name) async {}
}
final profileProvider = AsyncNotifierProvider<Profile, User>(Profile.new);
final storageProvider = FutureProvider<Object>((ref) async => Object());
