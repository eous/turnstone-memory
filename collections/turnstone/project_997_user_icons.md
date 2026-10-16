---
name: project_997_user_icons
description: "#997 user icons: 2026-10-13/14 rulings (initial on six colours picked at creation, write scope to change, PNG uploads one per person, admin reset, IdP import later) and where the scope lives."
metadata:
  type: project
---

#997 (user icons, pre-work for the #998 attribution UX) was re-scoped on 2026-10-13 against `dev` @
4593eefb. The issue-versus-code table, code map, bugs on the path, open decisions and both design
passes live in `docs/design/997-user-icons-scope.md` (local, git-ignored). Code work is on branch
`feat/997-user-icons` in its own worktree off `origin/dev`.

**Rulings (maintainer, 2026-10-13):**
1. Each user sets their own visual (self-service). Read means no writes: changing it needs the
   write scope for every credential, so a viewer keeps the colour picked at creation (ruling 12
   replaced "viewers included").
2. A user can upload a picture, pick one of six colours for the generated default, or reset
   (removes the picture; the colour stays). No symbol or emoji picker. (Shuffle through generated
   designs was the first ruling; six swatches replaced it once the design became initials.)
3. Users without a picture get a generated visual: simple, randomized, unique per user, built so two
   users are hard to confuse.
4. Self-service and the generated default ship first, on every install. Identity-provider picture
   import is a second change: providers that send a picture claim first, then Entra via Graph after
   a live-tenant spike.
5. Any signed-in user may see any user's visual (matches today's id exposure). Fetching an upload
   by id shows that the id exists, which is fine: ids are random uuid4 hex and already visible to
   every signed-in user.
6. Admins can reset another user's visual to the default.
7. Formats: uploads are PNG, stored and served as a 256px square, never SVG. The generated default
   is an initial on a per-user colour and colour tint, drawn by the page because the tint must
   follow the theme toggle; there is no generated SVG (the maintainer dropped it when adopting
   initials).
8. People are round; personas and service accounts are square (the maintainer's "ok" to that
   recommendation; the initials prototype bears it out).
9. One letter, not two (two blur at the 16px presence-stack size).
10. The server picks each new account's colour at creation, avoiding people who share its
    initial. The account stores its colour (0-5); with none stored, the server hashes the id.
11. The server sends the initial with the colour wherever it sends a name, so one Python rule
    serves the creation-time pick and the page. Amber is left out of the six colours (it is the
    accent and the rail's attention badge).

12. Read means no writes (above). The maintainer floated a desaturated colour for read-only users;
    Claude recommended against it for now (hues converge, grey reads as disabled, the avatar would
    follow the role) and suggested a role badge in #998's member lists. Unanswered; not built.
13. Picture decoding queues, one at a time per process (uploads past 4 waiting get 503), with
    per-format pixel limits (2048 PNG/WebP, 4096 JPEG) and a cap on JPEG scans.
14. Login, setup and refresh return the login name as `username` plus a new `display_name`;
    whoami keeps the display name in `username` and adds `display_name`.
15. Initials use titlecase, not uppercase (Georgian keeps its ordinary letters). The JPEG scan cap
    also guards the other image decoders (chat attachments, thumbnails, the orientation fix),
    folded into the #997 branch by the maintainer's choice.
16. Upload admission: one upload in flight per person, held from the moment it starts arriving,
    plus the cap of five in flight per process (one decoding, four waiting); both refusals answer
    503 with Retry-After.
17. Pictures uploaded with a wide-gamut colour profile are read as sRGB and look a little duller;
    accepted and documented, with no server-side colour conversion.
18. The send path's repeated decoding (rotated photos turned and re-encoded on every turn) is fixed
    in #997 by a per-process cache keyed by content hash, by the maintainer's choice over a separate
    issue. Past about 15 rotated phone photos in one conversation it stops helping; left as is (base
    cost), not random eviction, an upright copy stored at upload, or a bigger budget.
19. Creating a session with several attachments names the refused file in the error, and
    thumbnails decode JPEGs at reduced scale; both folded into #997.
20. Orientation is read once, at open, from the EXIF a JPEG, PNG or WebP carries ahead of its
    pixels, as a browser reads a JPEG's or PNG's. An upright picture is sent without a decode, and
    the cache holds only rotated photos' turned copies.
21. Avatars live in three nullable columns on `users` (colour, picture, picture hash), not a table
    of their own: a write is one UPDATE that finds no row once the account is gone, and deleting
    the user deletes the picture.

Rulings 9-11 came from the maintainer agreeing to every recommendation on review page v5; 12-15
from the first /review round's questions, the same day; 16-19 from the second round's, 2026-10-14;
20-21 from the third round's, the same day.

**Code:** PR #1384 (`feat/997-user-icons` to dev: the image-decoder hardening, the upload
byte budget, then the feature, with migration 083 after #1359's 082). The hardening went to
main for 1.8.7 in PR #1386, after dev's 7dc4ff19 so it cherry-picked cleanly.

**Context:** members will see other members' names (#998), but a planned presence stack in the
interactive session pane shows icons without names, before anyone types. That is why initials
replaced the abstract-figure design, and why same-initial, same-colour pairs still matter.

**Why:** the issue body (filed 2026-08-11) does not match the code: login reads only ID-token
claims, the attachment blob store is workstream-bound, panes show no sender at all, and service
principals such as `channel-gateway` appear as senders.

**How to apply:** treat the issue body's mechanics (blob-store reuse, a column on
`oidc_identities`, immutable caching, "panes render text labels") as superseded by the scope note,
and re-check its line numbers before coding ([[project_velocity]]). The initials prototype and
Claude's verification scripts are in `docs/design/997-initials/`. Related:
[[project_multiuser_attribution_ux]], [[feedback_minimal_scope_first]],
[[reference_entra_obo_harness]].
