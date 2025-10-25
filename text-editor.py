import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import font
from typing import Optional
import os
import keyword
import tokenize
import io
import builtins
import re

def get_dunder_methods():
    types_to_check = [
        object, int, str, list, dict, float, set, tuple, bool, type,
        bytes, bytearray, complex, range, slice, memoryview
    ]
    dunders = set()
    for typ in types_to_check:
        for name in dir(typ):
            if name.startswith('__') and name.endswith('__'):
                attribute = getattr(typ, name, None)
                if callable(attribute):
                    dunders.add(name)
    return dunders

class FindDialogue:
    def __init__(self, text_box):
        self.text_box = text_box
        self.find_window = self.setup_window()
        self.window_frame = ttk.Frame(self.find_window, padding=(10,10,15,15))
        find_frame = ttk.Frame(self.window_frame)
        self.entry_frame = ttk.Frame(find_frame)
        self.next_frame = ttk.Frame(find_frame)
        self.dir_frame = ttk.Frame(find_frame)
        self.direction_var = tk.StringVar()
        self.user_input = tk.StringVar()
        self.regex = ""
        self.entry_text = ""
        self.matches = []
        self.find_index = -1
        self.cursor_index = 0
        self.word_var = tk.IntVar(value=1)
        self.wrap_var = tk.IntVar(value=1)
        self.match_all_var = tk.IntVar(value=0)
        self.create_dialogue()
        self.entry_frame.pack(fill="x", expand=True)
        self.next_frame.pack(fill="x", expand=True)
        self.dir_frame.pack(fill="x", expand=True)
        find_frame.pack(fill="x")
        self.window_frame.pack()

    def setup_window(self):
        find_window = tk.Toplevel()
        find_window.transient(self.text_box.winfo_toplevel())
        find_window.grab_set()
        find_window.focus_force()
        find_window.protocol("WM_DELETE_WINDOW", self.close)
        find_window.title("Find")
        return find_window

    def create_options(self):
        options_label = ttk.Label(self.next_frame, text="Options:")
        options_label.pack(side="left", padx=(0, 10))
        whole_word_radio = ttk.Checkbutton(self.next_frame, variable=self.word_var, text="Whole word")
        wrap_around_radio = ttk.Checkbutton(self.next_frame, variable=self.wrap_var, text="Wrap around")
        match_all = ttk.Checkbutton(self.next_frame, text="Match all", variable=self.match_all_var)
        whole_word_radio.pack(side="left")
        wrap_around_radio.pack(side="left")
        match_all.pack(side="left")

    def create_dialogue(self):
        self.create_options()
        self.create_find_label()
        self.create_find_entry()
        self.create_close_button()
        self.create_direction_label()
        self.create_radio_buttons()
        self.create_next_button()

    def create_find_label(self):
        find_label = ttk.Label(self.entry_frame, text="Find:", font=(font.nametofont("TkDefaultFont"), 10))
        find_label.pack(side="left", padx=(0, 5))

    def create_find_entry(self):
        find_entry = ttk.Entry(self.entry_frame, width=55, textvariable=self.user_input)
        find_entry.bind("<Return>", self.find)
        find_entry.focus_set()
        find_entry.pack(side="left", fill="x", expand=True)

    def create_radio_buttons(self):
        up_radio = ttk.Radiobutton(self.dir_frame, variable=self.direction_var, text="Up", value="Up")
        down_radio = ttk.Radiobutton(self.dir_frame, variable=self.direction_var, text="Down", value="Down")
        self.direction_var.set("Down")
        up_radio.pack(side="left")
        down_radio.pack(side="left")

    def create_close_button(self):
        close_button = ttk.Button(self.entry_frame, text="Close", command=self.close)
        close_button.pack(side="right", anchor="e", padx=8)

    def create_next_button(self):
        next_button = ttk.Button(self.next_frame, text="Find Next", command=self.find)
        next_button.pack(side="right", anchor="e",padx=(0, 8), pady=(5, 0))

    def create_direction_label(self):
        direction_label = ttk.Label(self.dir_frame, text="Direction:", font=(font.nametofont("TkDefaultFont"), 10))
        direction_label.pack(side="left")

    def find_matches(self):
        input_text = self.user_input.get()
        if input_text != self.entry_text:
            self.find_index = -1
            self.entry_text = input_text
        if self.word_var.get():
            words = input_text.split()
            self.regex = r'\b' + r'\b\s+\b'.join(map(re.escape, words)) + r'\b'
        else:
           self.regex = re.escape(input_text)
        matches = list(re.finditer(self.regex, self.text_box.get("1.0", "end-1c")))
        return matches

    def find(self, event=None):
        user_input = self.user_input.get()
        if not user_input:
             messagebox.showerror("Empty search error", "Error: invalid search. Try again...")
             return
        if not user_input.strip():
             messagebox.showerror("Invalid search error", "Error: whitespace only searches not allowed. Try again...")
             return
        self.matches = self.find_matches()
        if self.matches:
            self.highlight_match()
        else:
            self.text_box.bell()

    def highlight_match(self):
        if not self.match_all_var.get():
            direction = self.direction_var.get()
            if direction == "Up":
                self.find_index -= 1
            else:
                self.find_index += 1
            self.clamp_match_index(direction)
            current_match = self.matches[self.find_index]
            start_index = self.text_box.index(f"1.0 + {current_match.start()} chars")
            self.cursor_index = self.text_box.index(f"1.0 + {current_match.end()} chars")
            self.configure_tags(start_index)
            self.text_box.see(start_index)
        else:
            self.select_all_matches()

    def select_all_matches(self):
        self.text_box.tag_remove("fake_sel", "1.0", "end")
        self.text_box.tag_remove("sel", "1.0", "end")
        self.text_box.tag_configure("fake_sel", background="grey", foreground="white")
        for match in self.matches:
            start_index = self.text_box.index(f"1.0 + {match.start()} chars")
            end_index = self.text_box.index(f"1.0 + {match.end()} chars")
            self.text_box.tag_add("sel", start_index, end_index)
            self.text_box.tag_add("fake_sel", start_index, end_index)

    def clamp_match_index(self, direction):
        wrap_around = self.wrap_var.get()
        first_up_search = -2
        if wrap_around and self.find_index != first_up_search:
            self.find_index %= len(self.matches)
        else:
            last_match = len(self.matches)-1
            if direction == "Up" and self.find_index < 0:
                self.find_index = 0
            elif direction == "Down" and self.find_index > last_match:
                self.find_index = last_match

    def configure_tags(self, start_index):
        self.text_box.tag_remove("fake_sel", "1.0", "end")
        self.text_box.tag_remove("sel", "1.0", "end")
        self.text_box.tag_configure("fake_sel", background="grey", foreground="white")
        self.text_box.tag_add("sel", start_index, self.cursor_index)
        self.text_box.tag_add("fake_sel", start_index, self.cursor_index)

    def close(self):
        if self.cursor_index != 0:
            self.text_box.mark_set("insert", self.cursor_index)
        self.find_window.destroy()

class ReplaceDialogue(FindDialogue):
    def __init__(self, text_box):
        FindDialogue.__init__(self,text_box)
        self.find_window.title("Find And Replace")
        replace_frame = ttk.Frame(self.window_frame)
        replace_label = ttk.Label(replace_frame,text="Replace:",font=(font.nametofont("TkDefaultFont"), 10))
        self.replace_input = tk.StringVar()
        self.replace_entry = ttk.Entry(replace_frame,width=55,textvariable=self.replace_input)
        self.replace_entry.bind("<Return>", self.replace)
        replace_label.pack(side="left",padx=(0,5),fill="x", expand=True)
        self.replace_entry.pack(side="left")
        self.replace_button = ttk.Button(replace_frame,text="Replace", command=self.replace)
        self.replace_button.pack(side="right",padx=8,anchor="e")
        replace_frame.pack(pady=(10,0))

    def replace(self, event=None):
        user_input = self.replace_input.get()
        is_space = any(char.isspace() for char in user_input)
        if user_input == "":
            messagebox.showerror("Empty replace error", "Error: must input valid text. Try again...")
            return
        if is_space:
            messagebox.showerror("Whitespace error", "Error: cannot replace whitespace. Try again...")
            return
        if self.matches:
            if not self.match_all_var.get():
                self.replace_single_match(user_input)
            else:
                self.replace_all_matches(user_input)
        else:
            self.text_box.bell()

    def replace_single_match(self, user_input):
        current_match = self.matches[self.find_index]
        start_index = self.text_box.index(f"1.0 + {current_match.start()} chars")
        end_index = self.text_box.index(f"1.0 + {current_match.end()} chars")
        self.text_box.delete(start_index, end_index)
        self.text_box.insert(start_index, user_input)
        self.matches = self.find_matches()
        self.find_index = -1
        end_row, end_col = end_index.split(".")
        end_col = int(end_col)
        end_col -= (len(current_match.group()) - len(user_input))
        end_index = f"{end_row}.{end_col}"
        self.cursor_index = end_index

    def replace_all_matches(self, user_input):
        for match in reversed(self.matches):
            start_index = self.text_box.index(f"1.0 + {match.start()} chars")
            end_index = self.text_box.index(f"1.0 + {match.end()} chars")
            self.text_box.delete(start_index, end_index)
            self.text_box.insert(start_index, user_input)
        self.matches = self.find_matches()
        self.find_index = -1

class TextEditor:

    MAX_UNDO = 25
    DUNDERS = get_dunder_methods()
    BUILTINS = set(dir(builtins))
    LIGHT_THEME_COLOURS = {"comments": "red", "strings": "light blue",
                                "keywords": "orange", "names": "black", "builtins": "purple",
                                "self": "orange", "dunders": "purple", "numbers": "darkblue", "op": "black",
                                "functions": "blue"}

    DARK_THEME_COLOURS = {"comments": "#fa4d4d", "strings": "light blue",
                               "keywords": "orange", "names": "white", "builtins": "#eb9cf7",
                               "self": "orange", "dunders": "#eb9cf7", "numbers": "light blue", "op": "white",
                               "functions": "#52aeba"}

    def __init__(self):
        self.undo_stack = []
        self.redo_stack = []
        self.current_file_path = None
        self.file_name = "untitled"
        self.word_wrap = True
        self.python_mode = False
        self.recent_files = []
        self.recent_files_menu: Optional[tk.Menu] = None
        self.options_menu: Optional[tk.Menu] = None
        self.backspace_id: Optional[str] = None
        self.space_id: Optional[str] = None
        self.key_release_id: Optional[str] = None
        self.window = tk.Tk()
        self.window.title(self.file_name)
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.create_menu_bar()
        self.create_window_bindings()
        self.text_box = self.create_text_area()
        self.configure_tags(TextEditor.LIGHT_THEME_COLOURS)
        self.text_row_label, self.text_col_label = self.create_line_positions()

    def create_menu_bar(self):
        menu_bar = tk.Menu(self.window)
        self.window.config(menu=menu_bar)
        file_menu = self.create_file_menu(menu_bar)
        edit_menu = self.create_edit_menu(menu_bar)
        self.options_menu = self.create_options_menu(menu_bar)
        format_menu = self.create_format_menu(menu_bar)
        menu_bar.add_cascade(label="File", menu=file_menu)
        menu_bar.add_cascade(label="Edit", menu=edit_menu)
        menu_bar.add_cascade(label="Options", menu=self.options_menu)
        menu_bar.add_cascade(label="Format", menu=format_menu)

    def create_file_menu(self,menu_bar):
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="New File", accelerator="Ctrl+N", command=self.new_file)
        file_menu.add_command(label="Open", accelerator="Ctrl+O", command=self.open)
        self.recent_files_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Recent Files", menu=self.recent_files_menu)
        file_menu.add_separator()
        file_menu.add_command(label="Save", accelerator="Ctrl+S", command=self.save)
        file_menu.add_command(label="Save As", accelerator="Ctrl+Shift+S", command=self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Close", accelerator="Ctrl+Q", command=self.close)
        return file_menu

    def create_edit_menu(self,menu_bar):
        edit_menu = tk.Menu(menu_bar, tearoff=0)
        edit_menu.add_command(label="Undo",accelerator="Ctrl+Z",command=self.undo)
        edit_menu.add_command(label="Redo",accelerator="Ctrl+Shift+Z", command=self.redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Select All", accelerator="Ctrl+A", command=self.select_all)
        edit_menu.add_command(label="Cut", accelerator="Ctrl+X", command=self.cut)
        edit_menu.add_command(label="Paste", accelerator="Ctrl+V", command=self.paste)
        edit_menu.add_separator()
        edit_menu.add_command(label="Find", accelerator="Ctrl+F", command=self.find)
        edit_menu.add_command(label="Replace", accelerator="Ctrl+Shift+F", command=self.replace)
        return edit_menu

    def create_options_menu(self, menu_bar):
        options_menu = tk.Menu(menu_bar, tearoff=0)
        options_menu.add_command(label="Python Mode", accelerator="Alt+M", command=self.enable_python_mode)
        options_menu.add_command(label="Text Mode", accelerator="Alt+C", command=self.enable_text_mode)
        options_menu.entryconfig("Text Mode", foreground="grey")
        options_menu.add_separator()
        options_menu.add_command(label="Dark Theme", accelerator="Ctrl+G", command=self.dark_theme)
        options_menu.add_command(label="Light Theme", accelerator="Alt+G", command=self.light_theme)
        options_menu.entryconfig("Light Theme", foreground="grey")
        options_menu.add_separator()
        options_menu.add_command(label="Word Wrap", accelerator="Ctrl+T", command=self.toggle_word_wrap)
        options_menu.entryconfig("Word Wrap", foreground="grey")
        return options_menu

    def create_format_menu(self, menu_bar):
        format_menu = tk.Menu(menu_bar, tearoff=0)
        font_menu = tk.Menu(format_menu, tearoff=0)
        font_size_menu = tk.Menu(format_menu, tearoff=0)
        format_menu.add_cascade(label="Font",menu=font_menu)
        format_menu.add_cascade(label="Font Size", menu=font_size_menu)
        for font_name in list(font.families()):
            font_menu.add_command(label=font_name, command=lambda name=font_name: self.set_font(name))
        font_sizes = 30
        for index in range(font_sizes):
            font_size = f"{index * 2 + 2}pt" #Increase the font sizes by increments of 2.
            font_size_menu.add_command(label=font_size,command=lambda size=font_size: self.set_font_size(size))
        return format_menu

    def set_font(self, font_name):
        current_font = self.text_box.cget("font")
        current_font = font.Font(font=current_font)
        self.text_box.config(font=(font_name, current_font.actual("size")))

    def set_font_size(self, font_size):
        current_font = self.text_box.cget("font")
        current_font = font.Font(font=current_font)
        font_size, _ = font_size.split("p") #Get the number component of font size.
        self.text_box.config(font=(current_font.actual("family"), int(font_size)))

    def find(self,event=None):
        FindDialogue(self.text_box)

    def replace(self, event=None):
        ReplaceDialogue(self.text_box)

    def toggle_word_wrap(self, event=None):
        self.word_wrap = not self.word_wrap
        if self.word_wrap:
            self.text_box.config(wrap="word")
            self.options_menu.entryconfig("Word Wrap", foreground="grey")
        else:
            self.text_box.config(wrap="none")
            self.options_menu.entryconfig("Word Wrap", foreground="black")

    def enable_python_mode(self, event=None):
        if self.key_release_id is None:
            self.key_release_id = self.text_box.bind("<KeyRelease>", self.highlight_text)
        self.options_menu.entryconfig("Python Mode",foreground="grey")
        self.options_menu.entryconfig("Text Mode", foreground="black")
        self.python_mode = True
        self.clear_highlighting()
        self.highlight_text()
        self.bind_space_backspace()

    def enable_text_mode(self, event=None):
        if self.key_release_id is not None:
            self.key_release_id = self.text_box.unbind("<KeyRelease>", self.key_release_id)
        self.options_menu.entryconfig("Python Mode", foreground="black")
        self.options_menu.entryconfig("Text Mode", foreground="grey")
        self.python_mode = False
        self.clear_highlighting()
        self.unbind_space_backspace()

    def dark_theme(self, event=None):
        self.text_box.config(insertbackground="white", background="#152e3d", foreground="white")
        self.configure_tags(TextEditor.DARK_THEME_COLOURS)
        self.options_menu.entryconfig("Dark Theme", foreground="grey")
        self.options_menu.entryconfig("Light Theme", foreground="black")

    def light_theme(self, event=None):
        self.text_box.config(insertbackground="black", background="white", foreground="black")
        self.configure_tags(TextEditor.LIGHT_THEME_COLOURS)
        self.options_menu.entryconfig("Dark Theme", foreground="black")
        self.options_menu.entryconfig("Light Theme", foreground="grey")

    def create_text_area(self):
        editor_frame = ttk.Frame(self.window, padding=(1, 0, 0, 0))
        text_box = tk.Text(editor_frame, width=55, height=25, padx=5, pady=5,font=("Arial", 12),undo=False,wrap="word")
        vertical_scrollbar = ttk.Scrollbar(editor_frame, orient="vertical")
        text_box.config(yscrollcommand=vertical_scrollbar.set)
        vertical_scrollbar.config(command=text_box.yview)
        vertical_scrollbar.pack(side="right", fill="y")
        text_box.bind("<ButtonRelease-1>", self.text_interact)
        text_box.bind("<<Modified>>", self.text_interact)
        text_box.bind("<<Modified>>", self.set_title, add="+")
        text_box.bind("<space>", self.save_word)
        text_box.bind("<Return>", self.save_word)
        text_box.bind("<Tab>", self.save_word)
        text_box.bind("<Tab>", self.handle_indent, add="+")
        text_box.bind("<Key>", lambda t=text_box: text_box.see(tk.INSERT))
        text_box.pack(fill="both", expand=True)
        editor_frame.pack(fill="both", expand=True)
        self.window.after(50, lambda:editor_frame.pack_propagate(False)) #Stops the text editor frame from resizing when font size and font changes.
        return text_box

    def create_window_bindings(self):
        self.create_file_bindings()
        self.create_edit_bindings()
        self.create_options_bindings()

    def create_file_bindings(self):
        self.window.bind("<Control-n>", self.new_file)
        self.window.bind("<Control-o>", self.open)
        self.window.bind("<Control-s>", self.save)
        self.window.bind("<Control-S>", self.save_as)
        self.window.bind("<Control-q>", self.close)

    def create_edit_bindings(self):
        self.window.unbind_class("Text","<Control-z>")
        self.window.bind_class("Text", "<Control-z>", self.undo)
        self.window.unbind_class("Text", "<Control-Z>")
        self.window.bind_class("Text", "<Control-Z>", self.redo)
        self.window.unbind_class("Text", "<Control-a>")
        self.window.bind_class("Text", "<Control-a>", self.select_all)
        self.window.unbind_class("Text", "<Control-x>")
        self.window.bind_class("Text", "<Control-x>", self.cut)
        self.window.unbind_class("Text", "<Control-v>")
        self.window.bind_class("Text", "<Control-v>", self.paste)
        self.window.bind("<Control-f>", self.find)
        self.window.bind("<Control-F>", self.replace)

    def create_options_bindings(self):
        self.window.bind("<Control-g>", self.dark_theme)
        self.window.bind("<Alt-g>", self.light_theme)
        self.window.bind("<Control-t>", self.toggle_word_wrap)
        self.window.bind("<Alt-m>", self.enable_python_mode)
        self.window.bind("<Alt-c>", self.enable_text_mode)

    def create_line_positions(self):
        line_frame = ttk.Frame(self.window)
        text_row_label = ttk.Label(line_frame, text="Ln: 0", padding=(0, 0, 8, 0))
        text_col_label = ttk.Label(line_frame, text="Col: 0", padding=(0, 0, 5, 0))
        text_col_label.pack(side="right")
        text_row_label.pack(side="right")
        line_frame.pack(fill="x")
        return text_row_label, text_col_label

    def run_editor(self):
        self.window.mainloop()

    def handle_indent(self,event=None):
        self.text_box.insert(tk.INSERT, "    ")
        return "break"

    def handle_spaces(self, event=None):
        cursor_index = self.text_box.index("insert")
        prev_index = self.text_box.index(f"{cursor_index}-1c")
        prev_char = self.text_box.get(prev_index)
        col = cursor_index.split(".")[1]
        if col == "0" or prev_char == " ":
            self.text_box.insert(tk.INSERT,"  ")
        else:
            self.text_box.insert(tk.INSERT," ")
        return "break"

    def handle_backspace(self, event=None):
        if not self.text_box.tag_ranges("sel"):
            cursor_index = self.text_box.index("insert")
            prev_index = self.text_box.index(f"{cursor_index}-2c")
            chars_before = self.text_box.get(prev_index, cursor_index)
            if chars_before == "  ":
                self.text_box.delete(prev_index, cursor_index)
                return "break"
        else:
            self.text_box.delete("sel.first", "sel.last")
            return "break"

    def set_file_name(self, file_path):
        self.file_name = os.path.basename(file_path)
        self.window.title(self.file_name)

    def set_title(self,event=None):
        if self.text_box.edit_modified():
            self.text_box.edit_modified(False)
            self.window.title("*" + self.file_name + "*")

    def new_file(self,event=None):
        self.text_box.delete("1.0", tk.END)
        self.file_name = "untitled"
        self.window.title(self.file_name)
        self.text_box.edit_modified(False)
        self.unbind_space_backspace()

    def cut(self, event=None):
        try:
            self.save_word()
            selected_text = self.text_box.get("sel.first", "sel.last")
            self.text_box.delete("sel.first", "sel.last")
            self.text_box.clipboard_clear()
            self.text_box.clipboard_append(selected_text)
        except tk.TclError:
            pass

    def paste(self, event=None):
        try:
            self.save_word()
            self.redo_stack.clear()
            cursor_pos = self.text_box.index(tk.INSERT)
            pasted_text = self.text_box.clipboard_get().rstrip()
            self.text_box.insert(cursor_pos,pasted_text)
        except tk.TclError:
            pass
        return "break"

    def select_all(self, event=None):
        self.text_box.tag_add("sel", "1.0", "end")

    def undo(self,event=None):
        current_text = self.text_box.get("1.0", "end-1c")
        self.text_box.delete("1.0", tk.END)
        if self.redo_stack:
            last_item = self.redo_stack[-1]
        else:
            last_item = None
        if self.undo_stack:
            last_state = self.undo_stack.pop()
            self.redo_stack.append(current_text)
            self.text_box.insert("1.0", last_state)
        else:
            self.remove_duplicates(last_item,current_text)
        self.remove_empty_strings()
        if self.python_mode:
            self.highlight_text()

    def redo(self,event=None):
        if self.redo_stack:
            next_state = self.redo_stack.pop()
            current_text = self.text_box.get("1.0", "end-1c")
            self.undo_stack.append(current_text)
            self.text_box.delete("1.0", tk.END)
            self.text_box.insert("1.0", next_state)
            if self.python_mode:
                self.highlight_text()

    def remove_empty_strings(self):
        for string in self.redo_stack[:]:
            if string == "":
                self.redo_stack.remove(string)

    def remove_duplicates(self, last_item, current_text):
        if len(self.redo_stack) > 1:
            if last_item != self.redo_stack[-2]:
                self.redo_stack.append(current_text)
        else:
            self.redo_stack.append(current_text)
            self.redo_stack = list(dict.fromkeys(self.redo_stack))

    def bind_space_backspace(self):
        if self.backspace_id is None and self.space_id is None:
            self.space_id = self.text_box.bind("<space>", self.handle_spaces, add="+")
            self.backspace_id = self.text_box.bind("<BackSpace>", self.handle_backspace)

    def unbind_space_backspace(self):
        if self.backspace_id is not None and self.space_id is not None:
            self.space_id = self.text_box.unbind("<space>", self.space_id)
            self.backspace_id = self.text_box.unbind("<BackSpace>", self.backspace_id)

    def highlight_if_python(self):
        if self.window.title().endswith(".py"):
            self.bind_space_backspace()
            self.highlight_text()
            self.options_menu.entryconfig("Python Mode", foreground="grey")
            self.options_menu.entryconfig("Text Mode", foreground="black")
            self.options_menu.entryconfig("Word Wrap", foreground="black")
            self.text_box.config(wrap="none")
            self.word_wrap = False
            self.python_mode = True
        else:
            self.options_menu.entryconfig("Python Mode", foreground="black")
            self.options_menu.entryconfig("Text Mode", foreground="grey")
            self.options_menu.entryconfig("Word Wrap", foreground="grey")
            self.text_box.config(wrap="word")
            self.word_wrap = True
            self.python_mode = False
            self.unbind_space_backspace()

    def open(self,event=None):
        file_types=(("Text Files", "*.txt"),("Python Files", "*.py"))
        file_path = filedialog.askopenfilename(title="Open a file...",filetypes=file_types)
        editor_text = self.text_box.get("1.0","end-1c")
        editor_text = editor_text.strip()
        if file_path:
            self.current_file_path = file_path
            self.set_file_name(file_path)
            self.update_recent_files(file_path)
            if editor_text:
                self.text_box.delete("1.0", tk.END)
            index = 1
            with open(self.current_file_path) as file:
                lines = file.readlines()
                for line in lines:
                    self.text_box.insert(f"{index}.0",line)
                    index += 1
                self.highlight_if_python()
                self.undo_stack.clear()
                self.redo_stack.clear()
            self.text_box.edit_modified(False)

    def save(self,event=None):
        if self.current_file_path:
            with open(self.current_file_path,"w") as file:
                file.write(self.text_box.get("1.0", "end-1c"))
                self.text_box.edit_modified(False)
                self.window.title(self.file_name)
            return True
        else:
            saved = self.save_as()
            return saved

    def save_as(self,event=None):
        file_types = (("Text files", "*.txt"),("Python Files","*.py"))
        file_path = filedialog.asksaveasfilename(defaultextension=".txt",filetypes=file_types)
        if file_path:
            self.current_file_path = file_path
            self.set_file_name(file_path)
            self.update_recent_files(file_path)
            with open(self.current_file_path, "w") as file:
                file.write(self.text_box.get("1.0", "end-1c"))
                self.text_box.edit_modified(False)
            return True
        else:
            return False

    def text_interact(self,event=None):
        cursor_pos = self.text_box.index(tk.INSERT)
        cursor_pos = cursor_pos.split(".")
        cursor_row, cursor_col = cursor_pos
        self.text_row_label.config(text=f"Ln: {cursor_row}")
        self.text_col_label.config(text=f"Col: {cursor_col}")
        self.text_box.tag_remove("fake_sel", "1.0", "end")

    def open_recent_file(self, file_path):
        if os.path.exists(file_path):
            self.current_file_path = file_path
            self.set_file_name(file_path)
            with open(self.current_file_path, "r") as file:
                content = file.read()
            self.text_box.delete("1.0", tk.END)
            self.text_box.insert("1.0", content)
            self.text_box.edit_modified(False)
            self.update_recent_files(file_path)
            self.highlight_if_python()
            self.undo_stack.clear()
            self.redo_stack.clear()
        else:
            messagebox.showerror(title="File Not Found",message=f"{file_path} does not exist.")
            self.recent_files.remove(file_path)
            self.update_recent_files(None)

    def update_recent_files(self, file_path):
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        if file_path is not None:
            self.recent_files.insert(0, file_path)
        self.recent_files = self.recent_files[:5]
        self.recent_files_menu.delete(0, tk.END)
        for recent_file in self.recent_files:
            self.recent_files_menu.add_command(label=recent_file,command=lambda
            r=recent_file: self.open_recent_file(r))

    def save_word(self, event=None):
        current_text = self.text_box.get("1.0", "end-1c")
        if self.undo_stack and self.undo_stack[-1] == current_text:
            return
        if len(self.undo_stack) >= self.MAX_UNDO:
            self.undo_stack.pop(0)
        self.undo_stack.append(current_text)
        self.redo_stack.clear()

    def configure_tags(self, theme_colours):
        self.text_box.tag_configure("comments", foreground=theme_colours["comments"])
        self.text_box.tag_configure("strings", foreground=theme_colours["strings"])
        self.text_box.tag_configure("keywords", foreground=theme_colours["keywords"])
        self.text_box.tag_configure("names", foreground=theme_colours["names"])
        self.text_box.tag_configure("builtins", foreground=theme_colours["builtins"])
        self.text_box.tag_configure("self", foreground=theme_colours["self"])
        self.text_box.tag_configure("dunders", foreground=theme_colours["dunders"])
        self.text_box.tag_configure("numbers", foreground=theme_colours["numbers"])
        self.text_box.tag_configure("functions", foreground=theme_colours["functions"])

    def gen_tokens(self):
        text_content = self.text_box.get("1.0", "end-1c")
        tokens = []
        readline = io.StringIO(text_content).readline
        try:
            for token in tokenize.generate_tokens(readline):
                tokens.append(token)
        except tokenize.TokenError:
            pass
        return tokens

    @staticmethod
    def check_names(tok_string,function_next):
        if keyword.iskeyword(tok_string):
            if tok_string == "def":
                function_next = True
            tag = "keywords"
        elif tok_string in TextEditor.BUILTINS:
            tag = "builtins"
            function_next = False
        elif tok_string == "self":
            tag = "self"
            function_next = False
        elif tok_string in TextEditor.DUNDERS:
            tag = "dunders"
            function_next = False
        elif function_next:
            tag = "functions"
            function_next = False
        else:
            tag = "names"
        return tag, function_next

    @staticmethod
    def assign_text_tag(tok_type, tok_string, function_next):
        tag = None
        if tok_type == tokenize.COMMENT:
            tag = "comments"
        elif tok_type == tokenize.STRING:
            tag = "strings"
        elif tok_type == tokenize.NUMBER:
            tag = "numbers"
        elif tok_type == tokenize.NAME:
            tag, function_next = TextEditor.check_names(tok_string,function_next)
        elif tok_type == tokenize.OP:
            tag = "op"
        return tag, function_next

    def highlight_text(self,event=None):
        self.clear_highlighting()
        tokens = self.gen_tokens()
        function_next = False
        for index, token in enumerate(tokens):
            tok_string = token.string
            tok_type = token.type
            start_line, start_col = token.start
            end_line, end_col = token.end
            tag, function_next = TextEditor.assign_text_tag(tok_type,tok_string,function_next)
            if index > 0:
                prev_token = tokens[index-1]
                if tag == "builtins" and prev_token.type == tokenize.OP and prev_token.string == ".":
                    tag = "names"
            if tag:
                start_index = f"{start_line}.{start_col}"
                end_index = f"{end_line}.{end_col}"
                self.text_box.tag_add(tag, start_index, end_index)

    def clear_highlighting(self):
        for tag in self.text_box.tag_names():
            self.text_box.tag_remove(tag, "1.0", "end")

    def close(self,event=None):
        file_title = self.window.title()
        if file_title.startswith("*"):
            response = messagebox.askyesnocancel("Save Changes?", "Do you want to save changes?")
            if response:
                saved = self.save()
                if saved:
                    self.window.destroy()
            elif response is False:
                self.window.destroy()
        else:
            self.window.destroy()

if __name__ == "__main__":
    text_editor = TextEditor()
    text_editor.run_editor()
