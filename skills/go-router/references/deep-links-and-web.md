# Deep links, web URLs and state restoration

go_router shows whatever the incoming URL matches, so a deep link needs only the platform setup below. Redirects and `onEnter` apply to deep links too.

## Flutter's built-in handler

Since Flutter 3.27, Flutter's own deep-link handler is **on by default** on Android and iOS, and it hands links to go_router.
- **Below Flutter 3.27,** opt in yourself:
  - Android: `<meta-data android:name="flutter_deeplinking_enabled" android:value="true" />` inside `<activity>`
  - iOS: set `FlutterDeepLinkingEnabled` to `YES` in `Info.plist`
- **If another plugin handles links** (`app_links`, `uni_links`, a vendor SDK), turn the built-in handler **off**: `android:value="false"` / `FlutterDeepLinkingEnabled` = `NO`. Then pass the links to `router.go(...)` yourself, so links aren't handled twice. Before converting a link to an internal location, validate its scheme, host and path. Handle the initial link and later events once each.

## Android App Links

Inside the `.MainActivity` `<activity>` in `android/app/src/main/AndroidManifest.xml`:

```xml
<intent-filter android:autoVerify="true">
    <action android:name="android.intent.action.VIEW" />
    <category android:name="android.intent.category.DEFAULT" />
    <category android:name="android.intent.category.BROWSABLE" />
    <data android:scheme="http" android:host="example.com" />
    <data android:scheme="https" />
</intent-filter>
```

Host `https://example.com/.well-known/assetlinks.json`:

```json
[{
  "relation": ["delegate_permission/common.handle_all_urls"],
  "target": {
    "namespace": "android_app",
    "package_name": "com.example.app",
    "sha256_cert_fingerprints": ["<SHA-256 of the signing certificate>"]
  }
}]
```

Use the fingerprint of the certificate that signs the installed build, and the installed application id (per flavor). For Play-distributed apps, that's the Play app-signing certificate, not your upload key.

## iOS universal links

1. **Turn on the capability:** in Xcode, open Runner → Signing & Capabilities and add **Associated Domains** with `applinks:example.com`. This writes `ios/Runner/Runner.entitlements`:

```xml
<key>com.apple.developer.associated-domains</key>
<array>
  <string>applinks:example.com</string>
</array>
```

2. **Host the association file** at `https://example.com/.well-known/apple-app-site-association`, with no `.json` extension, served as JSON:

```json
{
  "applinks": {
    "details": [
      {
        "appIDs": ["TEAMID.com.example.app"],
        "components": [{ "/": "/*" }]
      }
    ]
  }
}
```

This is the current format. Older guides add `"apps": []` and `"paths": [...]`; don't mix those in. Use your real team-id prefix and bundle id, and list only the paths the app should open in `components` (`/*` opens every path).

## Testing deep links

```sh
# Android: opens the app directly (doesn't verify the hosted assetlinks.json)
adb shell 'am start -a android.intent.action.VIEW -c android.intent.category.BROWSABLE -d "https://example.com/items/42"' com.example.app

# iOS simulator
xcrun simctl openurl booted https://example.com/items/42
```

To test the whole chain, including the hosted files, tap the link in a browser or messaging app on a device. Flutter DevTools has a **Deep links** tool that checks the Android setup.

## Web URLs

The web uses the **hash** strategy by default (`/#/items/42`). For clean URLs (`/items/42`), use the path strategy:

```yaml
# pubspec.yaml
dependencies:
  flutter_web_plugins:
    sdk: flutter
```

```dart
import 'package:flutter/widgets.dart';
import 'package:flutter_web_plugins/url_strategy.dart';

void main() {
  usePathUrlStrategy(); // before runApp
  runApp(const App());
}
```

- **With the path strategy, configure the web server** to rewrite app routes to `index.html`, while still serving assets and API routes as they are. Otherwise a refresh on `/items/42` returns 404.
- **Apps hosted under a sub-path** need `<base href="/subpath/">` in `web/index.html`, with both a leading and a trailing slash.
- **The snippet above** is a sketch of your own `main`: use your app's imports and root widget.

## State restoration

To restore the location and stacks after the OS kills the app:
- **App and router:** set `restorationScopeId` on `MaterialApp.router` and on `GoRouter`.
- **Routes:** a `GoRoute` `pageBuilder` must return a `Page` with a `restorationId`.
- **Shells:** for a `ShellRoute` or `StatefulShellRoute`, set the shell's `restorationScopeId` and use a shell `pageBuilder` whose `Page` has a `restorationId`. Give each `StatefulShellBranch` its own `restorationScopeId`.
- **`extra`:** JSON-compatible values use the default serializer; supply an `extraCodec` for custom objects that must round-trip.

Never make `extra` the only input of a deep-linkable route.
