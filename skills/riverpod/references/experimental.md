# Experimental: mutations and offline persistence

Both APIs are experimental in Riverpod 3.x and may change without a major version bump. Use them only if the project already does, or the user accepts that risk. Pin the Riverpod version, and check the current API docs before writing code.

## Mutations

Mutations track the state of a side effect (form submit, delete, purchase) so the UI can show pending, error or success states. They keep that UI state out of the provider's own state. They also keep the providers used during the operation alive, which fixes the "`onPressed` + `ref.read` + auto-dispose disposed my provider mid-request" problem.

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/experimental/mutation.dart'; // or riverpod/ or hooks_riverpod/

// Top-level, or a `static final` on the notifier. The type is the result type.
final addTodo = Mutation<Todo>();

class AddTodoButton extends ConsumerWidget {
  const AddTodoButton({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final status = ref.watch(addTodo);

    return switch (status) {
      MutationPending() => const CircularProgressIndicator(),
      MutationError(:final error) => TextButton(
          onPressed: () => _submit(ref),
          child: Text('Retry ($error)'),
        ),
      MutationSuccess(:final value) => Text('Added ${value.title}'),
      MutationIdle() => ElevatedButton(
          onPressed: () => _submit(ref),
          child: const Text('Add'),
        ),
    };
  }

  Future<void> _submit(WidgetRef ref) async {
    try {
      await addTodo.run(ref, (tsx) {
        // tsx.get keeps the provider alive for the duration of the mutation.
        final todos = tsx.get(todoListProvider.notifier);
        return todos.add('Eat a cookie'); // returns Future<Todo>
      });
    } catch (_) {
      // run() records the failure as MutationError and then rethrows.
      // The button above renders that error.
    }
  }
}
```

- **States:** `MutationIdle`, `MutationPending`, `MutationError` and `MutationSuccess` form a sealed set, so you can switch over them exhaustively.
- **Keyed instances:** `final removeTodo = Mutation<void>(); removeTodo(todo.id)` gives one instance per id. This lets list items show their own spinners.
- **Reset:** a mutation returns to idle once it completes and has no listeners, or when you call `addTodo.reset(ref)`. In Riverpod 3.3.2+, an in-flight result doesn't replace the idle state after a `reset`.
- **Container disposed mid-run:** a successful in-flight callback still returns normally, but its UI state is gone.
- **No serialization:** starting a second `run` while one is pending supersedes the displayed state, but both callbacks run. Disable the button while `MutationPending` if writes must not overlap.
- **Observers see it too:** `ProviderObserverContext.mutation` tells an observer which mutation caused an update.
- **`run` rethrows failures** after recording them as `MutationError`. Catch them (as above), or they surface as uncaught errors.
- **Still put the logic in a Notifier method.** The mutation only wraps the call.

## Offline persistence

This persists a Notifier's state to local storage and restores it on the next launch. It works with any Notifier type, with or without code generation. Riverpod ships only the interfaces. `riverpod_sqflite` provides `JsonSqFliteStorage`, or you can implement `Storage` yourself.

```sh
flutter pub add riverpod_sqflite sqflite path
```

```dart
import 'dart:convert';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/experimental/persist.dart';
import 'package:path/path.dart';
import 'package:riverpod_sqflite/riverpod_sqflite.dart';
import 'package:sqflite/sqflite.dart';

// Share a single Storage instance across providers.
final storageProvider = FutureProvider<JsonSqFliteStorage>((ref) async {
  return JsonSqFliteStorage.open(join(await getDatabasesPath(), 'riverpod.db'));
});

final todosProvider = AsyncNotifierProvider<Todos, List<Todo>>(Todos.new);

class Todos extends AsyncNotifier<List<Todo>> {
  @override
  Future<List<Todo>> build() async {
    // Call persist first. Don't await it: the network request starts right away
    // while the cached value is shown.
    persist(
      ref.watch(storageProvider.future),
      key: 'todos', // must be unique across all persisted providers
      encode: (todos) => jsonEncode(todos.map((todo) => todo.toJson()).toList()),
      decode: (raw) => (jsonDecode(raw) as List)
          .map((e) => Todo.fromJson(e as Map<String, Object?>))
          .toList(),
      options: const StorageOptions(
        // cacheTime: StorageCacheTime.unsafe_forever, // default is 2 days
        destroyKey: '1', // bump it when the serialized format changes
      ),
    );
    return ref.watch(apiProvider).fetchTodos(); // server data replaces the cached data
  }

  Future<void> add(Todo todo) async {
    final operationRef = ref;
    final previous = await future;
    if (!operationRef.mounted) return;
    state = AsyncData([...previous, todo]); // persisted automatically
  }
}
```

`Todo` needs matching `toJson()` and `Todo.fromJson()` methods (hand-written, or generated by json_serializable/Freezed).

- **Code generation:** import `package:riverpod_annotation/experimental/json_persist.dart` and annotate the notifier class with both `@riverpod` and `@JsonPersist()`. Then call `persist(ref.watch(storageProvider.future))` in `build`. The generated method supplies the default key and codec. The storage must be JSON-compatible and the state serializable.
- **Family providers** need a key that includes the argument, such as `'todos-$userId'`.
- **The default cache time is 2 days,** because persistence is designed as a cache for IO. For user preferences, use `unsafe_forever`, and delete the stored entry yourself if the provider is ever removed.
- **`destroyKey`** throws away old persisted data when the format changes. Riverpod has no real data migration.
- **`AsyncValue.isFromCache`** tells the UI that the value came from storage rather than the server.
- **During restore plus a network request,** cached data may be attached to an `AsyncLoading` value. Render it by checking `value` and `isFromCache`. Awaiting the provider's `.future` waits for a fresh result by default.
- **`persist(...).future` is a nullable `Future<void>`.** To start from the persisted value instead of fetching first, await it so the restore finishes, then inspect `state` and decide whether to fetch.
