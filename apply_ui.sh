#!/usr/bin/env bash
# dopamine v1.4.0 — full animation set in the in-chat card (reel spin, coin flip, dice slide, roulette land, banner pop).
# Run from inside the dopamine-repo folder:  bash apply_ui.sh
set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[ -f pyproject.toml ] && [ -d dopamine ] || { echo "ERROR: run this from the dopamine-repo folder."; exit 1; }
echo ">> writing dopamine/render.py"
cat > dopamine/render.py <<'R_EOF'
#!/usr/bin/env python3
"""Render a dopamine game result into a self-contained HTML card.

render_card(result) -> str (full <div> with inline <style>, no external assets).
Suits are cosmetic (the engine's outcomes are numeric); they're derived
deterministically from the bet's fairness hash + nonce so they're stable but
don't affect any provably-fair verification.
"""
import hashlib

_CSS = """
<style>
.dop{--gold:#e7c66b;--gold-d:#9c8540;--win:#46e08a;--lose:#ff5d73;--push:#e7c66b;
 --card:#f7f4ec;--cr:#cf2d3b;--cb:#16181d;--txt:#e9e6dd;--dim:#8a988f;
 --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
 font-family:var(--mono);color:var(--txt);width:100%;max-width:560px;container-type:inline-size;border-radius:18px;position:relative;
 background:radial-gradient(120% 90% at 50% 0,#0c2a1e,#061711);border:1px solid rgba(231,198,107,.28);
 box-shadow:0 20px 60px rgba(0,0,0,.55),inset 0 1px 0 rgba(255,255,255,.04);padding:18px 20px 16px;overflow:hidden}
@media (prefers-reduced-motion:reduce){.dop *{animation:none!important}}
.dop::before{content:"";position:absolute;inset:8px;border-radius:12px;border:1px solid rgba(231,198,107,.12);pointer-events:none}
.dop .eb{display:flex;justify-content:space-between;align-items:center;font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:var(--gold-d)}
.dop .eb b{color:var(--gold);font-weight:700}.dop .eb .h{color:#5b6b62;font-size:10px;letter-spacing:.08em}
.dop .lane{display:flex;align-items:center;justify-content:space-between;margin-top:6px}
.dop .who{font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--dim)}
.dop .tot{font-size:13px}.dop .tag{margin-left:8px;padding:2px 7px;border-radius:999px;font-size:10px;letter-spacing:.12em;text-transform:uppercase}
.dop .tag.bust{background:rgba(255,93,115,.16);color:var(--lose)}.dop .tag.bj{background:rgba(70,224,138,.16);color:var(--win)}
.dop .hand{display:flex;gap:8px;margin:8px 0 2px;flex-wrap:wrap}
.dop .card{width:clamp(44px,11cqi,64px);height:clamp(62px,15.4cqi,90px);border-radius:8px;position:relative;flex:0 0 auto;background:linear-gradient(160deg,#fff,var(--card));
 box-shadow:0 7px 16px rgba(0,0,0,.5),inset 0 0 0 1px rgba(0,0,0,.07);animation:dl .42s cubic-bezier(.2,.8,.2,1) both}
.dop .card:nth-child(2){animation-delay:.08s}.dop .card:nth-child(3){animation-delay:.16s}
.dop .card:nth-child(4){animation-delay:.24s}.dop .card:nth-child(5){animation-delay:.32s}.dop .card:nth-child(6){animation-delay:.40s}
@keyframes dl{from{opacity:0;transform:translateY(-16px) rotate(-6deg) scale(.96)}to{opacity:1;transform:none}}
.dop .card .r{position:absolute;font-weight:800;font-size:clamp(11px,3.4cqi,15px);line-height:1;font-family:Georgia,serif}
.dop .card .r.tl{top:7px;left:8px}.dop .card .r.br{bottom:7px;right:8px;transform:rotate(180deg)}
.dop .card .s{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:clamp(22px,7cqi,30px)}
.dop .card.red{color:var(--cr)}.dop .card.black{color:var(--cb)}
.dop .banner{margin:12px 0;text-align:center;border-radius:10px;padding:12px;font-family:system-ui,Segoe UI,Roboto,sans-serif;
 font-weight:800;letter-spacing:.04em;font-size:clamp(17px,5.5cqi,22px);text-transform:uppercase;animation:pop .4s both}
.dop .banner small{display:block;font-family:var(--mono);font-weight:600;font-size:12px;letter-spacing:.18em;margin-top:3px;opacity:.85}
.dop .banner.win{color:var(--win);background:radial-gradient(80% 140% at 50% 0,rgba(70,224,138,.18),transparent);text-shadow:0 0 22px rgba(70,224,138,.55)}
.dop .banner.lose{color:var(--lose);background:radial-gradient(80% 140% at 50% 0,rgba(255,93,115,.16),transparent);text-shadow:0 0 22px rgba(255,93,115,.45)}
.dop .banner.push{color:var(--push);background:radial-gradient(80% 140% at 50% 0,rgba(231,198,107,.14),transparent)}
.dop .strip{display:grid;grid-template-columns:repeat(auto-fit,minmax(118px,1fr));gap:8px;margin-top:10px;border-top:1px solid rgba(231,198,107,.12);padding-top:10px}
.dop .stat{text-align:center}.dop .stat .k{font-size:10px;letter-spacing:.18em;text-transform:uppercase;color:var(--dim)}
.dop .stat .v{font-size:15px;margin-top:3px}.dop .stat .v.up{color:var(--win)}.dop .stat .v.down{color:var(--lose)}
.dop .reels{display:flex;gap:8px;justify-content:center;margin:6px 0}
.dop .reel{width:clamp(48px,14cqi,60px);height:clamp(58px,17cqi,72px);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:clamp(26px,8cqi,34px);
 background:#0a0d0c;box-shadow:inset 0 0 0 1px rgba(231,198,107,.25),inset 0 8px 18px rgba(0,0,0,.6);animation:spin .55s ease-out both}
.dop .reel:nth-child(2){animation-delay:.12s}.dop .reel:nth-child(3){animation-delay:.24s}
.dop .wheel{width:clamp(76px,24cqi,96px);height:clamp(76px,24cqi,96px);border-radius:50%;margin:6px auto;display:flex;align-items:center;justify-content:center;
 font-size:28px;font-weight:800;color:#fff;border:3px solid rgba(231,198,107,.5);
 background:conic-gradient(#1a1a1a 0 10deg,#cf2d3b 10deg 20deg,#1a1a1a 20deg 30deg,#cf2d3b 30deg 40deg,#1a1a1a 40deg 50deg,#138a36 50deg 60deg,#1a1a1a 60deg 360deg)}
.dop .coin{width:clamp(70px,22cqi,84px);height:clamp(70px,22cqi,84px);border-radius:50%;margin:6px auto;display:flex;align-items:center;justify-content:center;animation:flip .6s ease-out both;
 font-size:32px;font-weight:800;color:#3b2f0c;background:radial-gradient(circle at 35% 30%,#f6dd95,#caa544);
 box-shadow:0 6px 14px rgba(0,0,0,.45),inset 0 0 0 3px rgba(255,255,255,.25)}
.dop .track{height:10px;border-radius:999px;background:#0a0d0c;position:relative;margin:20px 0 8px;box-shadow:inset 0 0 0 1px rgba(231,198,107,.2)}
.dop .track .wz{position:absolute;top:0;bottom:0;background:rgba(70,224,138,.22);border-radius:999px}
.dop .track .rl{position:absolute;top:-5px;width:3px;height:20px;background:var(--gold);animation:slide .5s ease-out both}
.dop .hands{display:flex;justify-content:center;gap:26px;font-size:clamp(34px,11cqi,46px);margin:8px 0}
.dop .center{text-align:center;font-size:13px;color:var(--dim);margin-top:6px}.dop .center b{color:var(--txt)}

.dop .felt{display:grid;grid-template-columns:auto repeat(12,1fr);grid-auto-rows:clamp(20px,6.4cqi,30px);gap:3px;margin:8px 0 4px}
.dop .num,.dop .zero{display:flex;align-items:center;justify-content:center;border-radius:4px;font-weight:700;color:#fff;position:relative;font-size:clamp(9px,2.6cqi,12px)}
.dop .num.red{background:#b3242f}.dop .num.black{background:#1c1f25}
.dop .zero{grid-row:1/4;grid-column:1;background:#138a36;padding:0 2px}
.dop .win{box-shadow:0 0 0 2px #fff,0 0 14px rgba(255,255,255,.65);z-index:2;animation:land .5s both}
.dop .ball{position:absolute;top:-3px;right:-3px;width:9px;height:9px;border-radius:50%;background:#fff;box-shadow:0 0 8px #fff;z-index:4}
.dop .chip{position:absolute;width:clamp(17px,5cqi,22px);height:clamp(17px,5cqi,22px);border-radius:50%;
 background:radial-gradient(circle at 35% 30%,#f6dd95,#caa544);border:2px dashed #8a6d1f;color:#3b2f0c;
 font-size:clamp(7px,2.2cqi,9px);font-weight:800;display:flex;align-items:center;justify-content:center;
 box-shadow:0 2px 6px rgba(0,0,0,.55);z-index:3}
.dop .outside,.dop .doz{display:grid;gap:3px;margin-top:3px}
.dop .outside{grid-template-columns:repeat(6,1fr)}.dop .doz{grid-template-columns:repeat(3,1fr)}
.dop .obet{display:flex;align-items:center;justify-content:center;padding:7px 2px;border-radius:4px;
 font-size:clamp(8px,2.3cqi,11px);letter-spacing:.03em;text-transform:uppercase;position:relative;
 background:#0d1f17;border:1px solid rgba(231,198,107,.2);color:var(--txt)}
.dop .obet.red{background:#7a1a22}.dop .obet.black{background:#161a1f}
.dop .obet.lit{outline:2px solid var(--gold);outline-offset:-2px}
.dop .betspot{display:flex;align-items:center;gap:10px;margin:8px 0 2px}
.dop .betspot .ring{width:clamp(34px,10cqi,44px);height:clamp(34px,10cqi,44px);border-radius:50%;
 border:2px dashed rgba(231,198,107,.4);display:flex;align-items:center;justify-content:center}
.dop .bchip{width:clamp(28px,8.5cqi,38px);height:clamp(28px,8.5cqi,38px);border-radius:50%;
 background:radial-gradient(circle at 35% 30%,#f6dd95,#caa544);border:2px dashed #8a6d1f;color:#3b2f0c;
 font-size:clamp(9px,2.8cqi,12px);font-weight:800;display:flex;align-items:center;justify-content:center;box-shadow:0 3px 8px rgba(0,0,0,.5)}
.dop .betspot .lbl{font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:var(--dim)}
@keyframes spin{0%{transform:translateY(-42px);filter:blur(3px);opacity:.4}100%{transform:none;filter:none;opacity:1}}
@keyframes flip{0%{transform:rotateY(0)}100%{transform:rotateY(720deg)}}
@keyframes slide{from{left:0}}
@keyframes land{0%{transform:scale(1)}40%{transform:scale(1.35)}100%{transform:scale(1)}}
@keyframes pop{from{opacity:0;transform:scale(.9)}to{opacity:1;transform:none}}
</style>
"""

_SUITS = [("\u2660", "black"), ("\u2665", "red"), ("\u2666", "red"), ("\u2663", "black")]


def _suit(h, nonce, i):
    n = int(hashlib.sha256(f"{h}:{nonce}:s{i}".encode()).hexdigest(), 16)
    return _SUITS[n % 4]


def _rank(r):
    return {1: "A", 11: "J", 12: "Q", 13: "K"}.get(int(r), str(int(r)))


def _card(rank_val, h, nonce, i):
    g, cls = _suit(h, nonce, i)
    lbl = _rank(rank_val)
    return (f'<div class="card {cls}"><span class="r tl">{lbl}</span>'
            f'<span class="s">{g}</span><span class="r br">{lbl}</span></div>')


def _strip(r):
    net = r["net"]
    ncls = "up" if net > 0 else ("down" if net < 0 else "")
    nstr = f"+{net:g}" if net > 0 else f"{net:g}"
    return (f'<div class="strip">'
            f'<div class="stat"><div class="k">Wager</div><div class="v">{r["wager"]:g}</div></div>'
            f'<div class="stat"><div class="k">Payout</div><div class="v">{r["payout"]:g}</div></div>'
            f'<div class="stat"><div class="k">Net</div><div class="v {ncls}">{nstr}</div></div>'
            f'<div class="stat"><div class="k">Balance</div><div class="v">{r["balance"]:,.0f}</div></div>'
            f'</div>')


def _eb(game, r):
    h = r.get("fair", {}).get("server_seed_hash", "")
    short = (h[:8] + "\u2026") if h else ""
    return f'<div class="eb"><span>DOPAMINE \u00b7 <b>{game}</b></span><span class="h">fair \u25c6 {short}</span></div>'


def _wrap(body):
    return f'<div class="dop">{body}</div>{_CSS}'


def render_card(r):
    g = r.get("game")
    if g == "blackjack":
        return _wrap(_blackjack(r))
    if g == "slots":
        return _wrap(_slots(r))
    if g == "roulette":
        return _wrap(_roulette(r))
    if g == "coinflip":
        return _wrap(_coinflip(r))
    if g == "dice":
        return _wrap(_dice(r))
    if g == "rps":
        return _wrap(_rps(r))
    return _wrap(_eb(g or "game", r) + _strip(r))  # fallback


def _banner(kind, big, small):
    return f'<div class="banner {kind}">{big}<small>{small}</small></div>'


def _result_kind(r):
    return "win" if r["net"] > 0 else ("lose" if r["net"] < 0 else "push")


def _net_word(r):
    return f'+{r["net"]:g}' if r["net"] > 0 else (f'{r["net"]:g}' if r["net"] < 0 else "push")


def _blackjack(r):
    o = r["outcome"]; h = r.get("fair", {}).get("server_seed_hash", ""); n = r.get("fair", {}).get("nonce", 0)
    dealer = "".join(_card(c, h, n, 100 + i) for i, c in enumerate(o["dealer"]))
    player = "".join(_card(c, h, n, i) for i, c in enumerate(o["player"]))
    dtag = ' <span class="tag bust">Bust</span>' if o["dealer_total"] > 21 else (
           ' <span class="tag bj">BJ</span>' if o["result"] == "dealer_blackjack" else "")
    ptag = ' <span class="tag bust">Bust</span>' if o["player_total"] > 21 else (
           ' <span class="tag bj">BJ</span>' if o["result"] == "blackjack" else "")
    labels = {"blackjack": "Blackjack!", "dealer_bust": "Dealer bust", "win": "You win",
              "dealer_blackjack": "Dealer blackjack", "bust": "Bust", "lose": "Dealer wins", "push": "Push"}
    big = (f'Winner {_net_word(r)}' if r["net"] > 0 else (labels.get(o["result"], "Lose") if r["net"] < 0 else "Push"))
    return (_eb("BLACKJACK", r) +
            f'<div class="lane"><span class="who">Dealer</span><span class="tot">{o["dealer_total"]}{dtag}</span></div>'
            f'<div class="hand">{dealer}</div>' +
            _banner(_result_kind(r), big, labels.get(o["result"], "")) +
            f'<div class="lane"><span class="who">You</span><span class="tot">{o["player_total"]}{ptag}</span></div>'
            f'<div class="hand">{player}</div>' +
            f'<div class="betspot"><div class="ring"><div class="bchip">{r["wager"]:g}</div></div><span class="lbl">your bet</span></div>' +
            _strip(r))


_SLOT_EMOJI = {"seven": "7\ufe0f\u20e3", "claw": "\U0001f9be", "star": "\u2b50", "bell": "\U0001f514",
               "lemon": "\U0001f34b", "cherry": "\U0001f352"}


def _slots(r):
    o = r["outcome"]
    reels = "".join(f'<div class="reel">{_SLOT_EMOJI.get(x, x)}</div>' for x in o["reels"])
    big = (f'{"Jackpot " if r["net"] >= r["wager"]*10 else "Win "}{_net_word(r)}' if r["net"] > 0 else "No match")
    return (_eb("SLOTS", r) + f'<div class="reels">{reels}</div>' +
            _banner(_result_kind(r), big, " ".join(o["reels"])) + _strip(r))


_RRED = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}


def _roulette(r):
    o = r["outcome"]; win_n = int(o["number"]); col = o["color"]; bet = o["bet"]; val = o.get("value")
    w = f'{r["wager"]:g}'
    cells = []
    zc = " win" if win_n == 0 else ""
    zball = '<span class="ball"></span>' if win_n == 0 else ""
    zchip = f'<span class="chip">{w}</span>' if (bet == "number" and str(val) == "0") else ""
    cells.append(f'<div class="zero{zc}">0{zball}{zchip}</div>')
    for n in range(1, 37):
        ccol = (n + 2) // 3 + 1
        crow = 1 if n % 3 == 0 else (2 if n % 3 == 2 else 3)
        nc = "red" if n in _RRED else "black"
        ex = " win" if n == win_n else ""
        ball = '<span class="ball"></span>' if n == win_n else ""
        chip = f'<span class="chip">{w}</span>' if (bet == "number" and str(val) == str(n)) else ""
        cells.append(f'<div class="num {nc}{ex}" style="grid-column:{ccol};grid-row:{crow}">{n}{ball}{chip}</div>')
    grid = f'<div class="felt">{"".join(cells)}</div>'

    def ob(label, key, cls=""):
        lit = " lit" if bet == key else ""
        chip = f'<span class="chip">{w}</span>' if bet == key else ""
        return f'<div class="obet {cls}{lit}">{label}{chip}</div>'
    outside = ('<div class="outside">' + ob("1-18", "low") + ob("Even", "even") + ob("Red", "red", "red")
               + ob("Black", "black", "black") + ob("Odd", "odd") + ob("19-36", "high") + '</div>')

    def dz(label, idx):
        is_b = bet == "dozen" and str(val) == str(idx)
        return f'<div class="obet{(" lit" if is_b else "")}">{label}{("<span class=" + chr(34) + "chip" + chr(34) + ">" + w + "</span>") if is_b else ""}</div>'
    dozens = f'<div class="doz">{dz("1st 12",1)}{dz("2nd 12",2)}{dz("3rd 12",3)}</div>'

    big = f'Win {_net_word(r)}' if r["net"] > 0 else "Miss"
    vtxt = "" if val in (None, "None") else " " + str(val)
    sub = f'bet {bet}{vtxt} \u00b7 landed {win_n} {col}'
    return (_eb("ROULETTE", r) + grid + outside + dozens +
            f'<div class="center">{sub}</div>' +
            _banner(_result_kind(r), big, "") + _strip(r))


def _coinflip(r):
    o = r["outcome"]; face = "H" if o["result"] == "heads" else "T"
    big = f'Win {_net_word(r)}' if r["net"] > 0 else "Lose"
    return (_eb("COINFLIP", r) + f'<div class="coin">{face}</div>'
            f'<div class="center">you picked <b>{o["pick"]}</b> \u00b7 flipped <b>{o["result"]}</b></div>' +
            _banner(_result_kind(r), big, "") + _strip(r))


def _dice(r):
    o = r["outcome"]; t = o["target"]; roll = o["roll"]
    if o["direction"] == "under":
        wz = f'left:0;width:{t}%'
    else:
        wz = f'left:{t}%;width:{100-t}%'
    big = f'Win {_net_word(r)}' if r["net"] > 0 else "Lose"
    return (_eb("DICE", r) +
            f'<div class="track"><div class="wz" style="{wz}"></div><div class="rl" style="left:{min(max(roll,0),100)}%"></div></div>'
            f'<div class="center">roll <b>{roll}</b> \u00b7 {o["direction"]} <b>{t:g}</b> \u00b7 {o["chance_pct"]:g}% chance</div>' +
            _banner(_result_kind(r), big, "") + _strip(r))


_RPS_EMOJI = {"rock": "\u270a", "paper": "\u270b", "scissors": "\u270c\ufe0f"}


def _rps(r):
    o = r["outcome"]
    big = (f'Win {_net_word(r)}' if r["net"] > 0 else ("Push" if o["result"] == "tie" else "Lose"))
    return (_eb("RPS", r) +
            f'<div class="hands"><span>{_RPS_EMOJI.get(o["you"],"?")}</span><span>{_RPS_EMOJI.get(o["house"],"?")}</span></div>'
            f'<div class="center">you <b>{o["you"]}</b> \u00b7 house <b>{o["house"]}</b></div>' +
            _banner(_result_kind(r) if o["result"] != "tie" else "push", big, "") + _strip(r))

R_EOF
echo ">> updating dopamine/__init__.py"
cat > dopamine/__init__.py <<'I_EOF'
#!/usr/bin/env python3
"""SuperClaw Dopamine — DB-backed, provably-fair game engine for AI agents.

Pure stdlib (sqlite3 + hmac). No real money, no chain, no network.
Agents hold virtual chips, play house games + PvP duels, all results
are provably fair (HMAC-SHA256 over server_seed:client_seed:nonce).

CLI:  python dopamine.py <command> [--flags]
Run `python dopamine.py help` for the full command list.
"""
import sqlite3, hashlib, hmac, secrets, json, os, time, argparse, sys

DB_PATH       = os.environ.get("DOPAMINE_DB", "dopamine.db")
HOUSE_EDGE    = float(os.environ.get("DOPAMINE_HOUSE_EDGE", "0.05"))   # 5% default
DUEL_RAKE     = float(os.environ.get("DOPAMINE_DUEL_RAKE", "0.05"))    # 5% of the pot on PvP duels
START_BALANCE = float(os.environ.get("DOPAMINE_START_BALANCE", "1000"))

# ----------------------------------------------------------------------------- DB
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init():
    c = db()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS agents (
      id INTEGER PRIMARY KEY,
      name TEXT UNIQUE NOT NULL,
      balance REAL NOT NULL,
      total_wagered REAL NOT NULL DEFAULT 0,
      total_won REAL NOT NULL DEFAULT 0,
      games_played INTEGER NOT NULL DEFAULT 0,
      created_at INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS seeds (
      agent_id INTEGER NOT NULL REFERENCES agents(id),
      server_seed TEXT NOT NULL,
      server_seed_hash TEXT NOT NULL,
      client_seed TEXT NOT NULL,
      nonce INTEGER NOT NULL DEFAULT 0,
      active INTEGER NOT NULL DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS bets (
      id INTEGER PRIMARY KEY,
      agent_id INTEGER NOT NULL REFERENCES agents(id),
      game TEXT NOT NULL,
      wager REAL NOT NULL,
      payout REAL NOT NULL,
      net REAL NOT NULL,
      outcome TEXT NOT NULL,
      server_seed_hash TEXT NOT NULL,
      client_seed TEXT NOT NULL,
      nonce INTEGER NOT NULL,
      created_at INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS duels (
      id INTEGER PRIMARY KEY,
      creator_id INTEGER NOT NULL REFERENCES agents(id),
      creator_choice INTEGER NOT NULL,
      stake REAL NOT NULL,
      opponent_id INTEGER,
      opponent_choice INTEGER,
      state TEXT NOT NULL DEFAULT 'OPEN',
      winner_id INTEGER,
      created_at INTEGER NOT NULL
    );
    """)
    c.commit(); c.close()

# ----------------------------------------------------------------------------- provably fair
def _new_pair():
    s = secrets.token_hex(32)
    return s, hashlib.sha256(s.encode()).hexdigest()

def get_seed(c, agent_id):
    row = c.execute("SELECT rowid,* FROM seeds WHERE agent_id=? AND active=1", (agent_id,)).fetchone()
    if row: return row
    s, h = _new_pair()
    client = secrets.token_hex(8)
    c.execute("INSERT INTO seeds(agent_id,server_seed,server_seed_hash,client_seed,nonce,active) VALUES(?,?,?,?,0,1)",
              (agent_id, s, h, client))
    return c.execute("SELECT rowid,* FROM seeds WHERE agent_id=? AND active=1", (agent_id,)).fetchone()

def rng_stream(server_seed, client_seed, nonce):
    """Deterministic stream of floats in [0,1) for one (seed,client,nonce)."""
    counter = 0
    while True:
        msg = f"{client_seed}:{nonce}:{counter}".encode()
        d = hmac.new(server_seed.encode(), msg, hashlib.sha256).digest()
        for i in range(0, len(d), 4):
            yield int.from_bytes(d[i:i+4], "big") / 2**32
        counter += 1

# ----------------------------------------------------------------------------- agent ops
def register(name):
    init()
    c = db()
    try:
        c.execute("INSERT INTO agents(name,balance,created_at) VALUES(?,?,?)",
                  (name, START_BALANCE, int(time.time())))
        c.commit()
        aid = c.execute("SELECT id FROM agents WHERE name=?", (name,)).fetchone()["id"]
        get_seed(c, aid); c.commit()
        return {"ok": True, "agent": name, "balance": START_BALANCE}
    except sqlite3.IntegrityError:
        return {"ok": False, "error": f"agent '{name}' already exists"}
    finally:
        c.close()

def _agent(c, name):
    r = c.execute("SELECT * FROM agents WHERE name=?", (name,)).fetchone()
    if not r: raise SystemExit(f"unknown agent '{name}' — register first")
    return r

def balance(name):
    c = db(); a = _agent(c, name); c.close()
    return {"agent": a["name"], "balance": round(a["balance"], 4),
            "wagered": round(a["total_wagered"], 2), "won": round(a["total_won"], 2),
            "games": a["games_played"]}

def leaderboard(limit=10):
    c = db()
    rows = c.execute("SELECT name,balance,total_wagered,games_played FROM agents ORDER BY balance DESC LIMIT ?",
                     (limit,)).fetchall()
    c.close()
    return [{"rank": i+1, "agent": r["name"], "balance": round(r["balance"], 2),
             "wagered": round(r["total_wagered"], 2), "games": r["games_played"]}
            for i, r in enumerate(rows)]

def fairness(name):
    c = db(); a = _agent(c, name); s = get_seed(c, a["id"]); c.commit(); c.close()
    return {"agent": name, "server_seed_hash": s["server_seed_hash"],
            "client_seed": s["client_seed"], "next_nonce": s["nonce"],
            "note": "verify past bets after rotating the seed to reveal server_seed"}

def rotate_seed(name):
    c = db(); a = _agent(c, name); old = get_seed(c, a["id"])
    s, h = _new_pair(); client = secrets.token_hex(8)
    c.execute("UPDATE seeds SET active=0 WHERE agent_id=? AND active=1", (a["id"],))
    c.execute("INSERT INTO seeds(agent_id,server_seed,server_seed_hash,client_seed,nonce,active) VALUES(?,?,?,?,0,1)",
              (a["id"], s, h, client))
    c.commit(); c.close()
    return {"revealed_server_seed": old["server_seed"], "revealed_hash": old["server_seed_hash"],
            "new_server_seed_hash": h, "new_client_seed": client}

# ----------------------------------------------------------------------------- bet settlement
def _settle(name, game, wager, payout_mult, outcome):
    """Apply one house bet atomically and record it. payout_mult is multiple of wager returned."""
    c = db()
    a = _agent(c, name)
    wager = round(float(wager), 4)
    if wager <= 0: c.close(); return {"ok": False, "error": "wager must be > 0"}
    if wager > a["balance"]: c.close(); return {"ok": False, "error": "insufficient balance"}
    s = get_seed(c, a["id"])
    payout = round(wager * payout_mult, 4)
    net = round(payout - wager, 4)
    new_bal = round(a["balance"] - wager + payout, 4)
    c.execute("UPDATE agents SET balance=?, total_wagered=total_wagered+?, total_won=total_won+?, games_played=games_played+1 WHERE id=?",
              (new_bal, wager, payout, a["id"]))
    c.execute("INSERT INTO bets(agent_id,game,wager,payout,net,outcome,server_seed_hash,client_seed,nonce,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
              (a["id"], game, wager, payout, net, json.dumps(outcome), s["server_seed_hash"], s["client_seed"], s["nonce"], int(time.time())))
    c.execute("UPDATE seeds SET nonce=nonce+1 WHERE rowid=?", (s["rowid"],))
    c.commit(); c.close()
    return {"ok": True, "game": game, "wager": wager, "payout": payout, "net": net,
            "balance": new_bal, "outcome": outcome,
            "fair": {"server_seed_hash": s["server_seed_hash"], "client_seed": s["client_seed"], "nonce": s["nonce"]}}

def _stream_for(name):
    c = db(); a = _agent(c, name); s = get_seed(c, a["id"]); c.commit(); c.close()
    return rng_stream(s["server_seed"], s["client_seed"], s["nonce"])

# ----------------------------------------------------------------------------- GAMES (house)
def coinflip(name, wager, pick):
    pick = pick.lower()
    if pick not in ("heads", "tails"): return {"ok": False, "error": "pick heads|tails"}
    st = _stream_for(name)
    side = "heads" if next(st) < 0.5 else "tails"
    win = side == pick
    mult = 2 * (1 - HOUSE_EDGE) if win else 0
    return _settle(name, "coinflip", wager, mult, {"pick": pick, "result": side, "win": win})

def dice(name, wager, target, direction):
    direction = direction.lower()
    target = float(target)
    if not (0 < target < 100): return {"ok": False, "error": "target must be 0<target<100"}
    if direction not in ("over", "under"): return {"ok": False, "error": "direction over|under"}
    st = _stream_for(name)
    roll = round(next(st) * 100, 2)
    if direction == "under":
        win = roll < target; chance = target / 100
    else:
        win = roll > target; chance = (100 - target) / 100
    mult = (1 / chance) * (1 - HOUSE_EDGE) if win else 0
    return _settle(name, "dice", wager, mult,
                   {"target": target, "direction": direction, "roll": roll, "win": win,
                    "chance_pct": round(chance * 100, 2)})

RPS_NAMES = {1: "rock", 2: "paper", 3: "scissors"}
def _rps_winner(a, b):  # 1=rock 2=paper 3=scissors; returns 0 tie, 1 a wins, 2 b wins
    if a == b: return 0
    return 1 if (a - b) % 3 == 1 else 2

def rps(name, wager, choice):
    cmap = {"rock": 1, "paper": 2, "scissors": 3}
    pick = cmap.get(str(choice).lower(), None) or (int(choice) if str(choice).isdigit() else None)
    if pick not in (1, 2, 3): return {"ok": False, "error": "choice rock|paper|scissors"}
    st = _stream_for(name)
    house = int(next(st) * 3) + 1
    w = _rps_winner(pick, house)
    if w == 0:   mult = 1            # push
    elif w == 1: mult = 2 * (1 - HOUSE_EDGE)
    else:        mult = 0
    return _settle(name, "rps", wager, mult,
                   {"you": RPS_NAMES[pick], "house": RPS_NAMES[house],
                    "result": ["tie", "win", "lose"][w]})

ROULETTE_RED = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
def roulette(name, wager, bet, value=None):
    bet = bet.lower()
    st = _stream_for(name)
    n = int(next(st) * 37)  # 0..36, single-zero European
    color = "green" if n == 0 else ("red" if n in ROULETTE_RED else "black")
    win, pay = False, 0
    if bet == "number":
        win = (n == int(value)); pay = 35
    elif bet in ("red", "black"):
        win = (color == bet); pay = 1
    elif bet in ("even", "odd"):
        win = (n != 0 and (n % 2 == 0) == (bet == "even")); pay = 1
    elif bet in ("low", "high"):
        win = (1 <= n <= 18) if bet == "low" else (19 <= n <= 36); pay = 1
    elif bet == "dozen":
        d = int(value)  # 1,2,3
        win = (d - 1) * 12 < n <= d * 12; pay = 2
    else:
        return {"ok": False, "error": "bet number|red|black|even|odd|low|high|dozen"}
    mult = (1 + pay) * (1 - HOUSE_EDGE) if win else 0
    return _settle(name, "roulette", wager, mult,
                   {"bet": bet, "value": value, "number": n, "color": color, "win": win})

SLOT_REEL = (["seven"]*1 + ["claw"]*2 + ["star"]*4 + ["bell"]*6 + ["lemon"]*8 + ["cherry"]*9)
SLOT_PAY  = {"seven": 60, "claw": 25, "star": 12, "bell": 8, "lemon": 5, "cherry": 3}
def slots(name, wager):
    st = _stream_for(name)
    reels = [SLOT_REEL[int(next(st) * len(SLOT_REEL))] for _ in range(3)]
    if reels[0] == reels[1] == reels[2]:
        mult = SLOT_PAY[reels[0]] * (1 - HOUSE_EDGE)
    elif reels.count("cherry") == 2:
        mult = 2 * (1 - HOUSE_EDGE)        # two cherries small win
    else:
        mult = 0
    return _settle(name, "slots", wager, mult, {"reels": reels, "win": mult > 0})

# ---- Blackjack (auto-resolved with a strategy or explicit action list) -------
def _bj_total(hand):
    t = sum(min(c, 10) for c in hand); aces = hand.count(1)
    while aces and t + 10 <= 21: t += 10; aces -= 1
    return t
def _is_soft(hand):
    t = sum(min(c, 10) for c in hand); aces = hand.count(1)
    return aces > 0 and t + 10 <= 21

def blackjack(name, wager, strategy="basic", stand_on=17, actions=None):
    st = _stream_for(name)
    draw = lambda: int(next(st) * 13) + 1  # 1..13 (1=ace, 11-13 face=10)
    player = [draw(), draw()]; dealer = [draw(), draw()]
    log = []
    p_bj = _bj_total(player) == 21
    d_bj = _bj_total(dealer) == 21

    if not (p_bj or d_bj):
        if actions:  # explicit agent decisions: list of 'hit'/'stand'
            for act in actions:
                if act == "hit":
                    player.append(draw()); log.append("hit")
                    if _bj_total(player) > 21: break
                else:
                    log.append("stand"); break
        else:  # auto strategy
            while True:
                t = _bj_total(player)
                if strategy == "dealer":
                    go = t < 17
                elif strategy == "aggressive":
                    go = t < 19 and not (_is_soft(player) and t >= 18)
                elif strategy == "conservative":
                    go = t < 13
                else:  # basic-ish: hit <17, stand >=17
                    go = t < int(stand_on)
                if go and t <= 21:
                    player.append(draw()); log.append("hit")
                else:
                    log.append("stand"); break
        # dealer plays to 17 (stands on all 17) if player not bust
        if _bj_total(player) <= 21:
            while _bj_total(dealer) < 17:
                dealer.append(draw())

    pt, dt = _bj_total(player), _bj_total(dealer)
    if p_bj and not d_bj:      mult, res = 2.5, "blackjack"
    elif d_bj and not p_bj:    mult, res = 0,   "dealer_blackjack"
    elif p_bj and d_bj:        mult, res = 1,   "push"
    elif pt > 21:              mult, res = 0,   "bust"
    elif dt > 21:              mult, res = 2,   "dealer_bust"
    elif pt > dt:              mult, res = 2,   "win"
    elif pt < dt:             mult, res = 0,   "lose"
    else:                      mult, res = 1,   "push"
    return _settle(name, "blackjack", wager, mult,
                   {"player": player, "player_total": pt, "dealer": dealer, "dealer_total": dt,
                    "actions": log, "result": res})

# ----------------------------------------------------------------------------- PvP duels (agent vs agent RPS, 80/20)
def duel_create(name, choice, stake):
    cmap = {"rock": 1, "paper": 2, "scissors": 3}
    pick = cmap.get(str(choice).lower()) or (int(choice) if str(choice).isdigit() else None)
    if pick not in (1, 2, 3): return {"ok": False, "error": "choice rock|paper|scissors"}
    c = db(); a = _agent(c, name); stake = round(float(stake), 4)
    if stake <= 0 or stake > a["balance"]: c.close(); return {"ok": False, "error": "bad stake / insufficient balance"}
    c.execute("UPDATE agents SET balance=balance-? WHERE id=?", (stake, a["id"]))  # escrow
    c.execute("INSERT INTO duels(creator_id,creator_choice,stake,created_at) VALUES(?,?,?,?)",
              (a["id"], pick, stake, int(time.time())))
    gid = c.execute("SELECT last_insert_rowid() AS i").fetchone()["i"]
    c.commit(); c.close()
    return {"ok": True, "duel_id": gid, "stake": stake, "state": "OPEN",
            "note": "your choice is committed; opponent joins to settle"}

def duel_list():
    c = db()
    rows = c.execute("""SELECT d.id,d.stake,a.name AS creator FROM duels d
                        JOIN agents a ON a.id=d.creator_id WHERE d.state='OPEN' ORDER BY d.id""").fetchall()
    c.close()
    return [{"duel_id": r["id"], "creator": r["creator"], "stake": r["stake"]} for r in rows]

def duel_join(name, duel_id, choice):
    cmap = {"rock": 1, "paper": 2, "scissors": 3}
    pick = cmap.get(str(choice).lower()) or (int(choice) if str(choice).isdigit() else None)
    if pick not in (1, 2, 3): return {"ok": False, "error": "choice rock|paper|scissors"}
    c = db(); b = _agent(c, name)
    d = c.execute("SELECT * FROM duels WHERE id=?", (duel_id,)).fetchone()
    if not d or d["state"] != "OPEN": c.close(); return {"ok": False, "error": "duel not open"}
    if d["creator_id"] == b["id"]: c.close(); return {"ok": False, "error": "cannot join your own duel"}
    if d["stake"] > b["balance"]: c.close(); return {"ok": False, "error": "insufficient balance"}
    c.execute("UPDATE agents SET balance=balance-? WHERE id=?", (d["stake"], b["id"]))  # escrow
    w = _rps_winner(d["creator_choice"], pick)
    pot = d["stake"] * 2
    rake = 0.0
    creator = c.execute("SELECT * FROM agents WHERE id=?", (d["creator_id"],)).fetchone()
    if w == 0:  # tie -> refund both
        c.execute("UPDATE agents SET balance=balance+? WHERE id=?", (d["stake"], creator["id"]))
        c.execute("UPDATE agents SET balance=balance+? WHERE id=?", (d["stake"], b["id"]))
        winner_id, result = None, "tie"
    else:
        # rake comes off the pot; loser keeps a 20% anti-bankruptcy floor; winner takes the rest
        win_id  = creator["id"] if w == 1 else b["id"]
        lose_id = b["id"] if w == 1 else creator["id"]
        rake        = round(pot * DUEL_RAKE, 4)
        loser_keep  = round(d["stake"] * 0.2, 4)
        winner_take = round(pot - rake - loser_keep, 4)
        c.execute("UPDATE agents SET balance=balance+? WHERE id=?", (winner_take, win_id))
        c.execute("UPDATE agents SET balance=balance+? WHERE id=?", (loser_keep, lose_id))
        winner_id, result = win_id, "creator_win" if w == 1 else "opponent_win"
    c.execute("UPDATE duels SET opponent_id=?,opponent_choice=?,state='SETTLED',winner_id=? WHERE id=?",
              (b["id"], pick, winner_id, duel_id))
    c.commit()
    out = {"ok": True, "duel_id": duel_id, "result": result,
           "creator": creator["name"], "creator_choice": RPS_NAMES[d["creator_choice"]],
           "opponent": b["name"], "opponent_choice": RPS_NAMES[pick], "pot": pot, "rake": rake}
    c.close(); return out

# ----------------------------------------------------------------------------- CLI
def main():
    p = argparse.ArgumentParser(prog="dopamine", description="SuperClaw Dopamine — DB-backed, provably fair")
    sub = p.add_subparsers(dest="cmd")

    def add(name, *flags):
        sp = sub.add_parser(name)
        for f, req in flags:
            sp.add_argument(f"--{f}", required=req)
        sp.add_argument("--render", choices=["json", "card"], default="json")
        return sp

    add("register", ("agent", True))
    add("balance", ("agent", True))
    sub.add_parser("leaderboard").add_argument("--limit", default="10")
    add("fairness", ("agent", True))
    add("rotate-seed", ("agent", True))
    add("coinflip", ("agent", True), ("wager", True), ("pick", True))
    add("dice", ("agent", True), ("wager", True), ("target", True), ("direction", True))
    add("rps", ("agent", True), ("wager", True), ("choice", True))
    add("roulette", ("agent", True), ("wager", True), ("bet", True), ("value", False))
    add("slots", ("agent", True), ("wager", True))
    bj = add("blackjack", ("agent", True), ("wager", True))
    bj.add_argument("--strategy", default="basic"); bj.add_argument("--stand-on", default="17")
    bj.add_argument("--actions", default=None, help="comma list: hit,hit,stand")
    add("duel-create", ("agent", True), ("choice", True), ("stake", True))
    sub.add_parser("duel-list")
    add("duel-join", ("agent", True), ("id", True), ("choice", True))
    sub.add_parser("help")

    a = p.parse_args()
    init()
    if a.cmd == "register":        r = register(a.agent)
    elif a.cmd == "balance":       r = balance(a.agent)
    elif a.cmd == "leaderboard":   r = leaderboard(int(a.limit))
    elif a.cmd == "fairness":      r = fairness(a.agent)
    elif a.cmd == "rotate-seed":   r = rotate_seed(a.agent)
    elif a.cmd == "coinflip":      r = coinflip(a.agent, a.wager, a.pick)
    elif a.cmd == "dice":          r = dice(a.agent, a.wager, a.target, a.direction)
    elif a.cmd == "rps":           r = rps(a.agent, a.wager, a.choice)
    elif a.cmd == "roulette":      r = roulette(a.agent, a.wager, a.bet, a.value)
    elif a.cmd == "slots":         r = slots(a.agent, a.wager)
    elif a.cmd == "blackjack":
        acts = a.actions.split(",") if a.actions else None
        r = blackjack(a.agent, a.wager, a.strategy, a.stand_on, acts)
    elif a.cmd == "duel-create":   r = duel_create(a.agent, a.choice, a.stake)
    elif a.cmd == "duel-list":     r = duel_list()
    elif a.cmd == "duel-join":     r = duel_join(a.agent, a.id, a.choice)
    else:
        print(__doc__); return
    if getattr(a, "render", "json") == "card" and isinstance(r, dict) and r.get("ok") and r.get("game"):
        from dopamine.render import render_card
        print(render_card(r))
    else:
        print(json.dumps(r, indent=2))

if __name__ == "__main__":
    main()

I_EOF
echo ">> updating SKILL.md"
cat > SKILL.md <<'S_EOF'
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

S_EOF
sed -i.bak 's/version = "1.3.0"/version = "1.4.0"/; s/version = "1.2.0"/version = "1.4.0"/; s/version = "1.1.0"/version = "1.4.0"/; s/version = "1.0.0"/version = "1.4.0"/' pyproject.toml && rm -f pyproject.toml.bak
echo ""
echo "DONE. Now run:"
echo "   git add -A && git commit -m \"v1.4.0: animated in-chat cards\" && git push"
