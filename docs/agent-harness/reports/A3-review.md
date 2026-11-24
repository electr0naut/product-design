# Phase A3 review

**Approved: A3 is done and correct.**
- The host gateway is stopped.
- No host gateway service is installed.
- Only container gateway processes remain.
- The fallback rule for chatting was applied properly: an unconfirmed version means using
  `docker exec -it hermes hermes`.

## Optional, not blocking

The container image is built from `/srv/hermes` (`Dockerfile.lab` plus the `hermes-agent` checkout), so its
version can be confirmed without guessing:

```bash
git -C /srv/hermes/hermes-agent rev-parse --short=12 HEAD
```

- **If it prints `caafe5389ae5`** (the host's commit), both run the same code. `HERMES_HOME=/srv/hermes/data hermes`
  then becomes a safe way to chat from the host, as long as no host `gateway` command is ever run with it.
- **If it prints something else**, keep using `docker exec -it hermes hermes`.

Report the result in the A4 report. Don't switch the chat path without the user's OK.

## A4

The plan stands as written: apply `A1-decisions.md` (4 removed, 6 paused, 4 kept), find the cause of the
nightly backup's exit 128, run `cron doctor`, and show `cron list` as a table. It needs the user's go.
