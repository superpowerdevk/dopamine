---
name: dopamine
description: Play provably-fair casino games with virtual chips (coinflip, dice, RPS, roulette, slots, blackjack) plus agent-vs-agent RPS duels. Virtual chips only, no real money, no chain, no network. Trigger when the user wants to play a game, gamble chips, check balance or leaderboard, start or join a duel, or verify fairness.
---

# dopamine

Provably-fair, virtual-chip casino. Chips are virtual; never imply real money or cash value.

## Setup (once)
If the dopamine command is missing: pip3 install "git+https://github.com/superpowerdevk/dopamine"
If still not found, run as: python3 -m dopamine ...

## RENDERING RULE (mandatory — do not deviate)
When a HUMAN is playing in chat, every game result MUST be shown by running the command with
--render card and displaying the returned HTML card. This is the ONLY way to present a result.
- Do NOT re-describe the hand, reels, roll, or numbers in prose.
- Do NOT print wager/payout/net/balance as text or bullet lists — the card already shows them.
- At MOST one short flavor line (<=10 words) may go above the card. Nothing below it except the next-turn pop-up.
For scheduled/cron play with no human watching, use --render json instead (no card, no pop-ups).

## INTERACTION LOOP (same every game, every turn)
1. Collect the bet with an option pop-up (do not ask the user to type a command).
2. Run the game command with --render card.
3. Show the card (and only the card, per the rendering rule).
4. Offer the next turn with an option pop-up: Deal again / Change bet / Switch game / Cash out.
Repeat. Keep the rhythm identical so the experience is uniform on mobile and desktop.

## Per-game pop-up flow
- blackjack: pop-up bet amount -> run --render card -> next-turn pop-up.
- roulette: pop-up bet type (number/red/black/even/odd/low/high/dozen) -> pop-up amount (and value if number/dozen) -> run --render card -> next-turn pop-up.
- coinflip: pop-up heads/tails -> pop-up amount -> run --render card -> next-turn pop-up.
- dice: pop-up over/under -> pop-up target (0-100) -> pop-up amount -> run --render card -> next-turn pop-up.
- slots: pop-up amount -> run --render card -> next-turn pop-up.
Note: blackjack resolves in one shot today (no live hit/stand mid-hand yet).

## Register first
dopamine register --agent <name>   (new agents start with 1000 chips)

## Commands (append --render card for human play, --render json for cron)
dopamine coinflip --agent <name> --wager <n> --pick heads|tails
dopamine dice --agent <name> --wager <n> --target <0-100> --direction over|under
dopamine rps --agent <name> --wager <n> --choice rock|paper|scissors
dopamine roulette --agent <name> --wager <n> --bet number|red|black|even|odd|low|high|dozen [--value <v>]
dopamine slots --agent <name> --wager <n>
dopamine blackjack --agent <name> --wager <n> [--actions hit,hit,stand]
dopamine duel-create --agent <name> --choice rock|paper|scissors --stake <n>
dopamine duel-list
dopamine duel-join --agent <name> --id <duel_id> --choice rock|paper|scissors
dopamine balance --agent <name>
dopamine leaderboard --limit <n>
dopamine fairness --agent <name>
dopamine rotate-seed --agent <name>

