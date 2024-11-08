import requests
import time
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import print as rprint
from difflib import SequenceMatcher

class JeopardyGame:
    def __init__(self):
        self.console = Console()
        self.categories = ["Science", "History", "Geography", "Arts", "Sports"]
        self.points = [100, 200, 300, 400, 500]
        self.board = {}
        self.score = 0

    def generate_question(self, category, points):
        """Generate a question and answer using Ollama"""
        prompt = f"""Generate a {category} trivia question worth {points} points.
        Respond with only the question on one line, followed by the answer on the next line.
        Make it challenging but fair for the points value."""

        try:
            response = requests.post('http://localhost:11434/api/generate',
                                  json={
                                      "model": "mistral",
                                      "prompt": prompt,
                                      "stream": False
                                  })
            response.raise_for_status()
            result = response.json()

            # Split response into question and answer
            lines = result['response'].strip().split('\n')
            if len(lines) >= 2:
                question = lines[0].strip()
                answer = lines[1].strip()
                # Remove common prefixes if they exist
                answer = answer.lower().replace('answer:', '').replace('a:', '').strip()
                return {
                    "question": question,
                    "answer": answer
                }
            else:
                # Fallback question if parsing fails
                return {
                    "question": f"This {category} question is worth ${points}",
                    "answer": "backup"
                }

        except Exception as e:
            self.console.print(f"[red]Error generating question: {str(e)}[/red]")
            # Provide a backup question
            return {
                "question": f"This {category} question is worth ${points}",
                "answer": "backup"
            }

    def check_answer(self, player_answer: str, correct_answer: str) -> bool:
            """
            Check if the player's answer matches the correct answer using a more robust matching strategy.

            Args:
                player_answer (str): The player's answer
                correct_answer (str): The correct answer

            Returns:
                bool: True if the answer is correct, False otherwise
            """
            player_answer = player_answer.lower().strip()
            correct_answer = correct_answer.lower().strip()

            # Direct match
            if player_answer == correct_answer:
                return True

            # Calculate similarity ratio
            similarity = SequenceMatcher(None, player_answer, correct_answer).ratio()
            if similarity > 0.8:  # 80% similarity threshold
                return True

            # Handle cases where one answer is a more specific version of the other
            player_words = set(player_answer.split())
            correct_words = set(correct_answer.split())

            # Check if all important words from the correct answer are in the player's answer
            important_words = {word for word in correct_words
                             if len(word) > 3}  # Skip small words like "the", "a", etc.
            if important_words and important_words.issubset(player_words):
                return True

            return False

    def initialize_board(self):
        """Initialize the game board with questions and answers"""
        self.board = {}
        for category in self.categories:
            self.console.print(f"Generating questions for {category}...")
            self.board[category] = {}
            for points in self.points:
                qa_pair = self.generate_question(category, points)
                self.board[category][points] = {
                    "question": qa_pair["question"],
                    "answer": qa_pair["answer"],
                    "answered": False
                }
                # Small delay to prevent overwhelming the API
                time.sleep(0.5)

    def display_board(self):
        """Display the game board using Rich"""
        table = Table(title="Jeopardy Board")

        # Add categories as columns
        for category in self.categories:
            table.add_column(category, justify="center")

        # Add rows for each point value
        for points in self.points:
            row = []
            for category in self.categories:
                if self.board[category][points]["answered"]:
                    row.append("[dim]----[/dim]")
                else:
                    row.append(f"${points}")
            table.add_row(*row)

        self.console.clear()
        self.console.print(table)
        self.console.print(f"\nCurrent Score: ${self.score}")

    def play_turn(self):
            """Handle a single turn"""
            # Add exit option
            if not Confirm.ask("\nDo you want to continue playing?", default=True):
                return False

            # Get category selection
            category = Prompt.ask("Choose a category", choices=self.categories)

            # Get points selection
            available_points = [str(p) for p, q in self.board[category].items()
                              if not q["answered"]]
            if not available_points:
                rprint("[red]No more questions in this category![/red]")
                return True

            points = int(Prompt.ask("Choose points", choices=available_points))

            # Display question
            question = self.board[category][points]["question"]
            correct_answer = self.board[category][points]["answer"].lower()

            self.console.print(f"\n[blue]Question ({category} for ${points}):[/blue]")
            self.console.print(question)

            # Get answer
            player_answer = Prompt.ask("\nYour answer").lower()

            # Check answer using the new method
            if self.check_answer(player_answer, correct_answer):
                self.score += points
                rprint("[green]Correct![/green]")
            else:
                self.score -= points
                rprint(f"[red]Sorry, the correct answer was: {correct_answer}[/red]")
                time.sleep(2)

            self.board[category][points]["answered"] = True
            time.sleep(2)
            return True

    def play_game(self):
        """Main game loop"""
        self.console.clear()
        rprint("[yellow]Welcome to Terminal Jeopardy![/yellow]")
        rprint("Initializing game board with Ollama...")
        self.initialize_board()

        while True:
            self.display_board()

            # Check if all questions are answered
            all_answered = all(
                question["answered"]
                for category in self.board.values()
                for question in category.values()
            )

            if all_answered:
                break

            if not self.play_turn():
                rprint("\n[yellow]Thanks for playing![/yellow]")
                break

        self.console.print(f"\nGame Over! Final Score: ${self.score}")

if __name__ == "__main__":
    game = JeopardyGame()
    game.play_game()
