import random
import time
import tkinter as tk

CELL = 24
COLS = 10
ROWS = 20
CANVAS_W = COLS * CELL + 180
CANVAS_H = ROWS * CELL + 20

SHAPES = [
    ([[1, 1, 1, 1]], "#35c9ff"),
    ([[1, 1], [1, 1]], "#f2d74e"),
    ([[0, 1, 0], [1, 1, 1]], "#b76cff"),
    ([[1, 0, 0], [1, 1, 1]], "#4e7af2"),
    ([[0, 0, 1], [1, 1, 1]], "#f29b4e"),
    ([[0, 1, 1], [1, 1, 0]], "#4ef27a"),
    ([[1, 1, 0], [0, 1, 1]], "#f24e4e"),
]


def rotate(shape):
    return [list(row) for row in zip(*shape[::-1])]


class Tetris:
    def __init__(self, root):
        self.root = root
        self.root.title("Tetris")
        self.root.resizable(False, False)
        self.canvas = tk.Canvas(root, width=CANVAS_W, height=CANVAS_H, bg="#101010", highlightthickness=0)
        self.canvas.pack()

        self.offset_x = 10
        self.offset_y = 10
        self.grid = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.score = 0
        self.lines = 0
        self.game_over = False
        self.drop_interval = 0.45
        self.last_drop = time.monotonic()

        self.current = self.new_piece()
        self.next_piece = self.new_piece()

        self.bind_inputs()
        self.tick()

    def bind_inputs(self):
        self.root.bind("<Left>", lambda e: self.move(-1, 0))
        self.root.bind("<Right>", lambda e: self.move(1, 0))
        self.root.bind("<Down>", lambda e: self.soft_drop())
        self.root.bind("<Up>", lambda e: self.rotate_piece())
        self.root.bind("<Escape>", lambda e: self.root.destroy())

        self.canvas.bind("<Button-1>", lambda e: self.rotate_piece())
        self.canvas.bind("<Button-3>", lambda e: self.hard_drop())
        self.canvas.bind("<B1-Motion>", self.drag_move)

    def new_piece(self):
        shape, color = random.choice(SHAPES)
        shape = [row[:] for row in shape]
        x = COLS // 2 - len(shape[0]) // 2
        y = -len(shape)
        return {"shape": shape, "color": color, "x": x, "y": y}

    def collides(self, shape, x, y):
        for r, row in enumerate(shape):
            for c, val in enumerate(row):
                if not val:
                    continue
                nx = x + c
                ny = y + r
                if nx < 0 or nx >= COLS or ny >= ROWS:
                    return True
                if ny >= 0 and self.grid[ny][nx]:
                    return True
        return False

    def move(self, dx, dy):
        if self.game_over:
            return False
        piece = self.current
        nx = piece["x"] + dx
        ny = piece["y"] + dy
        if not self.collides(piece["shape"], nx, ny):
            piece["x"] = nx
            piece["y"] = ny
            self.draw()
            return True
        return False

    def rotate_piece(self):
        if self.game_over:
            return
        piece = self.current
        rotated = rotate(piece["shape"])
        if not self.collides(rotated, piece["x"], piece["y"]):
            piece["shape"] = rotated
        else:
            for dx in (-1, 1, -2, 2):
                if not self.collides(rotated, piece["x"] + dx, piece["y"]):
                    piece["x"] += dx
                    piece["shape"] = rotated
                    break
        self.draw()

    def soft_drop(self):
        if not self.move(0, 1):
            self.lock_piece()

    def hard_drop(self):
        if self.game_over:
            return
        while self.move(0, 1):
            pass
        self.lock_piece()

    def lock_piece(self):
        piece = self.current
        for r, row in enumerate(piece["shape"]):
            for c, val in enumerate(row):
                if not val:
                    continue
                nx = piece["x"] + c
                ny = piece["y"] + r
                if ny >= 0:
                    self.grid[ny][nx] = piece["color"]
        self.clear_lines()
        self.current = self.next_piece
        self.next_piece = self.new_piece()
        if self.collides(self.current["shape"], self.current["x"], self.current["y"]):
            self.game_over = True
        self.draw()

    def clear_lines(self):
        new_grid = []
        cleared = 0
        for row in self.grid:
            if all(cell is not None for cell in row):
                cleared += 1
            else:
                new_grid.append(row)
        for _ in range(cleared):
            new_grid.insert(0, [None for _ in range(COLS)])
        if cleared:
            self.grid = new_grid
            self.lines += cleared
            self.score += cleared * 100
            self.drop_interval = max(0.1, 0.45 - self.lines * 0.01)

    def drag_move(self, event):
        if self.game_over:
            return
        piece = self.current
        piece_w = len(piece["shape"][0])
        target_col = (event.x - self.offset_x) // CELL
        new_x = int(target_col - piece_w // 2)
        new_x = max(0, min(COLS - piece_w, new_x))
        if not self.collides(piece["shape"], new_x, piece["y"]):
            piece["x"] = new_x
            self.draw()

    def tick(self):
        now = time.monotonic()
        if not self.game_over and now - self.last_drop >= self.drop_interval:
            if not self.move(0, 1):
                self.lock_piece()
            self.last_drop = now
        self.draw()
        self.root.after(50, self.tick)

    def draw_cell(self, grid_x, grid_y, color):
        x0 = self.offset_x + grid_x * CELL
        y0 = self.offset_y + grid_y * CELL
        x1 = x0 + CELL
        y1 = y0 + CELL
        self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="#242424")

    def draw_piece(self, shape, x, y, color):
        for r, row in enumerate(shape):
            for c, val in enumerate(row):
                if val:
                    ny = y + r
                    if ny >= 0:
                        self.draw_cell(x + c, ny, color)

    def draw(self):
        self.canvas.delete("all")
        board_w = COLS * CELL
        board_h = ROWS * CELL
        self.canvas.create_rectangle(
            self.offset_x,
            self.offset_y,
            self.offset_x + board_w,
            self.offset_y + board_h,
            fill="#171717",
            outline="#2a2a2a",
        )

        for r in range(ROWS):
            for c in range(COLS):
                color = self.grid[r][c]
                if color:
                    self.draw_cell(c, r, color)
                else:
                    x0 = self.offset_x + c * CELL
                    y0 = self.offset_y + r * CELL
                    x1 = x0 + CELL
                    y1 = y0 + CELL
                    self.canvas.create_rectangle(x0, y0, x1, y1, outline="#232323")

        if not self.game_over:
            self.draw_piece(
                self.current["shape"],
                self.current["x"],
                self.current["y"],
                self.current["color"],
            )

        hud_x = self.offset_x + board_w + 20
        self.canvas.create_text(hud_x, 30, anchor="w", fill="#eaeaea", text="Tetris", font=("Segoe UI", 14, "bold"))
        self.canvas.create_text(hud_x, 60, anchor="w", fill="#eaeaea", text=f"Score: {self.score}")
        self.canvas.create_text(hud_x, 80, anchor="w", fill="#eaeaea", text=f"Lines: {self.lines}")
        self.canvas.create_text(hud_x, 120, anchor="w", fill="#bdbdbd", text="Arrows: move/rotate/drop")
        self.canvas.create_text(hud_x, 140, anchor="w", fill="#bdbdbd", text="Mouse: L rotate, R drop")
        self.canvas.create_text(hud_x, 160, anchor="w", fill="#bdbdbd", text="Drag: move piece")
        self.canvas.create_text(hud_x, 180, anchor="w", fill="#bdbdbd", text="Esc: quit")

        if self.game_over:
            self.canvas.create_text(
                self.offset_x + board_w // 2,
                self.offset_y + board_h // 2,
                fill="#f2f2f2",
                text="GAME OVER",
                font=("Segoe UI", 18, "bold"),
            )


def main():
    root = tk.Tk()
    Tetris(root)
    root.mainloop()


if __name__ == "__main__":
    main()
