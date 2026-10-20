"""Headless integration tests using the application's real drawing/event code."""
import builtins
import importlib.util
import os
from pathlib import Path
import random
import sys
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame

from simulator.app import App
from simulator.engine import Simulation
from simulator.reporting import chart_surface

FACTORS = [40, 1, 25, 14, 5, 2, 5]
ROOT = Path(__file__).resolve().parent.parent


def key(code, text=''):
    return pygame.event.Event(pygame.KEYDOWN, key=code, unicode=text)


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.app = App()
        self.app.frame = lambda: None

    def tearDown(self):
        pygame.quit()

    def test_results_render_without_tkinter_and_return(self):
        original = builtins.__import__
        def no_tk(name, *args, **kwargs):
            if name == 'tkinter' or name.startswith('tkinter.'):
                raise AssertionError('Results must not depend on Tkinter')
            return original(name, *args, **kwargs)
        with patch('builtins.__import__', side_effect=no_tk):
            for days, exit_key in [(1, pygame.K_RETURN), (8, pygame.K_SPACE), (366, pygame.K_ESCAPE)]:
                with self.subTest(days=days):
                    history = [(20, 5, 3, 2)] * days
                    self.assertEqual(chart_surface(history).get_size(), (800, 520))
                    self.app.events = unittest.mock.Mock(side_effect=[[], [key(exit_key)]])
                    self.app.results(history)
                    self.assertTrue(self.app.running)

    def test_input_retry_and_escape(self):
        self.app.events = unittest.mock.Mock(side_effect=[
            [key(pygame.K_a, 'a'), key(pygame.K_RETURN)],
            [key(pygame.K_BACKSPACE), key(pygame.K_5, '5'), key(pygame.K_RETURN)]])
        self.assertEqual(self.app.ask('Percentage', 0, 100), 5)
        self.app.events = lambda: [key(pygame.K_ESCAPE)]
        self.assertIsNone(self.app.ask('Percentage', 0, 100))

    def test_new_collects_settings_and_launches(self):
        with patch.object(self.app, 'ask', side_effect=FACTORS + [2]), \
                patch.object(self.app, 'simulation') as run:
            self.app.new()
            run.assert_called_once_with(FACTORS)

    def test_new_save_and_failure_notice(self):
        with patch.object(self.app, 'ask', side_effect=FACTORS + [1, 'Name']), \
                patch('simulator.app.save_disease', side_effect=OSError('Denied')), \
                patch.object(self.app, 'notice') as notice, \
                patch.object(self.app, 'simulation') as run:
            self.app.new()
            notice.assert_called_once()
            run.assert_called_once_with(FACTORS)

    def test_saved_wraps_right_and_left(self):
        other = [20, 3, 0, 3, 0, 1, 10]
        for arrow, expected in [(pygame.K_RIGHT, FACTORS), (pygame.K_LEFT, other)]:
            # Four rights wrap twice; one left wraps to the last record.
            arrows = [key(arrow)] * (4 if arrow == pygame.K_RIGHT else 1)
            self.app.events = unittest.mock.Mock(side_effect=[arrows + [key(pygame.K_RETURN)],
                                                              [key(pygame.K_ESCAPE)]])
            with patch('simulator.app.load_diseases', return_value=([('A', FACTORS), ('B', other)], '')), \
                    patch.object(self.app, 'simulation') as run:
                self.app.saved()
                run.assert_called_once_with(expected)

    def test_saved_empty_is_safe(self):
        self.app.events = unittest.mock.Mock(side_effect=[
            [key(pygame.K_LEFT), key(pygame.K_RIGHT), key(pygame.K_RETURN)], [key(pygame.K_ESCAPE)]])
        with patch('simulator.app.load_diseases', return_value=([], 'No saved diseases yet.')):
            self.app.saved()

    def test_simulation_speed_controls_and_results(self):
        self.app.events = unittest.mock.Mock(side_effect=[
            [key(pygame.K_RIGHT)], [key(pygame.K_LEFT)], [key(pygame.K_SPACE)]])
        with patch('simulator.app.pygame.time.get_ticks', side_effect=[0, 20, 40, 60]), \
                patch.object(self.app, 'results') as results:
            self.app.simulation(FACTORS)
            results.assert_called_once()

    def test_close_each_screen(self):
        for screen in ('saved', 'ask', 'simulation', 'results', 'notice', 'run'):
            self.app.running = True
            pygame.event.clear()
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            self.app.events = App.events.__get__(self.app, App)
            with self.subTest(screen=screen):
                if screen == 'saved':
                    self.app.saved()
                elif screen == 'ask':
                    self.app.ask('Input', 0, 100)
                elif screen == 'simulation':
                    self.app.simulation(FACTORS)
                elif screen == 'results':
                    self.app.results([(20, 5, 3, 2)])
                elif screen == 'notice':
                    self.app.notice('Message')
                else:
                    self.app.run()
                self.assertFalse(self.app.running)

    def test_pre_refactor_behavior_preserved(self):
        """Run the frozen app under controlled time; compare exact engine state."""
        namespace = {'__name__': 'baseline', '__file__': str(ROOT / 'main.py')}
        source = (ROOT / 'docs/baselines/pre_refactor_main.py.txt').read_text(encoding='utf-8-sig')
        exec(compile(source, 'pre_refactor_main.py.txt', 'exec'), namespace)
        for seed in (2, 42):
            baseline = namespace['App']()
            clock = [0]
            baseline.events = lambda: [key(pygame.K_SPACE)] if clock[0] > 4000 else []
            baseline.frame = lambda: clock.__setitem__(0, clock[0] + 20)
            baseline.results = lambda history: None
            captured = {}
            def trace(frame, event, arg):
                if event == 'return' and frame.f_code is namespace['App'].simulation.__code__:
                    captured.update(frame.f_locals)
            saved_random = random.getstate()
            try:
                random.seed(seed)
                with patch('pygame.time.get_ticks', side_effect=lambda: clock[0]):
                    sys.setprofile(trace)
                    try:
                        baseline.simulation(FACTORS)
                    finally:
                        sys.setprofile(None)
                old_rng = random.getstate()
            finally:
                random.setstate(saved_random)
            sim = Simulation(FACTORS, seed=seed)
            sim.advance(4000)
            self.assertEqual(sim.history, captured['history'])
            self.assertEqual(sim.rng.getstate(), old_rng)
            position = lambda people: [(p.x, p.y, p.dx, p.dy, p.state, p.start_day) for p in people]
            self.assertEqual(position(sim.people), position(captured['people']))
