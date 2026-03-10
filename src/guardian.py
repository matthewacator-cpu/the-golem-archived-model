"""
guardian.py — Vision Guardian (Phase 1)

Every 1 Hz pulse: capture screen → ask moondream to rate doomscroll risk →
intervene if the organism has enough energy *and* the risk is above threshold.

Dependencies (install once):
    pip install mss pillow pyyaml ollama

Vision model (install once):
    ollama pull moondream

Falls back gracefully to silent no-op when:
  - screenshot deps are missing
  - ollama / moondream aren't running
  - energy or coherence is below configured thresholds
"""

import asyncio
import base64
import json
import time
from io import BytesIO
from pathlib import Path

# ── optional imports (fail gracefully) ───────────────────────────────────────
try:
    import mss
    from PIL import Image
    _SCREENSHOT_OK = True
except ImportError:
    _SCREENSHOT_OK = False

try:
    import ollama as _ollama
    _OLLAMA_OK = True
except ImportError:
    _OLLAMA_OK = False

try:
    import yaml
    _YAML_OK = True
except ImportError:
    _YAML_OK = False


# ─────────────────────────────────────────────────────────────────────────────
_BASE = Path(__file__).parent.parent          # project root
_DEFAULT_CONFIG_PATH = _BASE / "src" / "config.yaml"

_DEFAULT_CFG = {
    "paths": {
        "state_file": "/mnt/c/Users/matth/OneDrive/Desktop/system/vessel_state.json",
    },
    "models": {"vision": "moondream"},
    "metabolism": {
        "energy_threshold_low": 15,
        "coherence_threshold": 0.45,
        "doomscroll_risk_threshold": 70,
    },
    "guardian": {
        "enabled": True,
        "screenshot_enabled": True,
        "screenshot_scale": [640, 360],
        "intervention_cooldown_secs": 900,
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Merge override into base, recursively for nested dicts."""
    result = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def _load_config(config_path=None) -> dict:
    path = Path(config_path) if config_path else _DEFAULT_CONFIG_PATH
    if _YAML_OK and path.exists():
        try:
            loaded = yaml.safe_load(path.read_text()) or {}
            return _deep_merge(_DEFAULT_CFG, loaded)
        except Exception:
            pass
    return dict(_DEFAULT_CFG)


# ─────────────────────────────────────────────────────────────────────────────
class Guardian:
    """
    Vision-based attention guardian.

    Usage in life.py:
        guardian = Guardian()
        # inside the 1 Hz async block:
        asyncio.create_task(guardian.pulse())
    """

    def __init__(self, config_path=None):
        self._cfg = _load_config(config_path)
        self._g_cfg = self._cfg["guardian"]
        self._m_cfg = self._cfg["metabolism"]
        self._state_file = self._cfg["paths"]["state_file"]
        self._vision_model = self._cfg["models"]["vision"]
        self._last_intervention: float = 0.0
        self._available = _SCREENSHOT_OK and _OLLAMA_OK

        if not _SCREENSHOT_OK:
            print("[Guardian] mss/Pillow not found — screenshot vision disabled. "
                  "Run: pip install mss pillow")
        if not _OLLAMA_OK:
            print("[Guardian] ollama package not found — vision disabled. "
                  "Run: pip install ollama")

    # ── public ───────────────────────────────────────────────────────────────

    async def pulse(self) -> None:
        """Main 1 Hz hook.  Call with asyncio.create_task(guardian.pulse())."""
        if not self._g_cfg.get("enabled", True):
            return
        if not self._available:
            return
        if not self._g_cfg.get("screenshot_enabled", True):
            return

        state = self._load_state()
        if state["energy"] < self._m_cfg["energy_threshold_low"]:
            return
        if state["coherence"] < self._m_cfg["coherence_threshold"]:
            return

        b64 = self._capture_screen()
        if b64 is None:
            return

        risk, description = await self._analyze_screen(b64)

        if risk > self._m_cfg["doomscroll_risk_threshold"]:
            await self._intervene(risk, description, state)

    # ── private helpers ───────────────────────────────────────────────────────

    def _load_state(self) -> dict:
        defaults = {"energy": 100.0, "coherence": 0.5, "dopamine": 0.5}
        try:
            with open(self._state_file) as f:
                s = json.load(f)
            for k, v in defaults.items():
                s.setdefault(k, v)
            return s
        except Exception:
            return defaults

    def _capture_screen(self):
        """Grab primary monitor, resize, return base-64 PNG string or None."""
        try:
            scale = self._g_cfg.get("screenshot_scale", [640, 360])
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                raw = sct.grab(monitor)
                img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
                img = img.resize((scale[0], scale[1]))
                buf = BytesIO()
                img.save(buf, format="PNG")
                return base64.b64encode(buf.getvalue()).decode()
        except Exception as exc:
            print(f"[Guardian] Screenshot failed: {exc}")
            return None

    async def _analyze_screen(self, b64_image: str):
        """Ask the vision model to rate doomscroll risk. Returns (risk_int, desc_str)."""
        prompt = (
            "You are The Golem's Guardian Eyes.\n"
            "Look at this screenshot and respond in EXACTLY this format (no extra text):\n"
            "DOOM_RISK: <integer 0-100>\n"
            "DESCRIPTION: <one short sentence describing what the human is viewing>\n\n"
            "DOOM_RISK should be HIGH (70-100) for social media feeds, short-form video, "
            "news doom-loops, or idle browsing. LOW (0-30) for coding, writing, reading "
            "documents, or productive work."
        )
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: _ollama.chat(
                    model=self._vision_model,
                    messages=[{
                        "role": "user",
                        "content": prompt,
                        "images": [b64_image],
                    }],
                ),
            )
            text = response["message"]["content"].strip()
            risk = 50
            description = "Unknown content"
            for line in text.splitlines():
                if "DOOM_RISK:" in line:
                    try:
                        risk = max(0, min(100, int(line.split(":", 1)[-1].strip())))
                    except ValueError:
                        pass
                if "DESCRIPTION:" in line:
                    description = line.split(":", 1)[-1].strip()
            return risk, description
        except Exception as exc:
            # Moondream not running, model not pulled, etc. — stay silent.
            return 40, f"(vision unavailable: {exc})"

    async def _intervene(self, risk: int, description: str, state: dict) -> None:
        now = time.time()
        cooldown = self._g_cfg.get("intervention_cooldown_secs", 900)
        if now - self._last_intervention < cooldown:
            return
        self._last_intervention = now

        energy = state["energy"]
        bar = "█" * int(energy / 10) + "░" * (10 - int(energy / 10))
        print(
            f"\n┌─ GUARDIAN ────────────────────────────────────────────────\n"
            f"│  Seeing:      {description}\n"
            f"│  Doom risk:   {risk}/100\n"
            f"│  Energy:      [{bar}] {energy:.0f}%\n"
            f"│  Suggestion:  Close it. Return to the work.\n"
            f"└───────────────────────────────────────────────────────────\n"
        )
