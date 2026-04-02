import math
import random
import copy
from game import (
    get_legal_moves, apply_move, check_winner,
    WHITE, BLACK, WHITE_KING, BLACK_KING, EMPTY, count_pieces
)

# Minimax with Alpha-Beta Pruning

def evaluate(board, ai_color):
    w, wk, b, bk = count_pieces(board)
    if ai_color == WHITE:
        return (w + 2 * wk) - (b + 2 * bk)
    else:
        return (b + 2 * bk) - (w + 2 * wk)

def minimax(board, depth, alpha, beta, maximizing, ai_color, human_color):
    current_color = ai_color if maximizing else human_color
    winner = check_winner(board, human_color if maximizing else ai_color)
    if winner == ai_color:
        return 1000 + depth, None
    if winner == human_color:
        return -1000 - depth, None

    moves = get_legal_moves(board, current_color)
    if not moves:
        return (-1000 if maximizing else 1000), None

    if depth == 0:
        return evaluate(board, ai_color), None

    best_move = None
    if maximizing:
        best_val = -math.inf
        for move in moves:
            nb = apply_move(board, move)
            val, _ = minimax(nb, depth - 1, alpha, beta, False, ai_color, human_color)
            if val > best_val:
                best_val = val
                best_move = move
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return best_val, best_move
    else:
        best_val = math.inf
        for move in moves:
            nb = apply_move(board, move)
            val, _ = minimax(nb, depth - 1, alpha, beta, True, ai_color, human_color)
            if val < best_val:
                best_val = val
                best_move = move
            beta = min(beta, val)
            if beta <= alpha:
                break
        return best_val, best_move

def minimax_move(board, ai_color, human_color, depth):
    _, move = minimax(board, depth, -math.inf, math.inf, True, ai_color, human_color)
    return move


# Monte Carlo Tree Search

class MCTSNode:
    def __init__(self, board, color, move=None, parent=None):
        self.board = board
        self.color = color  # Color whose turn it is at this node
        self.move = move
        self.parent = parent
        self.children = []
        self.wins = 0
        self.visits = 0
        self.untried_moves = get_legal_moves(board, color)

    def uct_score(self, c=1.414):
        if self.visits == 0:
            return math.inf
        return (self.wins / self.visits) + c * math.sqrt(math.log(self.parent.visits) / self.visits)

    def select_child(self):
        return max(self.children, key=lambda n: n.uct_score())

    def expand(self):
        move = self.untried_moves.pop(random.randrange(len(self.untried_moves)))
        nb = apply_move(self.board, move)
        next_color = BLACK if self.color == WHITE else WHITE
        child = MCTSNode(nb, next_color, move=move, parent=self)
        self.children.append(child)
        return child

    def is_fully_expanded(self):
        return len(self.untried_moves) == 0

    def is_terminal(self):
        return check_winner(self.board, self.color) is not None or not get_legal_moves(self.board, self.color)

def rollout(board, color, ai_color):
    cur_board = copy.deepcopy(board)
    cur_color = color
    max_steps = 60
    for _ in range(max_steps):
        winner = check_winner(cur_board, WHITE if cur_color == BLACK else BLACK)
        if winner is not None:
            return 1 if winner == ai_color else 0
        moves = get_legal_moves(cur_board, cur_color)
        if not moves:
            return 0
        move = random.choice(moves)
        cur_board = apply_move(cur_board, move)
        cur_color = BLACK if cur_color == WHITE else WHITE
    # Draw — partial credit
    return 0.5

def backpropagate(node, result):
    while node is not None:
        node.visits += 1
        node.wins += result
        result = 1 - result  # Flip perspective
        node = node.parent

def mcts_move(board, ai_color, human_color, iterations):
    root = MCTSNode(board, ai_color)
    if not root.untried_moves:
        return None

    for _ in range(iterations):
        node = root

        # Selection
        while node.is_fully_expanded() and node.children and not node.is_terminal():
            node = node.select_child()

        # Expansion
        if not node.is_terminal() and node.untried_moves:
            node = node.expand()

        # Rollout
        result = rollout(node.board, node.color, ai_color)

        # Backpropagation
        backpropagate(node, result)

    if not root.children:
        moves = get_legal_moves(board, ai_color)
        return random.choice(moves) if moves else None

    best = max(root.children, key=lambda n: n.visits)
    return best.move