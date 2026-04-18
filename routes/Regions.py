# routes/regions.py
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
import logging
from database.queries import RegionQueries
from auth import RoleBasedAccessControl
from routes.helpers import extract_user_id

logger = logging.getLogger(__name__)
router = APIRouter()

# ============ SCHEMAS ============

class RegionCreate(BaseModel):
    region_name: str
    climate_type: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class RegionCellUpdate(BaseModel):
    column_name: str
    value: str

# ============ ROUTES ============

@router.get("/", tags=["Regions"])
async def get_all_regions(authorization: str = Header(None)):
    """GET all regions"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        RoleBasedAccessControl.check_permission(user_id, 'regions', 'read')
        regions = RegionQueries.get_all_regions()
        return {"count": len(regions), "regions": regions}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting regions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve regions")


@router.get("/{region_id}", tags=["Regions"])
async def get_region_by_id(region_id: int, authorization: str = Header(None)):
    """GET region by ID"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        RoleBasedAccessControl.check_permission(user_id, 'regions', 'read')
        region = RegionQueries.get_region_by_id(region_id)
        if not region:
            raise HTTPException(status_code=404, detail="Region not found")
        return region
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting region: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve region")


@router.post("/", status_code=201, tags=["Regions"])
async def create_region(region_data: RegionCreate, authorization: str = Header(None)):
    """CREATE new region - admin only"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        RoleBasedAccessControl.check_permission(user_id, 'regions', 'create')
        result = RegionQueries.create_region(
            region_name=region_data.region_name,
            climate_type=region_data.climate_type,
            latitude=region_data.latitude,
            longitude=region_data.longitude
        )
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create region")
        logger.info(f"Region created: {region_data.region_name} by user {user_id}")
        return {"message": "Region created successfully", "region": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating region: {e}")
        raise HTTPException(status_code=500, detail="Failed to create region")


@router.patch("/{region_id}/cell", tags=["Regions"])
async def update_region_cell(region_id: int, update_data: RegionCellUpdate, authorization: str = Header(None)):
    """UPDATE single cell in region - admin only"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        RoleBasedAccessControl.check_permission(user_id, 'regions', 'update')
        region = RegionQueries.get_region_by_id(region_id)
        if not region:
            raise HTTPException(status_code=404, detail="Region not found")
        RegionQueries.update_region_cell(region_id, update_data.column_name, update_data.value)
        logger.info(f"Region {region_id} updated: {update_data.column_name} by user {user_id}")
        return {
            "message": f"Region {update_data.column_name} updated successfully",
            "region_id": region_id,
            "column": update_data.column_name,
            "new_value": update_data.value
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating region: {e}")
        raise HTTPException(status_code=500, detail="Failed to update region")