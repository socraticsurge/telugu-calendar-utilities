# Guest profile storage internals

Keep consumers on `../guest-profile-store.ts`; that facade preserves the public API.
The store owns mutable state, storage calls, commit sequencing, and notifications.
These modules separate validation and compatibility without changing persisted data.

| Module | Responsibility |
| --- | --- |
| `types.ts` | Existing keys, schema constants, public and internal types |
| `values.ts` | Value validation and ID/revision generation |
| `birth-normalization.ts` | Normalize supported birth facts |
| `birth-ownership.ts` | Reject birth records this version cannot safely own |
| `profiles.ts` | Normalize, clone, serialize, and assess profile readiness |
| `legacy.ts` | Browser storage adapter and legacy row compatibility |
| `migration.ts` | Base-row migration and extension eligibility |
| `orphan-recovery.ts` | Recognize explicitly discardable orphan transactions |

## Invariants

- Preserve keys, schema versions, serialized field order, and exact ownership checks.
- Write base rows, then birth envelope, then commit marker; notify afterwards.
- A write failure makes in-memory state authoritative; do not roll back another tab's data.
- Unknown schemas and ambiguous ownership fail closed; do not overwrite them.
- An omitted or undefined patch field retains its value; null explicitly clears it.
- Leave calculation engines, ICS generation, UI behavior, and workflows untouched.

## Refactor verification

The existing guest-store tests remain unchanged; `guest-profile-storage-order.test.ts`
adds five checks for successful/partial writes, notification order, memory fallback,
and undefined-versus-null patch behavior.

A one-off differential harness compared this refactor to commit
`fb871d9511e50ebe221b39d05c50c6240ff9e003` in 738 synthetic scenarios.
It matched all 17 runtime exports, returns/errors, snapshots, notifications,
ordered storage calls, and stored bytes; no real user storage was accessed.

Local CodeScene scores: facade 6.85, normalization 8.41, ownership 9.00,
profiles 7.90, legacy 10.00, migration 9.68, recovery 8.90, values 9.09.
Types-only declarations are unscored; highest reported function complexity is 18.
These meet epic #561's floor of 6, not a claim that all residual debt is removed.

The owner approved the inventory-only test expectation change from 130 to 138
audited files; calculation assertions and quality thresholds are unchanged.
