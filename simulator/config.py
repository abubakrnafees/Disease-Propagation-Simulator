"""Validated configuration and backward-compatible saved disease records."""
import ast
from dataclasses import dataclass, fields
from pathlib import Path

SAVE_FILE = Path(__file__).resolve().parent.parent / "saved.txt"
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


@dataclass(frozen=True)
class DiseaseConfig:
    contagiousness: int
    population_size: int
    distancing: int
    recovery_days: int
    mortality: int
    recovered_immunity: int
    initial_infected: int

    def __post_init__(self):
        if not validate_factors(self.to_list()):
            raise ValueError("Disease settings must match the documented integer ranges.")

    def to_list(self):
        return [getattr(self, field.name) for field in fields(self)]

    @classmethod
    def from_list(cls, values):
        if not validate_factors(values):
            raise ValueError("Expected seven valid integer settings.")
        return cls(*values)

