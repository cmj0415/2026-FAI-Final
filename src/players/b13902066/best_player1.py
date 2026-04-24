import random

class BestPlayer1:
    def __init__(self, player_idx):
        self.player_idx = player_idx

    def action(self, hand, history):
        try:
            return self._action_impl(hand, history)
        except Exception:
            # 千萬不要 except BaseException / bare except
            # 發生任何普通錯誤時，至少回傳合法牌
            return hand[0]

    def _action_impl(self, hand, history):
        hand = list(hand)
        if not hand:
            return 1  # 理論上不會發生

        board = history.get("board", [])
        history_matrix = history.get("history_matrix", [])

        # board 防禦性轉換
        board = [list(row) for row in board if len(row) > 0]
        if len(board) != 4:
            return hand[0]

        NUM_SIM = 250

        known = set(hand)

        for row in board:
            for c in row:
                if isinstance(c, int):
                    known.add(c)

        for row in history_matrix:
            if row is None:
                continue
            for c in row:
                if isinstance(c, int) and 1 <= c <= 104:
                    known.add(c)

        unknown_cards = [c for c in range(1, 105) if c not in known]

        best_card = hand[0]
        best_score = float("inf")

        for card in hand:
            total_cost = 0.0

            for _ in range(NUM_SIM):
                k = min(3, len(unknown_cards))
                sampled = random.sample(unknown_cards, k) if k > 0 else []

                played = [(-1, c) for c in sampled]
                played.append((self.player_idx, card))
                played.sort(key=lambda x: x[1])

                sim_board = [row[:] for row in board]
                gained = 0

                for pid, c in played:
                    cost = self._place_card(sim_board, c)
                    if pid == self.player_idx:
                        gained += cost

                total_cost += gained

            avg_cost = total_cost / NUM_SIM
            avg_cost += 0.01 * self._future_risk(card, hand)

            if avg_cost < best_score:
                best_score = avg_cost
                best_card = card

        return best_card

    def _place_card(self, board, card):
        row_ends = [row[-1] for row in board if row]

        if len(row_ends) != 4:
            return 999

        if card < min(row_ends):
            idx = self._choose_row_to_take(board)
            penalty = self._row_penalty(board[idx])
            board[idx] = [card]
            return penalty

        best_idx = None
        best_end = -1

        for i, row in enumerate(board):
            if not row:
                continue
            end = row[-1]
            if end < card and end > best_end:
                best_end = end
                best_idx = i

        if best_idx is None:
            idx = self._choose_row_to_take(board)
            penalty = self._row_penalty(board[idx])
            board[idx] = [card]
            return penalty

        if len(board[best_idx]) >= 5:
            penalty = self._row_penalty(board[best_idx])
            board[best_idx] = [card]
            return penalty

        board[best_idx].append(card)
        return 0

    def _choose_row_to_take(self, board):
        best_idx = 0
        best_key = None

        for i, row in enumerate(board):
            key = (self._row_penalty(row), len(row), i)
            if best_key is None or key < best_key:
                best_key = key
                best_idx = i

        return best_idx

    def _row_penalty(self, row):
        return sum(self._bullheads(c) for c in row if isinstance(c, int))

    def _bullheads(self, card):
        if card == 55:
            return 55
        if card % 11 == 0:
            return 22
        if card % 10 == 0:
            return 10
        if card % 5 == 0:
            return 5
        return 1

    def _future_risk(self, card, hand):
        remaining = [c for c in hand if c != card]

        risk = 0

        if card == min(hand):
            risk += 3

        for c in remaining:
            risk += self._bullheads(c) * 0.2

        return risk