import random
import math
import statistics
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


def get_palindrome(n):
    string = str(n)
    palindrome = ""
    for i in range(len(string)):
        palindrome = palindrome + string[len(string) - i - 1]

    return int(palindrome)


def is_palindrome(n):
    return n == get_palindrome(n)


def palindrome_sequence(n):
    sequence = []
    stopper = 0
    temp = n

    while not is_palindrome(n):
        n = n + get_palindrome(n)
        sequence.append(n)

        stopper += 1

        if stopper > 100:
            return 0, sequence, 0

    avg_rate = math.log(n / temp) / stopper

    print(f"{temp} converges to {n}, with average rate r = {avg_rate}")

    return n, sequence


def animate_sequence(numbers, interval=900):
    """
    Animate the reverse-and-add sequences of multiple starting numbers
    simultaneously.

    numbers = list of starting values
    interval = milliseconds between terms
    """

    # Make sure numbers is a list
    numbers = list(numbers)

    # Calculate every trajectory
    trajectories = []
    finals = []

    for n in numbers:
        final, sequence = palindrome_sequence(n)

        terms = [n] + sequence

        trajectories.append(terms)
        finals.append(final)

    # Maximum number of steps among all trajectories
    max_length = max(len(terms) for terms in trajectories)

    # Log10 values
    ys = []

    for terms in trajectories:
        ys.append([math.log10(t) for t in terms])

    # Plot
    plt.style.use("dark_background")

    fig, ax = plt.subplots(figsize=(12, 7))

    ax.set_xlim(-0.5, max_length - 0.5)

    all_y = [y for trajectory in ys for y in trajectory]

    ax.set_ylim(
        min(all_y) - 0.5,
        max(all_y) + 0.8
    )

    ax.set_xlabel("Step")
    ax.set_ylabel("log10(term)")

    # Generate colors
    colors = plt.cm.hsv(
        [i / len(numbers) for i in range(len(numbers))]
    )

    lines = []
    dots = []
    stars = []

    for i, n in enumerate(numbers):

        line, = ax.plot(
            [],
            [],
            color=colors[i],
            lw=1.5,
            label=f"Start {n}"
        )

        dot, = ax.plot(
            [],
            [],
            "o",
            color=colors[i],
            ms=7
        )

        star, = ax.plot(
            [],
            [],
            "*",
            color="gold",
            ms=20
        )

        lines.append(line)
        dots.append(dot)
        stars.append(star)

    ax.legend(loc="upper left")

    def update(frame):

        for i, n in enumerate(numbers):

            terms = trajectories[i]
            y = ys[i]

            # Only draw the trajectory if it has reached this frame
            if frame < len(terms):

                x_values = list(range(frame + 1))
                y_values = y[:frame + 1]

                lines[i].set_data(x_values, y_values)
                dots[i].set_data(x_values, y_values)

                # Put a star on the final palindrome
                if frame == len(terms) - 1 and finals[i] != 0:
                    stars[i].set_data(
                        [frame],
                        [y[frame]]
                    )

        # Title
        current_values = []

        for i, n in enumerate(numbers):

            terms = trajectories[i]

            if frame < len(terms):
                value = terms[frame]
            else:
                value = terms[-1]

            current_values.append(
                f"{n} → {value:,};"
            )

        ax.set_title(
            f"Step {frame}   |   " + "   |   ".join(current_values),
            fontsize=13
        )

        return lines + dots + stars

    anim = FuncAnimation(
        fig,
        update,
        frames=max_length,
        interval=interval,
        repeat=False,
        blit=False
    )

    plt.show()

    return anim


def find_sequences(n):
    """
    Find all positive integers whose reverse-and-add sequence
    eventually passes through n.

    Returns a sorted list of all such starting integers.
    """

    # Numbers that can eventually reach n
    ancestors = {n}

    # We process numbers backwards from n
    stack = [n]

    while stack:

        target = stack.pop()

        # Find every x such that
        #
        # x + reverse(x) = target
        #
        # x must be smaller than target.
        for x in range(1, target):

            # A palindrome doesn't generate a next term,
            # so it cannot be a predecessor unless x == target.
            if is_palindrome(x):
                continue

            if x + get_palindrome(x) == target:

                if x not in ancestors:
                    ancestors.add(x)
                    stack.append(x)
                    
    print(len(ancestors))

    return sorted(ancestors)

animate_sequence([27849, 99924])

##successes = []
##finals = []
##for j in range(100,1000):
##    final1, sequence1 = palindrome_sequence(j)
##    final2, sequence2 = palindrome_sequence(2*j)
##    if final1 == final2:
##        successes.append(j)
##        finals.append(final1)
##
##print(successes)
##print(finals)
    

    
