"""Bigtool system for dynamic tool selection"""
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from invoice_agent.utils.logger import logger


class BaseTool(ABC):
    """Base class for all tools"""
    name: str = "base_tool"
    capability: str = ""
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """Execute the tool"""
        pass


class BigtoolPicker:
    """Dynamically select tools from pool based on capability and context"""
    
    def __init__(self):
        from invoice_agent.bigtool.tools.ocr_tools import TesseractOCR
        from invoice_agent.bigtool.tools.enrichment_tools import VendorDBEnrichment
        from invoice_agent.bigtool.tools.erp_tools import MockERPConnector
        from invoice_agent.bigtool.tools.email_tools import MockEmailTool
        from invoice_agent.bigtool.tools.storage_tools import LocalStorageTool
        
        # Initialize tool pools
        self.pools: Dict[str, List[BaseTool]] = {
            "ocr": [TesseractOCR()],
            "enrichment": [VendorDBEnrichment()],
            "erp_connector": [MockERPConnector()],
            "email": [MockEmailTool()],
            "storage": [LocalStorageTool()],
            "db": []  # DB operations handled by SQLAlchemy
        }
        
        logger.info("BigtoolPicker initialized with tool pools")
    
    def select(
        self,
        capability: str,
        context: Optional[Dict[str, Any]] = None
    ) -> BaseTool:
        """
        Select best tool for given capability
        
        Args:
            capability: Tool capability (ocr, enrichment, erp_connector, email, storage)
            context: Additional context for selection
            
        Returns:
            Selected tool instance
        """
        pool = self.pools.get(capability, [])
        
        if not pool:
            logger.warning(f"No tools available for capability: {capability}")
            return None
        
        # For now, return first tool in pool (can be enhanced with LLM-based selection)
        selected_tool = pool[0]
        
        logger.info(f"Bigtool selected: {selected_tool.name} for capability: {capability}")
        return selected_tool
    
    def get_pool(self, capability: str) -> List[BaseTool]:
        """Get all tools for a capability"""
        return self.pools.get(capability, [])
