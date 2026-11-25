+++
key = "FXL-4"
title = "Decode messages field by field"
rank = 4
blocked_by = ["FXL-1", "FXL-3"]
labels = []
+++
Add `src/decode.js`, following technical design section 6: `decode(message, text)` turns a valid candidate into
`{ number, label, beginString, supported, fields }`, with `fields` as `{ tag, name, value, enumName, known }`.

Acceptance criteria
- AC1: Fields come out in message order, including repeated tags; an empty value (`58=`) is shown as empty.
- AC2: A known tag gets its dictionary name; an unknown tag gets the name `Unknown tag X` (X the tag number) and
  `known: false`, with its raw value.
- AC3: An enum field gets the symbolic name of its value; a value missing from the dictionary keeps its raw value
  with `enumName` `unknown value`; a non-enum field has `enumName` `null`.
- AC4: `label` is `Message <number>: <MsgType name>`, for example `Message 3: Logon`; if 35 repeats, the first
  value is used.
- AC5: A message whose BeginString is not `FIX.4.2` or `FIX.4.4` has `supported: false`, the label
  `Message <number>: unsupported version <value of 8>`, and every field shown with its raw value and no dictionary name.
- AC6: Decoding 100 valid mixed messages (built with the test helper) takes under 5 seconds.
