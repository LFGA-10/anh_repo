import sys
import os

# Add src to PYTHONPATH automatically
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from data_prep.cli.ingest import main

if __name__ == "__main__":
    main()