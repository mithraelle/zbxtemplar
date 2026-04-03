"""Bundled test data locations (golden/reference YAML vs input fixtures)."""
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REFERENCE_DIR = TESTS_DIR / "reference"
FIXTURES_DIR = TESTS_DIR / "fixtures"
STUB_MODULES_DIR = TESTS_DIR / "stub_modules"