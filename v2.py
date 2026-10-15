import re
from collections import deque


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


def practice_vocab(vocab_words_and_definitions):
    if not vocab_words_and_definitions:
        raise ValueError("Enter at least one vocabulary word and definition.")

    cards = deque(vocab_words_and_definitions.items())
    words_to_review = set()
    mastered_words = set()
    first_try_correct = 0
    quit_early = False

    print("\nFlashcards: read the definition and type the matching word.")
    print("Type 'hint' for a clue, or 'I don't know' to see the answer.")
    print("Missed cards will come back later. Type 'quit' to end practice.\n")

    while cards:
        word, definition = cards.popleft()
        hint_number = 0
        print(f"Definition: {definition}")

        while True:
            answer = input("Word: ").strip()
            command = answer.casefold()

            if command in {"quit", "q"}:
                quit_early = True
                break
            if command in {"hint", "h", "?"}:
                hint_number += 1
                print(get_hint(word, hint_number))
                continue
            if command in {"i don't know", "i dont know", "idk"}:
                print(f"The word was '{word}'. It will come back later.")
                words_to_review.add(word)
                cards.append((word, definition))
                break

            if _normalize_answer(answer) == _normalize_answer(word):
                print("Correct!\n")
                mastered_words.add(word)
                if word not in words_to_review:
                    first_try_correct += 1
                break

            print(f"Not quite. The word was '{word}'. It will come back later.\n")
            words_to_review.add(word)
            cards.append((word, definition))
            break

        if quit_early:
            break

    mastered = len(mastered_words)
    print("\nPractice ended." if quit_early else "\nAll done!")
    print(
        f"Mastered: {mastered}/{len(vocab_words_and_definitions)}"
        f" | Correct on first try: {first_try_correct}"
        f" | Cards reviewed: {len(words_to_review)}"
    )
    return {
        "total": len(vocab_words_and_definitions),
        "mastered": mastered,
        "first_try_correct": first_try_correct,
        "reviewed": len(words_to_review),
    }


if __name__ == "__main__":
    vocab = input(
        "Paste vocabulary entries (number. word - definition):\n"
    ).strip()
    if not vocab:
        print("No vocabulary entered.")
    else:
        try:
            practice_vocab(seperate_vocab(vocab))
        except ValueError as error:
            print(f"Could not read the vocabulary list: {error}")
