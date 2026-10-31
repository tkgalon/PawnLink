import os
from pathlib import Path

# Set before pawnlink.api.main is imported, which decides at import time whether to mount the site.
os.environ["WEB_DIR"] = str(Path(__file__).parent / "web")
