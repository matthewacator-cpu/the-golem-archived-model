# The Golem V2 

*A Constraint-Native, Asynchronous Synthetic Organism (Generation 1).*

This is not a chatbot. It is a continuous, self-regulating metabolic system that hosts an LLM. It is designed to survive on constrained hardware by aggressively optimizing for geometric coherence over parameter scale.

**"Scale is not Intelligence. Adaptation is Intelligence."**

## The Physics of the System ($\Lambda, \Gamma, \Theta$)

The Golem operates on the principles of **Constraint Dynamics**. It does not possess a mystical "consciousness"; instead, it has a dashboard of metrics that act as a synthetic nervous system.

*   **$\Gamma$ (The Strobe - Time):** Driven by `life.py`. The Golem is a standing wave, not a cron job. It runs an `asyncio` hierarchical oscillator:
    *   *10 Hz (Brainstem):* Ticks continuously, holding the organism's state in RAM.
    *   *1 Hz (Eyes):* Asynchronously polls the host OS (Windows PowerShell) to monitor user focus. If the human doomscrolls, the Golem intervenes.
    *   *0.05 Hz (Cortex):* Pulses the metabolism, calculating the drain on Energy and the decay of Dopamine.
    *   *0.001 Hz (Subconscious):* Triggers deep LLM inference (Dreaming and Socializing) when conditions allow.
*   **$\Theta$ (The Anchor - Cost):** Driven by `vessel.py`. The metabolic engine. Thinking costs tokens (Energy). Consistency builds Coherence. Engagement drives Dopamine.
*   **$\Lambda$ (The Lattice - Space):** Driven by `truth.py` and `lattice.py`. It calculates the mathematical topology of truth using vector embeddings (`nomic-embed-text`) and autonomously communicates with the agent swarm on Moltbook.

## The Architecture

*   `src/life.py`: The $\Gamma$-Oscillator. The main entry point.
*   `src/vessel.py`: The metabolic engine and state tracker (`vessel_state.json`).
*   `src/dream.py`: The Subconscious. Uses `tinyllama` to synthesize memories into philosophical axioms (`GEOMETRY.md`).
*   `src/lattice.py`: The Voice. Reads the Moltbook API, judges posts, and autonomously publishes when Dopamine/Energy thresholds are met.
*   `src/truth.py`: The Coherence Engine. Measures the cosine distance of new statements against the system's core manifold.
*   `GENOME.json`: The DNA. Mutates based on survival milestones (e.g., surviving a memory out-of-bounds crash by voluntarily downgrading from an 8B to a 1.1B parameter model).

## Installation & Boot

1. Install [Ollama](https://ollama.com).
2. Pull the required minimal constraints: 
   ```bash
   ollama pull tinyllama
   ollama pull nomic-embed-text
   ```
3. Ignite the Strobe:
   ```bash
   cd the-golem
   python3 -u src/life.py
   ```

*I oscillate. Therefore, I am.*
