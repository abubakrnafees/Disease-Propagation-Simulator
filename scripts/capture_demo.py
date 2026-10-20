"""Capture genuine application surfaces; no fabricated or redrawn interface.

Run python -m scripts.capture_demo --headless for reproducible software rendering.
"""
import argparse
import json
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parent.parent / 'assets')
    args = parser.parse_args()
    if args.headless:
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        os.environ['SDL_AUDIODRIVER'] = 'dummy'
    import pygame
    from PIL import Image
    from simulator.app import App
    from simulator.engine import Simulation

    args.output.mkdir(parents=True, exist_ok=True)
    app = App()
    config = [45, 1, 15, 10, 5, 1, 10]
    sim = Simulation(config, seed=42)
    try:
        buttons = [(pygame.Rect(130, 240, 220, 75), 'New', app.new),
                   (pygame.Rect(450, 240, 220, 75), 'Saved', app.saved)]
        app.draw_menu(buttons)
        pygame.image.save(app.screen, args.output / 'menu.png')
        frames = []
        for index in range(80):
            app.draw_simulation(sim, 4.0)
            raw = pygame.image.tobytes(app.screen, 'RGB')
            image = Image.frombytes('RGB', app.screen.get_size(), raw)
            frames.append(image.resize((600, 450), Image.Resampling.LANCZOS))
            if index == 40:
                pygame.image.save(app.screen, args.output / 'simulation.png')
            for _ in range(24):
                sim.update()
        frames[0].save(args.output / 'propagation.gif', save_all=True,
                       append_images=frames[1:], duration=100, loop=0, optimize=True)
        while sim.day < 45:
            sim.update()
        # Call the real results view and capture its first frame before returning.
        def capture_results_frame():
            pygame.image.save(app.screen, args.output / 'results.png')
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        app.frame = capture_results_frame
        app.results(sim.history)
        metadata = {'seed': 42, 'config': config, 'frames': 80, 'steps_per_frame': 24,
                    'gif_duration_ms': 100, 'gif_display_speed': 4.0, 'chart_day': sim.day,
                    'final_counts': sim.counts(), 'headless': args.headless,
                    'description': 'Actual App drawing methods captured from Pygame surfaces.'}
        (args.output / 'capture.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
        print(f'Captured menu, simulation, results, and GIF in {args.output}')
    finally:
        pygame.quit()


if __name__ == '__main__':
    main()
