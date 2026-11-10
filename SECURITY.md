# Security policy

Edge-Radar runs on your own machine with your own Kalshi API key, and places real orders
when `DRY_RUN` is `false`. There is no hosted service and there are no user accounts; the
page under `site/` is static. A bug that leaks a credential, or that lets an order past a
risk gate that should have stopped it, is a security bug.

## Reporting a vulnerability

Report it privately through GitHub's security advisories: open the repository's
**Security** tab and click **Report a vulnerability**
(`https://github.com/ai-automation-tools/edge-radar/security/advisories/new`). Please don't
open a public issue for it.

Say what you found, the steps or input that show it, and the commit you saw it on. You'll
get a reply within a week. Once a fix ships, the advisory is published with credit to you
unless you'd rather stay anonymous.

## What counts

- A credential leaving the machine or landing in a log, a report, an email or a commit:
  the Kalshi key ID, the RSA private key under `keys/`, an odds API key, or anything else
  from `.env`.
- An order placed while `DRY_RUN` is `true`, or one that gets past a risk gate that should
  have rejected or trimmed it.
- Text from an API (a market title, an odds feed) that changes what the code runs rather
  than what it prices.
- A dependency with a known vulnerability that this code actually reaches.

A wrong price, a bad edge estimate or a losing bet is a bug or a modelling question, not a
vulnerability. Open a normal issue for those.

## Supported versions

Only the latest commit on `master` gets fixes. There are no tagged releases.
