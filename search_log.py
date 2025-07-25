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
        self.geometry("1000x700")
        self.minsize(700, 500)
        
        # Theme configuration - Refined colors for a more modern look
        self.dark_mode = False # Keep dark_mode for menu control
        self.themes = {
            'light': {
                'bg': '#f3f3f3',        # General background (lighter than f0f0f0)
                'fg': '#222222',        # General foreground
                'select_bg': '#cce8ff', # Softer, more modern light blue for selection
                'select_fg': '#000000',
                'entry_bg': '#ffffff',
                'entry_fg': '#000000',
                'button_bg': '#e0e0e0', # Subtle button background
                'button_fg': '#333333',
                'text_bg': '#ffffff',   # Main text background
                'text_fg': '#000000',
                'highlight': '#fffacd', # Softer lemon chiffon for highlight
                'current_highlight': '#ffcc80', # Softer orange for current highlight
                'find_bg': '#e8e8e8',   # Find dialog background
                'status_bg': '#e0e0e0', # Status bar background
                'border_color': '#dcdcdc', # Subtle border for frames
                'line_num_bg': '#f8f8f8', # Background for line numbers (slightly off-white)
                'line_num_fg': '#999999', # Foreground for line numbers (soft grey)
                'separator_bg': '#d0d0d0' # Separator line color
            },
            'dark': {
                'bg': '#252526',        # General background (VS Code dark)
                'fg': '#cccccc',        # General foreground
                'select_bg': '#005f99', # Deeper, richer blue for selection (VS Code blue)
                'select_fg': '#ffffff',
                'entry_bg': '#3c3c3c',  # Entry background
                'entry_fg': '#cccccc',
                'button_bg': '#4e4e4e', # Button background
                'button_fg': '#cccccc',
                'text_bg': '#1e1e1e',   # Main text background (VS Code editor background)
                'text_fg': '#d4d4d4',   # Main text foreground (VS Code editor foreground)
                'highlight': '#5f5f00', # Darker olive for highlight
                'current_highlight': '#e65100', # Deep orange for current highlight
                'find_bg': '#333333',   # Find dialog background
                'status_bg': '#007acc', # VS Code blue for status bar
                'border_color': '#4a4a4a', # Darker border
                'line_num_bg': '#2c2c2c', # Line number background (slightly lighter dark grey)
                'line_num_fg': '#6a6a6a', # Foreground for line numbers
                'separator_bg': '#3a3a3a' # Separator line color
            }
        }
        
        self.dropped_path = ""
        self.search_matches = []
        self.current_match_index = -1
        self.search_frame = None
        self.find_entry = None
        self.search_thread = None
        self.stop_search = False
        self.ui_update_queue = queue.Queue()
        self.current_font_size = 10 

        self.setup_style()
        self.create_menus()
        self.create_widgets()
        self.bind_events()
        self.apply_theme()
        self.process_queue()
        self.display_welcome_message()

    def setup_style(self):
        """Configure ttk styles for modern appearance"""
        self.style = ttk.Style()
        self.style.theme_use('clam') # 'clam' theme provides a good base for customization
        
        # General Button style
        self.style.configure("TButton", 
                             font=("Segoe UI", 10), 
                             padding=6, 
                             relief="flat", # Flat buttons
                             borderwidth=0) # No border
        # Map button colors to current theme colors in apply_theme

        # Entry style
        self.style.configure("TEntry", 
                             font=("Segoe UI", 10), 
                             padding=5,
                             relief="flat", # Flat entry fields
                             borderwidth=1) # Subtle border

        # Label style
        self.style.configure("TLabel", 
                             font=("Segoe UI", 10))

        # Scrollbar style (modern, thin scrollbars)
        self.style.configure("Vertical.TScrollbar", 
                             troughcolor="", # No trough color, blend with background
                             background="#888888", # Default scrollbar thumb color
                             bordercolor="", # No border
                             arrowcolor="#ffffff", # White arrows
                             gripcount=0, # No grip dots
                             relief="flat")
        self.style.map("Vertical.TScrollbar",
                        background=[('active', '#aaaaaa')]) # Darker on hover

        # Progressbar style
        self.style.configure("TProgressbar",
                             background="#0078d4", # A fixed blue for progress
                             troughcolor="#e0e0e0", # Lighter trough
                             borderwidth=0,
                             relief="flat")
        
        # Frame style (for consistent background)
        self.style.configure("TFrame", background=self.themes['light']['bg'])
        self.style.configure("Search.TFrame", background=self.themes['light']['find_bg'], relief="solid", borderwidth=1) # For the find bar
        self.style.configure("Separator.TFrame", background=self.themes['light']['separator_bg']) # Style for separator
        self.style.configure("StatusBar.TFrame", background=self.themes['light']['status_bg'], relief="raised", borderwidth=0)


    def create_menus(self):
        """Creates the application's menu bar and adds the 'View' menu with zoom actions."""
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open File/Folder...", command=self.browse_file_or_folder)
        file_menu.add_command(label="Save Results As...", command=self.save_results_as) # Added Save Results As
        file_menu.add_separator()
        file_menu.add_command(label="Reset", command=self.reset_application_state) # Added Reset
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)

        # View Menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)

        # Theme Submenu (now the primary way to change themes)
        theme_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Theme", menu=theme_menu)
        theme_menu.add_command(label="Light Mode", command=lambda: self.toggle_theme(False))
        theme_menu.add_command(label="Dark Mode", command=lambda: self.toggle_theme(True))


        # Zoom Actions
        view_menu.add_command(label="Zoom In (+)", command=self.zoom_in, accelerator="Ctrl++")
        view_menu.add_command(label="Zoom Out (-)", command=self.zoom_out, accelerator="Ctrl+-")
        view_menu.add_separator()
        view_menu.add_command(label="Reset Zoom (100%)", command=self.reset_zoom, accelerator="Ctrl+0")

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
                             fieldbackground=theme['entry_bg'],
                             bordercolor=theme['border_color'])
        
        self.style.configure("TLabel", 
                             background=theme['bg'], 
                             foreground=theme['fg'])
        
        self.style.configure("Vertical.TScrollbar", 
                             troughcolor=theme['bg'], 
                             background=theme['button_bg'],
                             bordercolor=theme['border_color'],
                             arrowcolor=theme['fg'])
        self.style.map("Vertical.TScrollbar",
                        background=[('active', theme['select_bg'])])
        
        self.style.configure("TProgressbar",
                             troughcolor=theme['button_bg'])
        
        self.style.configure("TFrame", background=theme['bg'])
        self.style.configure("Search.TFrame", background=theme['find_bg'])
        self.style.configure("Separator.TFrame", background=theme['separator_bg'])
        self.style.configure("StatusBar.TFrame", background=theme['status_bg'])


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
                             fieldbackground=theme['entry_bg'],
                             bordercolor=theme['border_color'])
        
        self.style.configure("TLabel", 
                             background=theme['bg'], 
                             foreground=theme['fg'])
        
        self.style.configure("Vertical.TScrollbar", 
                             troughcolor=theme['bg'], 
                             background=theme['button_bg'],
                             bordercolor=theme['border_color'],
                             arrowcolor=theme['fg'])
        self.style.map("Vertical.TScrollbar",
                        background=[('active', theme['select_bg'])])
        
        self.style.configure("TProgressbar",
                             troughcolor=theme['button_bg'])
        
        self.style.configure("TFrame", background=theme['bg'])
        self.style.configure("Search.TFrame", background=theme['find_bg'])
        self.style.configure("Separator.TFrame", background=theme['separator_bg'])
        self.style.configure("StatusBar.TFrame", background=theme['status_bg'])


    def create_widgets(self):
        # Main container frame (consistent padding)
        # Using .grid() for main_frame as well, to allow the find_frame to be gridded at row 0
        # If main_frame was .packed(), and find_frame was .gridded() into the root, it creates issues.
        self.main_frame = ttk.Frame(self, padding="10 10 10 10", style="TFrame")
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0) # Use grid for main_frame
        self.grid_rowconfigure(0, weight=1) # Let main_frame expand in root
        self.grid_columnconfigure(0, weight=1) # Let main_frame expand in root

        self.main_frame.grid_rowconfigure(3, weight=1) # Results frame expands vertically
        self.main_frame.grid_columnconfigure(0, weight=1) # Main column expands horizontally
        
        # Header frame with title only (no dark mode toggle button)
        self.header_frame = ttk.Frame(self.main_frame, style="TFrame")
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.header_frame.grid_columnconfigure(0, weight=1) 

        self.drop_label = ttk.Label(
            self.header_frame,
            text="📂 Drag & drop a folder or a .log/.txt/.logcat file:",
            font=("Segoe UI", 12, "bold"),
            style="TLabel"
        )
        self.drop_label.grid(row=0, column=0, sticky="w")
        
        # File path entry (no browse button next to it)
        self.file_input_frame = ttk.Frame(self.main_frame, style="TFrame")
        self.file_input_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        self.file_input_frame.grid_columnconfigure(0, weight=1)

        self.drop_entry = ttk.Entry(self.file_input_frame, font=("Segoe UI", 10), style="TEntry")
        self.drop_entry.grid(row=0, column=0, sticky="ew", padx=(0, 0))
        self.drop_entry.drop_target_register(DND_FILES)
        self.drop_entry.dnd_bind("<<Drop>>", self.on_drop)

        # Search section
        self.search_frame_container = ttk.Frame(self.main_frame, padding="10 0 10 10", style="TFrame")
        self.search_frame_container.grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)
        self.search_frame_container.grid_columnconfigure(0, weight=1)

        self.keyword_label = ttk.Label(
            self.search_frame_container,
            text="🔍 Enter keyword to search (or leave blank to open file):",
            font=("Segoe UI", 11, "bold"),
            style="TLabel"
        )
        self.keyword_label.grid(row=0, column=0, sticky="w", pady=(0, 5))

        self.keyword_entry = ttk.Entry(self.search_frame_container, font=("Segoe UI", 10), style="TEntry")
        self.keyword_entry.grid(row=1, column=0, sticky="ew", padx=(0, 5))
        self.keyword_entry.bind("<Return>", lambda e: self.search_logs())

        self.search_button = ttk.Button(
            self.search_frame_container,
            text="Search",
            command=self.search_logs,
            style="TButton"
        )
        self.search_button.grid(row=1, column=1, sticky="e")

        # Results section with scrollbars and line numbers
        self.results_frame = ttk.Frame(self.main_frame, style="TFrame", relief="solid", borderwidth=1)
        self.results_frame.grid(row=3, column=0, columnspan=2, padx=0, pady=0, sticky="nsew")
        self.results_frame.grid_rowconfigure(0, weight=1)
        self.results_frame.grid_columnconfigure(0, weight=0)
        self.results_frame.grid_columnconfigure(1, weight=0)
        self.results_frame.grid_columnconfigure(2, weight=1)

        self.linenumbers = tk.Text(
            self.results_frame,
            width=4,
            padx=5,
            pady=10,
            font=("Consolas", self.current_font_size),
            relief="flat",
            bd=0,
            state="disabled",
            wrap="none"
        )
        self.linenumbers.grid(row=0, column=0, sticky="ns")

        self.separator_line = ttk.Frame(self.results_frame, width=1, style="Separator.TFrame")
        self.separator_line.grid(row=0, column=1, sticky="ns")

        self.result_text = tk.Text(
            self.results_frame, 
            wrap="word", 
            font=("Consolas", self.current_font_size),
            relief="flat", 
            bd=0,
            padx=10,
            pady=10
        )
        
        self.v_scrollbar = ttk.Scrollbar(self.results_frame, orient="vertical", command=self._sync_scroll, style="Vertical.TScrollbar")
        self.result_text.configure(yscrollcommand=self.v_scrollbar.set)
        
        self.result_text.grid(row=0, column=2, sticky="nsew")
        self.v_scrollbar.grid(row=0, column=3, sticky="ns")

        # Status bar
        self.status_frame = ttk.Frame(self.main_frame, style="StatusBar.TFrame", relief="flat", borderwidth=0)
        self.status_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        self.status_frame.grid_columnconfigure(0, weight=1)

        self.status_label = ttk.Label(
            self.status_frame,
            text="Ready",
            font=("Segoe UI", 9),
            anchor="w",
            style="TLabel"
        )
        self.status_label.grid(row=0, column=0, sticky="ew", padx=5, pady=2)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.status_frame,
            variable=self.progress_var,
            mode='determinate',
            length=200,
            style="TProgressbar"
        )
        self.progress_bar.grid(row=0, column=1, sticky="e", padx=5, pady=2)
        self.progress_bar.grid_remove()

        self.result_text.tag_configure("highlight", foreground="black")
        self.result_text.tag_configure("current_highlight", foreground="black")

    def bind_events(self):
        self.bind("<Control-f>", self.show_find_dialog)
        self.result_text.bind("<Control-f>", self.show_find_dialog)
        
        self.result_text.bind("<MouseWheel>", self.on_mousewheel)
        self.result_text.bind("<Button-4>", self.on_mousewheel)
        self.result_text.bind("<Button-5>", self.on_mousewheel)

        self.result_text.bind("<<ContentChanged>>", lambda e: self.after_idle(self._update_line_numbers))
        self.result_text.bind("<KeyRelease>", lambda e: self.result_text.event_generate("<<ContentChanged>>"))
        self.result_text.bind("<<Paste>>", lambda e: self.result_text.event_generate("<<ContentChanged>>"))
        self.result_text.bind("<<Cut>>", lambda e: self.result_text.event_generate("<<ContentChanged>>"))
        self.result_text.bind("<Configure>", lambda e: self.after_idle(self._update_line_numbers))

        self.bind("<Control-plus>", self.zoom_in)
        self.bind("<Control-equal>", self.zoom_in)
        self.bind("<Control-minus>", self.zoom_out)
        self.bind("<Control-0>", self.reset_zoom)

    def zoom_in(self, event=None):
        if self.current_font_size < 30:
            self.current_font_size += 1
            self._update_font_size()

    def zoom_out(self, event=None):
        if self.current_font_size > 8:
            self.current_font_size -= 1
            self._update_font_size()

    def reset_zoom(self, event=None):
        self.current_font_size = 10
        self._update_font_size()

    def _update_font_size(self):
        self.result_text.config(font=("Consolas", self.current_font_size))
        self.linenumbers.config(font=("Consolas", self.current_font_size))
        self._update_line_numbers()


    def _sync_scroll(self, *args):
        self.result_text.yview(*args)
        self.linenumbers.yview(*args)
        self.after_idle(self._update_line_numbers)


    def _update_line_numbers(self):
        theme = self.themes['dark' if self.dark_mode else 'light']
        self.linenumbers.config(state="normal")
        self.linenumbers.delete("1.0", tk.END)

        content = self.result_text.get("1.0", "end-1c") 
        total_lines = content.count('\n') + 1 if content else 0

        line_numbers_text = ""
        if total_lines > 0:
            num_digits = len(str(total_lines))
            self.linenumbers.config(width=max(4, num_digits + 1)) 

            for i in range(1, total_lines + 1):
                line_numbers_text += f"{i}\n"
        else:
            self.linenumbers.config(width=4) 
        
        self.linenumbers.insert("1.0", line_numbers_text)

        self.linenumbers.tag_configure("line", 
                                       justify='right', 
                                       foreground=theme['line_num_fg'], 
                                       background=theme['line_num_bg'])
        self.linenumbers.tag_add("line", "1.0", "end")
        
        self.linenumbers.yview_moveto(self.result_text.yview()[0])
        self.linenumbers.config(state="disabled")

    def _reset_line_numbers(self):
        self.linenumbers.config(state="normal")
        self.linenumbers.delete("1.0", tk.END)
        self.linenumbers.config(state="disabled")
        self.linenumbers.yview_moveto(0)

    def on_mousewheel(self, event):
        if event.num == 4:
            self._sync_scroll("scroll", -1, "units")
        elif event.num == 5:
            self._sync_scroll("scroll", 1, "units")
        else:
            self._sync_scroll("scroll", int(-1*(event.delta/120)), "units")

    def toggle_theme(self, force_dark=None):
        if force_dark is not None:
            self.dark_mode = force_dark
        else:
            self.dark_mode = not self.dark_mode
            
        if self.dark_mode:
            self.configure_dark_theme()
        else:
            self.configure_light_theme()
        self.apply_theme()
        self._update_line_numbers()

    def apply_theme(self):
        theme = self.themes['dark' if self.dark_mode else 'light']
        
        self.configure(bg=theme['bg'])
        
        # Apply theme to all ttk frames (iterate through widgets to apply styles)
        # Ensure 'Search.TFrame' is explicitly handled if it exists
        for frame in [self.main_frame, self.header_frame, self.file_input_frame, 
                      self.search_frame_container, self.results_frame]:
            frame.configure(style="TFrame") # Reapply TFrame style
        
        # Specific frame styles
        self.status_frame.configure(style="StatusBar.TFrame")
        self.separator_line.configure(style="Separator.TFrame")
        if self.search_frame: # Only apply if search_frame exists
            self.search_frame.configure(style="Search.TFrame")


        # Labels
        for label in [self.drop_label, self.keyword_label, self.status_label]:
            label.configure(background=theme['bg'], foreground=theme['fg'])
        
        # Text widget
        self.result_text.configure(bg=theme['text_bg'], fg=theme['text_fg'],
                                   insertbackground=theme['fg'], selectbackground=theme['select_bg'])
        
        # Line numbers widget
        self.linenumbers.configure(bg=theme['line_num_bg'], fg=theme['line_num_fg'],
                                   insertbackground=theme['line_num_fg'], selectbackground=theme['select_bg'])
        self.linenumbers.tag_configure("line", 
                                       foreground=theme['line_num_fg'], 
                                       background=theme['line_num_bg'])

        # Update highlighting colors
        self.result_text.tag_configure("highlight", background=theme['highlight'], foreground=theme['text_fg'])
        self.result_text.tag_configure("current_highlight", background=theme['current_highlight'], foreground=theme['text_fg'])
        
        # Update find dialog colors if it exists
        if self.search_frame:
            self.update_find_dialog_theme()

    def update_find_dialog_theme(self):
        """Update find dialog theme"""
        theme = self.themes['dark' if self.dark_mode else 'light']
        
        self.search_frame.configure(style="Search.TFrame") # Apply specific style for search frame
        
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
            self.progress_bar.grid()
            self.progress_var.set(progress_value)
        else:
            self.progress_bar.grid_remove()
        
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
            self.after(100, self.process_queue)

    def display_welcome_message(self):
        """Displays a welcome message with instructions in the result_text area."""
        welcome_text = """
Welcome to Cruz's Log File Search!

Here's how to use this application:

1.  **Select a File/Folder:**
    * **Drag & Drop:** Drag a log file (.log, .txt, .syslog, logcat) or a folder containing log files directly onto the "Drag & drop" entry field above.
    * **Menu:** Use the "File" menu -> "Open File/Folder..." to manually select a file or folder.

2.  **Search for a Keyword:**
    * Enter the text you want to find in the "Enter keyword to search" field.
    * Click the "Search" button or press Enter.
    * The results will show matching lines from the selected file(s), along with 5 lines before and 5 lines after each match for context.

3.  **Open a File (No Search):**
    * If you select a single file and leave the "Enter keyword to search" field blank, clicking "Search" will simply open and display the entire content of that file.

4.  **In-Text Find (Ctrl+F):**
    * Once content is displayed, press `Ctrl+F` to open a find bar at the top.
    * Type your search term, and navigate through matches using "Previous" and "Next" buttons.

5.  **Toggle Theme:**
    * Use the "View" menu -> "Theme" to switch between Light and Dark modes.

6.  **Zoom In/Out:**
    * Use the "View" menu at the top, then select "Zoom In (+)", "Zoom Out (-)", or "Reset Zoom (100%)".
    * Alternatively, press `Ctrl` + `+` (or `Ctrl` + `=`) to zoom in, `Ctrl` + `-` to zoom out, and `Ctrl` + `0` (zero) to reset zoom to default.

7.  **Reset Application:**
    * Go to "File" menu -> "Reset" to clear all inputs, results, and reset the application to its initial state.

8.  **Save Results:**
    * Go to "File" menu -> "Save Results As..." to save the content currently displayed in the results area to a text file.

Enjoy searching your logs!
"""
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, welcome_text)
        self._update_line_numbers()
        self.result_text.see("1.0")


    def show_find_dialog(self, event=None):
        if self.search_frame:
            # If already open, just focus the entry
            self.find_entry.focus_set()
            return

        # Create find dialog frame within main_frame
        self.search_frame = ttk.Frame(self.main_frame, style="Search.TFrame")
        # Place it at row 0 of main_frame's grid, pushing other content down
        self.search_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 2), padx=5) 
        
        # Shift existing content in main_frame down by one row
        # Iterate through relevant widgets and move them down one row
        # This is the crucial part to make the find bar appear 'on top'
        
        # Need to temporarily ungrid all widgets below row 0, then re-grid them
        # one row lower. This is a bit manual but necessary for a precise layout.
        
        # Store current widget positions and move them
        widgets_to_move = [
            (self.header_frame, 1), # Original row 0, moves to new row 1
            (self.file_input_frame, 2), # Original row 1, moves to new row 2
            (self.search_frame_container, 3), # Original row 2, moves to new row 3
            (self.results_frame, 4), # Original row 3, moves to new row 4
            (self.status_frame, 5) # Original row 4, moves to new row 5
        ]

        # Ungrid to prevent conflicts
        for widget, _ in widgets_to_move:
            widget.grid_forget()

        # Re-grid with new row positions
        self.header_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.file_input_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        self.search_frame_container.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)
        self.results_frame.grid(row=4, column=0, columnspan=2, padx=0, pady=0, sticky="nsew")
        self.status_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(5, 0))

        # Re-configure main_frame's grid weights to accommodate the new row 0 for find_frame
        # The new row for results_frame (row 4) now needs to be the one that expands
        self.main_frame.grid_rowconfigure(0, weight=0) # Find bar row fixed
        self.main_frame.grid_rowconfigure(1, weight=0) # Header row fixed
        self.main_frame.grid_rowconfigure(2, weight=0) # File input row fixed
        self.main_frame.grid_rowconfigure(3, weight=0) # Keyword search row fixed
        self.main_frame.grid_rowconfigure(4, weight=1) # Results frame expands vertically
        self.main_frame.grid_rowconfigure(5, weight=0) # Status bar row fixed


        ttk.Label(self.search_frame, text="Find:", style="TLabel").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        
        self.find_entry = ttk.Entry(self.search_frame, width=30, style="TEntry")
        self.find_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.find_entry.bind("<KeyRelease>", self.on_find_text_change)
        self.find_entry.bind("<Return>", self.find_next)
        self.find_entry.bind("<Escape>", self.hide_find_dialog)

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

        self.match_label = ttk.Label(
            self.search_frame, text="", style="TLabel"
        )
        self.match_label.grid(row=0, column=4, padx=5, pady=2, sticky="w")

        close_button = ttk.Button(
            self.search_frame, text="✕", command=self.hide_find_dialog,
            style="TButton", width=3
        )
        close_button.grid(row=0, column=5, padx=5, pady=2, sticky="e")

        self.search_frame.grid_columnconfigure(1, weight=1) # Allow entry to expand

        self.update_find_dialog_theme()
        self.find_entry.focus_set()

    def hide_find_dialog(self, event=None):
        if self.search_frame:
            self.search_frame.destroy()
            self.search_frame = None
            
            # Revert widget positions back to their original rows
            self.header_frame.grid_forget()
            self.file_input_frame.grid_forget()
            self.search_frame_container.grid_forget()
            self.results_frame.grid_forget()
            self.status_frame.grid_forget()

            self.header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
            self.file_input_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
            self.search_frame_container.grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)
            self.results_frame.grid(row=3, column=0, columnspan=2, padx=0, pady=0, sticky="nsew")
            self.status_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(5, 0))

            # Re-configure main_frame's grid weights back to original
            self.main_frame.grid_rowconfigure(0, weight=0) # Header row fixed
            self.main_frame.grid_rowconfigure(1, weight=0) # File input row fixed
            self.main_frame.grid_rowconfigure(2, weight=0) # Keyword search row fixed
            self.main_frame.grid_rowconfigure(3, weight=1) # Results frame expands vertically
            self.main_frame.grid_rowconfigure(4, weight=0) # Status bar row fixed


        self.clear_highlights()

    def on_find_text_change(self, event=None):
        search_text = self.find_entry.get()
        if search_text:
            self.highlight_all_matches(search_text)
        else:
            self.clear_highlights()
        self.update_match_navigation()

    def highlight_all_matches(self, search_text):
        self.clear_highlights()
        self.search_matches = []
        self.current_match_index = -1
        
        if not search_text:
            return

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

        if self.search_matches:
            self.current_match_index = 0
            self.highlight_current_match()

    def clear_highlights(self):
        self.result_text.tag_remove("highlight", "1.0", tk.END)
        self.result_text.tag_remove("current_highlight", "1.0", tk.END)
        self.search_matches = []
        self.current_match_index = -1
        if self.search_frame:
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
            self.prev_button.config(state="normal" if match_count > 0 else "disabled")
            self.next_button.config(state="normal" if match_count > 0 else "disabled")


    def highlight_current_match(self):
        if not self.search_matches:
            return

        self.result_text.tag_remove("current_highlight", "1.0", tk.END)
        
        start_pos, end_pos = self.search_matches[self.current_match_index]
        self.result_text.tag_add("current_highlight", start_pos, end_pos)
        
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
        path = event.data.strip().strip("{}")
        self.dropped_path = path
        self.drop_entry.delete(0, tk.END)
        self.drop_entry.insert(0, path)
        self.update_status("File/folder loaded: " + os.path.basename(path))
        self._reset_line_numbers()

    def browse_file_or_folder(self):
        """Allows user to browse for a file or folder (now only via menu)"""
        path = filedialog.askopenfilename(
            title="Select a Log File",
            filetypes=[("Log Files", "*.log *.txt *.syslog *.logcat"), ("All Files", "*.*")]
        )
        
        if not path: 
            path = filedialog.askdirectory(title="Select a Log Folder")

        if path:
            self.dropped_path = path
            self.drop_entry.delete(0, tk.END)
            self.drop_entry.insert(0, path)
            self.update_status("File/folder loaded: " + os.path.basename(path))
            self._reset_line_numbers()
        else:
            self.update_status("File/folder selection cancelled.", False)

    def reset_application_state(self):
        """Resets the application to its initial state."""
        if self.search_thread and self.search_thread.is_alive():
            self.stop_search = True
            # Wait a bit for the thread to stop, or implement a more robust stop mechanism
            # For simplicity, we'll just set the flag and let the thread clean up
            self.update_status("Cancelling current operation before reset...", True, self.progress_var.get())
            self.after(500, self._perform_reset_after_thread_stop) # Delay reset to allow thread to stop
        else:
            self._perform_reset_after_thread_stop()

    def _perform_reset_after_thread_stop(self):
        """Performs the actual reset after ensuring any running search thread has stopped."""
        self.drop_entry.delete(0, tk.END)
        self.keyword_entry.delete(0, tk.END)
        self.result_text.delete("1.0", tk.END)
        self._reset_line_numbers()
        self.update_status("Ready", False)
        
        self.dropped_path = ""
        self.search_matches = []
        self.current_match_index = -1
        self.stop_search = False
        
        if self.search_frame:
            self.hide_find_dialog()
        
        self.reset_zoom() # Reset font size
        self.display_welcome_message() # Show welcome message again
        messagebox.showinfo("Reset Complete", "Application has been reset to its initial state.")


    def save_results_as(self):
        """Saves the content of the result_text widget to a file."""
        content = self.result_text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("No Content", "There is no content to save in the results area.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            title="Save Results As"
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.update_status(f"Results saved to: {os.path.basename(file_path)}", False)
                messagebox.showinfo("Save Successful", f"Results successfully saved to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save results:\n{e}")
                self.update_status("Failed to save results.", False)
        else:
            self.update_status("Save operation cancelled.", False)


    def search_logs(self):
        """Start log search or open file in a separate thread"""
        if self.search_thread and self.search_thread.is_alive():
            self.stop_search = True
            self.update_status("Cancelling operation...", True, self.progress_var.get())
            return
        
        keyword = self.keyword_entry.get().strip()
        self.result_text.delete("1.0", tk.END)
        self._reset_line_numbers()
        
        if self.search_frame:
            self.hide_find_dialog()

        if not self.dropped_path:
            messagebox.showwarning("Missing Info", "Please drag & drop a file/folder or use the menu to browse.")
            return

        self.stop_search = False
        self.search_button.config(text="Cancel", state="normal")

        if not keyword and os.path.isfile(self.dropped_path):
            self.search_thread = threading.Thread(target=self._open_file_threaded, args=(self.dropped_path,))
        elif not keyword and os.path.isdir(self.dropped_path):
            messagebox.showwarning("Missing Keyword", "Please enter a keyword to search a directory.")
            self.search_button.config(text="Search", state="normal")
            self.update_status("Ready", False)
            return
        else:
            self.search_thread = threading.Thread(target=self._search_logs_threaded, args=(keyword,))
        
        self.search_thread.start()

    def _open_file_threaded(self, file_path):
        """Threaded function to open and display a single file"""
        try:
            self.update_status(f"Opening file: {os.path.basename(file_path)}...", True, 0)
            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                lines = file.readlines()
                total_lines = len(lines)
                for idx, line in enumerate(lines):
                    if self.stop_search:
                        break
                    self.ui_update_queue.put(lambda l=line: self.result_text.insert(tk.END, l))
                    progress = (idx / total_lines) * 100
                    self.update_status(f"Opening... {idx}/{total_lines} lines", True, progress)
            
            if self.stop_search:
                self.update_status("Operation cancelled", False)
            else:
                self.update_status(f"File '{os.path.basename(file_path)}' opened. Total lines: {total_lines}", False)
            
            self.ui_update_queue.put(self._update_line_numbers)

        except Exception as e:
            self.ui_update_queue.put(lambda: messagebox.showerror("Error", f"Error opening file: {str(e)}"))
        finally:
            self.ui_update_queue.put(lambda: self.search_button.config(text="Search", state="normal"))


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
                        if (file.lower().endswith((".log", ".txt", ".syslog", ".logcat"))
                            or file.lower().startswith("logcat.")):
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
                        if (file.lower().endswith((".log", ".txt", ".syslog", ".logcat"))
                            or file.lower().startswith("logcat.")):
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
                matches_found = self.result_text.get("1.0", tk.END).count("\n") - 1
                self.update_status(f"Search complete - {matches_found} lines found", False)
            
            self.ui_update_queue.put(self._update_line_numbers)

        except Exception as e:
            self.ui_update_queue.put(lambda: messagebox.showerror("Error", f"Search error: {str(e)}"))
        finally:
            self.ui_update_queue.put(lambda: self.search_button.config(text="Search", state="normal"))

    def search_file(self, file_path, keyword):
        found = False
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                lines = file.readlines()
                
                # Collect all relevant line ranges
                context_ranges = []
                for idx, line in enumerate(lines):
                    if keyword.lower() in line.lower():
                        start_context_idx = max(0, idx - 5)
                        end_context_idx = min(len(lines) - 1, idx + 5)
                        context_ranges.append((start_context_idx, end_context_idx))
                
                if not context_ranges:
                    return False # No matches found in this file

                # Sort ranges by their start index
                context_ranges.sort()

                # Merge overlapping or adjacent ranges
                merged_ranges = []
                if context_ranges:
                    current_start, current_end = context_ranges[0]
                    for i in range(1, len(context_ranges)):
                        next_start, next_end = context_ranges[i]
                        # If the next range overlaps or is adjacent (+1 for continuity)
                        if next_start <= current_end + 5: # Changed from +1 to +5 to merge contexts
                            current_end = max(current_end, next_end)
                        else:
                            merged_ranges.append((current_start, current_end))
                            current_start, current_end = next_start, next_end
                    merged_ranges.append((current_start, current_end)) # Add the last merged range

                # Print the merged ranges
                for start_idx, end_idx in merged_ranges:
                    found = True
                    self.ui_update_queue.put(lambda fp=file_path, s_idx=start_idx: 
                        self.result_text.insert(tk.END, f"\n--- {fp} (Context around line {s_idx+1}) ---\n"))
                    
                    for i in range(start_idx, end_idx + 1):
                        if self.stop_search:
                            break
                        current_line_num = i + 1
                        current_line_content = lines[i]
                        self.ui_update_queue.put(lambda ln=current_line_num, lc=current_line_content: 
                            self.result_text.insert(tk.END, f"{ln}: {lc}"))
                    
                    self.ui_update_queue.put(lambda: self.result_text.insert(tk.END, "---\n")) # Separator for context block
        except Exception as e:
            self.ui_update_queue.put(lambda fp=file_path, err=e: 
                self.result_text.insert(tk.END, f"Error reading {fp}: {err}\n"))
        return found


if __name__ == "__main__":
    app = LogSearchApp()
    app.mainloop()
