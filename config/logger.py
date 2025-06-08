import logging
import os

os.makedirs("logs", exist_ok=True)

logger = logging.getLogger("vector_logger")
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("logs/query.log", mode="a")
# formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
# file_handler.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(file_handler)
