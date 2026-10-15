import random
import re
import textwrap
import tkinter as tk
from collections import deque
from tkinter import ttk


def get_number(word):
    number = "".join(char for char in word if char.isdigit())
    return bool(number), number


def seperate_vocab(vocab):
    numbered_entries = list(re.finditer(r"\d+\.\s*", vocab))
    if numbered_entries:
        entries = [
            vocab[
                match.end():
                numbered_entries[index + 1].start()
                if index + 1 < len(numbered_entries)
                else len(vocab)
            ]
            for index, match in enumerate(numbered_entries)
        ]
    else:
        entries = [line for line in vocab.splitlines() if line.strip()]
        if not entries and vocab.strip():
            entries = [vocab]

    vocab_words_and_definitions = {}
    for entry in entries:
        separator = re.search(r"\s+-\s+", entry)
        if separator is None:
            raise ValueError(
                f"Could not find ' - ' between a vocabulary word and its "
                f"definition: {entry.strip()!r}"
            )

        word = entry[:separator.start()].strip()
        definition = entry[separator.end():].strip()
        if not word or not definition:
            raise ValueError(
                f"Each vocabulary entry needs a word and a definition: "
                f"{entry.strip()!r}"
            )
        if word in vocab_words_and_definitions:
            raise ValueError(f"Duplicate vocabulary word: {word!r}")

        vocab_words_and_definitions[word] = definition

    if not vocab_words_and_definitions:
        raise ValueError("Enter at least one vocabulary word and definition.")
    return vocab_words_and_definitions


def get_hint(word, hint_number=1):
    if hint_number <= 1:
        letter_count = sum(char.isalpha() for char in word)
        return f"The word starts with '{word[0]}' and has {letter_count} letters."

    prefix_length = min(max(2, (len(word) + 1) // 2), len(word))
    return f"The word starts with '{word[:prefix_length]}'."


def _normalize_answer(answer):
    return " ".join(re.sub(r"[^\w\s]", "", answer.casefold()).split())


def _answers_match(answer, expected):
    return _normalize_answer(answer) == _normalize_answer(expected)


class VocabFlashcardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Vocabulary Practice")
        self.root.geometry("920x780")
        self.root.minsize(680, 600)
        self.configure_styles()

        self.cards = deque()
        self.vocab_cards = {}
        self.current_cards = []
        self.total_cards = 0
        self.words_to_review = set()
        self.mastered_words = set()
        self.first_try_correct = 0
        self.hint_number = 0
        self.question_type = "definition"

        self.main_frame = ttk.Frame(root, padding=28, style="App.TFrame")
        self.main_frame.pack(fill="both", expand=True)
        self.show_vocab_screen()

    def configure_styles(self):
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        self.root.configure(background="#f6f1ff")
        style.configure("App.TFrame", background="#f6f1ff")
        style.configure("Header.TFrame", background="#f6f1ff")
        style.configure(
            "Title.TLabel",
            background="#f6f1ff",
            foreground="#30205c",
            font=("Segoe UI", 26, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background="#f6f1ff",
            foreground="#685d80",
            font=("Segoe UI", 11),
        )
        style.configure(
            "Card.TLabelframe",
            background="#ffffff",
            bordercolor="#e6def2",
            relief="solid",
        )
        style.configure(
            "Card.TLabelframe.Label",
            background="#ffffff",
            foreground="#46316f",
            font=("Segoe UI", 12, "bold"),
        )
        style.configure("Card.TFrame", background="#ffffff")
        style.configure(
            "Card.TLabel",
            background="#ffffff",
            foreground="#35284f",
            font=("Segoe UI", 13),
        )
        style.configure(
            "Card.TRadiobutton",
            background="#ffffff",
            foreground="#493765",
            font=("Segoe UI", 11),
        )
        style.map(
            "Card.TRadiobutton",
            background=[("active", "#fff7fc")],
            foreground=[("selected", "#6b36d9")],
        )
        style.configure(
            "Prompt.TLabel",
            background="#ffffff",
            foreground="#c04484",
            font=("Segoe UI", 10, "bold"),
        )
        style.configure(
            "TCheckbutton",
            background="#ffffff",
            foreground="#493765",
            font=("Segoe UI", 10),
        )
        style.map("TCheckbutton", background=[("active", "#ffffff")])
        style.configure(
            "Primary.TButton",
            background="#7041dc",
            foreground="#ffffff",
            font=("Segoe UI", 10, "bold"),
            padding=(18, 11),
            borderwidth=0,
        )
        style.map(
            "Primary.TButton",
            background=[("active", "#5528bf"), ("disabled", "#c5b6e5")],
            foreground=[("disabled", "#f4f6fc")],
        )
        style.configure(
            "Secondary.TButton",
            background="#ffe4f1",
            foreground="#873864",
            font=("Segoe UI", 10, "bold"),
            padding=(14, 9),
            borderwidth=0,
        )
        style.map(
            "Secondary.TButton",
            background=[("active", "#ffd0e6"), ("disabled", "#f4e8ef")],
        )
        style.configure(
            "Horizontal.TProgressbar",
            background="#19b7a0",
            troughcolor="#e8e0f4",
            bordercolor="#e8e0f4",
            lightcolor="#19b7a0",
            darkcolor="#19b7a0",
            thickness=12,
        )

    def clear_screen(self):
        self.root.unbind_all("<MouseWheel>")
        self.root.unbind_all("<Button-4>")
        self.root.unbind_all("<Button-5>")
        for child in self.main_frame.winfo_children():
            child.destroy()

    def show_vocab_screen(self):
        self.clear_screen()

        ttk.Label(
            self.main_frame,
            text="Vocabulary Practice",
            style="Title.TLabel",
        ).pack(anchor="w", pady=(0, 6))
        ttk.Label(
            self.main_frame,
            text="Paste da words & def below, or leave as \'file - load\' to load from file.",
            wraplength=720,
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(0, 12))

        editor_frame = ttk.Frame(
            self.main_frame,
            padding=3,
            style="Card.TFrame",
        )
        editor_frame.pack(fill="both", expand=True)
        self.vocab_text = tk.Text(
            editor_frame,
            height=10,
            wrap="word",
            font=("Segoe UI", 11),
            undo=True,
            background="#ffffff",
            foreground="#24324b",
            insertbackground="#7041dc",
            selectbackground="#eadfff",
            relief="flat",
            padx=12,
            pady=10,
        )
        editor_scrollbar = ttk.Scrollbar(
            editor_frame,
            orient="vertical",
            command=self.vocab_text.yview,
        )
        self.vocab_text.configure(yscrollcommand=editor_scrollbar.set)
        self.vocab_text.pack(side="left", fill="both", expand=True)
        editor_scrollbar.pack(side="right", fill="y")
        self.vocab_text.insert("1.0", "file - load")

        settings = ttk.LabelFrame(
            self.main_frame,
            text="Question types",
            padding=10,
            style="Card.TLabelframe",
        )
        settings.pack(fill="x", pady=(12, 0))

        self.multiple_choice_var = tk.BooleanVar(value=True)
        self.matching_var = tk.BooleanVar(value=True)
        self.word_bank_var = tk.BooleanVar(value=False)
        self.fill_blank_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            settings,
            text="Mix in multiple choice (word to definition)",
            variable=self.multiple_choice_var,
        ).pack(anchor="w")
        ttk.Checkbutton(
            settings,
            text="Mix in matching rounds (2-5 words)",
            variable=self.matching_var,
        ).pack(anchor="w")
        ttk.Checkbutton(
            settings,
            text="Mix in fill-in-the-blank questions",
            variable=self.fill_blank_var,
        ).pack(anchor="w")
        ttk.Checkbutton(
            settings,
            text="Use a word bank for definition to word questions",
            variable=self.word_bank_var,
        ).pack(anchor="w")

        self.error_label = ttk.Label(
            self.main_frame,
            text="",
            foreground="#b42318",
            wraplength=720,
        )
        self.error_label.pack(anchor="w", pady=(8, 0))
        ttk.Button(
            self.main_frame,
            text="Start Practice",
            command=self.start_practice,
            style="Primary.TButton",
        ).pack(anchor="e", pady=(10, 0))

    def start_practice(self):
        self.word_n_def = ""
        try:
            #print(self.vocab_text.get("1.0", "end-1c").strip().lower())

            #this if goes first so that it checks if the user wants to load from file first before checking if they inputed any vocab words so that it doesn't skip it
            if self.vocab_text.get("1.0", "end-1c").strip().lower() == "file - load": #if the user wants to load file, this checks that and starts loading file
                for file_name in open("file_name(DO_NOT_DELETE_PLZ).txt"):  # i have as this so that i dont have to look through the code to find where to change the file name and can have multiple files in the file name.txt file
                    #print(f"Loading vocab from file: {file_name.strip()}")
                    for line in open(file_name):
                        self.word_n_def += line.strip() + "\n"
                
                vocab_words_and_definitions = seperate_vocab(self.word_n_def)
            
                
            elif self.vocab_text: #check if inputed any vocab words first
                            #print(self.vocab_text.get("1.0", "end-1c").strip()) 
                            vocab_words_and_definitions = seperate_vocab(
                                self.vocab_text.get("1.0", "end-1c").strip()
                            )

        except ValueError as error:
            self.error_label.configure(text=str(error))
            return

        self.vocab_cards = vocab_words_and_definitions.copy()
        shuffled_cards = list(vocab_words_and_definitions.items())
        random.shuffle(shuffled_cards)
        self.cards = deque(shuffled_cards)
        self.total_cards = len(self.cards)
        self.words_to_review = set()
        self.mastered_words = set()
        self.first_try_correct = 0
        self.multiple_choice_enabled = self.multiple_choice_var.get()
        self.matching_enabled = self.matching_var.get()
        self.word_bank_enabled = self.word_bank_var.get()
        self.fill_blank_enabled = self.fill_blank_var.get()
        self.show_practice_screen()
        self.show_next_card()

    def show_practice_screen(self):
        self.clear_screen()

        ttk.Label(
            self.main_frame,
            text="Practice",
            style="Title.TLabel",
        ).pack(anchor="w", pady=(0, 8))
        header = ttk.Frame(self.main_frame, style="Header.TFrame")
        header.pack(fill="x", pady=(0, 10))
        ttk.Button(
            header,
            text="End Practice",
            command=self.show_summary,
            style="Secondary.TButton",
        ).pack(side="right")

        self.progress_label = ttk.Label(
            self.main_frame,
            text="",
            font=("Segoe UI", 10),
            style="Subtitle.TLabel",
        )
        self.progress_label.pack(anchor="w", pady=(0, 10))
        self.progress_bar = ttk.Progressbar(
            self.main_frame,
            mode="determinate",
            maximum=max(1, self.total_cards),
        )
        self.progress_bar.pack(fill="x", pady=(0, 16))

        self.question_area = ttk.Frame(
            self.main_frame,
            style="App.TFrame",
        )
        self.question_area.pack(fill="both", expand=True)

        self.question_canvas = tk.Canvas(
            self.question_area,
            background="#f6f1ff",
            highlightthickness=0,
            bd=0,
        )
        self.question_canvas.pack(side="left", fill="both", expand=True)
        self.question_scrollbar = ttk.Scrollbar(
            self.question_area,
            orient="vertical",
            command=self.question_canvas.yview,
            style="Vertical.TScrollbar",
        )
        self.question_scrollbar.pack(side="right", fill="y")
        self.question_canvas.configure(
            yscrollcommand=self.question_scrollbar.set,
        )
        self.root.bind_all("<MouseWheel>", self.scroll_question)

        self.card_frame = tk.Frame(
            self.question_canvas,
            background="#ffffff",
            bd=0,
            padx=26,
            pady=24,
        )
        self.question_window = self.question_canvas.create_window(
            16,
            16,
            anchor="nw",
            window=self.card_frame,
        )
        self.card_background = self.question_canvas.create_polygon(
            self.rounded_rectangle_points(0, 0, 120, 120, 22),
            smooth=True,
            splinesteps=24,
            fill="#ffffff",
            outline="#e6def2",
            width=1,
        )
        self.question_canvas.tag_lower(self.card_background)
        self.card_frame.bind("<Configure>", self.update_question_scrollregion)
        self.question_canvas.bind("<Configure>", self.resize_question_card)
    @staticmethod
    def rounded_rectangle_points(left, top, right, bottom, radius):
        return (
            left + radius, top,
            right - radius, top,
            right, top,
            right, top + radius,
            right, bottom - radius,
            right, bottom,
            right - radius, bottom,
            left + radius, bottom,
            left, bottom,
            left, bottom - radius,
            left, top + radius,
            left, top,
        )

    def resize_question_card(self, event):
        card_width = max(1, event.width - 32)
        self.question_canvas.itemconfigure(
            self.question_window,
            width=card_width,
        )
        self.update_question_scrollregion()

    def update_question_scrollregion(self, event=None):
        card_width = max(1, self.question_canvas.winfo_width() - 32)
        card_height = max(
            1,
            event.height if event is not None else self.card_frame.winfo_reqheight(),
        )
        self.question_canvas.coords(
            self.card_background,
            *self.rounded_rectangle_points(
                0,
                0,
                card_width + 32,
                card_height + 32,
                22,
            ),
        )
        self.question_canvas.configure(
            scrollregion=(0, 0, card_width + 32, card_height + 32),
        )
        self.question_canvas.yview_moveto(0)

    def scroll_question(self, event):
        hovered_widget = self.root.winfo_containing(event.x_root, event.y_root)
        while hovered_widget is not None:
            if hovered_widget is self.question_area:
                break
            hovered_widget = hovered_widget.master
        else:
            return None

        if getattr(event, "num", None) == 4:
            amount = -1
        elif getattr(event, "num", None) == 5:
            amount = 1
        else:
            amount = -1 if event.delta > 0 else 1
        self.question_canvas.yview_scroll(amount, "units")
        return "break"

    def show_next_card(self):
        if not self.cards:
            self.current_cards = []
            self.show_summary()
            return

        #available_types = ["definition"]  #this was commented out because none of the if statements check for this and so if you chose say for exmaple only multiple chose it would show multiple choice and whatever is in the else statement but im not deleting it rn because i dont remember why i put it and want to leave it in case it has a purpose
        available_types = [] # define emtpy list to use later to store types to use
        if self.multiple_choice_enabled:#checks if multiple choice is enabled
            available_types.append("multiple_choice") #if so, adds it to available types to use
        if self.matching_enabled and len(self.cards) >= 2: #im not putting comments for the other if statements because they are obvious and i already did the top one
            available_types.append("matching")
        if self.fill_blank_enabled:
            available_types.append("fill_blank")

        self.question_type = random.choice(available_types) # chooses a random type to use as the next question

        #print("Available question types:", available_types)
        #print("chosen question type:", self.question_type) #just sone print statemnets for debugginh

        if self.question_type == "matching": #obviously checks if the question type is matching and if so, chooses a random number of cards to use for the matching question
            round_size = random.randint(2, min(5, len(self.cards)))
            self.current_cards = [
                self.cards.popleft() for _ in range(round_size)
            ]
        else:
            self.current_cards = [self.cards.popleft()]

        self.hint_number = 0
        self.progress_label.configure( #the label to show progress
            text=(
                f"Words correct: {len(self.mastered_words)} / {self.total_cards}"
                f"    |    words remaining: {len(self.cards) + len(self.current_cards)}"
            )
        )
        self.progress_bar.configure(value=len(self.mastered_words)) # bar to show progress cuz bar is cool
        self.render_question() #renders the question based on the question type and the current cards

    def render_question(self):
        # clear the card frame of any previous question widgets so nothing oveerlaps or messes things up cuz thats a pain and dont look good
        for child in self.card_frame.winfo_children():
            child.destroy()

        #reset everything to avoid mixups
        self.answer_entry = None
        self.hint_button = None
        self.dont_know_button = None
        self.question_word_bank_var = None
        self.question_word_bank_frame = None
        self.question_answer_var = None

        #creat title blank, used later
        self.question_title = ttk.Label(
            self.card_frame,
            text="",
            font=("Segoe UI", 16, "bold"),
            style="Card.TLabel",
        )
        self.question_title.pack(anchor="w", pady=(0, 16))


        #create control frame along bottom to hold buttons and stuff
        controls = ttk.Frame(self.card_frame, style="Card.TFrame")
        controls.pack(fill="x", side="bottom", pady=(12, 0))

        #create widgets for feedback and hints
        self.feedback_label = ttk.Label(
            self.card_frame,
            text="",
            font=("Segoe UI", 11, "bold"),
            wraplength=700,
            style="Card.TLabel",
        )
        self.feedback_label.pack(anchor="w", pady=(8, 4))
        self.hint_label = ttk.Label(
            self.card_frame,
            text="",
            wraplength=700,
            style="Card.TLabel",
        )
        self.hint_label.pack(anchor="w", pady=(0, 4))

        # add check botton 
        self.action_button = ttk.Button(
            controls,
            text="Check Answer",
            command=self.submit_answer,
            style="Primary.TButton",
        )
        self.action_button.pack(side="right")

        #render question based off which question types where choses
        if self.question_type == "matching":
            self.render_matching_question(controls) # card thing for this was made earlier
            return

        word, definition = self.current_cards[0]
        if self.question_type == "multiple_choice":
            self.render_definition_choices(word, controls)
        elif self.question_type == "fill_blank":
            self.render_fill_blank_question(word, definition, controls)
        else:
            self.render_word_question(word, definition, controls)

    def render_word_question(self, word, definition, controls):
        self.question_title.configure(text="Which word matches this definition?")
        ttk.Label(
            self.card_frame,
            text=definition,
            font=("Segoe UI", 15),
            wraplength=700,
            justify="left",
            style="Card.TLabel",
        ).pack(anchor="w", fill="x", pady=(4, 18))

        self.hint_button = ttk.Button(
            controls,
            text="Hint",
            command=self.show_hint,
            style="Secondary.TButton",
        )
        self.hint_button.pack(side="left")
        self.dont_know_button = ttk.Button(
            controls,
            text="I don't know",
            command=self.mark_unknown,
            style="Secondary.TButton",
        )
        self.dont_know_button.pack(side="left", padx=(8, 0))

        if self.word_bank_enabled:
            self.answer_var = tk.StringVar(value="")
            choices = self.make_word_choices(word)
            choices_frame = ttk.Frame(self.card_frame, style="Card.TFrame")
            choices_frame.pack(anchor="w", fill="x")
            for choice in choices:
                ttk.Radiobutton(
                    choices_frame,
                    text=choice,
                    value=choice,
                    variable=self.answer_var,
                    style="Card.TRadiobutton",
                ).pack(anchor="w", pady=2)
            self.answer_entry = None
        else:
            self.answer_entry = ttk.Entry(
                self.card_frame,
                font=("Segoe UI", 13),
            )
            self.answer_entry.pack(fill="x", pady=(0, 12))
            self.answer_entry.bind(
                "<Return>",
                lambda *_: self.submit_answer(),
            )
            self.answer_entry.focus_set()

    def render_fill_blank_question(self, word, definition, controls):
        self.question_title.configure(
            text="Fill in the missing vocabulary word",
        )
        ttk.Label(
            self.card_frame,
            text="Complete the definition:",
            style="Prompt.TLabel",
        ).pack(anchor="w", pady=(2, 8))
        ttk.Label(
            self.card_frame,
            text=self.make_fill_blank_prompt(word, definition),
            font=("Segoe UI", 16, "bold"),
            wraplength=700,
            justify="left",
            style="Card.TLabel",
        ).pack(anchor="w", fill="x", pady=(0, 18))

        self.hint_button = ttk.Button(
            controls,
            text="Hint",
            command=self.show_hint,
            style="Secondary.TButton",
        )
        self.hint_button.pack(side="left")
        self.dont_know_button = ttk.Button(
            controls,
            text="I don't know",
            command=self.mark_unknown,
            style="Secondary.TButton",
        )
        self.dont_know_button.pack(side="left", padx=(8, 0))

        self.question_word_bank_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self.card_frame,
            text="Show word bank for this question",
            variable=self.question_word_bank_var,
            command=self.toggle_question_word_bank,
        ).pack(anchor="w", pady=(0, 8))
        self.question_word_bank_frame = ttk.Frame(
            self.card_frame,
            style="Card.TFrame",
        )
        self.question_word_bank_frame.pack(anchor="w", fill="x", pady=(0, 12))
        self.question_answer_var = tk.StringVar(value="")
        self.answer_entry = ttk.Entry(
            self.card_frame,
            font=("Segoe UI", 13),
        )
        self.answer_entry.pack(fill="x", pady=(0, 12))
        self.answer_entry.bind(
            "<Return>",
            lambda *_: self.submit_answer(),
        )
        self.answer_entry.focus_set()

    @staticmethod
    def make_fill_blank_prompt(word, definition):
        word_pattern = re.compile(
            rf"(?<!\w){re.escape(word)}(?!\w)",
            re.IGNORECASE,
        )
        if word_pattern.search(definition):
            return word_pattern.sub("________", definition)
        return f"________ — {definition}"

    def toggle_question_word_bank(self):
        if self.question_word_bank_frame is None:
            return
        for child in self.question_word_bank_frame.winfo_children():
            child.destroy()

        if not self.question_word_bank_var.get():
            self.answer_entry.configure(state="normal")
            self.answer_entry.pack(fill="x", pady=(0, 12))
            self.answer_entry.focus_set()
            return

        self.answer_entry.pack_forget()
        self.answer_entry.configure(state="normal")
        word = self.current_cards[0][0]
        for choice in self.make_word_choices(word):
            ttk.Radiobutton(
                self.question_word_bank_frame,
                text=choice,
                value=choice,
                variable=self.question_answer_var,
                style="Card.TRadiobutton",
            ).pack(anchor="w", pady=2)

    def get_file_questions(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                vocab = file.read()
        except Exception as error:
            raise ValueError(f"Error reading file: {error}")

        return seperate_vocab(vocab)

    def render_definition_choices(self, word, controls):
        self.question_title.configure(
            text="Choose the definition for this word",
        )
        ttk.Label(
            self.card_frame,
            text=word,
            font=("Segoe UI", 17, "bold"),
            wraplength=700,
            style="Card.TLabel",
        ).pack(anchor="w", pady=(4, 14))

        self.choice_var = tk.StringVar(value="")
        choices = self.make_definition_choices(word)
        choices_frame = ttk.Frame(self.card_frame, style="Card.TFrame")
        choices_frame.pack(anchor="w", fill="both", expand=True)
        for index, (_, definition) in enumerate(choices):
            ttk.Radiobutton(
                choices_frame,
                text="\n".join(textwrap.wrap(definition, width=76)),
                value=str(index),
                variable=self.choice_var,
                style="Card.TRadiobutton",
            ).pack(anchor="w", fill="x", pady=4)

        self.dont_know_button = ttk.Button(
            controls,
            text="I don't know",
            command=self.mark_unknown,
        )
        self.dont_know_button.pack(side="left")
        self.choice_options = choices

    def render_matching_question(self, controls):
        self.question_title.configure(
            text=f"Match these {len(self.current_cards)} words to their definitions",
        )
        shuffled_definitions = list(self.current_cards)
        random.shuffle(shuffled_definitions)
        self.matching_definitions = shuffled_definitions
        self.matching_vars = {}

        definitions_frame = ttk.LabelFrame(
            self.card_frame,
            text="Definitions",
            padding=10,
            style="Card.TLabelframe",
        )
        definitions_frame.pack(fill="x", pady=(4, 12))
        for index, (_, definition) in enumerate(shuffled_definitions, start=1):
            ttk.Label(
                definitions_frame,
                text=f"{index}. {definition}",
                wraplength=680,
                justify="left",
                style="Card.TLabel",
            ).pack(anchor="w", pady=3)

        matches_frame = ttk.LabelFrame(
            self.card_frame,
            text="Choose a definition number for each word",
            padding=10,
            style="Card.TLabelframe",
        )
        matches_frame.pack(fill="both", expand=True)
        number_choices = [str(index) for index in range(1, len(self.current_cards) + 1)]
        for row, (word, _) in enumerate(self.current_cards):
            ttk.Label(
                matches_frame,
                text=word,
                style="Card.TLabel",
            ).grid(
                row=row,
                column=0,
                sticky="w",
                padx=(0, 12),
                pady=5,
            )
            answer_var = tk.StringVar(value="")
            self.matching_vars[word] = answer_var
            ttk.Combobox(
                matches_frame,
                textvariable=answer_var,
                values=number_choices,
                state="readonly",
                width=8,
            ).grid(row=row, column=1, sticky="w", pady=5)

        self.dont_know_button = ttk.Button(
            controls,
            text="I don't know",
            command=self.mark_unknown,
        )
        self.dont_know_button.pack(side="left")

    def make_word_choices(self, answer_word):
        choices = [answer_word]
        distractors = [
            word for word in self.vocab_cards if word != answer_word
        ]
        random.shuffle(distractors)
        choices.extend(distractors[:3])
        random.shuffle(choices)
        return choices

    def make_definition_choices(self, answer_word):
        answer_card = (
            answer_word,
            self.vocab_cards[answer_word],
        )
        distractors = [
            (word, definition) for word, definition in self.vocab_cards.items()
            if word != answer_word and definition != answer_card[1]
        ]
        random.shuffle(distractors)
        choices = [answer_card, *distractors[:3]]
        random.shuffle(choices)
        return choices

    def show_hint(self):
        if not self.current_cards or self.question_type == "matching":
            return

        self.hint_number += 1
        self.hint_label.configure(
            text=get_hint(self.current_cards[0][0], self.hint_number)
        )

    def submit_answer(self):
        if not self.current_cards:
            return

        if self.question_type == "matching":
            self.submit_matching_answer()
        elif self.question_type == "multiple_choice":
            self.submit_definition_choice()
        else:
            self.submit_word_answer()

    def submit_word_answer(self):
        word, _ = self.current_cards[0]
        if (
            self.question_type == "fill_blank"
            and self.question_word_bank_var is not None
            and self.question_word_bank_var.get()
        ):
            answer = self.question_answer_var.get()
        elif self.question_type == "definition" and self.word_bank_enabled:
            answer = self.answer_var.get()
        else:
            answer = self.answer_entry.get().strip()
        if not answer:
            self.feedback_label.configure(
                text="Choose or enter an answer, ask for a hint, or choose 'I don't know'.",
                foreground="#9a6700",
            )
            return

        if _answers_match(answer, word):
            self.mark_correct([word])
        else:
            self.mark_incorrect([word], f"The answer is '{word}'.")

    def submit_definition_choice(self):
        word = self.current_cards[0][0]
        selected = self.choice_var.get()
        if not selected:
            self.feedback_label.configure(
                text="Choose a definition or choose 'I don't know'.",
                foreground="#9a6700",
            )
            return

        selected_card = self.choice_options[int(selected)]
        if _answers_match(selected_card[0], word):
            self.mark_correct([word])
        else:
            self.mark_incorrect(
                [word],
                f"The definition of '{word}' is: {self.current_cards[0][1]}",
            )

    def submit_matching_answer(self):
        if any(not variable.get() for variable in self.matching_vars.values()):
            self.feedback_label.configure(
                text="Choose a definition number for every word.",
                foreground="#9a6700",
            )
            return

        definition_numbers = {
            word: index
            for index, (word, _) in enumerate(self.matching_definitions, start=1)
        }
        correct_words = [
            word
            for word, answer_var in self.matching_vars.items()
            if answer_var.get() == str(definition_numbers[word])
        ]
        missed_words = [
            word for word, _ in self.current_cards if word not in correct_words
        ]

        if not missed_words:
            self.mark_correct(correct_words)
            return

        for word in correct_words:
            self.mastered_words.add(word)
            if word not in self.words_to_review:
                self.first_try_correct += 1
        missed_answers = ", ".join(
            f"{word} -> {definition_numbers[word]}" for word in missed_words
        )
        self.mark_incorrect(
            missed_words,
            f"Review: {missed_answers}.",
        )

    def mark_correct(self, words):
        for word in words:
            self.mastered_words.add(word)
            if word not in self.words_to_review:
                self.first_try_correct += 1
        self.feedback_label.configure(
            text="Correct!" if len(words) == 1 else "All matches are correct!",
            foreground="#18794e",
        )
        if hasattr(self, "progress_bar"):
            self.progress_bar.configure(value=len(self.mastered_words))
        self.prepare_next_button()

    def mark_incorrect(self, words, message):
        current_cards_by_word = {
            word: (word, definition) for word, definition in self.current_cards
        }
        for word in words:
            self.words_to_review.add(word)
            self.cards.append(current_cards_by_word[word])
        self.feedback_label.configure(
            text=f"{message} These will come back later.",
            foreground="#b42318",
        )
        self.prepare_next_button()

    def mark_unknown(self):
        if not self.current_cards:
            return

        if self.question_type == "matching":
            answers = ", ".join(
                f"{word} -> {index}"
                for index, (word, _) in enumerate(
                    self.matching_definitions,
                    start=1,
                )
            )
            message = f"Answers: {answers}."
        elif self.question_type == "multiple_choice":
            word, definition = self.current_cards[0]
            message = f"The definition of '{word}' is: {definition}"
        else:
            message = f"The answer is '{self.current_cards[0][0]}'."

        self.mark_incorrect(
            [word for word, _ in self.current_cards],
            message,
        )

    def prepare_next_button(self):
        if self.answer_entry is not None:
            self.answer_entry.configure(state="disabled")
        self.action_button.configure(
            text="Next Question",
            command=self.show_next_card,
            style="Primary.TButton",
        )
        self.action_button.focus_set()
        self.dont_know_button.configure(state="disabled")
        if self.hint_button is not None:
            self.hint_button.configure(state="disabled")

    def show_summary(self):
        completed = (
            len(self.mastered_words) == self.total_cards and not self.cards
        )

        self.clear_screen()
        ttk.Label(
            self.main_frame,
            text="All done!" if completed else "Practice ended",
            style="Title.TLabel",
        ).pack(anchor="w", pady=(0, 14))
        ttk.Label(
            self.main_frame,
            text=(
                f"Mastered: {len(self.mastered_words)} / {self.total_cards}\n"
                f"Correct on first try: {self.first_try_correct}\n"
                f"Cards sent back for review: {len(self.words_to_review)}"
            ),
            font=("Segoe UI", 14),
            justify="left",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(0, 24))
        ttk.Button(
            self.main_frame,
            text="Practice Again",
            command=self.show_vocab_screen,
            style="Primary.TButton",
        ).pack(anchor="w")
        


def main():
    root = tk.Tk()
    VocabFlashcardApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
