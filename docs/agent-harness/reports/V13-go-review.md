# FIX Lens v1.3: approved by Ubay. What is decided, and what comes next

## Decisions of 2026-11-27 (Ubay's words quoted)
- **PRD v1.3 and technical design v1.3 are approved.** I asked: "Reply 'approved' (or tell me what to change)
  for PRD v1.3 and design v1.3." He answered: **"approved, I will compact after so save the decision"**.
  The two choices I had flagged as mine (a page of 200 messages; a byte limit of 10,485,760) stand with it.
  The documents: `fix-lens/prd.md` and `fix-lens/technical-design.md` at the commit that adds this file.
- Before that, the same day: **"10000 is the max for now"** (the limit, and theme A means files well beyond
  it), **"v1.3 is fine"** (do it now, before his real-log test), **"lets produce the updated PRDs and start the
  work"**.
- **Phasing: "agreed on the phasing of the project".** Phase 2 is themes C, D and E; phase 3 is A, B and G;
  phase 4 is F and H (`fix-lens/phase-2-scope.md`). Earlier: "lets keep A, B, F, G, H for phases 3 and 4".
- **The validation brief is scoped to the product:** "dont include out of scope FIX versions", "analyse the
  brief and take out what is out of scope", "Build the brief removing what is clearly out of scope or not
  feasible" (`fix-lens/validation/BRIEF.md`; his original is `BRIEF-original.md`).

## What v1.3 is
The limits go from 1,000 messages and 1,048,576 bytes to 10,000 messages and 10,485,760 bytes; the timeline
and the cards are shown 200 messages at a time (PRD US-010, AC-057 to AC-062; design sections 4, 9, 10, 15 and
16). Three tickets: FXL-19 the limits and the performance tests, FXL-20 `src/paging.js`, FXL-21 the pager on
the page. Baseline measured on v1.2 with the limit lifted: analysis of 10,000 messages 0.3 to 0.6 s; drawing
all of them 11 s.

## Next, in this order (reviewing session)
1. Write tickets `FXL-19.md` to `FXL-21.md`. Criteria that say "nothing else changes" go in the text, not as
   numbered criteria (they cannot have a fail-first test). FXL-21 lists `styles.css` among its files.
2. Write the hidden acceptance tests for the three tickets, and change the ones that pin the old limits
   (`acc-limits.test.js` at least): retire the old test ids by decision, add the new ones. Check every new test
   against a reference build of my own before it is committed.
3. One commit with the tests, then decisions: retire the replaced hidden tests, `refresh_copies` of that commit
   (design v1.3 and the hidden files, host and worker reading copies).
4. **Standing session or a job:** add the three tickets' hidden files to `[expected_hidden.fix-lens]` in the
   host config (FXL-19 `acc-limits.test.js`, FXL-20 and FXL-21 the new paging files), and confirm the copies.
5. `load_tickets` decision for FXL-19, FXL-20, FXL-21, in that order.
6. Review each landing; real-browser check at 10,000 messages (first page within 3 s, a change within 1 s).

## Answered by Ubay later on 2026-11-27
- **The BRD route:** "we generate a new BRD with the phases without going through the previous reviewers and it
  is autoapproved. I just need the BRD updated with the changes". Done: Confluence page 589885, version 4.
- **Publishing PRD v1.3 and design v1.3 to Confluence:** "Yes". Done: PRD page 557109 version 8, design page
  1409027 version 5. Both are the repository files as they stand at this commit.
- **The privacy and markup checks in the validation:** "Phase 2". Recorded in `fix-lens/phase-2-scope.md` and
  in the BRD; the running validation is not changed.

## Still open with Ubay
- From earlier today: the root-only token file for the job user; closing the standing VM session; the Qwen
  model for the fallback reviewer (after the bake-off).
- Before phase 3: whether the tool stays a page that runs entirely in the browser.

## Running in the background
The independent validation of v1.2 (a sub-agent of the reviewing session) writes into `fix-lens/validation/`.
Its files are committed as unreviewed work in progress; every finding is to be verified before it becomes a
ticket. Its measurements at 2,500 to 10,000 messages are information for v1.3, not defects of v1.2.
