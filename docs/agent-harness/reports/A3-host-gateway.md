# Phase A3: stop the host gateway, 2026-11-24

User go received in the VM session. Followed the A2 review's protocol.

| Check | Result |
|---|---|
| `hermes gateway stop` (host) | "Stopped gateway for this profile" |
| `hermes gateway status` (host) | "Gateway is not running" |
| Host gateway service installed? | No: `systemctl --user list-unit-files` shows no hermes unit; status says "To install as user service" |
| `pgrep -af "hermes.*gateway"` | only container processes (s6 `main-wrapper.sh gateway run`, `hermes ... gateway run --replace`); no host gateway |
| Host version | v0.23.3 (2026.9.24), local caafe5389ae5 |
| Container version | `vunknown (2026.9.24)` |
| `/srv/hermes/data` | owner `ubay`, mode 700, readable by `ubay` |

## Chat decision

Same release date, but the container does not report a version number, so "same version" cannot be
confirmed. The doc's rule for that case: chat through the container with `docker exec -it hermes hermes`.
`HERMES_HOME=/srv/hermes/data hermes` was NOT adopted, and no permissions were changed.
If you want the host CLI path, confirm the image's real version first (e.g. check the image tag/build
file in `/srv/hermes`).

No cron job or container setting was changed.

Next: A4 (apply `A1-decisions.md`), needs your OK.
