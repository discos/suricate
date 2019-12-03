import os

suricate_dir = os.path.join(os.getenv('HOME'), '.suricate')
config_dir = os.path.join(suricate_dir, 'config')
config_file  = os.path.join(config_dir, 'config.yaml')
log_dir = os.path.join(suricate_dir, 'logs')
template_dir = os.path.join(suricate_dir, 'templates')
