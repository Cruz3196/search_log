import os
import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter import filedialog, scrolledtext

class LogSearchApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("Jose Cruz Log Search Tool")
        self.geometry("900x650")

        # Instructions
        tk.Label(self, text="📁 Drag & drop a folder or a .log/.txt/.logcat file below:").pack()

        # Drag-and-drop area
        self.drop_area = tk.Text(self, height=3, width=100)
        self.drop_area.pack(pady=10)
        self.drop_area.drop_target_register(DND_FILES)
        self.drop_area.dnd_bind("<<Drop>>", self.handle_drop)

        # Keyword entry
        tk.Label(self, text="🔍 Enter keyword to search:").pack()
        self.keyword_entry = tk.Entry(self, width=50)
        self.keyword_entry.pack(pady=5)

        # Search button
        tk.Button(self, text="Search", command=self.search_keyword).pack(pady=10)

        # Output area
        self.output_area = scrolledtext.ScrolledText(self, width=150, height=30)
        self.output_area.pack(pady=10)

        # Ctrl+F search
        self.bind_all("<Control-f>", self.open_find_window)

        self.dropped_path = None

    def handle_drop(self, event):
        dropped = event.data.strip('{}')  # Handle Windows paths with spaces
        if os.path.isdir(dropped) or os.path.isfile(dropped):
            self.dropped_path = dropped
            self.drop_area.delete("1.0", tk.END)
            self.drop_area.insert(tk.END, self.dropped_path)
        else:
            self.output_area.insert(tk.END, "❌ Please drop a valid folder or supported log file.\n")

    def search_keyword(self):
        keyword = self.keyword_entry.get().strip()
        if not keyword:
            self.output_area.insert(tk.END, "⚠️ Please enter a keyword.\n")
            return

        if not self.dropped_path:
            self.output_area.insert(tk.END, "⚠️ Please drop a folder or file.\n")
            return

        self.output_area.delete("1.0", tk.END)
        matched = False

        if os.path.isdir(self.dropped_path):
            for root, _, files in os.walk(self.dropped_path):
                for file in files:
                    if self.is_supported_log(file):
                        file_path = os.path.join(root, file)
                        matched |= self.search_file(file_path, keyword)
        elif os.path.isfile(self.dropped_path) and self.is_supported_log(self.dropped_path):
            matched |= self.search_file(self.dropped_path, keyword)

        if not matched:
            self.output_area.insert(tk.END, "✅ No matches found.\n")

    def is_supported_log(self, filename):
        supported_exts = (".log", ".syslog", ".txt", ".logcat")
        name_keywords = ("cv5", "android", "qnx")
        filename_lower = filename.lower()
        return filename_lower.endswith(supported_exts) or any(k in filename_lower for k in name_keywords)

    def search_file(self, file_path, keyword):
        matched = False
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    if keyword in line:
                        matched = True
                        self.output_area.insert(tk.END, f"[{os.path.basename(file_path)}] Line {line_num}: {line}")
        except Exception as e:
            self.output_area.insert(tk.END, f"❌ Error reading {file_path}: {e}\n")
        return matched

    def open_find_window(self, event=None):
        find_window = tk.Toplevel(self)
        find_window.title("Find in Output")
        find_window.geometry("300x80")
        find_window.resizable(False, False)

        tk.Label(find_window, text="🔎 Find:").pack(pady=5)
        find_entry = tk.Entry(find_window, width=30)
        find_entry.pack()
        find_entry.focus()

        def search():
            search_term = find_entry.get()
            self.output_area.tag_remove("highlight", "1.0", tk.END)
            if search_term:
                start_pos = "1.0"
                while True:
                    start_pos = self.output_area.search(search_term, start_pos, stopindex=tk.END)
                    if not start_pos:
                        break
                    end_pos = f"{start_pos}+{len(search_term)}c"
                    self.output_area.tag_add("highlight", start_pos, end_pos)
                    self.output_area.tag_config("highlight", background="yellow")
                    start_pos = end_pos

        find_entry.bind("<Return>", lambda e: search())

if __name__ == "__main__":
    app = LogSearchApp()
    app.mainloop()
