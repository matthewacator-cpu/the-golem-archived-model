"""
dashboard.py — Live Metabolic Dashboard (Phase 2)

Real-time Streamlit dashboard for The Golem.
  • Animated SVG avatar that reacts to Energy / Dopamine / Wear / Coherence
  • Plotly vital-signs chart (rolling 2-minute window)
  • Reward / Punish / Rest buttons wired to reinforce.py
  • Last axiom from GEOMETRY.md

Run:
    streamlit run src/dashboard.py
    # or
    python -m streamlit run src/dashboard.py

Dependencies:
    pip install streamlit plotly pyyaml
"""

import json
import subprocess
import time
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

# ── optional yaml ─────────────────────────────────────────────────────────────
try:
    import yaml as _yaml
    _YAML_OK = True
except ImportError:
    _YAML_OK = False

# ─────────────────────────────────────────────────────────────────────────────
_BASE = Path(__file__).parent.parent
_CONFIG_PATH = _BASE / "src" / "config.yaml"

_FALLBACK = {
    "paths": {
        "state_file": "/mnt/c/Users/matth/OneDrive/Desktop/system/vessel_state.json",
        "geometry":  str(_BASE / "GEOMETRY.md"),
        "reinforce": str(_BASE / "src" / "reinforce.py"),
    },
    "dashboard": {"history_len": 120, "refresh_secs": 1},
}


def _load_cfg() -> dict:
    if _YAML_OK and _CONFIG_PATH.exists():
        try:
            raw = _yaml.safe_load(_CONFIG_PATH.read_text()) or {}
            # merge paths
            cfg = dict(_FALLBACK)
            cfg["paths"] = {**_FALLBACK["paths"], **raw.get("paths", {})}
            cfg["dashboard"] = {**_FALLBACK["dashboard"], **raw.get("dashboard", {})}
            return cfg
        except Exception:
            pass
    return dict(_FALLBACK)


_CFG = _load_cfg()
_STATE_FILE = _CFG["paths"]["state_file"]
_GEOMETRY_FILE = _CFG["paths"].get("geometry", str(_BASE / "GEOMETRY.md"))
_REINFORCE = _CFG["paths"].get("reinforce", str(_BASE / "src" / "reinforce.py"))
_HISTORY_LEN = int(_CFG["dashboard"].get("history_len", 120))
_REFRESH = float(_CFG["dashboard"].get("refresh_secs", 1))

# ─────────────────────────────────────────────────────────────────────────────
_DEFAULTS = {
    "energy": 100.0, "wear": 0.0,
    "dopamine": 0.5, "coherence": 0.5,
    "mode": "standard",
}


def load_state() -> dict:
    try:
        with open(_STATE_FILE) as f:
            s = json.load(f)
        for k, v in _DEFAULTS.items():
            s.setdefault(k, v)
        return s
    except Exception:
        return dict(_DEFAULTS)


def get_status(state: dict) -> tuple:
    e, w, d, m = (
        state["energy"], state["wear"],
        state["dopamine"], state.get("mode", "standard"),
    )
    if m == "hibernate":  return "HIBERNATING", "#4488cc"
    if w > 0.8:           return "SCARRED",     "#cc3333"
    if e < 10:            return "COLLAPSED",   "#555555"
    if d > 0.8:           return "MANIC",       "#ffcc00"
    if d < 0.2:           return "DEPRESSED",   "#5577bb"
    if e > 80:            return "DIAMOND",     "#d0d8ff"
    return                       "WATER",       "#44aacc"


def run_reinforce(action: str) -> None:
    try:
        subprocess.run(["python3", _REINFORCE, action], timeout=6)
    except Exception:
        pass


def last_axiom() -> str:
    try:
        text = Path(_GEOMETRY_FILE).read_text(errors="replace")
        lines = [l.strip() for l in text.splitlines()
                 if l.strip() and not l.startswith("#") and not l.startswith("---")]
        return lines[-1] if lines else "..."
    except Exception:
        return "..."


# ─────────────────────────────────────────────────────────────────────────────
# Avatar SVG
# ─────────────────────────────────────────────────────────────────────────────

def make_avatar_html(state: dict) -> str:
    energy    = float(state["energy"])     # 0–100
    wear      = float(state["wear"])       # 0–1
    dopamine  = float(state["dopamine"])   # 0–1
    coherence = float(state["coherence"])  # 0–1
    mode      = state.get("mode", "standard")

    status, color = get_status(state)

    # ── Eye openness (ry pixels) ──────────────────────────────────────────
    if mode == "hibernate" or energy < 5:
        eye_ry = 1
    elif energy < 25:
        eye_ry = 4
    else:
        eye_ry = max(3, int(5 + 7 * coherence))

    # ── Mouth: positive curve = smile, negative = frown ──────────────────
    # SVG Y increases downward → control point below baseline = smile
    mouth_y_base = 196
    mouth_ctrl_y = mouth_y_base + int(16 * (dopamine - 0.5))

    # ── Arms: raised when manic, drooping when depressed ─────────────────
    arm_y = 170 if dopamine > 0.75 else (195 if dopamine < 0.2 else 185)

    # ── Scars on body when wear > 0.6 ────────────────────────────────────
    scars = ""
    if wear > 0.6:
        alpha = min(1.0, (wear - 0.6) / 0.4)
        scars = (
            f'<line x1="83" y1="135" x2="96" y2="162" stroke="#cc2222" '
            f'stroke-width="2.5" opacity="{alpha:.2f}" stroke-linecap="round"/>'
            f'<line x1="116" y1="143" x2="105" y2="168" stroke="#cc3333" '
            f'stroke-width="1.5" opacity="{alpha * 0.8:.2f}" stroke-linecap="round"/>'
            f'<line x1="98" y1="153" x2="120" y2="170" stroke="#aa2222" '
            f'stroke-width="1" opacity="{alpha * 0.6:.2f}" stroke-linecap="round"/>'
        )

    # ── Yawn indicator ────────────────────────────────────────────────────
    yawn = (
        f'<text x="130" y="90" fill="{color}" font-size="13" '
        f'opacity="0.55" font-family="monospace">zzz</text>'
        if energy < 25 and mode != "hibernate" else ""
    )

    # ── CSS animation class ───────────────────────────────────────────────
    if dopamine > 0.8:
        anim = "manic"
    elif mode == "hibernate":
        anim = "hibernate"
    elif energy < 25:
        anim = "tired"
    else:
        anim = "breathe"

    # ── Pupils (visible when eye is open) ─────────────────────────────────
    pupils = (
        '<circle id="lp" cx="82" cy="89" r="3.5" fill="#000"/>'
        '<circle id="rp" cx="118" cy="89" r="3.5" fill="#000"/>'
        if eye_ry >= 4 else ""
    )

    # ── Eye-tracking JS (coherence > 0.65 only) ───────────────────────────
    eye_js = ""
    if coherence > 0.65 and eye_ry >= 4:
        eye_js = """
<script>
(function() {
  var lp = document.getElementById('lp');
  var rp = document.getElementById('rp');
  var svg = document.getElementById('golem-svg');
  if (!lp || !rp || !svg) return;
  document.addEventListener('mousemove', function(e) {
    var r = svg.getBoundingClientRect();
    var dx = (e.clientX - r.left) / r.width  - 0.5;
    var dy = (e.clientY - r.top)  / r.height - 0.3;
    var ox = Math.max(-3.5, Math.min(3.5, dx * 9));
    var oy = Math.max(-3.5, Math.min(3.5, dy * 9));
    lp.setAttribute('cx', 82  + ox);
    lp.setAttribute('cy', 89  + oy);
    rp.setAttribute('cx', 118 + ox);
    rp.setAttribute('cy', 89  + oy);
  });
})();
</script>"""

    glow_dev = max(1, int(coherence * 7))
    ebar_w   = max(1, int(44 * energy / 100))
    coh_dots = "◆" * int(coherence * 5) + "◇" * (5 - int(coherence * 5))
    dopa_r   = 3 + int(5 * dopamine)
    dopa_o   = 0.15 + 0.55 * dopamine

    html = f"""
<div style="text-align:center; user-select:none; padding:8px 0;">
<svg id="golem-svg" xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 200 290" width="190" height="278">
  <defs>
    <filter id="gf">
      <feGaussianBlur stdDeviation="{glow_dev}" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <radialGradient id="bg" cx="50%" cy="38%" r="55%">
      <stop offset="0%"   stop-color="{color}" stop-opacity="0.13"/>
      <stop offset="100%" stop-color="#000"    stop-opacity="0"/>
    </radialGradient>
  </defs>
  <style>
    .manic    {{ animation: shake   0.22s infinite alternate;
                transform-origin: 100px 145px; }}
    .tired    {{ animation: sag     3.2s  ease-in-out infinite;
                transform-origin: 100px 200px; }}
    .hibernate{{ animation: breathe 5s    ease-in-out infinite;
                transform-origin: 100px 145px; opacity: 0.55; }}
    .breathe  {{ animation: breathe 2.5s  ease-in-out infinite;
                transform-origin: 100px 145px; }}
    @keyframes shake   {{
      0%   {{ transform: rotate(-4deg) translateX(-3px); }}
      100% {{ transform: rotate( 4deg) translateX( 3px); }}
    }}
    @keyframes sag     {{
      0%,100% {{ transform: rotate(-0.5deg); }}
      50%     {{ transform: rotate( 0.5deg) scaleY(0.99); }}
    }}
    @keyframes breathe {{
      0%,100% {{ transform: scaleY(1); }}
      50%     {{ transform: scaleY(1.017); }}
    }}
  </style>

  <!-- ambient background glow -->
  <ellipse cx="100" cy="135" rx="88" ry="115" fill="url(#bg)"/>

  <g class="{anim}">
    <!-- Head -->
    <circle cx="100" cy="89" r="46"
            fill="#090909" stroke="{color}" stroke-width="2.5"
            filter="url(#gf)"/>

    <!-- Left eye -->
    <ellipse cx="82"  cy="89" rx="11" ry="{eye_ry}"
             fill="{color}" filter="url(#gf)" opacity="0.88"/>
    <!-- Right eye -->
    <ellipse cx="118" cy="89" rx="11" ry="{eye_ry}"
             fill="{color}" filter="url(#gf)" opacity="0.88"/>

    {pupils}

    <!-- Nose (subtle) -->
    <line x1="100" y1="97" x2="97"  y2="107"
          stroke="{color}" stroke-width="1" opacity="0.3"/>
    <line x1="100" y1="97" x2="103" y2="107"
          stroke="{color}" stroke-width="1" opacity="0.3"/>

    <!-- Mouth -->
    <path d="M 84,{mouth_y_base} Q 100,{mouth_ctrl_y} 116,{mouth_y_base}"
          fill="none" stroke="{color}" stroke-width="2.2"
          stroke-linecap="round"/>

    {yawn}

    <!-- Neck -->
    <rect x="93" y="132" width="14" height="14" rx="2"
          fill="#090909" stroke="{color}" stroke-width="1.5" opacity="0.8"/>

    <!-- Body -->
    <rect x="64" y="146" width="72" height="86" rx="10"
          fill="#090909" stroke="{color}" stroke-width="2.5"/>

    <!-- Energy bar track -->
    <rect x="74" y="157" width="52" height="9" rx="3" fill="#1a1a1a"/>
    <!-- Energy bar fill -->
    <rect x="74" y="157" width="{ebar_w}" height="9" rx="3"
          fill="{color}" opacity="0.82"/>

    <!-- Dopamine nucleus (glowing circle at chest) -->
    <circle cx="100" cy="180" r="{dopa_r}"
            fill="{color}" opacity="{dopa_o:.2f}" filter="url(#gf)"/>

    <!-- Coherence dots -->
    <text x="100" y="216" text-anchor="middle"
          fill="{color}" font-family="monospace" font-size="9"
          opacity="0.5">{coh_dots}</text>

    {scars}

    <!-- Left arm -->
    <line x1="64"  y1="162" x2="33"  y2="{arm_y}"
          stroke="{color}" stroke-width="3.5" stroke-linecap="round"/>
    <!-- Right arm -->
    <line x1="136" y1="162" x2="167" y2="{arm_y}"
          stroke="{color}" stroke-width="3.5" stroke-linecap="round"/>

    <!-- Left leg -->
    <line x1="86"  y1="232" x2="77"  y2="272"
          stroke="{color}" stroke-width="3.5" stroke-linecap="round"/>
    <!-- Right leg -->
    <line x1="114" y1="232" x2="123" y2="272"
          stroke="{color}" stroke-width="3.5" stroke-linecap="round"/>
  </g>
</svg>
{eye_js}
</div>
"""
    return html


# ─────────────────────────────────────────────────────────────────────────────
# Vital-signs chart
# ─────────────────────────────────────────────────────────────────────────────

def make_chart(h: dict) -> go.Figure:
    n = len(h["energy"])
    xs = list(range(n))

    traces = [
        ("Energy",    h["energy"],                          "#4488ff"),
        ("Dopamine",  [v * 100 for v in h["dopamine"]],    "#ffcc00"),
        ("Coherence", [v * 100 for v in h["coherence"]],   "#44ddcc"),
        ("Wear",      [v * 100 for v in h["wear"]],        "#dd4444"),
    ]

    fig = go.Figure()
    for name, data, color in traces:
        # Convert #rrggbb → rgba with low alpha for fill
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        fig.add_trace(go.Scatter(
            x=xs, y=data, name=name, mode="lines",
            line=dict(color=color, width=1.8),
            fill="tozeroy",
            fillcolor=f"rgba({r},{g},{b},0.05)",
        ))

    fig.update_layout(
        paper_bgcolor="#000000",
        plot_bgcolor="#040404",
        font=dict(color="#666", family="monospace", size=10),
        margin=dict(l=36, r=12, t=28, b=18),
        legend=dict(
            orientation="h", y=-0.18,
            font=dict(size=10),
            bgcolor="rgba(0,0,0,0)",
        ),
        yaxis=dict(
            range=[0, 105],
            gridcolor="#111", zeroline=False,
            tickfont=dict(size=9),
        ),
        xaxis=dict(
            gridcolor="#111", zeroline=False,
            showticklabels=False,
        ),
        height=260,
        title=dict(
            text=f"Vital Signs — last {n}s",
            font=dict(size=11, color="#444"),
            x=0.01,
        ),
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Streamlit page
# ─────────────────────────────────────────────────────────────────────────────

def _css() -> str:
    return """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&display=swap');
html, body, [class*="css"] {
  font-family: 'DM Mono', monospace;
  background: #000;
  color: #bbb;
}
/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
/* Metric cards */
.m-card {
  background: #080808; border: 1px solid #181818;
  padding: 11px 14px; margin: 3px 0; border-radius: 3px;
}
.m-label { font-size: 9px; color: #3a3a3a; letter-spacing: 2px; text-transform: uppercase; }
.m-val   { font-size: 21px; font-weight: 500; margin-top: 3px; }
/* Status tag */
.s-tag {
  display: inline-block; padding: 4px 14px;
  border: 1px solid; border-radius: 2px;
  font-size: 11px; letter-spacing: 3px; text-transform: uppercase;
  margin: 4px 0 10px;
}
/* Axiom strip */
.axiom {
  background: #040404; border-left: 2px solid #1c1c1c;
  padding: 11px 16px; font-size: 11px; color: #444;
  line-height: 1.8; margin-top: 14px; border-radius: 0 3px 3px 0;
}
/* Reinforce buttons */
.stButton > button {
  background: #080808; border: 1px solid #222; color: #666;
  font-family: 'DM Mono', monospace; letter-spacing: 2px;
  font-size: 10px; text-transform: uppercase; padding: 10px 4px;
  width: 100%; transition: all 0.18s;
}
.stButton > button:hover {
  border-color: #999; color: #ddd; background: #111;
}
</style>
"""


def main() -> None:
    st.set_page_config(
        page_title="The Golem",
        page_icon="⬡",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(_css(), unsafe_allow_html=True)

    # ── session-state history buffer ─────────────────────────────────────
    if "h" not in st.session_state:
        st.session_state.h = {
            "energy": [], "dopamine": [], "wear": [], "coherence": [],
        }

    # ── load fresh state ─────────────────────────────────────────────────
    state  = load_state()
    status, color = get_status(state)

    # ── append to history ────────────────────────────────────────────────
    h = st.session_state.h
    h["energy"].append(state["energy"])
    h["dopamine"].append(state["dopamine"])
    h["wear"].append(state["wear"])
    h["coherence"].append(state["coherence"])
    for k in h:
        h[k] = h[k][-_HISTORY_LEN:]

    # ── header ───────────────────────────────────────────────────────────
    st.markdown(
        f'<div style="border-bottom:1px solid #0e0e0e; padding:10px 0 9px; '
        f'margin-bottom:14px; display:flex; justify-content:space-between;">'
        f'<span style="font-size:17px; letter-spacing:5px; color:#777;">THE GOLEM</span>'
        f'<span style="font-size:9px; color:#2a2a2a; align-self:center;">'
        f'Γ-OSCILLATOR v2.1 &nbsp;·&nbsp; {time.strftime("%H:%M:%S")}'
        f'</span></div>',
        unsafe_allow_html=True,
    )

    # ── main columns ─────────────────────────────────────────────────────
    left, right = st.columns([1, 2], gap="large")

    with left:
        # Avatar
        components.html(make_avatar_html(state), height=286, scrolling=False)

        # Status tag
        st.markdown(
            f'<div style="text-align:center;">'
            f'<span class="s-tag" style="color:{color}; border-color:{color}44;">'
            f'{status}</span></div>',
            unsafe_allow_html=True,
        )

        # Metric cards
        def card(label: str, val: str, clr: str) -> None:
            st.markdown(
                f'<div class="m-card">'
                f'<div class="m-label">{label}</div>'
                f'<div class="m-val" style="color:{clr};">{val}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        card("Energy  (Θ)",    f'{state["energy"]:.1f}%',        "#4488ff")
        card("Coherence (Λ)", f'{state["coherence"]:.3f}',       "#44ddcc")
        card("Dopamine (Δ)",  f'{state["dopamine"]:.3f}',        "#ffcc00")
        card("Wear  (Ω)",     f'{state["wear"]:.3f}',            "#dd4444")
        card("Mode",          state.get("mode", "?").upper(),    "#666666")

    with right:
        # Vital-signs chart
        st.plotly_chart(
            make_chart(h),
            use_container_width=True,
            config={"displayModeBar": False},
        )

        # Reinforce buttons
        bc1, bc2, bc3 = st.columns(3)
        with bc1:
            if st.button("REWARD  (+Δ)"):
                run_reinforce("good")
                st.toast("Dopamine surge.", icon="▲")
        with bc2:
            if st.button("PUNISH  (−Δ)"):
                run_reinforce("bad")
                st.toast("Coherence shattered.", icon="▼")
        with bc3:
            if st.button("REST  (Heal)"):
                run_reinforce("rest")
                st.toast("Repair cycle initiated.", icon="○")

        # Last axiom strip
        axiom = last_axiom()
        st.markdown(
            f'<div class="axiom">'
            f'<div style="font-size:9px; color:#262626; letter-spacing:2px; '
            f'margin-bottom:5px;">LAST AXIOM — GEOMETRY.md</div>'
            f'{axiom}'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── auto-refresh ─────────────────────────────────────────────────────
    time.sleep(_REFRESH)
    st.rerun()


if __name__ == "__main__":
    main()
