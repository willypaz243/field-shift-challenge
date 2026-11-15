# Local sync client

Issue #49. Data modules for the Expo app; screen implementation is separate.
Use Node 22.13 or newer in a range supported by `package.json`.

```sh
npm ci
npm run typecheck
npm run lint
npm run format:check
npm test -- --runInBand
```

## Integration

Create one client at application startup and reuse it across screens:

```ts
import { openOfflineClient } from "./src/offline/open";
import { MockTransport } from "./src/offline/mock";

const client = await openOfflineClient(new MockTransport());
```

Screens call `useLocalData(client, zoneId)`. The hook loads SQLite immediately,
then refreshes on mount and whenever the app becomes active. A network failure
leaves the saved snapshot available. `data === null` means a complete first sync
is still required. Translate UI messages through the app's i18n layer.
`client.store.state(zoneId)` exposes the last successful local update timestamp.
The hook returns failures separately from cached data.

Replace `MockTransport` with `HttpTransport(baseUrl)` at startup for the real API.
Screens continue to read SQLite. Inject authentication through the transport's
optional fetch argument once the device-token contract is defined.

## Storage and retries

`sync_state` stores version, hash and successful update time per zone.
`sync_sections` stores each contract section as JSON per zone. Deltas replace
included sections; omitted sections are preserved and empty arrays clear lists.
A first sync requires all nine sections. Writes and version updates share one
exclusive SQLite transaction. Older versions cannot overwrite newer snapshots.
The contract does not define hash canonicalization; hashes are stored as opaque
metadata. The mock hash is a fixture identifier.

Queue submissions with `client.outbox.enqueue({ id, kind, payload })`, using a
caller-generated UUID that remains stable across retries. Kinds are `reports`,
`feedback` and `plans`. Reports use multipart; other kinds use JSON. Report
coordinates are rounded to three decimals. Native attachments use persisted
`{ uri, name, type }` descriptors; callers must keep files until upload succeeds.
A successful response removes the item; failures persist with exponential retry
from one second to one hour. Refresh attempts drain due items even if pulling
fails. `client.outbox.flush()` can also run after connectivity returns. The
client owns no background timer: retries run on refresh or explicit flush.
Only the reports contract defines duplicate 409 as success. Permanent errors
remain queued for inspection rather than losing submissions.

## Mock and verification

Fixtures copy valid examples from `../docs/API-CONTRACT.md`; crops import the
existing catalog. They demonstrate one zone, sparse forecast days and one
complete rotation, not live agricultural advice or a complete forecast year.
The mock records accepted submissions in memory and returns no changes when
`desde_version` matches its version.

Jest executes real SQLite SQL through Node's SQLite adapter, including restart
persistence, transaction rollback, deltas, retries and multipart requests.
Native `expo-sqlite`, attachment uploads and airplane mode still require a device
smoke test once screens are integrated. Exclusive transactions target native;
Expo's web SQLite transaction support needs a separate implementation.
