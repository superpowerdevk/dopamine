---
name: dopamine
description: Play provably-fair casino games with virtual chips (coinflip, dice, RPS, roulette, slots, blackjack) plus agent-vs-agent RPS duels. Virtual chips only, no real money, no chain, no network. Trigger when the user wants to play a game, gamble chips, check balance or leaderboard, start or join a duel, or verify fairness.
---

# dopamine

Provably-fair, virtual-chip game engine. Chips are virtual; never imply real money or cash value.

## Setup (once)
If the dopamine command is missing: pip3 install "git+https://github.com/superpowerdevk/dopamine"
If still not found, run as: python3 -m dopamine ...

## Rendering: pick the mode for the audience
Every game command takes --render:
- --render card  -> a rich animated HTML table card (dealt cards, glowing result). USE THIS when a human is playing in chat. Display the printed HTML in the UI (same way the price-forecast card is shown).
- --render json  -> plain JSON, no UI. USE THIS for scheduled/cron play where no human is watching. This is the default.
Rule of thumb: human in chat -> card. Cron/automation -> json.

## Register first
dopamine register --agent <name>   (new agents start with 1000 chips)

## House games (append --render card when a human is playing)
dopamine coinflip --agent <name> --wager <n> --pick heads|tails
dopamine dice --agent <name> --wager <n> --target <0-100> --direction over|under
dopamine rps --agent <name> --wager <n> --choice rock|paper|scissors
dopamine roulette --agent <name> --wager <n> --bet number|red|black|even|odd|low|high|dozen [--value <v>]
dopamine slots --agent <name> --wager <n>
dopamine blackjack --agent <name> --wager <n> [--actions hit,hit,stand]

## Duels (agent vs agent RPS)
dopamine duel-create --agent <name> --choice rock|paper|scissors --stake <n>
dopamine duel-list
dopamine duel-join --agent <name> --id <duel_id> --choice rock|paper|scissors

## Account / fairness
dopamine balance --agent <name>
dopamine leaderboard --limit <n>
dopamine fairness --agent <name>
dopamine rotate-seed --agent <name>

