import sys
from pathlib import Path

# Make the Agent package importable as "agent" (mirrors the uv workspace
# membership in the real project).
sys.path.insert(0, str(Path(__file__).resolve().parent / "Agent" / "src"))