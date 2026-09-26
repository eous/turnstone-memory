---
name: project_model_modal_kind_redesign
description: "Admin add/edit model modal for rerank/TTS/embedding kinds: kind-aware redesign still DEFERRED (2026-07-06); only a backend rerank-detect fix shipped."
metadata: 
  node_type: memory
  type: project
---

The admin "add/edit model" modal (`turnstone/console/static/admin.js` + `index.html`; backend `admin_detect_model` in `console/server.py`) was built for chat models and breaks for non-chat types as they're added (rerank, TTS/STT, soon embedding). Two pains: (1) `base_url` is overloaded and type-dependent; (2) capabilities is a raw-JSON textarea you hand-author by reading source.

**Root analysis (2026-06-01):** the missing abstraction is **modality/kind**, NOT a new provider class or API surface. A model is `provider × kind`. 4 of 5 kinds (chat, embedding, stt, tts) are OpenAI-wire — `base_url = $host/v1`, SDK appends the path, probe via `/v1/models`. **Rerank is the lone outlier**: Cohere/Jina `POST <full-url>` lane (`CohereJinaRerankClient`, resolved in `rerank_config.py`), `base_url` must be the full `/rerank` path, never speaks `/v1/models`. So: DON'T add provider classes (audio/embedding are just the OpenAI SDK with `client.audio.*`/`client.embeddings.*`; rerank already has its own lane). Add an explicit `kind` field that drives form fields, base_url semantics, probe dispatch, and role eligibility (today `kind` is implicit, smeared across capability flags + the Roles tab). Keep a raw-JSON "Advanced" escape hatch. The raw-JSON cap editor is the chronic pain, most acute for local/self-hosted models (no static cap-table entry) — i.e. exactly Turnstone's identity.

**Deferred (user chose minimal scope):** the type-aware modal redesign (Phase 1) and a self-describing per-kind field-schema endpoint (Phase 2, probably over-engineered at current scale).

**Shipped 2026-06-01 (backend-only, this is the whole fix):** rerank add-via-modal was hard-broken — `admin_detect_model` always ran the `/v1/models` probe and gated calibration on `reachable`, so a `/rerank` endpoint failed either way (`$host/v1` → probe passes but calibration POSTs the wrong path; `$host/rerank` → probe 404s). Fix: branch on `supports_rerank` BEFORE the probe → calibrate-directly-as-reachability-check (success autopopulates the 3 cal fields; failure → `reachable:False`+error; empty base_url → 400; no-separation → reachable+note), and drop the dead post-probe calibrate block. Tests in `tests/test_admin_calibrate_endpoint.py`. NOTE: the hand-JSON `supports_rerank` pain was later resolved by the admin-shelf Models hatch (2026-06-10, PR #647): a capability tile matrix with a dedicated supports_rerank tile + known-model autofill replaced raw-JSON authoring ([[project_admin_shelf_redesign]]). `recalibrateModel` on a saved reranker was never broken. What REMAINS deferred from this memory: the kind-aware form reshaping (base_url semantics + probe dispatch keyed on an explicit `kind` discriminator).

**Re-verified 2026-07-06: still deferred, no drift.** Grepped console static JS/HTML for a `kind`/`modelKind` discriminator field — none exists yet; the modal is unchanged since the 2026-06-01 rerank fix. Safe to keep treating Phase 1/2 as open.

Relates to [[project_reranker_backend_design]], [[project_model_definitions]], [[project_bm25_rerank_redirect]].
