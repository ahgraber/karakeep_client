import logging
from pathlib import Path

# Package initialization for aizk

# assumes:
# karakeep_client
# ├ src/
# | └ karakeep_client
# |   └ __init__.py - (this file)
# └ VERSION

# with open(Path(__file__).parent.parent / "VERSION", "r") as f:
#     __version__ = f.readline().strip()

# add nullhandler to prevent a default configuration being used if the calling application doesn't set one
logger = logging.getLogger("karakeep_client").addHandler(logging.NullHandler())
