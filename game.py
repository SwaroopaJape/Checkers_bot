import copy

BOARD_SIZE = 8 

EMPTY = 0
WHITE = 1
BLACK = 2
WHITE_KING = 3
BLACK_KING = 4

def initial_board():
    board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    rows_per_side = (BOARD_SIZE // 2) - 1
    for r in range(rows_per_side):
        for c in range(BOARD_SIZE):
            if (r + c) % 2 == 1:
                board[r][c] = BLACK
    for r in range(BOARD_SIZE - rows_per_side, BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if (r + c) % 2 == 1:
                board[r][c] = WHITE
    return board

def is_king(piece):
    return piece in (WHITE_KING, BLACK_KING)

def piece_color(piece):
    if piece in (WHITE, WHITE_KING):
        return WHITE
    if piece in (BLACK, BLACK_KING):
        return BLACK
    return EMPTY

def promote(board):
    for c in range(BOARD_SIZE):
        if board[0][c] == WHITE:
            board[0][c] = WHITE_KING
        if board[BOARD_SIZE - 1][c] == BLACK:
            board[BOARD_SIZE - 1][c] = BLACK_KING

def get_directions(piece):
    if piece == WHITE:
        return [(-1, -1), (-1, 1)]
    if piece == BLACK:
        return [(1, -1), (1, 1)]
    return [(-1, -1), (-1, 1), (1, -1), (1, 1)]

def in_bounds(r, c):
    return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE

def get_jumps(board, r, c, piece, visited=None):
    if visited is None:
        visited = set()
    visited.add((r, c))
    color = piece_color(piece)
    dirs = get_directions(piece)
    sequences = []
    found_any = False
    for dr, dc in dirs:
        mr, mc = r + dr, c + dc
        lr, lc = r + 2 * dr, c + 2 * dc
        if not in_bounds(lr, lc):
            continue
        mid_piece = board[mr][mc]
        if piece_color(mid_piece) not in (EMPTY, color) and mid_piece != EMPTY and (lr, lc) not in visited:
            found_any = True
            new_board = copy.deepcopy(board)
            new_board[lr][lc] = piece
            new_board[r][c] = EMPTY
            new_board[mr][mc] = EMPTY
            # Check promotion mid-chain only for non-kings reaching back row
            became_king = False
            if piece == WHITE and lr == 0:
                new_board[lr][lc] = WHITE_KING
                became_king = True
            elif piece == BLACK and lr == BOARD_SIZE - 1:
                new_board[lr][lc] = BLACK_KING
                became_king = True
            new_piece = new_board[lr][lc]
            if became_king:
                sequences.append(((r, c), (lr, lc), new_board))
            else:
                sub = get_jumps(new_board, lr, lc, new_piece, set(visited))
                if sub:
                    for seq in sub:
                        sequences.append(((r, c), (lr, lc)) + seq[2:] if isinstance(seq[0], tuple) else seq)
                        # Rebuild: store as (from, to, board_after)
                        # Simplify: store full chain as list of steps
                    for seq in sub:
                        sequences.append(((r, c), (lr, lc), seq[2]))
                else:
                    sequences.append(((r, c), (lr, lc), new_board))
    if not found_any:
        return []
    return sequences

def get_all_jumps(board, r, c, piece):
    color = piece_color(piece)
    dirs = get_directions(piece)
    results = []
    visited = {(r, c)}

    def dfs(cur_board, cur_r, cur_c, cur_piece, path, visited):
        dirs2 = get_directions(cur_piece)
        found = False
        for dr, dc in dirs2:
            mr, mc = cur_r + dr, cur_c + dc
            lr, lc = cur_r + 2 * dr, cur_c + 2 * dc
            if not in_bounds(lr, lc):
                continue
            mid = cur_board[mr][mc]
            
            if cur_board[lr][lc] == EMPTY and piece_color(mid) not in (EMPTY, color) and mid != EMPTY and (lr, lc) not in visited:
                found = True
                nb = copy.deepcopy(cur_board)
                nb[lr][lc] = cur_piece
                nb[cur_r][cur_c] = EMPTY
                nb[mr][mc] = EMPTY
                became_king = False
                if cur_piece == WHITE and lr == 0:
                    nb[lr][lc] = WHITE_KING; became_king = True
                elif cur_piece == BLACK and lr == BOARD_SIZE - 1:
                    nb[lr][lc] = BLACK_KING; became_king = True
                new_p = nb[lr][lc]
                new_visited = visited | {(lr, lc)}
                dfs(nb, lr, lc, new_p, path + [(lr, lc)], new_visited)
        if not found and len(path) > 1:
            results.append((path, cur_board))

    dfs(board, r, c, piece, [(r, c)], visited)
    return results

def get_legal_moves(board, color):
    jumps = []
    steps = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            piece = board[r][c]
            if piece_color(piece) != color:
                continue
            # Collect jumps
            chains = get_all_jumps(board, r, c, piece)
            jumps.extend(chains)
            # Collect steps (only if no jumps found globally — enforced after)
            dirs = get_directions(piece)
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if in_bounds(nr, nc) and board[nr][nc] == EMPTY:
                    nb = copy.deepcopy(board)
                    nb[nr][nc] = piece
                    nb[r][c] = EMPTY
                    if piece == WHITE and nr == 0:
                        nb[nr][nc] = WHITE_KING
                    elif piece == BLACK and nr == BOARD_SIZE - 1:
                        nb[nr][nc] = BLACK_KING
                    steps.append(([(r, c), (nr, nc)], nb))
    if jumps:
        return jumps  # Jumps are mandatory
    return steps

def apply_move(board, move):
    path, new_board = move
    promote(new_board)
    return new_board

def check_winner(board, current_color):
    opponent = BLACK if current_color == WHITE else WHITE
    opp_moves = get_legal_moves(board, opponent)
    if not opp_moves:
        return current_color
    my_moves = get_legal_moves(board, current_color)
    if not my_moves:
        return opponent
    return None

def count_pieces(board):
    white = white_kings = black = black_kings = 0
    for row in board:
        for p in row:
            if p == WHITE: white += 1
            elif p == WHITE_KING: white_kings += 1
            elif p == BLACK: black += 1
            elif p == BLACK_KING: black_kings += 1
    return white, white_kings, black, black_kings