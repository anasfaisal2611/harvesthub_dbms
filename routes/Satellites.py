# routes/satellites.py
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
import logging
from database.queries import SatelliteQueries
from auth import RoleBasedAccessControl
from routes.helpers import extract_user_id

logger = logging.getLogger(__name__)
router = APIRouter()

# ============ SCHEMAS ============

class SatelliteCreate(BaseModel):
    satellite_name: str
    provider: str
    resolution: float

class SatelliteCellUpdate(BaseModel):
    column_name: str
    value: str

# ============ ROUTES ============

@router.get("/", tags=["Satellites"])
async def get_all_satellites(authorization: str = Header(None)):
    """GET all satellites"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        RoleBasedAccessControl.check_permission(user_id, 'satellites', 'read')
        satellites = SatelliteQueries.get_all_satellites()
        return {"count": len(satellites), "satellites": satellites}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting satellites: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve satellites")


@router.get("/{satellite_id}", tags=["Satellites"])
async def get_satellite_by_id(satellite_id: int, authorization: str = Header(None)):
    """GET satellite by ID"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        RoleBasedAccessControl.check_permission(user_id, 'satellites', 'read')
        satellite = SatelliteQueries.get_satellite_by_id(satellite_id)
        if not satellite:
            raise HTTPException(status_code=404, detail="Satellite not found")
        return satellite
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting satellite: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve satellite")


@router.post("/", status_code=201, tags=["Satellites"])
async def create_satellite(satellite_data: SatelliteCreate, authorization: str = Header(None)):
    """CREATE new satellite - admin only"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        RoleBasedAccessControl.check_permission(user_id, 'satellites', 'create')
        result = SatelliteQueries.create_satellite(
            satellite_name=satellite_data.satellite_name,
            provider=satellite_data.provider,
            resolution=satellite_data.resolution
        )
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create satellite")
        logger.info(f"Satellite created: {satellite_data.satellite_name} by user {user_id}")
        return {"message": "Satellite created successfully", "satellite": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating satellite: {e}")
        raise HTTPException(status_code=500, detail="Failed to create satellite")


@router.patch("/{satellite_id}/cell", tags=["Satellites"])
async def update_satellite_cell(satellite_id: int, update_data: SatelliteCellUpdate, authorization: str = Header(None)):
    """UPDATE single cell in satellite - admin only"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        RoleBasedAccessControl.check_permission(user_id, 'satellites', 'update')
        satellite = SatelliteQueries.get_satellite_by_id(satellite_id)
        if not satellite:
            raise HTTPException(status_code=404, detail="Satellite not found")
        SatelliteQueries.update_satellite_cell(satellite_id, update_data.column_name, update_data.value)
        logger.info(f"Satellite {satellite_id} updated: {update_data.column_name} by user {user_id}")
        return {
            "message": f"Satellite {update_data.column_name} updated successfully",
            "satellite_id": satellite_id,
            "column": update_data.column_name,
            "new_value": update_data.value
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating satellite: {e}")
        raise HTTPException(status_code=500, detail="Failed to update satellite")


@router.delete("/{satellite_id}", tags=["Satellites"])
async def delete_satellite(satellite_id: int, authorization: str = Header(None)):
    """DELETE satellite - admin only"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        RoleBasedAccessControl.check_permission(user_id, 'satellites', 'delete')
        satellite = SatelliteQueries.get_satellite_by_id(satellite_id)
        if not satellite:
            raise HTTPException(status_code=404, detail="Satellite not found")
        SatelliteQueries.delete_satellite(satellite_id)
        logger.info(f"Satellite {satellite_id} deleted by user {user_id}")
        return {"message": "Satellite deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting satellite: {e}")
        raise HTTPException(status_code=400, detail="Failed to delete satellite")