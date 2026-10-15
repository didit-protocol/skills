---
name: didit-sdk-integration
description: >
  Integrate the Didit client SDKs into web and mobile apps. Use when the user wants to launch
  a Didit verification session in a web page (redirect, iframe, or the JavaScript SDK
  @didit-protocol/sdk-web), an iOS app (DiditSDK, Swift), an Android app (me.didit:didit-sdk,
  Kotlin), a React Native or Expo app (@didit-protocol/sdk-react-native) or a Flutter app
  (didit_sdk); create the session on a backend and hand the url or session_token to the
  client; handle SDK results, callbacks and errors; submit monitored transactions from the
  device with a transaction SDK token (submitTransaction, wallet ownership, step-up
  verification); or send monitoring events from a device with a monitoring token. Keeps the
  API key on the backend. Also use for any combination of Identity verification,
  Transaction monitoring and end-user Authentication, checking release availability first.
version: 1.1.0
metadata:
  openclaw:
    requires:
      env: []
    primaryEnv: DIDIT_API_KEY
    emoji: "🧩"
    homepage: https://docs.didit.me
---

# Didit SDK Integration (Web, iOS, Android, React Native, Flutter)

## Overview

Choose Identity verification, Transaction monitoring, Authentication, or any combination. For verification and monitoring, your backend uses the API key to create what the client needs; the client receives a credential for that purpose. End-user Authentication uses its own session credentials and requires an enabled application. Start with the [three-product prompt](#three-product-integration-prompt).

| Product | Backend preparation | Client receives | Client integration |
|---|---|---|---|
| Verification sessions | `POST /v3/session/` | `url` (web) or `session_token` (iOS, Android, React Native, Flutter) | `startVerification` |
| Transactions | `POST /v3/transactions/sdk-token/` | `sdk_token` | `submitTransaction`, plus `getTransaction` on mobile |
| Events | `POST /v3/events/sdk-token/` | `monitoring_token` | None: plain HTTPS to `POST /v1/events/` |
| End-user Authentication (early access) | Confirm the enabled application's Authentication runtime | End-user access/refresh tokens | Hosted PKCE flow; dedicated SDKs are release-dependent |

**Rules:**
- Never put the API key in a browser, app or WebView. It stays on your backend.
- SDK results are UX hints. Grant access only after your backend confirms the outcome with a webhook or `GET /v3/session/{session_id}/decision/` (sessions) or `GET /v3/transactions/{uuid}/` (transactions).
- Colors, logo and intro screens come from the console White Label settings, not from SDK options.

**Verification/transaction versions documented here:** Web SDK 0.4.0, iOS 4.9.1, Android 4.9.1, React Native 4.9.1, Flutter 4.9.1. These versions do not establish availability of Authentication or `@didit-protocol/signals`.

**Pricing:** The SDKs have no list price of their own. A session bills the features of its workflow (only features that finish); a transaction submitted from a device bills like a server-side one ($0.02 Transaction Screening). These are the list prices until 1 November 2026, when Didit pricing changes and the 500 free checks a month become $10 of free credit a month. Check [didit.me/pricing](https://didit.me/pricing) for current prices.

**Docs:** https://docs.didit.me/integration/sdks · Web: https://docs.didit.me/integration/web-sdks/javascript-sdk · Native: https://docs.didit.me/integration/native-sdks/overview · Transactions from the device: https://docs.didit.me/transaction-monitoring/sdk-transaction-submission · Events from the device: https://docs.didit.me/transaction-monitoring/sdk-event-submission

---

## Backend API credentials

The verification and monitoring backend requests below need `DIDIT_API_KEY`, sent in the `x-api-key` header. Use your application's API key from the [Didit Business Console](https://business.didit.me) under **Developers > API keys**, or create an account and key programmatically (see Getting Started). Named keys with custom access need **Sessions** write to create sessions (a key without it gets `url` and `session_token` back as `null`) and **Transactions** write to mint transaction or monitoring tokens; a key limited to some workflows can only create sessions for those workflows and cannot mint tokens.

The device-facing `/v1/` endpoints never take the API key: they take `X-Transaction-Token` or `X-Monitoring-Token`.

Authentication-only integrations do not need this API key or a verification workflow. An end-user Bearer token is separate from a console token, verification `session_token`, transaction token and monitoring token. A publishable key identifies an application; it does not authorize server operations.

## Getting Started (No Account Yet?)

This provisions a developer account for verification/monitoring, not an end user's sign-up. Reuse an existing application when available. If you need a Didit API key, create one in 2 API calls:

1. **Register:** `POST https://apx.didit.me/auth/v2/programmatic/register/` with `{"email": "you@yourdomain.com", "password": "MyStr0ng!Pass"}`
2. **Check email** for a 6-character verification code
3. **Verify:** `POST https://apx.didit.me/auth/v2/programmatic/verify-email/` with `{"email": "you@yourdomain.com", "code": "A3K9F2"}`. The key is in the response at `application.api_key`.

**To add credits:** `GET /v3/billing/balance/` to check, `POST /v3/billing/top-up/` with `{"amount_in_dollars": 50}` for a Stripe checkout link.

See the **didit-verification-management** skill for full platform management (workflows, sessions, users, billing).

---

## Three-product integration prompt

Copy the prompt below and fill in the application context. It follows the [canonical integration prompt](https://docs.didit.me/integration/integration-prompt), with the audited platform examples in this skill. Authentication SDKs, JWT/JWKS, automatic auth events and Authentication step-ups remain release-dependent; selecting them does not establish readiness.

```text
Integrate only the Didit products I select into my application.

Application context:
- Stack: [framework and language]
- Surface: [web, iOS, Android, React Native, Flutter, or backend-only]
- Products: [Identity verification, Transaction monitoring, Authentication]
- Didit application/environment: [existing application or setup needed]
- Person reference: [stable server-owned identifier used as vendor_data]
- Use case and database: [describe]

Support each selection independently:
| Selection | Build |
|---|---|
| Identity verification | Verification sessions and backend decisions |
| Transaction monitoring | Transactions and selected application events |
| Authentication | End-user sign-up, login, session validation and logout |
| Identity verification + Transaction monitoring | Both with one person reference |
| Identity verification + Authentication | Sign-in and policy-driven verification |
| Transaction monitoring + Authentication | Bind monitoring to the signed-in person |
| Identity verification + Transaction monitoring + Authentication | All three, separate decisions |

Inspect my installed/published SDK versions, their exports, and the application's
enabled capabilities before writing adapters. Authentication SDKs (@didit-protocol/auth*,
DiditAuth on native platforms, didit_auth), @didit-protocol/signals, JWT/JWKS,
automatic auth events and Authentication step-ups are release-dependent. Keep an
unavailable adapter disabled, report the missing capability and finish independently
available products. Never invent a package version, SDK method, issuer or successful flow.

Use the same Didit application/environment across products, with sandbox and live
kept separate. Resolve vendor_data from my authenticated user on the server, never
from a client-selected user ID. For an enabled current Authentication runtime, map
its validated sub to my stable vendor_data on the server. The upcoming external_id
mapping and vendor_data claim are release-dependent; do not send undocumented fields
to hosted authorization or link people by unverified email.

Keep credentials separate:
- x-api-key stays on the backend for verification/monitoring.
- Verification url/session_token goes only to the user's verification client.
- sdk_token uses X-Transaction-Token for device transactions.
- monitoring_token uses X-Monitoring-Token for device events.
- End-user Bearer access/refresh tokens belong to Authentication, not console login.
- A publishable key identifies the application and is not server authorization.
Never log tokens, callback codes, secrets or credential-bearing verification URLs.

Identity verification, only if selected:
Reuse or create a workflow. Create POST /v3/session/ on my authenticated backend
with the server-owned vendor_data. Send the returned url to the web SDK/redirect,
or session_token to a native SDK. Use the returned URL as-is. SDK callbacks and
redirect status are UI hints: verify the signed webhook or fetch
GET /v3/session/{session_id}/decision/ on the backend, check ownership, and act on
the actual decision. Sign-in success alone never approves identity verification.

Transaction monitoring, only if selected:
No verification workflow is needed just to submit transactions. Mint
POST /v3/transactions/sdk-token/ on the backend for the user's vendor_data and
return sdk_token to submitTransaction. Use the platform's actual payload schema:
web category/details differ from mobile type/info and the REST wire schema.
Preserve transaction IDs and reconcile an uncertain submission before resending;
a repeated transaction_id is rejected, not an idempotent success. For pending
verification_session actions, open the supported verification flow if selected,
or hold the transaction for supported continuation. Never treat SDK completion
or authentication as payment authorization: read the backend transaction result.

For application-owned events, enable event monitoring and mint
POST /v3/events/sdk-token/ with narrow categories and limits. Read monitoring_token;
send it as X-Monitoring-Token to POST /v1/events/ or POST /v1/events/batch/.
Use the documented event envelope and preserve event_id and occurred_at on retries.
Use HTTPS while a signals SDK is unavailable. Do not duplicate automatically
delivered Didit Authentication events with customer-submitted login events.

Authentication, only if selected and enabled:
Read https://docs.didit.me/authentication/overview and the matching quickstart.
Developer account registration is not end-user sign-up. Confirm the application's
runtime URL and exact registered redirects/origins. The documented early-access
hosted sign-in/ flow uses random state and S256 PKCE, handles configured sign-up,
login, reset and MFA, and returns a code. Check callback state, then exchange the
code at token/ with the original verifier and redirect URI. Validate the resulting
opaque access token via GET session/; do not decode it as a JWT or invent JWKS.
Serialize refreshes through token/ and replace both tokens together: replay of a
consumed refresh token revokes the session. Do not blindly retry uncertain refreshes.
DELETE session/ revokes logout; clear local user state and report revocation failures.
Use secure HttpOnly cookies with CSRF protection for server sessions, and protected
native token storage. Authentication-only must not create verification workflows
or mint transaction/monitoring tokens. Never fabricate a step-up or event subscription.
Read https://docs.didit.me/authentication/tokens-and-jwks and
https://docs.didit.me/authentication/events-and-webhooks for the release gates.
When JWTs become available, use a trusted configured issuer/JWKS, validate signature,
algorithm, issuer, audience and time claims, and use a live session check when immediate
revocation matters. An ID token is not an API access token.

Test the selected products alone and together using one server-resolved vendor_data.
Cover cross-user/application rejection, callback state/replay, expiry, refresh races,
logout, backend verification decisions, pending transaction actions, webhook signature
rejection and duplicate delivery as applicable. Respect Retry-After; distinguish invalid
input from credential/capability errors. Report actual results and missing live/release
checks. Disabled or simulated integrations must not be reported as production-ready.
```

---

## Choose a Verification Integration

| Option | Use when | Client input | How the client learns the outcome |
|---|---|---|---|
| Redirect | Simplest web flow; cross-device | `url` | Your `callback` URL gets `?verificationSessionId=...&status=Approved\|Declined\|In Review` |
| Iframe (no SDK) | Embed in a page without npm | `url` | `postMessage` events from `https://verify.didit.me` |
| Web SDK | Web apps (any framework or vanilla JS), modal or inline | `url` | `onComplete` callback |
| iOS SDK | Native iOS (SwiftUI) | `session_token` | `.diditVerification` view modifier |
| Android SDK | Native Android (Kotlin, Jetpack Compose) | `session_token` | `onResult` callback |
| React Native SDK | React Native 0.76+ (New Architecture), Expo development builds | `session_token` | `Promise<VerificationResult>` |
| Flutter SDK | Flutter 3.3+ | `session_token` | `Future<VerificationResult>` |
| WebView | Only on a platform with no native SDK | `url` | Intercept navigation to your `callback` URL |

Native SDKs (iOS, Android, React Native, Flutter) add NFC chip reading and native camera capture; always prefer them to a WebView in a mobile app.

---

## Verification Sessions

### Step 1: Create the session on your backend

```
POST https://verification.didit.me/v3/session/
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `workflow_id` | uuid | **Yes** | Workflow to run (from the console **Workflows** page) |
| `vendor_data` | string | No | Your user id. Links sessions to one user and is the subject for transactions and events |
| `callback` | string | No | Redirect target after the flow. Didit appends `verificationSessionId` and `status`. Custom schemes (`myapp://`) work for mobile |
| `callback_method` | string | No | `initiator` (default), `completer` or `both`: which device follows the callback in a cross-device flow. Use `both` if callbacks are unreliable |
| `language` | string | No | ISO 639-1 UI language; the `url` then contains a language segment (`/es/session/...`) |
| `metadata` | JSON | No | Echoed back in responses and webhooks, never shown to the user |
| `contact_details`, `expected_details`, `portrait_image`, `sandbox_scenario` | object / string | No | See **didit-verification-management** |

**Python (backend):**

```python
import os
import requests

def create_didit_session(user_id: str) -> dict:
    response = requests.post(
        "https://verification.didit.me/v3/session/",
        headers={"x-api-key": os.environ["DIDIT_API_KEY"], "Content-Type": "application/json"},
        json={
            "workflow_id": os.environ["DIDIT_WORKFLOW_ID"],
            "vendor_data": user_id,
            "callback": "https://yourapp.example.com/verification-done",
            "callback_method": "both",
        },
        timeout=30,
    )
    response.raise_for_status()
    session = response.json()
    # Return only what the client needs: url for web, session_token for native SDKs.
    return {"session_id": session["session_id"], "url": session["url"], "session_token": session["session_token"]}
```

**TypeScript (Node backend):**

```typescript
const response = await fetch("https://verification.didit.me/v3/session/", {
  method: "POST",
  headers: { "x-api-key": process.env.DIDIT_API_KEY!, "Content-Type": "application/json" },
  body: JSON.stringify({ workflow_id: process.env.DIDIT_WORKFLOW_ID, vendor_data: userId }),
});
if (!response.ok) throw new Error(`Didit ${response.status}: ${await response.text()}`);
const { session_id, url, session_token } = await response.json();
```

**Response (201):**

```json
{
  "session_id": "11111111-2222-3333-4444-555555555555",
  "session_number": 43762,
  "session_token": "3FaJ9wLqX2Mz",
  "url": "https://verify.didit.me/session/3FaJ9wLqX2Mz",
  "vendor_data": "user-42",
  "metadata": null,
  "status": "Not Started",
  "workflow_id": "11111111-2222-3333-4444-555555555555",
  "workflow_version": 3,
  "callback": "https://yourapp.example.com/verification-done"
}
```

- Use `url` as is; never build it from `session_token` (white-label domains and the language segment change it).
- If an unfinished session already exists for the same `vendor_data` on the workflow's latest published version, that session is returned instead of a new one.
- `session_token` lets whoever holds it complete the verification as the user: send it only to that user's client and do not log it.

### Step 2: Open the session on the client

#### Redirect

```javascript
window.location.href = session.url;

// On your callback page: untrusted UI hints only
const params = new URLSearchParams(window.location.search);
const sessionId = params.get("verificationSessionId");
const status = params.get("status"); // "Approved" | "Declined" | "In Review"
```

#### Iframe (no SDK)

```html
<iframe src="SESSION_URL" style="width: 100%; height: 700px; border: none;"
        allow="camera; microphone; fullscreen; autoplay; encrypted-media"></iframe>
<script>
  window.addEventListener("message", (event) => {
    if (event.origin !== "https://verify.didit.me") return; // or your white-label domain
    const { type, data } = event.data || {};
    if (type === "didit:completed") {
      // data.sessionId, data.status: confirm on your backend before acting
    }
  });
</script>
```

- The `allow` attribute is mandatory: without it the camera never starts.
- A reverse proxy must not strip the `Permissions-Policy` header; camera and microphone must be allowed for your origin.
- With a Content Security Policy add `frame-src https://verify.didit.me;`.
- Messages are `{ type: "didit:<event>", data: {...}, timestamp }`; read the payload from `event.data.data`.

#### Web SDK (`@didit-protocol/sdk-web` 0.4.0)

```bash
npm install @didit-protocol/sdk-web
# or a script tag: https://unpkg.com/@didit-protocol/sdk-web/dist/didit-sdk.umd.min.js (global DiditSDK)
```

```typescript
import { DiditSdk } from "@didit-protocol/sdk-web";

DiditSdk.shared.onComplete = (result) => {
  // result.type: "completed" | "cancelled" | "failed"
  if (result.type === "completed") notifyBackend(result.session?.sessionId);
  if (result.type === "failed") console.error(result.error?.type, result.error?.message);
};

await DiditSdk.shared.startVerification({
  url: session.url, // from your backend
  configuration: { closeModalOnComplete: true },
  // inline instead of a modal: { embedded: true, embeddedContainerId: "didit-container" }
});
```

- Singleton `DiditSdk.shared`. `startVerification({ url, configuration? }): Promise<void>`; the outcome arrives in `onComplete`. Also `onStateChange(state, error?)` (`idle`, `loading`, `ready`, `error`) and `onEvent(event)` for step events (`didit:ready`, `didit:started`, `didit:step_started`, `didit:step_completed`, `didit:step_changed`, `didit:media_started`, `didit:media_captured`, `didit:document_selected`, `didit:verification_submitted`, `didit:code_sent`, `didit:code_verified`, `didit:status_updated`, `didit:completed`, `didit:cancelled`, `didit:error`, `didit:close_request`).
- `close()` closes everything on screen; `destroy()` tears the instance down. Properties: `state`, `configuration`, `isPresented`, `errorMessage`.
- There is no language option: the language comes from the session `url` (set `language` when creating the session).
- Embedded mode fills the host element, so give it a resolved height. The SDK iframe already sets the camera permissions.

#### iOS (`DiditSDK` 4.9.1, Swift)

Install with Swift Package Manager (`https://github.com/didit-protocol/sdk-ios.git`, from `4.9.1`) or CocoaPods (the podspec is not on Trunk). Pick exactly one variant:

| Variant | SPM product | CocoaPods subspec | NFC | Auto-capture | Minimum iOS |
|---|---|---|---|---|---|
| All (default) | `DiditSDK` | `DiditSDK/All` | Yes | Yes | 15.0 |
| NFC | `DiditSDKNFC` | `DiditSDK/NFC` | Yes | No | 15.0 |
| AutoDetection | `DiditSDKAutoDetection` | `DiditSDK/AutoDetection` | No | Yes | 13.0 |
| Core | `DiditSDKCore` | `DiditSDK/Core` | No | No | 13.0 |

```ruby
podspec_url = 'https://raw.githubusercontent.com/didit-protocol/sdk-ios/4.9.1/DiditSDK.podspec'
platform :ios, '15.0'
pod 'DiditSDK/All', :podspec => podspec_url
```

SPM does not enforce the iOS 15 floor: set the deployment target to 15.0 yourself for `DiditSDK` or `DiditSDKNFC`. Code always writes `import DiditSDK`.

**Info.plist:** `NSCameraUsageDescription`, `NSMicrophoneUsageDescription` and `NSPhotoLibraryUsageDescription` are required (iOS terminates the app when a missing key's resource is accessed). With the NFC or All variant also add `NFCReaderUsageDescription`, the **Near Field Communication Tag Reading** capability, the entitlement `com.apple.developer.nfc.readersession.formats` = `TAG`, and `com.apple.developer.nfc.readersession.iso7816.select-identifiers` = `D23300000045737445494420763335`, `A0000002471001`, `A0000002472001`, `00000000000000`. NFC does not run on the simulator.

```swift
import SwiftUI
import DiditSDK

struct VerifyView: View {
    let sessionToken: String  // from your backend

    var body: some View {
        Button("Verify identity") {
            DiditSdk.shared.startVerification(
                token: sessionToken,
                configuration: DiditSdk.Configuration(languageLocale: .spanish, closeOnComplete: true)
            )
        }
        .diditVerification { result in
            switch result {
            case .completed(let session):
                print(session.sessionId, session.status.rawValue)  // "Approved" | "Pending" | "Declined"
            case .cancelled(let session):
                print("cancelled", session?.sessionId ?? "no session yet")
            case .failed(let error, _):
                print(error.localizedDescription)
            }
        }
    }
}
```

- `DiditSdk.shared.startVerification(token: String, configuration: Configuration? = nil)` is synchronous (not `async`); the result arrives through `.diditVerification(onComplete:)` on a view in the hierarchy.
- `DiditSdk.shared.dismiss()` ends an active flow and delivers `.cancelled(session:)`. Do not set `isPresented = false` or dismiss the SDK's view controller yourself.
- Observe `DiditSdk.shared.state` (`.idle`, `.creatingSession`, `.loading`, `.ready`, `.error(String)`) for custom loading UI.

#### Android (`me.didit:didit-sdk` 4.9.1, Kotlin)

Requirements: minSdk 23 (ML auto-capture needs API 24+, manual capture below), Kotlin 1.9+.

```kotlin
// settings.gradle.kts
dependencyResolutionManagement {
    repositories {
        google()
        mavenCentral()
        maven { url = uri("https://raw.githubusercontent.com/didit-protocol/sdk-android/main/repository") }
    }
}

// app/build.gradle.kts
dependencies { implementation("me.didit:didit-sdk:4.9.1") }
android {
    packaging { resources { excludes += "META-INF/versions/9/OSGI-INF/MANIFEST.MF" } }
}
```

Artifacts (keep all `me.didit` artifacts on the same version): `didit-sdk` (full: auto-capture + NFC), `didit-sdk-core` (manual capture only), `didit-sdk-autodetection`, `didit-sdk-autodetection-play`, `didit-sdk-nfc`. Permissions (`INTERNET`, `ACCESS_NETWORK_STATE`, `CAMERA`, `NFC`) merge from the SDK manifest; camera and NFC are declared optional hardware.

```kotlin
// Application.onCreate()
DiditSdk.initialize(this)

// Activity: launch the UI when the SDK is ready
lifecycleScope.launch {
    DiditSdk.state.collect { state ->
        when (state) {
            is DiditSdkState.Ready -> DiditSdk.launchVerificationUI(this@MainActivity)
            is DiditSdkState.Error -> Log.e("Didit", state.message)
            else -> Unit // Idle, CreatingSession, Loading
        }
    }
}

DiditSdk.startVerification(token = sessionToken, configuration = Configuration(closeOnComplete = true)) { result ->
    when (result) {
        is VerificationResult.Completed -> Log.d("Didit", "${result.session.sessionId} ${result.session.status.rawValue}")
        is VerificationResult.Cancelled -> Log.d("Didit", "cancelled ${result.session?.sessionId}")
        is VerificationResult.Failed -> Log.e("Didit", result.error.message ?: "error")
    }
}
```

- `DiditSdk.startVerification(token: String, configuration: Configuration? = null, onResult: (VerificationResult) -> Unit)`. Without `DiditSdk.initialize(context)` first, `onResult` receives `Failed(VerificationError.NotInitialized, null)`.
- Imports: `me.didit.sdk.DiditSdk`, `me.didit.sdk.DiditSdkState`, `me.didit.sdk.VerificationResult`, `me.didit.sdk.Configuration`.

#### React Native (`@didit-protocol/sdk-react-native` 4.9.1)

Requirements: React Native 0.76+ with the New Architecture, iOS 13+ (NFC 15+), Android API 24+, Kotlin 1.9+, Java 17+. Not available in Expo Go: use a development build or `npx expo prebuild`.

```bash
npx expo install @didit-protocol/sdk-react-native   # Expo: add "@didit-protocol/sdk-react-native" to expo.plugins
npm install @didit-protocol/sdk-react-native        # React Native CLI
```

- Expo config plugin options: `{ "iosNfcEnabled": false, "androidNfcEnabled": false }` builds without NFC. The plugin adds the Maven repository, the podspec and the Android packaging rules.
- React Native CLI: add the DiditSDK podspec pinned to tag `4.9.1` (never `main`) to the Podfile, the Didit Maven repository to `settings.gradle`, and the packaging rules from the docs; `DIDIT_SDK_IOS_NFC_ENABLED=false` / `diditSdkAndroidNfcEnabled=false` turn NFC off. Add the iOS Info.plist keys listed above.

```typescript
import { startVerification, VerificationStatus } from "@didit-protocol/sdk-react-native";

const result = await startVerification(sessionToken, { languageCode: "es", closeOnComplete: true });
switch (result.type) {
  case "completed":
    if (result.session.status === VerificationStatus.Approved) { /* wait for backend confirmation */ }
    break;
  case "cancelled":
    break;
  case "failed":
    console.error(result.error.type, result.error.message);
    break;
}
```

`startVerification(token: string, config?: DiditConfig): Promise<VerificationResult>`.

#### Flutter (`didit_sdk` 4.9.1)

Requirements: Flutter 3.3+, Dart 3.11+, iOS 13+ (NFC 15+), Android API 23+.

```bash
flutter pub add didit_sdk
```

iOS: select the native variant in `ios/Podfile` (`$DiditSdkIosVariant = 'all'`, `'core'`, `'autodetection'` or `'nfc'`; `all` and `nfc` need `platform :ios, '15.0'`) with the podspec pinned to tag `4.9.1`, then add the Info.plist keys listed above. Android: select the native variant with `diditSdkAndroidVariant` in `android/gradle.properties` (`all` by default, `core`, `autodetection` or `nfc`; `core` and `autodetection` drop NFC), or depend on `didit_sdk_core` / `didit_sdk_autodetection` / `didit_sdk_nfc` instead of `didit_sdk` to pin the variant on both platforms (then import from that package, for example `package:didit_sdk_core/sdk_flutter.dart`). `all` and `nfc` builds need `pickFirsts += "META-INF/versions/9/OSGI-INF/MANIFEST.MF"` in `packaging.resources`. Full snippets: https://docs.didit.me/integration/native-sdks/flutter-sdk

```dart
import 'package:didit_sdk/sdk_flutter.dart';

final result = await DiditSdk.startVerification(
  sessionToken,
  config: const DiditConfig(languageCode: 'es', closeOnComplete: true),
);
switch (result) {
  case VerificationCompleted(:final session):
    debugPrint('${session.sessionId} ${session.status}');
  case VerificationCancelled():
    debugPrint('cancelled');
  case VerificationFailed(:final error):
    debugPrint('${error.type} ${error.message}');
}
```

`static Future<VerificationResult> startVerification(String token, {DiditConfig? config})`. Without `languageCode` the device locale is sent.

#### WebView (fallback only)

Load the session `url` and intercept navigation to your `callback` URL (read `verificationSessionId` and `status`). Required settings:
- A generic mobile user agent, for example `Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36`.
- React Native (`react-native-webview`): `javaScriptEnabled`, `domStorageEnabled`, `allowsInlineMediaPlayback`, `mediaPlaybackRequiresUserAction={false}`, `mediaCapturePermissionGrantType="grant"`.
- Flutter (`webview_flutter`): `JavaScriptMode.unrestricted`, iOS creation params `allowsInlineMediaPlayback: true` and `mediaTypesRequiringUserAction: const {}`, grant `setOnPlatformPermissionRequest`, and on Android `setMediaPlaybackRequiresUserGesture(false)`.

A WebView loses NFC and native capture. Never open a `wallet_ownership` URL (see Transactions) in an embedded WebView.

### Configuration options

| Option | Web (`DiditSdkConfiguration`) | iOS (`DiditSdk.Configuration`) / Android (`Configuration`) | React Native / Flutter (`DiditConfig`) | Default |
|---|---|---|---|---|
| Debug logging | `loggingEnabled` | `loggingEnabled` | `loggingEnabled` | `false` |
| Close (X) button | `showCloseButton` | `showCloseButton` | `showCloseButton` | `true` |
| Exit confirmation | `showExitConfirmation` | `showExitConfirmation` | `showExitConfirmation` | `true` |
| Close when complete | `closeModalOnComplete` | `closeOnComplete` | `closeOnComplete` | `false` |
| Language | From the session `url` | `languageLocale: SupportedLanguage?` (`.spanish` / `SupportedLanguage.SPANISH`) | `languageCode` (ISO 639-1 string) | Device locale, English fallback |
| Language selector on welcome screen | - | `showLanguageSelector` | `showLanguageSelector` | `false` |
| Font | - | `fontFamily` (iOS: registered in `UIAppFonts`; Android: `res/font/` name) | `fontFamily` | System font |
| First document camera | `defaultDocumentCamera` (`'front'`/`'back'`) | `defaultDocumentCamera` (`CameraLens`) | `defaultDocumentCamera` (`CameraLens`) | back |
| First liveness camera | `defaultLivenessCamera` | `defaultLivenessCamera` | `defaultLivenessCamera` | front |
| Document camera switcher | `showDocumentCameraSwitchButton` | `showDocumentCameraSwitchButton` | `showDocumentCameraSwitchButton` | `true` |
| Liveness camera switcher | `showLivenessCameraSwitchButton` | `showLivenessCameraSwitchButton` | `showLivenessCameraSwitchButton` | `true` |
| Web only | `containerElement` (`document.body`), `zIndex` (`9999`), `embedded` (`false`), `embeddedContainerId` (required when embedded) | - | - | |

Camera options need Web SDK 0.4.0+. A device without the requested camera keeps the one it has; switchers are hidden on single-camera devices. The liveness camera options apply to passive liveness.

### Step 3: Read the SDK result

| Surface | Status values | Notes |
|---|---|---|
| Redirect and WebView callback | `Approved`, `Declined`, `In Review` | Query parameters on your callback URL |
| Iframe `didit:completed` | `data.status`, open string | Usually `Approved`, `Declined`, `In Review` |
| Web SDK `onComplete` | `session.status` | Typed `Approved \| Pending \| Declined` but passes the hosted status through (can be `In Review`); `Pending` when none was reported |
| iOS, Android, React Native, Flutter | `Approved`, `Pending`, `Declined` | Any other status (for example `In Review`) maps to `Pending` |

Result shapes: Web `{ type: "completed" | "cancelled" | "failed", session?: { sessionId, status }, error?: { type, message } }`; iOS `VerificationResult` `.completed(session:)`, `.cancelled(session:)`, `.failed(error:session:)`; Android sealed `VerificationResult.Completed(session)`, `Cancelled(session?)`, `Failed(error, session?)`; React Native the same union as web with `type`; Flutter sealed `VerificationCompleted`, `VerificationCancelled`, `VerificationFailed`. The SDKs return only the session id and status: all extracted data comes from the webhook or the decision endpoint.

| Platform | Error types |
|---|---|
| Web | `sessionExpired`, `networkError`, `cameraAccessDenied`, `unknown` |
| iOS (`VerificationError`) | `.sessionExpired`, `.retryBlocked`, `.networkError`, `.cameraAccessDenied`, `.unknown(String)` |
| Android (`VerificationError`) | `SessionExpired`, `RetryBlocked`, `NetworkError`, `CameraAccessDenied`, `NotInitialized`, `ApiError(statusCode, errorMessage)`, `Unknown(message)` |
| React Native, Flutter (`VerificationErrorType`) | `sessionExpired`, `networkError`, `cameraAccessDenied`, `notInitialized`, `apiError`, `retryBlocked`, `unknown` |

`sessionExpired`: create a new session. `retryBlocked`: the user reached the maximum number of verification attempts.

### Step 4: Confirm on your backend

Subscribe to the `status.updated` webhook (see **didit-verification-management** for destinations and signature checks) or call `GET /v3/session/{session_id}/decision/` with the API key. Treat the decision `status` as the source of truth: grant access only on `Approved`; `In Review` waits for a reviewer; for `Expired` create a new session.

### Starting from a workflow id (no backend session)

Native, React Native and Flutter SDKs can also start from a workflow id: iOS `startVerification(workflowId:vendorData:configuration:)`, Android `startVerification(workflowId, vendorData, configuration, onResult)`, React Native `startVerificationWithWorkflow(workflowId, { vendorData, metadata, contactDetails, expectedDetails, config })`, Flutter `startVerificationWithWorkflow(workflowId, {vendorData, config})`. This is the workflow's UniLink: no API key is involved, so anyone who has the workflow id can start sessions for it, and `vendorData` is only attached when the **Vendor Data** option is enabled on the workflow in the console. The web equivalent is the UniLink URL (`https://verify.didit.me/u/...`) passed to the Web SDK or an iframe. Use backend sessions in production.

---

## Transactions (submitTransaction)

Submits a monitored transaction (including Travel Rule transfers and crypto screening) from the end user's device. The SDK attaches a device fingerprint automatically and Didit derives IP and user agent server-side. The token fixes the subject: `subject.externalUserId` in the payload is replaced with the token's `vendor_data`. See **didit-transaction-monitoring** for rules, statuses and Travel Rule.

### Step 1: Mint a transaction SDK token (backend)

```
POST https://verification.didit.me/v3/transactions/sdk-token/
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `vendor_data` | string | **Yes** | Your user id (max 255). Every transaction submitted with the token gets this subject |
| `ttl_seconds` | integer | No | Lifetime, `60` to `86400`, default `900` |
| `max_uses` | integer | No | Successful submissions allowed (`>= 1`). Omit or `null` for unlimited within the TTL |

camelCase aliases `vendorData`, `ttlSeconds`, `maxUses` are accepted. Response `201`:

```json
{"sdk_token": "q7Zt...urlsafe", "expires_at": "2026-07-07T12:15:00Z"}
```

Mint a fresh token per user session and keep `max_uses` tight.

### Step 2: Submit from the client

**Web (0.3.0+):**

```typescript
import { DiditSdk, DiditTransactionError } from "@didit-protocol/sdk-web";

try {
  const result = await DiditSdk.shared.submitTransaction({
    transactionToken: sdkToken,
    transaction: {
      txnId: "wd-2026-07-07-0042",
      category: "finance",
      details: { direction: "out", amount: "250.00", currency: "EUR" },
      subject: { fullName: "Jane Doe" },
      counterparty: { fullName: "Ana Diaz", paymentMethod: { type: "bank_account", accountId: "acct-0001" } },
      customProperties: { order_id: "ORD-7891" },
    },
    autoLaunchAction: true, // default; only wallet_ownership is auto-launched
    onActionCompleted: (refreshed, error) => console.log(refreshed.status, error?.type),
  });
  console.log(result.transactionId, result.status, result.actionRequired?.type);
} catch (error) {
  if (error instanceof DiditTransactionError) {
    // error.type: "invalid_token" | "expired_token" | "validation" (see error.fieldErrors) | "network"
  }
}
```

`submitTransaction(options: { transactionToken, transaction, baseUrl?, autoLaunchAction?, onActionCompleted? }): Promise<SubmitTransactionResult>`. The web payload uses `category`, `details` and `customProperties`; the SDK maps them to the wire names `type`, `info` and `props`. The Web SDK has no `getTransaction`: re-read with `GET /v1/transactions/{transaction_id}/` and the same `X-Transaction-Token` header.

**Mobile (iOS and Android 4.1.0+, and the React Native and Flutter releases that pin them):** the payload uses the wire names directly (`txnId`, `type`, `info`, `subject`, `counterparty`, `props`, `travelRule`, `includeCryptoScreening`).

| Platform | Signature | Errors |
|---|---|---|
| iOS | `try await DiditSdk.shared.submitTransaction(transactionToken:transaction:options:) -> DiditTransactionResult` and `getTransaction(transactionToken:transactionId:options:)` | `DiditTransactionError` `.invalidToken(message:)`, `.expiredToken(message:)`, `.validation(fieldErrors:)`, `.network(message:)` |
| Android | `suspend fun DiditSdk.submitTransaction(transactionToken, transaction, options = DiditTransactionOptions())` and `getTransaction(transactionToken, transactionId, options)` (package `me.didit.sdk.transactions`; call `DiditSdk.initialize` first) | sealed `DiditTransactionException` `InvalidToken`, `ExpiredToken`, `Validation(fieldErrors)`, `Network` |
| React Native | `submitTransaction(transactionToken, transaction, options?)`, `getTransaction(transactionToken, transactionId, options?)` | `DiditTransactionError` with `.code` `invalid_token` / `expired_token` / `validation` / `network` and `.fieldErrors` |
| Flutter | `DiditSdk.submitTransaction(transactionToken, payload, {options})`, `DiditSdk.getTransaction(transactionToken, transactionId, {options})` | `DiditTransactionException` with `.code` (same four values) and `.fieldErrors` |

Options: `baseUrl`, `autoLaunchAction` (default `true`), `onTransactionUpdated(result)`; iOS and Android also take `useNativeWalletOwnership` (default `true`: native flow, falling back to an in-app browser tab, then the default browser).

```kotlin
import me.didit.sdk.DiditSdk
import me.didit.sdk.transactions.*

val result = DiditSdk.submitTransaction(
    transactionToken = sdkToken,
    transaction = DiditTransactionPayload(
        txnId = "wd-2026-07-07-0042",
        type = "travelRule",
        info = DiditTransactionInfo(direction = "out", amount = 0.25, currency = "ETH", currencyType = "crypto",
            cryptoParams = mapOf("crypto_chain" to "ETH")),
        subject = DiditTransactionParticipant(fullName = "Jane Doe"),
        counterparty = DiditTransactionParticipant(fullName = "Jane Doe",
            paymentMethod = DiditTransactionPaymentMethod(type = "unhosted_wallet", accountId = "0xBeneficiaryWallet01")),
        travelRule = DiditTravelRule(status = "AWAITING_COUNTERPARTY",
            beneficiaryData = mapOf("wallet_address" to "0xBeneficiaryWallet01", "name" to "Jane Doe")),
        includeCryptoScreening = true
    ),
    options = DiditTransactionOptions(onTransactionUpdated = { refreshed -> Log.d("Didit", "${refreshed.status}") })
)
```

Swift, React Native and Dart use the same type names (`DiditTransactionPayload`, `DiditTransactionInfo`, `DiditTransactionParticipant`, `DiditTransactionPaymentMethod`; Travel Rule is `DiditTravelRuleInfo` on iOS and `DiditTravelRule` elsewhere; React Native takes a plain object typed `DiditTransaction`).

### Payload fields

| SDK field (web name if different) | `/v3/transactions/` field | Notes |
|---|---|---|
| `txnId` | `transaction_id` | **Required**, max 128, unique per application: a repeated id is a `validation` error |
| `txnDate`, `zoneId` | `transaction_at`, `time_zone` | ISO 8601 (defaults to now), IANA zone |
| `type` (`category`) | `transaction_category` | **Required**: `finance`, `kyc`, `travelRule`, `userPlatformEvent`, `gamblingBet`, ... |
| `info` (`details`) | `transaction_details` | **Required** `direction` (`in`/`out`, `inbound`/`outbound` also accepted), `amount`, `currency`; optional `currencyType` (`fiat`/`crypto`), `amountInDefaultCurrency`, `defaultCurrencyCode`, `paymentDetails`, `paymentTxnId` (on-chain hash), `type` (web `actionType`), `cryptoParams` |
| `subject`, `counterparty` | `subject`, `counterparty` | `type` (`individual`/`company`), `fullName` (**required on the subject**), `firstName`, `lastName`, `dob` (YYYY-MM-DD), `address`, `institutionInfo`, `device`, `paymentMethod` (`type`, `accountId`, `issuingCountry`). Counterparty `paymentMethod.type: "unhosted_wallet"` declares a self-hosted wallet |
| `props` (`customProperties`) | `custom_properties` | Usable in rules as `custom_values.<key>` |
| `travelRule` | `travel_rule_details` | `status` is required by the API (Didit drives the exchange and ignores it when Travel Rule is enabled), `protocol`, `required`, `obligationsCount`, `originatorData`, `beneficiaryData`, `metadata` |
| `includeCryptoScreening` | `include_crypto_screening` | Per-transaction screening override |

### Step 3: Handle the result and `actionRequired`

Result: `transactionId` (Didit UUID), `status` (`APPROVED`, `IN_REVIEW`, `DECLINED`, `AWAITING_USER`), `travelRuleStatus`, `actionRequired` (`type`, `url`, `sessionId`, `sessionToken`, `status`, `widgetSessionId`, `expiresAt`).

| `actionRequired.type` | What the SDK does | What your app does |
|---|---|---|
| `wallet_ownership` | Auto-launches the proof flow when `autoLaunchAction` is true, re-reads the transaction afterwards and calls `onActionCompleted` (web) / `onTransactionUpdated` (mobile) | Nothing, or open `url` yourself in a real browser surface (never an embedded WebView) if you turned auto-launch off |
| `verification_session` | Never auto-launches | Start your verification flow with `sessionToken` (mobile) or `url` (web), then re-read the transaction |

```swift
if let action = result.actionRequired, action.type == DiditTransactionActionRequired.verificationSessionType,
   let token = action.sessionToken {
    DiditSdk.shared.startVerification(token: token)  // not async; result via .diditVerification
}
```

```typescript
// React Native
if (result.actionRequired?.type === "verification_session" && result.actionRequired.sessionToken) {
  await startVerification(result.actionRequired.sessionToken);
  const refreshed = await getTransaction(sdkToken, result.transactionId);
}
```

`sessionToken` is optional in every SDK (and `url` on mobile): check before use. `actionRequired` returns to `null` once resolved, and your backend receives `transaction.status.updated` (see **didit-transaction-monitoring**).

---

## Events (device lane)

The SDK versions documented here have no events method. The dedicated `@didit-protocol/signals` package is release-dependent: verify its published exports before using it. Mint a monitoring token on your backend, then post events from the device with your own HTTP client (`fetch`, `URLSession`, OkHttp). Event ingestion must be on (**Transactions > Settings > Event monitoring**); otherwise every write answers `403` with `{"code": "event_monitoring_disabled"}`. Full event envelope, categories and rules: **didit-event-monitoring**.

```
POST https://verification.didit.me/v3/events/sdk-token/
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `vendor_data` | string | **Yes** | Subject of every event sent with the token |
| `entity_type` | string | No | `individual` (default) or `company` |
| `allowed_event_categories` | string[] | No | Limit to `auth`, `session`, `gameplay`, `bonus`, `affiliate`, `payment`, `dispute`, `security`, `responsible_gambling`, `custom` (default: all) |
| `ttl_seconds` | integer | No | `60` to `86400`, default `900` |
| `max_uses` | integer | No | One use per event, default `1000`; `null` for unlimited |
| `bind_to_origin` | string | No | Browser `Origin` that must match exactly (a request without `Origin` is refused) |

Response `201`: `monitoring_token`, `expires_at`, `allowed_event_categories`, `max_uses`, `bind_to_origin`.

```typescript
await fetch("https://verification.didit.me/v1/events/", {
  method: "POST",
  headers: { "X-Monitoring-Token": monitoringToken, "Content-Type": "application/json" },
  body: JSON.stringify({
    event_id: "session-abc-login-1",
    event_category: "auth",
    action_type: "login",
    occurred_at: new Date().toISOString(),
    session: { session_id: "web-session-abc", sequence: 1 },
    payload: { method: "password" },
  }),
});
```

No subject in the body: it comes from the token. `POST /v1/events/batch/` takes `{"events": [...]}` (up to 500). Send `X-Monitoring-Token`; a transaction SDK token value is not accepted here.

---

## Error Responses

Backend endpoints (`POST /v3/session/`, `POST /v3/transactions/sdk-token/`, `POST /v3/events/sdk-token/`):

| Code | Meaning | Action |
|---|---|---|
| `400` | Invalid request | Read the field errors in the response body |
| `401` | The API key has expired | Rotate it or create a new key in **Developers > API keys** |
| `403` | Missing, wrong or revoked API key; a scoped key without access to this endpoint; a request from outside the key's IP allowlist; or not enough credits | Read the message in `detail` or `error`: fix the `x-api-key` header or the key's access, or top up |
| `429` | Rate limit: 300 POST/PATCH/DELETE and 600 GET requests a minute per key | Wait the `Retry-After` seconds, then retry |
| `400` (`/v3/session/`) | Unknown `workflow_id`, invalid `language`, blocklisted `vendor_data`, or not enough credits (`{"detail": "You don't have enough credits..."}`) | Fix the field, or top up |
| `403` (`/v3/session/`) | A key limited to some workflows asked for another workflow | Use one of the key's workflows |
| `429` (`/v3/session/`) | More than 600 session creations a minute | Wait `Retry-After` |
| `403` (`/v3/events/sdk-token/`) | `{"code": "event_monitoring_disabled"}` | Turn on event monitoring in the console |

Device endpoints (`/v1/transactions/`, `/v1/events/`):

| Code | Meaning | Action |
|---|---|---|
| `401` | Token missing, unknown, revoked, expired (the detail contains `expired`) or over `max_uses`; for monitoring tokens also an `Origin` that does not match `bind_to_origin` | Mint a new token on the backend |
| `400` | Payload validation failed (SDKs: `validation` with `fieldErrors`); for events also a category outside `allowed_event_categories` | Fix the payload |

---

## Common Workflows

### Web KYC with the JavaScript SDK

1. Backend: `POST /v3/session/` with `workflow_id` and `vendor_data`; return `url` to the browser.
2. Browser: `DiditSdk.shared.startVerification({ url })`; on `onComplete` with `type: "completed"`, show "checking your result".
3. Backend: on the `status.updated` webhook (or `GET /v3/session/{session_id}/decision/`), mark the user verified only when `status` is `Approved`.

### Mobile onboarding with a native SDK

1. App asks your backend for a session; backend returns `session_token` only.
2. iOS `DiditSdk.shared.startVerification(token:)`, Android `DiditSdk.startVerification(token = ...)`, React Native `startVerification(token)` or Flutter `DiditSdk.startVerification(token)`.
3. Treat `Pending` as "in review", then rely on the webhook for the final decision.

### Step-up check on a risky withdrawal from the app

1. Backend mints `POST /v3/transactions/sdk-token/` for the user's `vendor_data` (`max_uses: 1`).
2. App calls `submitTransaction`; a rule (Transactions > Rules, action **Change status > AWAITING_USER** with a Biometric Authentication workflow) moves it to `AWAITING_USER` with `actionRequired.type == "verification_session"`.
3. App starts the verification with `actionRequired.sessionToken` (web: `url`); Didit matches a live selfie against the face verified at onboarding for the same `vendor_data`.
4. The transaction re-evaluates to `APPROVED` or `DECLINED`; the backend gets `transaction.status.updated` and settles only then.

---

## Utility Scripts

**mint_sdk_tokens.py**: backend helper that creates a session and/or mints a transaction SDK token and/or a monitoring token, and prints only client-safe values (never the API key).

```bash
export DIDIT_API_KEY="your_api_key"

# Session for the Web SDK (url) or a native SDK (session_token)
python scripts/mint_sdk_tokens.py --vendor-data user-42 --workflow-id 11111111-2222-3333-4444-555555555555

# Transaction token for submitTransaction: 15 minutes, 3 submissions
python scripts/mint_sdk_tokens.py --vendor-data user-42 --transaction-token --ttl-seconds 900 --max-uses 3

# Monitoring token for device events, limited to auth and session events
python scripts/mint_sdk_tokens.py --vendor-data user-42 --monitoring-token --event-categories auth,session
```
