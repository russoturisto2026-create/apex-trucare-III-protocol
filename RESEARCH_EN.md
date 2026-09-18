# Research protocol

Chronological log of studying the **TruCare III pump protocol** — the commands the pump accepts,
and the responses it returns. The **Erwin Blueberry** app is used only as the standard means of
controlling the pump and is not itself studied. One entry equals one step (and one commit). Each
step references source materials by number from `MATERIALS_EN.md`; the step's findings are carried
over into `PROTOCOL_EN.md` with a reference to this step.

Maintenance rules are in `README_EN.md`. Key point: a finding gets **"confirmed"** status only
after ≥2 measurements with different characteristics (rule 8); before that it is an **"assumption"**.

Status legend: 🟡 assumption · 🟢 confirmed · 🔴 needs re-verification.

**Research boundary:** counts and captures are kept **from 16:34 (2026-09-16)** — earlier test-bench
activity (including user operations prior to this milestone) is pre-research context that set the
pump's initial state, and is not included in the findings. Captures started before the milestone
(e.g. the initial connection in Step 001) are used only for the part falling within the window, and
their findings are accepted only when confirmed within the window (e.g. topology/authorization —
Step 003, 16:52).

---

## Summary: current status

The summary reflects **currently valid** findings and is updated at every step. The log below is a
chronology: earlier findings in it are not rewritten, but marked "**→ refined:** Step NNN". Object
and command fields are described in the registry `tools/fields.py`, verified against all archived
captures (`tools/verify_fields.py`), and rendered into tables in PROTOCOL_EN.md; lists marked
"generated" below are built from the registry.

### Stage A — Transport and GATT topology — 🟢
- Services, characteristics, handles, MTU (517→251), enabling notifications — two connections
  matched byte-for-byte (Steps 001, 003).

### Stage B — Session and authorization — 🟢
- The pump's Bluetooth password (6 digits, written twice) in `0xFFC1`, verdict `0x00` in `0xFFC2` —
  two sessions and cross-check against the pump screen (Steps 001, 003).

### Stage C — Frame format — 🟢
- Command `35 LL 00 CC OO II <identity> [payload] CRC`, response `AA LL xx CC OO II [data] CRC`,
  CRC-16/MODBUS little-endian. Within the window: 1779 commands — all have the `0x35` marker, the
  length field equals the frame size, byte[2] = `00`, an `APEX…` block, correct CRC; 6284 responses
  of classes `A3`/`A1` — length field equals the frame size (Steps 004, 028).
- For `A5/03` the length field equals the frame minus CRC (all 250 frames in the window) 🟢; the
  reason for the difference has not been established.
- Response byte[2] depends on the object (`0x80` for `a3/21`, `0x25`/`0x26` for `a3/26`, `0x08` for
  `a3/08`…) — purpose not established.

### Stage D — Response objects
Generated:

<!-- gen:research_objects -->
- `a3/00` — main status: 64 of 88 bytes parsed (88 bytes); unparsed: 18..19, 22..23, 56..75. Table — PROTOCOL_EN.md §4.1.
- `a3/01` — detailed bolus log: 14 of 14 bytes parsed (128 records × 14 bytes). Table — PROTOCOL_EN.md §4.4.
- `a3/02` — basal change log: 102 of 102 bytes parsed (47 records × 102 bytes). Table — PROTOCOL_EN.md §4.6.
- `a3/03` — alarm history: 8 of 8 bytes parsed (28 records × 8 bytes). Table — PROTOCOL_EN.md §4.16.
- `a3/04` — refill history: 9 of 10 bytes parsed (11 records × 10 bytes); 🟡 refill history — type — off8; unparsed: 9. Table — PROTOCOL_EN.md §4.15.
- `a3/06` — daily doses (long history): 9 of 10 bytes parsed (38 records × 10 bytes); unparsed: 9. Table — PROTOCOL_EN.md §4.10.
- `a3/07` — bolus calculator: 246 of 246 bytes parsed (246 bytes). Table — PROTOCOL_EN.md §4.9.
- `a3/08` — basal profiles A–H: 96 of 96 bytes parsed (8 records × 96 bytes). Table — PROTOCOL_EN.md §4 (catalog).
- `a3/0a` — current TBR: 19 of 20 bytes parsed (20 bytes); unparsed: 6. Table — PROTOCOL_EN.md §4.7.
- `a3/0b` — last completed TBR: 26 of 26 bytes parsed (26 bytes). Table — PROTOCOL_EN.md §4.8.
- `a3/0c` — brief status: 4 of 20 bytes parsed (20 bytes); unparsed: 0..1, 6..19. Table — PROTOCOL_EN.md §4.2.
- `a3/21` — bolus log: 14 of 14 bytes parsed (10 records × 14 bytes). Table — PROTOCOL_EN.md §4.4.
- `a3/26` — daily doses (10 days): 9 of 10 bytes parsed (10 records × 10 bytes); unparsed: 9. Table — PROTOCOL_EN.md §4.10.
- `a3/27` — TBR log: 14 of 14 bytes parsed (10 records × 14 bytes). Table — PROTOCOL_EN.md §4.5.
- `a3/31` — firmware and protocol versions: 5 of 8 bytes parsed (8 bytes); unparsed: 0..2. Table — PROTOCOL_EN.md §4.11.
- `a1/55` — command acknowledgment: 🟢; frames in window: 181. Table — PROTOCOL_EN.md §4.12.
- `a1/a5` — rejection: command not accepted (pump locked): 🟢; frames in window: 2. Table — PROTOCOL_EN.md §4.12.
- `a1/a0` — simple bolus delivery progress: 🟢; frames in window: 38. Table — PROTOCOL_EN.md §4.12.
- `a1/a1` — extended bolus delivery progress: 🟢; frames in window: 54. Table — PROTOCOL_EN.md §4.12.
- `a1/aa` — bolus completion: 🟢; frames in window: 8. Table — PROTOCOL_EN.md §4.12.
<!-- /gen:research_objects -->

- `a3/08` — basal profiles: 8 records × 48 u16LE (0.025 U/h); record 00 matches command `a1/00`
  byte-for-byte 🟢 (Step 026); correspondence of records to profiles A… — 🟡.
- `a3/0a` — current TBR (§4.7), `a3/0b` — last completed TBR (§4.8) 🟢.
- `a3/26` (10 days) and `a3/06` (38 days) — daily doses (§4.9) 🟢.
- `a3/07`, `a3/31` — read by the app within the window, fields not parsed 🔲
  (byte-by-byte — `OBJECTS_EN.md`).
- IOB and battery percentage were not found on air — computed by the app 🟡 (Steps 006, 028).

### Stage E — Control commands
Generated:

<!-- gen:research_commands -->
- `a1/00` — write basal profile — 🟢 (Steps 026, 027); commands in window: 2.
- `a1/02` — start TBR / cancel bolus — 🟢 (Steps 024, 030, 031); commands in window: 9; fields in registry: 3.
- `a1/04` — select active basal profile — 🟢 (Steps 043, 044); commands in window: 6; fields in registry: 1.
- `a1/05` — cancel TBR — 🟢 (Steps 024, 026); commands in window: 4.
- `a1/11` — bolus presets — 🟢 (Steps 012, 025); commands in window: 10; fields in registry: 8.
- `a1/12` — start simple bolus — 🟢 (Steps 031); commands in window: 7.
- `a1/13` — start extended bolus — 🟢 (Steps 030, 046, 053); commands in window: 5.
- `a1/15` — write bolus calculator settings — 🟢 (Steps 036); commands in window: 15; fields in registry: 10.
- `a1/21` — stop / start delivery — 🟢 (Steps 027); commands in window: 3.
- `a1/31` — set pump time — 🟢 (Steps 009, 038); commands in window: 4.
- `a1/32` — write pump settings — 🟢 (Steps 009, 011, 013, 034); commands in window: 58; fields in registry: 18.
- `a1/33` — not established (response is an acknowledgment) — 🟡; commands in window: 3.
- `a1/34` — sound mode and its step — 🟢 (Steps 011, 016); commands in window: 56; fields in registry: 2.
- `a1/35` — change Bluetooth password — 🟢 (Steps 052); commands in window: 1.
<!-- /gen:research_commands -->

- Acknowledgment `a1/55 00 00` — for every `a1` command within 3 s: 121 of 121 in the window 🟢 (Step 028).

### Stage F — Behavior and timing — 🟢
- "Pulse" `a5/03`: unsolicited frame, period 180.0 ± 0.2 s, payload unchanged — 250 frames over the
  12.5 h window (Steps 005, 028).
- App polling cycle — 180 s: `a3/00`, `a3/0c`, `a3/21`, `a3/0a`, `a3/0b`, `a3/26` (243 full cycles);
  after writing settings — a repeated read of `a3/00`, `a3/0c` (Step 028).

### Open questions
- `a3/00`: unparsed offsets — PROTOCOL_EN.md §4.1.
- `a3/0c`: 16 of 20 bytes unparsed.
- `a1/12`, `a1/33` — purpose not established; `a1/31` (set time) needs a second observation within the window.
- `a1/00` — which profile is addressed; correspondence of `a3/08` records to profiles.
- TBR: rounding rule for percentages (one value); off86 not cross-checked against the screen.
- `a3/00` off16 "per day" counter — one reset observed.
- Bolus log `a3/21`: seconds are always `59`; extended bolus fields (off8/off10/off12) — one observation (Step 030).
- Object `a3/01` — detailed bolus log (128 records, structure = `a3/21`; fields mapped, §4.4/Step 040).
- TBR log `a3/27` — 10 records, completed TBRs (§4.5).
- Basal change log `a3/02` — 47 records (profile snapshot + timestamp), §4.6 (🟢).
- Simple/extended bolus: off6/off8 = requested/delivered (Step 031); bolus cancellation — `a1/02 00 00` (two observations).

---

## Step Log

### Step 000 — Project skeleton, methodology, recording the license agreement
- **Date:** 2026-09-16.
- **What was done:** created the repository skeleton (README with project rules, skeletons for
  `RESEARCH_EN.md`, `PROTOCOL_EN.md`, `MATERIALS_EN.md`), the test-bench connection skill `apex-device`,
  recorded the version of the app's license agreement (`user_agreement.md`).
- **Materials:** none (organizational step).
- **Protocol findings:** none.

### Step 001 — Pump connection: GATT topology, MTU, enabling notifications
- **Date/time:** 2026-09-16, connection ~16:22 (capture 16:21–16:25).
- **Research:** `etap-A-transport-gatt`.
- **Action:** the user connected the pump via the app in the standard way. Method: the **pump's
  serial number** was entered in the app (value not given), after which the pump appeared in the
  selection list; tapping the row for the pump with that serial number initiated the connection.
  Next came the "Devices" screen with the pump's status. The app was operated manually; no custom
  frames were sent to the pump (observation only).
- **Materials:** No. 1 (HCI capture; only the pump's address was observed among identifiers),
  No. 2 (screenshot of "Devices", serial number masked).
- **Parsing:** `tools/hci_topology.py` on material No. 1.
- **Observations:**
  - Pump GATT server: services `0x1800`/`0x1801`/`0x180A` and vendor services `0xFFE0`, `0xFFE5`,
    `0xFF90`, `0xFFC0` (handle ranges — PROTOCOL_EN.md §1.1).
  - MTU: request `517` → granted `251`.
  - Pump response channel: `0xFFE4` (`0x001C`, NOTIFY) — 40 notifications per session; enabled
    by writing `01 00` to CCCD `0x001D`.
  - Command channel: `0xFFE9` (`0x0021`, WRITE/WRITE_NR).
  - Channel `0xFFC0`: `0xFFC1` (WRITE) + `0xFFC2` (NOTIFY, CCCD `0x0045` enabled with `01 00`,
    1 notification) — presumably authorization; detailed in Stage B.
  - Radio↔screen cross-check: the screen showed firmware `1.1.1`, protocol version `4.12`, battery
    `1.36 V`/`46%`, status "Unlocked". Matching these values to specific response frames is a task
    for Stage D.
- **Finding:** the transport-layer topology is recorded in PROTOCOL_EN.md §1 with status
  🟡 assumption (one measurement). For 🟢, a repeat capture with different characteristics is
  required (reconnection / after a phone reboot) — the topology should match.
  **→ refined:** Step 003 — a second connection matched byte-for-byte → 🟢.

### Step 002 — Provenance of the license agreement (screenshots)
- **Date/time:** 2026-09-16, 16:15–16:17 (taken by the user).
- **Research:** `provenance-user-agreement`.
- **Action:** a set of screenshots of the Erwin Blueberry app's license agreement screen was saved
  (scrolled through in full). Organizational/provenance step, no exchange with the pump.
- **Material:** No. 3 — 33 frames (Parts 1–21), covering the text of `user_agreement.md`. No
  personal data found in the frames, no masking required. The archive includes a manifest
  `SHA256SUMS.txt` with the SHA-256 of each frame; the SHA-256 of the manifest itself is recorded
  in the registry as an integrity anchor.
- **Compliance check:** the first frame is the title and start of Part 1; the last is Part 21
  (force majeure); matches the text of `user_agreement.md`.
- **Finding:** the version of the agreement recorded in `user_agreement.md` (app 1.0 Build 489
  Patch1) is confirmed by screenshots from an actual instance of the app (material No. 3).

### Step 003 — Reconnection: topology confirmation (Stage A) and Bluetooth-password authorization (Stage B)
- **Date/time:** 2026-09-16; disconnection 16:51:21, reconnection 16:52:02.
- **Research:** `etap-B-avtorizaciya`.
- **Action:** the user disconnected the pump using the app's standard function ("Auxiliary
  functions" → "Danger zone" → "Disconnect pump"), then reconnected. On connecting, in addition to
  the serial number, the app requested the **pump password** (Bluetooth password), taken from the
  pump's "STATUS" menu, the `B/P:` line right after `S/N:`. Serial number and password values are
  not given. The app was operated manually; no custom frames were sent to the pump.
- **Materials:** No. 4 (HCI, both sessions), No. 5 (reconnection screenshots; PIN and serial number
  masked), No. 6 (photo of the pump's "STATUS" screen; S/N and B/P masked).
- **Parsing:** `tools/hci_topology.py` and `tools/hci_auth.py` on material No. 4.
- **Stage A (topology confirmation):** the reconnection session (conn 0x0005, 16:52) performed full
  GATT discovery; services, characteristics, handles, MTU (517→251), and CCCD enable order matched
  Step 001 (conn 0x0003) byte-for-byte. Two measurements with different characteristics (different
  sessions/time, after a standard disconnect cycle) → topology in PROTOCOL_EN.md §1 upgraded to 🟢.
- **Stage B (authorization):** sequence on connection: (1) `01 00` to CCCD 0x0045 (verdict channel
  0xFFC2); (2) writing the password to 0xFFC1 (0x0041) — 12 bytes; (3) verdict on 0xFFC2 (0x0044) —
  1 byte, `0x00` (success); (4) MTU 517→251; (5) `01 00` to CCCD 0x001D (response channel 0xFFE4);
  (6) commands. Password encoding: 12 bytes — six ASCII digits of the `B/P` string, written twice
  in a row (value not given). Radio↔screen cross-check: the ASCII digits over the air match the
  `B/P` string on the pump screen (material No. 6) — independent confirmation. Observed in both
  sessions → PROTOCOL_EN.md §3 with status 🟢.
- **Other (for future stages):** command frames (`0xFFE9`, starting with `0x35`, containing an
  identity block `APEX<serial>`) and response frames (`0xFFE4`, marker `0xAA`, carry no identity)
  are also visible in the capture. Parsing the frame format and catalog — Stages C-E.
- **Finding:** PROTOCOL_EN.md §1 → 🟢; §3 (authorization) filled in, status 🟢.

### Step 004 — Hypotheses on frame format and objects (analysis of material No. 4)
- **Type:** analytical step (no new materials collected; analysis of material No. 4).
- **Tools:** `tools/hci_frames.py` (frame collection, response reassembly by length, CRC check),
  `tools/hci_auth.py`, `tools/hci_topology.py`.
- **Observations (all — 🟡 assumption, one capture):**
  - **Frame format.** Command: `35 | length | field2 | class | code | index | APEX+serial | [payload] | CRC`.
    Response: `AA | length | field2 | class(echo) | code(echo) | record index | data | CRC`.
    Responses carry no identity. Details — PROTOCOL_EN.md §2.
  - **CRC-16/MODBUS**, little-endian — verified on 406 frames in both directions (12 "bad" ones —
    periodic `a5/03`, see §2.5).
  - **Timestamp** — 6 bytes `YY MM DD HH MM SS` (hex): `1a 09 10 10 16 14` = 2026-09-16
    16:22:20, matches the capture time (independent "radio↔time" cross-check).
  - **Object catalog** (class `a3`): `31` status initialization, `00` main status, `0c`/`0a`
    brief status/settings, `0b` schedule, `08` table of 8 records (presumed basal profiles), `07`
    large table (presumed bolus settings), `21` and `26` — logs of 10 records with timestamps.
    Class `a5/03` — periodic (presumed keepalive). Details — PROTOCOL_EN.md §4.
  - **Control** (class `a1`): `31` — set pump time (payload = timestamp equal to connection time
    → synchronization); acknowledgment `a1/55`. PROTOCOL_EN.md §5.
  **→ refined:** frame format and CRC 🟢 — Step 028 (1779 commands and 6284 responses in the window);
  `a1/31` — 🟡 (one observation in the window); acknowledgment `a1/55` 🟢 — Step 028.
- **Confidence:** status of all findings — 🟡, since obtained from a single capture. Plan to reach
  🟢 (rule 8): a second capture with **different values** — different time (checking timestamp
  field positions), different basal profile/bolus settings (linking objects `08`/`07`), and
  cross-checking status numeric fields (`00`/`0c`) against the pump screen (battery, reservoir,
  basal).
- **Finding:** PROTOCOL_EN.md §2, §4, §5 filled with hypotheses (🟡). Frame format and CRC — priority
  for confirmation in Stage C.
  **→ refined:** frame format 🟢 (Step 028); commands and fields — Steps 009–027, tables in
  PROTOCOL_EN.md §4–§5.

### Step 005 — Map of app capabilities and the pump's "pulse"
- **Date/time:** 2026-09-16, ~17:45 (menu screenshots).
- **Research:** `app-menu-map`; pulse analysis — from material No. 4.
- **Action:** the user went through the app's menus and took screenshots (material No. 7). No
  exchange with the pump was needed for the menu map. Pulse analysis — parsing of previously
  collected material No. 4.
- **Materials:** No. 7 (5 menu screenshots); No. 4 (HCI, for the pulse).
- **Menu map:** compiled in `APP_MENU.md` — screens Home/History/Devices/Bolus settings/Basal
  settings/Auxiliary functions; extraction groups G1–G6 identified.
- **Hypothesis corroboration (🟡):** the "Basal settings" menu (profile A…, 48-interval chart)
  indirectly confirms that object `a3/08` is basal profiles (8 × 48). Home screen buttons
  (Food/Bolus/Advice/TBR/Stop) and "Danger zone" define the list of control commands for Stage E.
  **→ refined:** `a3/08` record 00 equals command `a1/00` (write profile) byte-for-byte — Step 026 (🟢).
- **Pump "pulse" (`a5/03`):** `tools/hci_pulse.py` on material No. 4 — 12 frames with a **strict
  180.0 s step**, payload **identical** in all (`aa0600a5030080c2`), CRC-16/MODBUS valid. This is
  an unsolicited periodic heartbeat from the pump. Clarified §2.5: length of `a5` = `total − 2`.
- **Confidence:** the pulse was obtained from a single capture (🟡); confirmation — a second
  capture (group G6, holding the connection for ≥10 min): the period and payload constancy should
  repeat.
  **→ refined:** Step 028: 250 frames over a 12.5 h window, period 180.0 ± 0.2 s, payload unchanged → 🟢.
- **Finding:** `APP_MENU.md` added; PROTOCOL_EN.md §4 (a5/03 heartbeat, a3/08 basal profiles) and §2.5
  clarified; extraction group plan G1–G6 defined.

### Step 006 — G1 Status: fields of objects `a3/00` and `a3/0c`
- **Date/time:** 2026-09-16, ~18:01–18:02.
- **Research:** `etap-D-g1-status`.
- **Action:** the user opened the "Home" and "Devices" screens and took screenshots; the pump was
  connected, the app was polling status. HCI capture taken immediately afterward. Control was
  manual, no custom frames were sent.
- **Materials:** No. 8 (HCI, status 18:01–18:02), No. 9 (2 screenshots: Home IOB 1.87; Devices
  battery 1.36 V/46%, serial number masked). Parsing: `tools/hci_frames.py` + field analysis.
- **Observations:**
  - **Timestamp** `a3/00` off44–49 = `1a 09 10 12 02 00` = 2026-09-16 18:02:00 — matched the
    clock. Considering the series of values from Step 004 (16:22:20…16:29:00) — **🟢**.
  - **Current basal** `a3/00` off76 (u16LE) = `20`; 20 × **0.025 U** = 0.5 U/h — matches the
    screen (basal 0.5 U/h). Value stable → **🟡** (to be confirmed by changing basal, G2/G5).
    **→ refined:** off76 — current profile interval rate 🟢 — Steps 026 (screen 0.9 U/h), 027 (0.725 U/h; `ff ff` on stop).
  - **Battery voltage** `a3/0c` byte[3] = `136`; ×0.01 = 1.36 V — matches the screen at 18:01
    (g1_02) and the pump photo at 16:52 (material No. 6), two sessions → **🟢**.
  - **IOB** (1.87 U at 18:01; 2.33 at 17:44) not found in `a3/00` at any scale →
    presumably **computed by the app** from the bolus history (🟡).
  - **Reservoir** (101.7 U) not localized in `a3/00`/`a3/0c` — open question (candidate `a3/07`).
    **→ refined:** found: `a3/00` off52..55, 0.001 U — Step 007 (🟢).
  - **Dosing step of 0.025 U** confirmed over the air (basal 20 steps = 0.5 U/h).
- **Confidence:** timestamp and battery voltage — 🟢 (series of values/two sessions + radio↔screen
  cross-check). Basal — 🟡 (value did not change); IOB/reservoir — open.
  **→ refined:** basal 🟢 — Steps 026–027; reservoir 🟢 — Step 007; IOB not found on air (🟡).
- **Finding:** PROTOCOL_EN.md §4.1–4.3 filled in. Next: G2 (basal profile change) will lock in basal
  and object `a3/08`; reservoir search — in `a3/07` (G3).

### Step 007 — G1: classifying changing fields of `a3/00` (analysis of materials No. 4/No. 8)
- **Type:** analytical step (no new materials).
- **Research boundary:** only frames **from 16:34** are considered — the milestone from which
  counts and captures are kept. Data before 16:34 is valid but reflects user operations (boluses,
  etc.) performed before the research began and not part of documented steps; they set the pump's
  initial state but are not our actions.
- **Framework (set by the user):** fields changing over time are timestamps or insulin quantities
  (reservoir, delivery counter, basal); fields changing after operations are states.
- **Results (window ≥16:34):**
  - **Reservoir** = off52 (uint32 LE), unit 0.001 U: **16:52:06 → `101700` = 101.7 U**
    (matches the pump photo, material No. 6); 18:05 → 101050 ≈ 101 U (Home, material No. 9) → **🟢**.
  - **Delivery counter** = off16 (step 0.025 U): over the clean window 16:52→18:05 an increase of
    +0.625 U ≈ the reservoir decrease (0.65 U) at basal with no operations → 🟡.
    **→ refined:** unit 0.025 U 🟢 — Step 024 (increase at 0.5 / 0.9 / 6.0 U/h).
  - **Basal** off76 = 20 (0.5 U/h, step 0.025) — stable → 🟡.
    **→ refined:** 🟢 — Steps 026–027.
  - **Timestamp** off44-49 → 🟢; **battery voltage** `a3/0c[3]`=136=1.36 V → 🟢 (Step 006).
  - **State fields** off50/51/80/82/84/86: non-zero until ~16:47, then zero — a decaying "tail" of
    user operations **before 16:34**; not entered into the pump's field catalog.
- **CORRECTION to the earlier version of Step 007.** The following were removed as erroneous:
  (1) attributing state fields to "boluses performed in the research" — boluses before 16:34 were
  performed by the user outside documented steps; (2) the conclusion of "internal convergence" over
  the interval 16:22→18:05 — the analysis was mistakenly extended into the pre-research period. The
  former "open question" about the reservoir-decrease discrepancy is withdrawn: in the clean window
  (after the pre-16:34 operations decayed, ~16:47), the reservoir decrease is consistent with the
  basal.
- **Methodological correction (project rule):** extraction by groups is analyzed strictly within
  the research window (**from 16:34**) and within the window of the corresponding controlled
  capture, not across the entire log history.
- **Finding:** PROTOCOL_EN.md §4.1 brought to the window ≥16:34: reservoir 🟢; delivery counter and
  basal 🟡; state fields attributed to pre-research context.
  **→ refined:** counter 🟢 — Step 024; basal 🟢 — Steps 026–027; "state fields" before 16:47 — a
  TBR started before the window (Step 024).

### Step 008 — Interim object-parsing map (`OBJECTS_EN.md`)
- **Type:** analytical/instrumental step (no new materials).
- **What was done:** added `tools/object_map.py` and the document `OBJECTS_EN.md` — for each response
  object (`a3/00,0c,31,0a,0b,08,07,21,26`, `a5/03`) a word-by-word map of the payload with raw
  values, a "constant/variable" marker, and the current interpretation (🟢/🟡/🔲). Goal — so that
  findings can be checked against raw data rather than taken on faith.
- **New candidates in `a3/00`** (cross-check with app screens, material No. 7): off24 `320` → 8.0 U =
  "Maximum basal" (menu_04); off26 `480` → 12.0 U = "Maximum bolus" (menu_03). Status 🟡
  — confirmation: change the limit in the app and see the field change.
  **→ refined:** off26 🟢 — Step 009; off24 🟢 — Step 010.
- **Parsing `a3/00`:** 18/88 bytes (timestamp 🟢, reservoir 🟢, delivery counter 🟡, basal 🟡,
  max. basal/bolus 🟡). Other constants (off0=259, off8=2826, off14=150, off20=100, off28=140,
  off30=76, off32=92, off78=6402) — not parsed, candidates for settings/limits (checked by changing
  in the app).
  **→ refined:** constants parsed in Steps 013–027 (off0 — hypothesis); current status — PROTOCOL_EN.md §4.1.
- **Note:** objects `08/07/21/26/0a/0b/31` were read by the app on connection before 16:34 —
  their maps are given from pre-research frames and require a repeat capture within the window.
- **Finding:** `OBJECTS_EN.md` — a working map for further field parsing.

### Step 009 — G3/E: confirming "max. bolus" and the settings-write command `a1/32`
- **Date/time:** 2026-09-16, ~19:53 (after the user changed a setting).
- **Research:** `etap-E-zapis-nastroek`.
- **Action:** the user set **maximum bolus to 12.3** in the app (was 12.0). The app wrote the
  setting to the pump and re-read status. HCI capture — material No. 10.
- **Results:**
  - **`a3/00` off26 = 492** (was 480); ×0.025 = **12.3 U** (was 12.0). Second measurement with a
    different value → **maximum bolus confirmed (🟢)**.
  - Control command **`a1/32`** (write settings): payload ends with `40 01 ec 01` =
    max. basal 320 (8.0 U) + max. bolus 492 (12.3 U). I.e. a1/32 carries a settings block matching
    the `a3/00` constants. → **🟢** for max. bolus display; a1/32 entered into §5.
  - **`a1/31`** (set time): two different timestamp values were observed (16:22:20 and
    16:52:06) → **🟢**.
  - Corroboration of off24 (max. basal 320=8.0): present in the a1/32 block (value before max.
    bolus), but the value itself did not change → remains 🟡 until the limit is changed.
    **→ refined:** 🟢 — Step 010 (8.0→7.7).
- **Confidence:** max. bolus — 🟢 (two values 12.0/12.3 + same in command a1/32). Commands
  a1/31, a1/32 — 🟢. a1/33, a1/34 — 🟡 (purpose not established).
  **→ refined:** `a1/31` — 🟡: one observation in the window, 16:22:20 is before the window
  (Step 028); `a1/34` — sound mode and sound step 🟢 (Steps 011, 016); `a1/33` — not established.
- **Finding:** PROTOCOL_EN.md §4.1 (off26 🟢), §5 (a1/31, a1/32 🟢); OBJECTS_EN.md regenerated.

### Step 010 — confirming "max. basal" (off24)
- **Date/time:** 2026-09-16, ~20:08. **Research:** `etap-E-zapis-nastroek`. **Material:** No. 11 (HCI).
- **Action:** the user set **maximum basal to 7.7** (was 8.0).
- **Result:** `a3/00` off24: 320 → **308** (×0.025 = 7.7 U); command `a1/32` shows `34 01`
  (308) at the max. basal position. Two values (8.0/7.7) → **off24 = maximum basal 🟢**.
- **Finding:** PROTOCOL_EN.md §4.1 (off24 🟢); OBJECTS_EN.md regenerated; the settings block a1/32 —
  the last two u16 (max. basal, max. bolus) confirmed.

### Step 011 — Series of bolus/sound settings: fields of commands `a1/32` and `a1/34`
- **Date/time:** 2026-09-16, 20:16–20:18. **Research:** `etap-E-nastroiki-boljus`.
  **Materials:** No. 12 (HCI, series), No. 13 (4 screenshots "Bolus settings").
- **Method:** the user changed settings one by one; the sequence of `a1/32`/`a1/34` commands was
  extracted from the log, differences between neighboring commands were matched against the
  sequence of actions and screenshots.
- **Actions ↔ commands (all confirmed by value change + screen):**
  - extended bolus ON → `a1/32` byte[6] 00→01 → 🟢;
  - bolus speed Normal→Low → `a1/32` byte[0] 00→01 → 🟢 (partial enum);
    **→ refined:** reverse direction — Step 014; byte[0] — a bit field, fully parsed — Steps 020–023.
  - sound mode ON → `a1/34` byte[0] 00→01 → 🟢;
  - sound mode step 5.0→0.5→0.1 → `a1/34` byte[1] 03→01→00 (index; 3 values) → 🟢.
    **→ refined:** fourth menu item: index `2` = 1.0 U — Step 025.
- **Observation:** with every setting change the app sends both blocks `a1/32` and `a1/34`;
  also observed `a1/12` (`12 00 00`) and `a1/05` (no payload) — purpose not established (🟡).
  **→ refined:** `a1/05` — cancel TBR 🟢 (Steps 024, 026); `a1/12` not observed within the window (Step 028).
- **Confidence:** for each field — two states (before/after) + cross-check with a screenshot (s3/s4,
  material No. 13). Sound step — 3 values.
- **Finding:** PROTOCOL_EN.md §5.1 (block `a1/32`) and §5.2 (block `a1/34`) filled in.

### Step 012 — BG reminder (`a1/32` flags) and bolus presets (`a1/11`)
- **Date/time:** 2026-09-16, 22:42–22:43. **Research:** `etap-E-gk-presety`.
  **Materials:** No. 14 (HCI), No. 15 (2 screenshots "Bolus presets").
- **BG reminder:** `a1/32` byte[6] `01→03`. Since bit0 = extended bolus, byte[6] is a
  **bit field**: bit0=extended bolus, bit1=BG reminder → 🟢.
- **Bolus presets — command `a1/11`:** a list of u16LE (step 0.025 U) by slot. Final
  `84 00 54 00 50 00 05 00 03 00 …` = 3.3 / 2.1 / 2.0 / 0.125 / 0.075 / 0.0 U — exact match
  with the "Bolus presets" screen (material No. 15) → 🟢. On edit, the entire list is resent.
- **Other (Stage E):** further in the capture — commands `a1/02` (`01 08 00 00`, `01 02 20 00`…),
  `a1/12` (`0c/12/14 00 00`); purpose not established, requires a separate description of actions.
  **→ refined:** `a1/02` — start TBR 🟢 (Step 024).
- **Finding:** PROTOCOL_EN.md §5 (a1/11), §5.1 (byte[6]=flags), §5.3 (presets) filled in.

### Step 013 — Series of "Advanced settings" (`a1/32`): partial attribution
- **Date/time:** 2026-09-16, 23:12–23:21. **Research:** `etap-E-dop-nastroiki`.
  **Materials:** No. 16 (HCI + `a1_32_evolution.txt`), No. 17 (9 screenshots).
- **Method and caveat:** the user changed a large series of settings in a row (some — with
  rollbacks) without capturing between changes. Therefore "byte↔setting" attribution is reliable
  only where **the set number matched the byte**; flag/enum bytes are not disambiguated one by
  one — they cannot be guessed.
- **Confirmed (🟢, by value match):**
  - byte[3] = pump auto-off, hours (01→07 = 1→7 h);
  - byte[4] = "insulin running out" threshold, units (0a→0d = 10→13);
  - byte[5] = "insulin running out" time, half-hours (0b→0d = 5:30→6:30);
  - bytes[8..9] = screen auto-off, ×0.1 s (150↔600 = 15↔60 s);
  - bytes[10..11] = daily dose limit, units (64→fa = 100→250).
- **Clarification:** byte[6] confirmed earlier (bit0 extended bolus, bit1 BG reminder); byte[0] —
  a bit field (bit0 = bolus speed, Step 011; higher bits — other switches, not disambiguated).
  **→ refined:** byte[0] fully parsed — Steps 020–023.
- **Not disambiguated (🟡):** byte[0] higher bits, byte[1], byte[2], byte[7] — correspond to
  switches/enums (keypad lock, language, brightness, alarm duration/type, dose limit on).
  Require one change with a separate capture each; raw data — in `a1_32_evolution.txt` (No. 16)
  and screenshots (No. 17).
  **→ refined:** disambiguated one change at a time: byte[1] — alarm signal type (Step 017),
  byte[7] — signal duration (018), byte[2] — brightness (019), byte[0]: `0x40` language (020),
  `0x20` limit (021), `0x04` auto-off (022), `0x02` keypad lock (023).
- **Methodological correction (important):** for flag/enum settings we make **one change — one
  capture**, otherwise unambiguous attribution is impossible.
- **Reflection in object `a3/00`:** the same settings are visible in the status object (checked
  against the series log): off14 (150↔600) = screen auto-off; off20 (100↔250) = daily dose limit;
  off28/30/32 = bolus presets (slots 1–3). Entered into `OBJECTS_EN.md` (a3/00: 28/88 bytes).
- **Finding:** PROTOCOL_EN.md §5.1 supplemented (5 fields 🟢); `OBJECTS_EN.md` (a3/00) updated;
  flags/enums — 🟡 with raw data preserved.
  **→ refined:** flags and enumerations disambiguated — Steps 017–023.

### Step 014 — Bolus speed Low→Normal: reverse direction, reflection in `a3/00`
- **Date/time:** 2026-09-16, ~23:46. **Research:** `etap-E-skorost-boljusa`.
  **Materials:** No. 18 (HCI), No. 19 (screenshot "Bolus settings" after the change).
- **Action:** the user switched "Bolus speed" from "Low" to "Normal" (one change).
- **Command `a1/32`:** the last command in the log differs from the previous one only in byte[0]:
  `01→00` (`…010200070b0d03029600fa003401ec01` → `…000200070b0d03029600fa003401ec01`). Together
  with Step 011 (`00→01`), bit0 is confirmed in both directions → 🟢.
- **Object `a3/00`:** comparing status before/after each `a1/32` command — after this command only
  off2 changes `1→0`; in Step 011's log (No. 12) for Normal→Low (20:16) — off2 `0→1`. No other
  off2 values appear in either log → **off2 = bolus speed (0=Normal, 1=Low)** 🟢. Adjacent off3
  is unrelated (it changed in the Step 013 series).
- **Screenshot:** the "Bolus settings" screen shows "Bolus speed — Normal" (No. 19).
- **Tool:** `tools/object_map.py` now outputs single-byte fields aligned to the u16 grid; also
  fixed an omission of a known field at an odd offset (in `OBJECTS_EN.md` for `a3/0c` the off3 row
  "battery voltage" was being absorbed by the `2..3` row).
- **Finding:** PROTOCOL_EN.md §4.1 (off2 🟢) and §5.1 (byte[0] bit0 — both directions); `OBJECTS_EN.md`
  (a3/00: 29/88, a3/0c: off3 row restored).

### Step 015 — Extended bolus and BG reminder OFF: flags `a1/32` byte[6] and `a3/00` off4
- **Date/time:** 2026-09-16 ~23:55 and ~23:59. **Research:** `etap-E-flagi-boljusa`.
  **Materials:** No. 20 (HCI), No. 21 (2 screenshots "Bolus settings", one after each change).
- **Actions (one change at a time, capture after each):** the user turned off "Extended bolus"
  (~23:55), then "BG reminder" (~23:59).
- **Command `a1/32`:** byte[6] `03→02` (bit0 cleared), then `02→00` (bit1 cleared); other bytes
  unchanged. With Steps 011/012 (enabling) both bits are confirmed in both directions → 🟢.
- **Object `a3/00`:** comparing status before/after each `a1/32` command — only off4 changes:
  | time | action | `a1/32` byte[6] | `a3/00` off4 |
  |---|---|---|---|
  | 20:16 (Step 011, No. 12) | extended bolus ON | `00→01` | `0→2` |
  | 22:42 (Step 012, No. 14) | BG reminder ON | `01→03` | `2→6` |
  | ~23:55 | extended bolus OFF | `03→02` | `6→4` |
  | ~23:59 | BG reminder OFF | `02→00` | `4→0` |
  → **off4 — bit field: `0x02` = extended bolus, `0x04` = BG reminder** 🟢. In `a3/00` the bits
  are one position higher than in the command; bit0 (`0x01`) in off4 was not observed (values only
  0/2/4/6).
- **Screenshots:** No. 21 — both switches off in the corresponding order.
- **Finding:** PROTOCOL_EN.md §4.1 (off4 🟢) and §5.1 (byte[6] — turning off); `OBJECTS_EN.md` (a3/00: 30/88);
  `tools/object_map.py` KNOWN table supplemented.
- **Addendum (2026-09-17, per user's remark):** off4 of `a3/00` = byte[6] of `a1/32` × 2. Checked
  against logs No. 12 and No. 36: pairs (byte[6], off4) — only (0,0), (1,2), (3,6), (2,4), no
  exceptions; all four off4 values observed: `00` neither, `02` extended bolus, `04` BG reminder,
  `06` both. "Extended bolus" — enables the extended and dual-wave bolus (per the user).

### Step 016 — Sound mode OFF: `a1/34` byte[0] and reflection in `a3/0c` off4/off5
- **Date/time:** 2026-09-17, ~00:11. **Research:** `etap-E-zvukovoi-rezhim`.
  **Materials:** No. 22 (HCI), No. 23 (screenshot "Bolus settings" after the change).
- **Action:** the user turned off "Sound mode" (one change). On the screen, turning it off hides
  the "Sound mode step" line.
- **Command `a1/34`:** byte[0] `01→00`, other bytes unchanged (byte[1]=`00`, step 0.1 retained).
  With Step 011 (`00→01`) confirmed in both directions → 🟢.
- **Object `a3/0c`:** there are no sound settings in `a3/00` (unchanged after `a1/34` commands).
  In the brief status `a3/0c`, off4/off5 change only following `a1/34` commands:
  | time | command `a1/34` [0..1] | `a3/0c` off4..5 |
  |---|---|---|
  | 20:17 (Step 011, No. 12) | `01 03` (sound ON) | `00 03` → `01 03` |
  | 20:17–20:18 (Step 011) | `01 01`, `01 00` (step 5.0→0.5→0.1) | `01 01`, `01 00` |
  | 00:11 | `00 00` (sound OFF) | `00 00` (00:12) |
  → **off4 = sound mode (0/1)** 🟢 (both directions); **off5 = sound mode step, index as in
  `a1/34` byte[1]** 🟢 (3 values, same as the command in Step 011).
- **Finding:** PROTOCOL_EN.md §4.2 (off4, off5 🟢) and §5.2 (turning off, reflection in `a3/0c`);
  `OBJECTS_EN.md` (a3/0c: 3/20); `tools/object_map.py` KNOWN table supplemented.

### Step 017 — Alarm signal type: `a1/32` byte[1] and `a3/00` off1
- **Date/time:** 2026-09-17, ~00:18 and ~00:23. **Research:** `etap-E-vid-signala`.
  **Materials:** No. 24 (HCI), No. 25 (2 screenshots "Alarm signals"); cross-check — No. 16/No. 17 (Step 013).
- **Actions (one change at a time, capture after each):** the user switched "Signal type" to
  "Vibration" (~00:18), then to "Sound" (~00:23). The menu offers three options: Sound, Vibration,
  Sound and vibration (screenshot No. 25/01); per the user, indices follow menu order.
- **Command `a1/32`:** byte[1] `02→01` (Vibration), then `01→00` (Sound); other bytes unchanged.
- **Object `a3/00`:** off1 `2→1` (00:19), `1→0` (00:24) — only this byte.
- **Third value:** in Step 013 byte[1] became `02` at 23:17 and held until 00:18; screenshot
  No. 17 `adv_09` (23:19) shows "Sound and v…" → `2` = Sound and vibration.
- **Result:** **byte[1] of `a1/32` = off1 of `a3/00` = alarm signal type: 0=Sound, 1=Vibration, 2=Sound
  and vibration** 🟢 — all three values cross-checked screen↔air, matches menu order.
- **Incidental cross-check:** on screenshot No. 25/02 "Insulin running out — units" = 11 U, in the
  command byte[4]=`0b` (=11) — consistent with Step 013.
- **Finding:** PROTOCOL_EN.md §4.1 (off1 🟢) and §5.1 (byte[1] from 🟡 to 🟢); `OBJECTS_EN.md` (a3/00: 31/88).

### Step 018 — Alarm signal duration: `a1/32` byte[7] and `a3/0c` off2
- **Date/time:** 2026-09-17, ~00:29. **Research:** `etap-E-dlitelnost-signala`.
  **Materials:** No. 26 (HCI), No. 27 (screenshot with menu options); cross-check — No. 17 `adv_09` (Step 013).
- **Action:** the user switched "Signal duration" Short→Long (one change).
  Menu: Long, Normal, Short (No. 27); per the user, indices follow menu order.
- **Command `a1/32`:** byte[7] `02→00`, other bytes unchanged.
- **Object `a3/0c`:** off2 `2→0` (00:29). No changes in `a3/00`.
- **Byte history from the log (No. 26):**
  | time | `a1/32` byte[7] | `a3/0c` off2 | screen |
  |---|---|---|---|
  | 20:20 | — | `2` | (Short — see 00:25, No. 25/02) |
  | 23:15–23:16 (Step 013) | `1` | `1` | 23:19 "Normal…" (No. 17 `adv_09`) |
  | 23:20 (Step 013) | `2` | `2` | 00:25 "Short" (No. 25/02) |
  | 00:29 | `0` | `0` | 00:31 "Long" (No. 27) |
- **Result:** **byte[7] of `a1/32` = off2 of `a3/0c` = alarm signal duration: 0=Long, 1=Normal,
  2=Short** 🟢 — all three values cross-checked screen↔air, matches menu order.
- **Clarification to Step 013:** byte[7] was previously a candidate for "duration/type of alarm"
  (🟡) — closed. Byte[2] is unrelated to duration: it changed `04→00` at 23:21, while byte[7]
  remained `2` (Short) — byte[2]'s purpose was not established, 🟡.
  **→ refined:** byte[2] — screen brightness 🟢 — Step 019.
- **Finding:** PROTOCOL_EN.md §4.2 (off2 🟢) and §5.1 (byte[7] from 🟡 to 🟢); `OBJECTS_EN.md` (a3/0c: 4/20).

### Step 019 — Pump screen brightness: `a1/32` byte[2] and `a3/00` off3
- **Date/time:** 2026-09-17, ~00:41. **Research:** `etap-E-yarkost-ekrana`.
  **Materials:** No. 28 (HCI), No. 29 (screenshot with menu options); cross-check — No. 17 `adv_01`, `adv_05` (Step 013).
- **Action:** the user switched "Screen brightness" (Advanced settings) 10%→50% (one change).
  Menu: 10, 30, 50, 60, 80, 100% (No. 29).
- **Command `a1/32`:** byte[2] `00→02`, other bytes unchanged.
- **Object `a3/00`:** off3 `0→2` (00:41).
- **Cross-checking three values against the screen:**
  | time | `a1/32` byte[2] | `a3/00` off3 | screen |
  |---|---|---|---|
  | 23:12 (Step 013) | `00` | `0` | 10% (No. 17 `adv_01`) |
  | 23:15 (Step 013) | `04` | `4` | 80% (No. 17 `adv_05`) |
  | 00:41 | `02` | `2` | 50% (No. 29) |
- **Result:** **byte[2] of `a1/32` = off3 of `a3/00` = screen brightness, index of position in the
  menu** (0=10%, 1=30%, 2=50%, 3=60%, 4=80%, 5=100%) 🟢 — three values cross-checked screen↔air
  and match menu positions; values 1/3/5 are inferred from menu order.
- **Incidentally (settings restored ~00:37–00:38):** `a3/0c` off2 `0→2` (duration → Short) and
  `a1/32` byte[1] `0→1` (type → Vibration) — consistent with Steps 017/018. Also, at 00:38 bit
  `0x02` of byte[0] was toggled on and off (`a3/00` off5 `0→1→0`) — the user's action needs
  clarification, 🟡.
  **→ refined:** bit `0x02` — keypad lock 🟢 — Step 023.
- **Finding:** PROTOCOL_EN.md §4.1 (off3 🟢) and §5.1 (byte[2] from 🟡 to 🟢); `OBJECTS_EN.md` (a3/00: 32/88).

### Step 020 — Pump language: `a1/32` byte[0] bit `0x40` and `a3/00` off50
- **Date/time:** 2026-09-17, ~00:44. **Research:** `etap-E-yazyk-pompy`.
  **Materials:** No. 30 (HCI), No. 31 (screenshot with menu options); cross-check — No. 17 `adv_01`, `adv_05` (Step 013).
- **Action:** the user switched "Pump language" Russian→English (one change). Menu: Russian,
  English (No. 31).
- **Command `a1/32`:** byte[0] `00→40` — bit `0x40` set, other bytes unchanged.
- **Object `a3/00`:** off50 `0→1` (00:46).
- **History from the log (No. 30):**
  | time | `a1/32` byte[0] & `0x40` | `a3/00` off50 | screen |
  |---|---|---|---|
  | before 23:14 | `0` | `0` | 23:12 "Russian" (No. 17 `adv_01`) |
  | 23:14 (Step 013) | `0x40` | `1` | 23:15 "English" (No. 17 `adv_05`) |
  | 23:20–23:21 (Step 013) | `0` | `0` | — |
  | 00:44–00:46 | `0x40` | `1` | 00:48 "English" (No. 31) |
- **Result:** **bit `0x40` of byte[0] of `a1/32` = off50 of `a3/00` = pump language: 0=Russian,
  1=English** 🟢 — both directions in the log, both values cross-checked with the screen.
- **Remainder of byte[0]:** bits `0x02`, `0x04`, `0x20` not yet disambiguated (candidates —
  keypad lock, auto-off, daily dose limit). In screenshot No. 31, auto-off and keypad lock are off,
  byte[0]=`40` — consistent.
  **→ refined:** `0x20` — Step 021, `0x04` — Step 022, `0x02` — Step 023.
- **Discrepancy to verify:** the Step 007 note attributes off50 to "state fields", non-zero until
  ~16:47; in log No. 12, off50=0 already at 16:22. The note was not changed, requires re-verification
  against Step 007's materials.
  **→ refined:** resolved: non-zero fields until 16:47 — a TBR started before the window; off50 —
  language (Step 024).
- **Finding:** PROTOCOL_EN.md §4.1 (off50 🟢) and §5.1 (byte[0] bit6 🟢); `OBJECTS_EN.md` (a3/00: 33/88).

### Step 021 — Daily dose limit: switch (`a1/32` byte[0] bit `0x20`, `a3/00` off13) and value 200
- **Date/time:** 2026-09-17, ~02:55. **Research:** `etap-E-limit-dozy`.
  **Materials:** No. 32 (HCI), No. 33 (screenshot); cross-check — No. 17 `adv_09` (Step 013), No. 25/02 (Step 017).
- **Actions:** the user set the pump language back to Russian (~02:53), then turned on "Daily dose
  limit" and set "Total daily dose" to 200 U (~02:55).
- **Commands `a1/32` (in order):** byte[0] `40→00` (language → Russian; `a3/00` off50 `1→0`) →
  byte[0] `00→20` (limit ON) → bytes[10..11] `fa 00→c8 00` (250→200). Each command changes only
  the indicated bytes.
- **Object `a3/00`:** off13 `0→1` (limit ON), off20 `250→200`.
- **History of bit `0x20` / off13:**
  | time | `a1/32` byte[0] & `0x20` | `a3/00` off13 | screen |
  |---|---|---|---|
  | 23:19 (Step 013) | `0x20` | `1` | 23:19 switch ON, 250 U (No. 17 `adv_09`) |
  | 23:20 (Step 013) | `0` | `0` | 00:25 switch OFF (No. 25/02) |
  | 02:55 | `0x20` | `1` | 02:56 switch ON, 200 U (No. 33) |
- **Result:** **bit `0x20` of byte[0] of `a1/32` = off13 of `a3/00` = "Daily dose limit" on/off** 🟢
  — both directions, both states cross-checked with the screen. The limit value (byte[10..11] /
  off20) — third data point, 200.
- **Allowed values (addendum, 03:03):** the "Total daily dose" menu — 50, 100, 150, 200, 250, 300 U
  (No. 33/02). The field stores **the number of units directly** (100/200/250 observed on air), not
  a menu index — unlike screen brightness (Step 019).
- **Remainder of byte[0]:** bits `0x02` and `0x04` not disambiguated (candidates — keypad lock,
  auto-off).
  **→ refined:** `0x04` — Step 022, `0x02` — Step 023.
- **Finding:** PROTOCOL_EN.md §4.1 (off13 🟢) and §5.1 (byte[0] bit5 🟢, byte[10..11] +200); `OBJECTS_EN.md` (a3/00: 34/88).

### Step 022 — Pump auto-off: switch (bit `0x04`, `a3/00` off6), time (off7); reflections off8/off9
- **Date/time:** 2026-09-17, ~03:11. **Research:** `etap-E-avtovykl-pompy`.
  **Materials:** No. 34 (HCI), No. 35 (menu screenshot); cross-check — No. 17 `adv_01` (Step 013), No. 31 (Step 020).
- **Actions:** the user turned on "Auto-off" and selected "Auto-off time" 5 h (~03:11).
  Just before that, at 03:11 in the log — a change of "Total daily dose" 200→150 (bytes[10..11]
  `c8 00→96 00`, `a3/00` off20 `200→150`); the user did not report this — noted as an observation.
- **Commands `a1/32`:** byte[0] `20→24` (bit `0x04` set), then byte[3] `07→05` (5 h).
- **Object `a3/00`:** off6 `0→1`, off7 `7→5` (03:12).
- **Cross-check of the entire history of `a3/00` off6..9 against `a1/32` fields (No. 34):**
  | time | `a1/32` [0]&`0x04`, [3], [4], [5] | `a3/00` off6..9 | screen |
  |---|---|---|---|
  | 22:41 | `0, 1, 10, 11` | `0, 1, 10, 11` | — |
  | 23:11–23:12 (Step 013) | `4, 1→7, 10, 11` | `1, 1→7, 10, 11` | 23:12 auto-off ON, 1 h (No. 17 `adv_01`) |
  | 23:17–23:18 (Step 013) | `4, 7, 13, 13` | `1, 7, 13, 13` | — |
  | 23:20 (Step 013) | `0, 7, 11, 13` | `0, 7, 11, 13` | 00:48 auto-off OFF, no time row (No. 31) |
  | 03:11 | `4, 5, 11, 13` | `1, 5, 11, 13` | 03:13 time menu, 5 h selected (No. 35) |
- **Result (🟢):** bit `0x04` of byte[0] = off6 = "Auto-off" on/off (both directions, both states on
  the screen); off7 = auto-off time, hours (values 1/7/5); off8 = "insulin running out" threshold,
  units (10/13/11); off9 = "insulin running out" time, half-hours (11/13) — each matches bytes
  [3]/[4]/[5] of the command, confirmed in Step 013.
- **Menu:** values 2–8 h are visible (No. 35); value 1 h was observed on screen at 23:12 (No. 17),
  the list is likely scrolled — full range not recorded.
- **Remainder of byte[0]:** only bit `0x02` not disambiguated (candidate — keypad lock; at 00:38
  the bit was toggled back and forth, `a3/00` off5 `0→1→0`).
  **→ refined:** Step 023.
- **Finding:** PROTOCOL_EN.md §4.1 (off6..9 🟢) and §5.1 (byte[0] bit2 🟢; byte[3] +5 h; limit +150);
  `OBJECTS_EN.md` (a3/00: 38/88).

### Step 023 — Keypad lock: `a1/32` byte[0] bit `0x02` and `a3/00` off5; range of "insulin running out — time"
- **Date/time:** 2026-09-17, ~03:23 (menu — 03:29). **Research:** `etap-E-blokirovka-klaviatury`.
  **Materials:** No. 36 (HCI), No. 37 (2 screenshots); cross-check — No. 17 `adv_01`/`adv_05` (Step 013), No. 31 (Step 020).
- **Actions (from the log ~03:23):** auto-off time 5→3 h (byte[3] `05→03`), auto-off OFF (byte[0]
  `24→20`), then **in one command** byte[0] `20→02`: `0x20` cleared (dose limit OFF) and `0x02` set.
  The user reported enabling keypad lock; on screen (No. 37/01) — lock ON, auto-off and limit OFF.
- **Attributing `0x02`:** in the command `20→02` two bits change; `0x20` is already confirmed as
  the limit (Step 021) and is off on screen → `0x02` = keypad lock.
- **History of bit `0x02` / `a3/00` off5 (No. 36; evolution No. 16):**
  | time | `a1/32` byte[0] & `0x02` | `a3/00` off5 | screen |
  |---|---|---|---|
  | 23:14:01 (Step 013) | `0x02` | `1` | 23:15 lock ON (No. 17 `adv_05`); 23:12 before that — OFF (`adv_01`) |
  | 23:21:01 (Step 013) | `0` | `0` | 00:48 lock OFF, byte[0]=`40` (No. 31) |
  | 00:38 | `0x02` → `0` | `1` → `0` | — (brief toggle) |
  | 03:23 | `0x02` | `1` (03:25) | 03:26 lock ON (No. 37/01) |
- **Result:** **bit `0x02` of byte[0] of `a1/32` = off5 of `a3/00` = "Keypad lock" on/off** 🟢. Byte[0]
  is now fully parsed: `0x01` bolus speed, `0x02` keypad lock, `0x04` auto-off, `0x20` dose limit,
  `0x40` language; bits `0x08`/`0x10`/`0x80` not observed.
- **"Insulin running out — time":** menu 02:00–12:00 in steps of 0:30 (per the user; on No. 37/02
  02:00–05:00 are visible). Field byte[5] / `a3/00` off9 stores **the number of half-hours**, not
  a menu index: `0b`=11 → 5:30, `0d`=13 → 6:30 (with an index from 02:00 it would have been 7 and
  9). Value range — `4`…`24`.
- **Finding:** PROTOCOL_EN.md §4.1 (off5 🟢; off9 range) and §5.1 (byte[0] 🟢 in full; byte[5] range);
  `OBJECTS_EN.md` (a3/00: 39/88).

### Step 024 — Temporary basal rate (TBR): commands `a1/02`, `a1/05` and fields of `a3/00`
- **Date/time:** 2026-09-17, 03:37 — 04:05. **Research:** `etap-E-vbs`.
  **Materials:** No. 38 (HCI, 2 rotation files), No. 39 (2 screenshots "Home").
- **User actions (one at a time, capture after each):**
  1. ~03:35 turned off keypad lock (`a1/32` byte[0] `02→00`);
  2. 03:37 TBR **6 U/h for 45 min** (screen 03:39: "00:44, 6 U/h", No. 39/01);
  3. 04:01 cancelled the TBR;
  4. 04:02 TBR **113% for 2:45** (screen 04:04: "02:45, 1 U/h", No. 39/02).
- **Commands (each — acknowledgment `a1/55 0000`):**
  | time | command | payload | decoding |
  |---|---|---|---|
  | 03:37 | `a1/02` | `01 03 f0 00` | type `01` (U/h) · `03`×15 = 45 min · `240`×0.025 = 6.0 U/h |
  | 04:01 | `a1/05` | — | cancel TBR |
  | 04:02 | `a1/02` | `00 0b 71 00` | type `00` (%) · `0b`=11×15 = 165 min = 2:45 · `113`% |
- **Object `a3/00`:**
  | time | off51 | off80 | off82 | off84 | off86 | off76 |
  |---|---|---|---|---|---|---|
  | before 03:37 | 0 | 0 | 0 | 0 | 0 | 36 |
  | 03:37–03:59 | 1 | 240 | 1 | 45 | 0→22 | 36 |
  | 04:01 (after `a1/05`) | 0 | 0 | 0 | 0 | 0 | 36 |
  | 04:03–04:05 | 1 | 40 | 0 | 165 | 0→2 | 36 |
- **Result:**
  - `a1/02`: byte[0] — **TBR type** (`00` percent, `01` U/h); byte[1] — **duration in 15-min steps**;
    bytes[2..3] — **value, meaning depends on type** (U/h ×0.025 or %). Two different TBRs in the
    window, cross-checked with the screen → 🟢.
  - `a3/00` off51 — TBR active (1/0), off82 — type (= byte[0]), off84 — duration in minutes
    (= byte[1]×15), off80 — **resulting rate** in 0.025 U/h: for `01` = the value, for `00` =
    ⌊off76 × % / 100⌋ (36×113/100 = 40.68 → 40 = 1.0 U/h, screen "1 U/h") → 🟢; rounding rule —
    one data point, 🟡.
  - off86 — minutes since the TBR started (0→22 over 22 min; 0→2) → 🟡 (exact cross-check with the
    screen was not done).
  - `a1/05` — cancel TBR: after it the TBR fields reset to zero → 🟡 (one observation in the window).
    **→ refined:** second observation — Step 026 → 🟢.
- **Counter `a3/00` off16:** the increase matches delivery rate — +1 per 3 min at 0.5 U/h
  (20:20–23:56), ≈+2 per 3 min at 0.9 U/h (03:02–03:35), +12 per 3 min at TBR 6.0 U/h (03:38–03:59)
  → unit 0.025 U 🟢. Reset at 00:00 (2777 → 1 by 03:02) — "per-day counter" 🟡 (one observation).
- **off76** does not change during a TBR (36 = 0.9 U/h) — this is the profile basal; 20→36 at
  midnight matches the schedule, not yet cross-checked, 🟡.
  **→ refined:** 🟢 — Steps 026, 027.
- **Clarification to Step 007:** an archive check (tools/verify_fields.py) showed that at the start
  of the window (16:35–16:47) a TBR was already running in `a3/00` (off51=1, off80=80 = 2.0 U/h,
  off84=30), started before the window; the "state fields, non-zero until ~16:47" are it. off50 is
  unrelated to them (pump language, Step 020).
- **Finding:** fields entered into registry `tools/fields.py`; tables PROTOCOL_EN.md §4.1/§5.4 are
  generated from the registry.

### Step 025 — Bolus presets: 8 slots `a1/11` and `a3/00` off28..43; sound mode step menu
- **Date/time:** 2026-09-17, 03:50–03:53. **Research:** `etap-E-presety-boljusa`.
  **Materials:** No. 40 (HCI), No. 41 (2 screenshots: presets, sound step menu).
- **Action:** the user filled bolus preset slots 4–8 (slots 1–3 set in Step 012).
- **Commands `a1/11`** (the whole list on every edit) → final `84 00 54 00 50 00 17 00 1d 00 16 00 1c 00 01 00`.
- **Cross-check with the screen (No. 41/01, 03:53):**
  | slot | interval | u16 | ×0.025 | screen |
  |---|---|---|---|---|
  | Breakfast A | 5:00–6:59 | 132 | 3.3 | 3.3 U |
  | Breakfast B | 7:00–9:59 | 84 | 2.1 | 2.1 U |
  | Lunch A | 10:00–11:59 | 80 | 2.0 | 2.0 U |
  | Lunch B | 12:00–14:59 | 23 | 0.575 | 0.575 U |
  | Dinner A | 15:00–17:59 | 29 | 0.725 | 0.725 U |
  | Dinner B | 18:00–21:59 | 22 | 0.55 | 0.55 U |
  | Night A | 22:00–23:59 | 28 | 0.7 | 0.7 U |
  | Night B | 00:00–4:59 | 1 | 0.025 | 0.025 U |
- **Object `a3/00`:** off28..43 — the same 8 u16 values after each command (checked against the
  archive, no discrepancies). Previously only slots 1–3 were described in `OBJECTS_EN.md`.
- **"Sound mode step" menu (No. 41/02, 03:50):** 0.1 / 0.5 / 1.0 / 5.0 U. Index = position in the
  menu: `2` = 1.0 U — this index was skipped in Step 011's description ("not observed"); corrected
  per the user's remark.
- **Finding:** 8 slots 🟢; sound mode step — 4 values by menu. Fields in registry `tools/fields.py`.

### Step 026 — Second TBR cancellation; writing basal profile `a1/00` → `a3/08`
- **Date/time:** 2026-09-17, 04:40–04:47. **Research:** `etap-E-bazal-profil`.
  **Materials:** No. 42 (HCI), No. 43 (screenshot "Home", 04:42).
- **User actions:** 04:40 cancelled TBR (113%); 04:44 changed the basal profile (intervals from
  05:00).
- **TBR cancellation:** `a1/05` at 04:40:41 → acknowledgment `a1/55 0000`; in `a3/00` at 04:40:44
  off51/80/82/84 → 0. Second observation in the window (first — 04:01, Step 024) → `a1/05` = cancel
  TBR 🟢. Screen at 04:42 (No. 43): "Basal 0.9 U/h".
- **Profile write:** `a1/00` at 04:44:44, payload 96 bytes = 48 × u16LE (0.025 U/h), acknowledgment
  `a1/55 0000`: 00:00–04:59 `36` (0.9) · 05:00–07:59 `29` (0.725) · 08:00–15:59 `40` (1.0) ·
  16:00–23:59 `20` (0.5). Reading `a3/08` before and after: **only record 00** changed, its 96
  bytes are byte-for-byte **equal** to the command payload (previously `36` in slots 10–15).
  Records 1–2 filled with other values, 3–7 are zero.
- **`a3/00` off76:** values match the profile intervals: `20` (0.5) from 16:00, `36` (0.9) from
  00:00 (transition at 00:00:15), screen at 04:42 "0.9 U/h" → off76 = rate of the current
  half-hour interval of the profile 🟢. Transition to the new value `29` at 05:00 — Step 027.
- **Open:** which profile `a1/00` addresses and the correspondence of `a3/08` records to profiles
  A… — 🟡.
- **Finding:** registry `tools/fields.py` (off76 🟢; commands `a1/00` 🟢, `a1/05` 🟢); PROTOCOL_EN.md §4
  (row `a3/08`).

### Step 027 — Stopping and starting delivery: command `a1/21`; `a3/00` off76 = `ff ff`, off78..79 = stop time
- **Date/time:** 2026-09-17, 04:48–05:02. **Research:** `etap-E-stop-start`.
  **Materials:** No. 44 (HCI), No. 45 (2 screenshots "Home": stopped 04:51, started 05:01).
- **User actions:** 04:48 — "Stop" button on the Home screen; 05:00 — "Start" button.
- **Commands (acknowledgment `a1/55 0000` on each):** 04:48:43 `a1/21 01`; 05:00:07 `a1/21 00`.
- **Object `a3/00`:**
  | time | off76..77 | off78 | off79 | screen |
  |---|---|---|---|---|
  | before 04:48 | `24 00` (0.9 U/h) | `02` | `19` (25) | — |
  | 04:48:45 | `ff ff` | `04` | `30` (48) | 04:51 "Stopped, 0 U/h", "Bolus"/"TBR" locked, "Start" button |
  | 05:00:10 | `1d 00` (0.725 U/h) | `04` | `30` (48) | 05:01 "Basal 0.725 U/h", "Stop" button |
  Other bytes of `a3/00` and `a3/0c` did not change on stop/start (aside from the ongoing counter,
  reservoir, and voltage fluctuation 1.35↔1.36 V).
- **off76..77:** `ff ff` — delivery stopped; after start — the value of the current profile
  interval: 05:00 — the first interval, changed in Step 026 (`29` = 0.725 U/h), the screen matched
  → this also confirms the profile write.
- **off78..79 did not revert on start** → this is not a pump state field. `04 30` = **04:48** —
  stop time; the previous `02 19` = 02:25. Across all logs (including before the window): every
  `a1/21 01` writes the pump's current time to off78..79 (19:25, 19:57, 20:25, 20:57, 21:24, 21:57
  — Sep 15; 02:25 — Sep 16; 04:48 — Sep 17), start does not change it →
  **time of the last stop (hours, minutes)** 🟢.
- **`a1/21`:** `01` — stop, `00` — start → 🟢 (both values in the window, cross-checked with the
  screen). Before the window the app repeated `a1/21 00` 2 and 4 min after start — purpose of the
  repeats not established.
- **Finding:** registry `tools/fields.py` (off76 — value `ff ff`; field off78..79; command `a1/21`);
  PROTOCOL_EN.md tables regenerated.

### Step 028 — Document revision against the archive: frame format, pulse, polling cycle, objects within the window
- **Date/time:** 2026-09-17, 05:10–05:40. **Research:** revision (no new materials; data — all
  archives `archive/**/NN-hci.zip`, window from 2026-09-16 16:34, 8313 frames).
- **Reason:** the user pointed out that the summary and manually-maintained sections diverged from
  what had actually been established (pulse "single capture", "flags/enums 🟡", etc.). The registry
  and generation covered only field tables; the summary, log, and manual sections had not been
  revisited.
- **Frame format (checked against the archive):** 1779 commands — `0x35` marker, length field =
  frame size, byte[2] = `00`, `APEX…` block, CRC-16/MODBUS valid for all; frame with no payload —
  20 bytes (1660). Responses: `0xAA` marker for all 6534; length field = frame size for all 6284
  `A3`/`A1` responses; for 250 `A5/03` frames the length field = 6 (frame without CRC). → frame
  format 🟢.
- **Pulse `a5/03`:** 250 frames, payload always `aa0600a50300`, intervals 180.0 ± 0.2 s (236 ×
  180.0), no gaps over Sep 16 16:35 — Sep 17 05:02 → 🟢.
- **Polling cycle:** 327 `a3/00` requests, main interval 180 s (211); 243 cycles
  `a3/00 a3/0c a3/21 a3/0a a3/0b a3/26`, 29 shortened `a3/00 a3/0c`, after writing settings — a
  repeated read of `a3/00 a3/0c`.
- **Acknowledgments:** all 121 `a1` commands in the window received `a1/55 00 00` within 3 s → 🟢.
- **Objects within the window:** `a3/07` (8 frames), `a3/08` (48, records 00–07), `a3/0a` and
  `a3/0b` (252 each), `a3/21` and `a3/26` (2480 each, records 00–09), `a3/31` (1). The note "read
  before 16:34, re-capture within the window" in `OBJECTS_EN.md` was incorrect — all object maps have
  been regenerated from frames within the window.
- **Commands by window:** `a1/31` — one observation (the second value from Step 009 is before the
  window) → downgraded to 🟡; `a1/12` not observed within the window. A rule was added to
  `tools/verify_fields.py`: a command is 🟢 only with ≥2 observations within the window or an
  explicit cross-check against the screen.
- **Fixed in the documents:** the RESEARCH_EN.md summary was rewritten as the current status (object
  and command lists generated from the registry); 30 outdated findings in the log were marked
  "→ refined"; PROTOCOL_EN.md §2 (status 🟢, figures from the archive), §2.5, §4 (object catalog,
  pulse), §6 (polling cycle, acknowledgments); OBJECTS_EN.md — all objects per the window; APP_MENU.md
  — captured screens.

### Step 029 — Bolus log: object `a3/21`
- **Date/time:** 2026-09-17, screen — 05:36; capture — up to 16:56. **Research:** `etap-D-zhurnal-boljusov`.
  **Materials:** No. 46 (HCI, 2 rotation files), No. 47 (screenshot "Bolus history").
- **Action:** the user opened "Home → History → Bolus history" (no new boluses).
- **Screen (No. 47):** 6 "Simple" rows: 0.5 U 16:14; 0.5 U 16:11; 0.5 U 16:06; 0.5 U 16:02; 1 U
  15:55; 0.125 U 14:38 (all — September 16, 2026).
- **Object `a3/21`** (10 records of 14 bytes each, read on every polling cycle; unchanged within
  the window):
  | record | bytes 0..5 | off6 u16 | off8 u16 | off10..13 | screen |
  |---|---|---|---|---|---|
  | 00 | `1a 09 10 10 0e 3b` = Sep 16 16:14:59 | 20 (0.5) | 20 | `00000000` | 0.5 U 16:14 |
  | 01 | Sep 16 16:11:59 | 20 | 20 | 0 | 0.5 U 16:11 |
  | 02 | Sep 16 16:06:59 | 20 | 20 | 0 | 0.5 U 16:06 |
  | 03 | Sep 16 16:02:59 | 20 | 20 | 0 | 0.5 U 16:02 |
  | 04 | Sep 16 15:55:59 | 40 (1.0) | 40 | 0 | 1 U 15:55 |
  | 05 | Sep 16 14:38:59 | 5 (0.125) | 5 | 0 | 0.125 U 14:38 |
  | 06–09 | 14:26, 14:22, 14:18, 14:14 | 25, 26, 16, 14 | same | 0 | not shown on screen |
- **Result:** `a3/21` — **bolus log**, record 00 is the most recent. Bytes 0..4 — date and time
  `YY MM DD HH MM` 🟢; off6 u16 — dose, 0.025 U 🟢 (6 records cross-checked with the screen by time
  and dose). Byte 5 is `59` in all records — likely not the actual seconds (🟡). off8 equals off6
  in all records — presumably "requested / delivered" (🟡; would distinguish an interrupted bolus).
  off10..13 — zeros (🔲).
- **Limitation:** the boluses in the log are from before the research window (Sep 16 14:14–16:14);
  no new boluses occurred within the window. The records were read within the window (frames
  No. 46), values cross-checked with the screen within the window.
- **Tools:** the registry and verification now support fields of multi-record objects
  (`records=True`); table PROTOCOL_EN.md §4.4 is generated.

### Step 030 — Extended bolus: command `a1/13`, notifications `a1/a1`, cancellation, record `a3/21`
- **Date/time:** 2026-09-17, 17:25–17:41. **Research:** `etap-E-rastyanutyi-boljus`.
  **Materials:** No. 48 (HCI), No. 49 (3 screenshots: log during delivery, Home with delivered
  portion, log after cancellation).
- **User actions:** 17:25 turned on "Extended bolus"; 17:26 delivered an **extended bolus of 1 U
  over 45 min**; observed the delivery progress; ~17:35 pressed bolus "Cancel". Pump — a test bench
  with no patient (project rules, `legal_EN.md`).
- **Enabling the mode:** `a1/32` byte[6] `00→01` (17:25:36); `a3/00` off4 `0→2` (17:25:52) — as in
  Step 015.
- **Start — command `a1/13`:** 17:26:30 payload `28 00 03 00` = **dose** u16 `40` × 0.025 = 1.0 U ·
  **duration** u16 `3` × 15 min = 45 min. Matched the screen "Extended: 1 U 00:45" (No. 49).
  Acknowledgment `a1/55` returned an **echo of the payload** `28 00 03 00` (for other commands —
  `00 00`). → `a1/13` = start extended bolus 🟢.
- **Delivery progress — notifications `a1/a1`:** unsolicited frames, u16LE — cumulative delivered
  dose (0.025 U): 17:27:39 `2` (0.05) · 17:29:54 `4` (0.10) · 17:32:09 `6` (0.15) · 17:34:24 `8`
  (0.20). Matches the Home screen tile "0.150 Extended" (No. 49) and "Act. insulin". Interval ≈
  135 s (1 U / 45 min = 0.05 U every 2.25 min). 🟢
- **Cancellation:** 17:35:17 command `a1/02` with payload `00 00`, acknowledgment `a1/55 00 00`;
  delivery stopped at 0.2 U. One observation → 🟡 (the same `a1/02` used for TBR; here a short
  payload `00 00`).
- **Record `a3/21`:** after the bolus the log shifted, record 00 = the extended bolus. Final record
  00: `1a 09 11 11 1a 3b 00 00 00 00 28 00 08 00` = **Sep 17 17:26:59**, off6 = 0, off8 = 0,
  **bytes 10..11 = 40 (1.0 U requested), 12..13 = 8 (0.2 U delivered)**. Screen after cancellation
  — "Extended: 0.2 U 00:45 17:26" (No. 49). → for an extended bolus the dose sits in 10..13
  (requested/delivered), off6/off8 = 0; for a simple bolus — the reverse (Step 029). 🟡 (one
  observation).
- **New object `a3/01`:** at 17:35 object `a3/01` was read — 128+ records of 14 bytes, record
  structure matches `a3/21` (detailed log). Fields not parsed (🔲); entered into the §4 catalog.
- **Tools/safety:** extended bolus fields — in the registry (🟡); table §4.4 regenerated. The
  action was performed by the user on the bench pump with no patient; no custom frames were sent to
  the pump.

### Step 031 — Simple bolus with cancellation: command `a1/12`, notifications `a1/a0`; off6/off8 = requested/delivered; TBR 120%
- **Date/time:** 2026-09-17, 18:13–18:16. **Research:** `etap-E-prostoi-boljus-otmena`.
  **Materials:** No. 50 (HCI), No. 51 (2 screenshots: Home with delivered dose, Home with TBR 120%).
- **Actions:** the user delivered a **simple bolus of 2 U** (18:13) and almost immediately pressed
  "Cancel" (0.55 U delivered); then set a **TBR of 120% for 2:30** (18:15). Bench with no patient.
- **Start — `a1/12`:** payload `50 00 00` = dose u16 `80` × 0.025 = 2.0 U (+ byte `00`). →
  `a1/12` = start simple bolus 🟢. Before the window the same command appeared as
  `0c/12/14 00 00` (simple boluses) — the earlier note "not established" is withdrawn.
- **Delivery progress — `a1/a0`:** unsolicited frames, cumulative delivered dose u16 (0.025 U):
  `2`…`22` (0.05…0.55). Analog of `a1/a1` for extended boluses.
- **Cancellation — `a1/02 00 00`:** second observation (first — extended bolus, Step 030) →
  bolus cancellation 🟢.
- **Record `a3/21` (confirming the user's hypothesis):** record 00 = `…50 00 16 00 00 00 00 00`:
  off6 = `80` (2.0 U — **requested**), off8 = `22` (0.55 U — **delivered**), bytes 10..13 = 0.
  Screen: "0.55 U at 18:13" (No. 51). → off6 = requested, off8 = delivered 🟢; for the extended
  bolus — the reverse (in 10..13).
- **TBR 120%:** `a1/02` `00 0a 78 00` = type `00` (%) · `0a`=10×15 = 150 min = 2:30 · `120`%.
  `a3/00` off80 = `24` = ⌊20 × 120 / 100⌋ = 0.6 U/h (screen "0.6 U/h", No. 51) — second observation
  of a percent-type TBR, formula off80 = ⌊off76 × % / 100⌋ confirmed.
- **Finding:** registry (`a1/12` 🟢; off6/off8 requested/delivered 🟢; cancellation `a1/02 00 00`
  🟢); PROTOCOL_EN.md §4.4, §5.
- **`a3/00` off86 (TBR — elapsed) → 🟢:** across all archive frames it grows +1 min from the start
  of the TBR (0 when off51=0); the remaining time on screen = off84−off86 (18:20: 150−5 = 145 min =
  02:25, No. 51). Previously 🟡 (Step 024).

### Step 032 — TBR log `a3/27`; detailed bolus log `a3/01`
- **Date/time:** 2026-09-17, ~18:26. **Research:** `etap-E-prostoi-boljus-otmena`.
  **Materials:** No. 52 (HCI), No. 53 (screenshot "TBR history").
- **Action:** the user opened "Home → History → TBR history". The app read the new object
  **`a3/27`** (10 records of 14 bytes each).
- **Parsing `a3/27`** (all 6 screen rows matched):
  | idx | start | off6 type | off8 dur | off10 value | off12 delivered | screen |
  |---|---|---|---|---|---|---|
  | 00 | Sep 17 04:03 | 0 (%) | 11 (2:45) | 113 (%) | 26 (0.65 U) | 0.65 U · 113% · 02:45 |
  | 01 | Sep 17 03:37 | 1 (U/h) | 3 (0:45) | 240 (6.0) | 96 (2.4 U) | 2.4 U · 6 U/h · 00:45 |
  | 02 | Sep 16 16:16 | 1 | 2 (0:30) | 80 (2.0) | 39 (0.975) | 0.975 U · 2 U/h · 00:30 |
- **Fields of `a3/27`** 🟢: 0..5 — start `YY MM DD HH MM SS`; off6 — type (0%, 1 U/h; as byte[0] of
  `a1/02`); off8 — duration ×15 min; off10 — value (% or 0.025 U/h depending on type); off12 —
  delivered, 0.025 U.
- **User observation (correct):** the TBR log shows only **completed** TBRs — the active 120% TBR
  (Step 031) is absent from the list; likewise the "Bolus history" shows only completed boluses.
  The currently active delivery is visible in status `a3/00` (TBR — off51/80/82/84; bolus —
  notifications `a1/a0`/`a1/a1`).
- **Object `a3/01`:** 128 records of 14 bytes, record structure = `a3/21` (record 00 = simple
  bolus 18:13, record 01 = extended bolus 17:26) — detailed bolus log; in the §4 catalog and
  `OBJECTS_EN.md`.
- **Finding:** registry (fields of `a3/27` 🟢); PROTOCOL_EN.md §4.5 and catalog (`a3/27`, `a3/01`);
  `OBJECTS_EN.md`.

### Step 033 — Basal change log — object `a3/02`
- **Date/time:** 2026-09-17, ~21:41 (read on reconnection after a phone reboot); screen — 21:45.
  **Research:** `etap-D-zhurnal-bazala`. **Materials:** No. 54 (HCI), No. 55 (screenshot "Basal changes").
- **Action:** the user opened "Home → History → Basal changes". On reconnection the app read
  object **`a3/02`** (47 records of 102 bytes each).
- **Record structure:** bytes 0..5 — profile-change timestamp; bytes 6..101 — 48 × u16LE
  (half-hour rates, 0.025 U/h) — a snapshot of the basal profile. Daily dose = sum of 48 rates ×
  0.025 × 0.5.
- **Cross-check with the screen (all matched):**
  | idx | timestamp | profile (first intervals) | sum×0.0125 | screen |
  |---|---|---|---|---|
  | 00 | Sep 17 04:44 | 36×10, 29×6, 40×16, 20×16 | 18.675 U | 18.675 U · Sep 17 04:44 |
  | 01 | Sep 14 22:26 | 36×48 (0.9 U/h exactly) | 19.200 U | 19.2 U · Sep 14 22:26 |
  | 02 | Sep 14 16:16 | 28×… | 20.000 U | 20 U · Sep 14 16:16 |
  | 03 | Sep 13 23:09 | 8×… | 3.600 U | 3.6 U · Sep 13 23:09 |
- **Link to Step 026:** record 00 (Sep 17 04:44) is the exact profile written by command `a1/00`;
  the half-hour rates of `a3/02` idx00 match the `a1/00` payload and object `a3/08` (record 00).
  This confirms both the `a3/08` parsing and the profile write.
- **Result:** `a3/02` = basal change log 🟢 (timestamp + profile snapshot); the timestamp field is
  in the registry. The profile is stored as 48 half-hour rates — the same encoding as `a3/08`.
- **Phone reboot:** tcpip mode restored via path (2) of the `apex-device` skill; the HCI log after
  the reboot was started fresh, objects re-read on reconnection.

### Step 034 — Pump lock: `a1/32` byte[0] bit `0x10`, `a3/00` off11; rejection `a1/a5`; unlock on the pump
- **Date/time:** 2026-09-17, 21:55–22:05. **Research:** `etap-E-blokirovka-pompy`.
  **Materials:** No. 56 (HCI), No. 57 (3 screenshots).
- **User actions:** 21:55 "Auxiliary functions → Danger zone → Pump lock" → "Lock" (dialog: "You
  can only unlock the pump from the pump's menu", No. 57/01); ~22:01 unlocked the pump from its
  menu. Bench with no patient.
- **Enabling — `a1/32`:** 21:55:22 the settings block differs from the previous one (17:25:36)
  **only in byte[0]:** `00 → 10`; the other 15 bytes are the same. Acknowledgment `a1/55 00 00`.
  Bit `0x10` had not appeared over the air before.
- **Status `a3/00` off11:** 21:54:24 = `0`; 21:55:27 and afterward = `1` (21:56, 21:59, 22:01:35,
  22:02:02); 22:05:02 = `0`, 22:08:02 = `0`. In all other `a3/00` frames in the archive off11 = `0`
  (574 frames).
- **Screen:** 21:56 "Devices" — "Locked", lock icons on "Bolus settings" and "Basal settings"
  (No. 57/02); 22:05 — "Unlocked" (No. 57/03). Per the user, in the locked state only "Disconnect
  pump" is available in the app.
- **Unlocking on the pump:** between 22:02:02 and 22:05:02 the app sent no `a1/*` commands (only
  polling `a3/00`, `a3/0c`, `a3/0a`, `a3/0b` and a read of `a3/27` at 22:03:46) — the change of
  off11 `1→0` came from the pump. This is a second, independently-natured measurement (a change
  from the other side, a different value).
  → **`a1/32` byte[0] bit `0x10` = `a3/00` off11 = pump lock** 🟢.
- **Rejection — `a1/a5`:** following `a1/32`, the app, as always, sent `a1/34` (sound block
  unchanged, 21:55:24) — to the now-locked pump. The response was **`a1/a5 00 00`** instead of
  `a1/55`; `a1/a5` occurs once in the entire archive. Hypothesis: an acknowledgment meaning
  "command rejected — pump locked". One observation → 🟡.
- **Reading while locked:** polling of `a3/*` objects responds as usual — the lock applies only to
  `a1` commands.
- **Finding:** registry (`pump_lock` 🟢, flag `pump_side` — value change on the pump without an app
  command, accounted for in `tools/verify_fields.py`); PROTOCOL_EN.md §2.2 (`a1/a5`), §4.1, §5.1, §6;
  APP_MENU.md.
- **Privacy:** in screenshot No. 57/02 the serial number is masked; No. 57/01 and No. 57/03 do not
  contain it.

### Step 035 — TBR descriptors: `a3/0a` (current) and `a3/0b` (last completed)
- **Date/time:** 2026-09-17, analysis against the archive (`a3/0a`/`a3/0b` are read every polling
  cycle). **Research:** revision. **Materials:** No. 38, No. 39 (TBR 6 U/h, 113%), No. 52 (TBR log),
  No. 54 (120% completion).
- **Task (user request):** cross-check `a3/0a`/`a3/0b` against the commands of the most recent
  delivered and completed TBRs.
- **`a3/0a` — current (most recently started) TBR** (20 bytes): 0..5 start (duplicated 7..12), 13
  type (0%/1 U/h), 14..15 duration ×15 min, 16..17 value, 18..19 delivered (0.025 U; grows,
  resets at the end). Matched the commands: 6 U/h → type 1/dur 3/value 240; 113% → 0/11/113;
  120% → 0/10/120.
- **`a3/0b` — last completed TBR** (26 bytes): 1..6 start, 13 type, 14..15 duration, 16..17 value,
  18..23 end, 24..25 delivered (0.025 U). Checked: 6 U/h → delivered 96 = 2.4 U (= `a3/27` off12);
  113% (cancelled 04:40) → 26 = 0.65 U; 120% → end Sep 17 20:46 (start 18:15 + 2:30), delivered 59
  (No. 54).
- **Correction (per the user's remark):** the start time is recorded twice in both — `a3/0a` off0
  and off7 (with byte 6 = `00` between them), `a3/0b` off1 and off7 (preceded by byte 0). Previously
  bytes 7..12 remained unparsed.
- **Result:** `a3/0a` = current TBR, `a3/0b` = last completed TBR — both mirror the `a1/02` command;
  `a3/0b` adds the end time and total delivered dose (= `a3/27`). 🟢. Byte 0 of `a3/0b`
  (counter/type) — not established.

### Step 036 — Bolus calculator: object `a3/07`, command `a1/15`; Prepare Write assembly in `hci_frames.py`
- **Date/time:** 2026-09-17, 22:24–22:55. **Research:** `etap-E-kalkulyator-boljusa`.
  **Materials:** No. 58 (HCI), No. 59 (8 screenshots).
- **User actions** ("Devices → Bolus settings", bench with no patient): 22:24 turned off and 22:25
  turned on the calculator; 22:27 carb units CU → grams; 22:30 carb ratios 9/8/7 g/U from
  00:00/15:00/20:00; 22:32 BG units mmol/L → mg/dL; 22:41 sensitivity 03:30 → 54 mg/dL/U; 22:42
  target BG 05:30 → 107 mg/dL; 22:42 active insulin time 06:00 → 05:30; 22:54 grams → CU and ratio
  12:30 → 0.1 U/CU; 22:54 mg/dL → mmol/L; 22:55 sensitivity 22:30 → 4.7 mmol/L/U.
- **Command `a1/15`:** a 264-byte frame (length u16LE `08 01` in bytes [1..2]) longer than the MTU —
  the app sends a Prepare Write (246 + 5 bytes), an Execute Write, and a regular tail write
  (13 bytes). `tools/hci_frames.py` previously assembled only single writes — the command was
  invisible (the parse left a `64/30…` tail). Assembly support was added; output on all prior
  archives is unchanged (frame and digest cross-check), and in No. 58 — 12 `a1/15` commands, CRC
  valid for all.
- **Link to `a3/07`:** after the `a1/55` acknowledgment the app re-reads `a3/07`; the `a1/15`
  payload (244 bytes) equals bytes 0..243 of the object — 13 matches, no discrepancies. Bytes
  244..245 = CRC-16/MODBUS of bytes 0..243 (matched for all the different contents) — computed by
  the pump.
- **Fields** (each action changed only "its" field and the CRC):

  | time | action | change | screen |
  |---|---|---|---|
  | 22:24:50 / 22:25:22 | calculator off / on | off0 `01→00→01` | "Enable calculator" on (No. 59/01) |
  | 22:27:12 | CU → grams | off1 `01→00` | "Grams…" (No. 59/05) |
  | 22:30:35 | ratios | off8..15: (8, slot 30), (7, slot 40) | 9/8/7 g/U from 00:00/15:00/20:00 (No. 59/02) |
  | 22:32:19 | mmol/L → mg/dL | off1 `00→10` | "mg/dL" (No. 59/05) |
  | 22:41:42 | sensitivity | off152..155: (54, slot 7) | 50/54 from 00:00/03:30 (No. 59/03) |
  | 22:42:02 | target BG | off222..223: (107, slot 11) | 100/107 from 00:00/05:30 (No. 59/04) |
  | 22:42:25 | active insulin time | off2..3 `360→330` min | 06:00 (No. 59/01) → 05:30 (No. 59/05) |
  | 22:54:09 / 22:54:45 | grams → CU / mg/dL → mmol/L | off1 `10→11→01` | "CU", "mmol…" (No. 59/08) |
  | 22:54:35 | CU ratio | off60..63: (2, slot 25) | before edit 0.50/1.00 from 00:00/04:00 (No. 59/06); tile "0.1 U/CU" (No. 59/08) |
  | 22:55:00 | mmol sensitivity | off108..111: (47, slot 45) | 4.0/4.1/4.7 from 00:00/11:30/22:30 (No. 59/07) |

- **Table encoding:** 12 records of "value · half-hour start slot", slot 48 — an empty record
  (user's hint: 48 half-hour slots). Scales: grams — g/U; CU — × 0.05 U/CU (10 → "0.50", 20 →
  "1.00"); mmol/L — × 0.1 (40 → "4.0"); mg/dL — as-is. Target BG — records of 2 bytes (u8 · u8).
- **Separate storage (user's hypothesis confirmed):** changing units changes only off1; after
  switching to mg/dL, the mg/dL table remained 50 (≠ 4.0 × 18), and on returning to mmol/L —
  4.0/4.1 (not recomputed from 50/54). The user noted: "the numbers there are completely different
  and appear to be stored separately".
- **"Bolus settings" tiles** show the record for the current slot: 22:26 "1.0 U/CU" (record from
  04:00 = 20 × 0.05), "4.1" (from 11:30), "5.8" (from 14:30); 22:42 "7 g/U" (from 20:00), "54",
  "107"; 22:55 "0.1 U/CU" (from 12:30), "4.7" (from 22:30).
- **Statuses:** all fields 🟢, except "target BG (mmol/L)" 🟡 — unchanged within the window, the
  interval list was not captured (confirmed only by the "5.8" tile).
- **Numbering:** a parallel session also recorded the TBR-descriptor parsing as "Step 034"; by the
  user's decision it was renamed to Step 035 (heading and references), the calculator became
  Step 036.
- **Finding:** registry (11 `a3/07` fields, command `a1/15`); PROTOCOL_EN.md §4 (catalog), §4.9, §5;
  OBJECTS_EN.md; APP_MENU.md; `tools/hci_frames.py` (Prepare Write assembly).

### Step 037 — TBR: start source (`a3/0a` off0 / `a3/0b` off1) and completion cause (`a3/0b` byte 0)
- **Date/time:** 2026-09-17, 22:50–23:13. **Research:** `etap-E-vbs-istochnik`. **Materials:** No. 60 (HCI).
- **Scenarios (per the user's request):** a TBR started and cancelled **from the pump**; then a TBR
  started and cancelled **from the app** (twice). Bench with no patient.
- **Key observation:** actions from the pump **do not generate `a1/02`/`a1/05` commands** over the
  radio — the app only re-reads `a3/0a`/`a3/0b`. Cancellation from the app — command `a1/05`.
- **Start source = the first date** (`a3/0a` off0, `a3/0b` off1). Previously (Step 035) I mistakenly
  called it a "copy of the start time":
  | TBR | off0/off1 | actual start off7 | source |
  |---|---|---|---|
  | from the app (120%, 18:15; 3.0 U/h 23:09; 127% 23:12) | = command time | same | app |
  | from the pump (0.125 U/h, 22:50) | `00 00 00 00 00 00` | 22:50 | pump |
  The actual start is always in off7; the first date is empty when started from the pump.
- **Completion cause = byte 0 of `a3/0b`** (correction to the earlier shallow finding "2 = from the pump"):
  | byte0 | meaning | observations |
  |---|---|---|
  | 1 | ran to completion | end ≈ start+duration (16:47, 20:46) |
  | 2 | cancelled from the pump | 22:52 (no `a1/05` command); also Sep 16 02:25 |
  | 3 | cancelled from the app | 04:01, 04:40, 23:11, 23:13 — each time an `a1/05` is present |
  Value 0 was not seen in the window (the user suggested it exists — likely a different completion
  cause).
- **Result:** a TBR has two independent indicators — **who started it** (first date: filled = app,
  zeros = pump) and **how it ended** (byte 0 of `a3/0b`: 1/2/3). Both 🟢. The `a3/0a`/`a3/0b`
  registry entries were corrected (off0/off1 — "app command / source", off7 — "start"); a "how it
  ended" field was added.

### Step 038 — Setting pump time `a1/31` (second observation); BG units mmol/L → mg/dL
- **Date/time:** 2026-09-17, 23:42–23:43. **Research:** `etap-E-vremya-edinicy-gk`.
  **Materials:** No. 61 (HCI), No. 62 (screenshot). Bench with no patient.
- **User actions:** "Danger zone → Synchronize pump time"; then "Bolus settings → BG units"
  mmol/L → mg/dL.
- **Setting the time — `a1/31`:** 23:42:43 payload `1a 09 11 17 2a 2b` = **2026-09-17 23:42:43** —
  the phone's time at the moment of sending; acknowledgment `a1/55 00 00`, CRC valid. Status
  `a3/00` off44..49: 23:42:37 — `…17 2a 00` (23:42:00); 23:42:49 — `…17 2a 2b` (**23:42:43**, the
  written value); 23:44:00 — `…17 2c 00`. Other observations within the window — Sep 16 16:52:06
  (Step 009) and Sep 17 20:52:08 (the app synchronized the time itself on reconnection after the
  phone reboot, Step 033); the values differ, the reflection in status matched → **`a1/31` = set
  pump time 🟡→🟢**.
- **Seconds in status:** before and after setting, off49 = `00`; written seconds are visible only
  until the minute changes. Hypothesis: the pump keeps time to the minute. 🟡 (one observation).
  Pump clock drift cannot be measured: before setting, the pump's time matched the phone's to the
  minute.
- **BG units — `a1/15`:** 23:42:54 the app re-read `a3/07` (the entire block is sent before a
  write), 23:42:59 `a1/15`, acknowledgment `a1/55`; 23:43:02 `a3/07` changed only off1 `01→11`
  (bit `0x10`) and CRC off244..245. Screen at 23:43 (No. 62): "mg/dL", "Sensitivity 54 mg/dL/U",
  "Target BG 107 mg/dL" — the mg/dL table values, written at 22:41–22:42, were not recomputed.
  Third confirmation of bit `0x10` and of the tables being stored separately (Step 036).
- **Finding:** registry (`a1/31` 🟢; cross-check `calc_bg_units` No. 62; note on the status
  timestamp); PROTOCOL_EN.md §4.1, §5.

### Step 039 — Daily doses: objects `a3/26` (10 days) and `a3/06` (38 days)
- **Date/time:** 2026-09-17, ~23:24. **Research:** `etap-D-dnevnye-dozy`. **Materials:** No. 63 (HCI + screenshot).
- **Action:** the user opened "Home → History → Daily doses". Values matched objects `a3/26`
  (polled each cycle) and `a3/06` (same structure, longer).
- **Record structure (10 bytes):** 0..1 bolus, 2..3 basal, 4..5 temporary basal (u16LE, 0.025 U);
  6..8 date `YY MM DD`; byte 9 — `00`. On-screen total = sum of the three fields.
- **Cross-check with the screen (all rows matched):**
  | date | bolus | basal | temp basal | total | screen |
  |---|---|---|---|---|---|
  | Sep 17 | 1.65 | 16.025 | 4.625 | 22.3 | 22.3 U (expanded: basal 16.025 / bolus 1.65 / temp basal 4.625) |
  | Sep 16 | 60.25 | 3.625 | 5.575 | 69.45 | 69.45 U |
  | Sep 15 | 86.025 | 0.775 | 8.675 | 95.475 | 95.475 U |
  | Sep 14 | 50.6 | 0.225 | 4.825 | 55.65 | 55.65 U |
- **Result:** `a3/26` = daily doses for 10 days, `a3/06` = the same for 38 days 🟢. The expanded
  screen row (basal/bolus/temp basal) matched the three record fields.
- **Note:** previously (Step 028) `a3/26` was marked "last 3 bytes look like a date" — now fully parsed.

### Step 040 — Detailed bolus log `a3/01`: field mapping (date and doses)
- **Date/time:** 2026-09-18, analysis against the archive. **Research:** `etap-D-dnevnye-dozy`.
  **Materials:** No. 46, No. 63.
- **Reason (user's remark):** in the `a3/01` map, the first bytes are the date, and the field was
  not marked, so the date "drifted" across the table's u16 cells.
- **Structure of `a3/01`** matches `a3/21` (§4.4): bytes 0..5 — date/time `YY MM DD HH MM SS`;
  off6/off8 — simple bolus requested/delivered; off10/off12 — extended bolus set/delivered. Record
  00 = the most recent bolus (Sep 17 18:13 — simple 2.0/0.55), record 01 = extended (Sep 17 17:26).
  128 records versus 10 for `a3/21`.
- **Result:** `a3/01` fields mapped (date 🟢, simple-bolus doses 🟢, extended-bolus doses 🟡 — as in
  `a3/21`); the date no longer "drifts" in the `OBJECTS_EN.md` table.
- **Open (dual/combo bolus):** an `a3/21` record from 23:16 showed both off6/off8 (1.15/0.9) and
  off10/off12 (0.85/0) simultaneously — the immediate and extended portions in a single record.
  The exact semantics (1.15 versus 0.9+0.85) is not confirmed without a "Bolus history" screenshot
  of that bolus — 🟡, awaiting a frame.

### Step 041 — Dual (combo) bolus: immediate + extended portions in record `a3/21`/`a3/01`
- **Date/time:** 2026-09-17, 23:16 (bolus), cancelled ~23:17. **Research:** `etap-E-kombo-boljus`.
  **Materials:** No. 63 (HCI), No. 64 (user screenshots: bolus confirmation; daily doses for 10 days).
- **Action:** the user set a **combo bolus** — screen "Confirm bolus" (No. 64): "Simple bolus:
  1.15 U, Extended bolus: 0.85 U, Duration: 00:15" — then interrupted delivery.
- **Record `a3/21` (00):** `2e 00 24 00 22 00 00 00` → off6=46 (1.15 U immediate — requested),
  off8=36 (0.9 — immediate delivered, interrupted), off10=34 (0.85 U extended — set), off12=0
  (extended not delivered).
- **Result:** a single log record describes both parts of the bolus: **off6/off8 = immediate
  (simple) portion requested/delivered, off10/off12 = extended portion set/delivered**. A simple
  bolus = only off6/off8; a purely extended bolus (Step 030) = only off10/off12; combo = both.
  Fields renamed ("immediate"/"extended portion") and upgraded to 🟢 (the extended portion
  confirmed by the screen: 1.0 in Step 030 and 0.85 in Step 041).
- **Incidentally:** a screenshot of the 10-day daily doses (No. 64) — an additional cross-check for
  Step 039 (Sep 11 = 68.25; Sep 10 = 69.65).

### Step 042 — Target BG (mmol/L) in `a3/07`: interval list cross-checked with the screen 🟡→🟢
- **Date/time:** 2026-09-18, 00:21. **Research:** `etap-E-kalkulyator-boljusa`.
  **Materials:** No. 65 (HCI), No. 66 (screenshot). Bench with no patient.
- **User actions:** "Bolus settings → BG units" mg/dL → mmol/L; "Target BG" — added an entry
  19:00 → 5.8.
- **Air:** 00:21:32 `a1/15` → `a3/07` changed only off1 `11→01` (bit `0x10` cleared) and the CRC;
  00:21:47 `a1/15` → off200..201 `38 30` → `3a 26` (the empty record (56, slot 48) replaced by
  (58, slot 38 = 19:00)). Both acknowledged with `a1/55`.
- **Table off196..219 after the change:** (56, 0) · (58, 29) · (58, 38) · 9 empty records (56, 48).
  Screen (No. 66): 5.6 mmol/L 00:00 · 5.8 14:30 · 5.8 19:00 — matched. The format "u8 × 0.1 mmol/L ·
  u8 slot" confirmed on a new record; the new value took the first empty record. The mg/dL table
  (100 / 107) did not change — separate storage.
- **Finding:** `calc_target_mmol` 🟡→🟢 (two different contents, list cross-checked with the
  screen); PROTOCOL_EN.md §4.9 (generated).

### Step 043 — Basal profiles: selection `a1/04`, active profile `a3/00` off12, `a3/08` = profiles A–H, `a1/00` writes to the active one
- **Date/time:** 2026-09-18, 00:47–00:59. **Research:** `etap-E-bazalnye-profili`.
  **Materials:** No. 67 (HCI), No. 68 (6 screenshots). Bench with no patient.
- **User actions:** "Basal settings → Profile" — B, C, D in turn, then A, with a screenshot of the
  "Basal schedule" for each; then B again, changed the rate of the last slot 23:30 → 1.25 U/h;
  screenshot of the profile list. Per the user, there are 8 profiles, 3 filled.
- **Command `a1/04`** (1-byte payload — profile number), acknowledgment `a1/55 00 00`; after ~2 s —
  status, after ~4 s the app re-reads `a3/08`:

  | time | `a1/04` | `a3/00` off12 | off76 (rate at 00:30) | screen |
  |---|---|---|---|---|
  | 00:48:01 | `01` | `0→1` | 36 → 12 (0.3) | B "Total 15.25 U" (No. 68/02) |
  | 00:48:26 | `02` | `1→2` | 12 → 36 (0.9) | C "Total 20.0 U" (No. 68/03) |
  | 00:48:48 | `03` | `2→3` | 36 → 0 (0.0) | D "Total 0.0 U" (No. 68/04) |
  | 00:50:31 | `00` | `3→0` | 0 → 36 (0.9) | A "Total 18.675 U" (No. 68/01, before switching) |
  | 00:58:01 | `01` | `0→1` | 36 → 12 | "Profile B" (No. 68/06) |

  → `a1/04` = select active profile 🟢; `a3/00` off12 = active profile number 🟢 (a previously
  unparsed byte; `0` in all prior archives). An empty profile has off76 = `0`, not `ff ff` (stopped).
- **`a3/08` = profiles by number** (sum × 0.0125 = "Total"; rate-change points):
  - 00 = A 18.675: 00:00 0.9 · 05:00 0.725 · 08:00 1.0 · 16:00 0.5 — matched entirely (No. 68/01);
  - 01 = B 15.25: 00:00 0.3 · 01:00 0.5 · 02:00 0.6 · 03:00 0.7 · 04:00 1.1 · 05:00 1.2 · 06:00 1.0 ·
    07:00 0.8 · 08:00 0.6 · 11:00 0.5 · 15:00 0.7 · 16:00 0.8 · 18:00 0.6 · 19:00 0.5 · 23:30 0.2 —
    visible portion matched (No. 68/02, No. 68/05);
  - 02 = C 20.0: 00:00 0.9 · 02:00 1.0 · 04:00 1.1 · 05:00 1.0 · 06:00 0.9 · 07:00 0.8 · 08:00 0.7 ·
    10:00 0.6 · 12:00 0.7 · 15:00 0.8 · 16:00 0.9 · 20:00 0.8 · 23:00 0.9 — visible portion
    00:00–15:00 matched (No. 68/03);
  - 03 = D 0.0 (No. 68/04); 04–07 — zero. Profile list in the app — A…G visible, H below the
    scroll (No. 68/06).
- **Writing a profile `a1/00` → to the active profile:** 00:58:20 (B active) payload 96 bytes, sum
  15.775, slot 47 = 50; 00:58:23 in `a3/08` **only record 01** changed: slot 47 8 → 50 (0.2 →
  1.25 U/h). Screen: "Total 15.775 U", 23:30 → 1.25 U/h (No. 68/05). First observation — Step 026
  (A active, record 00 changed). → the question "which profile is addressed" resolved: the active
  one 🟢.
- **Finding:** registry (field `basal_profile`; commands `a1/04`, `a1/00`; note on off76);
  PROTOCOL_EN.md §4 (catalog `a3/08`), §4.1, §5; APP_MENU.md.

### Step 044 — Profile H: number `7` over the air; coverage revision — `a3/08` and the `a3/02` profile snapshot entered into the registry
- **Date/time:** 2026-09-18, 02:07. **Research:** `etap-E-bazalnye-profili`.
  **Materials:** No. 69 (HCI), No. 70 (screenshot). Bench with no patient.
- **User action:** "Basal settings → Profile" → H.
- **Air:** 02:06:59 `a1/04` with payload `07`, acknowledgment `a1/55`; 02:07:02 `a3/00` off12
  `1→7`, off76 = `0` (profile empty, not `ff ff`). Screen (No. 70): "Profile H", list scrolled to
  the end — B…H, H selected. → value `7` = H confirmed over the air and on screen; the profile
  list is complete: **A–H, 8 total** = `a3/08` records idx 00–07.
- **User's remark:** in `OBJECTS_EN.md` "nothing is recorded" for the basal profiles. Checked: the
  byte-map takes labels only from the registry `tools/fields.py`, and the `a3/08` parsing lived
  only as text (§4 catalog, Steps 026, 043). Coverage revision across all window objects
  (parsed/length): `a3/00` 63/88, `a3/01` 14/14, `a3/02` 6/102, `a3/06` 9/10, `a3/07` 246/246,
  **`a3/08` 0/96**, `a3/0a` 19/20, `a3/0b` 26/26, `a3/0c` 4/20, `a3/21` 14/14, `a3/26` 9/10,
  `a3/27` 14/14, `a3/31` 0/8.
- **Fixed:** two table fields entered into the registry — `a3/08` (48 × u16LE, × 0.025 U/h; record
  = profile A–H) and `a3/02` off6..101 (profile snapshot at the time of the change, same encoding).
  Now `a3/08` is 96/96, `a3/02` is 102/102, and both are visible in `OBJECTS_EN.md`.
- **Remains unparsed:** `a3/00` (25 bytes: 10, 18..19, 22..23, 56..75), `a3/0c` (16 bytes), `a3/31`
  (8 bytes, from the second session), one byte each in `a3/06` and `a3/26`.
- **Finding:** registry (`basal_profile` — value `7` and full menu A–H; new fields
  `basal_profile_rates`, `basal_log_profile`; command `a1/04`); PROTOCOL_EN.md §4 (catalog `a3/08`);
  OBJECTS_EN.md.

### Step 045 — Bolus series: sixth byte of the log — position within the minute; `a1/aa`; daily counter 🟢; seconds in the timestamp; `a3/31` — versions
- **Date/time:** 2026-09-18, 02:18–02:36. **Research:** `etap-E-seriya-bolusov`.
  **Materials:** No. 71 (HCI), No. 72 (2 screenshots). Bench with no patient.
- **User actions:** a series of three 0.025 U boluses at 02:18 (02:18:07, 02:18:19, 02:18:27) and a
  series of 0.025 / 0.05 / 0.075 U at 02:28 (02:28:07, 02:28:14, 02:28:25); "Bolus history" opened.
- **The sixth byte of the log record is the position within the minute, not seconds** (previously
  🟡 "always 59 in all records"):
  - the 02:18 series produced records with `59`, `58`, `57` within the same minute;
  - the 02:28 series showed the mechanics: after the first bolus a record had `59`; after the
    second it became `58` while a new record got `59`; after the third — `57`, `58`, `59` top to
    bottom;
  - screen (No. 72): "Simple 0.075 U 02:28", "0.05 U 02:28", "0.025 U 02:28", then three "0.025 U
    02:18" — the order and doses matched `a3/21` idx00–05.
  → **off5 = record position within the minute: `59` for the newest, then `58`, `57`** 🟢. Fields
  are also separated in `a3/01` (detailed log): time — 5 bytes, position — a separate byte.
- **Bolus completion — notification `a1/aa`:** after the last `a1/a0`, an `a1/aa` arrives with the
  final delivered dose (u16LE, 0.025 U): `01 00`, `02 00`, `03 00` in the 02:28 series. Six
  observations → 🟢 (§6).
- **Daily counter `a3/00` off16..17 🟡→🟢:** the midnight reset was observed twice — Sep 16→17
  (2777 → 1) and Sep 17→18 (903 → 1). The "per day 🟡" note is removed (user's remark: the counter
  has now passed midnight a second time).
- **Seconds in the status timestamp (user's remark confirmed):** in the regular per-minute status,
  seconds are `00`; non-zero seconds appear only when the status is re-read at the moment of an
  event — setting the time, changing profile, a bolus, TBR start/cancel. 18 such cases within the
  window over two days → 🟢 (§6).
- **`a3/31` — versions (user's remark: "handshake — firmware and protocol version"):** 8 bytes
  `00 00 00 | 01 01 01 | 04 0c`; bytes 3..5 = firmware **1.1.1**, 6..7 = protocol **4.12** — exactly
  what's on the pump's info card (No. 57 21:56 and No. 72 02:26). Value unchanged across all
  captures → 🟢; PROTOCOL_EN.md §4.11. A `const` field type was added to verification: a constant is
  🟢 only if it stays unchanged within the window and is cross-checked with the screen ≥2 times.
- **Log records after creation:** checked against all captures — record content (doses) is not
  rewritten; only the minute-position byte changes, when a newer record is added within the same
  minute.
- **Finding:** registry (`bolus_log_pos`, `blog01_pos`, `fw_version`, `proto_version`; notes on
  `delivered_counter`, `status_time`, command `a1/12`); PROTOCOL_EN.md §4 (catalog `a3/31`), §4.11,
  §6; OBJECTS_EN.md; `tools/verify_fields.py`.

### Step 046 — Extended bolus of 2 U with cancellation: second observation of `a1/13`; basal dosing unit 🟡→🟢
- **Date/time:** 2026-09-18, 04:00–04:06. **Research:** `etap-E-rastyanutyi-boljus`.
  **Materials:** No. 73 (HCI), No. 74 (screenshot). Bench with no patient.
- **User actions:** delivered an **extended bolus of 2 U** (04:00) and cancelled it 3 minutes later
  (04:03).
- **Start — `a1/13`:** 04:00:12 payload `50 00 03 00` = dose u16 `80` × 0.025 = **2.0 U**, duration
  u16 `3` × 15 min = **45 min**; acknowledgment `a1/55` returned an echo of the payload. Second
  observation of the command with a different value (first — 1.0 U over 45 min, Step 030).
- **Delivery progress — `a1/a1`:** 04:00:47 `02 00` (0.05 U), 04:01:54 `04 00` (0.10 U) — interval
  ≈ 67 s (2 U / 45 min = 0.05 U every 1.125 min). No completion notification (`a1/aa`, as for a
  simple bolus): the bolus was cancelled before finishing delivery.
- **Cancellation — `a1/02 00 00`:** 04:03:01, acknowledgment `a1/55 00 00`; third observation of
  bolus cancellation with the same command.
- **Log record `a3/21`:** a record appeared for Sep 18 04:00, position 59, off6 = 0, off8 = 0,
  **off10 = 80** (2.0 U set), **off12 = 4** (0.1 U delivered). Screen (No. 74): "Extended: 0.1 U,
  00:45, September 18, 2026, 04:00". Matched.
- **Dosing unit (user's question):** the 🟡 in §4.3 did not mark the 0.025 U value itself, but the
  assumption that basal profile rates are encoded in the same units. Closed by data from Steps
  043/044: raw rates of four profiles matched the screen (36 → 0.9 · 29 → 0.725 · 40 → 1.0 · 20 →
  0.5 · 50 → 1.25 U/h), sums × 0.0125 matched the "Total" row (No. 68). Direct confirmation of the
  delivery step — boluses of 0.025 / 0.05 / 0.075 U from raw `1` / `2` / `3` (Step 045, No. 72). →
  §4.3 fully 🟢.
- **Finding:** registry (command `a1/13` — second value and cross-check; extended-portion log
  fields — cross-checks with No. 74; cancellation `a1/02`); PROTOCOL_EN.md §4.3, §5.

### Step 047 — Extended bolus of 0.25 U: completion `a1/aa`; the log record is created at the moment of completion
- **Date/time:** 2026-09-18, 04:12–04:27. **Research:** `etap-E-batareya-obrazcy`.
  **Materials:** No. 75 (HCI), No. 76 (screenshots). Bench with no patient.
- **User action:** an extended bolus of **0.25 U over 15 min**; specifically timed to wait for
  delivery to finish in order to catch the completion response (user's remark: "if it has a
  completion response, you have to catch it after 15 minutes").
- **Start:** 04:12:19 `a1/13` `0a 00 01 00` = 10 × 0.025 = **0.25 U**, 1 × 15 min = 15 min;
  acknowledgment — payload echo.
- **Delivery progress:** ten `a1/a1` notifications in steps of 0.025 U: `01 00` (04:13:04) …
  `09 00` (04:25:05), interval ≈ 90 s (0.25 U / 15 min). Screen at 04:23 (No. 76): "0.175 ○ 0.25 U
  Extended", timer 00:09, current rate 0.025 U/h.
- **Completion:** 04:26:35 — **`a1/aa 0a 00`** = 10 × 0.025 = 0.25 U. The same notification as for
  a simple bolus (Step 045), i.e. `a1/aa` is shared between both kinds.
- **Moment the log record appears:** the record for Sep 18 04:12 (off10 = 10 set, off12 = 10
  delivered) appeared in `a3/21` **at the very moment 04:26:35**, i.e. at completion. For the
  cancelled bolus (Step 046), the record appeared at the moment of cancellation. This explains why
  no record was ever observed "filling in" over time — it is created already closed.
- **Detailed log `a3/01`:** reads at 04:04 and 04:26 repeated the `a3/21` records for the 2 U and
  0.25 U extended boluses byte-for-byte → extended-portion fields in `a3/01` 🟡→🟢 (previously
  "not cross-checked with the screen").

### Step 048 — Battery: stable 2 bars at 1.34 V; brief dips — a sag under load
- **Date/time:** 2026-09-18, observed over the window (Sep 18 04:14 — stable transition). **Materials:** No. 75.
- **User's remark:** the voltage dropped lower than predicted; the battery percentage on the app
  screen is a value computed by the app itself, there is no such field on the pump.
- **Data:** `a3/00` off0 = `3` at 1.35–1.37 V (686 frames). From Sep 18 04:13:54, when `a3/0c` off3
  showed **1.34 V**, off0 stably `2` (all frames until 04:38). → the threshold 3→2 lies **between
  1.34 and 1.35 V**, matching the earlier hypothesis (3→2 at 1.34 V).
- **Brief dips:** over two days, 11 pairs of transitions `3`→`2`→`3` at a rounded 1.35 V, each a
  single frame. User's explanation: the measured voltage is rounded, and under load (motor
  running, screen backlight) it sags below the threshold, recovering at rest. Consistent with the
  data: the dips began once the voltage approached the threshold and stopped once it settled into
  a stable `2`.
- **Result:** off0 = number of bars by voltage 🟡→🟢 (two stable states at different voltages).
  Steps 4→3 and 2→1 were not observed within the window — they remain part of the encoding
  description, not a confirmed fact.

### Step 049 — Basal samples: bit `0x08` of byte[0] of `a1/32` and `a3/00` off10
- **Date/time:** 2026-09-18, 04:35. **Materials:** No. 75 (HCI), No. 76 (screenshot 04:41).
- **User action:** "Basal settings → Basal samples" — turned on.
- **Air:** 04:35:15 `a1/34` (unchanged), 04:35:17 `a1/32` with byte[0] `00 → 08`; acknowledgments
  `a1/55`. In status `a3/00`, off10 became `1` (04:35:22), after which the app re-read `a3/08`.
- **Screen (No. 76):** the "Basal samples" toggle is on, with a list of four samples appearing
  beneath it.
- **Result:** **bit `0x08` of byte[0] of `a1/32` = `a3/00` off10 = "Basal samples" on/off** 🟢.
  Field off10 and bit `0x08` were previously unparsed; in byte[0] only bit `0x80` remains
  undisambiguated.
- **Finding:** registry (`basal_samples`, `battery_bars`, extended-portion fields of `a3/01`,
  command `a1/13`); PROTOCOL_EN.md §5.1, §6; OBJECTS_EN.md.

### Step 050 — Document revision: table of class-`A1` frames (acknowledgments and notifications); catalog status of `a3/01`
- **Date/time:** 2026-09-18 (analysis against the archive, no new actions on the bench). **Materials:**
  existing ones — No. 46, No. 50, No. 63, No. 71, No. 73, No. 75 (HCI with boluses) and No. 72,
  No. 74, No. 76 (screens).
- **User's remarks:** the documents show no `a1/a0`, `a1/a1`, and similar frames; the object
  catalog shows `a3/01` in yellow even though all its fields are already 🟢.
- **What was done:** an `ANSWERS` list was added to the registry — class-`A1` frames coming from
  the pump; table PROTOCOL_EN.md §4.12 is generated from it. Previously they were only mentioned in
  command notes and in §6.

  | Code | Purpose | Frames in window | Status |
  |---|---|---|---|
  | `a1/55` | command acknowledgment (echoes the payload for bolus starts) | 176 | 🟢 |
  | `a1/a0` | simple bolus delivery progress (cumulative dose, × 0.025 U) | 38 | 🟢 |
  | `a1/a1` | extended bolus delivery progress | 15 | 🟢 |
  | `a1/aa` | bolus completion (final dose) | 7 | 🟢 |
  | `a1/a5` | rejection: command not accepted (pump locked) | 1 | 🟡 |
- **Catalog `a3/01`:** status corrected from "🟡 — Step 032" to "fields — §4.4; 🟢 — Steps 040, 041,
  045, 047": the record fully parsed (14/14 bytes), cross-checked against `a3/21` and the screen.
- **Object coverage after the revision** (parsed / length): `a3/00` 64/88 (unparsed 18..19,
  22..23, 56..75); `a3/01`, `a3/02`, `a3/07`, `a3/08`, `a3/0b`, `a3/21`, `a3/27` — fully; `a3/06`
  and `a3/26` — 9/10 (byte 9); `a3/0a` — 19/20 (byte 6); `a3/0c` — 4/20; `a3/31` — 5/8 (bytes 0..2 —
  zero). The only command still at 🟡 — `a1/33`.
- **Finding:** registry (`ANSWERS`); `tools/gen_tables.py` (`answers` table); PROTOCOL_EN.md §4
  (catalog `a3/01`), §4.12.

### Step 051 — Exchange and authorization timings, how the pump presents itself over the air, timestamp precision, missing quantities
- **Date/time:** 2026-09-18 (analysis across all archived captures in the window; no new actions on
  the bench). **Materials:** existing HCI archives of the window (No. 4–6, …, No. 75).
- **Task (user's list):** collect the remaining unparsed items; cross-check request/response
  timings, especially during authorization; describe how the pump presents itself on the BLE air;
  separate objects by timestamp precision; record the absence of battery percentage and IOB.
- **Response delays** (all captures in the window): command `a1` → acknowledgment `a1/55`: 177
  pairs, median 186 ms, min 67, 95th percentile 489, max 539 ms. Read `a3` → first response frame:
  3943 pairs, median 139 ms, min 51, 95th percentile 189, max 1187 ms. → PROTOCOL_EN.md §6.
- **Authorization** (three connections in the window): from connection establishment to writing the
  password 1.34–1.64 s (this is time the app spends on service discovery), **the verdict arrives
  0.01–0.10 s after the password is written**, then MTU 517 and enabling notifications, the first
  command at +3.4…3.8 s. There is no artificial delay on successful authorization. **There were no
  failed attempts within the window**, so the presence of anti-brute-force protection (delay,
  lockout after N attempts) **was not tested** — a separate measurement with a deliberately wrong
  password would be needed. → PROTOCOL_EN.md §3.3.1.
- **Presentation over the air** (572 advertising frames from the pump, 4 distinct payloads): ADV
  carries `Flags 06`, an incomplete list of 16-bit UUIDs `0xFFE0` and `0xFFE5`, and 16 bytes of
  manufacturer data; SCAN_RSP — **the full name `APEX<serial>`**, connection interval range
  20–30 ms, TX Power 5. The serial number and set of services are visible over the air before
  connecting and before authorization. → PROTOCOL_EN.md §3.0.
- **Timestamp precision:** seconds are present only in the status timestamp (and only in a status
  re-read at the moment of an event) and in the TBR end time in `a3/0b`. For `a3/02`, `a3/27`,
  `a3/0a`, and the start fields of `a3/0b`, the seconds byte is always `00`; bolus logs record time
  to the minute plus a within-minute position; daily doses — only a date. → PROTOCOL_EN.md §4.13.
- **What the pump does not transmit:** battery percentage (only voltage and bars exist) and active
  insulin (IOB). Both quantities are computed by the app itself; this work records only the fact
  that these fields are absent from the pump's frames. → PROTOCOL_EN.md §4.14.
- **Remaining unparsed items** (after the revision): `a3/00` — bytes 18..19, 22..23, 56..75;
  `a3/0c` — 16 of 20 bytes; `a3/06` and `a3/26` — byte 9; `a3/0a` — byte 6; `a3/31` — bytes 0..2
  (always zero); command `a1/33` (`03 00`). Also awaiting a repeat measurement: `a1/a5` (rejection
  by a locked pump, one observation) and the Bluetooth PIN-change procedure (command unknown).
- **Finding:** PROTOCOL_EN.md §3.0, §3.3.1, §4.13, §4.14, §6; `OBJECTS_EN.md` supplemented with maps of
  class-`a1` frames, object `a3/02`, and the "pulse" `a5/03` (the generator now supports class `a1`).

### Step 052 — Changing the Bluetooth password: command `a1/35`; the authorization verdict is not a simple flag
- **Date/time:** 2026-09-18, 05:42–05:43. **Research:** based on an existing capture (bench remote).
  **Materials:** No. 77 (HCI).
- **User action:** "Devices → Danger zone → Change Bluetooth password"; the new password sent to
  the pump (05:43). Bench with no patient.
- **Command `a1/35`:** 05:42:52 payload **6 bytes**, acknowledgment `a1/55`. This is the only
  control command at the moment of the change. The bytes are the new password, but **not ASCII
  digits** (unlike the authorization write at `0x0041`): the command encodes the password in an
  internal representation. The value and the method for decoding it are not given in the documents
  (rule 5 — the password remains `<password>`).
- **Confirming the effect:** immediately after `a1/35` the app reconnected and **successfully
  authorized with the new password** — on channel `0x0041` in subsequent sessions the six ASCII
  digits go through twice (the same authorization encoding as for the original password, §3.3),
  and the sessions proceed to the normal command flow. This is a radio-side cross-check that the
  command changed the password. → `a1/35` = change Bluetooth password 🟢.
- **Authorization verdict — correction to §3.3:** in these sessions the verdict on `0x0044` was
  `01`, not `00`. Yet the ordinary command exchange followed it, i.e. the session was working. So
  the verdict is **not a simple "success/failure" flag** — both `00` (Steps 001/003) and `01`
  (Step 052) were observed, both with a working session. The exact meaning of the byte is not
  established; the earlier claim "`0x00` — success" is weakened.
- **Project rule (per the user's remark):** the previously proposed "test of anti-brute-force
  protection with a deliberately wrong password" is **withdrawn** — this would be bypassing a
  protection, which rule 9 forbids even on one's own device. The wording in §3.3.1 was corrected.
- **Finding:** registry (command `a1/35`); PROTOCOL_EN.md §3.3 (verdict), §3.3.1 (rule), §3.4
  (encoding), §5.

### Step 053 — Command sent to a locked pump: second observation of rejection `a1/a5`; an ongoing bolus is not interrupted
- **Date/time:** 2026-09-18, 16:37–16:41. **Research:** `etap-E-blokirovka-pompy`.
  **Materials:** No. 78 (HCI), No. 79 (screenshot). Bench with no patient.
- **User actions:** started an extended bolus, then locked the pump (user's remark: "locked it,
  with a bolus running").
- **Extended bolus — `a1/13`:** 16:37:42 payload `50 00 01 00` = 2.0 U over 15 min; acknowledgment
  `a1/55` with echo. Screen (No. 79): "2.0 U at 16:37 Bolus", "Act. insulin 0.12 U". Third value of
  the command (after 1.0/45 and 2.0/45).
- **Lock — `a1/32`:** 16:38:08 byte[0] = `18` = bit `0x10` (lock) on top of `0x08` (basal samples);
  acknowledgment `a1/55 00 00` — **the lock command was accepted as usual**. `a3/00` off11 became
  `1` (16:38:12).
- **Rejection `a1/a5` — second observation:** at 16:38:10 an automatic `a1/34` (the app sends it
  right after `a1/32`) arrived at the now-locked pump and received `a1/a5 00 00` instead of
  `a1/55`. First observation — Sep 17 21:55 (Step 034), the same pattern. → **`a1/a5` = rejection
  "command not accepted, pump locked" 🟡→🟢** (two measurements, different captures).
- **The ongoing bolus is not interrupted:** after `off11 0→1`, `a1/a1` notifications continued
  (16:38:17 `04 00` … 16:40:54 `12 00`) — the extended bolus kept being delivered. The lock blocks
  new commands but does not stop the current delivery. In the app, the "Bolus", "TBR", "Stop"
  buttons are locked (No. 79) — a command cannot be issued manually, so the only command that
  reached the locked pump was the automatic `a1/34`.
- **Finding:** registry (`a1/a5` 🟢; notes on `pump_lock` and command `a1/13`); PROTOCOL_EN.md §4.12, §6.

### Step 054 — Refill history: new object `a3/04`
- **Date/time:** 2026-09-18, 17:58. **Research:** `etap-E-istoriya-zapravok`.
  **Materials:** No. 80 (HCI), No. 81 (screenshot). Bench with no patient.
- **User action:** "Home → History → Refill history". The app read the new object **`a3/04`**
  (11 records of 10 bytes each).
- **Record structure** (cross-checked against all 8 visible screen rows):
  | idx | time | volume (u16 × 0.025) | type | screen |
  |---|---|---|---|---|
  | 00 | Sep 16 23:58 | 168 → 4.2 U | 1 | Manual 4.2 U Sep 16 23:58 |
  | 01 | Sep 14 15:27 | 302 → 7.55 U | 1 | Manual 7.55 U |
  | 02 | Sep 10 16:44 | 1725 → 43.125 U | 1 | Manual 43.125 U |
  | 03 | Sep 07 12:23 | 375 → 9.375 U | 1 | Manual 9.375 U |
  | 04 | Sep 04 13:29 | 308 → 7.7 U | 1 | Manual 7.7 U |
  | 05 | Sep 03 13:24 | 516 → 12.9 U | 1 | Manual 12.9 U |
  | 06 | Sep 03 13:14 | 11440 → 286 U | 1 | Manual 286 U |
  | 07 | Sep 03 13:11 | 2408 → 60.2 U | 1 | Manual 60.2 U |
- **Fields of `a3/04`** 🟢: 0..5 — time `YY MM DD HH MM SS` (seconds `00`, to the minute); 6..7 —
  reservoir refill volume ×0.025 U; 8 — type (`1` = "Manual"). Byte 8 = `0` occurred in one record
  outside the screen (Sep 03 12:37, 0.8 U) — purpose not cross-checked (🟡); byte 9 always `00`.
- **Finding:** registry (`refill_time`, `refill_amount` 🟢; `refill_type` 🟡); PROTOCOL_EN.md §4
  (catalog), §4.15; OBJECTS_EN.md.

### Step 055 — Alarm history: new object `a3/03`
- **Date/time:** 2026-09-18, 18:14. **Research:** `etap-E-istoriya-trevog`.
  **Materials:** No. 82 (HCI), No. 83 (screenshot). Bench with no patient.
- **User action:** "Home → History → Alarm history". The app read the new object **`a3/03`**
  (12 records of 8 bytes each).
- **Record structure** (cross-checked against the screen):
  | idx | time | code | screen |
  |---|---|---|---|
  | 00 | Sep 14 12:10 | 13 | Reservoir empty |
  | 01 | Sep 14 08:54 | 3 | Button error |
  | 02 | Sep 10 16:40 | 13 | Reservoir empty |
  | 07 | Sep 10 14:36 | 5 | Battery low |
  | 08 | Sep 10 13:48 | 13 | Reservoir empty |
- **Fields of `a3/03`** 🟢: 0..5 — time `YY MM DD HH MM SS` (seconds `00`, to the minute); 6..7 —
  alarm code (u16LE): `13` = reservoir empty, `3` = button error, `5` = battery low (cross-checked
  with the screen). Codes `1`, `2`, `8` are absent from the visible part of the screen — their
  purpose not cross-checked.
- **Finding:** registry (`alarm_time`, `alarm_code`); PROTOCOL_EN.md §4 (catalog), §4.16; OBJECTS_EN.md.
