#!/usr/bin/env python
"""Standalone launcher for PBIP MCP Server.

This script can be run directly without module import issues.
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
script_dir = Path(__file__).parent
src_dir = script_dir / "src"
sys.path.insert(0, str(src_dir))

# Now we can import and run the server
if __name__ == "__main__":
    from pbip_mcp.server import main

    main()
