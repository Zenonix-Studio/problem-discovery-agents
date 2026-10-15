import pytest

from problem_discovery_agents import run


def test_cli_rejects_non_pilot_category() -> None:
    with pytest.raises(SystemExit) as result:
        run.main(["--category", "Other"])
    assert result.value.code == 2


def test_cli_reports_safe_setup_error(monkeypatch, capsys) -> None:
    monkeypatch.setattr(run, "load_settings", lambda: object())
    monkeypatch.setattr(run, "build_services", lambda settings, client: (_ for _ in ()).throw(RuntimeError("sentinel-secret-value")))
    assert run.main(["--category", "Developer Tools & Productivity"]) == 2
    output = capsys.readouterr().out
    assert "Run setup failed: RuntimeError: operation failed" in output
    assert "sentinel-secret-value" not in output
