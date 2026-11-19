import sys
from pathlib import Path

# Ensure Capstone directory is on sys.path
capstone_root = Path(__file__).resolve().parent.parent
if str(capstone_root) not in sys.path:
    sys.path.insert(0, str(capstone_root))
