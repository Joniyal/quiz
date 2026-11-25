"""
Logic module for loading, shuffling, scoring, and saving a quiz.
"""

import csv
import os
import random


class QuizLogic:
    """Manage quiz questions, progress, scoring, and score history."""

    def __init__(self, data_file=None, scores_file=None):
        """Set file locations and initialize in-memory quiz state."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(base_dir, "data")
        self.data_file = data_file or os.path.join(data_dir, "questions.csv")
        self.scores_file = scores_file or os.path.join(data_dir, "scores.csv")
        self.questions = []
        self.current_index = 0
        self.score = 0

    def load_questions(self):
        """FR1: Load and validate ten questions from the CSV file."""
        if not os.path.isfile(self.data_file):
            raise OSError("Question file is missing: " + self.data_file)
        questions = []
        try:
            with open(self.data_file, "r", encoding="utf-8", newline="") as file:
                reader = csv.DictReader(file)
                required = {"question", "option1", "option2",
                            "option3", "option4", "answer"}
                if reader.fieldnames is None or not required.issubset(reader.fieldnames):
                    raise ValueError("Question file has invalid columns.")
                for row in reader:
                    question = (row.get("question") or "").strip()
                    options = [
                        (row.get(f"option{index}") or "").strip()
                        for index in range(1, 5)
                    ]
                    if not question or any(not option for option in options):
                        raise ValueError("Question file contains an empty field.")
                    answer = int((row.get("answer") or "").strip())
                    if answer < 0 or answer > 3:
                        raise ValueError("Answer index must be between 0 and 3.")
                    questions.append({
                        "question": question,
                        "options": options,
                        "answer": answer,
                    })
        except (csv.Error, KeyError, ValueError, AttributeError) as error:
            raise ValueError("Could not read question file: " + str(error))
        if len(questions) != 10:
            raise ValueError("Question file must contain exactly 10 questions.")
        return questions

    def start_quiz(self):
        """FR1 / FR5: Reset state and shuffle questions for a new attempt."""
        self.questions = self.load_questions()
        random.shuffle(self.questions)
        self.current_index = 0
        self.score = 0

    def current_question(self):
        """FR2: Return the current question or None after the final answer."""
        if self.current_index >= len(self.questions):
            return None
        return self.questions[self.current_index]

    def submit_answer(self, selected_index):
        """FR3: Check a selected option and advance one question."""
        if selected_index < 0 or selected_index > 3:
            raise IndexError("Selected option is out of range.")
        question = self.current_question()
        if question is None:
            raise IndexError("The quiz is already complete.")
        is_correct = selected_index == question["answer"]
        if is_correct:
            self.score += 1
        self.current_index += 1
        return is_correct

    def skip_question(self):
        """Move to the next question without changing the score."""
        if self.current_index < len(self.questions):
            self.current_index += 1

    def save_score(self, percentage):
        """FR4: Append the final score to a CSV score history."""
        parent = os.path.dirname(self.scores_file)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        exists = os.path.isfile(self.scores_file)
        try:
            with open(self.scores_file, "a", encoding="utf-8", newline="") as file:
                writer = csv.writer(file)
                if not exists:
                    writer.writerow(["score", "total", "percentage"])
                writer.writerow([self.score, len(self.questions), percentage])
            return True
        except OSError as error:
            raise OSError("Could not save score: " + str(error))
