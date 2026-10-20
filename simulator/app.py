"""Pygame interface; calculation and reporting live in separate modules."""
import pygame

from .config import FIELDS, load_diseases, save_disease
from .engine import Simulation
from .reporting import chart_surface

SIZE = (800, 600)
WHITE, BLACK = (255, 255, 255), (25, 25, 25)
GREEN, RED, PINK = (35, 165, 75), (220, 55, 55), (210, 100, 175)


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
        try:
            chart = chart_surface(history)
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

    def draw_simulation(self, simulation, speed):
        """Draw the current engine state without advancing it."""
        self.screen.fill(WHITE)
        self.text(f"Day: {simulation.day} | Speed: {speed:.1f}x | Dead: {simulation.dead}", 10)
        self.text("Arrows: speed | Space: results | Esc: menu", 50)
        pygame.draw.rect(self.screen, (128, 128, 128), (15, 95, 770, 490), 8)
        colors = {"healthy": GREEN, "sick": RED, "recovered": PINK}
        for person in simulation.people:
            pygame.draw.circle(self.screen, colors[person.state],
                               (round(person.x), round(person.y)), 8)

    def simulation(self, factors):
        simulation = Simulation(factors)
        interval = 2000
        previous = pygame.time.get_ticks()
        while self.running:
            now = pygame.time.get_ticks()
            # Apply the previous speed to the time that has already elapsed.
            simulation.advance(now - previous, 2000 / interval)
            previous = now
            for event in self.events():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
                    if event.key == pygame.K_SPACE and self.running:
                        self.results(simulation.history)
                        return
                    if event.key == pygame.K_RIGHT:
                        interval = max(100, interval - 100)
                    elif event.key == pygame.K_LEFT:
                        interval = min(10000, interval + 100)
            if not self.running:
                return
            if simulation.finished:
                self.results(simulation.history)
                return
            self.draw_simulation(simulation, 2000 / interval)
            self.frame()

    def draw_menu(self, buttons):
        self.screen.fill(WHITE)
        self.text("Disease Propagation", 70, large=True)
        for rect, label, _ in buttons:
            color = (190, 190, 190) if rect.collidepoint(pygame.mouse.get_pos()) else (180, 215, 235)
            pygame.draw.rect(self.screen, color, rect, border_radius=8)
            self.screen.blit(self.heading.render(label, True, BLACK), (rect.x + 65, rect.y + 20))
        self.text("Choose New or Saved. Esc closes the app.", 530)

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
                self.draw_menu(buttons)
                self.frame()
        finally:
            pygame.quit()

