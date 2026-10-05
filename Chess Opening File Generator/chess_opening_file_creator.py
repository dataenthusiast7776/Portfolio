import chess
import chess.engine
import chess.pgn


# ============================================================
# CONFIGURATION
# ============================================================

STOCKFISH_PATH = (
    r"C:\Users\vrajm\OneDrive\Desktop\stockfish"
    r"\stockfish-windows-x86-64-avx2.exe"
)

# Stockfish search depth at each position.
ENGINE_DEPTH = 10

# Maximum number of positions analyzed.
MAX_POSITIONS = 10_000

# Search 10 moves for each side:
#
# 10 White moves + 10 Black moves = 20 plies
#
MAX_PLIES = 40

# We are building a BLACK repertoire.
PLAYER_COLOR = chess.BLACK

# Ask Stockfish for its top 3 moves.
#
# We need 3 because the opponent may have 3 moves
# within the 0.10-pawn window.
MAX_OPPONENT_MOVES = 3

# Opponent moves must ALL be within 0.10 pawns
# of Stockfish's best move.
OPPONENT_MOVE_THRESHOLD = 0.10

# Print progress every N analyzed positions.
PROGRESS_INTERVAL = 100


# ============================================================
# START STOCKFISH
# ============================================================

def start_engine():

    try:

        engine = chess.engine.SimpleEngine.popen_uci(
            STOCKFISH_PATH
        )

        return engine

    except Exception as e:

        print()
        print("Could not start Stockfish.")
        print()
        print("Error:")
        print(e)
        print()

        return None


# ============================================================
# GET ENGINE MOVES
# ============================================================

def get_engine_moves(board, engine):

    try:

        results = engine.analyse(
            board,
            chess.engine.Limit(
                depth=ENGINE_DEPTH
            ),
            multipv=MAX_OPPONENT_MOVES
        )

    except chess.engine.EngineTerminatedError:

        print()
        print("Stockfish terminated unexpectedly.")
        print("Stopping search safely.")
        print()

        return None

    except Exception as e:

        print()
        print("Stockfish analysis failed:")
        print(e)
        print()

        return None

    output = []

    for result in results:

        score = result["score"].pov(
            board.turn
        )

        numerical_score = score.score(
            mate_score=100000
        )

        output.append({
            "move": result["pv"][0],
            "score": numerical_score,
            "pv": result["pv"]
        })

    return output


# ============================================================
# CHOOSE RELEVANT MOVES
# ============================================================

def choose_relevant_moves(
    board,
    engine,
    player_color
):

    candidates = get_engine_moves(
        board,
        engine
    )

    # Stockfish failed.
    if candidates is None:
        return None

    # No legal moves.
    if len(candidates) == 0:
        return []

    # ========================================================
    # OUR MOVE
    # ========================================================
    #
    # We are building a Black repertoire.
    #
    # Therefore, whenever it is Black's turn, we only ever
    # play Stockfish's #1 move.
    #
    # ========================================================

    if board.turn == player_color:

        return [
            candidates[0]
        ]

    # ========================================================
    # OPPONENT MOVE
    # ========================================================
    #
    # White is the opponent.
    #
    # Include up to 3 White moves, but ONLY if each is within
    # 0.10 pawns of the best move.
    #
    # Example:
    #
    # 1. e4    +0.20
    # 2. d4    +0.24
    # 3. Nf3   +0.27
    #
    # All three are within 0.10 of +0.20.
    #
    # So we keep all three.
    #
    # ========================================================

    best_score = candidates[0]["score"]

    relevant = []

    for candidate in candidates:

        difference = (
            abs(
                best_score
                - candidate["score"]
            ) / 100
        )

        if difference <= OPPONENT_MOVE_THRESHOLD:

            relevant.append(candidate)

        else:

            # Since candidates are sorted by engine
            # evaluation, all later moves will be at
            # least as far from the best move.
            break

    return relevant


# ============================================================
# FORMAT SCORE
# ============================================================

def format_score(score):

    if abs(score) >= 90000:

        if score > 0:
            return "Mate"

        return "-Mate"

    return f"{score / 100:+.2f}"


# ============================================================
# SEARCH TREE
# ============================================================

def search_tree(
    board,
    game_node,
    engine,
    state,
    starting_ply,
    player_color
):

    # --------------------------------------------------------
    # POSITION LIMIT
    # --------------------------------------------------------

    if state["positions"] >= MAX_POSITIONS:

        return True

    # --------------------------------------------------------
    # DEPTH LIMIT
    # --------------------------------------------------------

    plies_from_start = (
        board.ply()
        - starting_ply
    )

    if plies_from_start >= MAX_PLIES:

        return True

    # --------------------------------------------------------
    # GAME OVER
    # --------------------------------------------------------

    if board.is_game_over():

        return True

    # --------------------------------------------------------
    # COUNT POSITION
    # --------------------------------------------------------

    state["positions"] += 1

    # --------------------------------------------------------
    # PROGRESS
    # --------------------------------------------------------

    if (
        state["positions"]
        % PROGRESS_INTERVAL
        == 0
    ):

        print(
            f"Analyzed "
            f"{state['positions']:,} positions..."
        )

    # --------------------------------------------------------
    # GET RELEVANT MOVES
    # --------------------------------------------------------

    relevant_moves = choose_relevant_moves(
        board,
        engine,
        player_color
    )

    # Stockfish died.
    if relevant_moves is None:

        state["engine_failed"] = True

        return False

    # --------------------------------------------------------
    # SEARCH EACH MOVE
    # --------------------------------------------------------

    for candidate in relevant_moves:

        # Stop if Stockfish failed.
        if state["engine_failed"]:

            return False

        # Stop if we hit the position budget.
        if state["positions"] >= MAX_POSITIONS:

            return True

        move = candidate["move"]

        score = candidate["score"]

        # ----------------------------------------------------
        # ADD MOVE TO PGN
        # ----------------------------------------------------

        child_node = game_node.add_variation(
            move
        )

        # Store engine evaluation.
        child_node.comment = (
            "Stockfish: "
            + format_score(score)
        )

        # ----------------------------------------------------
        # MAKE MOVE
        # ----------------------------------------------------

        board.push(move)

        # ----------------------------------------------------
        # RECURSE
        # ----------------------------------------------------

        completed = search_tree(
            board,
            child_node,
            engine,
            state,
            starting_ply,
            player_color
        )

        # ----------------------------------------------------
        # UNDO MOVE
        # ----------------------------------------------------

        board.pop()

        # ----------------------------------------------------
        # HANDLE ENGINE FAILURE
        # ----------------------------------------------------

        if (
            not completed
            and state["engine_failed"]
        ):

            return False

    return True


# ============================================================
# MAIN SEARCH FUNCTION
# ============================================================

def Search(
    board,
    player_color=PLAYER_COLOR
):

    # --------------------------------------------------------
    # CREATE PGN
    # --------------------------------------------------------

    game = chess.pgn.Game()

    game.headers["Event"] = (
        "ChessLab Deep Search"
    )

    game.headers["Site"] = (
        "ChessLab"
    )

    game.headers["White"] = (
        "Opponent"
    )

    game.headers["Black"] = (
        "Repertoire"
    )

    # --------------------------------------------------------
    # PRESERVE STARTING POSITION
    # --------------------------------------------------------

    normal_board = chess.Board()

    if board.fen() != normal_board.fen():

        game.setup(board)

    # --------------------------------------------------------
    # SEARCH STATE
    # --------------------------------------------------------

    state = {
        "positions": 0,
        "engine_failed": False
    }

    starting_ply = board.ply()

    # --------------------------------------------------------
    # START STOCKFISH
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("STARTING STOCKFISH")
    print("=" * 60)
    print()

    engine = start_engine()

    if engine is None:

        return game, state["positions"]

    print("Stockfish started successfully.")
    print()

    # --------------------------------------------------------
    # RUN SEARCH
    # --------------------------------------------------------

    try:

        search_tree(
            board.copy(),
            game,
            engine,
            state,
            starting_ply,
            player_color
        )

    except KeyboardInterrupt:

        print()
        print("Search interrupted by user.")
        print()

    except chess.engine.EngineTerminatedError:

        print()
        print("Stockfish terminated unexpectedly.")
        print("Search stopped safely.")
        print()

        state["engine_failed"] = True

    except Exception as e:

        print()
        print("Unexpected search error:")
        print(e)
        print()

        state["engine_failed"] = True

    finally:

        # ----------------------------------------------------
        # SAFELY CLOSE STOCKFISH
        # ----------------------------------------------------

        try:

            engine.quit()

        except Exception:

            # Stockfish may already have died.
            pass

    # --------------------------------------------------------
    # SEARCH SUMMARY
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("SEARCH COMPLETE")
    print("=" * 60)

    print(
        f"Positions analyzed: "
        f"{state['positions']:,}"
    )

    print(
        f"Maximum positions: "
        f"{MAX_POSITIONS:,}"
    )

    print(
        f"Maximum depth: "
        f"{MAX_PLIES} plies"
    )

    print(
        f"Maximum moves per side: "
        f"{MAX_PLIES // 2}"
    )

    print(
        "Repertoire color: BLACK"
    )

    print(
        "Opponent move threshold: "
        f"{OPPONENT_MOVE_THRESHOLD:.2f}"
    )

    if state["engine_failed"]:

        print()
        print(
            "WARNING: Stockfish stopped before "
            "the search was completed."
        )

    print("=" * 60)
    print()

    return game, state["positions"]


# ============================================================
# CONVERT GAME TO PGN
# ============================================================

def game_to_pgn(game):

    exporter = chess.pgn.StringExporter(
        headers=True,
        variations=True,
        comments=True
    )

    return game.accept(exporter)


# ============================================================
# SAVE PGN
# ============================================================

def save_pgn(
    game,
    filename="search_result.pgn"
):

    pgn = game_to_pgn(game)

    try:

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(pgn)

        print(
            f"PGN saved to: {filename}"
        )

    except Exception as e:

        print()
        print("Could not save PGN:")
        print(e)
        print()


# ============================================================
# MAIN PROGRAM
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("CHESSLAB OPENING FILE CREATOR")
    print("=" * 60)
    print()

    # --------------------------------------------------------
    # FEN INPUT
    # --------------------------------------------------------

    print(
        "Enter the FEN for the starting position."
    )

    print(
        "Press Enter for the normal starting position."
    )

    print()

    fen = input("FEN: ").strip()

    # --------------------------------------------------------
    # CREATE BOARD
    # --------------------------------------------------------

    if fen == "":

        board = chess.Board()

    else:

        try:

            board = chess.Board(fen)

        except ValueError as e:

            print()
            print("=" * 60)
            print("INVALID FEN")
            print("=" * 60)
            print()
            print(e)
            print()

            raise SystemExit

    # --------------------------------------------------------
    # DISPLAY POSITION
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("STARTING POSITION")
    print("=" * 60)
    print()

    print(board)

    print()

    print("FEN:")
    print(board.fen())

    print()

    print(
        "Side to move:",
        "White" if board.turn == chess.WHITE
        else "Black"
    )

    print(
        "Repertoire color: Black"
    )

    print()

    # --------------------------------------------------------
    # RUN SEARCH
    # --------------------------------------------------------

    game, positions = Search(
        board,
        player_color=chess.BLACK
    )

    # --------------------------------------------------------
    # GENERATE PGN
    # --------------------------------------------------------

    pgn = game_to_pgn(game)

    print()
    print("=" * 60)
    print("GENERATED PGN")
    print("=" * 60)
    print()

    print(pgn)

    # --------------------------------------------------------
    # SAVE PGN
    # --------------------------------------------------------

    save_pgn(
        game,
        "search_result.pgn"
    )

    print()
    print("Done.")
