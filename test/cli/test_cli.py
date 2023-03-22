from firecli.version import __version__
from firecli.cli import main


def test_help_page(cli_runner):
    result = cli_runner.invoke(main, ['--help'], catch_exceptions=False, prog_name='firecli')

    assert result.exit_code == 0


def test_help_page_without_args(cli_runner):
    result = cli_runner.invoke(main, [], catch_exceptions=False, prog_name='firecli')

    assert result.exit_code == 0


def test_show_version(cli_runner):
    result = cli_runner.invoke(main, ['--version'], catch_exceptions=False, prog_name='firecli')

    assert result.exit_code == 0
    assert __version__ in result.output
