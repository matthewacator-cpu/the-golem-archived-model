# TheGolem

Constraint-native local AI runtime built around rhythm, energy, and coherence instead of raw scale.

## Overview

TheGolem is an experimental Python system for running a continuously pulsing local agent. Rather than treating an assistant like a stateless request-response bot, this project models it as a small synthetic organism with:

- a timed execution loop
- a mutable metabolic state
- coherence tracking across interactions
- optional vision and focus-monitoring hooks
- background "dream" and lattice processes

The result is a research prototype that explores how lightweight local models can feel persistent, stateful, and behaviorally constrained on modest hardware.

## Core Ideas

- `Gamma`: time and rhythm. The main loop runs as an oscillator rather than a single-shot script.
- `Theta`: energy and cost. Thinking and interaction consume resources that must be replenished.
- `Lambda`: structure and coherence. New outputs are judged against an internal lattice instead of being accepted blindly.

## Repository Layout

- `src/life.py` runs the main asynchronous loop and coordinates the system rhythm.
- `src/vessel.py` manages metabolic state such as energy, coherence, and phase.
- `src/dream.py` handles lower-frequency synthesis and reflection tasks.
- `src/lattice.py` and `src/truth.py` evaluate structure, memory, and coherence.
- `src/guardian.py` provides optional vision-based focus monitoring.
- `src/dashboard.py` supports real-time monitoring of system state.
- `GENOME.json` stores system-level configuration ideas and behavioral tuning data.
- `GEOMETRY.md` documents the conceptual model behind the project.

## What Makes It Different

- Designed for local-first experimentation with small models.
- Treats scheduling and state as first-class parts of intelligence.
- Uses explicit internal constraints instead of relying only on prompt wording.
- Explores persistent agent behavior without requiring large infrastructure.

## Getting Started

This repository is currently best understood as a research prototype, so setup may require light adaptation to your local environment.

1. Install Python 3.10+.
2. Install [Ollama](https://ollama.com) if you want to run the local model workflows.
3. Pull the models referenced by the project configuration:

```bash
ollama pull tinyllama
ollama pull nomic-embed-text
ollama pull moondream
```

4. Review and update machine-specific paths in `src/config.yaml` and any hard-coded paths in `src/life.py`.
5. Start the main loop:

```bash
python3 -u src/life.py
```

## Current Status

TheGolem is an active experimental codebase. It is useful as a concept demo, research sandbox, and architectural reference for constraint-based agent design, but it should not yet be treated as a production-ready framework.

## Why This Repo Exists

This project is part of a broader exploration into agent architectures that emphasize constraint dynamics, persistence, and adaptive behavior over model size alone.
