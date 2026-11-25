"""
Project        : MCQ Quiz App
Team           : <team number>
Members        : <member 1>, <member 2>, <member 3>
AI tools       : Microsoft Copilot
Run            : python main.py
"""

import ctypes
import random
import sys
import tkinter as tk
from tkinter import messagebox

from logic import QuizLogic


class RoundedButton(tk.Canvas):
    """A fixed-size canvas button with rounded corners."""

    def __init__(
        self, parent, text, command, background, hover_background, foreground,
        font, width=220, height=48, radius=12
    ):
        super().__init__(
            parent, width=width, height=height, bg=parent.cget("bg"),
            highlightthickness=0, bd=0, cursor="hand2"
        )
        self.command = command
        self.background = background
        self.hover_background = hover_background
        self.enabled = True
        x0, y0, x1, y1 = 1, 1, width - 1, height - 1
        diameter = radius * 2
        self.shape_items = [
            self.create_rectangle(
                x0 + radius, y0, x1 - radius, y1, fill=background, outline=background
            ),
            self.create_rectangle(
                x0, y0 + radius, x1, y1 - radius, fill=background, outline=background
            ),
            self.create_oval(
                x0, y0, x0 + diameter, y0 + diameter,
                fill=background, outline=background
            ),
            self.create_oval(
                x1 - diameter, y0, x1, y0 + diameter,
                fill=background, outline=background
            ),
            self.create_oval(
                x0, y1 - diameter, x0 + diameter, y1,
                fill=background, outline=background
            ),
            self.create_oval(
                x1 - diameter, y1 - diameter, x1, y1,
                fill=background, outline=background
            ),
        ]
        self.create_text(
            width / 2, height / 2, text=text, fill=foreground, font=font
        )
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)

    def set_background(self, color):
        """Update the rounded shape fill."""
        for item in self.shape_items:
            self.itemconfigure(item, fill=color, outline=color)

    def on_enter(self, _event):
        """Show the hover color when the mouse enters the button."""
        if self.enabled:
            self.set_background(self.hover_background)

    def on_leave(self, _event):
        """Restore the normal color when the mouse leaves the button."""
        self.set_background(self.background)

    def on_click(self, _event):
        """Run the button command when it is clicked."""
        if self.enabled:
            self.command()
        return "break"


class QuizApp:
    """Tkinter interface for the MCQ quiz application."""

    def __init__(self, root):
        """Initialize the window, widgets, and quiz state."""
        self.root = root
        self.root.title("MCQ Quiz App")
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_width = min(1280, max(360, int(screen_width * 0.85)))
        window_height = min(900, max(420, int(screen_height * 0.85)))
        x_position = max(0, (screen_width - window_width) // 2)
        y_position = max(0, (screen_height - window_height) // 2)
        root.geometry(
            f"{window_width}x{window_height}+{x_position}+{y_position}"
        )
        root.minsize(min(540, window_width), min(480, window_height))
        root.resizable(True, True)
        self.celebration_window = None
        self.celebration_canvas = None
        self.celebration_id = None
        self.celebration_frame = 0
        self.celebration_particles = []
        self.selection_warning = False
        self.colors = {
            "background": "#F3F6FB",
            "navy": "#172B4D",
            "blue": "#356AE6",
            "blue_hover": "#2858C7",
            "text": "#24324A",
            "muted": "#718096",
            "border": "#E2E8F0",
            "option": "#FFFFFF",
            "option_selected": "#EEF4FF",
            "option_hover": "#F3F7FF",
            "option_selected_hover": "#E2ECFF",
            "green": "#198754",
            "red": "#C0392B",
        }
        root.configure(bg=self.colors["background"])
        self.logic = QuizLogic()

        header = tk.Frame(root, bg=self.colors["navy"], height=72)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header, text="MCQ QUIZ", bg=self.colors["navy"], fg="#FFFFFF",
            font=("Arial", 24, "bold")
        ).pack(anchor="w", padx=32, pady=(22, 0))

        content = tk.Frame(root, bg=self.colors["background"])
        content.pack(fill="both", expand=True, padx=30, pady=24)
        self.card = tk.Frame(
            content, bg="#FFFFFF", highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        self.card.pack(fill="both", expand=True)

        status_row = tk.Frame(self.card, bg="#FFFFFF")
        status_row.pack(fill="x", padx=28, pady=(22, 10))
        self.info_label = tk.Label(
            status_row, text="", bg="#FFFFFF", fg=self.colors["text"],
            font=("Arial", 13, "bold")
        )
        self.info_label.pack(side="left")
        self.timer_label = tk.Label(
            status_row, text="", bg="#FFF4E5", fg="#9A5B00",
            font=("Arial", 12, "bold"), padx=14, pady=6
        )
        self.timer_label.pack(side="right")
        self.timer_id = None
        self.transition_id = None

        self.progress_track = tk.Frame(
            self.card, bg="#E8EDF5", height=7
        )
        self.progress_track.pack(fill="x", padx=28)
        self.progress_fill = tk.Frame(self.progress_track, bg=self.colors["blue"])
        self.progress_fill.place(relx=0, rely=0, relheight=1, relwidth=0)

        prompt_frame = tk.Frame(self.card, bg="#FFFFFF")
        prompt_frame.pack(fill="x", padx=28, pady=(22, 14))
        self.question_label = tk.Label(
            prompt_frame, text="", bg="#FFFFFF", fg=self.colors["text"],
            font=("Arial", 20, "bold"), wraplength=640, justify="left",
            anchor="w"
        )
        self.question_label.pack(fill="x")

        self.option_var = tk.IntVar(value=-1)
        self.option_buttons = []
        self.hovered_option = None
        self.hover_jobs = {}
        self.options_frame = tk.Frame(self.card, bg="#FFFFFF")
        self.options_frame.pack(fill="x", padx=22, pady=2)
        for index in range(4):
            button = tk.Button(
                self.options_frame,
                text="",
                command=lambda selected=index: self.select_option(selected),
                font=("Arial", 13),
                anchor="w",
                width=1,
                padx=14,
                pady=9,
                wraplength=500,
                bg=self.colors["option"],
                fg=self.colors["text"],
                activebackground=self.colors["option_selected"],
                activeforeground=self.colors["text"],
                highlightthickness=1,
                highlightbackground=self.colors["border"],
                highlightcolor=self.colors["blue"],
                relief="flat",
                bd=0,
                cursor="hand2",
            )
            button.pack(fill="x", padx=6, pady=4)
            button.bind(
                "<Enter>",
                lambda event, selected=index: self.on_option_enter(selected)
            )
            button.bind(
                "<Leave>",
                lambda event, selected=index: self.on_option_leave(selected)
            )
            self.option_buttons.append(button)

        self.result_label = tk.Label(
            self.card, text="", bg="#FFFFFF", fg=self.colors["muted"],
            font=("Arial", 12, "bold")
        )
        self.result_label.pack(pady=(10, 4))
        self.actions_frame = tk.Frame(self.card, bg="#FFFFFF")
        self.actions_frame.pack(pady=(4, 20))
        self.actions_frame.grid_rowconfigure(0, minsize=56)
        self.submit_button = RoundedButton(
            self.actions_frame, text="Submit Answer", command=self.submit_answer,
            font=("Arial", 12, "bold"), background=self.colors["blue"],
            hover_background=self.colors["blue_hover"], foreground="#FFFFFF"
        )
        self.submit_button.grid(row=0, column=0, pady=2)
        self.restart_button = RoundedButton(
            self.actions_frame, text="Restart Quiz", command=self.restart_quiz,
            font=("Arial", 11, "bold"), background="#EDF1F7",
            hover_background="#DFE6F0", foreground=self.colors["text"]
        )
        self.restart_button.grid(row=1, column=0, pady=2)

        self.root.bind("<Configure>", self.resize_layout)
        self.start_quiz()

    def resize_layout(self, event):
        """Adjust text wrapping to the available window width."""
        if event.widget is not self.root:
            return
        card_width = self.card.winfo_width()
        self.question_label.config(wraplength=max(200, card_width - 56))
        option_wraplength = max(180, card_width - 100)
        for button in self.option_buttons:
            button.config(wraplength=option_wraplength)
        if self.celebration_window is not None:
            self.position_celebration()

    def start_quiz(self):
        """Load questions and display the first question."""
        self.cancel_timers()
        try:
            self.logic.start_quiz()
        except (OSError, ValueError) as error:
            messagebox.showerror("Quiz Error", str(error))
            self.question_label.config(text="Quiz could not start.")
            return
        self.show_question()

    def show_question(self):
        """FR1 / FR2: Display the current question and four options."""
        self.transition_id = None
        self.cancel_timer()
        question = self.logic.current_question()
        if question is None:
            self.show_result()
            return
        self.submit_button.grid()
        self.options_frame.pack(
            before=self.result_label, fill="x", padx=22, pady=2
        )
        for button in self.option_buttons:
            button.config(state="normal")
        number = self.logic.current_index + 1
        total = len(self.logic.questions)
        self.info_label.config(text=f"Question {number} of {total}")
        self.question_label.config(text=question["question"])
        self.progress_fill.place(
            relx=0, rely=0, relheight=1,
            relwidth=(number - 1) / total if total else 0
        )
        for index, option in enumerate(question["options"]):
            self.option_buttons[index].config(text=option)
        self.option_var.set(-1)
        self.update_option_styles()
        self.selection_warning = False
        self.result_label.config(
            text=f"Current score: {self.logic.score}",
            fg=self.colors["muted"]
        )
        self.remaining_seconds = 60
        self.update_timer()

    def submit_answer(self):
        """FR3: Validate an answer choice and update the score."""
        selected = self.option_var.get()
        if selected < 0:
            self.selection_warning = True
            self.result_label.config(
                text="Please choose an option before submitting.",
                fg=self.colors["red"]
            )
            return
        self.cancel_timer()
        try:
            is_correct = self.logic.submit_answer(selected)
        except (ValueError, IndexError) as error:
            messagebox.showerror("Invalid Answer", str(error))
            return
        if is_correct:
            self.result_label.config(text="Correct!", fg=self.colors["green"])
        else:
            self.result_label.config(text="Wrong!", fg=self.colors["red"])
        self.transition_id = self.root.after(500, self.show_question)

    def update_timer(self):
        """FR6: Update the one-minute countdown and skip at zero."""
        timer_color = self.colors["red"] if self.remaining_seconds <= 10 else "#9A5B00"
        timer_bg = "#FDECEC" if self.remaining_seconds <= 10 else "#FFF4E5"
        self.timer_label.config(
            text=f"TIME  {self.remaining_seconds:02d}s",
            fg=timer_color,
            bg=timer_bg
        )
        if self.remaining_seconds <= 0:
            self.skip_question()
            return
        self.remaining_seconds -= 1
        self.timer_id = self.root.after(1000, self.update_timer)

    def skip_question(self):
        """FR6: Skip the current question when its one-minute limit expires."""
        self.cancel_timer()
        self.logic.skip_question()
        self.result_label.config(
            text="Time expired - question skipped.",
            fg=self.colors["red"]
        )
        self.transition_id = self.root.after(500, self.show_question)

    def select_option(self, selected):
        """Select one answer card and update its visual state."""
        self.option_var.set(selected)
        self.update_option_styles()
        if self.selection_warning:
            self.result_label.config(
                text=f"Current score: {self.logic.score}",
                fg=self.colors["muted"]
            )
            self.selection_warning = False

    def on_option_enter(self, index):
        """Animate an answer card toward its hover color."""
        self.hovered_option = index
        selected = self.option_var.get() == index
        color = "option_selected_hover" if selected else "option_hover"
        self.animate_option(index, self.colors[color])

    def on_option_leave(self, index):
        """Animate an answer card back to its selected or neutral color."""
        if self.hovered_option == index:
            self.hovered_option = None
        selected = self.option_var.get() == index
        color = "option_selected" if selected else "option"
        self.animate_option(index, self.colors[color])

    def animate_option(self, index, target_color):
        """Transition an option card's background color over a few frames."""
        if index in self.hover_jobs:
            self.root.after_cancel(self.hover_jobs.pop(index))

        button = self.option_buttons[index]
        start_color = button.cget("bg")
        start_rgb = tuple(
            int(start_color[position:position + 2], 16)
            for position in (1, 3, 5)
        )
        target_rgb = tuple(
            int(target_color[position:position + 2], 16)
            for position in (1, 3, 5)
        )
        frame_count = 8
        frame = 0

        def animate_frame():
            nonlocal frame
            frame += 1
            rgb = tuple(
                round(start + (end - start) * frame / frame_count)
                for start, end in zip(start_rgb, target_rgb)
            )
            button.config(bg="#{:02X}{:02X}{:02X}".format(*rgb))
            if frame == frame_count:
                self.hover_jobs.pop(index, None)
            else:
                self.hover_jobs[index] = self.root.after(15, animate_frame)

        self.hover_jobs[index] = self.root.after(15, animate_frame)

    def update_option_styles(self):
        """Highlight the selected option while keeping unselected choices neutral."""
        selected = self.option_var.get()
        for index, button in enumerate(self.option_buttons):
            selected_option = index == selected
            hovered = index == self.hovered_option
            background = (
                "option_selected_hover" if selected_option else "option_hover"
            ) if hovered else (
                "option_selected" if selected_option else "option"
            )
            button.config(
                fg=self.colors["blue"] if index == selected else self.colors["text"],
                highlightbackground=self.colors["blue"] if index == selected else self.colors["border"],
                highlightthickness=2 if index == selected else 1,
            )
            self.animate_option(index, self.colors[background])

    def cancel_timer(self):
        """Cancel the active countdown callback."""
        if self.timer_id is not None:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

    def cancel_timers(self):
        """Cancel countdown and question-transition callbacks."""
        self.cancel_timer()
        if self.transition_id is not None:
            self.root.after_cancel(self.transition_id)
            self.transition_id = None

    def show_result(self):
        """FR4: Save the final score and show the result screen."""
        self.cancel_timers()
        self.timer_label.config(text="")
        total = len(self.logic.questions)
        percentage = (self.logic.score * 100) // total if total else 0
        try:
            saved = self.logic.save_score(percentage)
        except OSError as error:
            messagebox.showerror("Save Error", str(error))
            saved = False
        message = f"Quiz complete!\nScore: {self.logic.score}/{total}"
        message += f"\nPercentage: {percentage}%"
        if saved:
            message += "\nScore saved successfully."
        self.question_label.config(
            text=message, font=("Arial", 19, "bold"), justify="center",
            anchor="center"
        )
        self.info_label.config(text="Result")
        self.progress_fill.place(relx=0, rely=0, relheight=1, relwidth=1)
        self.options_frame.pack_forget()
        self.submit_button.grid_remove()
        self.result_label.config(text="", fg=self.colors["muted"])
        if total and self.logic.score == total:
            self.start_celebration()

    def start_celebration(self):
        """Show a transparent confetti animation across the app window."""
        self.root.update_idletasks()
        transparent_color = "#010203"
        self.celebration_window = tk.Toplevel(self.root)
        self.celebration_window.overrideredirect(True)
        self.celebration_window.transient(self.root)
        self.celebration_window.configure(bg=transparent_color)
        self.celebration_window.wm_attributes(
            "-transparentcolor", transparent_color
        )
        self.celebration_canvas = tk.Canvas(
            self.celebration_window, bg=transparent_color, highlightthickness=0
        )
        self.celebration_canvas.pack(fill="both", expand=True)
        self.position_celebration()
        self.celebration_window.lift(self.root)
        self.celebration_frame = 0
        self.celebration_particles = []
        self.animate_celebration()

    def position_celebration(self):
        """Keep the transparent animation aligned with the app window."""
        if self.celebration_window is None:
            return
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x_position = self.root.winfo_rootx()
        y_position = self.root.winfo_rooty()
        self.celebration_window.geometry(
            f"{width}x{height}+{x_position}+{y_position}"
        )

    def animate_celebration(self):
        """Burst confetti from the stats area across the whole window."""
        canvas = self.celebration_canvas
        if canvas is None:
            return
        canvas.update_idletasks()
        width = max(canvas.winfo_width(), 300)
        height = max(canvas.winfo_height(), 300)
        if not self.celebration_particles:
            colors = [
                self.colors["blue"], self.colors["green"], "#F4B400",
                "#E85D75", "#8B5CF6"
            ]
            center_x = width / 2
            center_y = height * 0.42
            for _ in range(90):
                x = random.uniform(center_x - width * 0.18, center_x + width * 0.18)
                y = random.uniform(center_y - height * 0.06, center_y + height * 0.06)
                size = random.randint(5, 10)
                color = random.choice(colors)
                shape = canvas.create_rectangle(
                    x, y, x + size, y + size * 0.6, fill=color, outline=color
                )
                self.celebration_particles.append(
                    [shape, random.uniform(-12, 12), random.uniform(-12, -3), size]
                )

        for particle in self.celebration_particles:
            shape, speed_x, speed_y, size = particle
            x0, y0, x1, y1 = canvas.coords(shape)
            if y0 > height or x1 < 0 or x0 > width:
                center_x = width / 2
                center_y = height * 0.42
                new_x = random.uniform(
                    center_x - width * 0.18, center_x + width * 0.18
                )
                new_y = random.uniform(
                    center_y - height * 0.06, center_y + height * 0.06
                )
                canvas.coords(shape, new_x, new_y, new_x + size, new_y + size * 0.6)
                particle[1] = random.uniform(-12, 12)
                particle[2] = random.uniform(-12, -3)
            else:
                canvas.move(shape, speed_x, speed_y)
                particle[2] += 0.35

        self.celebration_frame += 1
        if self.celebration_frame >= 70:
            self.finish_celebration()
        else:
            self.celebration_id = self.root.after(35, self.animate_celebration)

    def finish_celebration(self):
        """Remove the transparent confetti overlay."""
        self.celebration_id = None
        self.cancel_celebration()

    def cancel_celebration(self):
        """Stop an active celebration before restarting the quiz."""
        if self.celebration_id is not None:
            self.root.after_cancel(self.celebration_id)
            self.celebration_id = None
        if self.celebration_canvas is not None:
            self.celebration_canvas.destroy()
            self.celebration_canvas = None
        if self.celebration_window is not None:
            self.celebration_window.destroy()
            self.celebration_window = None

    def restart_quiz(self):
        """FR5: Restart with a shuffled question set."""
        self.cancel_timers()
        self.cancel_celebration()
        self.question_label.config(
            font=("Arial", 20, "bold"), justify="left", anchor="w"
        )
        for button in self.option_buttons:
            button.config(state="normal")
        self.start_quiz()


if __name__ == "__main__":
    if sys.platform == "win32":
        ctypes.windll.user32.SetProcessDPIAware()
    window = tk.Tk()
    app = QuizApp(window)
    window.mainloop()
