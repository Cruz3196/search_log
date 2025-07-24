import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
import threading
import queue # For thread-safe UI updates

class LogSearchApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cruz's Log File Search")
        self.geometry("900x700")
        self.minsize(600, 500) # Set a minimum size for responsiveness
        
        # Theme configuration
        self.dark_mode = False
        self.themes = {
            'light': {
                'bg': '#f0f0f0', # Lighter background for main window
                'fg': '#333333',
                'select_bg': '#a8d8ff', # Softer blue for selection
                'select_fg': '#000000',
                'entry_bg': '#ffffff',
                'entry_fg': '#000000',
                'button_bg': '#e0e0e0',
                'button_fg': '#333333',
                'text_bg': '#ffffff',
                'text_fg': '#000000',
                'highlight': '#ffff99', # Softer yellow
                'current_highlight': '#ffcc66', # Softer orange
                'find_bg': '#e8e8e8',
                'status_bg': '#e0e0e0',
                'border_color': '#cccccc'
            },
            'dark': {
                'bg': '#2c2c2c',
                'fg': '#e0e0e0',
                'select_bg': '#005f9e',
                'select_fg': '#ffffff',
                'entry_bg': '#3a3a3a',
                'entry_fg': '#e0e0e0',
                'button_bg': '#4a4a4a',
                'button_fg': '#e0e0e0',
                'text_bg': '#1e1e1e',
                'text_fg': '#e0e0e0',
                'highlight': '#808000', # Darker yellow for contrast
                'current_highlight': '#a0522d', # Darker orange
                'find_bg': '#383838',
                'status_bg': '#3a3a3a',
                'border_color': '#4a4a4a'
            }
        }
        
        self.dropped_path = ""
        self.search_matches = []
        self.current_match_index = -1
        self.search_frame = None
        self.find_entry = None
        self.search_thread = None
        self.stop_search = False
        self.ui_update_queue = queue.Queue() # Queue for thread-safe UI updates

        self.setup_style()
        self.create_widgets()
        self.bind_events()
        self.apply_theme()
        self.process_queue() # Start processing UI updates from queue

    def setup_style(self):
        """Configure ttk styles for modern appearance"""
        self.style = ttk.Style()
        self.style.theme_use('clam') # 'clam' theme provides a good base for customization
        
        # General button style
        self.style.configure("TButton", 
                             font=("Segoe UI", 10), 
                             padding=6, 
                             relief="flat", 
                             borderwidth=1)
        self.style.map("TButton", 
                       background=[('active', self.themes['light']['select_bg'])],
                       foreground=[('active', self.themes['light']['select_fg'])])

        # Entry style
        self.style.configure("TEntry", 
                             font=("Segoe UI", 10), 
                             padding=5)

        # Label style
        self.style.configure("TLabel", 
                             font=("Segoe UI", 10))

        # Scrollbar style
        self.style.configure("TScrollbar", 
                             troughcolor=self.themes['light']['bg'], 
                             background=self.themes['light']['button_bg'],
                             bordercolor=self.themes['light']['border_color'],
                             arrowcolor=self.themes['light']['fg'])
        self.style.map("TScrollbar",
                       background=[('active', self.themes['light']['select_bg'])])

        # Progressbar style
        self.style.configure("TProgressbar",
                             background="#0078d4", # A fixed blue for progress
                             troughcolor=self.themes['light']['button_bg'],
                             borderwidth=0)
        
        # Frame style (for consistent background)
        self.style.configure("TFrame", background=self.themes['light']['bg'])


    def configure_light_theme(self):
        """Configure styles for light theme"""
        theme = self.themes['light']
        self.style.configure("TButton", 
                             background=theme['button_bg'], 
                             foreground=theme['button_fg'])
        self.style.map("TButton", 
                       background=[('active', theme['select_bg'])],
                       foreground=[('active', theme['select_fg'])])
        self.style.configure("TEntry", 
                             background=theme['entry_bg'], 
                             foreground=theme['entry_fg'], 
                             fieldbackground=theme['entry_bg'])
        self.style.configure("TLabel", 
                             background=theme['bg'], 
                             foreground=theme['fg'])
        self.style.configure("TScrollbar", 
                             troughcolor=theme['bg'], 
                             background=theme['button_bg'],
                             bordercolor=theme['border_color'],
                             arrowcolor=theme['fg'])
        self.style.map("TScrollbar",
                       background=[('active', theme['select_bg'])])
        self.style.configure("TProgressbar",
                             troughcolor=theme['button_bg'])
        self.style.configure("TFrame", background=theme['bg'])

    def configure_dark_theme(self):
        """Configure styles for dark theme"""
        theme = self.themes['dark']
        self.style.configure("TButton", 
                             background=theme['button_bg'], 
                             foreground=theme['button_fg'])
        self.style.map("TButton", 
                       background=[('active', theme['select_bg'])],
                       foreground=[('active', theme['select_fg'])])
        self.style.configure("TEntry", 
                             background=theme['entry_bg'], 
                             foreground=theme['entry_fg'], 
                             fieldbackground=theme['entry_bg'])
        self.style.configure("TLabel", 
                             background=theme['bg'], 
                             foreground=theme['fg'])
        self.style.configure("TScrollbar", 
                             troughcolor=theme['bg'], 
                             background=theme['button_bg'],
                             bordercolor=theme['border_color'],
                             arrowcolor=theme['fg'])
        self.style.map("TScrollbar",
                       background=[('active', theme['select_bg'])])
        self.style.configure("TProgressbar",
                             troughcolor=theme['button_bg'])
        self.style.configure("TFrame", background=theme['bg'])

    def create_widgets(self):
        # Main container frame
        self.main_frame = ttk.Frame(self, padding="10 10 10 10")
        self.main_frame.pack(fill="both", expand=True)
        self.main_frame.grid_rowconfigure(3, weight=1) # Results frame expands vertically
        self.main_frame.grid_columnconfigure(0, weight=1) # Main column expands horizontally
        
        # Header frame with dark mode toggle and title
        self.header_frame = ttk.Frame(self.main_frame)
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.header_frame.grid_columnconfigure(0, weight=1) # Label takes most space

        self.drop_label = ttk.Label(
            self.header_frame,
            text="📂 Drag & drop a folder or a .log/.txt/.logcat file:",
            font=("Segoe UI", 12, "bold")
        )
        self.drop_label.grid(row=0, column=0, sticky="w")
        
        # Dark mode toggle button
        self.theme_button = ttk.Button(
            self.header_frame,
            text="🌙 Dark Mode",
            command=self.toggle_theme,
            style="TButton"
        )
        self.theme_button.grid(row=0, column=1, sticky="e")

        # File path entry and browse button
        self.file_input_frame = ttk.Frame(self.main_frame)
        self.file_input_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        self.file_input_frame.grid_columnconfigure(0, weight=1) # Entry takes most space

        self.drop_entry = ttk.Entry(self.file_input_frame, font=("Segoe UI", 10))
        self.drop_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.drop_entry.drop_target_register(DND_FILES)
        self.drop_entry.dnd_bind("<<Drop>>", self.on_drop)

        self.browse_button = ttk.Button(
            self.file_input_frame,
            text="Browse...",
            command=self.browse_file_or_folder,
            style="TButton"
        )
        self.browse_button.grid(row=0, column=1, sticky="e")

        # Search section
        self.search_frame_container = ttk.Frame(self.main_frame, padding="10 0 10 10")
        self.search_frame_container.grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)
        self.search_frame_container.grid_columnconfigure(0, weight=1) # Keyword entry expands

        self.keyword_label = ttk.Label(
            self.search_frame_container,
            text="🔍 Enter keyword to search:",
            font=("Segoe UI", 11, "bold")
        )
        self.keyword_label.grid(row=0, column=0, sticky="w", pady=(0, 5))

        self.keyword_entry = ttk.Entry(self.search_frame_container, font=("Segoe UI", 10))
        self.keyword_entry.grid(row=1, column=0, sticky="ew", padx=(0, 5))
        self.keyword_entry.bind("<Return>", lambda e: self.search_logs())

        self.search_button = ttk.Button(
            self.search_frame_container,
            text="Search",
            command=self.search_logs,
            style="TButton"
        )
        self.search_button.grid(row=1, column=1, sticky="e")

        # Results section with scrollbars
        self.results_frame = ttk.Frame(self.main_frame, relief="flat", borderwidth=1)
        self.results_frame.grid(row=3, column=0, columnspan=2, padx=0, pady=0, sticky="nsew")
        self.results_frame.grid_rowconfigure(0, weight=1)
        self.results_frame.grid_columnconfigure(0, weight=1)
        
        self.result_text = tk.Text(
            self.results_frame, 
            wrap="word", 
            font=("Consolas", 10),
            relief="flat", # Text widget itself should be flat, border handled by frame
            bd=0,
            padx=10,
            pady=10
        )
        
        # Vertical scrollbar
        self.v_scrollbar = ttk.Scrollbar(self.results_frame, orient="vertical", command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=self.v_scrollbar.set)
        
        self.result_text.grid(row=0, column=0, sticky="nsew")
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")

        # Status bar
        self.status_frame = ttk.Frame(self.main_frame, relief="flat", borderwidth=1)
        self.status_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        self.status_frame.grid_columnconfigure(0, weight=1) # Status label expands

        self.status_label = ttk.Label(
            self.status_frame,
            text="Ready",
            font=("Segoe UI", 9),
            anchor="w"
        )
        self.status_label.grid(row=0, column=0, sticky="ew", padx=5, pady=2)
        
        # Progress bar (initially hidden)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.status_frame,
            variable=self.progress_var,
            mode='determinate',
            length=200,
            style="TProgressbar"
        )
        self.progress_bar.grid(row=0, column=1, sticky="e", padx=5, pady=2)
        self.progress_bar.grid_remove() # Hide initially

        # Configure text highlighting tags
        self.result_text.tag_configure("highlight", foreground="black") # Background set in apply_theme
        self.result_text.tag_configure("current_highlight", foreground="black") # Background set in apply_theme

    def bind_events(self):
        # Bind Ctrl+F for find functionality
        self.bind("<Control-f>", self.show_find_dialog)
        self.result_text.bind("<Control-f>", self.show_find_dialog)
        
        # Bind mouse wheel to text widget
        self.result_text.bind("<MouseWheel>", self.on_mousewheel)
        self.result_text.bind("<Button-4>", self.on_mousewheel) # For Linux
        self.result_text.bind("<Button-5>", self.on_mousewheel) # For Linux

    def on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        if event.num == 4: # Linux scroll up
            self.result_text.yview_scroll(-1, "units")
        elif event.num == 5: # Linux scroll down
            self.result_text.yview_scroll(1, "units")
        else: # Windows/macOS
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
        
        # Main window background
        self.configure(bg=theme['bg'])
        
        # Apply theme to all ttk frames
        for frame in [self.main_frame, self.header_frame, self.file_input_frame, 
                       self.search_frame_container, self.results_frame, self.status_frame]:
            self.style.configure(frame.winfo_class(), background=theme['bg']) # Update style for the widget class
            frame.configure(style=frame.winfo_class()) # Apply the style

        # Labels
        for label in [self.drop_label, self.keyword_label, self.status_label]:
            label.configure(background=theme['bg'], foreground=theme['fg'])
        
        # Text widget
        self.result_text.configure(bg=theme['text_bg'], fg=theme['text_fg'],
                                   insertbackground=theme['fg'], selectbackground=theme['select_bg'])
        
        # Update highlighting colors (Text widget tags are not ttk styles)
        self.result_text.tag_configure("highlight", background=theme['highlight'], foreground=theme['text_fg'])
        self.result_text.tag_configure("current_highlight", background=theme['current_highlight'], foreground=theme['text_fg'])
        
        # Update find dialog colors if it exists
        if self.search_frame:
            self.update_find_dialog_theme()

    def update_find_dialog_theme(self):
        """Update find dialog theme"""
        theme = self.themes['dark' if self.dark_mode else 'light']
        
        self.search_frame.configure(background=theme['find_bg'])
        
        # Update all widgets in search frame
        for widget in self.search_frame.winfo_children():
            if isinstance(widget, ttk.Label):
                widget.configure(background=theme['find_bg'], foreground=theme['fg'])
            elif isinstance(widget, ttk.Entry):
                widget.configure(background=theme['entry_bg'], foreground=theme['entry_fg'],
                                 fieldbackground=theme['entry_bg'], insertbackground=theme['fg'])
            elif isinstance(widget, ttk.Button):
                widget.configure(background=theme['button_bg'], foreground=theme['button_fg'])

    def update_status(self, message, show_progress=False, progress_value=0):
        """Thread-safe update status bar message and progress"""
        self.ui_update_queue.put(lambda: self._update_status_ui(message, show_progress, progress_value))

    def _update_status_ui(self, message, show_progress, progress_value):
        """Actual UI update for status bar (called from main thread)"""
        self.status_label.config(text=message)
        
        if show_progress:
            self.progress_bar.grid() # Show progress bar
            self.progress_var.set(progress_value)
        else:
            self.progress_bar.grid_remove() # Hide progress bar
        
        self.update_idletasks()

    def process_queue(self):
        """Process UI updates from the queue"""
        try:
            while True:
                callback = self.ui_update_queue.get_nowait()
                callback()
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_queue) # Check queue every 100ms

    def show_find_dialog(self, event=None):
        if self.search_frame:
            self.search_frame.destroy()

        # Create find dialog frame
        theme = self.themes['dark' if self.dark_mode else 'light']
        self.search_frame = ttk.Frame(self.main_frame, style="TFrame", relief="raised", borderwidth=1)
        self.search_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 2), padx=5) # Place it at the top
        self.search_frame.grid_columnconfigure(1, weight=1) # Entry takes most space

        ttk.Label(self.search_frame, text="Find:", style="TLabel").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        
        self.find_entry = ttk.Entry(self.search_frame, width=30, style="TEntry")
        self.find_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.find_entry.bind("<KeyRelease>", self.on_find_text_change)
        self.find_entry.bind("<Return>", self.find_next)
        self.find_entry.bind("<Escape>", self.hide_find_dialog)

        # Navigation buttons
        self.prev_button = ttk.Button(
            self.search_frame, text="Previous", command=self.find_previous,
            style="TButton", state="disabled", width=8
        )
        self.prev_button.grid(row=0, column=2, padx=2, pady=2)

        self.next_button = ttk.Button(
            self.search_frame, text="Next", command=self.find_next,
            style="TButton", state="disabled", width=6
        )
        self.next_button.grid(row=0, column=3, padx=2, pady=2)

        # Match count label
        self.match_label = ttk.Label(
            self.search_frame, text="", style="TLabel"
        )
        self.match_label.grid(row=0, column=4, padx=5, pady=2, sticky="w")

        # Close button
        close_button = ttk.Button(
            self.search_frame, text="✕", command=self.hide_find_dialog,
            style="TButton", width=3
        )
        close_button.grid(row=0, column=5, padx=5, pady=2, sticky="e")

        # Ensure theme is applied to new widgets
        self.update_find_dialog_theme()
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
        self.update_match_navigation() # Update navigation buttons and count

    def highlight_all_matches(self, search_text):
        # Clear previous highlights
        self.clear_highlights()
        self.search_matches = []
        self.current_match_index = -1 # Reset index when re-highlighting
        
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

        # Highlight the first match if any
        if self.search_matches:
            self.current_match_index = 0
            self.highlight_current_match()

    def clear_highlights(self):
        self.result_text.tag_remove("highlight", "1.0", tk.END)
        self.result_text.tag_remove("current_highlight", "1.0", tk.END)
        self.search_matches = []
        self.current_match_index = -1
        if self.search_frame: # Update match label when highlights are cleared
            self.match_label.config(text="")
            self.prev_button.config(state="disabled")
            self.next_button.config(state="disabled")

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
            current_display = self.current_match_index + 1 if self.current_match_index >= 0 else 0
            self.match_label.config(text=f"{current_display} of {match_count}")
            self.prev_button.config(state="normal" if match_count > 1 else "disabled")
            self.next_button.config(state="normal" if match_count > 1 else "disabled")

    def highlight_current_match(self):
        if not self.search_matches or self.current_match_index < 0:
            return

        # Remove previous current highlight
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

        self.current_match_index = (self.current_match_index - 1 + len(self.search_matches)) % len(self.search_matches)
        self.highlight_current_match()
        self.update_match_navigation()

    def on_drop(self, event):
        path = event.data.strip().strip("{}")  # Removes curly braces if path has spaces
        self.dropped_path = path
        self.drop_entry.delete(0, tk.END)
        self.drop_entry.insert(0, path)
        self.update_status("File/folder loaded: " + os.path.basename(path))

    def browse_file_or_folder(self):
        """Allows user to browse for a file or folder"""
        path = filedialog.askopenfilename(
            title="Select a Log File",
            filetypes=[("Log Files", "*.log *.txt *.syslog"), ("All Files", "*.*")]
        )
        if not path: # If no file selected, try folder
            path = filedialog.askdirectory(title="Select a Log Folder")

        if path:
            self.dropped_path = path
            self.drop_entry.delete(0, tk.END)
            self.drop_entry.insert(0, path)
            self.update_status("File/folder loaded: " + os.path.basename(path))

    def search_logs(self):
        """Start log search in a separate thread"""
        if self.search_thread and self.search_thread.is_alive():
            self.stop_search = True
            self.update_status("Cancelling search...", True, self.progress_var.get())
            return
        
        keyword = self.keyword_entry.get().strip()
        self.result_text.delete("1.0", tk.END)
        
        # Clear find dialog if open
        if self.search_frame:
            self.hide_find_dialog()

        if not self.dropped_path or not keyword:
            messagebox.showwarning("Missing Info", "Please drop a file/folder or browse, and enter a keyword.")
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
            elif os.path.isfile(self.dropped_path):
                total_files = 1
            else:
                self.update_status("Invalid file or folder.", False)
                return
            
            self.update_status(f"Searching in {total_files} files...", True, 0)
            
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
                            self.update_status(
                                f"Searching... {processed_files}/{total_files} files", True, progress)
            elif os.path.isfile(self.dropped_path):
                self.update_status("Searching file...", True, 0)
                matched = self.search_file(self.dropped_path, keyword)
                self.update_status("Search complete", True, 100)
            
            if not matched and not self.stop_search:
                self.ui_update_queue.put(lambda: self.result_text.insert(tk.END, "No matches found.\n"))
            
            if self.stop_search:
                self.update_status("Search cancelled", False)
            else:
                matches_found = self.result_text.get("1.0", tk.END).count("\n") - 1 # Exclude the initial blank line
                self.update_status(f"Search complete - {matches_found} lines found", False)
        
        except Exception as e:
            self.ui_update_queue.put(lambda: messagebox.showerror("Error", f"Search error: {str(e)}"))
        finally:
            self.ui_update_queue.put(lambda: self.search_button.config(text="Search", state="normal"))

    def search_file(self, file_path, keyword):
        found = False
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                lines = file.readlines()
                for idx, line in enumerate(lines, start=1):
                    if self.stop_search:
                        break
                    if keyword.lower() in line.lower(): # Case-insensitive search
                        if not found:
                            self.ui_update_queue.put(lambda fp=file_path: 
                                self.result_text.insert(tk.END, f"\n--- {fp} ---\n"))
                            found = True
                        self.ui_update_queue.put(lambda i=idx, l=line: 
                            self.result_text.insert(tk.END, f"{i}: {l}"))
        except Exception as e:
            self.ui_update_queue.put(lambda fp=file_path, err=e: 
                self.result_text.insert(tk.END, f"Error reading {fp}: {err}\n"))
        return found


if __name__ == "__main__":
    app = LogSearchApp()
    app.mainloop()
