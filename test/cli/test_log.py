from firecli.cli import main


def test_log_show_help_page(cli_runner):
    result = cli_runner.invoke(main, ['log', 'show', '--help'], catch_exceptions=False, prog_name='firecli')

    assert result.exit_code == 0


def test_log_tail_help_page(cli_runner):
    result = cli_runner.invoke(main, ['log', 'show', '--help'], catch_exceptions=False, prog_name='firecli')

    assert result.exit_code == 0
