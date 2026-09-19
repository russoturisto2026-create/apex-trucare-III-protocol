# TruCare III Insulin Pump Protocol

Lawful study of **the protocol of the TruCare III pump itself** (manufacturer Apex Medical) — the
commands the pump accepts and the responses it emits over the radio link. The official
**Erwin Blueberry** app (v1.0 Build 489 Patch1) is used **strictly for its intended purpose** — as
the standard means of controlling the pump; the app itself is not an object of study. The work is
carried out on a **test bench**: the pump is not connected to a person. No bypass mechanisms are
used — only what already passes over the radio link and is visible on the screen is recorded. The
test-bench phone and the pump are property of the study's author, lawfully acquired; the official
**Erwin Blueberry** app is lawfully obtained from Google Play and used as intended (it is not an
object of study).

Analysis of the captured materials (HCI captures, pump response objects) and documentation upkeep
are carried out with the help of **Claude** (Anthropic) as an analysis tool: matching frames to the
screen, maintaining the field registry, and generating tables. All conclusions rest on the attached
materials and are checked by scripts (`tools/`); the tool does not replace evidence, it helps
organize it.

## What's where

| File | Purpose |
|---|---|
| `RESEARCH_EN.md` | Research log — a step-by-step journal, with links to source materials. |
| `PROTOCOL_EN.md` | Technical description of the protocol — control commands and response objects, with links to steps. |
| `MATERIALS_EN.md` | Registry of source materials: No. → type → description → step → archive. |
| `user_agreement.md` | Recorded version of the app's license agreement. |
| `legal_EN.md` | Legal grounds: cross-check of the agreement against the scope of the research, a declaration of non-contradiction. |
| `DISCLAIMER_EN.md` | Disclaimer: the protocol description may contain inaccuracies; provided "as is", without warranty. |
| `APP_MENU.md` | Map of the app's capabilities (menu → protocol objects → extraction groups). |
| `OBJECTS_EN.md` | Intermediate map of response-object parsing (byte by byte: what has been decoded). |
| `.claude/skills/apex-device/` | Skill for connecting to the test bench and capturing materials (HCI, screenshots). |
| `archive/` | All source materials, archives only, **outside git** (see `.gitignore`). |

Traceability: `PROTOCOL_EN.md` → step in `RESEARCH_EN.md` → material No. in `MATERIALS_EN.md` →
archive `archive/<study>/NN-*.zip`.

## Project rules

1. **One step — one commit.** A step is a meaningful unit of observation. The commit message
   references the step and the archive numbers.
2. **Materials under numbers and SHA-256.** Each captured material is given a running number and
   the **SHA-256 of the source file** — independent proof of integrity; everything is registered in
   `MATERIALS_EN.md`. The hash is computed on the artifact file itself (the one inside the archive);
   integrity verification means extracting the file and checking `sha256sum` against the registry
   entry. The files themselves live only in archives, outside git.
3. **Step archives, separated by type.** A step's materials are packed into `archive/<study>/`:
   `NN-hci.zip` (only the extracted `btsnoop_hci`), `NN-screens.zip`, `NN-photos.zip`. The full
   bugreport is not kept.
4. **Two-way linking.** `RESEARCH_EN.md` links to materials; `PROTOCOL_EN.md` links to steps in
   `RESEARCH_EN.md`. A claim without a link to evidence is not recorded.
5. **Privacy.** No text document contains personal data, passwords, serial numbers, device
   addresses, or identity blocks — only placeholders (`<identity>`, `<serial>`, `<crc>`, etc.).
   Screenshots/photos with sensitive data are cropped/redacted.
6. **Self-containedness.** This project's documents rely only on their own materials; they contain
   no references to third-party projects, their files, or packages.
7. **Status changes only on evidence.** Every conclusion is always accompanied by a reference to a
   step and a material; when materials conflict, the status is "needs re-verification," not
   "confirmed."
8. **Reliability: ≥2 measurements with different characteristics.** A claim (a field's presence, its
   encoding, the semantics of a command/response) is promoted to "confirmed" status only after being
   reproduced in at least two measurements that differ in their characteristics — a different
   parameter value, a different device/session state, different connection conditions, or a
   "radio ↔ screen" cross-check. At least one of the confirmations must be independent in nature
   (not a repeat of the same action). One measurement is an "assumption"; two or more consistent
   ones are "confirmed."
9. **Observation only.** We record exchanges initiated by the official app (logged manually). We do
   not send our own frames to the pump and do not bypass protection. Therapeutic commands are
   executed by the app on the bench pump, which is not connected to a person.

## Research step procedure

1. Connect to the test bench (the `apex-device` skill).
2. Manually run the scenario in the app.
3. Capture materials: `bugreport` → extract `btsnoop_hci` (delete the bugreport); if needed,
   `screencap`; photos are taken by the user. Assign numbers to the materials.
4. Parse the HCI capture, describe the step in `RESEARCH_EN.md`, log the materials in
   `MATERIALS_EN.md`.
5. Enter the fields into the `tools/fields.py` registry (location within the command and status,
   values with menu items, screen cross-checks, steps, materials, status); run
   `tools/verify_fields.py` (checked against all archived captures — there should be no errors) and
   `tools/gen_tables.py` (the field tables in `PROTOCOL_EN.md`/`OBJECTS_EN.md` are generated from the
   registry and are not edited by hand).
6. Pack the materials into `archive/<study>/NN-*.zip`.
7. One commit per step.
