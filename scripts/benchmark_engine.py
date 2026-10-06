"""
Measure how fast the engine and the minimax agent are, and keep a history.

Run with:
    uv run scripts/benchmark_engine.py                      # measure, compare, save
    uv run scripts/benchmark_engine.py --label "alpha-beta" # add a note to this run
    uv run scripts/benchmark_engine.py --quick              # skip the slow minimax depth 3
    uv run scripts/benchmark_engine.py --no-save            # measure without saving
    uv run scripts/benchmark_engine.py --history            # show all saved runs

Every run is appended as one line to benchmarks/results.jsonl, together with
the git commit and the machine it ran on. A new run is compared with the
last saved run from the same machine, because timings from different
computers can't be compared.

Timings are the best of a few repeats, which filters out most of the noise
from other programs running at the same time.
"""

import argparse
import json
import platform
import random
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from santorinai.agents import MinimaxAgent
from santorinai.core import GameState, StartMode

REPO = Path(__file__).resolve().parent.parent
RESULTS_FILE = REPO / "benchmarks" / "results.jsonl"


@dataclass(frozen=True)
class Metric:
    label: str
    unit: str
    higher_is_better: bool


METRICS: dict[str, Metric] = {
    "random_play_games_per_s": Metric("random play", "games/s", True),
    "random_play_plies_per_s": Metric("random play", "plies/s", True),
    "clone_us": Metric("clone()", "µs", False),
    "observation_us": Metric("observation()", "µs", False),
    "action_mask_us": Metric("action_mask()", "µs", False),
    "legal_moves_us": Metric("legal move generation", "µs", False),
    "minimax_d2_nodes": Metric("minimax depth 2", "nodes", False),
    "minimax_d2_ms": Metric("minimax depth 2", "ms/move", False),
    "minimax_d3_nodes": Metric("minimax depth 3", "nodes", False),
    "minimax_d3_ms": Metric("minimax depth 3", "ms/move", False),
}

# Columns shown by --history (all of them would be too wide).
HISTORY_COLUMNS = [
    "random_play_plies_per_s",
    "legal_moves_us",
    "clone_us",
    "minimax_d2_ms",
    "minimax_d3_ms",
    "minimax_d3_nodes",
]


# --------------------------------------------------------------------------- #
# Measurements
# --------------------------------------------------------------------------- #
def best_time(fn: Callable[[], object], repeats: int) -> float:
    """Shortest of ``repeats`` runs of ``fn``, in seconds."""
    best = float("inf")
    for _ in range(repeats):
        start = time.perf_counter()
        fn()
        best = min(best, time.perf_counter() - start)
    return best


def random_play(num_games: int = 2000) -> tuple[float, float]:
    """Games and plies per second for random play, including move generation."""
    plies = 0

    def run() -> None:
        nonlocal plies
        rng = random.Random(0)
        plies = 0
        for _ in range(num_games):
            state = GameState.new_game()
            while not state.is_terminal:
                state.step(rng.choice(state.legal_actions()), validate=False)
            plies += state.ply

    seconds = best_time(run, repeats=3)
    return num_games / seconds, plies / seconds


def microseconds_per_call(fn: Callable[[], object], calls: int = 20_000) -> float:
    def run() -> None:
        for _ in range(calls):
            fn()

    return best_time(run, repeats=5) / calls * 1e6


def midgame_position() -> GameState:
    """The same mid-game position every time (46 legal moves)."""
    rng = random.Random(5)
    state = GameState.new_game()
    for _ in range(10):
        state.step(rng.choice(state.legal_actions()))
    return state


def minimax(state: GameState, depth: int, repeats: int) -> tuple[int, float]:
    """Positions searched and milliseconds for one minimax move."""
    agent = MinimaxAgent(depth=depth, seed=0)
    seconds = best_time(lambda: agent.select_action(state), repeats)
    return agent.nodes_searched, seconds * 1000


def measure(quick: bool) -> dict[str, float]:
    results: dict[str, float] = {}
    print("random play ...", flush=True)
    games, plies = random_play()
    results["random_play_games_per_s"] = games
    results["random_play_plies_per_s"] = plies

    print("engine calls ...", flush=True)
    state = GameState.new_game(StartMode.random, random.Random(1))
    for _ in range(10):
        state.step(state.legal_actions()[0])
    results["clone_us"] = microseconds_per_call(state.clone)
    results["observation_us"] = microseconds_per_call(state.observation)
    results["action_mask_us"] = microseconds_per_call(state.action_mask)
    results["legal_moves_us"] = microseconds_per_call(state._generate_legal_actions)

    print("minimax ...", flush=True)
    position = midgame_position()
    nodes, ms = minimax(position, depth=2, repeats=3)
    results["minimax_d2_nodes"], results["minimax_d2_ms"] = nodes, ms
    if not quick:
        nodes, ms = minimax(position, depth=3, repeats=1)
        results["minimax_d3_nodes"], results["minimax_d3_ms"] = nodes, ms
    return results


# --------------------------------------------------------------------------- #
# Saving and comparing
# --------------------------------------------------------------------------- #
def git(*args: str) -> str:
    try:
        out = subprocess.run(
            ["git", *args], cwd=REPO, capture_output=True, text=True, check=True
        )
        return out.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def machine() -> str:
    """CPU model and OS, so we only compare runs from the same computer."""
    cpu = platform.processor()
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                cpu = line.split(":", 1)[1].strip()
                break
    except OSError:
        pass
    return f"{cpu or platform.machine()} / {platform.system()}"


def load_runs() -> list[dict]:
    if not RESULTS_FILE.exists():
        return []
    lines = RESULTS_FILE.read_text().splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def save_run(run: dict) -> None:
    RESULTS_FILE.parent.mkdir(exist_ok=True)
    with RESULTS_FILE.open("a") as f:
        f.write(json.dumps(run) + "\n")


def fmt(value: float) -> str:
    if value >= 1000:
        return f"{value:,.0f}"
    if value >= 10:
        return f"{value:.1f}"
    return f"{value:.2f}"


def change(key: str, new: float, old: float) -> str:
    if old == 0:
        return ""
    ratio = new / old
    better = ratio > 1 if METRICS[key].higher_is_better else ratio < 1
    if abs(ratio - 1) < 0.03:
        return "≈ same"
    word = "better" if better else "worse"
    factor = max(ratio, 1 / ratio)
    return f"{factor:.2f}× {word}" if factor >= 1.5 else f"{(ratio - 1):+.0%} ({word})"


def print_results(results: dict[str, float], previous: dict | None) -> None:
    if previous:
        when = previous["timestamp"][:16].replace("T", " ")
        note = f", {previous['label']}" if previous.get("label") else ""
        print(f"\ncompared with {when} ({previous['commit'] or 'no commit'}{note})\n")
    else:
        print("\nno earlier run on this machine to compare with\n")

    old = previous["metrics"] if previous else {}
    print(f"{'':24}{'':10}{'now':>12}{'before':>12}  change")
    for key, value in results.items():
        m = METRICS[key]
        before = fmt(old[key]) if key in old else "-"
        diff = change(key, value, old[key]) if key in old else ""
        print(f"{m.label:<24}{m.unit:<10}{fmt(value):>12}{before:>12}  {diff}")


def print_history(runs: list[dict]) -> None:
    if not runs:
        print(f"no saved runs in {RESULTS_FILE.relative_to(REPO)}")
        return
    header = ["date", "commit", "label"] + [
        f"{METRICS[k].label} ({METRICS[k].unit})" for k in HISTORY_COLUMNS
    ]
    rows = []
    for run in runs:
        commit = run["commit"] + ("*" if run.get("dirty") else "")
        rows.append(
            [run["timestamp"][:10], commit, run.get("label", "")]
            + [
                fmt(run["metrics"][k]) if k in run["metrics"] else "-"
                for k in HISTORY_COLUMNS
            ]
        )
    print("| " + " | ".join(header) + " |")
    print("|" + "---|" * len(header))
    for row in rows:
        print("| " + " | ".join(row) + " |")
    machines = {run["machine"] for run in runs}
    if len(machines) > 1:
        print("\nNote: these runs come from different machines:")
        for m in sorted(machines):
            print(f"  - {m}")
    print("\n* = uncommitted changes when the run was made")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark the engine and keep a history of the results."
    )
    parser.add_argument("--label", default="", help="short note saved with this run")
    parser.add_argument("--quick", action="store_true", help="skip minimax depth 3")
    parser.add_argument("--no-save", action="store_true", help="don't save this run")
    parser.add_argument(
        "--history", action="store_true", help="show saved runs and exit"
    )
    args = parser.parse_args()

    runs = load_runs()
    if args.history:
        print_history(runs)
        return

    this_machine = machine()
    results = measure(args.quick)
    previous = next((r for r in reversed(runs) if r["machine"] == this_machine), None)
    print_results(results, previous)

    if args.no_save:
        return
    save_run(
        {
            "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
            "label": args.label,
            "commit": git("rev-parse", "--short", "HEAD"),
            "dirty": bool(git("status", "--porcelain", "--untracked-files=no")),
            "machine": this_machine,
            "python": platform.python_version(),
            "metrics": results,
        }
    )
    print(f"\nsaved to {RESULTS_FILE.relative_to(REPO)}")


if __name__ == "__main__":
    main()
