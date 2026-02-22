from argparse import Namespace

import main as main_module


def test_main_entry_calls_wrapper_with_main_and_args(monkeypatch) -> None:
    expected_args = Namespace(year=2025, month="Jan", day=1, command=None)
    calls: dict[str, object] = {}

    def fake_get_args(argv):
        calls["argv"] = argv
        return expected_args

    def fake_wrapper(fn, args):
        calls["fn"] = fn
        calls["args"] = args

    monkeypatch.setattr(main_module, "get_args", fake_get_args)

    rc = main_module.main_entry(["--year", "2025"], wrapper=fake_wrapper)

    assert rc == 0
    assert calls["argv"] == ["--year", "2025"]
    assert calls["fn"] is main_module.main
    assert calls["args"] is expected_args


def test_main_entry_uses_none_argv_when_not_provided(monkeypatch) -> None:
    seen: dict[str, object] = {}

    def fake_get_args(argv):
        seen["argv"] = argv
        return Namespace(year=2025, month="Jan", day=1, command=None)

    def fake_wrapper(fn, args):
        seen["wrapped"] = True

    monkeypatch.setattr(main_module, "get_args", fake_get_args)

    rc = main_module.main_entry(wrapper=fake_wrapper)

    assert rc == 0
    assert seen["argv"] is None
    assert seen["wrapped"] is True
