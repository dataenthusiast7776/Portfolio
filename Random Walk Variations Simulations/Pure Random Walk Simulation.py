import math, random
import statistics
import matplotlib.pyplot as plt

def random_walk(iterations):
    pos = [0]
    for i in range(iterations):
        pos.append(pos[i] + ((-1) ** (random.randint(1,2))))

    return pos


def walk_to_price(walk, start_price=100.0, step_pct=0.01):
    """Turn the +/-1 walk into a positive price series so '% return' makes sense.
    Each +1 step is a +1% return and each -1 step is a -1% return (compounded),
    so the price is a fair game: no built-in edge for or against the strategy."""
    price = [start_price]
    for i in range(1, len(walk)):
        price.append(price[-1] * (1 + step_pct * (walk[i] - walk[i - 1])))
    return price


def naive_strategy(price, enter_at=0, take_profit=0.10, stop_loss=0.10, reenter=True):
    """Naive trading strategy, run one iteration at a time.
    - Enter (go long) at index `enter_at`.
    - Every iteration, check return = price / entry_price - 1.
    - Exit if return >= +take_profit OR return <= -stop_loss.
    - If reenter=True, buy again on the very next iteration; if False, stop after one trade.
    Returns a list of trades: (entry_index, exit_index, return)."""
    trades = []
    in_position = False
    entry_price = None
    entry_idx = None

    for i in range(enter_at, len(price)):
        if not in_position:
            in_position = True
            entry_price = price[i]
            entry_idx = i
        else:
            ret = price[i] / entry_price - 1
            if ret >= take_profit or ret <= -stop_loss:
                trades.append((entry_idx, i, ret))
                in_position = False
                if not reenter:
                    break
    return trades


def dip_buying_strategy(walk, price, window=10, entry_threshold=-0.5, exit_return=0.0,
                        stop_loss=0.10, max_hold=500, loss_cooldown=100):
    """Buy-the-dip strategy, run one iteration at a time.
    - Signal: average change of the walk over the last `window` iterations,
      avg = (walk[i] - walk[i - window]) / window   (ranges from -1 to +1).
    - Enter (go long) only if flat, not in a cooldown, AND avg < entry_threshold.
    - Exit on whichever happens first:
        TARGET     : return >= exit_return   (0.0 = sell the moment the trade breaks even)
        STOP LOSS  : return <= -stop_loss    (set stop_loss=None to disable)
        TIME STOP  : held for >= max_hold iterations (set max_hold=None to disable)
    - LOSS COOLDOWN: after any exit with a negative return, no new entries are allowed for the
      next `loss_cooldown` iterations (set to 0 to disable). No cooldown after a winning exit.
      Note: with exit_return=0 a trade can only end in a loss via the stop loss or time stop.
    Returns (trades, open_position, blocked_signals)
      trades          = list of (entry_index, exit_index, return, worst_return_while_held, exit_reason)
      open_position   = (entry_index, entry_price, worst_return_so_far) if still holding at the end, else None
      blocked_signals = number of iterations where the entry signal fired but the cooldown blocked it."""
    trades = []
    in_position = False
    entry_price = None
    entry_idx = None
    worst = 0.0
    blocked_until = -1       # entries are blocked while i <= blocked_until
    blocked_signals = 0

    for i in range(window, len(price)):
        if in_position:
            ret = price[i] / entry_price - 1
            worst = min(worst, ret)
            reason = None
            if ret >= exit_return:
                reason = "target hit"
            elif stop_loss is not None and ret <= -stop_loss:
                reason = "stop loss"
            elif max_hold is not None and i - entry_idx >= max_hold:
                reason = "time stop"

            if reason is not None:
                trades.append((entry_idx, i, ret, worst, reason))
                in_position = False
                if ret < 0:
                    blocked_until = i + loss_cooldown
        else:
            avg_change = (walk[i] - walk[i - window]) / window
            if avg_change < entry_threshold:
                if i <= blocked_until:
                    blocked_signals += 1
                else:
                    in_position = True
                    entry_price = price[i]
                    entry_idx = i
                    worst = 0.0

    open_position = (entry_idx, entry_price, worst) if in_position else None
    return trades, open_position, blocked_signals


# Settings
N = 10000              # random walk length (try 20000 to see individual trades clearly)
ENTER_AT = 100      # iteration at which the strategy first enters
TAKE_PROFIT = 0.20   # exit at +10%
STOP_LOSS = 0.05    # exit at -10%

WINDOW = 10
ENTRY_THRESHOLD = -0.5
EXIT_RETURN = 0.0    # sell as soon as the trade is back to break-even (0.0)
MAX_HOLD = 10000       # time stop: force an exit after this many iterations (None to disable)
LOSS_COOLDOWN = 400  # iterations to stay out of the market after a LOSING trade (0 to disable)

#Run Random Walk + Strategy
x = range(N + 1)
y = random_walk(N)
print(f"Average position: {sum(y)/len(y)}")

price = walk_to_price(y)
trades, open_pos, blocked = dip_buying_strategy(y, price, WINDOW, ENTRY_THRESHOLD, EXIT_RETURN,
                                                STOP_LOSS, MAX_HOLD, LOSS_COOLDOWN)

##Naive Strategy results
##returns = [t[2] for t in trades]
##wins = sum(1 for r in returns if r > 0)
##capital = 1.0
##for r in returns:
##    capital *= (1 + r)
##print(f"Trades: {len(trades)}")
##if trades:
##    print(f"Win rate: {wins / len(trades) * 100:.1f}%")
##    print(f"Average return per trade: {statistics.mean(returns) * 100:.2f}%")
##    print(f"Compounded growth of $1: ${capital:.3g}")
##
###Plot Price with entries and exits in red
##entry_idx = [t[0] for t in trades]
##exit_idx = [t[1] for t in trades]
##
##plt.figure(figsize=(14, 6))
##plt.plot(x, price, linewidth=0.8, color="steelblue", label="Price (from random walk)")
##plt.scatter(entry_idx, [price[i] for i in entry_idx], color="red", marker="^", s=18, label="Entry", zorder=3)
##plt.scatter(exit_idx, [price[i] for i in exit_idx], color="red", marker="x", s=18, label="Exit", zorder=3)
##plt.xlabel("Iteration")
##plt.ylabel("Price")
###plt.yscale("log")
##plt.title("Random Walk with Naive +/-10% Trading Strategy")
##plt.legend()
##plt.tight_layout()
##plt.show()

#dip_buying_strategy results
print(f"Closed trades: {len(trades)}")
capital = 1.0
if trades:
    returns = [t[2] for t in trades]
    holds = [t[1] - t[0] for t in trades]
    wins = sum(1 for r in returns if r > 0)
    capital = math.prod(1 + r for r in returns)
    print(f"Win rate: {wins / len(trades) * 100:.1f}%")
    print(f"Average return per trade: {statistics.mean(returns) * 100:.2f}%")
    print(f"Average hold time: {statistics.mean(holds):.1f} iterations | longest: {max(holds)}")
    print(f"Worst drawdown while holding a trade: {min(t[3] for t in trades) * 100:.1f}%")
    for reason in ("target hit", "stop loss", "time stop"):
        count = sum(1 for t in trades if t[4] == reason)
        print(f"  Exits by {reason}: {count}")
    print(f"Compounded growth of $1 (closed trades only): ${capital:.4g}")
print(f"Entry signals blocked by the loss cooldown: {blocked}")

if open_pos is not None:
    unrealized = price[-1] / open_pos[1] - 1
    print(f"STILL HOLDING at the end: entered at iteration {open_pos[0]}, "
          f"unrealized return {unrealized * 100:.2f}%, worst so far {open_pos[2] * 100:.2f}%")
    print(f"Mark-to-market growth of $1 (including open position): ${capital * (1 + unrealized):.4g}")
else:
    print("No open position at the end.")

#Plot Price with entries and exits in red
entry_idx = [t[0] for t in trades]
exit_idx = [t[1] for t in trades]
if open_pos is not None:
    entry_idx.append(open_pos[0])

plt.figure(figsize=(14, 6))
plt.plot(x, price, linewidth=0.8, color="steelblue", label="Price (from random walk)")
plt.scatter(entry_idx, [price[i] for i in entry_idx], color="red", marker="^", s=40, label="Entry", zorder=3)
plt.scatter(exit_idx, [price[i] for i in exit_idx], color="red", marker="x", s=40, label="Exit", zorder=3)
plt.xlabel("Iteration")
plt.ylabel("Price (log scale)")
plt.yscale("log")
plt.title(f"Dip-Buying: enter if {WINDOW}-step avg change < {ENTRY_THRESHOLD}, sell at break-even, "
          f"SL -{STOP_LOSS*100:.0f}%, max hold {MAX_HOLD}, loss cooldown {LOSS_COOLDOWN}")
plt.legend()
plt.tight_layout()
plt.show()

def monte_carlo(runs=1000, N=10000):
    results = []
    for _ in range(runs):
        y = random_walk(N)
        p = walk_to_price(y)
        tr, op, bl = dip_buying_strategy(y, p, WINDOW, ENTRY_THRESHOLD, EXIT_RETURN,
                                         STOP_LOSS, MAX_HOLD, LOSS_COOLDOWN)
        growth = math.prod(1 + t[2] for t in tr)
        if op is not None:
            growth *= p[-1] / op[1]          # mark any open position to market
        results.append(growth - 1)
    pos = sum(r > 0 for r in results) / runs * 100
    print(f"Positive runs: {pos:.1f}%")
    print(f"Mean: {statistics.mean(results)*100:.2f}%  Median: {statistics.median(results)*100:.2f}%")
    print(f"Worst: {min(results)*100:.1f}%  Best: {max(results)*100:.1f}%")

monte_carlo(1000)
