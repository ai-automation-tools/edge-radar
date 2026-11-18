# Contributing to Edge-Radar

Edge-Radar places real orders on Kalshi when `DRY_RUN=false`, so a change to the money path gets
more care than a change anywhere else. Read [AGENTS.md](AGENTS.md) first: it holds the risk gates,
the sizing rules and the things that must never happen.

## Set up

```bash
python -m venv .venv            # Python 3.11 or 3.12
make install                    # hashed dev lock, then the package in editable mode
make hooks                      # pre-commit: black, flake8, detect-secrets, config and diagram guards
cp .env.example .env            # fill in keys; keep DRY_RUN=true
make doctor                     # checks env, keys and gates
```

A dev container (`.devcontainer/`) does the install and hook steps for you.

## Make a change

1. Branch from `master` and keep the PR to one concern.
2. Run `make test`. Tests never touch a live account: the suite disables `.env` loading and mocks
   every venue call. Don't add one that needs a real key or a network call.
3. Never run anything with `--execute` to try a change. Preview mode shows exactly what would be sent.
4. Add a line to [docs/CHANGELOG.md](docs/CHANGELOG.md), and tick or add the item in
   [docs/ROADMAP.md](docs/ROADMAP.md) if it has one.
5. If the commit hook warns that code cited by `docs/diagrams/betting-data-flow.json` changed, update
   the cited line ranges and rebuild with `python scripts/diagrams/build_betting_diagram.py --pin-head`
   (see [docs/diagrams/README.md](docs/diagrams/README.md)).

## The money path

These need a review from the code owner ([.github/CODEOWNERS](.github/CODEOWNERS)) and a test that
pins the behaviour:

- `scripts/kalshi/kalshi_executor.py`: the gates, sizing and order placement
- `scripts/kalshi/kalshi_client.py`, `scripts/kalshi/kalshi_settler.py`
- `scripts/shared/` modules that feed them: fees, trade log, shard funding, venue eligibility
- `app/config.py`: every risk knob and its default
- `scripts/schedulers/`: the tasks that run unattended

A new risk knob goes in `app/config.py` and `.env.example`, never in `os.getenv` elsewhere (a hook
checks this). Don't change a gate's default to loosen it.

## Security

Report a vulnerability privately as described in [SECURITY.md](SECURITY.md), not as an issue. Never
commit `.env`, `.env.*` (except the `*.example` templates) or anything under `keys/`.
