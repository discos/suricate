import pytest
from mock import patch, mock_open

user_config = """
HTTP:
  baseurl: pippo
  port: 7000
"""


def test_configuration_file_exists():
    """In case the user created a configuration file with custom
    parameters, the default values have to be overwritten."""
    from suricate.configuration import config
    default_baseurl = config['HTTP']['baseurl']
    default_port = config['HTTP']['port']
    from suricate import configuration
    try:
        with patch(
                "suricate.configuration.open",
                mock_open(read_data=user_config)) as f:

            reload(configuration)
            config = configuration.config
            assert config['HTTP']['baseurl'] != default_baseurl
            assert config['HTTP']['baseurl'] == 'pippo'
            assert config['HTTP']['port'] != default_port
            assert config['HTTP']['port'] == 7000
            f.assert_called_with(configuration.config_file)
    finally:
        reload(configuration)


def test_wrong_configuration_file():
    """In case the user created a configuration file with custom
    parameters, the default values have to be overwritten."""
    from suricate.configuration import config
    default_baseurl = config['HTTP']['baseurl']
    default_port = config['HTTP']['port']
    from suricate import configuration
    try:
        with patch(
                "suricate.configuration.open",
                mock_open(read_data='')) as f:

            reload(configuration)
            config = configuration.config
            assert config['HTTP']['baseurl'] == default_baseurl
            assert config['HTTP']['port'] == default_port
            f.assert_called_with(configuration.config_file)
    finally:
        reload(configuration)


if __name__ == '__main__':
    pytest.main()
