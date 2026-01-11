import tkinter as tk
from tkinter import messagebox

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None


def show_popup(title, message):
    messagebox.showinfo(title, message)


def main():
    root = tk.Tk()
    root.title("Game Main Menu")
    root.resizable(False, False)

    bg_path = r"C:\Users\trave\OneDrive\Immagini\asdasd.jpg"
    bg_photo = None

    if Image and ImageTk:
        try:
            img = Image.open(bg_path)
            bg_photo = ImageTk.PhotoImage(img)
            root.geometry(f"{img.width}x{img.height}")
            bg_label = tk.Label(root, image=bg_photo)
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as exc:
            print(f"Background image failed to load: {exc}")
    else:
        print("Pillow is not installed; background image disabled.")

    def restore_menu():
        root.deiconify()
        root.lift()
        root.focus_force()

    def start_game():
        root.withdraw()
        try:
            import tetris

            tetris.main(parent=root, on_close=restore_menu)
        except Exception as exc:
            restore_menu()
            messagebox.showerror("Error", f"Failed to start Tetris: {exc}")

    title_label = tk.Label(
        root,
        text="Main Menu",
        font=("Segoe UI", 16, "bold"),
        bg="#f0f0f0",
    )
    title_label.pack(pady=16)

    button_frame = tk.Frame(root, bg="#f0f0f0")
    button_frame.pack(pady=8)

    buttons = [
        ("Start Game", start_game),
        ("Options", lambda: show_popup("Options", "Options menu coming soon.")),
        ("Credits", lambda: show_popup("Credits", "Made with Python.")),
        ("Help", lambda: show_popup("Help", "Use the menu to navigate.")),
        ("Quit", root.destroy),
    ]

    for text, command in buttons:
        btn = tk.Button(
            button_frame,
            text=text,
            width=18,
            height=2,
            command=command,
        )
        btn.pack(pady=6)

    root.mainloop()


if __name__ == "__main__":
    main()
