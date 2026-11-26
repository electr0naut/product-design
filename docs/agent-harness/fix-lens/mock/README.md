# FIX Lens presentation mock (reviewer's design reference, not landed code)

A restyled copy of the page, built on the landed logic plus two local changes: the dictionaries as JS modules (the
FXL-8 fix) and a new `src/orders.js`. Checked in Chromium with `sample.log`: no console errors, no requests to
another origin, the pasted `<img onerror>` text stays text.

What it shows:
- **Layout:** a header with the privacy line, the input, a summary strip (messages, valid, malformed, sequence
  gaps, orders), then the timeline (left, sticky) beside the decoded messages (right). One column under 900 px.
- **Timeline rows:** message number, time, event badge, direction, sequence number, order ids. Order events have a
  blue edge, a sequence gap is amber, rejects are red.
- **Message cards:** a header (number, message type, direction, sequence, time) and a table: tag, field, value,
  meaning. Malformed messages appear in log order as red cards.
- **Themes:** light and dark. The page follows the system setting; the button switches it until the page is
  reloaded. Nothing is stored, because the PRD forbids persistence.
- **Order story:** every ClOrdID, OrderID and OrigClOrdID is a button. Clicking one shows only that order's
  messages and events, under a banner with its ids, terms and latest state. Orders are linked through 11, 37 and
  41, so a cancel/replace chain stays one order. "Show all messages" returns to the full log.

The same constraints as the product: no inline script or style, text set with `textContent` only, no attribute set
from pasted data, no storage, no network.
