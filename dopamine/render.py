#!/usr/bin/env python3
"""Render a dopamine game result into a self-contained, JS-ANIMATED HTML card.

render_card(result) -> str. An inline <script> drives animation after mount:
blackjack deals card-by-card; roulette spins a real wheel that decelerates and
lands the ball on the number; slots reels cycle and stop; the coin flips; dice
tumble through values then settle; RPS shakes ("shoot") then reveals.
No network, no external assets. Honours prefers-reduced-motion.

Suits/positions are cosmetic, derived from the fairness hash; they don't affect
provably-fair verification.
"""
import hashlib
import math

_CSS = """
<style>
.dop{--gold:#e7c66b;--gold-d:#9c8540;--win:#46e08a;--lose:#ff5d73;--push:#e7c66b;
 --card:#f7f4ec;--cr:#cf2d3b;--cb:#16181d;--txt:#e9e6dd;--dim:#8a988f;
 --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
 font-family:var(--mono);color:var(--txt);width:100%;max-width:560px;container-type:inline-size;
 border-radius:18px;position:relative;background:radial-gradient(120% 90% at 50% 0,#0c2a1e,#061711);
 border:1px solid rgba(231,198,107,.28);box-shadow:0 20px 60px rgba(0,0,0,.55);padding:18px 20px 16px;overflow:hidden}
.dop::before{content:"";position:absolute;inset:8px;border-radius:12px;border:1px solid rgba(231,198,107,.12);pointer-events:none}
.dop .eb{display:flex;justify-content:space-between;align-items:center;font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:var(--gold-d)}
.dop .eb b{color:var(--gold);font-weight:700}.dop .eb .h{color:#5b6b62;font-size:10px;letter-spacing:.08em}
.dop .lane{display:flex;align-items:center;justify-content:space-between;margin-top:6px}
.dop .who{font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--dim)}
.dop .tot{font-size:13px}.dop .tag{margin-left:8px;padding:2px 7px;border-radius:999px;font-size:10px;letter-spacing:.12em;text-transform:uppercase}
.dop .tag.bust{background:rgba(255,93,115,.16);color:var(--lose)}.dop .tag.bj{background:rgba(70,224,138,.16);color:var(--win)}
.dop .hand{display:flex;gap:8px;margin:8px 0 2px;flex-wrap:wrap}
.dop .card{width:clamp(44px,11cqi,64px);height:clamp(62px,15.4cqi,90px);border-radius:8px;position:relative;flex:0 0 auto;
 background:linear-gradient(160deg,#fff,var(--card));box-shadow:0 7px 16px rgba(0,0,0,.5),inset 0 0 0 1px rgba(0,0,0,.07)}
.dop .card .r{position:absolute;font-weight:800;font-size:clamp(11px,3.4cqi,15px);line-height:1;font-family:Georgia,serif}
.dop .card .r.tl{top:7px;left:8px}.dop .card .r.br{bottom:7px;right:8px;transform:rotate(180deg)}
.dop .card .s{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:clamp(22px,7cqi,30px)}
.dop .card.red{color:var(--cr)}.dop .card.black{color:var(--cb)}
.dop .banner{margin:12px 0;text-align:center;border-radius:10px;padding:12px;font-family:system-ui,Segoe UI,Roboto,sans-serif;
 font-weight:800;letter-spacing:.04em;font-size:clamp(17px,5.5cqi,22px);text-transform:uppercase}
.dop .banner small{display:block;font-family:var(--mono);font-weight:600;font-size:12px;letter-spacing:.18em;margin-top:3px;opacity:.85}
.dop .banner.win{color:var(--win);background:radial-gradient(80% 140% at 50% 0,rgba(70,224,138,.18),transparent);text-shadow:0 0 22px rgba(70,224,138,.55)}
.dop .banner.lose{color:var(--lose);background:radial-gradient(80% 140% at 50% 0,rgba(255,93,115,.16),transparent)}
.dop .banner.push{color:var(--push)}
.dop .strip{display:grid;grid-template-columns:repeat(auto-fit,minmax(118px,1fr));gap:8px;margin-top:10px;border-top:1px solid rgba(231,198,107,.12);padding-top:10px}
.dop .stat{text-align:center}.dop .stat .k{font-size:10px;letter-spacing:.18em;text-transform:uppercase;color:var(--dim)}
.dop .stat .v{font-size:15px;margin-top:3px}.dop .stat .v.up{color:var(--win)}.dop .stat .v.down{color:var(--lose)}
.dop .betspot{display:flex;align-items:center;gap:10px;margin:8px 0 2px}
.dop .betspot .ring{width:clamp(34px,10cqi,44px);height:clamp(34px,10cqi,44px);border-radius:50%;border:2px dashed rgba(231,198,107,.4);display:flex;align-items:center;justify-content:center}
.dop .bchip{width:clamp(28px,8.5cqi,38px);height:clamp(28px,8.5cqi,38px);border-radius:50%;background:radial-gradient(circle at 35% 30%,#f6dd95,#caa544);
 border:2px dashed #8a6d1f;color:#3b2f0c;font-size:clamp(9px,2.8cqi,12px);font-weight:800;display:flex;align-items:center;justify-content:center}
.dop .betspot .lbl{font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:var(--dim)}
/* roulette wheel */
.dop .wheelwrap{position:relative;width:clamp(190px,62cqi,250px);margin:8px auto 2px}
.dop .wheel{display:block;width:100%;height:auto;filter:drop-shadow(0 10px 22px rgba(0,0,0,.5))}
.dop .landed{text-align:center;font-size:13px;color:var(--dim);margin-top:2px}.dop .landed b{color:var(--txt)}
.dop .betline{text-align:center;font-size:11px;letter-spacing:.06em;color:var(--gold-d);text-transform:uppercase;margin-top:4px}
.dop .betline b{color:var(--gold)}
/* reels / coin / track / dice / rps */
.dop .reels{display:flex;gap:8px;justify-content:center;margin:6px 0}
.dop .reel{width:clamp(48px,14cqi,60px);height:clamp(58px,17cqi,72px);border-radius:8px;display:flex;align-items:center;justify-content:center;
 font-size:clamp(26px,8cqi,34px);background:#0a0d0c;box-shadow:inset 0 0 0 1px rgba(231,198,107,.25),inset 0 8px 18px rgba(0,0,0,.6);overflow:hidden}
.dop .coin{width:clamp(70px,22cqi,84px);height:clamp(70px,22cqi,84px);border-radius:50%;margin:6px auto;display:flex;align-items:center;justify-content:center;
 font-size:32px;font-weight:800;color:#3b2f0c;background:radial-gradient(circle at 35% 30%,#f6dd95,#caa544);box-shadow:0 6px 14px rgba(0,0,0,.45)}
.dop .coin.flipping{animation:dopflip .7s ease-out}
.dop .rollnum{text-align:center;font-size:clamp(32px,11cqi,46px);font-weight:800;color:var(--gold);margin:6px 0 2px;text-shadow:0 0 18px rgba(231,198,107,.4)}
.dop .track{height:10px;border-radius:999px;background:#0a0d0c;position:relative;margin:8px 0;box-shadow:inset 0 0 0 1px rgba(231,198,107,.2)}
.dop .track .wz{position:absolute;top:0;bottom:0;background:rgba(70,224,138,.22);border-radius:999px}
.dop .track .rl{position:absolute;top:-5px;width:3px;height:20px;background:var(--gold);left:0}
.dop .hands{display:flex;justify-content:center;gap:26px;font-size:clamp(34px,11cqi,46px);margin:8px 0}
.dop .center{text-align:center;font-size:13px;color:var(--dim);margin-top:6px}.dop .center b{color:var(--txt)}
/* JS-driven reveal */
.dop .anim{opacity:0;transform:translateY(-12px);transition:opacity .34s ease,transform .42s cubic-bezier(.2,.8,.2,1)}
.dop .card.anim{transform:translateY(-22px) rotate(-7deg) scale(.94)}
.dop .anim.go{opacity:1;transform:none}
.dop .shake{animation:dopshake .24s ease-in-out infinite}
@keyframes dopflip{0%{transform:rotateY(0)}100%{transform:rotateY(720deg)}}
@keyframes dopshake{0%,100%{transform:translateY(0) rotate(-6deg)}50%{transform:translateY(-12px) rotate(6deg)}}
@media (prefers-reduced-motion:reduce){.dop .anim{opacity:1!important;transform:none!important;transition:none!important}
 .dop .coin.flipping{animation:none}.dop .shake{animation:none}}
</style>
"""

_SCRIPT = """
<script>
(function(){
  var s=document.currentScript; var root=(s&&s.closest&&s.closest('.dop'))||document;
  var reduce=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function run(){
    var faces=["7\\uFE0F\\u20E3","\\u2B50","\\uD83D\\uDD14","\\uD83C\\uDF4B","\\uD83C\\uDF52","\\uD83E\\uDDBE"];
    root.querySelectorAll(".anim").forEach(function(e){
      var d=reduce?0:(parseFloat(e.getAttribute("data-d"))||0);
      setTimeout(function(){ e.classList.add("go"); }, d);
    });
    root.querySelectorAll("[data-spin]").forEach(function(e){
      var fin=e.getAttribute("data-final"); var stop=parseFloat(e.getAttribute("data-spin"))||800;
      if(reduce){ e.textContent=fin; return; }
      var iv=setInterval(function(){ e.textContent=faces[Math.floor(Math.random()*faces.length)]; },80);
      setTimeout(function(){ clearInterval(iv); e.textContent=fin; }, stop);
    });
    root.querySelectorAll("[data-flip]").forEach(function(e){
      var fin=e.getAttribute("data-final"); if(reduce){ e.textContent=fin; return; }
      e.classList.add("flipping"); setTimeout(function(){ e.textContent=fin; }, 350);
    });
    root.querySelectorAll("[data-slide]").forEach(function(e){
      var to=e.getAttribute("data-slide"); if(reduce){ e.style.left=to+"%"; return; }
      requestAnimationFrame(function(){ e.style.transition="left .75s cubic-bezier(.2,.8,.2,1)"; e.style.left=to+"%"; });
    });
    // dice: tumble through values then settle
    root.querySelectorAll("[data-roll]").forEach(function(e){
      var fin=e.getAttribute("data-roll"); if(reduce){ e.textContent=fin; return; }
      var iv=setInterval(function(){ e.textContent=Math.floor(Math.random()*101); },55);
      setTimeout(function(){ clearInterval(iv); e.textContent=fin; }, 900);
    });
    // rps: shake ("shoot") then reveal
    root.querySelectorAll("[data-throw]").forEach(function(e){
      var fin=e.getAttribute("data-final"); if(reduce){ e.textContent=fin; return; }
      e.classList.add("shake");
      setTimeout(function(){ e.classList.remove("shake"); e.textContent=fin; }, 850);
    });
    // roulette wheel: spin and decelerate to land the winner under the pointer
    root.querySelectorAll("[data-wheel]").forEach(function(e){
      var deg=parseFloat(e.getAttribute("data-wheel"))||0;
      var cx=parseFloat(e.getAttribute("data-cx"))||120, cy=parseFloat(e.getAttribute("data-cy"))||120;
      if(reduce){ e.setAttribute("transform","rotate("+deg+" "+cx+" "+cy+")"); return; }
      var dur=2900, t0=null;
      function ease(p){ return 1-Math.pow(1-p,3); }
      function frame(ts){ if(t0===null)t0=ts; var p=Math.min((ts-t0)/dur,1);
        e.setAttribute("transform","rotate("+(deg*ease(p)).toFixed(2)+" "+cx+" "+cy+")");
        if(p<1) requestAnimationFrame(frame); }
      requestAnimationFrame(frame);
    });
  }
  if(document.readyState==="loading"){ document.addEventListener("DOMContentLoaded",run); } else { run(); }
})();
</script>
"""

_SUITS = [("\u2660", "black"), ("\u2665", "red"), ("\u2666", "red"), ("\u2663", "black")]
_RRED = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
_WHEEL = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10,
          5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26]
_SLOT_EMOJI = {"seven": "7\ufe0f\u20e3", "claw": "\U0001f9be", "star": "\u2b50",
               "bell": "\U0001f514", "lemon": "\U0001f34b", "cherry": "\U0001f352"}
_RPS_EMOJI = {"rock": "\u270a", "paper": "\u270b", "scissors": "\u270c\ufe0f"}
STEP = 300  # ms between dealt items (slightly slower pace)


def _suit(h, nonce, i):
    n = int(hashlib.sha256(f"{h}:{nonce}:s{i}".encode()).hexdigest(), 16)
    return _SUITS[n % 4]


def _rank(r):
    return {1: "A", 11: "J", 12: "Q", 13: "K"}.get(int(r), str(int(r)))


def _card(rank_val, h, nonce, i, delay):
    g, cls = _suit(h, nonce, i)
    lbl = _rank(rank_val)
    return (f'<div class="card anim {cls}" data-d="{delay}"><span class="r tl">{lbl}</span>'
            f'<span class="s">{g}</span><span class="r br">{lbl}</span></div>')


def _eb(game, r):
    h = r.get("fair", {}).get("server_seed_hash", "")
    short = (h[:8] + "\u2026") if h else ""
    return f'<div class="eb"><span>DOPAMINE \u00b7 <b>{game}</b></span><span class="h">fair \u25c6 {short}</span></div>'


def _strip(r, delay):
    net = r["net"]
    ncls = "up" if net > 0 else ("down" if net < 0 else "")
    nstr = f"+{net:g}" if net > 0 else f"{net:g}"
    return (f'<div class="strip anim" data-d="{delay}">'
            f'<div class="stat"><div class="k">Wager</div><div class="v">{r["wager"]:g}</div></div>'
            f'<div class="stat"><div class="k">Payout</div><div class="v">{r["payout"]:g}</div></div>'
            f'<div class="stat"><div class="k">Net</div><div class="v {ncls}">{nstr}</div></div>'
            f'<div class="stat"><div class="k">Balance</div><div class="v">{r["balance"]:,.0f}</div></div>'
            f'</div>')


def _banner(kind, big, small, delay):
    return f'<div class="banner anim {kind}" data-d="{delay}">{big}<small>{small}</small></div>'


def _kind(r):
    return "win" if r["net"] > 0 else ("lose" if r["net"] < 0 else "push")


def _netw(r):
    return f'+{r["net"]:g}' if r["net"] > 0 else (f'{r["net"]:g}' if r["net"] < 0 else "push")


def _wrap(body):
    return f'<div class="dop">{body}{_SCRIPT}</div>{_CSS}'


def render_card(r):
    g = r.get("game")
    fn = {"blackjack": _blackjack, "slots": _slots, "roulette": _roulette,
          "coinflip": _coinflip, "dice": _dice, "rps": _rps}.get(g)
    return _wrap(fn(r) if fn else (_eb(g or "game", r) + _strip(r, 0)))


def _blackjack(r):
    o = r["outcome"]; h = r.get("fair", {}).get("server_seed_hash", ""); n = r.get("fair", {}).get("nonce", 0)
    d = 0
    dealer = ""
    for i, c in enumerate(o["dealer"]):
        dealer += _card(c, h, n, 100 + i, d); d += STEP
    bann_d = d + STEP
    player = ""
    pd = bann_d + STEP
    for i, c in enumerate(o["player"]):
        player += _card(c, h, n, i, pd); pd += STEP
    bet_d = pd
    strip_d = pd + STEP
    dtag = ' <span class="tag bust">Bust</span>' if o["dealer_total"] > 21 else (
           ' <span class="tag bj">BJ</span>' if o["result"] == "dealer_blackjack" else "")
    ptag = ' <span class="tag bust">Bust</span>' if o["player_total"] > 21 else (
           ' <span class="tag bj">BJ</span>' if o["result"] == "blackjack" else "")
    labels = {"blackjack": "Blackjack!", "dealer_bust": "Dealer bust", "win": "You win",
              "dealer_blackjack": "Dealer blackjack", "bust": "Bust", "lose": "Dealer wins", "push": "Push"}
    big = f'Winner {_netw(r)}' if r["net"] > 0 else (labels.get(o["result"], "Lose") if r["net"] < 0 else "Push")
    return (_eb("BLACKJACK", r) +
            f'<div class="lane"><span class="who">Dealer</span><span class="tot">{o["dealer_total"]}{dtag}</span></div>'
            f'<div class="hand">{dealer}</div>' +
            _banner(_kind(r), big, labels.get(o["result"], ""), bann_d) +
            f'<div class="lane"><span class="who">You</span><span class="tot">{o["player_total"]}{ptag}</span></div>'
            f'<div class="hand">{player}</div>' +
            f'<div class="betspot anim" data-d="{bet_d}"><div class="ring"><div class="bchip">{r["wager"]:g}</div></div>'
            f'<span class="lbl">your bet</span></div>' + _strip(r, strip_d))


def _slots(r):
    o = r["outcome"]; reels = ""
    stops = [600, 1000, 1400]
    for i, x in enumerate(o["reels"]):
        fin = _SLOT_EMOJI.get(x, x)
        reels += f'<div class="reel" data-spin="{stops[i] if i < len(stops) else 1400}" data-final="{fin}">\u2753</div>'
    big = (f'{"Jackpot " if r["net"] >= r["wager"]*10 else "Win "}{_netw(r)}' if r["net"] > 0 else "No match")
    return (_eb("SLOTS", r) + f'<div class="reels">{reels}</div>' +
            _banner(_kind(r), big, " ".join(o["reels"]), 1600) + _strip(r, 1750))


def _wheel_svg(win_n):
    step = 360.0 / 37
    cx = cy = 120.0
    R = 112.0
    r_in = 46.0
    segs = []
    for i, num in enumerate(_WHEEL):
        a0 = math.radians(i * step - 90)
        a1 = math.radians((i + 1) * step - 90)
        x0, y0 = cx + R * math.cos(a0), cy + R * math.sin(a0)
        x1, y1 = cx + R * math.cos(a1), cy + R * math.sin(a1)
        xi0, yi0 = cx + r_in * math.cos(a0), cy + r_in * math.sin(a0)
        xi1, yi1 = cx + r_in * math.cos(a1), cy + r_in * math.sin(a1)
        col = "#138a36" if num == 0 else ("#b3242f" if num in _RRED else "#1c1f25")
        d = (f'M{x0:.1f},{y0:.1f} A{R:.0f},{R:.0f} 0 0 1 {x1:.1f},{y1:.1f} '
             f'L{xi1:.1f},{yi1:.1f} A{r_in:.0f},{r_in:.0f} 0 0 0 {xi0:.1f},{yi0:.1f} Z')
        segs.append(f'<path d="{d}" fill="{col}" stroke="#0a0d0c" stroke-width="0.6"/>')
        am = math.radians((i + 0.5) * step - 90)
        lr = (R + r_in) / 2 + 6
        lx, ly = cx + lr * math.cos(am), cy + lr * math.sin(am)
        rot = (i + 0.5) * step
        segs.append(f'<text x="{lx:.1f}" y="{ly:.1f}" fill="#fff" font-size="9" font-weight="700" '
                    f'text-anchor="middle" dominant-baseline="central" '
                    f'transform="rotate({rot:.1f} {lx:.1f} {ly:.1f})">{num}</text>')
    w = _WHEEL.index(win_n)
    deg = 1800 - (w + 0.5) * step  # 5 turns, land winner at top
    wheel = (f'<g data-wheel="{deg:.2f}" data-cx="{cx:.0f}" data-cy="{cy:.0f}">{"".join(segs)}</g>')
    hub = f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r_in-4:.0f}" fill="#0a1f17" stroke="rgba(231,198,107,.45)" stroke-width="1.5"/>'
    hub += f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="8" fill="#caa544"/>'
    pointer = f'<path d="M{cx:.0f},2 l-8,-14 l16,0 Z" fill="#e7c66b" transform="translate(0,14)"/>'
    ball = f'<circle cx="{cx:.0f}" cy="16" r="5.5" fill="#fff" stroke="#aaa" stroke-width="1"/>'
    return f'<div class="wheelwrap"><svg viewBox="0 0 240 244" class="wheel">{wheel}{hub}{pointer}{ball}</svg></div>'


def _roulette(r):
    o = r["outcome"]; win_n = int(o["number"]); col = o["color"]; bet = o["bet"]; val = o.get("value")
    wheel = _wheel_svg(win_n)
    vtxt = "" if val in (None, "None") else " " + str(val)
    big = f'Win {_netw(r)}' if r["net"] > 0 else "Miss"
    return (_eb("ROULETTE", r) + wheel +
            f'<div class="betline anim" data-d="0">your bet \u00b7 <b>{bet}{vtxt}</b></div>' +
            f'<div class="landed anim" data-d="2850">landed <b>{win_n} {col}</b></div>' +
            _banner(_kind(r), big, "", 3050) + _strip(r, 3250))


def _coinflip(r):
    o = r["outcome"]; face = "H" if o["result"] == "heads" else "T"
    big = f'Win {_netw(r)}' if r["net"] > 0 else "Lose"
    return (_eb("COINFLIP", r) + f'<div class="coin" data-flip="1" data-final="{face}">?</div>'
            f'<div class="center anim" data-d="700">you picked <b>{o["pick"]}</b> \u00b7 flipped <b>{o["result"]}</b></div>' +
            _banner(_kind(r), big, "", 850) + _strip(r, 1000))


def _dice(r):
    o = r["outcome"]; t = o["target"]; roll = o["roll"]
    wz = f'left:0;width:{t}%' if o["direction"] == "under" else f'left:{t}%;width:{100-t}%'
    pos = min(max(roll, 0), 100)
    chance = o.get("chance_pct", o.get("chance", ""))
    ctxt = f' \u00b7 {chance:g}% chance' if isinstance(chance, (int, float)) else ""
    big = f'Win {_netw(r)}' if r["net"] > 0 else "Lose"
    return (_eb("DICE", r) +
            f'<div class="rollnum" data-roll="{roll:g}">0</div>'
            f'<div class="track"><div class="wz" style="{wz}"></div><div class="rl" data-slide="{pos}"></div></div>'
            f'<div class="center anim" data-d="1000">{o["direction"]} <b>{t:g}</b>{ctxt}</div>' +
            _banner(_kind(r), big, "", 1150) + _strip(r, 1300))


def _rps(r):
    o = r["outcome"]
    you = _RPS_EMOJI.get(o["you"], "?"); house = _RPS_EMOJI.get(o["house"], "?")
    big = (f'Win {_netw(r)}' if r["net"] > 0 else ("Push" if o["result"] == "tie" else "Lose"))
    return (_eb("RPS", r) +
            f'<div class="hands"><span data-throw="1" data-final="{you}">\u270a</span>'
            f'<span data-throw="1" data-final="{house}">\u270a</span></div>'
            f'<div class="center anim" data-d="950">you <b>{o["you"]}</b> \u00b7 house <b>{o["house"]}</b></div>' +
            _banner(_kind(r) if o["result"] != "tie" else "push", big, "", 1100) + _strip(r, 1250))

