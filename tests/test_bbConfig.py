# File: test_BBConfig.py

import pytest
from unittest.mock import mock_open, patch
from brainboost_configuration_package.BBConfig import BBConfig

@pytest.fixture(autouse=True)
def reset_BBConfig():
    """
    Fixture to reset BBConfig's internal state before each test.
    """
    BBConfig._conf = {}
    BBConfig._resolved_conf = {}
    BBConfig._overrides = {}
    BBConfig._config_file = '/brainboost/global.config'
    yield
    # Cleanup after test if necessary
    BBConfig._conf = {}
    BBConfig._resolved_conf = {}
    BBConfig._overrides = {}
    BBConfig._config_file = '/brainboost/global.config'

def test_configure_with_custom_file():
    """
    Test the configure method with a custom configuration file.
    """
    custom_config_content = """
    # Custom configuration for WorkTwins
    mode = sandbox
    userdata_path = com_worktwins_userdata
    filter_sensitive_data = True
    ocr_to_use = easyocr
    work_foot_print_megabytes = 4096
    snapshots_database_path = {$userdata_path}/snapshots.db
    write_screenshots_to_files = False
    snapshots_database_enabled = True
    monitor_user_input = True

    # Log configuration
    log_path = {$userdata_path}/com_worktwins_logs
    log_path_ocr = {$userdata_path}/com_worktwins_ocr
    log_path_images = {$userdata_path}/com_worktwins_images
    log_base_url_1_5 = http://100.96.1.34:8080/log
    log_debug_mode = True
    log_telegram_service_url = http://0.0.0.0:8080/send_telegram_notification
    log_enable_storage = True
    log_terminal_output = True
    log_delimiter = |
    log_sqlite3_storage_enabled = False
    log_sqlite3_storage_path =  {$userdata_path}/logs.db
    log_page_size = 100
    log_header = timestampt,type,process_name,source_code_line,message,exec_time
    log_memsize_limit = 52428800

    # paths
    resource_path = /com_worktwins_resources

    github_user_path = {$userdata_path}/com_worktwins_data_github
    gitlab_user_path = {$userdata_path}/com_worktwins_data_gitlab
    tmp_snapshots_user_path = {$userdata_path}/com_worktwins_temp_snapshots
    reports_user_path = {$userdata_path}/com_worktwins_data_reports
    """
    
    # Mock the open function to read the custom configuration
    with patch('builtins.open', mock_open(read_data=custom_config_content)) as mocked_file:
        custom_config_path = 'path/to/worktwins.conf'
        # Also mock os.path.isfile to return True for the custom_config_path
        with patch('os.path.isfile', return_value=True):
            BBConfig.configure(custom_config_path)
            # Ensure the file was opened correctly
            mocked_file.assert_called_once_with(custom_config_path)
    
    # Verify that the custom configuration was loaded
    assert BBConfig.get('mode') == 'sandbox'
    assert BBConfig.get('userdata_path') == 'com_worktwins_userdata'
    assert BBConfig.get('filter_sensitive_data') is True
    assert BBConfig.get('ocr_to_use') == 'easyocr'
    assert BBConfig.get('work_foot_print_megabytes') == 4096
    assert BBConfig.get('snapshots_database_path') == 'com_worktwins_userdata/snapshots.db'
    assert BBConfig.get('write_screenshots_to_files') is False
    assert BBConfig.get('snapshots_database_enabled') is True
    assert BBConfig.get('monitor_user_input') is True
    
    # Verify nested references are resolved correctly
    assert BBConfig.get('log_path') == 'com_worktwins_userdata/com_worktwins_logs'
    assert BBConfig.get('log_path_ocr') == 'com_worktwins_userdata/com_worktwins_ocr'
    assert BBConfig.get('log_path_images') == 'com_worktwins_userdata/com_worktwins_images'
    assert BBConfig.get('log_delimiter') == '|'
    assert BBConfig.get('log_memsize_limit') == 52428800

def test_override_method():
    """
    Test the override method to ensure it correctly overrides configuration values in-memory.
    """
    default_config_content = """
    # Default configuration
    mode = production
    userdata_path = /default_userdata
    filter_sensitive_data = False
    snapshots_database_path = {$userdata_path}/snapshots.db
    """
    
    # Mock the open function to read the default configuration
    with patch('builtins.open', mock_open(read_data=default_config_content)) as mocked_file:
        default_config_path = '/brainboost/global.config'
        # Also mock os.path.isfile to return True for the default_config_path
        with patch('os.path.isfile', return_value=True):
            BBConfig.configure(default_config_path)
            # Ensure the file was opened correctly
            mocked_file.assert_called_once_with(default_config_path)
    
    # Verify initial configuration
    assert BBConfig.get('mode') == 'production'
    assert BBConfig.get('userdata_path') == '/default_userdata'
    assert BBConfig.get('filter_sensitive_data') is False
    assert BBConfig.get('snapshots_database_path') == '/default_userdata/snapshots.db'
    
    # Override the 'mode' and 'filter_sensitive_data' configurations
    BBConfig.override('mode', 'testing')
    BBConfig.override('filter_sensitive_data', True)
    
    # Verify that overrides are applied
    assert BBConfig.get('mode') == 'testing'
    assert BBConfig.get('filter_sensitive_data') is True
    
    # Verify that other configurations remain unchanged
    assert BBConfig.get('userdata_path') == '/default_userdata'
    assert BBConfig.get('snapshots_database_path') == '/default_userdata/snapshots.db'
    
    # Override a non-existing key to ensure it can be set via overrides
    BBConfig.override('new_key', 'new_value')
    assert BBConfig.get('new_key') == 'new_value'
    
    # Attempting to get a key that doesn't exist and hasn't been overridden should raise KeyError
    with pytest.raises(KeyError, match="Key 'non_existing_key' not found in configuration."):
        BBConfig.get('non_existing_key')

def test_circular_reference_detection():
    """
    Test that a circular reference in the configuration raises a ValueError.
    """
    circular_config_content = """
    key1 = {$key2}
    key2 = {$key1}
    """
    
    # Mock the open function to read the circular configuration
    with patch('builtins.open', mock_open(read_data=circular_config_content)) as mocked_file:
        circular_config_path = 'path/to/circular.config'
        # Mock os.path.isfile to return True
        with patch('os.path.isfile', return_value=True):
            BBConfig.configure(circular_config_path)
            mocked_file.assert_called_once_with(circular_config_path)
    
    # Attempting to get 'key1' should raise a ValueError due to circular reference
    with pytest.raises(ValueError, match="Circular reference detected for key: key1"):
        BBConfig.get('key1')

def test_list_parsing():
    """
    Test that configuration values with commas are correctly parsed into lists.
    """
    list_config_content = """
    servers = server1, server2, server3
    ports = 80, 443, 8080
    debug_modes = True, False, True
    """
    
    # Mock the open function to read the list configuration
    with patch('builtins.open', mock_open(read_data=list_config_content)) as mocked_file:
        list_config_path = 'path/to/list.config'
        # Mock os.path.isfile to return True
        with patch('os.path.isfile', return_value=True):
            BBConfig.configure(list_config_path)
            mocked_file.assert_called_once_with(list_config_path)
    
    # Verify that the lists are parsed correctly
    assert BBConfig.get('servers') == ['server1', 'server2', 'server3']
    assert BBConfig.get('ports') == [80, 443, 8080]
    assert BBConfig.get('debug_modes') == [True, False, True]

def test_missing_configuration_file():
    """
    Test that configuring with a non-existent file raises FileNotFoundError.
    """
    # Mock os.path.isfile to return False, simulating a missing file
    with patch('os.path.isfile', return_value=False):
        with pytest.raises(FileNotFoundError, match="Custom configuration file 'path/to/missing.config' not found."):
            BBConfig.configure('path/to/missing.config')

def test_non_string_values():
    """
    Test that non-string configuration values are parsed correctly.
    """
    non_string_config_content = """
    integer_value = 42
    float_value = 3.1415
    boolean_true = True
    boolean_false = False
    """
    
    # Mock the open function to read the non-string configuration
    with patch('builtins.open', mock_open(read_data=non_string_config_content)) as mocked_file:
        non_string_config_path = 'path/to/non_string.config'
        # Mock os.path.isfile to return True
        with patch('os.path.isfile', return_value=True):
            BBConfig.configure(non_string_config_path)
            mocked_file.assert_called_once_with(non_string_config_path)
    
    # Verify that non-string values are parsed correctly
    assert BBConfig.get('integer_value') == 42
    assert BBConfig.get('float_value') == 3.1415
    assert BBConfig.get('boolean_true') is True
    assert BBConfig.get('boolean_false') is False
