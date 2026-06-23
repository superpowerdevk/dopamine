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
    print(json.dumps(r, indent=2))

if __name__ == "__main__":
    main()
