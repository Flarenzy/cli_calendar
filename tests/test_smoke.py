import importlib


def test_core_modules_importable() -> None:
    # This should not initialize curses UI, only ensure runtime deps resolve.
    importlib.import_module("constants")
    importlib.import_module("ArgParser")
    importlib.import_module("CliCalendar")
