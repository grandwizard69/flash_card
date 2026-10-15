import re
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


class VocabFlashcardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Vocabulary Flashcards")
        self.root.geometry("760x600")
        self.root.minsize(560, 460)

        self.cards = deque()
        self.current_card = None
        self.total_cards = 0
        self.words_to_review = set()
        self.mastered_words = set()
        self.first_try_correct = 0
        self.hint_number = 0

        self.main_frame = ttk.Frame(root, padding=24)
        self.main_frame.pack(fill="both", expand=True)
        self.show_vocab_screen()

    def clear_screen(self):
        for child in self.main_frame.winfo_children():
            child.destroy()

    def show_vocab_screen(self):
        self.clear_screen()

        ttk.Label(
            self.main_frame,
            text="Vocabulary Flashcards",
            font=("Segoe UI", 23, "bold"),
        ).pack(anchor="w", pady=(0, 6))
        ttk.Label(
            self.main_frame,
            text="Paste your word list below. Put each word and definition "
            "on a line, separated by ' - '. Numbering is optional.",
            wraplength=680,
        ).pack(anchor="w", pady=(0, 14))

        self.vocab_text = tk.Text(
            self.main_frame,
            height=13,
            wrap="word",
            font=("Segoe UI", 11),
            undo=True,
        )
        self.vocab_text.pack(fill="both", expand=True)
        self.vocab_text.insert(
            "1.0",
            "1. Parietal Lobe - A sensory processing area of the brain.\n"
            "2. Lobotomy - A surgical procedure that severs nerve pathways "
            "in a lobe of the brain.",
        )

        self.error_label = ttk.Label(
            self.main_frame,
            text="",
            foreground="#b42318",
            wraplength=680,
        )
        self.error_label.pack(anchor="w", pady=(8, 0))
        ttk.Button(
            self.main_frame,
            text="Start Practice",
            command=self.start_practice,
        ).pack(anchor="e", pady=(12, 0))

    def start_practice(self):
        try:
            vocab_words_and_definitions = seperate_vocab(
                self.vocab_text.get("1.0", "end-1c").strip()
            )
        except ValueError as error:
            self.error_label.configure(text=str(error))
            return

        self.cards = deque(vocab_words_and_definitions.items())
        self.total_cards = len(self.cards)
        self.words_to_review = set()
        self.mastered_words = set()
        self.first_try_correct = 0
        self.show_practice_screen()
        self.show_next_card()

    def show_practice_screen(self):
        self.clear_screen()

        header = ttk.Frame(self.main_frame)
        header.pack(fill="x", pady=(0, 16))
        ttk.Label(
            header,
            text="Flashcard Practice",
            font=("Segoe UI", 21, "bold"),
        ).pack(side="left")
        ttk.Button(
            header,
            text="End Practice",
            command=self.show_summary,
        ).pack(side="right")

        self.progress_label = ttk.Label(
            self.main_frame,
            text="",
            font=("Segoe UI", 10),
        )
        self.progress_label.pack(anchor="w", pady=(0, 10))

        self.card_frame = ttk.LabelFrame(
            self.main_frame,
            text="What word matches this definition?",
            padding=20,
        )
        self.card_frame.pack(fill="both", expand=True)

        self.definition_label = ttk.Label(
            self.card_frame,
            text="",
            font=("Segoe UI", 15),
            wraplength=640,
            justify="left",
        )
        self.definition_label.pack(anchor="w", fill="x", pady=(4, 18))

        self.answer_entry = ttk.Entry(
            self.card_frame,
            font=("Segoe UI", 13),
        )
        self.answer_entry.pack(fill="x", pady=(0, 12))
        self.answer_entry.bind(
            "<Return>",
            lambda *_: self.submit_answer(),
        )

        self.feedback_label = ttk.Label(
            self.card_frame,
            text="",
            font=("Segoe UI", 11, "bold"),
            wraplength=640,
        )
        self.feedback_label.pack(anchor="w", pady=(0, 8))

        self.hint_label = ttk.Label(
            self.card_frame,
            text="",
            wraplength=640,
        )
        self.hint_label.pack(anchor="w", pady=(0, 12))

        controls = ttk.Frame(self.card_frame)
        controls.pack(fill="x", side="bottom")
        self.hint_button = ttk.Button(
            controls,
            text="Hint",
            command=self.show_hint,
        )
        self.hint_button.pack(side="left")
        self.dont_know_button = ttk.Button(
            controls,
            text="I don't know",
            command=self.mark_unknown,
        )
        self.dont_know_button.pack(side="left", padx=(8, 0))
        self.action_button = ttk.Button(
            controls,
            text="Check Answer",
            command=self.submit_answer,
        )
        self.action_button.pack(side="right")

    def show_next_card(self):
        if not self.cards:
            self.current_card = None
            self.show_summary()
            return

        self.current_card = self.cards.popleft()
        self.hint_number = 0
        self.progress_label.configure(
            text=(
                f"Mastered: {len(self.mastered_words)}"
                f" / {self.total_cards}"
                f"    |    Cards left in this round: {len(self.cards) + 1}"
            )
        )
        self.definition_label.configure(text=self.current_card[1])
        self.answer_entry.configure(state="normal")
        self.answer_entry.delete(0, "end")
        self.answer_entry.focus_set()
        self.feedback_label.configure(text="", foreground="")
        self.hint_label.configure(text="")
        self.hint_button.configure(state="normal")
        self.dont_know_button.configure(state="normal")
        self.action_button.configure(text="Check Answer", command=self.submit_answer)

    def show_hint(self):
        if self.current_card is None:
            return

        self.hint_number += 1
        self.hint_label.configure(
            text=get_hint(self.current_card[0], self.hint_number)
        )

    def submit_answer(self):
        if self.current_card is None or str(self.answer_entry["state"]) == "disabled":
            return

        word, _ = self.current_card
        answer = self.answer_entry.get().strip()
        if not answer:
            self.feedback_label.configure(
                text="Enter an answer, ask for a hint, or choose 'I don't know'.",
                foreground="#9a6700",
            )
            return

        if _normalize_answer(answer) == _normalize_answer(word):
            self.mastered_words.add(word)
            if word not in self.words_to_review:
                self.first_try_correct += 1
            self.feedback_label.configure(
                text="Correct!",
                foreground="#18794e",
            )
            self.prepare_next_button()
        else:
            self.queue_for_review(word)
            self.feedback_label.configure(
                text=f"Not quite. The answer is '{word}'. This card will come back later.",
                foreground="#b42318",
            )
            self.prepare_next_button()

    def mark_unknown(self):
        if self.current_card is None:
            return

        word, _ = self.current_card
        self.queue_for_review(word)
        self.feedback_label.configure(
            text=f"The answer is '{word}'. This card will come back later.",
            foreground="#9a6700",
        )
        self.prepare_next_button()

    def queue_for_review(self, word):
        self.words_to_review.add(word)
        self.cards.append(self.current_card)

    def prepare_next_button(self):
        self.answer_entry.configure(state="disabled")
        self.hint_button.configure(state="disabled")
        self.dont_know_button.configure(state="disabled")
        self.action_button.configure(
            text="Next Card",
            command=self.show_next_card,
        )
        self.action_button.focus_set()

    def show_summary(self):
        completed = (
            len(self.mastered_words) == self.total_cards and not self.cards
        )

        self.clear_screen()
        ttk.Label(
            self.main_frame,
            text="All done!" if completed else "Practice ended",
            font=("Segoe UI", 23, "bold"),
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
        ).pack(anchor="w", pady=(0, 24))
        ttk.Button(
            self.main_frame,
            text="Practice Again",
            command=self.show_vocab_screen,
        ).pack(anchor="w")


def main():
    root = tk.Tk()
    VocabFlashcardApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
