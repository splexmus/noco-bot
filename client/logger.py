import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "models"

class Logger:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename='app.log',
            encoding='utf-8',
            filemode='w'
        )

    def log_error(self, mesg) -> None:
        self.logger.error(mesg)

    def log_warning(self, mesg) -> None:
        self.logger.warning(mesg)