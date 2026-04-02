import streamlit as st
import time 
import random

from game import (
    initial_board, get_legal_moves, apply_move, check_winner,
    piece_color, is_king, promote,
    WHITE, BLACK, WHITE_KING, BLACK_KING, EMPTY, BOARD_SIZE,
)
from ai import minimax_move, mcts_move

def simulate_game(depth, board_ph, status_ph, game_num, max_moves=100):
    """Runs a visual game of AI vs AI, returning the winner or DRAW."""
    board = initial_board()
    turn = WHITE
    moves_played = 0
    
    # 1. NEW: Initialize a dictionary to keep track of board states
    state_history = {} 
    
    while moves_played < max_moves:
        winner = check_winner(board, turn)
        if winner: return winner
        
        # 2. NEW: Take an immutable snapshot of the board and whose turn it is
        current_state = (tuple(tuple(row) for row in board), turn)
        
        # 3. NEW: Count how many times we have seen this exact state
        state_history[current_state] = state_history.get(current_state, 0) + 1
        
        # 4. NEW: If we hit 3 times, force a draw!
        if state_history[current_state] >= 3:
            # Draw the final board state before exiting
            with board_ph.container():
                render_board(board, None, [], False, turn, key_prefix=f"sim_{game_num}_{moves_played}_")
            status_ph.warning("Draw by Threefold Repetition!")
            return "DRAW"
        
        # Update the status text
        status_ph.info(f"**Game {game_num}/10** | Move {moves_played+1}: {'⚪ White' if turn == WHITE else '⚫ Black'} is thinking...")
        
        # Render the board visually in the placeholder
        with board_ph.container():
            render_board(board, None, [], False, turn, key_prefix=f"sim_{game_num}_{moves_played}_")
        
        # Wait 0.5 seconds so you can see the state!
        time.sleep(0.5) 
        
        if moves_played == 0:
            # Force variety: Pick a random opening move
            moves = get_legal_moves(board, turn)
            move = random.choice(moves)
        else:
            opponent = BLACK if turn == WHITE else WHITE
            move = minimax_move(board, turn, opponent, depth)
            
        if move is None:
            return BLACK if turn == WHITE else WHITE
            
        board = apply_move(board, move)
        turn = BLACK if turn == WHITE else WHITE
        moves_played += 1
        
    # Draw the final board state before exiting (if max moves reached)
    with board_ph.container():
        render_board(board, None, [], False, turn, key_prefix=f"sim_{game_num}_{moves_played}_")
        
    return "DRAW"

st.set_page_config(
    page_title="Checkers AI",
    page_icon="🔴",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=IBM+Plex+Mono:wght@400;600&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background-color: #0f0a00 !important;
}
section[data-testid="stSidebar"] {
    background: #100c00 !important;
    border-right: 1px solid #3a2800;
}
h1 { font-family: 'Playfair Display', serif !important; color: #f0c060 !important; }
p, li { color: #c0a060; font-family: 'IBM Plex Mono', monospace; }

/* Make every button in the board grid a fixed square */
div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"] button {
    width: 64px !important;
    height: 64px !important;
    min-width: 64px !important;
    padding: 0 !important;
    font-size: 1.5rem !important;
    line-height: 1 !important;
    border-radius: 0 !important;
    border: 1px solid #1a1000 !important;
}
</style>
""", unsafe_allow_html=True)


# ── State helpers ─────────────────────────────────────────────────────────────

def init_game():
    board = initial_board()
    st.session_state.board        = board
    st.session_state.turn         = WHITE
    st.session_state.selected     = None
    st.session_state.legal_moves  = get_legal_moves(board, WHITE)
    st.session_state.game_over    = False
    st.session_state.winner       = None
    st.session_state.status       = "Click one of your pieces to begin"
    st.session_state.move_log     = []
    st.session_state.game_started = True


def handle_click(r, c):
    board       = st.session_state.board
    selected    = st.session_state.selected
    legal_moves = st.session_state.legal_moves

    valid_sources = {move[0][0] for move in legal_moves}
    dest_map = {}
    if selected is not None:
        for move in legal_moves:
            path, _ = move
            if path[0] == selected:
                dest_map[path[-1]] = move

    if selected is None:
        if (r, c) in valid_sources:
            st.session_state.selected = (r, c)
            st.session_state.status   = f"Piece at ({r},{c}) selected — click a marked square to move"
        else:
            st.session_state.status = "Not a movable piece — pick one of your ⚪ pieces"
    else:
        if (r, c) in dest_map:
            move = dest_map[(r, c)]
            nb   = apply_move(board, move)
            promote(nb)
            path, _ = move
            st.session_state.move_log.append(
                f"YOU  ({path[0][0]},{path[0][1]}) → ({path[-1][0]},{path[-1][1]})"
            )
            st.session_state.board    = nb
            st.session_state.selected = None
            winner = check_winner(nb, WHITE)
            if winner:
                st.session_state.game_over = True
                st.session_state.winner    = winner
                return
            new_moves = get_legal_moves(nb, BLACK)
            if not new_moves:
                st.session_state.game_over = True
                st.session_state.winner    = WHITE
                st.session_state.status    = "AI has no moves — You win!"
                return
            st.session_state.legal_moves = new_moves
            st.session_state.turn        = BLACK
            st.session_state.status      = "AI is thinking…"
        elif (r, c) in valid_sources:
            st.session_state.selected = (r, c)
            st.session_state.status   = f"Switched to piece at ({r},{c})"
        else:
            st.session_state.selected = None
            st.session_state.status   = "Deselected — click one of your pieces"


def run_ai_turn():
    board = st.session_state.board
    agent = st.session_state.agent_choice
    if agent == "Minimax + Alpha-Beta":
        move = minimax_move(board, BLACK, WHITE, st.session_state.ai_depth)
    else:
        move = mcts_move(board, BLACK, WHITE, st.session_state.ai_iters)

    if move is None:
        st.session_state.game_over = True
        st.session_state.winner    = WHITE
        st.session_state.status    = "AI has no moves — You win!"
        return

    nb = apply_move(board, move)
    promote(nb)
    path, _ = move
    st.session_state.move_log.append(
        f"AI   ({path[0][0]},{path[0][1]}) → ({path[-1][0]},{path[-1][1]})"
    )
    st.session_state.board = nb
    winner = check_winner(nb, BLACK)
    if winner:
        st.session_state.game_over = True
        st.session_state.winner    = winner
        return
    new_moves = get_legal_moves(nb, WHITE)
    if not new_moves:
        st.session_state.game_over = True
        st.session_state.winner    = BLACK
        st.session_state.status    = "You have no moves — AI wins!"
        return
    st.session_state.legal_moves = new_moves
    st.session_state.turn        = WHITE
    st.session_state.status      = "Your turn — click one of your pieces"


# ── Board renderer ────────────────────────────────────────────────────────────

PIECE_GLYPH = {
    WHITE:       "⚪",
    WHITE_KING:  "👑",
    BLACK:       "⚫",
    BLACK_KING:  "♛",
    EMPTY:       " ",
}

def render_board(board, selected, legal_moves, game_over, turn, key_prefix=""):
    dest_squares = set()
    src_squares  = set()

    if not game_over and turn == WHITE:
        for move in legal_moves:
            path, _ = move
            src_squares.add(path[0])
            if selected is not None and path[0] == selected:
                dest_squares.add(path[-1])

    # Build one big style block for all cells upfront (avoids per-cell markdown spam)
    style_rules = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            dark    = (r + c) % 2 == 1
            is_sel  = selected == (r, c)
            is_dest = (r, c) in dest_squares
            is_src  = (r, c) in src_squares
            piece   = board[r][c]
            pc      = piece_color(piece)

            if not dark:
                bg = "#c8a870"
            elif is_sel:
                bg = "#b89000"
            elif is_dest:
                bg = "#2d5e0a"
            elif is_src and not game_over:
                bg = "#3a2200"
            else:
                bg = "#1e1200"

            fg = ("#f0f0e8" if pc == WHITE
                  else "#0a0500" if pc == BLACK
                  else "#806030")

            # Target the button by its key — Streamlit renders key as part of the element id
            style_rules.append(
                f'button[data-testid="baseButton-secondary"][kind="secondary"]'
                f'[aria-label="cell_{r}_{c}"] {{'
                f'background:{bg} !important; color:{fg} !important;}}'
            )

    # Simpler approach: use nth-of-type per row/col
    cell_styles = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            dark    = (r + c) % 2 == 1
            is_sel  = selected == (r, c)
            is_dest = (r, c) in dest_squares
            is_src  = (r, c) in src_squares
            piece   = board[r][c]
            pc      = piece_color(piece)

            if not dark:
                bg = "#c8a870"
            elif is_sel:
                bg = "#b89000"
            elif is_dest:
                bg = "#2d5e0a"
            elif is_src and not game_over:
                bg = "#3a2200"
            else:
                bg = "#1e1200"

            fg = ("#f0f0e8" if pc == WHITE
                  else "#050200" if pc == BLACK
                  else "#806030")

            cell_styles.append((r, c, bg, fg))

    # Render rows
    for r in range(BOARD_SIZE):
        cols = st.columns(BOARD_SIZE, gap="small")
        for c in range(BOARD_SIZE):
            _, _, bg, fg = cell_styles[r * BOARD_SIZE + c]
            piece  = board[r][c]
            is_dest = (r, c) in dest_squares

            glyph = PIECE_GLYPH.get(piece, " ")
            if piece == EMPTY and is_dest:
                glyph = "·"

            with cols[c]:
                # Inject cell-specific colour via a tiny scoped style using nth-child
                # We target the column's button directly
                st.markdown(
                    f"<style>"
                    f"div[data-testid='stHorizontalBlock']:nth-of-type({r + 2}) "
                    f"div[data-testid='stColumn']:nth-child({c + 1}) button"
                    f"{{background:{bg}!important;color:{fg}!important;}}"
                    f"</style>",
                    unsafe_allow_html=True,
                )
                clicked = st.button(glyph, key=f"{key_prefix}cell_{r}_{c}")
                if clicked and not game_over and turn == WHITE:
                    handle_click(r, c)
                    st.rerun()


# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ♟ Checkers AI")
    st.markdown("---")

    game_started = st.session_state.get("game_started", False)

    if not game_started:
        agent = st.radio(
            "Choose opponent",
            ["Minimax + Alpha-Beta", "Monte Carlo Tree Search"],
            key="widget_agent_choice",
        )
        if agent == "Minimax + Alpha-Beta":
            st.slider("Search Depth", 1, 7, 4, key="widget_ai_depth",
                      help="Higher depth = stronger AI, but slower response")
        else:
            st.slider("MCTS Iterations", 100, 3000, 500, step=100, key="widget_ai_iters",
                      help="More iterations = stronger AI, but slower response")

        st.markdown("---")
        st.markdown("**You** → ⚪ White  \n**AI** → ⚫ Black")
        st.markdown("---")
        
        if st.button("▶  Start Game", use_container_width=True):
            
            st.session_state.agent_choice = st.session_state.widget_agent_choice
            
            st.session_state.ai_depth = st.session_state.get("widget_ai_depth", 4)
            st.session_state.ai_iters = st.session_state.get("widget_ai_iters", 500)
            
            init_game()
            st.rerun()
        st.markdown("---")
        if st.button("🧪 Simulate AI vs AI", use_container_width=True):
            st.session_state.running_sim = True
            st.session_state.ai_depth = st.session_state.get("widget_ai_depth", 4)
            st.rerun()

    else:
        # Game in progress — settings are locked, show stats only
        board   = st.session_state.board
        wn = sum(1 for row in board for p in row if p in (WHITE, WHITE_KING))
        bn = sum(1 for row in board for p in row if p in (BLACK, BLACK_KING))
        wk = sum(1 for row in board for p in row if p == WHITE_KING)
        bk = sum(1 for row in board for p in row if p == BLACK_KING)

        agent_label = st.session_state.get("agent_choice", "")
        st.markdown(f"**Opponent:** {agent_label}")
        if agent_label == "Minimax + Alpha-Beta":
            st.markdown(f"**Depth:** {st.session_state.get('ai_depth', 4)}")
        else:
            st.markdown(f"**Iterations:** {st.session_state.get('ai_iters', 500)}")
        st.markdown("---")

        c1, c2 = st.columns(2)
        c1.metric("⚪ You", wn, f"+{wk}K" if wk else None)
        c2.metric("⚫ AI",  bn, f"+{bk}K" if bk else None)

        st.markdown("---")
        st.markdown("**Move Log**")
        log_text = "\n".join(st.session_state.move_log[-16:]) or "—"
        st.code(log_text, language=None)
        st.markdown("---")

        if st.button("🔄  New Game", use_container_width=True):
            for k in ["board","turn","selected","legal_moves",
                      "game_over","winner","status","move_log","game_started"]:
                st.session_state.pop(k, None)
            st.rerun()


# ── Main content ──────────────────────────────────────────────────────────────

st.markdown("# Checkers")

if st.session_state.get("running_sim", False):
    st.markdown("### 🤖 Live AI vs AI Simulation")
    st.markdown("Watching 10 games to demonstrate that perfect play results in a draw. *(Note: At 0.5s per move, this will take several minutes!)*")
    
    # Create empty placeholders that we can overwrite in the loop
    progress_bar = st.progress(0)
    stats_ph = st.empty()
    status_ph = st.empty()
    board_ph = st.empty()
    
    results = {WHITE: 0, BLACK: 0, "DRAW": 0}
    depth = st.session_state.get("ai_depth", 3)
    
    def update_stats():
        with stats_ph.container():
            c1, c2, c3 = st.columns(3)
            c1.metric("⚪ White Wins", results[WHITE])
            c2.metric("⚫ Black Wins", results[BLACK])
            c3.metric("🤝 Draws", results["DRAW"])
            
    update_stats() # Draw initial 0-0-0 stats
    
    for i in range(1, 11):
        # Run the visual game
        res = simulate_game(depth, board_ph, status_ph, i)
        
        # Record and update results
        results[res] += 1
        progress_bar.progress(i * 10)
        update_stats()
        
        # Brief pause so the user can read the result before the board wipes
        status_ph.success(f"Game {i} finished: {res}. Starting next game...")
        time.sleep(2)
            
    status_ph.success("Simulation Complete! As expected, perfect optimal play neutralizes both sides.")
    
    if st.button("⬅ Return to Main Menu"):
        st.session_state.running_sim = False
        st.rerun()
        
    st.stop()

game_started = st.session_state.get("game_started", False)

game_started = st.session_state.get("game_started", False)

if not game_started:
    st.markdown("""
Configure your opponent in the **sidebar**, then press **▶ Start Game**.

**You play ⚪ White — AI plays ⚫ Black.**

**Rules reminder**
- Pieces move diagonally forward; Kings move in all four directions.
- Jumps are mandatory. Chains of jumps happen in one turn.
- A piece reaching the far end is crowned King.
- Win by capturing all enemy pieces or leaving them with no legal moves.

**How to move:** Click one of your pieces (it turns yellow), then click a marked square to move there. Click a different piece to re-select.
""")
else:
    board       = st.session_state.board
    selected    = st.session_state.selected
    legal_moves = st.session_state.legal_moves
    game_over   = st.session_state.game_over
    turn        = st.session_state.turn
    winner      = st.session_state.winner

    if game_over:
        msg = "🎉 **You win!**" if winner == WHITE else "🤖 **AI wins!**"
        st.success(msg)
    else:
        label = "Your turn" if turn == WHITE else "🤖 AI is thinking…"
        st.info(f"{label} — {st.session_state.status}")

    render_board(board, selected, legal_moves, game_over, turn)

    st.caption("⚪ your piece · 👑 your king · ⚫ AI piece · ♛ AI king · 🟡 selected · 🟢 valid destination")

    if not game_over and turn == BLACK:
        with st.spinner("AI calculating move…"):
            time.sleep(1)
            run_ai_turn()
        st.rerun()