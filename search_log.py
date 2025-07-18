import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD


class LogSearchApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("Log File Keyword Search")
        self.geometry("800x600")
        self.configure(bg="white")

        self.dropped_path = ""

        self.create_widgets()

    def create_widgets(self):
        self.drop_label = tk.Label(
            self,
            text="📂 Drag & drop a folder or a .log/.txt/.logcat file below:",
            bg="white",
            font=("Segoe UI", 12),
        )
        self.drop_label.pack(pady=10)

        self.drop_entry = tk.Entry(self, width=100)
        self.drop_entry.pack(pady=5)
        self.drop_entry.drop_target_register(DND_FILES)
        self.drop_entry.dnd_bind("<<Drop>>", self.on_drop)

        self.keyword_label = tk.Label(
            self,
            text="🔍 Enter keyword to search:",
            bg="white",
            font=("Segoe UI", 11),
        )
        self.keyword_label.pack(pady=10)

        self.keyword_entry = tk.Entry(self, width=50)
        self.keyword_entry.pack()

        self.search_button = tk.Button(
            self,
            text="Search",
            command=self.search_logs,
            bg="#e0e0e0",
            font=("Segoe UI", 10),
        )
        self.search_button.pack(pady=10)

        self.result_text = tk.Text(self, wrap="word", font=("Consolas", 10))
        self.result_text.pack(padx=10, pady=10, expand=True, fill="both")

    def on_drop(self, event):
        path = event.data.strip().strip("{}")  # Removes curly braces if path has spaces
        self.dropped_path = path
        self.drop_entry.delete(0, tk.END)
        self.drop_entry.insert(0, path)

    def search_logs(self):
        keyword = self.keyword_entry.get().strip()
        self.result_text.delete("1.0", tk.END)

        if not self.dropped_path or not keyword:
            messagebox.showwarning("Missing Info", "Please drop a file/folder and enter a keyword.")
            return

        matched = False
        if os.path.isdir(self.dropped_path):
            for root, _, files in os.walk(self.dropped_path):
                for file in files:
                    if (
                        file.lower().endswith((".log", ".txt", ".syslog"))
                        or file.lower().startswith("logcat.")
                        or file.lower() == "logcat"
                    ):
                        file_path = os.path.join(root, file)
                        matched |= self.search_file(file_path, keyword)
        elif os.path.isfile(self.dropped_path):
            matched = self.search_file(self.dropped_path, keyword)
        else:
            self.result_text.insert(tk.END, "Invalid file or folder.\n")

        if not matched:
            self.result_text.insert(tk.END, "No matches found.\n")

    def search_file(self, file_path, keyword):
        found = False
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                lines = file.readlines()
                for idx, line in enumerate(lines, start=1):
                    if keyword in line:
                        if not found:
                            self.result_text.insert(tk.END, f"\n--- {file_path} ---\n")
                            found = True
                        self.result_text.insert(tk.END, f"{idx}: {line}")
        except Exception as e:
            self.result_text.insert(tk.END, f"Error reading {file_path}: {e}\n")
        return found


if __name__ == "__main__":
    app = LogSearchApp()
    app.mainloop()
