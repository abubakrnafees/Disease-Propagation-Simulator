from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from simulator.config import DiseaseConfig, FIELDS, load_diseases, save_disease, validate_factors

FACTORS = [40, 1, 25, 14, 5, 2, 5]


class ConfigTests(unittest.TestCase):
    def test_valid_round_trip(self):
        self.assertEqual(DiseaseConfig.from_list(FACTORS).to_list(), FACTORS)

    def test_invalid_inputs(self):
        bad = [None, (), [], FACTORS[:-1], FACTORS + [1]]
        for i, (_, low, high) in enumerate(FIELDS):
            for value in [low - 1, high + 1, True, 1.0, '1']:
                factors = FACTORS.copy()
                factors[i] = value
                bad.append(factors)
        for factors in bad:
            self.assertFalse(validate_factors(factors))
            with self.assertRaises(ValueError):
                DiseaseConfig.from_list(factors)

    def test_persistence_and_malformed_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'saved.txt'
            self.assertEqual(load_diseases(path)[0], [])
            path.write_text('Old ' + str(FACTORS), encoding='utf-8')
            save_disease('Scénario', FACTORS, path)
            with path.open('a', encoding='utf-8') as output:
                output.write('\n\nBroken\nShort [1, 2]\nBad [True,1,25,14,5,2,5]\n')
            records, message = load_diseases(path)
            self.assertEqual(records, [('Old', FACTORS), ('Scénario', FACTORS)])
            self.assertIn('3 invalid', message)

    def test_invalid_names_or_settings_not_saved(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'saved.txt'
            for name in ['', ' ', 'a[b', 'x]', 'new\nline', 'x\rreturn']:
                with self.assertRaises(ValueError):
                    save_disease(name, FACTORS, path)
            with self.assertRaises(ValueError):
                save_disease('Name', [1], path)
            self.assertFalse(path.exists())

    def test_empty_unreadable_bad_encoding(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'saved.txt'
            path.write_text('\n\n', encoding='utf-8')
            self.assertEqual(load_diseases(path), ([], ''))
            path.write_bytes(b'\xff\xff')
            self.assertIn('Could not read', load_diseases(path)[1])
            with patch.object(Path, 'read_text', side_effect=PermissionError('Denied')):
                self.assertIn('Could not read', load_diseases(path)[1])

    def test_shipped_saves_compatible(self):
        records, message = load_diseases()
        self.assertGreaterEqual(len(records), 2)
        self.assertEqual(message, '')
        self.assertTrue(all(validate_factors(factors) for _, factors in records))
