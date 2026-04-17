from unittest.mock import MagicMock

from zbxtemplar.executor.operations.ImportOperation import ImportOperation


def test_reads_file_and_imports(tmp_path):
    test_str = "zabbix_export:\n  version: '7.4'\n"
    yaml_file = tmp_path / "templates.yml"
    yaml_file.write_text(test_str)

    api = MagicMock()
    op = ImportOperation([str(yaml_file)], api)
    op.execute()
    api.configuration.import_.assert_called_once()
    call_kwargs = api.configuration.import_.call_args[1]
    assert call_kwargs["source"] == test_str
    assert call_kwargs["format"] == "yaml"
    assert call_kwargs["rules"]["templates"]["createMissing"] is True


def test_list_of_files(tmp_path):
    file1 = tmp_path / "templates.yml"
    file1.write_text("zabbix_export:\n  version: '7.4'\n")
    file2 = tmp_path / "hosts.yml"
    file2.write_text("zabbix_export:\n  version: '7.4'\n")

    api = MagicMock()
    op = ImportOperation([str(file1), str(file2)], api)
    op.execute()
    assert api.configuration.import_.call_count == 2
