# routes/observations.py
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
import logging
from database.queries import ObservationQueries, FieldQueries, SatelliteQueries, CropCycleQueries
from auth import RoleBasedAccessControl
from routes.helpers import extract_user_id

logger = logging.getLogger(__name__)
router = APIRouter()

# ============ SCHEMAS ============

class ObservationCreate(BaseModel):
    field_id: int
    satellite_id: int
    cycle_id: int
    observation_date: str
    cloud_cover: float

class ObservationCellUpdate(BaseModel):
    column_name: str
    value: str

# ============ ROUTES ============

@router.get("/", tags=["Observations"])
async def get_all_observations(authorization: str = Header(None)):
    """GET all observations with RBAC filtering"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        user = RoleBasedAccessControl.check_permission(user_id, 'observations', 'read')
        all_obs = ObservationQueries.get_all_observations()
        if user['role'] == 'farmer':
            user_fields = FieldQueries.get_fields_by_user(user_id)
            user_field_ids = {f['id'] for f in user_fields}
            observations = [o for o in all_obs if o['field_id'] in user_field_ids]
            visibility = "own field observations only"
        else:
            observations = all_obs
            visibility = "all observations"
        logger.info(f"User {user_id} ({user['role']}) retrieved {len(observations)} observations")
        return {"count": len(observations), "user_role": user['role'], "visibility": visibility, "observations": observations}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting observations: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve observations")


@router.get("/field/{field_id}", tags=["Observations"])
async def get_observations_by_field(field_id: int, authorization: str = Header(None)):
    """GET all observations for a specific field"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        user = RoleBasedAccessControl.check_permission(user_id, 'observations', 'read')
        field = FieldQueries.get_field_by_id(field_id)
        if not field:
            raise HTTPException(status_code=404, detail="Field not found")
        if user['role'] == 'farmer' and field['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        all_obs = ObservationQueries.get_all_observations()
        observations = [o for o in all_obs if o['field_id'] == field_id]
        return {"field_id": field_id, "field_name": field['field_name'], "count": len(observations), "observations": observations}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting field observations: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve observations")


@router.get("/{observation_id}", tags=["Observations"])
async def get_observation_by_id(observation_id: int, authorization: str = Header(None)):
    """GET observation by ID"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        user = RoleBasedAccessControl.check_permission(user_id, 'observations', 'read')
        observation = ObservationQueries.get_observation_by_id(observation_id)
        if not observation:
            raise HTTPException(status_code=404, detail="Observation not found")
        if user['role'] == 'farmer':
            field = FieldQueries.get_field_by_id(observation['field_id'])
            if not field or field['user_id'] != user_id:
                raise HTTPException(status_code=403, detail="Access denied")
        return observation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting observation: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve observation")


@router.post("/", status_code=201, tags=["Observations"])
async def create_observation(obs_data: ObservationCreate, authorization: str = Header(None)):
    """CREATE new observation - admin only"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        RoleBasedAccessControl.check_permission(user_id, 'observations', 'create')
        if not FieldQueries.get_field_by_id(obs_data.field_id):
            raise HTTPException(status_code=404, detail="Field not found")
        if not SatelliteQueries.get_satellite_by_id(obs_data.satellite_id):
            raise HTTPException(status_code=404, detail="Satellite not found")
        if not CropCycleQueries.get_crop_cycle_by_id(obs_data.cycle_id):
            raise HTTPException(status_code=404, detail="Crop cycle not found")
        result = ObservationQueries.create_observation(
            field_id=obs_data.field_id,
            satellite_id=obs_data.satellite_id,
            cycle_id=obs_data.cycle_id,
            observation_date=obs_data.observation_date,
            cloud_cover=obs_data.cloud_cover
        )
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create observation")
        logger.info(f"Observation created for field {obs_data.field_id} by user {user_id}")
        return {"message": "Observation created successfully", "observation": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating observation: {e}")
        raise HTTPException(status_code=500, detail="Failed to create observation")


@router.patch("/{observation_id}/cell", tags=["Observations"])
async def update_observation_cell(observation_id: int, update_data: ObservationCellUpdate, authorization: str = Header(None)):
    """UPDATE single cell in observation - admin only"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        RoleBasedAccessControl.check_permission(user_id, 'observations', 'update')
        if not ObservationQueries.get_observation_by_id(observation_id):
            raise HTTPException(status_code=404, detail="Observation not found")
        ObservationQueries.update_observation_cell(observation_id, update_data.column_name, update_data.value)
        logger.info(f"Observation {observation_id} updated: {update_data.column_name} by user {user_id}")
        return {
            "message": f"Observation {update_data.column_name} updated successfully",
            "observation_id": observation_id,
            "column": update_data.column_name,
            "new_value": update_data.value
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating observation: {e}")
        raise HTTPException(status_code=500, detail="Failed to update observation")