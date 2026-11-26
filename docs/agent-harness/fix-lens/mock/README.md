# FIX Lens presentation mock (reviewer's design reference, not landed code)

A restyled copy of the page, built on the landed logic plus local changes: the dictionaries as JS modules (the
FXL-8 fix) and three new pure modules, `src/orders.js`, `src/summary.js` and `src/filters.js`. Checked in Chromium with `sample.log`: no console errors, no requests to
another origin, the pasted `<img onerror>` text stays text.

What it shows:
- **Layout:** a header with the privacy line, the input, a summary strip (messages, valid, malformed, sequence
  gaps, orders), the buys/sells/net table, the filters, then the timeline (left, sticky) beside the decoded
  messages (right). One column under 900 px.
- **Buys, sells and net by symbol:** one line per symbol: buy orders, bought quantity, average buy price, sell
  orders, sold quantity, average sell price, and net (bought minus sold). Quantities are fills from execution
  reports (LastQty 32 at LastPx 31), counted once per ExecID (17). It follows the filters and the selected order.
- **Filters:** Account (1), SenderCompID (49), SenderSubID (50), TargetCompID (56), TargetSubID (57), each a list of
  the values found in the log. Account keeps every message of the orders that carry it; the other four match the
  message itself. Malformed messages are hidden while a filter is on.
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
