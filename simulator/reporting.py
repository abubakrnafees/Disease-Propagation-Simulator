"""Render statistics with Agg; never create a Tkinter window."""


def chart_surface(history):
    import pygame
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
    return pygame.image.frombuffer(
        bytes(canvas.buffer_rgba()), canvas.get_width_height(), "RGBA").copy()
