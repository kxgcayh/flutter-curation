# Controller and lifecycle hooks

Controller hooks own creation and disposal. Where a hook has a `keys:` parameter, changing a key disposes the old object and creates a new one. Which arguments are read only at creation and which update live depends on the hook. Initial text, initial page and bounds are creation-only. The exceptions are listed per hook below.

## Text and focus

```dart
class LoginForm extends HookWidget {
  const LoginForm({this.initialEmail = '', super.key});
  final String initialEmail;

  @override
  Widget build(BuildContext context) {
    final email = useTextEditingController(text: initialEmail);
    final password = useTextEditingController();
    final passwordFocus = useFocusNode();

    return Column(children: [
      TextField(
        controller: email,
        textInputAction: TextInputAction.next,
        onSubmitted: (_) => passwordFocus.requestFocus(),
      ),
      TextField(controller: password, focusNode: passwordFocus, obscureText: true),
    ]);
  }
}
```

- **`text:` is used once.** To load a new record, key the controller by the record's id, so the draft starts fresh from the model when the record changes:

```dart
final controller = useTextEditingController(text: serverName, keys: [recordId]);
```

  Local edits survive refreshes of the same record. For an explicit reset, assign `controller.text` in the reset button's callback. Don't assign it from `useEffect` on every model change: that overwrites what the user is typing, and notifies listeners during build. If you need a live sync, update after the frame (`addPostFrameCallback`) and decide what happens to unsaved edits. To reset a `useState` draft the same way (`useState` has no `keys`), key a child widget by the record id.

- **From a full value:** `useTextEditingController.fromValue(TextEditingValue(text: 'hi'))` sets selection and composing as well.
- **Pass `keys: [id]`** to get a fresh controller when the edited entity changes.
- **Other focus hooks:** `useFocusNode` takes the usual `FocusNode` options (`debugLabel`, `onKeyEvent`, `skipTraversal`, `canRequestFocus`, ...) and updates them on later builds. `useFocusScopeNode` is the scope equivalent.

## Scrolling and paging

| Hook | Creates |
| --- | --- |
| `useScrollController(initialScrollOffset:, keepScrollOffset:, onAttach:, onDetach:, keys:)` | `ScrollController` |
| `usePageController(initialPage:, keepPage:, viewportFraction:, onAttach:, onDetach:, keys:)` | `PageController` |
| `useFixedExtentScrollController(initialItem:, keys:)` | `FixedExtentScrollController` |
| `useDraggableScrollableController()` | `DraggableScrollableController` |
| `useTransformationController(initialValue:)` | `TransformationController` (for `InteractiveViewer`) |
| `useTreeSliverController()` | `TreeSliverController` |

```dart
class Feed extends HookWidget {
  const Feed({required this.items, super.key});
  final List<String> items;

  @override
  Widget build(BuildContext context) {
    final scroll = useScrollController();
    useOnListenableChange(scroll, () {
      if (scroll.position.extentAfter < 300) debugPrint('load more');
    });
    return ListView(controller: scroll, children: [for (final i in items) Text(i)]);
  }
}
```

## Animation

```dart
class FadeIn extends HookWidget {
  const FadeIn({required this.child, super.key});
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final controller = useAnimationController(duration: const Duration(milliseconds: 300));
    useEffect(() {
      controller.forward();
      return null;
    }, const []);
    final opacity = useAnimation(controller); // rebuilds on every tick
    return Opacity(opacity: opacity, child: child);
  }
}
```

- **`vsync` is optional.** Without it, the hook uses its own `useSingleTickerProvider`, which respects `TickerMode`. You can't switch between an implicit and an explicit `vsync` later.
- **What updates:** a new `duration` (and `reverseDuration`) updates the controller, and replacing one explicit `vsync` with another resyncs it. `initialValue`, `lowerBound`, `upperBound` and `debugLabel` are read only on the first build. Switching between implicit and explicit `vsync` changes the hook order and isn't supported.
- **Prefer `AnimatedBuilder` or a transition widget** (`FadeTransition`) to `useAnimation` when only a small subtree depends on the value, so the whole widget doesn't rebuild every frame.
- **Several controllers in one widget:** call `useAnimationController` several times, since each gets its own ticker. Use `useSingleTickerProvider()` when you construct a controller yourself, e.g. for a third-party controller that needs a `TickerProvider`.

## Other object hooks

| Hook | Notes |
| --- | --- |
| `useExpansibleController()` | for `ExpansionTile` / `Expansible` (0.21.3+). On 0.21.2, use `useExpansionTileController`, which is deprecated from 0.21.3 |
| `useOverlayPortalController()` | `OverlayPortalController` |
| `useSnapshotController(allowSnapshotting:)` | `SnapshotController` (0.21.3+). `allowSnapshotting` updates on later builds |
| `useWidgetStatesController(values:)` | `WidgetStatesController` (`MaterialStatesController` replacement) |
| `useAutomaticKeepAlive(wantKeepAlive: true)` | keeps the widget alive, like `AutomaticKeepAliveClientMixin`. Needs an ancestor that handles keep-alive notifications, such as a lazy list with automatic keep-alives enabled |

## App lifecycle and platform

```dart
// Starts with WidgetsBinding.instance.lifecycleState (nullable); rebuilds on change.
final lifecycle = useAppLifecycleState();
// previous is nullable; neither callback rebuilds the widget.
useOnAppLifecycleStateChange((previous, current) {
  if (current == AppLifecycleState.resumed) refreshData();
});
final brightness = usePlatformBrightness();
useOnPlatformBrightnessChange((previous, current) => debugPrint('$current'));
```

## Material and Cupertino controller hooks

| Hook | flutter_hooks ≤ 0.21.3+1 | flutter_hooks 0.21.4+ (Flutter 3.47+) |
| --- | --- | --- |
| `useTabController(initialLength:, initialIndex:, animationDuration:, vsync:, keys:)` | in `flutter_hooks` | deprecated; use `material_hooks` |
| `useSearchController()` | in `flutter_hooks` | deprecated; use `material_hooks` |
| `useCarouselController(initialItem:)` | in `flutter_hooks` | deprecated; use `material_hooks` |
| `useCupertinoTabController(initialIndex:)` | in `flutter_hooks` (0.21.3+) | deprecated; use `cupertino_hooks` |

According to the flutter_hooks 0.21.4 changelog, Flutter deprecated `package:flutter/material.dart` and `package:flutter/cupertino.dart` in favour of the `material_ui` and `cupertino_ui` packages, so these hooks moved too. On Flutter 3.47+, add `material_hooks` or `cupertino_hooks` (0.1.0: Flutter ≥ 3.47.0, Dart ^3.13.0, flutter_hooks 0.21.4 exactly) and hide the deprecated copies. Material:

```dart
import 'package:material_ui/material_ui.dart';
import 'package:flutter_hooks/flutter_hooks.dart'
    hide useCarouselController, useSearchController, useTabController;
import 'package:material_hooks/material_hooks.dart';
```

Cupertino:

```dart
import 'package:cupertino_ui/cupertino_ui.dart';
import 'package:flutter_hooks/flutter_hooks.dart' hide useCupertinoTabController;
import 'package:cupertino_hooks/cupertino_hooks.dart';
```

Use each controller with the matching UI library's widgets. The hook names and named arguments are unchanged. On older Flutter, keep using the `flutter_hooks` versions.

The example below uses the **legacy** `flutter_hooks` `useTabController` (flutter_hooks ≤ 0.21.3+1). With the imports above, the same code uses the `material_hooks` version:

```dart
class Tabs extends HookWidget {
  const Tabs({super.key});

  @override
  Widget build(BuildContext context) {
    final tabs = useTabController(initialLength: 2); // vsync is provided by the hook
    return Column(children: [
      TabBar(controller: tabs, tabs: const [Tab(text: 'A'), Tab(text: 'B')]),
      Expanded(
        child: TabBarView(controller: tabs, children: const [Text('A'), Text('B')]),
      ),
    ]);
  }
}
```

Changing `initialLength` doesn't resize an existing `TabController`. Pass `keys: [length]` so a new one is created.
