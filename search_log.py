import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
import threading


class LogSearchApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cruz's Log File Search")
        self.geometry("900x700")
        
        # Theme configuration
        self.dark_mode = False
        self.themes = {
            'light': {
                'bg': '#ffffff',
                'fg': '#000000',
                'select_bg': '#0078d4',
                'select_fg': '#ffffff',
                'entry_bg': '#ffffff',
                'entry_fg': '#000000',
                'button_bg': '#e1e1e1',
                'button_fg': '#000000',
                'text_bg': '#f0f0f0',
                'text_fg': '#000000',
                'highlight': '#ffff00',
                'current_highlight': '#ffa500',
                'find_bg': '#f0f0f0',
                'status_bg': '#f0f0f0'
            },
            'dark': {
                'bg': '#2d2d2d',
                'fg': '#ffffff',
                'select_bg': '#0078d4',
                'select_fg': '#ffffff',
                'entry_bg': '#404040',
                'entry_fg': '#ffffff',
                'button_bg': '#505050',
                'button_fg': '#ffffff',
                'text_bg': '#1e1e1e',
                'text_fg': '#ffffff',
                'highlight': '#ffff00',
                'current_highlight': '#ffa500',
                'find_bg': '#404040',
                'status_bg': '#404040'
            }
        }
        
        self.dropped_path = ""
        self.search_matches = []
        self.current_match_index = -1
        self.search_frame = None
        self.find_entry = None
        self.search_thread = None
        self.stop_search = False

        self.setup_style()
        self.create_widgets()
        self.bind_events()
        self.apply_theme()

    def setup_style(self):
        """Configure ttk styles for modern appearance"""
        self.style = ttk.Style()
        
        # Configure styles for light theme initially
        self.configure_light_theme()

    def configure_light_theme(self):
        """Configure styles for light theme"""
        self.style.theme_use('clam')
        
        # Configure scrollbar
        self.style.configure("Vertical.TScrollbar",
                           background="#e1e1e1",
                           troughcolor="#f0f0f0",
                           bordercolor="#d0d0d0",
                           arrowcolor="#666666",
                           darkcolor="#e1e1e1",
                           lightcolor="#ffffff")
        
        # Configure progressbar
        self.style.configure("TProgressbar",
                           background="#0078d4",
                           troughcolor="#e1e1e1",
                           borderwidth=0,
                           lightcolor="#0078d4",
                           darkcolor="#0078d4")

    def configure_dark_theme(self):
        """Configure styles for dark theme"""
        self.style.theme_use('clam')
        
        # Configure scrollbar for dark theme
        self.style.configure("Vertical.TScrollbar",
                           background="#505050",
                           troughcolor="#2d2d2d",
                           bordercolor="#404040",
                           arrowcolor="#ffffff",
                           darkcolor="#505050",
                           lightcolor="#606060")
        
        # Configure progressbar for dark theme
        self.style.configure("TProgressbar",
                           background="#0078d4",
                           troughcolor="#404040",
                           borderwidth=0,
                           lightcolor="#0078d4",
                           darkcolor="#0078d4")

    def create_widgets(self):
        # Main container
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Header frame with dark mode toggle
        self.header_frame = tk.Frame(self.main_frame)
        self.header_frame.pack(fill="x", pady=(0, 10))
        
        self.drop_label = tk.Label(
            self.header_frame,
            text="📂 Drag & drop a folder or a .log/.txt/.logcat file below:",
            font=("Segoe UI", 12),
        )
        self.drop_label.pack(side="left")
        
        # Dark mode toggle button
        self.theme_button = tk.Button(
            self.header_frame,
            text="🌙 Dark Mode",
            command=self.toggle_theme,
            font=("Segoe UI", 9),
            relief="flat",
            bd=1
        )
        self.theme_button.pack(side="right")

        # File path entry
        self.drop_entry = tk.Entry(self.main_frame, width=100, font=("Segoe UI", 10))
        self.drop_entry.pack(pady=5, fill="x")
        self.drop_entry.drop_target_register(DND_FILES)
        self.drop_entry.dnd_bind("<<Drop>>", self.on_drop)

        # Search section
        self.search_frame_container = tk.Frame(self.main_frame)
        self.search_frame_container.pack(pady=10)
        
        self.keyword_label = tk.Label(
            self.search_frame_container,
            text="🔍 Enter keyword to search:",
            font=("Segoe UI", 11),
        )
        self.keyword_label.pack()

        self.keyword_entry = tk.Entry(self.search_frame_container, width=50, font=("Segoe UI", 10))
        self.keyword_entry.pack(pady=5)
        self.keyword_entry.bind("<Return>", lambda e: self.search_logs())

        self.search_button = tk.Button(
            self.search_frame_container,
            text="Search",
            command=self.search_logs,
            font=("Segoe UI", 10),
            relief="flat",
            bd=1,
            padx=20,
            pady=5
        )
        self.search_button.pack(pady=5)

        # Results section with scrollbars
        self.results_frame = tk.Frame(self.main_frame)
        self.results_frame.pack(padx=10, pady=10, expand=True, fill="both")

        # Text widget with scrollbars
        self.text_frame = tk.Frame(self.results_frame)
        self.text_frame.pack(expand=True, fill="both")
        
        self.result_text = tk.Text(
            self.text_frame, 
            wrap="word", 
            font=("Consolas", 10),
            relief="flat",
            bd=1,
            padx=10,
            pady=10
        )
        
        # Vertical scrollbar
        self.v_scrollbar = ttk.Scrollbar(self.text_frame, orient="vertical", command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=self.v_scrollbar.set)
        
        # Grid layout for text and vertical scrollbar only
        self.result_text.grid(row=0, column=0, sticky="nsew")
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        
        self.text_frame.grid_rowconfigure(0, weight=1)
        self.text_frame.grid_columnconfigure(0, weight=1)

        # Status bar
        self.status_frame = tk.Frame(self.main_frame, relief="sunken", bd=1)
        self.status_frame.pack(fill="x", pady=(5, 0))
        
        self.status_label = tk.Label(
            self.status_frame,
            text="Ready",
            font=("Segoe UI", 9),
            anchor="w"
        )
        self.status_label.pack(side="left", padx=5, pady=2)
        
        # Progress bar (initially hidden)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.status_frame,
            variable=self.progress_var,
            mode='determinate',
            length=200
        )

        # Configure text highlighting tags
        self.result_text.tag_configure("highlight", foreground="black")
        self.result_text.tag_configure("current_highlight", foreground="black")

    def bind_events(self):
        # Bind Ctrl+F for find functionality
        self.bind("<Control-f>", self.show_find_dialog)
        self.result_text.bind("<Control-f>", self.show_find_dialog)
        
        # Bind mouse wheel to text widget
        self.result_text.bind("<MouseWheel>", self.on_mousewheel)

    def on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        self.result_text.yview_scroll(int(-1*(event.delta/120)), "units")

    def toggle_theme(self):
        """Toggle between light and dark themes"""
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            self.configure_dark_theme()
            self.theme_button.config(text="☀️ Light Mode")
        else:
            self.configure_light_theme()
            self.theme_button.config(text="🌙 Dark Mode")
        self.apply_theme()

    def apply_theme(self):
        """Apply the current theme to all widgets"""
        theme = self.themes['dark' if self.dark_mode else 'light']
        
        # Main window
        self.configure(bg=theme['bg'])
        
        # Frames
        for frame in [self.main_frame, self.header_frame, self.search_frame_container, 
                     self.results_frame, self.text_frame]:
            frame.configure(bg=theme['bg'])
        
        # Labels
        for label in [self.drop_label, self.keyword_label, self.status_label]:
            label.configure(bg=theme['bg'], fg=theme['fg'])
        
        # Entries
        for entry in [self.drop_entry, self.keyword_entry]:
            entry.configure(bg=theme['entry_bg'], fg=theme['entry_fg'], 
                          insertbackground=theme['fg'], selectbackground=theme['select_bg'])
        
        # Buttons
        for button in [self.search_button, self.theme_button]:
            button.configure(bg=theme['button_bg'], fg=theme['button_fg'],
                           activebackground=theme['select_bg'], activeforeground=theme['select_fg'])
        
        # Text widget
        self.result_text.configure(bg=theme['text_bg'], fg=theme['text_fg'],
                                 insertbackground=theme['fg'], selectbackground=theme['select_bg'])
        
        # Status frame
        self.status_frame.configure(bg=theme['status_bg'])
        
        # Update highlighting colors
        self.result_text.tag_configure("highlight", background=theme['highlight'])
        self.result_text.tag_configure("current_highlight", background=theme['current_highlight'])
        
        # Update find dialog colors if it exists
        if self.search_frame:
            self.update_find_dialog_theme()

    def update_find_dialog_theme(self):
        """Update find dialog theme"""
        theme = self.themes['dark' if self.dark_mode else 'light']
        
        self.search_frame.configure(bg=theme['find_bg'])
        
        # Update all widgets in search frame
        for widget in self.search_frame.winfo_children():
            if isinstance(widget, tk.Label):
                widget.configure(bg=theme['find_bg'], fg=theme['fg'])
            elif isinstance(widget, tk.Entry):
                widget.configure(bg=theme['entry_bg'], fg=theme['entry_fg'],
                               insertbackground=theme['fg'])
            elif isinstance(widget, tk.Button):
                widget.configure(bg=theme['button_bg'], fg=theme['button_fg'])

    def update_status(self, message, show_progress=False, progress_value=0):
        """Update status bar message and progress"""
        self.status_label.config(text=message)
        
        if show_progress:
            if not self.progress_bar.winfo_ismapped():
                self.progress_bar.pack(side="right", padx=5, pady=2)
            self.progress_var.set(progress_value)
        else:
            if self.progress_bar.winfo_ismapped():
                self.progress_bar.pack_forget()
        
        self.update_idletasks()

    def show_find_dialog(self, event=None):
        if self.search_frame:
            self.search_frame.destroy()

        # Create find dialog frame
        theme = self.themes['dark' if self.dark_mode else 'light']
        self.search_frame = tk.Frame(self.main_frame, bg=theme['find_bg'], relief="raised", bd=1)
        self.search_frame.pack(fill="x", padx=5, pady=2)

        tk.Label(self.search_frame, text="Find:", bg=theme['find_bg'], 
                fg=theme['fg'], font=("Segoe UI", 9)).pack(side="left", padx=5)
        
        self.find_entry = tk.Entry(self.search_frame, width=30, font=("Segoe UI", 9),
                                 bg=theme['entry_bg'], fg=theme['entry_fg'])
        self.find_entry.pack(side="left", padx=5)
        self.find_entry.bind("<KeyRelease>", self.on_find_text_change)
        self.find_entry.bind("<Return>", self.find_next)
        self.find_entry.bind("<Escape>", self.hide_find_dialog)

        # Navigation buttons
        self.prev_button = tk.Button(
            self.search_frame, text="Previous", command=self.find_previous,
            bg=theme['button_bg'], fg=theme['button_fg'], font=("Segoe UI", 8), 
            state="disabled", relief="flat"
        )
        self.prev_button.pack(side="left", padx=2)

        self.next_button = tk.Button(
            self.search_frame, text="Next", command=self.find_next,
            bg=theme['button_bg'], fg=theme['button_fg'], font=("Segoe UI", 8), 
            state="disabled", relief="flat"
        )
        self.next_button.pack(side="left", padx=2)

        # Match count label
        self.match_label = tk.Label(
            self.search_frame, text="", bg=theme['find_bg'], 
            fg=theme['fg'], font=("Segoe UI", 8)
        )
        self.match_label.pack(side="left", padx=5)

        # Close button
        close_button = tk.Button(
            self.search_frame, text="✕", command=self.hide_find_dialog,
            bg=theme['button_bg'], fg=theme['button_fg'], font=("Segoe UI", 8), 
            width=2, relief="flat"
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
        self.update_status("File/folder loaded: " + os.path.basename(path))

    def search_logs(self):
        """Start log search in a separate thread"""
        if self.search_thread and self.search_thread.is_alive():
            self.stop_search = True
            return
        
        keyword = self.keyword_entry.get().strip()
        self.result_text.delete("1.0", tk.END)
        
        # Clear find dialog if open
        if self.search_frame:
            self.hide_find_dialog()

        if not self.dropped_path or not keyword:
            messagebox.showwarning("Missing Info", "Please drop a file/folder and enter a keyword.")
            return

        self.stop_search = False
        self.search_button.config(text="Cancel", state="normal")
        self.search_thread = threading.Thread(target=self._search_logs_threaded, args=(keyword,))
        self.search_thread.start()

    def _search_logs_threaded(self, keyword):
        """Threaded log search function"""
        try:
            matched = False
            total_files = 0
            processed_files = 0
            
            # Count total files first for progress tracking
            if os.path.isdir(self.dropped_path):
                for root, _, files in os.walk(self.dropped_path):
                    for file in files:
                        if (file.lower().endswith((".log", ".txt", ".syslog"))
                            or file.lower().startswith("logcat.")
                            or file.lower() == "logcat"):
                            total_files += 1
            else:
                total_files = 1
            
            self.after(0, self.update_status, f"Searching in {total_files} files...", True, 0)
            
            if os.path.isdir(self.dropped_path):
                for root, _, files in os.walk(self.dropped_path):
                    if self.stop_search:
                        break
                    for file in files:
                        if self.stop_search:
                            break
                        if (file.lower().endswith((".log", ".txt", ".syslog"))
                            or file.lower().startswith("logcat.")
                            or file.lower() == "logcat"):
                            file_path = os.path.join(root, file)
                            matched |= self.search_file(file_path, keyword)
                            processed_files += 1
                            progress = (processed_files / total_files) * 100
                            self.after(0, self.update_status, 
                                     f"Searching... {processed_files}/{total_files}", True, progress)
            elif os.path.isfile(self.dropped_path):
                self.after(0, self.update_status, "Searching file...", True, 0)
                matched = self.search_file(self.dropped_path, keyword)
                self.after(0, self.update_status, "Search complete", True, 100)
            else:
                self.after(0, lambda: self.result_text.insert(tk.END, "Invalid file or folder.\n"))

            if not matched and not self.stop_search:
                self.after(0, lambda: self.result_text.insert(tk.END, "No matches found.\n"))
            
            if self.stop_search:
                self.after(0, self.update_status, "Search cancelled", False)
            else:
                matches_found = self.result_text.get("1.0", tk.END).count("\n") - 1
                self.after(0, self.update_status, f"Search complete - {matches_found} lines found", False)
        
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"Search error: {str(e)}"))
        finally:
            self.after(0, lambda: self.search_button.config(text="Search", state="normal"))

    def search_file(self, file_path, keyword):
        found = False
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                lines = file.readlines()
                for idx, line in enumerate(lines, start=1):
                    if self.stop_search:
                        break
                    if keyword in line:
                        if not found:
                            self.after(0, lambda fp=file_path: 
                                     self.result_text.insert(tk.END, f"\n--- {fp} ---\n"))
                            found = True
                        self.after(0, lambda i=idx, l=line: 
                                 self.result_text.insert(tk.END, f"{i}: {l}"))
        except Exception as e:
            self.after(0, lambda fp=file_path, err=e: 
                     self.result_text.insert(tk.END, f"Error reading {fp}: {err}\n"))
        return found


if __name__ == "__main__":
    app = LogSearchApp()
    app.mainloop()