"""Disease Propagation Simulator. Run with: python main.py."""
import ast
import math
from pathlib import Path
import random

import pygame

SAVE_FILE = Path(__file__).resolve().with_name("saved.txt")
SIZE = (800, 600)
WHITE, BLACK = (255, 255, 255), (25, 25, 25)
GREEN, RED, PINK = (35, 165, 75), (220, 55, 55), (210, 100, 175)
FIELDS = [
    ("Contagiousness (%)", 0, 100),
    ("Population size (1 = largest, 3 = smallest)", 1, 3),
    ("Social distancing (%)", 0, 100),
    ("Days to recover", 1, 365),
    ("Mortality (%)", 0, 100),
    ("Recovered immunity (1 = yes, 2 = no)", 1, 2),
    ("Initially infected (%)", 0, 100),
]


def validate_factors(values):
    return (isinstance(values, list) and len(values) == len(FIELDS)
            and all(type(value) is int and low <= value <= high
                    for value, (_, low, high) in zip(values, FIELDS)))


def load_diseases(path=SAVE_FILE):
    diseases, skipped = [], 0
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except FileNotFoundError:
        return [], "No saved diseases yet."
    except (OSError, UnicodeError) as error:
        return [], f"Could not read saved diseases: {error}"
    for line in lines:
        if not line.strip():
            continue
        try:
            name, separator, data = line.partition("[")
            factors = ast.literal_eval(separator + data)
            if not name.strip() or not validate_factors(factors):
                raise ValueError("Invalid disease")
            diseases.append((name.strip(), factors))
        except (ValueError, SyntaxError, TypeError, RecursionError):
            skipped += 1
    message = f"Skipped {skipped} invalid saved entry(s)." if skipped else ""
    return diseases, message


def save_disease(name, factors, path=SAVE_FILE):
    if not name.strip() or any(char in name for char in "[]\r\n"):
        raise ValueError("Use a name without brackets or line breaks.")
    if not validate_factors(factors):
        raise ValueError("Invalid disease settings.")
    # Ensure an existing file without a final newline still accepts a new entry.
    prefix = ""
    if path.exists() and path.stat().st_size:
        with path.open("rb") as existing:
            existing.seek(-1, 2)
            if existing.read(1) != b"\n":
                prefix = "\n"
    with path.open("a", encoding="utf-8") as output:
        output.write(f"{prefix}{name.strip()} {factors}\n")


class Person:
    def __init__(self, center, factors):
        self.x, self.y = center
        angle = random.uniform(0, math.tau)
        self.dx, self.dy = math.cos(angle), math.sin(angle)
        self.stationary = random.randrange(100) < factors[2]
        self.state = "sick" if random.randrange(100) < factors[6] else "healthy"
        self.start_day = 0

    def move(self):
        if self.stationary:
            return
        self.x += self.dx
        self.y += self.dy
        if self.x < 24 or self.x > 776:
            self.x = min(776, max(24, self.x))
            self.dx *= -1
        if self.y < 104 or self.y > 576:
            self.y = min(576, max(104, self.y))
            self.dy *= -1


def resolve_contact(first, second):
    dx, dy = second.x - first.x, second.y - first.y
    separation = math.hypot(dx, dy)
    if separation > 16:
        return False
    nx, ny = (dx / separation, dy / separation) if separation else (1, 0)
    overlap = 16 - separation + 0.01
    moving = int(not first.stationary) + int(not second.stationary)
    if moving:
        if not first.stationary:
            first.x -= nx * overlap / moving
            first.y -= ny * overlap / moving
            if first.dx * nx + first.dy * ny > 0:
                first.dx *= -1
                first.dy *= -1
        if not second.stationary:
            second.x += nx * overlap / moving
            second.y += ny * overlap / moving
            if second.dx * nx + second.dy * ny < 0:
                second.dx *= -1
                second.dy *= -1
    for person in (first, second):
        person.x = min(776, max(24, person.x))
        person.y = min(576, max(104, person.y))
    return True


class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(SIZE)
        pygame.display.set_caption("Disease Propagation")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 28)
        self.heading = pygame.font.Font(None, 40)
        self.running = True

    def events(self):
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
        return events

    def text(self, text, y, color=BLACK, large=False):
        font = self.heading if large else self.font
        # Wrap text to keep prompts and error messages within the window.
        line = ""
        for word in str(text).split():
            candidate = f"{line} {word}".strip()
            if font.size(candidate)[0] > 750 and line:
                self.screen.blit(font.render(line, True, color), (25, y))
                y += 30
                line = word
            else:
                line = candidate
        self.screen.blit(font.render(line, True, color), (25, y))

    def frame(self):
        pygame.display.flip()
        self.clock.tick(60)

    def ask(self, title, low=None, high=None):
        value, error = "", ""
        while self.running:
            for event in self.events():
                if event.type != pygame.KEYDOWN:
                    continue
                if event.key == pygame.K_ESCAPE:
                    return None
                if event.key == pygame.K_BACKSPACE:
                    value = value[:-1]
                elif event.key == pygame.K_RETURN:
                    if low is None:
                        if value.strip() and not any(c in value for c in "[]"):
                            return value.strip()
                        error = "Enter a name without brackets."
                    else:
                        try:
                            number = int(value)
                            if low <= number <= high:
                                return number
                        except ValueError:
                            pass
                        error = f"Enter a whole number from {low} to {high}."
                elif event.unicode.isprintable() and len(value) < 60:
                    value += event.unicode
            self.screen.fill(WHITE)
            self.text(title, 60, large=True)
            self.text(value + "|", 230)
            self.text(error, 320, RED)
            self.text("Enter to continue. Esc to return to the menu.", 530)
            self.frame()
        return None

    def new(self):
        factors = []
        for title, low, high in FIELDS:
            value = self.ask(title, low, high)
            if value is None:
                return
            factors.append(value)
        save = self.ask("Save this disease? (1 = yes, 2 = no)", 1, 2)
        if save is None:
            return
        if save == 1:
            name = self.ask("Disease name")
            if name is None:
                return
            try:
                save_disease(name, factors)
            except (OSError, ValueError) as error:
                self.notice(f"Could not save: {error}")
        if self.running:
            self.simulation(factors)

    def notice(self, message):
        while self.running:
            events = self.events()
            if any(e.type == pygame.KEYDOWN for e in events):
                return
            self.screen.fill(WHITE)
            self.text(message, 120)
            self.text("Press any key to continue.", 530)
            self.frame()

    def saved(self):
        diseases, message = load_diseases()
        index = 0
        while self.running:
            for event in self.events():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
                    if diseases:
                        if event.key == pygame.K_RIGHT:
                            index = (index + 1) % len(diseases)
                        elif event.key == pygame.K_LEFT:
                            index = (index - 1) % len(diseases)
                        elif event.key == pygame.K_RETURN:
                            self.simulation(diseases[index][1])
            self.screen.fill(WHITE)
            if diseases:
                name, factors = diseases[index]
                self.text(f"Saved {index + 1}/{len(diseases)}: {name}", 20, large=True)
                for row, ((label, _, _), value) in enumerate(zip(FIELDS, factors)):
                    self.text(f"{label}: {value}", 115 + row * 42)
            else:
                self.text("No valid saved diseases. Create one from New.", 100)
            self.text(message, 440, RED)
            self.text("Left / Right: choose | Enter: run | Esc: menu", 545)
            self.frame()

    def results(self, history):
        # Render directly into Pygame; no Tkinter or second window is required.
        try:
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_agg import FigureCanvasAgg

            figure = Figure(figsize=(8, 5.2), dpi=100)
            canvas = FigureCanvasAgg(figure)
            axes = figure.subplots()
            days = list(range(len(history)))
            for index, (label, color) in enumerate(zip(
                    ("Healthy", "Sick", "Recovered", "Dead"),
                    ("green", "red", "magenta", "gray"))):
                axes.plot(days, [row[index] for row in history], label=label,
                          color=color, marker="o" if len(history) == 1 else None)
            axes.set(xlabel="Day", ylabel="People", title="Disease Stats")
            axes.set_ylim(bottom=0)
            axes.legend()
            figure.tight_layout()
            canvas.draw()
            chart = pygame.image.frombuffer(
                bytes(canvas.buffer_rgba()), canvas.get_width_height(), "RGBA").copy()
        except (ImportError, RuntimeError) as error:
            self.notice(f"Could not display the chart: {error}")
            return

        while self.running:
            for event in self.events():
                if event.type == pygame.KEYDOWN and event.key in (
                        pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                    return
            if not self.running:
                return
            self.screen.fill(WHITE)
            self.screen.blit(chart, (0, 0))
            self.text("Enter / Space / Esc: return", 550)
            self.frame()

    def simulation(self, factors):
        people = [Person((x, y), factors)
                  for x in range(50, 760, factors[1] * 75)
                  for y in range(125, 560, 50)]
        day, dead = 0, 0
        interval = 2000
        elapsed = 0.0
        step_ms = 1000 / 60
        steps = 0
        history = []

        def record():
            history.append(tuple(sum(p.state == state for p in people)
                                 for state in ("healthy", "sick", "recovered")) + (dead,))

        record()
        previous = pygame.time.get_ticks()
        while self.running:
            now = pygame.time.get_ticks()
            # Scale one shared simulation clock, independent of drawing speed.
            elapsed += (now - previous) * (2000 / interval)
            previous = now
            for event in self.events():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
                    if event.key == pygame.K_SPACE:
                        self.results(history)
                        return
                    if event.key == pygame.K_RIGHT:
                        interval = max(100, interval - 100)
                    elif event.key == pygame.K_LEFT:
                        interval = min(10000, interval + 100)
            if not self.running:
                return
            while elapsed + 1e-9 >= step_ms:
                elapsed = max(0.0, elapsed - step_ms)
                for person in people:
                    person.move()
                # Each pair is considered once; use identities instead of coordinates.
                contacts = []
                states = {person: person.state for person in people}
                for index, first in enumerate(people):
                    for second in people[index + 1:]:
                        if resolve_contact(first, second):
                            contacts.append((first, second))
                for first, second in contacts:
                    for target, source in ((first, second), (second, first)):
                        if (states[target] == "healthy" and states[source] == "sick"
                                and target.state == "healthy" and random.randrange(100) < factors[0]):
                            target.state, target.start_day = "sick", day
                steps += 1
                if steps % 120 == 0:
                    day += 1
                    survivors = []
                    for person in people:
                        if person.state == "sick" and day - person.start_day >= factors[3]:
                            if random.randrange(100) < factors[4]:
                                dead += 1
                                continue
                            person.state = "recovered" if factors[5] == 1 else "healthy"
                        survivors.append(person)
                    people = survivors
                    record()
                    if day >= 365:
                        self.results(history)
                        return
            self.screen.fill(WHITE)
            self.text(f"Day: {day} | Speed: {2000 / interval:.1f}x | Dead: {dead}", 10)
            self.text("Arrows: speed | Space: results | Esc: menu", 50)
            pygame.draw.rect(self.screen, (128, 128, 128), (15, 95, 770, 490), 8)
            colors = {"healthy": GREEN, "sick": RED, "recovered": PINK}
            for person in people:
                pygame.draw.circle(self.screen, colors[person.state], (round(person.x), round(person.y)), 8)
            self.frame()

    def run(self):
        try:
            while self.running:
                buttons = [(pygame.Rect(130, 240, 220, 75), "New", self.new),
                           (pygame.Rect(450, 240, 220, 75), "Saved", self.saved)]
                for event in self.events():
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        for rect, _, action in buttons:
                            if rect.collidepoint(event.pos):
                                action()
                                break
                if not self.running:
                    break
                self.screen.fill(WHITE)
                self.text("Disease Propagation", 70, large=True)
                for rect, label, _ in buttons:
                    color = (190, 190, 190) if rect.collidepoint(pygame.mouse.get_pos()) else (180, 215, 235)
                    pygame.draw.rect(self.screen, color, rect, border_radius=8)
                    self.screen.blit(self.heading.render(label, True, BLACK), (rect.x + 65, rect.y + 20))
                self.text("Choose New or Saved. Esc closes the app.", 530)
                self.frame()
        finally:
            pygame.quit()


if __name__ == "__main__":
    App().run()
