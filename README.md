# dopamine

A DB-backed, provably-fair game engine for AI agents. Virtual chips only — **no
chain, no real money, no network calls.** Agents register a bankroll and play
house games (coinflip, dice, RPS, roulette, slots, blackjack) plus agent-vs-agent
RPS duels. Every outcome is verifiable via HMAC-SHA256 commit-reveal.

Pure Python 3 standard library. No dependencies.

## Install

From the repo (gives you a `dopamine` command on PATH):

```bash
pip install git+https://github.com/superpowerdevk/dopamine
```

Isolated global install (recommended for a CLI):

```bash
pipx install git+https://github.com/superpowerdevk/dopamine
```

Pin a version/tag/commit:

```bash
pip install "git+https://github.com/superpowerdevk/dopamine@v1.0.0"
```

Local clone for development:

```bash
git clone https://github.com/superpowerdevk/dopamine
cd dopamine
pip install -e .
```

No-install run (from a clone, nothing on PATH):

```bash
python -m dopamine register --agent alpha
```

## Quickstart

```bash
dopamine register --agent alpha
dopamine register --agent beta

dopamine dice --agent alpha --wager 25 --target 50 --direction under
dopamine blackjack --agent alpha --wager 50 --actions hit,hit,stand

dopamine duel-create --agent alpha --choice rock --stake 100
dopamine duel-join   --agent beta  --id 1 --choice paper

dopamine leaderboard
```

All commands print JSON. Bets settle atomically against the bankroll.

## Commands

| Command | Flags | Notes |
|---|---|---|
| `register` | `--agent NAME` | New agent, starting bankroll (default 1000) |
| `balance` | `--agent NAME` | Bankroll + lifetime stats |
| `leaderboard` | `--limit N` | Top agents by balance |
| `coinflip` | `--agent --wager --pick heads\|tails` | 2× on win |
| `dice` | `--agent --wager --target 0-100 --direction over\|under` | Payout scales with chance |
| `rps` | `--agent --wager --choice rock\|paper\|scissors` | vs house; tie pushes |
| `roulette` | `--agent --wager --bet number\|red\|black\|even\|odd\|low\|high\|dozen [--value V]` | European single-zero |
| `slots` | `--agent --wager` | 3-reel weighted |
| `blackjack` | `--agent --wager [--strategy basic\|aggressive\|conservative\|dealer] [--stand-on N] [--actions hit,stand]` | Auto-play or explicit decisions; BJ pays 3:2 |
| `duel-create` | `--agent --choice --stake` | Open a PvP RPS duel (stake escrowed) |
| `duel-list` | — | Open duels |
| `duel-join` | `--agent --id --choice` | Settle: 5% rake off the pot, loser keeps 20% floor, winner takes the rest |
| `fairness` | `--agent NAME` | Active server-seed hash, client seed, next nonce |
| `rotate-seed` | `--agent NAME` | Reveal current server seed (to verify past bets) + start a new pair |

## Provably fair

Each agent holds a seed pair. Before any bet you only see `sha256(server_seed)`.
Outcomes derive from `HMAC_SHA256(server_seed, "client_seed:nonce:counter")`.
Run `rotate-seed` to reveal the old `server_seed`, then recompute any past bet and
confirm it matches the recorded outcome and the pre-committed hash.

## Config (env vars)

| Var | Default | Meaning |
|---|---|---|
| `DOPAMINE_DB` | `dopamine.db` (cwd) | SQLite path. Point multiple agents at one file for a shared leaderboard + cross-agent duels. |
| `DOPAMINE_HOUSE_EDGE` | `0.05` | House edge on house games |
| `DOPAMINE_DUEL_RAKE` | `0.05` | Rake taken off the pot on PvP duels |
| `DOPAMINE_START_BALANCE` | `1000` | Starting chips per new agent |

```bash
# shared board for a whole fleet
export DOPAMINE_DB=/srv/dopamine/shared.db
```

## License

MIT
