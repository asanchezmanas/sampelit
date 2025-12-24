"""
Region Manager and Geo Allocator

Copyright (c) 2024 Samplit Technologies
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


@dataclass
class Region:
    """Region configuration"""
    code: str  # 'us-east', 'eu-west', 'ap-south'
    name: str
    db_url: str
    countries: List[str]  # Countries in this region
    gdpr_compliant: bool = False
    active: bool = True


class RegionManager:
    """
    Manages regions and routes requests
    
    Example:
        >>> manager = RegionManager()
        >>> manager.add_region(Region(
        ...     code='eu-west',
        ...     name='Europe West',
        ...     db_url='postgres://eu-db:5432',
        ...     countries=['DE', 'FR', 'ES'],
        ...     gdpr_compliant=True
        ... ))
        >>> 
        >>> region = manager.get_region_for_country('DE')
        >>> # Returns eu-west region
    """
    
    def __init__(self):
        self.regions: Dict[str, Region] = {}
        self.country_to_region: Dict[str, str] = {}
    
    def add_region(self, region: Region):
        """Add region"""
        self.regions[region.code] = region
        
        for country in region.countries:
            self.country_to_region[country] = region.code
        
        logger.info(f"Added region: {region.name} ({region.code})")
    
    def get_region(self, region_code: str) -> Optional[Region]:
        """Get region by code"""
        return self.regions.get(region_code)
    
    def get_region_for_country(self, country: str) -> Optional[Region]:
        """Get region for country"""
        region_code = self.country_to_region.get(country)
        if region_code:
            return self.regions[region_code]
        return None
    
    def list_regions(self) -> List[Region]:
        """List all regions"""
        return list(self.regions.values())


class GeoAllocator:
    """
    Geo-aware allocation
    
    Routes allocation to appropriate region based on user location.
    
    Example:
        >>> allocator = GeoAllocator(region_manager)
        >>> 
        >>> context = {'country': 'DE', 'device': 'mobile'}
        >>> region, variant = await allocator.allocate(experiment_id, context)
        >>> # Uses EU region for German user
    """
    
    def __init__(self, region_manager: RegionManager):
        self.region_manager = region_manager
    
    async def allocate(
        self,
        experiment_id: UUID,
        context: Dict[str, Any]
    ) -> tuple[Optional[Region], Optional[UUID]]:
        """
        Allocate with geo-routing
        
        Args:
            experiment_id: Experiment ID
            context: User context with country
        
        Returns:
            (region, variant_id)
        """
        # Determine region
        country = context.get('country', 'US')
        region = self.region_manager.get_region_for_country(country)
        
        if not region:
            logger.warning(f"No region found for country {country}, using default")
            region = self._get_default_region()
        
        logger.info(f"Routing to region: {region.code}")
        
        # Allocate in region (simplified)
        # In production, would use region-specific DB connection
        variant_id = None  # Placeholder
        
        return region, variant_id
    
    def _get_default_region(self) -> Region:
        """Get default region"""
        regions = self.region_manager.list_regions()
        return regions[0] if regions else None
