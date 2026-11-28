+++
key = "FXL-9"
title = "Accept ^A and <SOH> as delimiters, and a delimiter character inside a value"
rank = 9
blocked_by = []
labels = []
+++
Real logs often show the SOH byte as the text `^A` or `<SOH>`, and a field value may contain a `|`. Today such
messages are rejected. Change `src/framing.js` to follow technical design section 3 (v1.2): four delimiter forms,
the delimiter chosen per message, the separator rule for the three text forms, and byte counts that never
normalise the text. Section 15 lists the v1.1 behaviour this replaces. The shapes of candidates, fields and
errors do not change, and positions stay offsets into the pasted text.

`test/framing.test.js`, `test/framing-f1.test.js`, `test/framing-f1b.test.js`, `test/framing-f2.test.js`,
`test/framing-f2b.test.js`, `test/helpers.test.js`, `test/helpers/fix.js` and `test/static-checks.test.js` are
expected to change in this ticket. Tests that assert `field_without_equals` for a `|`-delimited message describe v1.1 and change with it.

Every message below was computed independently of the code, with BodyLength and CheckSum over SOH.

Acceptance criteria
- AC0: A test imports `splitMessages` and `checkMessage` from `src/framing.js` and `analyse` from
  `src/analyse.js`. Candidates, fields and errors have exactly the keys they had before this ticket.
- AC1: The reference message is valid in all four forms, with the same tags and values:
  `8=FIX.4.4|9=20|35=0|34=1|49=A|56=B|10=125|`,
  `8=FIX.4.4^A9=20^A35=0^A34=1^A49=A^A56=B^A10=125^A`,
  `8=FIX.4.4<SOH>9=20<SOH>35=0<SOH>34=1<SOH>49=A<SOH>56=B<SOH>10=125<SOH>`, and the same with the SOH character
  (0x01). A paste with those four on four lines gives four valid messages.
- AC2: Field positions are 0-based offsets in the pasted text. For the `^A` message they are 0, 11, 17, 23, 29, 35,
  41. For the `<SOH>` message they are 0, 14, 23, 32, 41, 50, 59.
- AC3: With a text delimiter, an occurrence that is not followed by digits and `=` is part of the value. These are
  valid, and tag 58 has the value shown:
  - `8=FIX.4.4|9=27|35=0|34=1|49=A|56=B|58=a|b|10=110|`: `a|b`;
  - `8=FIX.4.4|9=28|35=0|34=1|49=A|56=B|58=x||y|10=025|`: `x||y`;
  - `8=FIX.4.4|9=28|35=0|34=1|49=A|56=B|58=end||10=227|`: `end|`;
  - `8=FIX.4.4^A9=28^A35=0^A34=1^A49=A^A56=B^A58=a^Ab^A10=146^A`: `a^Ab`;
  - `8=FIX.4.4<SOH>9=31<SOH>35=0<SOH>34=1<SOH>49=A<SOH>56=B<SOH>58=a<SOH>b<SOH>10=081<SOH>`: `a<SOH>b`;
  - `8=FIX.4.4|9=33|35=0|34=1|49=A|56=B|58=café|€|10=078|`: `café|€` (BodyLength counts UTF-8 bytes).
- AC4: The other delimiter forms are ordinary text inside a message:
  `8=FIX.4.4^A9=27^A35=0^A34=1^A49=A^A56=B^A58=a|b^A10=110^A` is valid with 58 = `a|b`, and
  `8=FIX.4.4|9=28|35=0|34=1|49=A|56=B|58=a^Ab|10=146|` is valid with 58 = `a^Ab`.
- AC5: A value that contains the delimiter followed by digits and `=` reads as a new field, and no other reading
  is tried. `8=FIX.4.4|9=31|35=0|34=1|49=A|56=B|58=a|112=b|10=058|` is malformed with rule `checksum`. The same
  text ending `10=191|` is valid, with 58 = `a` and 112 = `b`.
- AC6: A delimiter that comes right after the CheckSum field ends the message even when other text follows:
  `10:00:00 OUT 8=FIX.4.4|9=20|35=0|34=1|49=A|56=B|10=125| trailing text` gives one valid message. Two messages on
  one line work with a text form too:
  `10:00:00 OUT 8=FIX.4.4^A9=20^A35=0^A34=1^A49=A^A56=B^A10=125^A8=FIX.4.2^A9=20^A35=0^A34=2^A49=A^A56=B^A10=124^A`
  gives two valid messages.
- AC7: A CheckSum computed over the delimiter's own text bytes is rejected:
  `8=FIX.4.4^A9=20^A35=0^A34=1^A49=A^A56=B^A10=049^A` is malformed with rule `checksum`.
- AC8: Errors keep their form and their positions in the pasted text:
  `8=FIX.4.4^A9=21^A35=0^A34=1^A49=A^A56=B^A10=126^A` gives
  `Message 1: BodyLength (9) says 21, actual 20 at position 12`.
- AC9: A candidate with no delimiter form after its BeginString, for example `8=FIX.4.4 9=20 35=0`, is malformed
  with rule `header_order`. `<soh>` in lower case is not a delimiter.
- AC10: With the SOH character nothing changes: every SOH separates fields, an empty piece between two SOH
  characters is `field_without_equals`, and a `|`, `^A` or `<SOH>` in such a message is ordinary text.
- AC11: `test/helpers/fix.js` takes the delimiter form as an option, and the size limits and the 100-message
  performance test still pass.
- AC12: The source check is extended now, so that every module written for v1.2 is held to it from the start
  (technical design section 8.4). `test/static-checks.test.js` also fails on: any `import(` call; any import of a
  path ending `.json`; an assignment to `.id`, `.name`, `.title`, `.src`, `.value`, `.style` or `.cssText` in
  `src/**/*.js`; and, in `index.html`, a `<script>` without `src`, a `<style>` element, a `style=` attribute or
  an `on...=` attribute. It checks that `src/dictionary/fix42.js` and `fix44.js` are each exactly
  `export default `, one JSON value and `;`. Each new rule has a test showing that it fails on a small bad
  example, and the check passes on the delivered code.
