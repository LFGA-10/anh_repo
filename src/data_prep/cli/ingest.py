import argparse
import os
from pathlib import Path
from data_prep.core.processor import processor
from data_prep.utils.logger import logger

def main():
    parser = argparse.ArgumentParser(description="UWERA AI Curriculum Ingestion CLI")
    parser.add_argument("--raw_dir", required=True, help="Path to raw documents directory")
    parser.add_argument("--trade_id", required=True, help="e.g. ANH")
    parser.add_argument("--trade_name", required=True, help="e.g. 'Animal Health'")
    parser.add_argument("--level_id", required=True, help="e.g. L3")
    parser.add_argument("--module_id", required=True, help="e.g. AHNRF302")
    parser.add_argument("--module_name", required=True, help="e.g. 'Ruminant farming'")
    
    args = parser.parse_args()
    
    raw_path = Path(args.raw_dir).resolve()
    if not raw_path.exists():
        logger.error(f"Directory not found: {raw_path}")
        return

    # Process all supported documents in the directory
    extensions = {".pdf", ".docx", ".txt"}
    for root, _, files in os.walk(raw_path):
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix.lower() in extensions:
                try:
                    processor.process_document(
                        doc_path=file_path,
                        trade_id=args.trade_id,
                        trade_name=args.trade_name,
                        level_id=args.level_id,
                        module_id=args.module_id,
                        module_name=args.module_name
                    )
                except Exception as e:
                    logger.error(f"Failed to process {file}: {e}")

if __name__ == "__main__":
    main()
