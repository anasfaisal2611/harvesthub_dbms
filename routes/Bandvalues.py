# routes/band_values.py
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
import logging
from database.queries import BandValueQueries, ObservationQueries, FieldQueries
from auth import RoleBasedAccessControl
from routes.helpers import extract_user_id

logger = logging.getLogger(__name__)
router = APIRouter()

# ============ SCHEMAS ============

class BandValueCreate(BaseModel):
    observation_id: int
    band_name: str
    band_value: float

class BandValueCellUpdate(BaseModel):
    column_name: str
    value: str

# ============ ROUTES ============

@router.get("/", tags=["Band Values"])
async def get_all_band_values(authorization: str = Header(None)):
    """GET all band values with RBAC filtering"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        user = RoleBasedAccessControl.check_permission(user_id, 'band_values', 'read')
        all_values = BandValueQueries.get_all_band_values()
        if user['role'] == 'farmer':
            # Filter to only band values from observations on the farmer's fields
            user_fields = FieldQueries.get_fields_by_user(user_id)
            user_field_ids = {f['id'] for f in user_fields}
            all_obs = ObservationQueries.get_all_observations()
            farmer_obs_ids = {o['id'] for o in all_obs if o['field_id'] in user_field_ids}
            band_values = [b for b in all_values if b['observation_id'] in farmer_obs_ids]
            visibility = "own field band values only"
        else:
            band_values = all_values
            visibility = "all band values"
        logger.info(f"User {user_id} ({user['role']}) retrieved {len(band_values)} band values")
        return {"count": len(band_values), "user_role": user['role'], "visibility": visibility, "band_values": band_values}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting band values: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve band values")


@router.get("/observation/{observation_id}", tags=["Band Values"])
async def get_band_values_by_observation(observation_id: int, authorization: str = Header(None)):
    """GET all band values for a specific observation"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        user = RoleBasedAccessControl.check_permission(user_id, 'band_values', 'read')
        observation = ObservationQueries.get_observation_by_id(observation_id)
        if not observation:
            raise HTTPException(status_code=404, detail="Observation not found")
        if user['role'] == 'farmer':
            field = FieldQueries.get_field_by_id(observation['field_id'])
            if not field or field['user_id'] != user_id:
                raise HTTPException(status_code=403, detail="Access denied")
        all_values = BandValueQueries.get_all_band_values()
        band_values = [b for b in all_values if b['observation_id'] == observation_id]
        return {"observation_id": observation_id, "count": len(band_values), "band_values": band_values}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting observation band values: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve band values")


@router.post("/", status_code=201, tags=["Band Values"])
async def create_band_value(band_data: BandValueCreate, authorization: str = Header(None)):
    """CREATE new band value - admin only"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        RoleBasedAccessControl.check_permission(user_id, 'band_values', 'create')
        if not ObservationQueries.get_observation_by_id(band_data.observation_id):
            raise HTTPException(status_code=404, detail="Observation not found")
        result = BandValueQueries.create_band_value(
            observation_id=band_data.observation_id,
            band_name=band_data.band_name,
            band_value=band_data.band_value
        )
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create band value")
        logger.info(f"Band value created for observation {band_data.observation_id} by user {user_id}")
        return {"message": "Band value created successfully", "band_value": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating band value: {e}")
        raise HTTPException(status_code=500, detail="Failed to create band value")


@router.patch("/{band_id}/cell", tags=["Band Values"])
async def update_band_value_cell(band_id: int, update_data: BandValueCellUpdate, authorization: str = Header(None)):
    """UPDATE single cell in band value - admin only"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        RoleBasedAccessControl.check_permission(user_id, 'band_values', 'update')
        BandValueQueries.update_band_value_cell(band_id, update_data.column_name, update_data.value)
        logger.info(f"Band value {band_id} updated: {update_data.column_name} by user {user_id}")
        return {
            "message": f"Band value {update_data.column_name} updated successfully",
            "band_id": band_id,
            "column": update_data.column_name,
            "new_value": update_data.value
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating band value: {e}")
        raise HTTPException(status_code=500, detail="Failed to update band value")


@router.delete("/{band_id}", tags=["Band Values"])
async def delete_band_value(band_id: int, authorization: str = Header(None)):
    """DELETE band value - admin only"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        RoleBasedAccessControl.check_permission(user_id, 'band_values', 'delete')
        band_value = BandValueQueries.get_band_value_by_id(band_id)
        if not band_value:
            raise HTTPException(status_code=404, detail="Band value not found")
        BandValueQueries.delete_band_value(band_id)
        logger.info(f"Band value {band_id} deleted by user {user_id}")
        return {"message": "Band value deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting band value: {e}")
        raise HTTPException(status_code=400, detail="Failed to delete band value")