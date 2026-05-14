import pandas as pd
import io
import json
from typing import List, Dict, Any
from fastapi import UploadFile

class IngestionParser:
    @staticmethod
    def parse_file(file: UploadFile, content: bytes) -> List[Dict[str, Any]]:
        """
        Parses a CSV or XLSX file and returns a list of dictionaries.
        """
        filename = file.filename.lower()
        
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content))
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(content))
        else:
            raise ValueError("Unsupported file format. Use CSV or XLSX.")
        
        # Basic normalization: strip whitespace from strings and column names
        df.columns = [str(c).strip().lower() for c in df.columns]
        df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
        
        # Safe conversion to JSON-compatible dictionaries
        records_json = df.to_json(orient="records", date_format="iso")
        return json.loads(records_json)

    @staticmethod
    def validate_columns(data: List[Dict[str, Any]], required_columns: List[str]):
        """
        Verifies if the required columns are present in the parsed data.
        """
        if not data:
            return
        
        present_columns = set(data[0].keys())
        missing = [col for col in required_columns if col.lower() not in present_columns]
        
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(missing)}")
