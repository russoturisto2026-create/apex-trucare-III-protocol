# Technical description of the TruCare III pump protocol

Description of the **pump's own protocol**: transport, frame format, control commands that the pump
accepts, and the response objects it returns. Exchanges are initiated by the official Erwin Blueberry
app (used as intended); the subject of this description is the pump's behavior, not the app's. The
document is based **exclusively** on this project's materials; every statement is accompanied by a
reference to a step in `RESEARCH_EN.md` and a confidence status.

Status legend: 🟡 assumption (single measurement) · 🟢 confirmed (≥2 measurements with different
characteristics, rule 8) · 🔴 needs re-verification.

Identifying data, addresses, serial numbers and passwords are not given — placeholders
(`<identity>`, `<serial>`, `<crc>`) appear in their place.

---

## 1. Transport

BLE GATT. The pump acts as the GATT server, the phone with the official app as the client. The
pump's address is not given here (`<address>`). Source: RESEARCH_EN.md, Step 001 and Step 003
(materials #1, #2, #4-6). **Status: 🟢 confirmed** — two independent measurements: Step 001
(conn 0x0003) and Step 003 (conn 0x0005, reconnection after a normal disconnect). Services,
characteristics, handles, MTU and the CCCD enable order matched byte-for-byte.

### 1.1. GATT services
| Service | Handle range | Purpose (tentative) |
|---|---|---|
| `0x1800` | 0x0001–0x000A | Generic Access (standard) |
| `0x1801` | 0x000B–0x000E | Generic Attribute (standard) |
| `0x180A` | 0x000F–0x0019 | Device Information (standard) |
| `0xFFE0` | 0x001A–0x001E | Pump notification channel (responses) |
| `0xFFE5` | 0x001F–0x0022 | Channel for writing commands to the pump |
| `0xFF90` | 0x0023–0x003E | Vendor service (FF91–FF99); no command/response traffic observed |
| `0xFFC0` | 0x003F–…      | Presumed authorization channel (see §3, Stage B) |

### 1.2. Protocol characteristics
- **Pump responses (pump → phone):** characteristic `0xFFE4`, value handle `0x001C`, property
  `NOTIFY`. This is where response frames arrive; many notifications were observed on this handle
  over the course of a connection session.
- **Commands to the pump (phone → pump):** characteristic `0xFFE9`, value handle `0x0021`,
  properties `WRITE` / `WRITE_NR`.
- **Channel `0xFFC0`:** write `0xFFC1` (value `0x0041`, `WRITE`) and notification `0xFFC2`
  (value `0x0044`, `NOTIFY`) — presumed authorization; details in §3 (Stage B).
- Service `0x180A` and the vendor service `0xFF90` (FF91–FF99) carry device information and
  vendor fields; no command/response protocol exchange was observed over them.

### 1.3. MTU negotiation
The client requests ATT MTU `517`; the pump grants `251`.

### 1.4. Enabling notifications
Notifications are enabled by writing `01 00` to the CCCD: `@0x001D` (for `0xFFE4`) and `@0x0045`
(for `0xFFC2`).

## 2. Frame format

**Status: 🟢 confirmed** (RESEARCH_EN.md: hypothesis — Step 004; verified against all archived
captures of the window — Step 028). In the window there are 1779 commands and 6534 responses; the
structure below holds for all of them. The identity block of commands is shown as `<identity>`.

### 2.1. Command frame (phone → pump, characteristic `0xFFE9`)
| Offset | Size | Field | Note |
|---|---|---|---|
| 0 | 1 | marker | always `0x35` |
| 1 | 1 | length | total frame length in bytes |
| 2 | 1 | field-2 | `0x00` for all 1779 commands in the window; purpose not established |
| 3 | 1 | class | `0xA3` — read object; `0xA1` — control/write |
| 4 | 1 | object/operation code | e.g. `0x00`, `0x08`, `0x21`, `0x26`, `0x31`, `0x33` |
| 5 | 1 | index/selector | `0xAA` — no index; otherwise a specific index/page |
| 6..17 | 12 | identity | ASCII `APEX`+serial number (`<identity>`) |
| 18..N-3 | var | payload | for commands with a parameter (e.g. setting the time) |
| N-2..N-1 | 2 | CRC | CRC-16/MODBUS, little-endian |

A frame without a parameter is 20 bytes (6-byte header + 12-byte identity + 2-byte CRC).
Example (read status): `35 14 00 a3 00 aa <identity> 98 86`.

### 2.2. Response frame (pump → phone, characteristic `0xFFE4`)
| Offset | Size | Field | Note |
|---|---|---|---|
| 0 | 1 | marker | always `0xAA` |
| 1 | 1 | length | total frame length; a frame may span multiple notifications |
| 2 | 1 | field-2 | depends on the object: `0x80` for `a3/21`, `0x25`/`0x26` for `a3/26`, `0x08` for `a3/08`, `0x00`/`0x01` for others; purpose not established |
| 3 | 1 | class | echo of the command's class (`0xA3`/`0xA1`/`0xA5`) |
| 4 | 1 | object code | echo of the command's code |
| 5 | 1 | record index | `00,01,02,…` for multi-record objects; `0xAA` for single-record ones |
| 6..N-3 | var | object data | **carries no identity** |
| N-2..N-1 | 2 | CRC | CRC-16/MODBUS, little-endian |

- A long response arrives as several notifications over `0xFFE4` and is reassembled using the
  length field.
- **Control acknowledgment:** class `0xA1`, code `0x55` (`A1/55`) — acknowledgment of a write
  command; it does not name the command by name.
- **Rejection:** `A1/A5 00 00` — response to command `a1/34` arriving at a locked pump (§5.1, bit
  `0x10`); hypothesis — "command rejected." 🟡 — Step 034, #56 (single observation).

### 2.3. Checksum
**CRC-16/MODBUS** (polynomial `0x8005`, init `0xFFFF`, reflected in/out, xorout `0x0000`),
appended **little-endian**. Verified against the window archive: correct for all 1779 commands and
6284 `A3`/`A1` responses (Step 028).

### 2.4. Timestamp (common field)
Six bytes `YY MM DD HH MM SS` (plain hex bytes, not BCD). Example: `1a 09 10 10 16 14` =
2026-09-16 16:22:20 (cross-checked against capture time). Appears in status and log objects, and as
the payload of the set-time command (§5).

### 2.5. Length field in `A5/03`
For classes `A3`/`A1`, field `[1]` = the full frame size including CRC (6284 responses in the
window). For the periodic `A5/03`, field `[1]` = `0x06` = the size **without CRC** (`total − 2`):
frame `aa0600a50300` + CRC `80c2`, all 250 frames in the window identical (Step 028) — 🟢. The
reason for the difference between classes is not established. `tools/hci_frames.py` cuts the
response by the length field, so the CRC of `A5/03` is not captured by parsing (a known tool
limitation).

## 3. Session establishment and authorization

**Status: 🟢 confirmed** (RESEARCH_EN.md, Step 001 and Step 003; materials #4-6). The pump requires
password authorization on every connection.

### 3.0. How the pump presents itself over the air
The pump is a peripheral BLE device, advertising continuously (while not connected). In the window's
captures its frames look like this (the device address is not given in the documents — `<address>`):

| Frame | Content |
|---|---|
| ADV | `Flags` = `06` (LE General Discoverable, no BR/EDR); **incomplete list of 16-bit UUIDs: `0xFFE0`, `0xFFE5`**; manufacturer data — 16 bytes `<manufacturer-data>` (the first bytes are constant, the tail varies frame to frame) |
| SCAN_RSP | **full name `APEX<serial>`** — the same identity block as in commands (§2.1); connection interval range `0x0010`–`0x0018` (20–30 ms); TX Power `5` |

That is, the pump's serial number is visible over the air **before** connection and before
authorization: it also serves as the device name by which the app finds the pump (§3.1). Services
`0xFFE0` (commands/responses) and `0xFFE5` (authorization) are advertised — the set of services is
known even before connection.
🟢 — Step 051; across all captures of the window: 572 pump advertising frames, four distinct
payloads.

### 3.1. Selecting the pump
Connection is initiated by selecting the pump by its **serial number**: the user enters the serial
number → the pump appears in the list → tapping the row → connection.

### 3.2. Password (pump Bluetooth password)
The source of the password is the pump's "STATUS" screen, the `B/P:` line (right after the `S/N:`
line). It is **six decimal digits**.

### 3.3. Connection sequence
1. Enable verdict notifications: write `01 00` to CCCD `0x0045` (characteristic `0xFFC2`).
2. Write the password to `0xFFC1` (value `0x0041`): **12 bytes** — the six ASCII password digits,
   written twice in a row (value not given, `<password>`).
3. Verdict: a notification on `0xFFC2` (value `0x0044`), **1 byte**. Values `0x00` (the first
   sessions, Steps 001/003) and `0x01` (sessions after the password change, Step 052) were both
   observed — **both lead to a working session** (a normal command flow follows either one). So the
   verdict is not a simple success/failure flag; its exact meaning is not established. No
   authorization failure was observed in the window's captures.
4. MTU negotiation (§1.3).
5. Enable response notifications: write `01 00` to CCCD `0x001D` (characteristic `0xFFE4`).
6. From here on — commands/responses (§4-§5).

### 3.3.1. Connection timings
Across all connections in the window (09.16 16:22, 09.16 16:52, 09.17 20:52) the picture is the
same, counted from the connection-established event:

| Step | Delay |
|---|---|
| enabling verdict notifications (CCCD `0x0045`) | +1.34…1.39 s |
| writing the password to `0xFFC1` | +1.36…1.64 s |
| **verdict `00` (success)** | **+0.01…0.10 s after the password write** |
| MTU request (517) | immediately after the verdict |
| enabling response notifications (CCCD `0x001D`) | +1.44…1.84 s |
| first `a1` command | +3.43…3.84 s |

The pump responds to the password within tens of milliseconds — **there is no artificial delay on
successful authorization**. All attempts in the captures used the correct password. Behavior on an
incorrect password (delay, attempt limiting) **is not studied**: per project rule 9 we do not brute
force the password and do not send the pump deliberately incorrect data — only what legitimately
passes over the radio link is recorded.
🟢 (successful path) — Step 051.

### 3.4. Confidence
The structure is confirmed by two sessions (conn `0x0003`, conn `0x0005`) and an independent
radio↔pump-screen cross-check: the ASCII digits in the `0xFFC1` write match the `B/P:` string on the
pump's screen (material #6). The encoding of the authorization write as "six ASCII digits twice" is
established for two passwords: the original one and the new one (after the 09.18 password change,
Step 052, channel `0x0041` — the same six digits twice). The password-change command is `a1/35`
(§5); its payload encodes the password **differently**, in an internal non-ASCII representation, and
is not decoded in the documents (rule 5).

## 4. Response objects (read)

Class `0xA3`. The catalog is based on frames from the research window (RESEARCH_EN.md, Step 028).
Fields `a3/00` and `a3/0c` — §4.1, §4.2 (tables generated from the registry); a byte-by-byte map of
all objects is in `OBJECTS_EN.md`.

| Code | Records | Frame size | Purpose | Status |
|---|---|---|---|---|
| `0x00` | 1 | 96 | main pump status — §4.1 | fields — §4.1 |
| `0x0C` | 1 | 28 | brief status — §4.2 | fields — §4.2 |
| `0x08` | 8 (idx 00–07) | 104 | basal profiles A–H (record = profile number): 48 × u16LE, 0.025 U/h, half-hour intervals; the "Total" on screen = sum × 0.0125; active — `a3/00` off12, selection — `a1/04` (0 = A … 7 = H), write — `a1/00` (into the active profile) | 🟢 — Steps 026, 043, 044; totals A 18.675 / B 15.25→15.775 / C 20.0 / D 0 cross-checked against the screen (#68) |
| `0x0A` | 1 | 20 | descriptor of the current (last started) TBR — §4.7 | fields — §4.7 |
| `0x0B` | 1 | 26 | descriptor of the last completed TBR — §4.8 | fields — §4.8 |
| `0x21` | 10 (idx 00–09) | 22 | bolus log, newest records first — §4.4 | fields — §4.4 |
| `0x02` | 47 (idx 00–…) | 102 | basal change log: timestamp + 48 half-hour profile rates — §4.6 | fields — §4.6 |
| `0x01` | 128 (idx 00–7f) | 14 | detailed bolus log (record structure = `a3/21`, §4.4); read when history is opened — §4.4 | fields — §4.4; 🟢 — Steps 040, 041, 045, 047 |
| `0x27` | 10 (idx 00–09) | 14 | TBR log, newest records first — §4.5 | fields — §4.5 |
| `0x26` | 10 (idx 00–09) | 10 | daily doses for 10 days — §4.10 | fields — §4.10 |
| `0x06` | 38 (idx 00–…) | 10 | daily doses, long history — §4.10 (same structure) | fields — §4.10 |
| `0x04` | 11 (idx 00–…) | 10 | reservoir refill history — §4.15 | fields — §4.15 |
| `0x03` | 12 (idx 00–…) | 8 | alarm history — §4.16 | fields — §4.16 |
| `0x07` | 1 | 254 | bolus calculator settings; write — command `a1/15`; read when "Bolus Settings" is opened and after a write — §4.9 | fields — §4.10 |
| `0x31` | 1 | 8 | versions: bytes 3..5 — firmware (1.1.1), 6..7 — exchange protocol (4.12); read on connect — §4.11 | fields — §4.11 |

Class `0xA5` (unsolicited frames):

| Code | Periodicity | Frame | Purpose | Status |
|---|---|---|---|---|
| `0x03` | 180.0 ± 0.2 s | `aa0600a50300` + CRC `80c2` | pump "heartbeat," payload constant; 250 frames over the 12.5 h window | 🟢 — Steps 005, 028 |

### 4.1. Fields of object `a3/00` (main status, 88 bytes of data)
Analysis is conducted within the research window **from 16:34 onward** (RESEARCH_EN.md Step 007);
earlier frames reflect user operations performed before the study began and are not included in the
findings.

The table is generated from the `tools/fields.py` registry and verified against archived captures
(`tools/verify_fields.py`); it is not edited manually.

<!-- gen:a3_00 -->
| Offset | Field | Encoding | Command | Status |
|---|---|---|---|---|
| 0 (u8) | battery indicator (bars) | number of bars by voltage `a3/0c` off3; the observed threshold 3→2 — between 1.34 and 1.35 V (steps 4→3 and 2→1 not observed in the window) | — | 🟢 — steps 024, 048; #20, #38, #75; `3` at 1.35–1.37 V (686 frames) and steadily `2` from 09.18 04:14, when voltage dropped to 1.34 V (Step 048). Brief single dips `3`→`2` at a rounded 1.35 V (11 pairs over two days) are a sag under load (motor, screen backlight) right at the threshold: `a3/0c` shows voltage rounded to 0.01 V and this is not visible there. The charge percentage shown on the app screen is computed by the app itself — there is no such field in the pump's frames |
| 1 (u8) | alarm signal type | `0`=Sound; `1`=Vibration; `2`=Sound and vibration (menu item order, #25) | `a1/32` [1] | 🟢 — steps 013, 017; #16, #17, #24, #25 |
| 2 (u8) | bolus speed | `0`=Normal; `1`=Low | `a1/32` [0, bit `0x01`] | 🟢 — steps 011, 014; #12, #13, #18, #19; the full menu was not captured; both values were observed |
| 3 (u8) | pump screen brightness | `0`=10 %; `1`=30 %; `2`=50 %; `3`=60 %; `4`=80 %; `5`=100 % (menu item order, #29) | `a1/32` [2] | 🟢 — steps 013, 019; #16, #17, #28, #29; the value is the menu item index |
| 4 (u8) | extended bolus / BG reminder | bit field: bit0 = "Extended bolus" (enables stretched and dual-wave bolus), bit1 = "BG reminder"; in `a3/00` off4 = byte × 2 (`00`/`02`/`04`/`06`) | `a1/32` [6] (status = byte × 2) | 🟢 — steps 011, 012, 015; #12, #13, #14, #20, #21 |
| 5 (u8) | keypad lock | `0`=off; `1`=on | `a1/32` [0, bit `0x02`] | 🟢 — steps 013, 023; #16, #17, #31, #36, #37 |
| 6 (u8) | pump auto power-off | `0`=off; `1`=on | `a1/32` [0, bit `0x04`] | 🟢 — steps 013, 022; #16, #17, #31, #34, #35, #37 |
| 7 (u8) | pump auto power-off time | number, hours | `a1/32` [3] | 🟢 — steps 013, 022; #16, #17, #34, #35; number of hours, not an index; the visible part of the menu shows 2–8 h (#35), 1 h — on screen (#17); the full list was not captured |
| 8 (u8) | "insulin running low" — units | number, U | `a1/32` [4] | 🟢 — steps 013, 022; #16, #17, #25; number of units; menu not captured |
| 9 (u8) | "insulin running low" — time | number of half-hours (not a menu index): `11`=05:30, `13`=06:30 | `a1/32` [5] | 🟢 — steps 013, 022, 023; #16, #17, #25, #37; menu 02:00–12:00 in steps of 0:30 (`4`…`24`) — per the user's account; #37 shows 02:00–05:00 |
| 10 (u8) | basal patterns | `0`=off; `1`=on | `a1/32` [0, bit `0x08`] | 🟢 — steps 049; #75, #76; 09.18 04:35:17 `a1/32` byte[0] `00→08`; `a3/00` off10 `0→1`; on screen the "Basal patterns" toggle is on and a list of four patterns appeared (#76). Previously byte off10 and bit `0x08` were unparsed |
| 11 (u8) | pump lock | `0`=unlocked; `1`=locked | `a1/32` [0, bit `0x10`] | 🟢 — steps 034, 053; #56, #57, #78, #79; enabled by the app (`a1/32` byte[0] bit `0x10`), lifted only from the pump's own menu — off11 `1→0` with no app command (Step 034); while locked, a command arriving at the pump is rejected with acknowledgment `a1/a5` (Steps 034, 053). **An already-running delivery is not interrupted by the lock:** on 09.18 an extended bolus kept being delivered (notifications `a1/a1`) after `off11 0→1` (Step 053); in the app the bolus/TBR/Stop buttons are locked out |
| 12 (u8) | active basal profile | `0`=A; `1`=B; `2`=C; `3`=D; `4`=E; `5`=F; `6`=G; `7`=H (menu item order, #70) | `a1/04` [0] | 🟢 — steps 043, 044; #67, #68, #69, #70; record number of the active `a3/08` profile; over the air 0–3 (A–D) and 7 (H, 09.18 02:06:59, #70); 4–6 — inferred from menu item order; before 09.18, `0` in all archives |
| 13 (u8) | daily dose limit | `0`=off; `1`=on | `a1/32` [0, bit `0x20`] | 🟢 — steps 013, 021; #16, #17, #25, #32, #33, #37 |
| 14..15 (u16LE) | screen auto-off | × 0.1 s | `a1/32` [8..9 (u16LE)] | 🟢 — steps 013; #16, #17, #31; menu not captured; over the air 150 and 600 |
| 16..17 (u16LE) | delivered insulin counter | × 0.025 U | — | 🟢 — steps 007, 024, 045; #8, #38, #71; increment matches the delivery rate (0.5 and 0.9 U/h, TBR 6.0 U/h); **per day**: reset to zero at midnight observed twice — 09.16→17 (2777 → 1) and 09.17→18 (903 → 1), Step 045 |
| 20..21 (u16LE) | total daily dose (limit) | number, U | `a1/32` [10..11 (u16LE)] | 🟢 — steps 013, 021, 022; #16, #17, #32, #33, #34; number of units, not an index; menu 50–300 in steps of 50 (#33) |
| 24..25 (u16LE) | maximum basal | × 0.025 U/h | `a1/32` [12..13 (u16LE)] | 🟢 — steps 010; #11; 8.0→7.7 (320→308) |
| 26..27 (u16LE) | maximum bolus | × 0.025 U | `a1/32` [14..15 (u16LE)] | 🟢 — steps 009; #10, #21; 12.0→12.3 (480→492) |
| 28..29 (u16LE) | bolus preset "Breakfast A 5:00–6:59" | × 0.025 U | `a1/11` [0..1 (u16LE)] | 🟢 — steps 012, 025; #14, #15, #40, #41 |
| 30..31 (u16LE) | bolus preset "Breakfast B 7:00–9:59" | × 0.025 U | `a1/11` [2..3 (u16LE)] | 🟢 — steps 012, 025; #14, #15, #40, #41 |
| 32..33 (u16LE) | bolus preset "Lunch A 10:00–11:59" | × 0.025 U | `a1/11` [4..5 (u16LE)] | 🟢 — steps 012, 025; #14, #15, #40, #41 |
| 34..35 (u16LE) | bolus preset "Lunch B 12:00–14:59" | × 0.025 U | `a1/11` [6..7 (u16LE)] | 🟢 — steps 012, 025; #14, #15, #40, #41 |
| 36..37 (u16LE) | bolus preset "Dinner A 15:00–17:59" | × 0.025 U | `a1/11` [8..9 (u16LE)] | 🟢 — steps 012, 025; #14, #15, #40, #41 |
| 38..39 (u16LE) | bolus preset "Dinner B 18:00–21:59" | × 0.025 U | `a1/11` [10..11 (u16LE)] | 🟢 — steps 012, 025; #14, #15, #40, #41 |
| 40..41 (u16LE) | bolus preset "Night A 22:00–23:59" | × 0.025 U | `a1/11` [12..13 (u16LE)] | 🟢 — steps 012, 025; #14, #15, #40, #41 |
| 42..43 (u16LE) | bolus preset "Night B 00:00–4:59" | × 0.025 U | `a1/11` [14..15 (u16LE)] | 🟢 — steps 012, 025; #14, #15, #40, #41 |
| 44..49 (6 bytes) | status timestamp | `YY MM DD HH MM SS`, byte = value (not BCD) | — | 🟢 — steps 006, 007, 038; #8, #61; in the regular (once-a-minute) status the seconds are `00`; nonzero seconds arrive when status is re-read at the moment of an event — time set, profile change, bolus, TBR (18 cases over two days, Step 045) |
| 50 (u8) | pump language | `0`=Russian; `1`=English (menu item order, #31) | `a1/32` [0, bit `0x40`] | 🟢 — steps 013, 020; #16, #17, #30, #31, #37 |
| 51 (u8) | TBR active | `0`=no; `1`=yes | — | 🟢 — steps 024; #38, #39; 1 after `a1/02`; 0 after `a1/05` (cancel) |
| 52..55 (u32LE) | reservoir remaining | × 0.001 U | — | 🟢 — steps 007; #6, #8, #9, #38, #39 |
| 76..77 (u16LE) | current basal rate (per profile) | × 0.025 U/h; `ff ff` — delivery stopped | — | 🟢 — steps 007, 024, 026, 027; #8, #9, #38, #42, #43, #44, #45; value of the active profile's current half-hour interval (`a3/08` record = off12; Step 043): 20 (0.5) from 16:00, 36 (0.9) from 00:00, 29 (0.725) from 05:00 after the profile write; unchanged during a TBR |
| 78..79 (u16LE) | time of last delivery stop | byte off78 — hours, off79 — minutes (pump time); written by the stop command `a1/21 01`, unchanged on start | — | 🟢 — steps 027; #44, #45; in the window: 02:25 (stop before the window, 09.16 02:25:20) → 04:48 (stop 09.17 04:48:43); before the window — 7 more stops with the same rule |
| 80..81 (u16LE) | TBR — value | meaning depends on type (byte[0]): `01` — U/h in steps of 0.025; `00` — percent. In `a3/00` off80 — the resulting rate, 0.025 U: at `01` equal to the value, at `00` = ⌊off76 × % / 100⌋ | `a1/02` [2..3 (u16LE)] (per the rule, see encoding) | 🟢 — steps 024; #38, #39; rounding down verified on one value (36 × 113 % = 40.68 → 40) |
| 82..83 (u16LE) | TBR — type | `0`=percent; `1`=U/h | `a1/02` [0] | 🟢 — steps 024; #38, #39 |
| 84..85 (u16LE) | TBR — duration | steps of 15 min; in `a3/00` off84 — minutes (byte × 15) | `a1/02` [1] (status = byte × 15) | 🟢 — steps 024; #38, #39 |
| 86..87 (u16LE) | TBR — elapsed | number, min | — | 🟢 — steps 024, 031; #38, #39, #51; minutes since TBR start: rises +1/min (per polling +3 over 3 min), 0 when off51=0; remaining on screen = off84−off86 (18:20: 150−5=145=02:25, #51) |
<!-- /gen:a3_00 -->

**IOB** (active insulin) is not found in `a3/00` → presumably computed by the app (🟡).

<!-- gen:a3_00_unknown -->
**Unparsed offsets** (24 of 88 bytes): 18..19, 22..23, 56..75 — byte-by-byte in `OBJECTS_EN.md`.
<!-- /gen:a3_00_unknown -->

**off0** is described in the table as a hypothesis (🟡): battery indicator by voltage steps; the
verification condition is given in the same place.

### 4.2. Fields of object `a3/0c` (brief status, 20 bytes of data)
<!-- gen:a3_0c -->
| Offset | Field | Encoding | Command | Status |
|---|---|---|---|---|
| 2 (u8) | alarm signal duration | `0`=Long; `1`=Normal; `2`=Short (menu item order, #27) | `a1/32` [7] | 🟢 — steps 013, 018; #16, #17, #25, #26, #27 |
| 3 (u8) | battery voltage | × 0.01 V | — | 🟢 — steps 003, 006; #5, #9 |
| 4 (u8) | sound mode | `0`=off; `1`=on | `a1/34` [0] | 🟢 — steps 011, 016; #12, #13, #22, #23 |
| 5 (u8) | sound mode step | `0`=0.1 U; `1`=0.5 U; `2`=1.0 U; `3`=5.0 U (menu item order, #41) | `a1/34` [1] | 🟢 — steps 011, 025; #12, #13, #41; the value is the menu item index |
<!-- /gen:a3_0c -->

<!-- gen:a3_0c_unknown -->
**Unparsed offsets** (16 of 20 bytes): 0..1, 6..19 — byte-by-byte in `OBJECTS_EN.md`.
<!-- /gen:a3_0c_unknown -->

The charge percentage (46%) was not found in the frame → presumably computed by the app from
voltage (🟡).

### 4.3. Insulin dosing unit
The pump's insulin quantities are encoded in steps of **0.025 U**. Confirmed by value changes:
max. bolus (480→492 = 12.0→12.3), max. basal (320→308 = 8.0→7.7), bolus presets (8 slots, Step
025), TBR (240 = 6.0 U/h, Step 024). The values of the basal profiles (`a3/08`) are in the same
units: 🟢 — Steps 043, 044, 046; the raw rates of four profiles matched the "Basal Schedule" screen
(36 → 0.9 · 29 → 0.725 · 40 → 1.0 · 20 → 0.5 · 50 → 1.25 U/h), and the sums of the 48 half-hour
rates × 0.0125 matched the "Total" line (18.675 / 15.25 / 15.775 / 20.0 / 0.0 U, #68). The delivery
step is also visible directly: boluses of 0.025 / 0.05 / 0.075 U are raw `1` / `2` / `3` (Step 045,
#72).

### 4.4. Bolus log — object `a3/21`
Ten records of 14 bytes each (idx 00–09), record 00 is the last bolus; read on every polling cycle.
For a **simple** bolus the dose is in off6/off8, bytes 10..13 are zero. For an **extended** bolus
(Step 030) off6/off8 = 0, and bytes 10..11 = the programmed dose, 12..13 = actually delivered
(0.025 U). The table is generated from the registry.

<!-- gen:a3_21 -->
| Offset | Field | Encoding | Command | Status |
|---|---|---|---|---|
| 0..4 (5 bytes) | bolus log — time | `YY MM DD HH MM` (byte = value) | — | 🟢 — steps 029; #46, #47; records 00–05 matched the "Bolus History" screen by date and time (16:14, 16:11, 16:06, 16:02, 15:55, 14:38) |
| 5 (u8) | bolus log — record position within the minute | `59` for the newest record of the minute; for earlier records of the same minute — `58`, `57`, … | — | 🟢 — steps 029, 045; #46, #71, #72; not seconds: a series of three boluses on 09.18 02:18 gave `59`,`58`,`57`, and in the 02:28 series (0.025 → 0.05 → 0.075 U) the byte of the already-created record was overwritten 59→58→57 as new records appeared; the order of records and doses matched the "Bolus History" screen (#72) |
| 6..7 (u16LE) | bolus log — immediate part: requested | × 0.025 U | — | 🟢 — steps 029, 030, 031, 041; #46, #47, #50, #64; immediate (simple) part, requested (= command a1/12); for a purely extended bolus = 0. Combo bolus: simple 1.15 + extended 0.85 (#64, Step 041) |
| 8..9 (u16LE) | bolus log — immediate part: delivered | × 0.025 U | — | 🟢 — steps 029, 031, 041; #46, #50, #64; immediate part, delivered; on cancellation < off6 (2.0→0.55 Step 031; 1.15→0.9 combo Step 041); for a completed one = off6; for a purely extended one = 0 |
| 10..11 (u16LE) | bolus log — extended part: programmed | × 0.025 U | — | 🟢 — steps 030, 041, 046; #48, #49, #64, #73, #74; extended part, programmed: 1.0 (Step 030), 0.85 in the combo bolus (#64, Step 041), 2.0 (Step 046); for a purely simple one = 0 |
| 12..13 (u16LE) | bolus log — extended part: delivered | × 0.025 U | — | 🟢 — steps 030, 041, 046; #48, #49, #64, #73, #74; extended part, delivered: 0.2 U (Step 030), 0 in the canceled combo (Step 041), 0.1 U on canceling a 2-unit bolus after 3 min (Step 046, screen "Extended 0.1 U 00:45") |
<!-- /gen:a3_21 -->

### 4.5. TBR log — object `a3/27`
Ten records of 14 bytes each (idx 00–09), record 00 is the last completed TBR; shows only
**completed** TBRs (the active one is not included). Structure — start (`a1/02`) plus the actually
delivered dose. The table is generated from the registry.

<!-- gen:a3_27 -->
| Offset | Field | Encoding | Command | Status |
|---|---|---|---|---|
| 0..5 (6 bytes) | TBR log — start time | `YY MM DD HH MM SS` (byte = value) | — | 🟢 — steps 032; #51, #52; TBR start time; records 00–05 matched the "Temp Basal History" screen |
| 6..7 (u16LE) | TBR log — type | `0`=percent; `1`=U/h | — | 🟢 — steps 032; #52, #53; same as byte[0] of command a1/02 |
| 8..9 (u16LE) | TBR log — duration | × 15 min | — | 🟢 — steps 032; #52, #53; × 15 min, same as byte[1] of command a1/02 |
| 10..11 (u16LE) | TBR log — value | meaning per type off6: percent or 0.025 U/h (as in the value of command a1/02) | — | 🟢 — steps 032; #51, #52, #53 |
| 12..13 (u16LE) | TBR log — delivered | × 0.025 U | — | 🟢 — steps 032; #52, #53; actually delivered over the duration of the TBR |
<!-- /gen:a3_27 -->

### 4.6. Basal change log — object `a3/02`
Record of 102 bytes: bytes 0..5 — timestamp of the profile change (`YY MM DD HH MM SS`); bytes
6..101 — **48 u16LE values** (half-hour intervals 00:00…23:30, step 0.025 U/h) — a snapshot of the
basal profile at the moment of the change. The daily dose shown on the "Basal Changes" screen =
sum of the 48 rates × 0.025 × 0.5 (half-hour). Verified (Step 033): record 00 (09.17 04:44) —
profile `36×10, 29×6, 40×16, 20×16` → 18.675 U; records 01–03 — 19.2 / 20.0 / 3.6 U — matched the
screen. The timestamp field is in the registry (§4.6, `a3/02`).

### 4.7. Current TBR — object `a3/0a`
Descriptor of the last started TBR (updated at the start of `a1/02`); while a TBR is active `a3/00`
off51 = 1. Bytes 0..5 and 7..12 — start time (twice); byte 13 — type; 14..15 — duration (×15 min);
16..17 — value (% or 0.025 U/h); 18..19 — delivered (0.025 U), accumulates over the run and is
reset at the end. Values equal those of command `a1/02` (Step 035). The table is generated from
the registry.

<!-- gen:a3_0a -->
| Offset | Field | Encoding | Command | Status |
|---|---|---|---|---|
| 0..5 (6 bytes) | current TBR — app command (source) | `YY MM DD HH MM SS` — time of the app command; `00 00 00 00 00 00` if the TBR was started **from the pump** | — | 🟢 — steps 035, 037; #38, #39, #52, #60; source of the start (Step 037): filled in when started from the app (= the off7 start), zeros — when started from the pump (then there is no a1/02 command) |
| 7..12 (6 bytes) | current TBR — start (actual) | `YY MM DD HH MM SS` — actual start (always filled in); byte 6 before it is `00` | — | 🟢 — steps 035, 037; #38, #39, #52, #60 |
| 13 (u8) | current TBR — type | `0`=percent; `1`=U/h | — | 🟢 — steps 035; #38, #39, #52; same as byte[0] of command a1/02 |
| 14..15 (u16LE) | current TBR — duration | × 15 min | — | 🟢 — steps 035; #38, #39, #52; ×15 min, same as byte[1] of a1/02 |
| 16..17 (u16LE) | current TBR — value | % or 0.025 U/h per type (value of command a1/02) | — | 🟢 — steps 035; #38, #39, #52 |
| 18..19 (u16LE) | current TBR — delivered | × 0.025 U | — | 🟢 — steps 035; #38, #39, #52; accumulates during delivery, resets at the end; final = `a3/0b`/`a3/27` off12 |
<!-- /gen:a3_0a -->

### 4.8. Last completed TBR — object `a3/0b`
Descriptor of the last **completed** TBR (updated at the moment it ends/is canceled). Byte 0 —
counter/type (not established); 1..6 and 7..12 — start time; byte 13 — type; 14..15 — duration;
16..17 — value; 18..23 — end time; 24..25 — delivered (0.025 U). Delivered matches `a3/27` off12;
end = start + duration (Step 035). The table is generated from the registry.

<!-- gen:a3_0b -->
| Offset | Field | Encoding | Command | Status |
|---|---|---|---|---|
| 0 (u8) | completed TBR — how it ended | `1`=ran to completion; `2`=canceled from the pump; `3`=canceled from the app | — | 🟢 — steps 035, 037; #38, #52, #54, #60; Step 037: 1 = ended ≈ start+duration; 2 = canceled from the pump (no a1/05 command); 3 = canceled from the app (a1/05 present). Value 0 was not observed |
| 1..6 (6 bytes) | completed TBR — app command (source) | `YY MM DD HH MM SS` — time of the app command; zeros if started **from the pump** | — | 🟢 — steps 035, 037; #38, #52, #54, #60; source of the start, same as off0 of `a3/0a` (Step 037) |
| 7..12 (6 bytes) | completed TBR — start (actual) | `YY MM DD HH MM SS` — actual start (always filled in) | — | 🟢 — steps 035, 037; #38, #52, #54, #60 |
| 13 (u8) | completed TBR — type | `0`=percent; `1`=U/h | — | 🟢 — steps 035; #38, #52, #54 |
| 14..15 (u16LE) | completed TBR — duration | × 15 min | — | 🟢 — steps 035; #38, #52, #54 |
| 16..17 (u16LE) | completed TBR — value | % or 0.025 U/h per type | — | 🟢 — steps 035; #38, #52, #54 |
| 18..23 (6 bytes) | completed TBR — end | `YY MM DD HH MM SS` | — | 🟢 — steps 035; #38, #52, #54; end time; start+duration (120 %: 18:15+2:30=20:45, end 20:46, #54) |
| 24..25 (u16LE) | completed TBR — delivered | × 0.025 U | — | 🟢 — steps 035; #38, #52, #54; = `a3/27` off12 (6 U/h → 96 = 2.4 U; 113 % → 26 = 0.65 U) |
<!-- /gen:a3_0b -->

### 4.9. Bolus calculator — object `a3/07`
246 bytes of data; written by command `a1/15` (§5), whose payload is byte-for-byte equal to bytes
0..243 of the object. Bytes 244..245 — CRC-16/MODBUS of bytes 0..243, recomputed by the pump (not
part of the command). Step 036, #58, #59.

- **Interval tables:** 12 records of "value · half-hour start slot" (slot 0..47 = 00:00…23:30);
  slot `48` is an empty record (the value in it is a filler). Records go in increasing slot order;
  on the app screen — a "time → value" list, the "Bolus Settings" tile shows the record for the
  current slot.
- **Separate storage per unit:** for grams and CU (carb units), and for mmol/L and mg/dL — separate
  tables. Switching units (off1) changes only the bit; values are not recalculated (22:27, 22:32,
  22:54 — only off1 and CRC).

| off | table | record | scale |
|---|---|---|---|
| 4..51 | carb ratios (grams) | u16LE value · u16LE slot | g/U |
| 52..99 | carb ratios (CU) | u16LE · u16LE | × 0.05 U/CU |
| 100..147 | sensitivity (mmol/L) | u16LE · u16LE | × 0.1 mmol/L/U |
| 148..195 | sensitivity (mg/dL) | u16LE · u16LE | mg/dL/U |
| 196..219 | target BG (mmol/L) | u8 · u8 | × 0.1 mmol/L |
| 220..243 | target BG (mg/dL) | u8 · u8 | mg/dL |

The field table is generated from the registry.

<!-- gen:a3_07 -->
| Offset | Field | Encoding | Command | Status |
|---|---|---|---|---|
| 0 (u8) | bolus calculator | `0`=off; `1`=on | `a1/15` [0] | 🟢 — steps 036; #58, #59; off 22:24:50, on 22:25:22 |
| 1 (u8) | carb units | `0`=grams; `1`=CU | `a1/15` [1, bit `0x01`] | 🟢 — steps 036; #58, #59; switching changes only the bit — tables off4 (grams) and off52 (CU) are stored independently |
| 1 (u8) | BG units | `0`=mmol/L; `1`=mg/dL | `a1/15` [1, bit `0x10`] | 🟢 — steps 036, 038; #58, #59, #61, #62; switching changes only the bit — the mmol/L tables (off100, off196) and mg/dL tables (off148, off220) are stored independently |
| 2..3 (u16LE) | active insulin time | number, min | `a1/15` [2..3 (u16LE)] | 🟢 — steps 036; #58, #59 |
| 4..51 (48 bytes) | carb ratios (grams) | 12 records × (u16LE g/U · u16LE half-hour start slot 0..47); slot 48 — empty record (§4.9) | `a1/15` [4..51 (u16LE)] | 🟢 — steps 036; #58, #59; 22:31 screen 9/8/7 g/U from 00:00/15:00/20:00 = (9,0),(8,30),(7,40); tile "7 g/U" 22:42 — record of the current slot |
| 52..99 (48 bytes) | carb ratios (CU) | 12 records × (u16LE × 0.05 U/CU · u16LE half-hour slot); slot 48 — empty record (§4.9) | `a1/15` [52..99 (u16LE)] | 🟢 — steps 036; #58, #59; 22:54 screen 0.50/1.00 U/CU from 00:00/04:00 = (10,0),(20,8); tile "1.0 U/CU" 22:26 and "0.1 U/CU" 22:55 (record (2,25)) — current slot |
| 100..147 (48 bytes) | sensitivity (mmol/L) | 12 records × (u16LE × 0.1 mmol/L/U · u16LE half-hour slot); slot 48 — empty record (§4.9) | `a1/15` [100..147 (u16LE)] | 🟢 — steps 036; #58, #59; 22:55 screen 4.0/4.1/4.7 from 00:00/11:30/22:30 = (40,0),(41,23),(47,45); tile "4.1" 22:26, "4.7" 22:55 |
| 148..195 (48 bytes) | sensitivity (mg/dL) | 12 records × (u16LE mg/dL/U · u16LE half-hour slot); slot 48 — empty record (§4.9) | `a1/15` [148..195 (u16LE)] | 🟢 — steps 036; #58, #59; 22:42 screen 50/54 from 00:00/03:30 = (50,0),(54,7); tile "54" 22:42 |
| 196..219 (24 bytes) | target BG (mmol/L) | 12 records × (u8 × 0.1 mmol/L · u8 half-hour slot); slot 48 — empty record (§4.9) | `a1/15` [196..219 (u16LE)] | 🟢 — steps 036, 042; #58, #59, #65, #66; on 09.18 00:21 a record was added at 19:00 → 5.8: (56,0),(58,29),(58,38) — screen 5.6/5.8/5.8 at 00:00/14:30/19:00 (#66); the new record took the first empty slot; the mg/dL table did not change |
| 220..243 (24 bytes) | target BG (mg/dL) | 12 records × (u8 mg/dL · u8 half-hour slot); slot 48 — empty record (§4.9) | `a1/15` [220..243 (u16LE)] | 🟢 — steps 036; #58, #59; 22:42 screen 100/107 from 00:00/05:30 = (100,0),(107,11); tile "107" 22:42 |
| 244..245 (u16LE) | calculator block checksum | CRC-16/MODBUS (LE) of bytes 0..243 of the object; not part of command `a1/15` | — | 🟢 — steps 036; #58; matched for all distinct contents in the window |
<!-- /gen:a3_07 -->

### 4.10. Daily doses — objects `a3/26` and `a3/06`
Record of 10 bytes: 0..1 — daily **bolus**, 2..3 — **basal**, 4..5 — **temporary basal** (all
u16LE, 0.025 U), 6..8 — **date** `YY MM DD`, byte 9 — `00`. The total shown on the "Daily Doses"
screen = sum of the three fields. `a3/26` — the last 10 days (read every polling cycle), `a3/06` —
same structure, 38 days. Verified (Step 039): the sums matched the screen row by row (09.17 = 22.3;
09.16 = 69.45; 09.15 = 95.475; …). The table is generated from the registry.

<!-- gen:a3_26 -->
| Offset | Field | Encoding | Command | Status |
|---|---|---|---|---|
| 0..1 (u16LE) | daily dose — bolus | × 0.025 U | — | 🟢 — steps 039; #46, #63; daily bolus; sum of the three fields = total shown on the "Daily Doses" screen |
| 2..3 (u16LE) | daily dose — basal | × 0.025 U | — | 🟢 — steps 039; #46, #63 |
| 4..5 (u16LE) | daily dose — temp. basal | × 0.025 U | — | 🟢 — steps 039; #46, #63 |
| 6..8 (3 bytes) | daily dose — date | `YY MM DD` (3 bytes, no time); byte 9 — `00` | — | 🟢 — steps 039; #46, #63 |
<!-- /gen:a3_26 -->

### 4.11. Versions — object `a3/31`
8 bytes: `00 00 00 | 01 01 01 | 04 0c`. Bytes 0..2 — zero; 3..5 — pump firmware version
(major·minor·patch); 6..7 — exchange protocol version. Matches the pump card in the app: "Firmware
version 1.1.1," "Protocol version 4.12" (#57, #72). The value is unchanged across all captures in
the window. The table is from the registry.

<!-- gen:a3_31 -->
| Offset | Field | Encoding | Command | Status |
|---|---|---|---|---|
| 3..5 (3 bytes) | pump firmware version | three bytes — major·minor·patch: `01 01 01` = 1.1.1 | — | 🟢 — steps 045; #57, #71, #72; unchanged across all captures in the window; on screen "Firmware version 1.1.1" (#57 21:56, #72 02:26) |
| 6..7 (u16LE) | exchange protocol version | two bytes — major·minor: `04 0c` = 4.12 | — | 🟢 — steps 045; #57, #71, #72; unchanged across all captures in the window; on screen "Protocol version 4.12" (#57, #72); bytes 0..2 of the object are zero |
<!-- /gen:a3_31 -->

### 4.12. Class `A1` frames from the pump — acknowledgments and notifications
The pump responds to commands with an acknowledgment and itself sends unsolicited frames about the
progress of delivery. All of them are class `0xA1` (§2.2), payload — after the frame header. The
table is generated from the registry.

<!-- gen:answers -->
| Code | Payload | Purpose | When it arrives | Status |
|---|---|---|---|---|
| `0x55` | `00 00`; for `a1/12`, `a1/13`, `a1/14` — echo of the command payload | command acknowledgment | within 3 s for every `a1` command (176 frames in the window) | 🟢 — steps 028, 045; payload echo was observed for bolus-start commands; for other commands — `00 00` |
| `0xA5` | `00 00` | rejection: command not accepted (pump locked) | for a command arriving at a locked pump (`a1/34` following an `a1/32` lock) | 🟢 — steps 034, 053; two observations: 09.17 21:55:24 (Step 034) and 09.18 16:38:10 (Step 053), both on `a1/34` after a lock; the lock command `a1/32` itself receives a normal acknowledgment `a1/55` |
| `0xA0` | u16LE — accumulated delivered dose, × 0.025 U | progress of a simple bolus's delivery | unsolicited, roughly every ~1 s while the immediate part is running (38 frames) | 🟢 — steps 031, 041, 045; the last value = the delivered dose; on cancellation, delivery stops at the value reached |
| `0xA1` | u16LE — accumulated delivered dose, × 0.025 U | progress of an extended bolus's delivery | unsolicited, in steps of 0.025 U (interval = duration / dose: 135 s, 67 s, 90 s) (15 frames) | 🟢 — steps 030, 046, 047 |
| `0xAA` | u16LE — final delivered dose, × 0.025 U | bolus completion | 1–3 s after the last `a1/a0` (simple) or `a1/a1` (extended); 7 frames | 🟢 — steps 045, 047; does not arrive for a canceled bolus; at this same moment a record appears in the `a3/21`/`a3/01` log |
<!-- /gen:answers -->

### 4.13. Timestamp precision by object
| Object | Field | Format | Seconds |
|---|---|---|---|
| `a3/00` | status timestamp | `YY MM DD HH MM SS` | only in a status re-read at the moment of an event; `00` in regular polling (§6, Step 045) |
| `a3/0b` | end of last TBR | `YY MM DD HH MM SS` | **present** (nonzero in 7 frames) |
| `a3/02` | profile change time | `YY MM DD HH MM SS` | always `00` — record is per-minute |
| `a3/27` | TBR start | `YY MM DD HH MM SS` | always `00` — per-minute |
| `a3/0a` | current TBR start, command time | `YY MM DD HH MM SS` | always `00` — per-minute |
| `a3/0b` | completed TBR start, command time | `YY MM DD HH MM SS` | always `00` — per-minute |
| `a3/21`, `a3/01` | bolus time | `YY MM DD HH MM` (5 bytes) | no seconds: the sixth byte is the record's position within the minute (§4.4) |
| `a3/26`, `a3/06` | daily-dose date | `YY MM DD` (3 bytes) | date only |

That is, the pump's internal clock is kept to minute precision; seconds appear only where the
moment of an event is recorded separately (status at the moment of the event, TBR end). 🟢 — Step
051.

### 4.15. Refill history — object `a3/04`
Log of manual reservoir refills; read when opening "Home → History → Refill History." Record of 10
bytes: 0..5 — time `YY MM DD HH MM SS` (seconds `00`, per-minute); 6..7 — refill volume (u16LE, ×
0.025 U); 8 — type (`1` = "Manual"). All 8 visible records matched the screen (Step 054, #81). The
table is from the registry.

<!-- gen:a3_04 -->
| Offset | Field | Encoding | Command | Status |
|---|---|---|---|---|
| 0..5 (6 bytes) | refill history — time | `YY MM DD HH MM SS` (byte = value); seconds `00` — record is per-minute | — | 🟢 — steps 054; #80, #81; records 00–07 matched the "Refill History" screen by date and time (09.16 23:58, 09.14 15:27, 09.10 16:44, 09.07 12:23, 09.04 13:29, 09.03 13:24/13:14/13:11) |
| 6..7 (u16LE) | refill history — volume | × 0.025 U | — | 🟢 — steps 054; #80, #81; reservoir refill volume; cross-checked against the screen: 4.2 / 7.55 / 43.125 / 9.375 / 7.7 / 12.9 / 286 / 60.2 U |
| 8 (u8) | refill history — type | `0`=other (not verified); `1`=Manual | — | 🟡 — steps 054; #80, #81; on screen all visible records show "Manual" (type 1); value 0 occurred in one non-visible record (09.03 12:37, 0.8 U) — purpose not verified; byte 9 is always `00` |
<!-- /gen:a3_04 -->

### 4.16. Alarm history — object `a3/03`
Log of pump alarms; read when opening "Home → History → Alarm History." Record of 8 bytes: 0..5 —
time `YY MM DD HH MM SS` (seconds `00`, per-minute); 6..7 — alarm code (u16LE). Codes cross-checked
against the screen: `13` — "Reservoir empty," `3` — "Button error," `5` — "Battery depleted" (Step
055, #83); code `1` occurred without an on-screen label. The table is from the registry.

<!-- gen:a3_03 -->
| Offset | Field | Encoding | Command | Status |
|---|---|---|---|---|
| 0..5 (6 bytes) | alarm history — time | `YY MM DD HH MM SS` (byte = value); seconds `00` — record is per-minute | — | 🟢 — steps 055; #82, #83; records matched the "Alarm History" screen by date and time (09.14 12:10, 09.14 08:54, 09.10 16:40/16:38/16:36/16:33, 09.10 14:36, 09.10 13:48) |
| 6..7 (u16LE) | alarm history — code | `1`=other (not verified); `2`=other (not verified); `3`=Button error; `5`=Battery depleted; `8`=other (not verified); `13`=Reservoir empty | — | 🟢 — steps 055; #82, #83; alarm code; cross-checked against the screen: 13 = reservoir empty, 3 = button error, 5 = battery depleted; codes 1, 2, 8 do not appear in the visible part of the screen — their purpose was not verified |
<!-- /gen:a3_03 -->

### 4.14. What is not present in the pump's frames
- **Battery charge percentage.** The frames only carry voltage (`a3/0c` off3, × 0.01 V) and a bar
  count (`a3/00` off0). The percentage shown by the app is its own conversion from voltage; there is
  no percentage field over the air.
- **Active insulin (IOB).** The pump does not transmit it in any object: the value is computed by
  the app from delivery logs and the active-insulin time (`a3/07` off2..3). How exactly the app
  computes it is outside the scope of this work: it is the pump's protocol that is being studied,
  not the app.

Both quantities are deliberately not described as protocol fields: **they are not provided by the
pump**. 🟢 — Steps 007, 024, 051 (search across all objects in the window).

## 5. Control commands

Class `0xA1`; the pump's response is acknowledgment `A1/55` (§2.2). The payload follows the
identity block `<identity>` (§2.1).

<!-- gen:commands -->
| Code | Payload | Purpose | Status |
|---|---|---|---|
| `0x00` | 96 bytes — 48 × u16LE, 0.025 U/h (half-hour intervals 00:00–23:30) | write a basal profile | 🟢 — steps 026, 027; writes to the **active** profile (`a3/00` off12): with A active (Step 026) record 00 of `a3/08` changed, with B active (09.18 00:58, Step 043) — only record 01 changed (slot 47: 0.2 → 1.25 U/h, "Total 15.775 U", #68); from 05:00 `a3/00` off76 = the new interval value (screen "0.725 U/h", Step 027) |
| `0x02` | 4 bytes: type · duration · value u16LE (§5.4); payload `00 00` — cancel bolus | start TBR / cancel bolus | 🟢 — steps 024, 030, 031; TBR: `01 03 f0 00` (6 U/h, 45 min), `00 0b 71 00` (113 %, 2:45), `00 0a 78 00` (120 %, 2:30); bolus cancel: `00 00` (extended 09.17 17:35, simple 18:13, extended 09.18 04:03) |
| `0x04` | 1 byte — profile number (0 = A … 7 = H) | select active basal profile | 🟢 — steps 043, 044; 09.18 00:48–02:07: `01`,`02`,`03`,`00`,`01`,`07` — `a3/00` off12 = number, off76 = the new profile's rate in the current half-hour (for the empty D and H — `0`, not `ff ff`); after the acknowledgment the app re-reads `a3/08` |
| `0x05` | none | cancel TBR | 🟢 — steps 024, 026; two observations in the window (04:01, 04:40): the TBR fields in `a3/00` reset to zero within 2–3 s |
| `0x11` | 8 × u16LE, 0.025 U (§5.3) | bolus presets | 🟢 — steps 012, 025 |
| `0x12` | u16LE dose (0.025 U) + byte | start a simple bolus | 🟢 — steps 031; delivery progress — unsolicited notifications `a1/a0` (u16LE, accumulated delivered dose 0.025 U: 2→…→22 = 0.05…0.55 U); completion — notification `a1/aa` with the final delivered dose (09.18 02:18 and 02:28: `01 00`, `02 00`, `03 00` = 0.025/0.05/0.075 U, Step 045); before the window it was seen as `0c/12/14 00 00` (same simple boluses) |
| `0x13` | 2 × u16LE: dose (0.025 U) · duration (×15 min) | start an extended bolus | 🟢 — steps 030, 046, 053; delivery progress — unsolicited notifications `a1/a1` (u16LE, accumulated delivered dose 0.025 U: 2→4→6→8 = 0.05…0.20 U); completion — `a1/aa` with the final dose (09.18 04:26:35 `0a 00` = 0.25 U, Step 047); the log record appears at the moment of completion or cancellation, not at the start |
| `0x15` | 244 bytes = object `a3/07` bytes 0..243 (§4.9) | write bolus calculator settings | 🟢 — steps 036; the frame, at 264 bytes, is longer than the MTU — Prepare Write + Execute Write + writing the tail; after the acknowledgment the app re-reads `a3/07`, the bytes match, the CRC at off244 is recomputed by the pump |
| `0x21` | 1 byte: `01` — stop, `00` — start | stop / start delivery | 🟢 — steps 027; after `01`: `a3/00` off76..77 = `ff ff`, off78..79 = the stop time, screen "Stopped"; after `00`: off76 = the profile interval's rate; before the window the app repeated `00` after 2 and 4 min |
| `0x31` | 6 bytes — time `YY MM DD HH MM SS` | set pump time | 🟢 — steps 009, 038; three observations in the window: 09.16 16:52:06, 09.17 20:52:08 (automatically on reconnect after a phone reboot), and 09.17 23:42:43 (manually, Step 038) — payload = phone time at the moment of sending, reflected in `a3/00` off44..49; before the window — 16:22:20 |
| `0x32` | 16 bytes — settings block (§5.1) | write pump settings | 🟢 — steps 009, 011, 013, 034 |
| `0x33` | `03 00` | not established (response — acknowledgment) | 🟡 |
| `0x34` | 16 bytes — sound block (§5.2) | sound mode and its step | 🟢 — steps 011, 016; the app sends `a1/34` together with `a1/32` on any settings change |
| `0x35` | 6 bytes — new Bluetooth password in an internal (non-ASCII) representation; value not given (`<password>`) | change Bluetooth password | 🟢 — steps 052; 09.18 05:42:52 "Danger Zone → Change Password"; acknowledgment `a1/55`; after the command the app reconnected and authorized with the new password (see §3.3). The password bytes are not decoded — recovering the secret is outside the scope of this work (rule 5) |
<!-- /gen:commands -->

On every settings change the app sends **both** blocks — `a1/32` and `a1/34`. The block values are
reflected in the status objects `a3/00` and `a3/0c` (§4.1, §4.2).

### 5.1. Settings block `a1/32` (16-byte payload after `<identity>`)
<!-- gen:a1_32 -->
| Byte(s) | Field | Encoding | Status (reflection) | Status |
|---|---|---|---|---|
| 0, bit `0x01` | bolus speed | `0`=Normal; `1`=Low | `a3/00` off2 | 🟢 — steps 011, 014; #12, #13, #18, #19; the full menu was not captured; both values were observed |
| 0, bit `0x02` | keypad lock | `0`=off; `1`=on | `a3/00` off5 | 🟢 — steps 013, 023; #16, #17, #31, #36, #37 |
| 0, bit `0x04` | pump auto power-off | `0`=off; `1`=on | `a3/00` off6 | 🟢 — steps 013, 022; #16, #17, #31, #34, #35, #37 |
| 0, bit `0x08` | basal patterns | `0`=off; `1`=on | `a3/00` off10 | 🟢 — steps 049; #75, #76; 09.18 04:35:17 `a1/32` byte[0] `00→08`; `a3/00` off10 `0→1`; on screen the "Basal patterns" toggle is on and a list of four patterns appeared (#76). Previously byte off10 and bit `0x08` were unparsed |
| 0, bit `0x10` | pump lock | `0`=unlocked; `1`=locked | `a3/00` off11 | 🟢 — steps 034, 053; #56, #57, #78, #79; enabled by the app (`a1/32` byte[0] bit `0x10`), lifted only from the pump's own menu — off11 `1→0` with no app command (Step 034); while locked, a command arriving at the pump is rejected with acknowledgment `a1/a5` (Steps 034, 053). **An already-running delivery is not interrupted by the lock:** on 09.18 an extended bolus kept being delivered (notifications `a1/a1`) after `off11 0→1` (Step 053); in the app the bolus/TBR/Stop buttons are locked out |
| 0, bit `0x20` | daily dose limit | `0`=off; `1`=on | `a3/00` off13 | 🟢 — steps 013, 021; #16, #17, #25, #32, #33, #37 |
| 0, bit `0x40` | pump language | `0`=Russian; `1`=English (menu item order, #31) | `a3/00` off50 | 🟢 — steps 013, 020; #16, #17, #30, #31, #37 |
| 1 | alarm signal type | `0`=Sound; `1`=Vibration; `2`=Sound and vibration (menu item order, #25) | `a3/00` off1 | 🟢 — steps 013, 017; #16, #17, #24, #25 |
| 2 | pump screen brightness | `0`=10 %; `1`=30 %; `2`=50 %; `3`=60 %; `4`=80 %; `5`=100 % (menu item order, #29) | `a3/00` off3 | 🟢 — steps 013, 019; #16, #17, #28, #29; the value is the menu item index |
| 3 | pump auto power-off time | number, hours | `a3/00` off7 | 🟢 — steps 013, 022; #16, #17, #34, #35; number of hours, not an index; the visible part of the menu shows 2–8 h (#35), 1 h — on screen (#17); the full list was not captured |
| 4 | "insulin running low" — units | number, U | `a3/00` off8 | 🟢 — steps 013, 022; #16, #17, #25; number of units; menu not captured |
| 5 | "insulin running low" — time | number of half-hours (not a menu index): `11`=05:30, `13`=06:30 | `a3/00` off9 | 🟢 — steps 013, 022, 023; #16, #17, #25, #37; menu 02:00–12:00 in steps of 0:30 (`4`…`24`) — per the user's account; #37 shows 02:00–05:00 |
| 6 | extended bolus / BG reminder | bit field: bit0 = "Extended bolus" (enables stretched and dual-wave bolus), bit1 = "BG reminder"; in `a3/00` off4 = byte × 2 (`00`/`02`/`04`/`06`) | `a3/00` off4 (status = byte × 2) | 🟢 — steps 011, 012, 015; #12, #13, #14, #20, #21 |
| 7 | alarm signal duration | `0`=Long; `1`=Normal; `2`=Short (menu item order, #27) | `a3/0c` off2 | 🟢 — steps 013, 018; #16, #17, #25, #26, #27 |
| 8..9 (u16LE) | screen auto-off | × 0.1 s | `a3/00` off14 | 🟢 — steps 013; #16, #17, #31; menu not captured; over the air 150 and 600 |
| 10..11 (u16LE) | total daily dose (limit) | number, U | `a3/00` off20 | 🟢 — steps 013, 021, 022; #16, #17, #32, #33, #34; number of units, not an index; menu 50–300 in steps of 50 (#33) |
| 12..13 (u16LE) | maximum basal | × 0.025 U/h | `a3/00` off24 | 🟢 — steps 010; #11; 8.0→7.7 (320→308) |
| 14..15 (u16LE) | maximum bolus | × 0.025 U | `a3/00` off26 | 🟢 — steps 009; #10, #21; 12.0→12.3 (480→492) |
<!-- /gen:a1_32 -->

Bit `0x80` of byte[0] did not occur in the research window (checked by `tools/verify_fields.py`).

### 5.2. Settings block `a1/34` (16 bytes)
<!-- gen:a1_34 -->
| Byte(s) | Field | Encoding | Status (reflection) | Status |
|---|---|---|---|---|
| 0 | sound mode | `0`=off; `1`=on | `a3/0c` off4 | 🟢 — steps 011, 016; #12, #13, #22, #23 |
| 1 | sound mode step | `0`=0.1 U; `1`=0.5 U; `2`=1.0 U; `3`=5.0 U (menu item order, #41) | `a3/0c` off5 | 🟢 — steps 011, 025; #12, #13, #41; the value is the menu item index |
<!-- /gen:a1_34 -->

### 5.3. Bolus presets — command `a1/11`
Eight u16LE values (step **0.025 U**), one per slot; when editing, the app resends the whole list.
The values are reflected in `a3/00` off28..43.

<!-- gen:a1_11 -->
| Byte(s) | Field | Encoding | Status (reflection) | Status |
|---|---|---|---|---|
| 0..1 (u16LE) | bolus preset "Breakfast A 5:00–6:59" | × 0.025 U | `a3/00` off28 | 🟢 — steps 012, 025; #14, #15, #40, #41 |
| 2..3 (u16LE) | bolus preset "Breakfast B 7:00–9:59" | × 0.025 U | `a3/00` off30 | 🟢 — steps 012, 025; #14, #15, #40, #41 |
| 4..5 (u16LE) | bolus preset "Lunch A 10:00–11:59" | × 0.025 U | `a3/00` off32 | 🟢 — steps 012, 025; #14, #15, #40, #41 |
| 6..7 (u16LE) | bolus preset "Lunch B 12:00–14:59" | × 0.025 U | `a3/00` off34 | 🟢 — steps 012, 025; #14, #15, #40, #41 |
| 8..9 (u16LE) | bolus preset "Dinner A 15:00–17:59" | × 0.025 U | `a3/00` off36 | 🟢 — steps 012, 025; #14, #15, #40, #41 |
| 10..11 (u16LE) | bolus preset "Dinner B 18:00–21:59" | × 0.025 U | `a3/00` off38 | 🟢 — steps 012, 025; #14, #15, #40, #41 |
| 12..13 (u16LE) | bolus preset "Night A 22:00–23:59" | × 0.025 U | `a3/00` off40 | 🟢 — steps 012, 025; #14, #15, #40, #41 |
| 14..15 (u16LE) | bolus preset "Night B 00:00–4:59" | × 0.025 U | `a3/00` off42 | 🟢 — steps 012, 025; #14, #15, #40, #41 |
<!-- /gen:a1_11 -->

### 5.4. Temporary basal rate — commands `a1/02`, `a1/05`
`a1/02` — start TBR (4 bytes), `a1/05` — cancel (no payload). TBR state — in `a3/00`
off51/80/82/84/86.

<!-- gen:a1_02 -->
| Byte(s) | Field | Encoding | Status (reflection) | Status |
|---|---|---|---|---|
| 0 | TBR — type | `0`=percent; `1`=U/h | `a3/00` off82 | 🟢 — steps 024; #38, #39 |
| 1 | TBR — duration | steps of 15 min; in `a3/00` off84 — minutes (byte × 15) | `a3/00` off84 (status = byte × 15) | 🟢 — steps 024; #38, #39 |
| 2..3 (u16LE) | TBR — value | meaning depends on type (byte[0]): `01` — U/h in steps of 0.025; `00` — percent. In `a3/00` off80 — the resulting rate, 0.025 U: at `01` equal to the value, at `00` = ⌊off76 × % / 100⌋ | `a3/00` off80 (per the rule, see encoding) | 🟢 — steps 024; #38, #39; rounding down verified on one value (36 × 113 % = 40.68 → 40) |
<!-- /gen:a1_02 -->

## 6. Dialogue behavior and timings

Based on frames from the research window (RESEARCH_EN.md, Step 028):
- **Polling cycle** — every **180 s** the app requests `a3/00`, `a3/0c`, `a3/21`, `a3/0a`, `a3/0b`,
  `a3/26` (243 full cycles; 29 shortened — only `a3/00`, `a3/0c`). 🟢
- **After a settings write** (`a1/32` + `a1/34`) — a repeat read of `a3/00`, `a3/0c`. 🟢
- **Acknowledgment** `a1/55 00 00` arrives for every `a1` command within 3 s (121 of 121). 🟢
  Exception — a locked pump: response `a1/a5 00 00` (Step 034). 🟡
- **Response delay** (across the whole window, Step 051): command `a1` → acknowledgment — median
  **186 ms** (min 67, 95th percentile 489, max 539 ms; 177 pairs); read `a3` → first response frame
  — median **139 ms** (min 51, 95th percentile 189, max 1187 ms; 3943 pairs). 🟢
- **"Heartbeat"** `a5/03` — unsolicited, every 180 s (§4). 🟢
- **Bolus completion** — unsolicited notification `a1/aa` with the final delivered dose (u16LE,
  0.025 U); arrives 1–3 s after the last `a1/a0` for a simple bolus and after the last `a1/a1` for
  an extended one. 🟢 — Steps 045, 047 (six simple boluses on 09.18 02:18/02:28 and an extended
  0.25 U one at 04:12→04:26). A record is added to the `a3/21`/`a3/01` log at this same moment — on
  completion or cancellation, but not on start.
- **Status timestamp** `a3/00` off44..49: in regular polling the seconds are `00` (the pump keeps
  time to minute precision); nonzero seconds occur only in a status re-read at the moment of an
  event. 🟢 — Step 045.
- **Pump lock and delivery.** A lock (`a3/00` off11 = 1) forbids new commands: any command arriving
  at a locked pump is rejected with acknowledgment `a1/a5` (§4.12). But it does **not interrupt**
  delivery already in progress — an extended bolus continued (notifications `a1/a1`) after the lock
  was set. 🟢 — Steps 034, 053.
