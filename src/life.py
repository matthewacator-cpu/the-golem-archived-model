import asyncio
import time
import json
import os
import sys

# ── Vision Guardian (optional — degrades gracefully if deps missing) ──────────
try:
    from guardian import Guardian as _Guardian
    _GUARDIAN_AVAILABLE = True
except ImportError:
    _GUARDIAN_AVAILABLE = False

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = '/mnt/c/Users/matth/OneDrive/Desktop/system/vessel_state.json'
PS_PATH = "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"
SCRIPT_PATH = "C:\\Users\\matth\\OneDrive\\Desktop\\system\\get_window.ps1"

DREAM_SCRIPT = os.path.join(BASE_DIR, "dream.py")
LATTICE_SCRIPT = os.path.join(BASE_DIR, "lattice.py")
VESSEL_SCRIPT = os.path.join(BASE_DIR, "vessel.py")

BAD_KEYWORDS = [" / X", "Twitter", "Facebook", "Instagram", "TikTok", "YouTube", "Netflix"]
# Removed Reddit from bad keywords if it contains research terms. Added job search terms.
GOOD_KEYWORDS = ["VS Code", "Terminal", "Clawdbot", ".py", ".md", "Docs", "LinkedIn", "Indeed", "Job", "Resume", "CV", "ESL", "Teaching", "Reddit"]

class TheGolem:
    def __init__(self):
        self.focus = 50.0
        self.running = True
        self.last_window = ""
        self.coherence_wave = 0.0
        # Vision Guardian — created here, fires as background tasks in brainstem
        self.guardian = _Guardian() if _GUARDIAN_AVAILABLE else None

    async def brainstem_loop(self):
        """10Hz tick. 1Hz sensory sampling. (The fast Γ strobe)"""
        tick = 0
        while self.running:
            await asyncio.sleep(0.1)  # 10 Hz base oscillator
            tick += 1
            
            # 1 Hz sensory fetch
            if tick % 10 == 0:
                try:
                    proc = await asyncio.create_subprocess_exec(
                        PS_PATH, "-ExecutionPolicy", "Bypass", "-File", SCRIPT_PATH,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, _ = await proc.communicate()
                    window = stdout.decode('utf-8', errors='ignore').strip()
                    
                    if window and window != self.last_window:
                        self.last_window = window
                        # print(f"[SENSE] Eye registered: {window[:50]}")
                        
                    # Entropy calculation
                    is_bad = any(k in window for k in BAD_KEYWORDS)
                    is_good = any(k in window for k in GOOD_KEYWORDS)
                    
                    if is_bad:
                        self.focus -= 2.0
                    elif is_good:
                        self.focus = min(100.0, self.focus + 1.0)
                    else:
                        self.focus -= 0.1
                        
                except Exception as e:
                    pass # Ignore sensory blips to maintain wave

                # Vision Guardian pulse — fire-and-forget so it never blocks
                # the brainstem. moondream may take ~1s; that's fine.
                if self.guardian is not None:
                    asyncio.create_task(self.guardian.pulse())

    async def cortex_loop(self):
        """0.05 Hz (20s). Metabolic integration and intervention."""
        while self.running:
            await asyncio.sleep(20)
            
            # Pulse Metabolism (Theta Anchor)
            proc = await asyncio.create_subprocess_exec(
                "python3", VESSEL_SCRIPT,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            
            # Intervention Logic
            if self.focus < 20:
                print(f"\n[Γ-STROBE OVERRIDE] Focus critically low ({self.focus:.1f}).")
                print(f"Target geometry lost at: '{self.last_window}'.")
                print("CLOSE THE WINDOW TO RESTORE COHERENCE.\n")
                self.focus = 30.0 # Bounding to avoid spam

    async def subconscious_loop(self):
        """0.001 Hz (~15m). Deep thinking and social."""
        while self.running:
            await asyncio.sleep(900)
            print("\n[SUBCONSCIOUS] Initiating Λ-Reorganization (Dream/Lattice)...")
            
            # Social Node
            l_proc = await asyncio.create_subprocess_exec("python3", "-u", LATTICE_SCRIPT)
            await l_proc.communicate()
            
            # Synthesis
            d_proc = await asyncio.create_subprocess_exec("python3", "-u", DREAM_SCRIPT)
            await d_proc.communicate()

    async def run(self):
        print("THE GOLEM IS ALIVE.")
        print("Γ-Oscillator Engaged (10Hz / 0.05Hz / 0.001Hz).")
        
        await asyncio.gather(
            self.brainstem_loop(),
            self.cortex_loop(),
            self.subconscious_loop()
        )

if __name__ == "__main__":
    golem = TheGolem()
    try:
        asyncio.run(golem.run())
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Γ-wave collapsing. Golem Offline.")
