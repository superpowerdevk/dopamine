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

