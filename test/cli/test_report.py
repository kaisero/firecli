from firecli.cli import main


def test_report_accessrules_without_comments_help_page(cli_runner):
    result = cli_runner.invoke(
        main, ['report', 'accessrules-without-comments', '--help'], catch_exceptions=False, prog_name='firecli'
    )

    assert result.exit_code == 0


def test_report_accessrules_without_ticket_id_help_page(cli_runner):
    result = cli_runner.invoke(
        main, ['report', 'accessrules-without-ticket-id', '--help'], catch_exceptions=False, prog_name='firecli'
    )

    assert result.exit_code == 0


def test_report_no_of_accessrules_help_page(cli_runner):
    result = cli_runner.invoke(
        main, ['report', 'no-of-accessrules', '--help'], catch_exceptions=False, prog_name='firecli'
    )

    assert result.exit_code == 0


def test_report_noncompliant_accessrules_help_page(cli_runner):
    result = cli_runner.invoke(
        main, ['report', 'noncompliant-accessrules', '--help'], catch_exceptions=False, prog_name='firecli'
    )

    assert result.exit_code == 0


def test_report_noncompliant_network_segments_help_page(cli_runner):
    result = cli_runner.invoke(
        main, ['report', 'noncompliant-network-segments', '--help'], catch_exceptions=False, prog_name='firecli'
    )

    assert result.exit_code == 0
