
from collections import Counter
from random import choice

WORDS = ["verity", "falsity", "cruelty", "lovity"]
SEQUENCE_LENGTH = 8
MAX_ATTEMPTS = 6


def new_game():
    return [choice(WORDS) for _ in range(SEQUENCE_LENGTH)]


def score_guess(guess, answer):
    feedback = ["black"] * len(answer)
    remaining = Counter()

    for index, (word, answer_word) in enumerate(
        zip(guess, answer)
    ):
        if word == answer_word:
            feedback[index] = "green"
        else:
            remaining[answer_word] += 1

    for index, word in enumerate(guess):
        if feedback[index] != "green" and remaining[word] > 0:
            feedback[index] = "yellow"
            remaining[word] -= 1

    return feedback


if __name__ == "__main__":
    answer = new_game()

    for attempt in range(1, MAX_ATTEMPTS + 1):
        while True:
            guess = input(
                f"Guess {attempt}/6 (enter 8 words):\n"
            ).lower().split()

            if len(guess) == SEQUENCE_LENGTH:
                break

            print("Please enter exactly 8 words.")

        print(" ".join(score_guess(guess, answer)))

        if guess == answer:
            print("You got it!")
            break
    else:
        print("Out of guesses! The answer was:", " ".join(answer))
