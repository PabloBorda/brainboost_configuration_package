# File: brainboost_configuration_package/BBConfig.py

import re
import os
import json

class BBConfig:
    
    _conf = {}
    _resolved_conf = {}
    _overrides = {}  # Dictionary to store overridden values in-memory
    _config_file = '/brainboost/global.config'  # Default configuration file path
    _upload_to_redis = False  # New flag to indicate whether to use Redis for global configuration
    
    @classmethod
    def read_config(cls):
        cls._conf = {}
        content = ''
        try:
            with open(cls._config_file) as f:
                content = f.readlines()
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file '{cls._config_file}' not found.")
        
        for l in content:
            l = l.strip()
            if len(l) > 3 and not l.startswith('#'):
                if '=' in l:
                    parts = l.split('=', 1)
                    a = parts[0].strip()
                    b = parts[1].strip()
                    cls._conf[a] = b
        return cls._conf
    
    @classmethod
    def resolve_value(cls, value, seen_keys=None):
        if seen_keys is None:
            seen_keys = set()
        
        pattern = re.compile(r'\{\$(\w+)\}')
        
        def replacer(match):
            key = match.group(1)
            if key in seen_keys:
                raise ValueError(f"Circular reference detected for key: {key}")
            seen_keys.add(key)
            replacement = cls.get(key, resolve=True, seen_keys=seen_keys)
            seen_keys.remove(key)
            return str(replacement)
        
        while True:
            new_value, count = pattern.subn(replacer, value)
            if count == 0:
                break
            value = new_value
        return value
    
    @classmethod
    def _parse_value(cls, value):
        """Parse the string value into the appropriate Python data type."""
        if not isinstance(value, str):
            return value

        value = value.strip()
        if value == 'True':
            return True
        elif value == 'False':
            return False
        elif value.isdigit():
            return int(value)
        else:
            try:
                float_val = float(value)
                return float_val
            except ValueError:
                pass
        return value

    @classmethod
    def get(cls, k, resolve=True, seen_keys=None):
        # If configuration was uploaded to Redis, try to retrieve it from there.
        if cls._upload_to_redis:
            try:
                import redis
                redis_server_ip = cls._conf.get("redis_server_ip", "localhost")
                redis_server_port = int(cls._conf.get("redis_server_port", "6379"))
                r = redis.Redis(host=redis_server_ip, port=redis_server_port, db=0)
                config_str = r.get("BBConfig:global_config")
                if config_str is not None:
                    cls._conf = json.loads(config_str)
                    print("Configuration retrieved from Redis for key 'BBConfig:global_config'.")
                else:
                    print("No configuration found in Redis under key 'BBConfig:global_config'. Using local configuration.")
            except Exception as e:
                print("Error reading configuration from Redis: " + str(e))
        
        if not cls._conf:
            cls.read_config()
        
        # 1) Check if there's an override for this key
        if k in cls._overrides:
            raw_value = cls._overrides[k]
        else:
            if k not in cls._conf:
                # For specific keys, use defaults if not found.
                if k == "redis_server_ip":
                    raw_value = "localhost"
                elif k == "redis_server_port":
                    raw_value = "6379"
                else:
                    raise KeyError(f"Key '{k}' not found in configuration.")
            else:
                raw_value = cls._conf[k]
        
        if resolve and isinstance(raw_value, str):
            resolved = cls.resolve_value(raw_value, seen_keys)
        else:
            resolved = raw_value
        
        if isinstance(resolved, str) and ',' in resolved:
            items = [item.strip() for item in resolved.split(',')]
            return [cls._parse_value(item) for item in items]
        else:
            return cls._parse_value(resolved)
    
    @classmethod
    def sandbox(cls):
        return cls.get(k='mode') == 'sandbox'
    
    @classmethod
    def override(cls, k, value):
        if not cls._conf:
            cls.read_config()
        
        cls._overrides[k] = value
        cls._conf[k] = value
        print(f"Configuration key '{k}' overridden with value: {value}.")
        if cls._upload_to_redis:
            try:
                import redis
                redis_server_ip = cls._conf.get("redis_server_ip", "localhost")
                redis_server_port = int(cls._conf.get("redis_server_port", "6379"))
                r = redis.Redis(host=redis_server_ip, port=redis_server_port, db=0)
                r.set("BBConfig:global_config", json.dumps(cls._conf))
                print("Overridden configuration updated in Redis for key 'BBConfig:global_config'.")
            except Exception as e:
                raise Exception("Failed to update configuration in Redis: " + str(e))
    
    @classmethod
    def add_if_not_exists(cls, k, value):
        if not cls._conf:
            cls.read_config()
        
        if k not in cls._conf:
            cls._conf[k] = value
        else:
            print(f"Warning: Key '{k}' already exists in the configuration. No changes were made.")
    
    @classmethod
    def configure(cls, custom_config_path, upload_to_redis=False):
        if not os.path.isfile(custom_config_path):
            raise FileNotFoundError(f"Custom configuration file '{custom_config_path}' not found.")
        
        cls._config_file = custom_config_path
        cls._conf = {}
        cls._overrides = {}
        cls.read_config()
        cls._resolved_conf = {}
        
        cls._upload_to_redis = upload_to_redis
        
        if upload_to_redis:
            try:
                import redis
                # Obtain Redis connection parameters from the loaded configuration.
                redis_server_ip = cls._conf.get("redis_server_ip", "localhost")
                redis_server_port = int(cls._conf.get("redis_server_port", "6379"))
                r = redis.Redis(host=redis_server_ip, port=redis_server_port, db=0)
                r.set("BBConfig:global_config", json.dumps(cls._conf))
                print("Configuration uploaded to Redis under key 'BBConfig:global_config' using Redis at {}:{}.".format(redis_server_ip, redis_server_port))
            except Exception as e:
                raise Exception("Failed to upload configuration to Redis: " + str(e))
# End of BBConfig.py
