from yaml import safe_load

import firecli.api.cfg as cfg

from firecli import PROJECT_DIR


def test_host_override_import_schema_validation_with_valid_configuration():
    with open(f'{PROJECT_DIR}/etc/overrides.yml') as f:
        config = safe_load(f)
    cfg.validate(config, 'object.host.override.import.src')


def test_host_override_import_schema_validation_with_empty_configuration():
    pass


def test_host_override_import_schema_validation_with_empty_objects():
    pass


def test_host_override_import_schema_validation_with_missing_required_fields():
    pass


def test_host_override_import_schema_validation_with_invalid_required_items_count():
    pass


def test_host_override_import_schema_validation_with_invalid_regex():
    pass
