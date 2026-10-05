# Portfolio

Projects by Vikram Rajmohan, a mathematics student at Amherst College interested in finance, data analysis, and software.

| Project | What it is | Tools |
|---|---|---|
| [Random Walk + Persistence Simulation](#random-walk--persistence-simulation) | Tests whether trading rules can beat a random market | Python, matplotlib |
| [Chess Opening File Generator](#chess-opening-file-generator) | [one-line description] | [tools] |
| [DataDorm](#datadorm) | [one-line description] | [tools] |
| [Mandarin Character Driller (Simplified)](#mandarin-character-driller-simplified) | [one-line description] | [tools] |
| [MatchMyApp](#matchmyapp) | [one-line description] | [tools] |

---

## Random Walk + Persistence Simulation

**File:** `Random Walk + Persistence Simulation.py`

A simulation that asks a simple question: if a price moves completely at random, can a trading rule still produce an edge? It generates random price paths, runs a "buy the dip" strategy on them, and uses Monte Carlo to see whether the results are skill or luck.

### How it works

1. **Random walk.** Builds a symmetric +1 / -1 walk of `N` steps.
2. **Price series.** Converts the walk into a positive price starting at 100, where each step is a +1% or -1% compounded move. Percent returns are meaningful and the path is a fair game by construction.
3. **Dip-buying strategy.** Runs one iteration at a time:
   - **Entry:** go long when the average change over the last 10 steps is below -0.5.
   - **Exit:** whichever comes first of a break-even target, a stop loss (-5%), or a maximum holding time.
   - **Loss cooldown:** after a losing exit, stay out of the market for 400 iterations.
4. **Reporting.** Prints win rate, average return per trade, hold times, worst drawdown while holding, exits by reason, blocked signals, and compounded growth of $1. Plots the price on a log scale with entries and exits marked.
5. **Monte Carlo.** Repeats the whole experiment 1,000 times on fresh random walks and summarizes the distribution of outcomes.

A simpler take-profit / stop-loss strategy (`naive_strategy`) is also included for comparison, with its reporting code commented out.

### Example results

Results change on every run because the walk is not seeded. One run of 1,000 simulations (10,000 steps each):

| Metric | Result |
|---|---|
| Runs with a positive return | 44.8% |
| Mean return | -0.25% |
| Median return | -2.91% |
| Worst / best run | -45.2% / +126.3% |

A single run of the strategy showed an **83% win rate** but a **negative average return per trade (-0.16%)**. Many small wins at break-even are wiped out by fewer, larger stop-loss losses.

### Takeaway

A high win rate does not mean a strategy has an edge. On a fair random walk, the dip-buying rule reshapes the distribution of outcomes (frequent small gains, occasional large losses) without improving the expected return. This is why backtests should be judged on expected value and tested against random baselines, not on win rate alone.

### Run it

```bash
pip install matplotlib
python "Random Walk + Persistence Simulation.py"
```

Parameters (walk length, window, entry threshold, stop loss, cooldown, and so on) are set in the `# Settings` block near the middle of the file.

---

## Chess Opening File Generator



**Tools:** Python, python-chess
**Run it:** `[command]`

---

## DataDorm



**Tools:** Streamlit
**Run it:** `[command]`

---

## Mandarin Character Driller (Simplified)



**Tools:** [...]
**Run it:** `[command]`

---

## MatchMyApp



**Tools:** [...]
**Run it:** `[command]`

---

## Contact

vrajmohan29@amherst.edu
