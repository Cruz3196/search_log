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
        self.search_matches = []
        self.current_match_index = -1
        self.search_frame = None
        self.find_entry = None

        self.create_widgets()
        self.bind_events()

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

        # Configure text highlighting tag
        self.result_text.tag_configure("highlight", background="yellow", foreground="black")
        self.result_text.tag_configure("current_highlight", background="orange", foreground="black")

    def bind_events(self):
        # Bind Ctrl+F for find functionality
        self.bind("<Control-f>", self.show_find_dialog)
        self.result_text.bind("<Control-f>", self.show_find_dialog)

    def show_find_dialog(self, event=None):
        if self.search_frame:
            self.search_frame.destroy()

        # Create find dialog frame
        self.search_frame = tk.Frame(self, bg="lightgray", relief="raised", bd=1)
        self.search_frame.pack(fill="x", padx=5, pady=2)

        tk.Label(self.search_frame, text="Find:", bg="lightgray", font=("Segoe UI", 9)).pack(side="left", padx=5)
        
        self.find_entry = tk.Entry(self.search_frame, width=30, font=("Segoe UI", 9))
        self.find_entry.pack(side="left", padx=5)
        self.find_entry.bind("<KeyRelease>", self.on_find_text_change)
        self.find_entry.bind("<Return>", self.find_next)
        self.find_entry.bind("<Escape>", self.hide_find_dialog)

        # Navigation buttons
        self.prev_button = tk.Button(
            self.search_frame, text="Previous", command=self.find_previous,
            bg="#e0e0e0", font=("Segoe UI", 8), state="disabled"
        )
        self.prev_button.pack(side="left", padx=2)

        self.next_button = tk.Button(
            self.search_frame, text="Next", command=self.find_next,
            bg="#e0e0e0", font=("Segoe UI", 8), state="disabled"
        )
        self.next_button.pack(side="left", padx=2)

        # Match count label
        self.match_label = tk.Label(
            self.search_frame, text="", bg="lightgray", font=("Segoe UI", 8)
        )
        self.match_label.pack(side="left", padx=5)

        # Close button
        close_button = tk.Button(
            self.search_frame, text="✕", command=self.hide_find_dialog,
            bg="#e0e0e0", font=("Segoe UI", 8), width=2
        )
        close_button.pack(side="right", padx=5)

        # Focus on the entry
        self.find_entry.focus_set()

    def hide_find_dialog(self, event=None):
        if self.search_frame:
            self.search_frame.destroy()
            self.search_frame = None
        self.clear_highlights()

    def on_find_text_change(self, event=None):
        search_text = self.find_entry.get()
        if search_text:
            self.highlight_all_matches(search_text)
        else:
            self.clear_highlights()

    def highlight_all_matches(self, search_text):
        # Clear previous highlights
        self.clear_highlights()
        self.search_matches = []
        
        if not search_text:
            return

        # Find all matches
        content = self.result_text.get("1.0", tk.END)
        start_pos = "1.0"
        
        while True:
            pos = self.result_text.search(search_text, start_pos, tk.END, nocase=True)
            if not pos:
                break
            
            end_pos = f"{pos}+{len(search_text)}c"
            self.search_matches.append((pos, end_pos))
            self.result_text.tag_add("highlight", pos, end_pos)
            
            start_pos = end_pos

        # Update UI
        self.update_match_navigation()

    def clear_highlights(self):
        self.result_text.tag_remove("highlight", "1.0", tk.END)
        self.result_text.tag_remove("current_highlight", "1.0", tk.END)
        self.search_matches = []
        self.current_match_index = -1

    def update_match_navigation(self):
        if not self.search_frame:
            return

        match_count = len(self.search_matches)
        
        if match_count == 0:
            self.match_label.config(text="No matches")
            self.prev_button.config(state="disabled")
            self.next_button.config(state="disabled")
            self.current_match_index = -1
        else:
            if self.current_match_index == -1:
                self.current_match_index = 0
                self.highlight_current_match()
            
            current_display = self.current_match_index + 1 if self.current_match_index >= 0 else 0
            self.match_label.config(text=f"{current_display} of {match_count}")
            self.prev_button.config(state="normal" if match_count > 1 else "disabled")
            self.next_button.config(state="normal" if match_count > 1 else "disabled")

    def highlight_current_match(self):
        if not self.search_matches or self.current_match_index < 0:
            return

        # Remove current highlight from all matches
        self.result_text.tag_remove("current_highlight", "1.0", tk.END)
        
        # Add current highlight to the current match
        start_pos, end_pos = self.search_matches[self.current_match_index]
        self.result_text.tag_add("current_highlight", start_pos, end_pos)
        
        # Scroll to the current match
        self.result_text.see(start_pos)

    def find_next(self, event=None):
        if not self.search_matches:
            return

        self.current_match_index = (self.current_match_index + 1) % len(self.search_matches)
        self.highlight_current_match()
        self.update_match_navigation()

    def find_previous(self, event=None):
        if not self.search_matches:
            return

        self.current_match_index = (self.current_match_index - 1) % len(self.search_matches)
        self.highlight_current_match()
        self.update_match_navigation()

    def on_drop(self, event):
        path = event.data.strip().strip("{}")  # Removes curly braces if path has spaces
        self.dropped_path = path
        self.drop_entry.delete(0, tk.END)
        self.drop_entry.insert(0, path)

    def search_logs(self):
        keyword = self.keyword_entry.get().strip()
        self.result_text.delete("1.0", tk.END)
        
        # Clear find dialog if open
        if self.search_frame:
            self.hide_find_dialog()

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