# Hidden suite fix: `acc-timeline` "event keys" was my mistake

The expected key list wasn't in sort order (`sender` sorts before `sendingTime`), while the received keys were
sorted. FXL-5 is correct. Fixed: the expected list is now sorted too, so it's the same key set. Copy the updated
`acc-timeline.test.js` to `~/.local/state/agent-harness/acceptance/fix-lens/`. In the acceptance history, the test
counts as passing from its next run. It never passed before, so it isn't a regression either way.
