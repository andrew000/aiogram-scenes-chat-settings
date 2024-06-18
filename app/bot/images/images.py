from pathlib import Path
from typing import Final

RAW_DIR: Final[Path] = Path(__file__).parent / "raw"
GREETING_IMAGE_PATH: Final[Path] = RAW_DIR / "GREETING.png"
FAREWELL_IMAGE_PATH: Final[Path] = RAW_DIR / "FAREWELL.png"
PROMOTE_IMAGE_PATH: Final[Path] = RAW_DIR / "PROMOTE.png"
EMPTY_VIDEO_IMAGE_PATH: Final[Path] = RAW_DIR / "EMPTY_VIDEO.mp4"
EMPTY_GIF_IMAGE_PATH: Final[Path] = RAW_DIR / "EMPTY_GIF.mp4"
EMPTY_STICKER_IMAGE_PATH: Final[Path] = RAW_DIR / "EMPTY_STICKER.webp"
