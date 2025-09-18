"""
Configuration management utilities
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manage configuration from files and environment variables"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_path: Path to configuration file (defaults to config/config.yaml)
        """
        self.config_path = config_path or self._find_config_file()
        self.config = {}
        
        # Load environment variables
        load_dotenv()
        
        # Load configuration
        self._load_config()
        
        logger.info(f"Configuration loaded from {self.config_path}")
    
    def _find_config_file(self) -> str:
        """Find the configuration file in common locations"""
        possible_paths = [
            'config/config.yaml',
            'config.yaml',
            os.path.expanduser('~/.datadog-cost-analyzer/config.yaml'),
            '/etc/datadog-cost-analyzer/config.yaml'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # Return default path if none found
        return 'config/config.yaml'
    
    def _load_config(self) -> None:
        """Load configuration from YAML file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = yaml.safe_load(f) or {}
                    
                # Substitute environment variables
                self._substitute_env_vars(self.config)
            else:
                logger.warning(f"Configuration file not found: {self.config_path}")
                self.config = self._get_default_config()
                
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self.config = self._get_default_config()
    
    def _substitute_env_vars(self, obj: Any) -> Any:
        """Recursively substitute environment variables in configuration"""
        if isinstance(obj, dict):
            return {key: self._substitute_env_vars(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_env_vars(item) for item in obj]
        elif isinstance(obj, str) and obj.startswith('${') and obj.endswith('}'):
            env_var = obj[2:-1]
            return os.getenv(env_var, obj)
        else:
            return obj
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'datadog': {
                'api_key': os.getenv('DD_API_KEY', ''),
                'app_key': os.getenv('DD_APP_KEY', ''),
                'site': os.getenv('DD_SITE', 'datadoghq.com')
            },
            'analysis': {
                'lookback_weeks': 12,
                'anomaly_detection': {
                    'z_score_threshold': 2.5,
                    'iqr_multiplier': 1.5,
                    'min_change_percent': 10.0,
                    'seasonal_periods': 4
                },
                'cost_categories': [
                    'infrastructure', 'logs', 'metrics', 'traces',
                    'synthetics', 'rum', 'security', 'network'
                ]
            },
            'reporting': {
                'formats': ['html', 'json', 'csv'],
                'email': {
                    'enabled': False,
                    'smtp_server': os.getenv('SMTP_SERVER', ''),
                    'smtp_port': int(os.getenv('SMTP_PORT', '587')),
                    'username': os.getenv('SMTP_USERNAME', ''),
                    'password': os.getenv('SMTP_PASSWORD', ''),
                    'from_email': os.getenv('FROM_EMAIL', ''),
                    'to_emails': os.getenv('TO_EMAILS', '').split(',') if os.getenv('TO_EMAILS') else []
                }
            },
            'web': {
                'host': '0.0.0.0',
                'port': 12000,
                'debug': False
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file': 'logs/cost_analyzer.log'
            }
        }
    
    def get_config(self) -> Dict[str, Any]:
        """Get the complete configuration"""
        return self.config.copy()
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get a specific configuration section"""
        return self.config.get(section, {})
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation
        
        Args:
            key: Configuration key in dot notation (e.g., 'analysis.lookback_weeks')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set_value(self, key: str, value: Any) -> None:
        """
        Set a configuration value using dot notation
        
        Args:
            key: Configuration key in dot notation
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        # Navigate to the parent dictionary
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
    
    def save_config(self, path: Optional[str] = None) -> None:
        """
        Save configuration to file
        
        Args:
            path: Path to save configuration (defaults to current config path)
        """
        save_path = path or self.config_path
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
                
            logger.info(f"Configuration saved to {save_path}")
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise
    
    def validate_config(self) -> Dict[str, Any]:
        """
        Validate configuration and return validation results
        
        Returns:
            Dictionary with validation results
        """
        results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check required Datadog credentials
        if not self.get_value('datadog.api_key'):
            results['errors'].append('Datadog API key is required')
            results['valid'] = False
        
        if not self.get_value('datadog.app_key'):
            results['errors'].append('Datadog Application key is required')
            results['valid'] = False
        
        # Check analysis parameters
        lookback_weeks = self.get_value('analysis.lookback_weeks', 0)
        if lookback_weeks < 1:
            results['warnings'].append('Lookback weeks should be at least 1')
        
        z_threshold = self.get_value('analysis.anomaly_detection.z_score_threshold', 0)
        if z_threshold < 1.0:
            results['warnings'].append('Z-score threshold should be at least 1.0')
        
        # Check web configuration
        port = self.get_value('web.port', 0)
        if not (1024 <= port <= 65535):
            results['warnings'].append('Web port should be between 1024 and 65535')
        
        return results
    
    def setup_logging(self) -> None:
        """Setup logging based on configuration"""
        log_config = self.get_section('logging')
        
        # Create logs directory if it doesn't exist
        log_file = log_config.get('file', 'logs/cost_analyzer.log')
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, log_config.get('level', 'INFO')),
            format=log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            handlers=[
                logging.FileHandler(log_file) if log_file else logging.NullHandler(),
                logging.StreamHandler()
            ]
        )
        
        logger.info("Logging configured")
    
    def get_datadog_credentials(self) -> Dict[str, str]:
        """Get Datadog API credentials"""
        return {
            'api_key': self.get_value('datadog.api_key', ''),
            'app_key': self.get_value('datadog.app_key', ''),
            'site': self.get_value('datadog.site', 'datadoghq.com')
        }