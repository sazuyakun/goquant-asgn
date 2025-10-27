"""Configuration loader for the application."""

import logging
import os

import yaml
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def load_env():
    """
    Loads .env file
    """
    env_path = ".env"
    if os.path.exists(env_path):
        load_dotenv(env_path)
        logger.info(".env file loaded.")
    else:
        logger.warning(".env file not found. API Keys may be missing.")


def load_config(config_path="config/targets.yaml"):
    """
    Loads configuration from a YAML file.
    """

    load_env()

    if not os.path.exists(config_path):
        logger.error("Config file not found at %s", config_path)
        raise FileNotFoundError(f"Config file not found at {config_path}")

    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    logger.info(f"Config file {config_path} loaded successfully.")
    return config
