# Rotating the Kalshi API key

*When a key may have leaked, when a copy lives somewhere you no longer control, or on a schedule. About
fifteen minutes. Nothing here places an order.* · [Setup guide](SETUP_GUIDE.md) · [Docs home](../README.md)

> [!IMPORTANT]
> **Choose RSA when you create the key.** Kalshi's dialog defaults new keys to **Ed25519** (since
> 2026-10-01). `kalshi_client.py` signs requests with RSA-PSS only, so an Ed25519 key fails every call
> with an auth error. Roadmap M3 tracks adding Ed25519 signing.

## Before you start

- **Pick a quiet window.** No execute run should start while the key is half-changed. Either disable the
  order-placing scheduled tasks for the duration, or rotate between their run times.
- **List every place the current key lives:** `.env` (`KALSHI_API_KEY`), the PEM at
  `KALSHI_PRIVATE_KEY_PATH` (default `keys/live/kalshi_private.key`), any `.env.<profile>` that overrides
  either, any hosted copy (`KALSHI_PRIVATE_KEY` holds the PEM inline for cloud hosts and app secrets), and
  any backup that includes `keys/`. Each one is either updated or deleted below.
- Never paste a key or PEM into a chat, an issue, a commit or a log. `keys/` and `.env` are git-ignored;
  keep it that way.

## Steps

1. **Create the new key.** Kalshi → Settings → API Keys → Create API Key → **key type RSA**. Kalshi shows
   the key ID and downloads the private key once.
2. **Install it.** Move the downloaded PEM over the file `KALSHI_PRIVATE_KEY_PATH` points at, and set
   `KALSHI_API_KEY` in `.env` to the new key ID. Do the same in each `.env.<profile>` that overrides
   either variable, and in every hosted secret that holds `KALSHI_PRIVATE_KEY`.
3. **Check it, read-only.**

   ```bash
   python scripts/doctor.py
   EDGE_RADAR_PROFILE=<name> python scripts/doctor.py   # once per profile
   ```

   Look for `PASS  Kalshi API connected (balance: ...)`. Do **not** use `--verify-eligibility` here: that
   probe places a real order.
4. **Revoke the old key** on the same Kalshi page, by its key ID.
5. **Check again** (step 3). It still passing proves nothing was quietly using the old key.
6. **Delete every other copy of the old key:** stale PEM files, hosted app secrets (delete the app too if
   it is retired), and backups that contain it.
7. **Re-enable** any tasks you disabled. The next scheduled settle or scan is the live confirmation; read
   its log.

## If something fails

| Symptom | Cause |
|:--|:--|
| `401` / signature error on every call | The key is Ed25519, the PEM and key ID are from different keys, or a profile still points at the old PEM |
| Passes in `doctor.py`, fails in a scheduled task | The task runs a profile whose `.env.<profile>` still overrides the key |
| Passes after revoking, but a hosted app stops working | It held its own copy (`KALSHI_PRIVATE_KEY`); give it the new key or retire it |

Roll back by reinstating the old key only if you have **not** revoked it yet; after step 4 the only way
forward is a new key.
