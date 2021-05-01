import pytest
from pytemplate.__main__ import cli
from typer.testing import CliRunner


class TestPytemplate:
    @pytest.fixture(autouse=True, scope="class")
    def runner(self):
        return CliRunner()

    def test_pytemplate_returns_zero(self, runner):
        result = runner.invoke(cli)
        assert not result.exception
        assert result.exit_code == 0

    def test_pytemplate_prints_something(self, runner):
        result = runner.invoke(cli)
        assert result.output

    def test_pytemplate_prints_help(self, runner):
        result = runner.invoke(cli, ['--help'])
        assert "Usage" in result.output

    def test_pytemplate_works_with_arg(self, runner):
        result = runner.invoke(cli, ['--x', 2])
        assert not result.exception
        assert result.exit_code == 0
