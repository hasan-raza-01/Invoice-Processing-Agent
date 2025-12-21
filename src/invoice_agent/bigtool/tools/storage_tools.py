"""Storage tools for file persistence"""
from invoice_agent.bigtool.bigtool_picker import BaseTool
from typing import Any
import json
import uuid
from pathlib import Path


class LocalStorageTool(BaseTool):
    """Local filesystem storage"""
    name = "local_storage"
    capability = "storage"
    
    def __init__(self):
        self.storage_dir = Path("data") / "stored_invoices"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def execute(self, data: Any, **kwargs) -> str:
        """
        Store data to local filesystem
        
        Args:
            data: Data to store
            
        Returns:
            Storage ID
        """
        storage_id = str(uuid.uuid4())
        file_path = self.storage_dir / f"{storage_id}.json"
        
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        
        return storage_id
