import yaml
import os


def load_config(config_path):
    """
    Loads a YAML configuration file and returns it as a dictionary.

    Parameters:
    - config_path (str): Path to the .yaml config file

    Returns:
    - dict: Config parameters
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)

    return config
