from __future__ import annotations

import logging

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.config import HOST, PORT
from app.routes import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Replicate OpenAI Gateway",
    description=(
        "An OpenAI-compatible API gateway that routes requests to Replicate-hosted models. "
        "Point any OpenAI SDK client at this server using base_url='http://localhost:8000/v1'."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/v1")

GH = "https://github.com/CookieShualon/replicate-openai"
GH_ICON = '<svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/></svg>'


@app.get("/", tags=["health"], response_class=HTMLResponse)
async def homepage(request: Request) -> HTMLResponse:
    base_url = str(request.url_for("list_models")).removesuffix("/models")
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Replicate OpenAI Gateway</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --bg:    #0b0c0e;
      --bg2:   #111316;
      --bg3:   #18191d;
      --bd:    #22242a;
      --bd2:   #2d2f36;
      --text:  #ededea;
      --dim:   #8a8c92;
      --muted: #4e5058;
      --a:     #b8f952;
      --a2:    #93d93b;
      --adim:  rgba(184,249,82,.07);
      --aglow: rgba(184,249,82,.18);
      --red:   #f87171;
      --blue:  #7eb8f7;
      --ora:   #f5a623;
      --pur:   #c084fc;
      --mono:  ui-monospace,"SF Mono","Cascadia Code",monospace;
    }}

    html {{ scroll-behavior: smooth; }}
    body {{
      font-family: -apple-system,BlinkMacSystemFont,"Inter","Segoe UI",sans-serif;
      background-color: var(--bg);
      background-image: radial-gradient(circle, rgba(255,255,255,.028) 1px, transparent 1px);
      background-size: 26px 26px;
      color: var(--text);
      min-height: 100vh;
      line-height: 1.6;
    }}

    /* ─── NAV ─────────────────────────────────────────── */
    nav {{
      position: sticky; top: 0; z-index: 100;
      height: 52px;
      display: flex; align-items: center; justify-content: space-between;
      padding: 0 2rem;
      background: rgba(11,12,14,.82);
      backdrop-filter: blur(18px) saturate(160%);
      border-bottom: 1px solid var(--bd);
    }}
    .n-left {{ display: flex; align-items: center; gap: 20px; }}
    .logo {{
      display: flex; align-items: center; gap: 9px;
      font-weight: 700; font-size: 0.9rem; letter-spacing: -.02em;
      text-decoration: none; color: var(--text);
    }}
    .logo-mark {{
      width: 26px; height: 26px; border-radius: 7px;
      background: var(--a); color: #000;
      font-weight: 900; font-size: 0.82rem;
      display: flex; align-items: center; justify-content: center;
      flex-shrink: 0;
    }}
    .n-ver {{
      font-size: 0.7rem; padding: 2px 7px; border-radius: 4px;
      background: var(--bg3); border: 1px solid var(--bd);
      color: var(--muted); font-family: var(--mono);
    }}
    .n-right {{ display: flex; align-items: center; gap: 2px; }}
    .n-link {{
      padding: 5px 11px; border-radius: 6px;
      font-size: 0.82rem; font-weight: 500;
      color: var(--dim); text-decoration: none;
      transition: color .15s, background .15s;
    }}
    .n-link:hover {{ color: var(--text); background: var(--bg3); }}
    .n-gh {{
      display: flex; align-items: center; gap: 6px;
      padding: 5px 12px; border-radius: 6px;
      font-size: 0.82rem; font-weight: 600;
      color: var(--text); text-decoration: none;
      background: var(--bg3); border: 1px solid var(--bd2);
      transition: border-color .15s, color .15s;
    }}
    .n-gh:hover {{ border-color: var(--a); color: var(--a); }}
    .n-status {{
      display: flex; align-items: center; gap: 6px;
      font-size: 0.75rem; color: var(--a); font-weight: 600;
      padding: 0 8px;
    }}
    .pulse {{
      width: 7px; height: 7px; border-radius: 50%;
      background: var(--a); flex-shrink: 0;
      animation: pulse 2.4s ease infinite;
    }}
    @keyframes pulse {{
      0%,100% {{ box-shadow: 0 0 0 0 var(--aglow); }}
      50%      {{ box-shadow: 0 0 0 5px transparent; }}
    }}

    /* ─── HERO ────────────────────────────────────────── */
    .hero {{
      display: grid; grid-template-columns: 1fr 1fr;
      gap: 2.5rem; align-items: center;
      max-width: 1120px; margin: 0 auto;
      padding: 5.5rem 2rem 4rem;
      position: relative;
    }}
    .hero::after {{
      content: "";
      position: absolute; top: 10%; left: 20%;
      width: 600px; height: 500px;
      background: radial-gradient(ellipse at center, rgba(184,249,82,.05) 0%, transparent 65%);
      pointer-events: none; z-index: 0;
    }}
    .hero-l, .hero-r {{ position: relative; z-index: 1; }}
    .eyebrow {{
      display: inline-flex; align-items: center; gap: 8px;
      font-size: 0.7rem; font-weight: 700; letter-spacing: .13em;
      text-transform: uppercase; color: var(--a);
      margin-bottom: 1.4rem;
    }}
    .eyebrow::before {{
      content: ""; display: block;
      width: 24px; height: 1.5px; background: var(--a);
    }}
    h1 {{
      font-size: clamp(2.4rem, 4.5vw, 3.6rem);
      font-weight: 800; letter-spacing: -.045em; line-height: 1.06;
      margin-bottom: 1.4rem;
    }}
    h1 em {{ font-style: normal; color: var(--a); }}
    .hero-desc {{
      font-size: 1rem; color: var(--dim); line-height: 1.75;
      margin-bottom: 2rem; max-width: 420px;
    }}
    .ctas {{ display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 2.2rem; }}
    .btn {{
      display: inline-flex; align-items: center; gap: 7px;
      padding: 9px 18px; border-radius: 8px;
      font-size: 0.87rem; font-weight: 600;
      text-decoration: none; border: 1px solid transparent;
      transition: all .15s;
    }}
    .btn-solid {{ background: var(--a); color: #000; border-color: var(--a); }}
    .btn-solid:hover {{ background: var(--a2); border-color: var(--a2); }}
    .btn-out {{ background: transparent; color: var(--dim); border-color: var(--bd2); }}
    .btn-out:hover {{ color: var(--text); border-color: var(--bd2); background: var(--bg3); }}
    .base-url {{
      display: inline-flex; align-items: stretch;
      background: var(--bg2); border: 1px solid var(--bd);
      border-radius: 8px; overflow: hidden;
      font-family: var(--mono);
    }}
    .bu-tag {{
      padding: 9px 12px; font-size: 0.68rem; font-weight: 700;
      letter-spacing: .09em; text-transform: uppercase;
      color: var(--muted); background: var(--bg3);
      border-right: 1px solid var(--bd); white-space: nowrap;
      display: flex; align-items: center;
    }}
    .bu-val {{
      padding: 9px 14px; font-size: 0.82rem; color: var(--a);
      display: flex; align-items: center;
    }}

    /* ─── TERMINAL ────────────────────────────────────── */
    .term {{
      background: #0d1117;
      border: 1px solid var(--bd);
      border-radius: 12px; overflow: hidden;
      box-shadow: 0 28px 64px rgba(0,0,0,.55), 0 0 0 1px rgba(255,255,255,.03);
    }}
    .term-bar {{
      display: flex; align-items: center; justify-content: space-between;
      padding: 9px 14px; background: #161b22;
      border-bottom: 1px solid var(--bd);
    }}
    .dots {{ display: flex; gap: 6px; }}
    .dot {{ width: 11px; height: 11px; border-radius: 50%; }}
    .dr {{ background: #ff5f57; }}
    .dy {{ background: #febc2e; }}
    .dg {{ background: #28c840; }}
    .term-title {{ font-size: 0.73rem; color: var(--muted); font-family: var(--mono); }}
    .term-body {{
      padding: 1.3rem 1.5rem;
      font-family: var(--mono); font-size: 0.79rem; line-height: 1.85;
    }}
    .tk  {{ color: #ff7b72; }}
    .tf  {{ color: #d2a8ff; }}
    .ts  {{ color: #a5d6ff; }}
    .tc  {{ color: #3d4450; font-style: italic; }}
    .tn  {{ color: var(--ora); }}
    .ta  {{ color: var(--a); }}
    .cur {{
      display: inline-block; width: 8px; height: 13px;
      background: var(--a); vertical-align: text-bottom;
      animation: blink 1.1s step-end infinite;
    }}
    @keyframes blink {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0; }} }}

    /* ─── STATS ───────────────────────────────────────── */
    .stats-wrap {{ border-top: 1px solid var(--bd); border-bottom: 1px solid var(--bd); }}
    .stats {{
      display: grid; grid-template-columns: repeat(3,1fr);
      max-width: 1120px; margin: 0 auto;
    }}
    .stat {{
      padding: 2.8rem 2.5rem;
      border-right: 1px solid var(--bd);
    }}
    .stat:last-child {{ border-right: none; }}
    .stat-n {{
      font-size: 3.2rem; font-weight: 800;
      letter-spacing: -.06em; line-height: 1;
      margin-bottom: .35rem;
    }}
    .stat-n span {{ color: var(--a); }}
    .stat-l {{ font-size: 0.85rem; color: var(--dim); }}

    /* ─── CONTAINER ───────────────────────────────────── */
    .wrap {{ max-width: 1120px; margin: 0 auto; padding: 0 2rem; }}

    /* ─── SECTION CHROME ──────────────────────────────── */
    .sec {{ padding: 5rem 0; }}
    .sec-hd {{ margin-bottom: 2.8rem; }}
    .sec-eye {{
      font-family: var(--mono);
      font-size: 0.68rem; font-weight: 700;
      letter-spacing: .12em; text-transform: uppercase;
      color: var(--muted); margin-bottom: .7rem;
      display: flex; align-items: center; gap: 10px;
    }}
    .sec-eye::after {{
      content: ""; height: 1px; background: var(--bd);
      width: 48px; display: block;
    }}
    h2 {{
      font-size: clamp(1.5rem,2.8vw,2rem);
      font-weight: 700; letter-spacing: -.03em; line-height: 1.2;
      margin-bottom: .5rem;
    }}
    .sec-sub {{ font-size: 0.93rem; color: var(--dim); max-width: 540px; }}

    /* ─── FEATURE LIST ────────────────────────────────── */
    .feat-list {{ display: flex; flex-direction: column; }}
    .feat {{
      display: grid;
      grid-template-columns: 52px minmax(0,1.1fr) minmax(0,1.6fr);
      gap: 2rem;
      padding: 1.75rem 1rem;
      margin: 0 -1rem;
      border-top: 1px solid var(--bd);
      border-radius: 8px;
      transition: background .18s;
    }}
    .feat:last-child {{ border-bottom: 1px solid var(--bd); }}
    .feat:hover {{ background: var(--adim); }}
    .feat-i {{
      font-family: var(--mono); font-size: 0.68rem;
      color: var(--muted); padding-top: 3px;
    }}
    .feat-name {{
      font-size: 0.97rem; font-weight: 600;
      margin-bottom: .45rem; color: var(--text);
    }}
    .feat-tags {{ display: flex; gap: 6px; flex-wrap: wrap; }}
    .ftag {{
      font-size: 0.68rem; padding: 2px 7px; border-radius: 4px;
      background: var(--bg3); border: 1px solid var(--bd);
      color: var(--muted); font-family: var(--mono);
    }}
    .feat-desc {{
      font-size: 0.87rem; color: var(--dim); line-height: 1.65;
      padding-top: 3px;
    }}
    .ic {{ font-family: var(--mono); font-size: .82rem; color: var(--a); }}

    /* ─── CODE BLOCK ──────────────────────────────────── */
    .code-wrap {{
      background: #0d1117; border: 1px solid var(--bd);
      border-radius: 12px; overflow: hidden;
    }}
    .code-hd {{
      display: flex; align-items: center; justify-content: space-between;
      padding: 9px 14px; background: #161b22;
      border-bottom: 1px solid var(--bd);
    }}
    .code-hd-l {{ display: flex; align-items: center; gap: 10px; }}
    .code-fname {{ font-size: 0.73rem; color: var(--muted); font-family: var(--mono); }}
    .code-badge {{
      font-size: 0.66rem; padding: 2px 8px; border-radius: 4px;
      background: var(--adim); color: var(--a);
      border: 1px solid rgba(184,249,82,.2); font-family: var(--mono); font-weight: 700;
    }}
    pre {{
      padding: 1.4rem 1.6rem; overflow-x: auto; margin: 0;
      font-family: var(--mono); font-size: 0.8rem; line-height: 1.78;
    }}

    /* ─── TABS + TABLE ────────────────────────────────── */
    .tabs {{
      display: flex; gap: 0;
      border-bottom: 1px solid var(--bd); margin-bottom: 1.4rem;
    }}
    .tab {{
      padding: 8px 18px;
      font-size: 0.84rem; font-weight: 500; cursor: pointer;
      background: none; border: none; color: var(--dim);
      border-bottom: 2px solid transparent; margin-bottom: -1px;
      transition: color .15s, border-color .15s;
    }}
    .tab.on {{ color: var(--text); border-bottom-color: var(--a); }}
    .tp {{ display: none; }}
    .tp.on {{ display: block; }}
    table {{
      width: 100%; border-collapse: collapse;
      background: var(--bg2); border: 1px solid var(--bd);
      border-radius: 10px; overflow: hidden;
    }}
    thead {{ background: var(--bg3); }}
    th {{
      padding: 10px 16px; text-align: left;
      font-size: 0.69rem; font-weight: 700;
      letter-spacing: .09em; text-transform: uppercase; color: var(--muted);
    }}
    td {{
      padding: 10px 16px; font-size: 0.83rem;
      border-top: 1px solid var(--bd);
    }}
    td:first-child {{ font-family: var(--mono); color: var(--a); font-size: 0.78rem; }}
    td:last-child {{ color: var(--dim); }}
    tr:hover td {{ background: rgba(255,255,255,.018); }}
    .env-t td:first-child {{ color: var(--ora); }}
    .env-t td:nth-child(2) {{ color: var(--blue); font-family: var(--mono); font-size: 0.76rem; }}

    /* ─── FOOTER ──────────────────────────────────────── */
    .foot-wrap {{ border-top: 1px solid var(--bd); }}
    footer {{
      max-width: 1120px; margin: 0 auto;
      display: flex; align-items: center; justify-content: space-between;
      flex-wrap: wrap; gap: 1rem;
      padding: 2rem 2rem;
    }}
    .foot-brand {{
      display: flex; align-items: center; gap: 8px;
      font-size: 0.85rem; font-weight: 600; color: var(--dim);
    }}
    .foot-links {{ display: flex; gap: 1.4rem; }}
    .foot-links a {{
      font-size: 0.8rem; color: var(--muted);
      text-decoration: none; transition: color .15s;
    }}
    .foot-links a:hover {{ color: var(--text); }}

    /* ─── RESPONSIVE ──────────────────────────────────── */
    @media (max-width: 800px) {{
      .hero {{ grid-template-columns: 1fr; padding: 3rem 1.5rem; gap: 2rem; }}
      .hero-r {{ display: none; }}
      .stats {{ grid-template-columns: 1fr; }}
      .stat {{ border-right: none; border-bottom: 1px solid var(--bd); padding: 1.8rem 1.5rem; }}
      .stat:last-child {{ border-bottom: none; }}
      .feat {{ grid-template-columns: 44px 1fr; }}
      .feat-desc {{ display: none; }}
      nav {{ padding: 0 1rem; }}
    }}
  </style>
</head>
<body>

<!-- ── NAV ─────────────────────────────────────── -->
<nav>
  <div class="n-left">
    <a href="/" class="logo">
      <div class="logo-mark">R</div>
      replicate-openai
    </a>
    <span class="n-ver">v1.0.0</span>
  </div>
  <div class="n-right">
    <div class="n-status"><div class="pulse"></div>Running</div>
    <a href="/docs" class="n-link">Docs</a>
    <a href="/redoc" class="n-link">ReDoc</a>
    <a href="/v1/models" class="n-link">Models</a>
    <a href="{GH}" target="_blank" class="n-gh">{GH_ICON}&nbsp;GitHub</a>
  </div>
</nav>

<!-- ── HERO ─────────────────────────────────────── -->
<div class="hero">
  <div class="hero-l">
    <div class="eyebrow">OpenAI-Compatible Gateway</div>
    <h1>Run Replicate<br>models via <em>OpenAI</em><br>SDK.</h1>
    <p class="hero-desc">
      Drop-in compatible with any OpenAI SDK client.
      Swap one URL, get access to every model on Replicate —
      thousands of text, image, audio, and video models — zero code changes.
    </p>
    <div class="ctas">
      <a href="/docs" class="btn btn-solid">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
        </svg>
        API Docs
      </a>
      <a href="{GH}" target="_blank" class="btn btn-out">{GH_ICON} View Source</a>
    </div>
    <div class="base-url">
      <span class="bu-tag">base_url</span>
      <span class="bu-val">{base_url}</span>
    </div>
  </div>

  <div class="hero-r">
    <div class="term">
      <div class="term-bar">
        <div class="dots">
          <div class="dot dr"></div>
          <div class="dot dy"></div>
          <div class="dot dg"></div>
        </div>
        <span class="term-title">quickstart.py</span>
        <span style="width:56px"></span>
      </div>
      <div class="term-body">
<span class="tk">from</span> openai <span class="tk">import</span> OpenAI<br>
<br>
client = OpenAI(<br>
&nbsp;&nbsp;&nbsp;&nbsp;base_url=<span class="ts">"{base_url}"</span>,<br>
&nbsp;&nbsp;&nbsp;&nbsp;api_key=<span class="ts">"not-used"</span>,<br>
)<br>
<br>
<span class="tc"># Chat</span><br>
r = client.chat.completions.<span class="tf">create</span>(<br>
&nbsp;&nbsp;&nbsp;&nbsp;model=<span class="ts">"llama-3-70b-instruct"</span>,<br>
&nbsp;&nbsp;&nbsp;&nbsp;messages=[{{"role":<span class="ts">"user"</span>,"content":<span class="ts">"Hi!"</span>}}],<br>
)<br>
<br>
<span class="tc"># Image generation</span><br>
img = client.images.<span class="tf">generate</span>(<br>
&nbsp;&nbsp;&nbsp;&nbsp;model=<span class="ts">"flux-schnell"</span>,<br>
&nbsp;&nbsp;&nbsp;&nbsp;prompt=<span class="ts">"a sunset over mountains"</span>,<br>
)<br>
<span class="tf">print</span>(img.data[<span class="tn">0</span>].url)<span class="cur"></span>
      </div>
    </div>
  </div>
</div>

<!-- ── STATS ─────────────────────────────────────── -->
<div class="stats-wrap">
  <div class="stats">
    <div class="stat">
      <div class="stat-n">1000<span>+</span></div>
      <div class="stat-l">Any Replicate model — text, image, audio, video</div>
    </div>
    <div class="stat">
      <div class="stat-n">9<span>+</span></div>
      <div class="stat-l">Built-in short aliases for popular models</div>
    </div>
    <div class="stat">
      <div class="stat-n">100<span>%</span></div>
      <div class="stat-l">OpenAI API compatible</div>
    </div>
  </div>
</div>

<!-- ── FEATURES ──────────────────────────────────── -->
<div class="sec">
  <div class="wrap">
    <div class="sec-hd">
      <div class="sec-eye">01 — Features</div>
      <h2>Everything you need,<br>nothing you don't.</h2>
      <p class="sec-sub">Built on FastAPI. No bloat, no lock-in, no surprises.</p>
    </div>
    <div class="feat-list">

      <div class="feat">
        <span class="feat-i">01</span>
        <div>
          <div class="feat-name">OpenAI-Compatible Surface</div>
          <div class="feat-tags">
            <span class="ftag">/v1/chat/completions</span>
            <span class="ftag">/v1/models</span>
            <span class="ftag">/v1/images/generations</span>
            <span class="ftag">/v1/completions</span>
          </div>
        </div>
        <div class="feat-desc">
          Implements the full OpenAI REST surface. Works with any OpenAI SDK — Python, Node, Go, Rust — no modifications needed.
        </div>
      </div>

      <div class="feat">
        <span class="feat-i">02</span>
        <div>
          <div class="feat-name">Real-time Streaming</div>
          <div class="feat-tags">
            <span class="ftag">stream: true</span>
            <span class="ftag">server-sent events</span>
          </div>
        </div>
        <div class="feat-desc">
          Full SSE streaming support. Tokens appear in real time as Replicate generates them, identical to the OpenAI streaming protocol.
        </div>
      </div>

      <div class="feat">
        <span class="feat-i">03</span>
        <div>
          <div class="feat-name">Smart Model Routing</div>
          <div class="feat-tags">
            <span class="ftag">short aliases</span>
            <span class="ftag">owner/model IDs</span>
            <span class="ftag">live list (5 min)</span>
          </div>
        </div>
        <div class="feat-desc">
          Use <span class="ic">llama-3-70b-instruct</span>, pass any <span class="ic">owner/model</span> ID directly, or fetch the full live list via <span class="ic">/v1/models</span>.
        </div>
      </div>

      <div class="feat">
        <span class="feat-i">04</span>
        <div>
          <div class="feat-name">Image Generation</div>
          <div class="feat-tags">
            <span class="ftag">FLUX</span>
            <span class="ftag">Stable Diffusion</span>
            <span class="ftag">Imagen 3/4</span>
            <span class="ftag">Ideogram</span>
          </div>
        </div>
        <div class="feat-desc">
          Generate images via the standard <span class="ic">/v1/images/generations</span> endpoint with FLUX Schnell, SDXL, Imagen 4, and more.
        </div>
      </div>

      <div class="feat">
        <span class="feat-i">05</span>
        <div>
          <div class="feat-name">BYOK Mode</div>
          <div class="feat-tags">
            <span class="ftag">AUTH_MODE=true</span>
            <span class="ftag">Bearer token</span>
          </div>
        </div>
        <div class="feat-desc">
          Bring-your-own-key mode lets each client pass their own Replicate token as <span class="ic">Authorization: Bearer</span>. Good for multi-user setups.
        </div>
      </div>

      <div class="feat">
        <span class="feat-i">06</span>
        <div>
          <div class="feat-name">Docker Ready</div>
          <div class="feat-tags">
            <span class="ftag">Dockerfile</span>
            <span class="ftag">--env-file</span>
          </div>
        </div>
        <div class="feat-desc">
          Ships with a <span class="ic">Dockerfile</span>. <span class="ic">docker build &amp;&amp; docker run --env-file .env</span> and you're live.
        </div>
      </div>

    </div>
  </div>
</div>

<!-- ── QUICKSTART ─────────────────────────────────── -->
<div class="sec" style="padding-top:0">
  <div class="wrap">
    <div class="sec-hd">
      <div class="sec-eye">02 — Quickstart</div>
      <h2>One line to switch.</h2>
      <p class="sec-sub">From OpenAI to Replicate in under a minute.</p>
    </div>
    <div class="code-wrap">
      <div class="code-hd">
        <div class="code-hd-l">
          <div class="dots">
            <div class="dot dr"></div>
            <div class="dot dy"></div>
            <div class="dot dg"></div>
          </div>
          <span class="code-fname">example.py</span>
        </div>
        <span class="code-badge">python</span>
      </div>
      <pre><span class="tk">from</span> openai <span class="tk">import</span> OpenAI

<span class="tc"># ← Change this one line</span>
client = OpenAI(
    base_url=<span class="ts">"{base_url}"</span>,
    api_key=<span class="ts">"not-used"</span>,
)

<span class="tc"># ── Chat ──────────────────────────────────────────────────</span>
response = client.chat.completions.<span class="tf">create</span>(
    model=<span class="ts">"llama-3-70b-instruct"</span>,
    messages=[{{"role": <span class="ts">"user"</span>, "content": <span class="ts">"Hello!"</span>}}],
)
<span class="tf">print</span>(response.choices[<span class="tn">0</span>].message.content)

<span class="tc"># ── Streaming ─────────────────────────────────────────────</span>
<span class="tk">with</span> client.chat.completions.<span class="tf">stream</span>(
    model=<span class="ts">"mistral-7b-instruct"</span>,
    messages=[{{"role": <span class="ts">"user"</span>, "content": <span class="ts">"Write a haiku."</span>}}],
) <span class="tk">as</span> stream:
    <span class="tk">for</span> text <span class="tk">in</span> stream.text_stream:
        <span class="tf">print</span>(text, end=<span class="ts">""</span>, flush=<span class="tk">True</span>)

<span class="tc"># ── Image generation ──────────────────────────────────────</span>
img = client.images.<span class="tf">generate</span>(
    model=<span class="ts">"flux-schnell"</span>,
    prompt=<span class="ts">"cinematic sunset over mountains"</span>,
)
<span class="tf">print</span>(img.data[<span class="tn">0</span>].url)</pre>
    </div>
  </div>
</div>

<!-- ── MODELS ─────────────────────────────────────── -->
<div class="sec">
  <div class="wrap">
    <div class="sec-hd">
      <div class="sec-eye">03 — Models</div>
      <h2>Pre-configured aliases.</h2>
      <p class="sec-sub">
        Short aliases for common models, or pass <span class="ic">owner/model</span> to use
        <em>any</em> of the thousands of models on Replicate directly.&nbsp;
        <a href="/v1/models" style="color:var(--a);text-decoration:none;font-style:normal">Browse live list →</a>
      </p>
    </div>
    <div class="tabs">
      <button class="tab on" onclick="tab(event,'chat')">Chat &amp; Text</button>
      <button class="tab" onclick="tab(event,'image')">Image Generation</button>
    </div>
    <div id="chat" class="tp on">
      <table>
        <thead><tr><th>Alias</th><th>Replicate Model</th></tr></thead>
        <tbody>
          <tr><td>llama-3-8b-instruct</td><td>meta/meta-llama-3-8b-instruct</td></tr>
          <tr><td>llama-3-70b-instruct</td><td>meta/meta-llama-3-70b-instruct</td></tr>
          <tr><td>llama-3.1-8b-instruct</td><td>meta/meta-llama-3.1-8b-instruct</td></tr>
          <tr><td>llama-3.1-70b-instruct</td><td>meta/meta-llama-3.1-70b-instruct</td></tr>
          <tr><td>llama-3.1-405b-instruct</td><td>meta/meta-llama-3.1-405b-instruct</td></tr>
          <tr><td>mistral-7b-instruct</td><td>mistralai/mistral-7b-instruct-v0.2</td></tr>
          <tr><td>mixtral-8x7b-instruct</td><td>mistralai/mixtral-8x7b-instruct-v0.1</td></tr>
          <tr><td>deepseek-r1</td><td>deepseek-ai/deepseek-r1</td></tr>
          <tr><td>qwen2.5-72b-instruct</td><td>qwen/qwen2.5-72b-instruct</td></tr>
        </tbody>
      </table>
    </div>
    <div id="image" class="tp">
      <table>
        <thead><tr><th>Alias</th><th>Replicate Model</th></tr></thead>
        <tbody>
          <tr><td>flux-schnell</td><td>black-forest-labs/flux-schnell</td></tr>
          <tr><td>flux-dev</td><td>black-forest-labs/flux-dev</td></tr>
          <tr><td>flux-pro</td><td>black-forest-labs/flux-1.1-pro</td></tr>
          <tr><td>flux-2-pro</td><td>black-forest-labs/flux-2-pro</td></tr>
          <tr><td>imagen-3</td><td>google/imagen-3</td></tr>
          <tr><td>imagen-4</td><td>google/imagen-4</td></tr>
          <tr><td>ideogram-v3</td><td>ideogram-ai/ideogram-v3-balanced</td></tr>
          <tr><td>stable-diffusion-3</td><td>stability-ai/stable-diffusion-3</td></tr>
          <tr><td>sdxl</td><td>stability-ai/sdxl</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</div>

<!-- ── CONFIG ─────────────────────────────────────── -->
<div class="sec" style="padding-top:0">
  <div class="wrap">
    <div class="sec-hd">
      <div class="sec-eye">04 — Configuration</div>
      <h2>Environment variables.</h2>
      <p class="sec-sub">Copy <span class="ic">.env.example</span> → <span class="ic">.env</span> and set your token.</p>
    </div>
    <table class="env-t">
      <thead><tr><th>Variable</th><th>Default</th><th>Description</th></tr></thead>
      <tbody>
        <tr><td>REPLICATE_API_TOKEN</td><td>required</td><td>Your Replicate API token — replicate.com/account/api-tokens</td></tr>
        <tr><td>AUTH_MODE</td><td>false</td><td>Set true for BYOK mode — clients pass their own token as Bearer</td></tr>
        <tr><td>HOST</td><td>0.0.0.0</td><td>Server bind address</td></tr>
        <tr><td>PORT</td><td>8000</td><td>Listen port</td></tr>
      </tbody>
    </table>
  </div>
</div>

<!-- ── FOOTER ─────────────────────────────────────── -->
<div class="foot-wrap">
  <footer>
    <div class="foot-brand">
      <div class="logo-mark" style="width:20px;height:20px;font-size:.7rem">R</div>
      CookieShualon / replicate-openai
    </div>
    <div class="foot-links">
      <a href="{GH}" target="_blank">GitHub</a>
      <a href="/docs">Swagger UI</a>
      <a href="/redoc">ReDoc</a>
      <a href="https://replicate.com" target="_blank">Replicate</a>
      <a href="https://fastapi.tiangolo.com" target="_blank">FastAPI</a>
    </div>
  </footer>
</div>

<script>
  function tab(e, id) {{
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('on'));
    document.querySelectorAll('.tp').forEach(p => p.classList.remove('on'));
    e.target.classList.add('on');
    document.getElementById(id).classList.add('on');
  }}
</script>

</body>
</html>"""
    return HTMLResponse(content=html)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logger.info("Starting Replicate OpenAI Gateway on %s:%s", HOST, PORT)
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=False,
        log_level="info",
    )
