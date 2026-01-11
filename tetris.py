import random
import time
import tkinter as tk

CELL = 28
COLS = 10
ROWS = 20
MARGIN = 16
PANEL_W = 220
BOARD_W = COLS * CELL
BOARD_H = ROWS * CELL
CANVAS_W = BOARD_W + PANEL_W + MARGIN * 2
CANVAS_H = BOARD_H + MARGIN * 2

BG_COLOR = "#0c0f14"
BOARD_COLOR = "#121823"
GRID_COLOR = "#1e2633"
TEXT_COLOR = "#e8f0ff"
MUTED_TEXT = "#9fb0c8"
ACCENT = "#57c7ff"

SHAPES = [
    ([[1, 1, 1, 1]], "#35c9ff"),
    ([[1, 1], [1, 1]], "#f2d74e"),
    ([[0, 1, 0], [1, 1, 1]], "#b76cff"),
    ([[1, 0, 0], [1, 1, 1]], "#4e7af2"),
    ([[0, 0, 1], [1, 1, 1]], "#f29b4e"),
    ([[0, 1, 1], [1, 1, 0]], "#4ef27a"),
    ([[1, 1, 0], [0, 1, 1]], "#f24e4e"),
]

LINE_SCORES = {1: 100, 2: 300, 3: 500, 4: 800}


def rotate(shape):
    return [list(row) for row in zip(*shape[::-1])]


def shade_color(hex_color, factor):
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    r = max(0, min(255, int(r * factor)))
    g = max(0, min(255, int(g * factor)))
    b = max(0, min(255, int(b * factor)))

    return f"#{r:02x}{g:02x}{b:02x}"


class Tetris:
    def __init__(self, root, on_close=None, owns_root=True):
        self.root = root
        self.on_close = on_close
        self.owns_root = owns_root

        self.root.title("Tetris")
        self.root.resizable(False, False)
        self.canvas = tk.Canvas(
            root,
            width=CANVAS_W,
            height=CANVAS_H,
            bg=BG_COLOR,
            highlightthickness=0,
        )
        self.canvas.pack()
        self.root.focus_set()

        self.offset_x = MARGIN
        self.offset_y = MARGIN
        self.board_x = self.offset_x
        self.board_y = self.offset_y
        self.panel_x = self.offset_x + BOARD_W + 20

        self.grid = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.score = 0
        self.lines = 0
        self.level = 1
        self.game_over = False
        self.running = True
        self.base_interval = 0.55
        self.drop_interval = self.base_interval
        self.soft_drop_interval = 0.05
        self.last_drop = time.monotonic()
        self.soft_drop_active = False

        self.current = self.new_piece()
        self.next_piece = self.new_piece()

        self.overlay = None
        self.bind_inputs()
        self.tick()

        self.root.protocol("WM_DELETE_WINDOW", self.handle_close)

    def bind_inputs(self):
        self.root.bind("<Left>", lambda e: self.move(-1, 0))
        self.root.bind("<Right>", lambda e: self.move(1, 0))
        self.root.bind("<Up>", lambda e: self.rotate_piece())
        self.root.bind("<Escape>", lambda e: self.handle_close())

        self.root.bind("<KeyPress-Down>", self.start_soft_drop)
        self.root.bind("<KeyRelease-Down>", self.stop_soft_drop)

        self.canvas.bind("<Button-1>", lambda e: self.rotate_piece())
        self.canvas.bind("<Button-3>", lambda e: self.hard_drop())
        self.canvas.bind("<B1-Motion>", self.drag_move)

    def handle_close(self):
        if self.on_close:
            self.on_close()
        self.root.destroy()

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

    def start_soft_drop(self, _event):
        self.soft_drop_active = True

    def stop_soft_drop(self, _event):
        self.soft_drop_active = False

    def soft_drop(self):
        if not self.move(0, 1):
            self.lock_piece()

    def hard_drop(self):
        if self.game_over:
            return
        distance = 0
        while self.move(0, 1):
            distance += 1
        self.score += distance * 2
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
            self.end_game()
        else:
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
            self.score += LINE_SCORES.get(cleared, cleared * 200)
            self.level = 1 + self.lines // 10
            self.drop_interval = max(0.08, self.base_interval - (self.level - 1) * 0.05)

    def end_game(self):
        self.game_over = True
        self.running = False
        self.draw()
        self.show_game_over()

    def reset_game(self):
        self.grid = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.score = 0
        self.lines = 0
        self.level = 1
        self.game_over = False
        self.running = True
        self.drop_interval = self.base_interval
        self.last_drop = time.monotonic()
        self.soft_drop_active = False
        self.current = self.new_piece()
        self.next_piece = self.new_piece()
        if self.overlay:
            self.overlay.destroy()
            self.overlay = None
        self.tick()

    def drag_move(self, event):
        if self.game_over:
            return
        if event.x < self.board_x or event.x > self.board_x + BOARD_W:
            return
        piece = self.current
        piece_w = len(piece["shape"][0])
        target_col = (event.x - self.board_x) // CELL
        new_x = int(target_col - piece_w // 2)
        new_x = max(0, min(COLS - piece_w, new_x))
        if not self.collides(piece["shape"], new_x, piece["y"]):
            piece["x"] = new_x
            self.draw()

    def tick(self):
        if not self.running:
            return
        now = time.monotonic()
        interval = self.soft_drop_interval if self.soft_drop_active else self.drop_interval
        if now - self.last_drop >= interval:
            if not self.move(0, 1):
                self.lock_piece()
            self.last_drop = now
        self.draw()
        self.root.after(16, self.tick)

    def get_ghost_y(self):
        piece = self.current
        ghost_y = piece["y"]
        while not self.collides(piece["shape"], piece["x"], ghost_y + 1):
            ghost_y += 1
        return ghost_y

    def draw_block(self, grid_x, grid_y, color, size=CELL):
        x0 = self.board_x + grid_x * size
        y0 = self.board_y + grid_y * size
        x1 = x0 + size
        y1 = y0 + size
        dark = shade_color(color, 0.7)
        light = shade_color(color, 1.25)

        self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline=dark)
        self.canvas.create_line(x0 + 2, y0 + 2, x1 - 2, y0 + 2, fill=light)
        self.canvas.create_line(x0 + 2, y0 + 2, x0 + 2, y1 - 2, fill=light)
        self.canvas.create_line(x0 + 2, y1 - 2, x1 - 2, y1 - 2, fill=dark)
        self.canvas.create_line(x1 - 2, y0 + 2, x1 - 2, y1 - 2, fill=dark)

    def draw_piece(self, shape, x, y, color):
        for r, row in enumerate(shape):
            for c, val in enumerate(row):
                if val:
                    ny = y + r
                    if ny >= 0:
                        self.draw_block(x + c, ny, color)

    def draw_preview(self, shape, color, x, y):
        cell = 16
        box = 4
        width = box * cell
        height = box * cell

        self.canvas.create_rectangle(x, y, x + width, y + height, fill=BOARD_COLOR, outline=GRID_COLOR)
        shape_h = len(shape)
        shape_w = len(shape[0])
        start_x = x + (box - shape_w) * cell // 2
        start_y = y + (box - shape_h) * cell // 2
        for r, row in enumerate(shape):
            for c, val in enumerate(row):
                if val:
                    px = start_x + c * cell
                    py = start_y + r * cell
                    self.canvas.create_rectangle(
                        px,
                        py,
                        px + cell,
                        py + cell,
                        fill=color,
                        outline=shade_color(color, 0.7),
                    )

    def draw_board(self):
        self.canvas.create_rectangle(
            self.board_x,
            self.board_y,
            self.board_x + BOARD_W,
            self.board_y + BOARD_H,
            fill=BOARD_COLOR,
            outline="#2a3649",
            width=2,
        )

        for r in range(ROWS):
            for c in range(COLS):
                x0 = self.board_x + c * CELL
                y0 = self.board_y + r * CELL
                x1 = x0 + CELL
                y1 = y0 + CELL
                self.canvas.create_rectangle(x0, y0, x1, y1, outline=GRID_COLOR)

        for r in range(ROWS):
            for c in range(COLS):
                color = self.grid[r][c]
                if color:
                    self.draw_block(c, r, color)

    def draw_hud(self):
        panel_x = self.panel_x
        self.canvas.create_text(
            panel_x,
            self.offset_y + 10,
            anchor="nw",
            fill=ACCENT,
            text="NEON TETRIS",
            font=("Segoe UI", 16, "bold"),
        )
        self.canvas.create_text(
            panel_x,
            self.offset_y + 45,
            anchor="nw",
            fill=TEXT_COLOR,
            text=f"Score  {self.score}",
            font=("Segoe UI", 12, "bold"),
        )
        self.canvas.create_text(
            panel_x,
            self.offset_y + 68,
            anchor="nw",
            fill=MUTED_TEXT,
            text=f"Lines   {self.lines}",
        )
        self.canvas.create_text(
            panel_x,
            self.offset_y + 90,
            anchor="nw",
            fill=MUTED_TEXT,
            text=f"Level   {self.level}",
        )

        self.canvas.create_text(
            panel_x,
            self.offset_y + 130,
            anchor="nw",
            fill=TEXT_COLOR,
            text="Next",
            font=("Segoe UI", 11, "bold"),
        )
        self.draw_preview(self.next_piece["shape"], self.next_piece["color"], panel_x, self.offset_y + 150)

        self.canvas.create_text(
            panel_x,
            self.offset_y + 240,
            anchor="nw",
            fill=TEXT_COLOR,
            text="Controls",
            font=("Segoe UI", 11, "bold"),
        )
        self.canvas.create_text(
            panel_x,
            self.offset_y + 265,
            anchor="nw",
            fill=MUTED_TEXT,
            text="Arrows: move + rotate",
        )
        self.canvas.create_text(
            panel_x,
            self.offset_y + 285,
            anchor="nw",
            fill=MUTED_TEXT,
            text="Down: soft drop",
        )
        self.canvas.create_text(
            panel_x,
            self.offset_y + 305,
            anchor="nw",
            fill=MUTED_TEXT,
            text="Mouse: L rotate, R drop",
        )
        self.canvas.create_text(
            panel_x,
            self.offset_y + 325,
            anchor="nw",
            fill=MUTED_TEXT,
            text="Drag: slide piece",
        )
        self.canvas.create_text(
            panel_x,
            self.offset_y + 355,
            anchor="nw",
            fill=MUTED_TEXT,
            text="Esc: back to menu",
        )

    def draw(self):
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, CANVAS_W, CANVAS_H, fill=BG_COLOR, outline="")

        self.draw_board()

        if not self.game_over:
            ghost_y = self.get_ghost_y()
            ghost_color = shade_color(self.current["color"], 0.35)
            for r, row in enumerate(self.current["shape"]):
                for c, val in enumerate(row):
                    if val:
                        ny = ghost_y + r
                        if ny >= 0:
                            x0 = self.board_x + (self.current["x"] + c) * CELL
                            y0 = self.board_y + ny * CELL
                            x1 = x0 + CELL
                            y1 = y0 + CELL
                            self.canvas.create_rectangle(x0, y0, x1, y1, outline=ghost_color)

            self.draw_piece(
                self.current["shape"],
                self.current["x"],
                self.current["y"],
                self.current["color"],
            )

        self.draw_hud()

    def show_game_over(self):
        self.overlay = tk.Frame(self.root, bg="#0f1520", bd=2, relief="ridge")
        self.overlay.place(relx=0.5, rely=0.5, anchor="center")

        title = tk.Label(
            self.overlay,
            text="GAME OVER",
            font=("Segoe UI", 16, "bold"),
            fg=ACCENT,
            bg="#0f1520",
        )
        title.pack(padx=20, pady=(18, 6))

        stats = tk.Label(
            self.overlay,
            text=f"Score {self.score}   Lines {self.lines}",
            font=("Segoe UI", 11),
            fg=TEXT_COLOR,
            bg="#0f1520",
        )
        stats.pack(pady=(0, 12))

        btn_frame = tk.Frame(self.overlay, bg="#0f1520")
        btn_frame.pack(pady=(0, 16))

        restart_btn = tk.Button(btn_frame, text="Restart", width=10, command=self.reset_game)
        restart_btn.pack(side="left", padx=6)

        menu_btn = tk.Button(btn_frame, text="Back to Menu", width=12, command=self.handle_close)
        menu_btn.pack(side="left", padx=6)


def main(parent=None, on_close=None):
    if parent is None:
        root = tk.Tk()
        owns_root = True
    else:
        root = tk.Toplevel(parent)
        owns_root = False

    Tetris(root, on_close=on_close, owns_root=owns_root)

    if owns_root:
        root.mainloop()


if __name__ == "__main__":
    main()
