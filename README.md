# Disease Propagation Simulator

Install Python and open this folder in VS Code. In Terminal > New Terminal:

```powershell
py -m pip install -r requirements.txt
py main.py
```

Use `python` instead of `py` if that is how Python is installed on your computer.

- New: enter settings in the application window; Enter confirms each answer.
- Saved: Left/Right cycles through diseases, Enter starts the selected one.
- Simulation: Left/Right slows down or speeds up movement, contacts, and days together (1x = two seconds per day). Space shows results inside the app and ends the run. Enter, Space, or Esc returns from results.
- Esc returns to the main menu; Esc at the main menu exits.

Saved diseases are stored beside main.py. Existing saved diseases remain compatible. Blank lines are ignored and invalid entries are reported. Recovery time accepts 1–365 days. Simulations last up to 365 days. Results include day zero, daily population counts, and deaths.

This is an educational model, not a validated epidemiological prediction tool.
