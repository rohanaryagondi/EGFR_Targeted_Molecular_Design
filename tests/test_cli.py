"""Test CLI entrypoint."""

from typer.testing import CliRunner

from statebind.cli import app

runner = CliRunner()


def test_cli_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_cli_info():
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0
    assert "StateBind" in result.output
    assert "context" in result.output


def test_cli_run_placeholder():
    result = runner.invoke(app, ["run", "--module", "context", "--config", "configs/context.yaml"])
    assert result.exit_code == 1
    assert "placeholder" in result.output.lower() or "not yet implemented" in result.output.lower()
