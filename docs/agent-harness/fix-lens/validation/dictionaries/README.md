# Dictionaries

No third-party dictionary file is stored here. Two were used, both downloaded by `sources/fetch.sh` and
recorded with their commit and SHA-256 in `sources/manifest.json`:

| Dictionary | Licence | Why it is not copied here |
|---|---|---|
| Orchestra `OrchestraFIX42.xml`, `OrchestraFIX44.xml` (FIX Trading Community, commit `ed111f1`) | Apache-2.0 | a copy is allowed, but the two files are 0.7 MB and 1.5 MB, over the size limit set for stored fixtures |
| QuickFIX `spec/FIX42.xml`, `spec/FIX44.xml` (commit `386ce46`) | QuickFIX Software License 1.0 | a copy is allowed with its notice; left out for the same size reason (0.13 MB and 0.32 MB) and because the engine package ships them |

What was checked with them (`tests/dictionary_check.py`, results in `reports/results.json`):

- **DICT-42-01, DICT-44-01:** the product's `src/dictionary/fix42.js` (405 fields) and `fix44.js` (912 fields)
  are equal, field for field and code for code, to an independent parse of the Orchestra files at the commit
  the product pins. No difference.
- **DICT-42-02, DICT-44-02 (informative):** against QuickFIX's dictionaries no tag is missing on either side.
  Three field names differ in FIX 4.2 (23 `IOIID` / `IOIid`, 297 `QuoteAckStatus` / `QuoteStatus`,
  327 `HaltReason` / `HaltReasonChar`) and one in FIX 4.4 (327); the product's names are the specification's.
  Where code sets differ (7 fields in FIX 4.2, 32 in FIX 4.4) the product always has the larger set.
- Neither dictionary lists `1` or `2` for ExecType (150) in FIX 4.4; both list them in FIX 4.2. The product's
  rule "1 or 2 is a Fill in FIX 4.2 only" follows the dictionaries (test S04-04).
