# routes/derived_metrics.py
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
import logging
from database.queries import DerivedMetricsQueries, ObservationQueries, FieldQueries
from auth import RoleBasedAccessControl
from routes.helpers import extract_user_id

logger = logging.getLogger(__name__)
router = APIRouter()

# ============ SCHEMAS ============

class DerivedMetricCreate(BaseModel):
    observation_id: int
    ndvi: float
    evi: float
    soil_moisture: float
    crop_health_score: float

class DerivedMetricCellUpdate(BaseModel):
    column_name: str
    value: float

# ============ ROUTES ============

@router.get("/", tags=["Derived Metrics"])
async def get_all_metrics(authorization: str = Header(None)):
    """GET all derived metrics with RBAC filtering"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        user = RoleBasedAccessControl.check_permission(user_id, 'derived_metrics', 'read')
        all_metrics = DerivedMetricsQueries.get_all_metrics()
        if user['role'] == 'farmer':
            user_fields = FieldQueries.get_fields_by_user(user_id)
            user_field_ids = {f['id'] for f in user_fields}
            all_obs = ObservationQueries.get_all_observations()
            farmer_obs_ids = {o['id'] for o in all_obs if o['field_id'] in user_field_ids}
            metrics = [m for m in all_metrics if m['observation_id'] in farmer_obs_ids]
            visibility = "own field metrics only"
        else:
            metrics = all_metrics
            visibility = "all metrics"
        logger.info(f"User {user_id} ({user['role']}) retrieved {len(metrics)} derived metrics")
        return {"count": len(metrics), "user_role": user['role'], "visibility": visibility, "derived_metrics": metrics}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting derived metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve derived metrics")


@router.get("/observation/{observation_id}", tags=["Derived Metrics"])
async def get_metrics_by_observation(observation_id: int, authorization: str = Header(None)):
    """GET derived metrics for a specific observation"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        user = RoleBasedAccessControl.check_permission(user_id, 'derived_metrics', 'read')
        observation = ObservationQueries.get_observation_by_id(observation_id)
        if not observation:
            raise HTTPException(status_code=404, detail="Observation not found")
        if user['role'] == 'farmer':
            field = FieldQueries.get_field_by_id(observation['field_id'])
            if not field or field['user_id'] != user_id:
                raise HTTPException(status_code=403, detail="Access denied")
        all_metrics = DerivedMetricsQueries.get_all_metrics()
        metrics = [m for m in all_metrics if m['observation_id'] == observation_id]
        return {"observation_id": observation_id, "count": len(metrics), "derived_metrics": metrics}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting observation metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve derived metrics")


@router.post("/", status_code=201, tags=["Derived Metrics"])
async def create_metric(metric_data: DerivedMetricCreate, authorization: str = Header(None)):
    """CREATE new derived metric - admin only"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        RoleBasedAccessControl.check_permission(user_id, 'derived_metrics', 'create')
        if not ObservationQueries.get_observation_by_id(metric_data.observation_id):
            raise HTTPException(status_code=404, detail="Observation not found")
        result = DerivedMetricsQueries.create_metric(
            observation_id=metric_data.observation_id,
            ndvi=metric_data.ndvi,
            evi=metric_data.evi,
            soil_moisture=metric_data.soil_moisture,
            crop_health_score=metric_data.crop_health_score
        )
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create derived metric")
        logger.info(f"Derived metric created for observation {metric_data.observation_id} by user {user_id}")
        return {"message": "Derived metric created successfully", "metric": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating derived metric: {e}")
        raise HTTPException(status_code=500, detail="Failed to create derived metric")


@router.patch("/{metric_id}/cell", tags=["Derived Metrics"])
async def update_metric_cell(metric_id: int, update_data: DerivedMetricCellUpdate, authorization: str = Header(None)):
    """UPDATE single cell in derived metric - admin only"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        RoleBasedAccessControl.check_permission(user_id, 'derived_metrics', 'update')
        DerivedMetricsQueries.update_metric_cell(metric_id, update_data.column_name, update_data.value)
        logger.info(f"Derived metric {metric_id} updated: {update_data.column_name} by user {user_id}")
        return {
            "message": f"Derived metric {update_data.column_name} updated successfully",
            "metric_id": metric_id,
            "column": update_data.column_name,
            "new_value": update_data.value
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating derived metric: {e}")
        raise HTTPException(status_code=500, detail="Failed to update derived metric")


@router.delete("/{metric_id}", tags=["Derived Metrics"])
async def delete_metric(metric_id: int, authorization: str = Header(None)):
    """DELETE derived metric - admin only"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        RoleBasedAccessControl.check_permission(user_id, 'derived_metrics', 'delete')
        metric = DerivedMetricsQueries.get_metric_by_id(metric_id)
        if not metric:
            raise HTTPException(status_code=404, detail="Derived metric not found")
        DerivedMetricsQueries.delete_metric(metric_id)
        logger.info(f"Derived metric {metric_id} deleted by user {user_id}")
        return {"message": "Derived metric deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting derived metric: {e}")
        raise HTTPException(status_code=400, detail="Failed to delete derived metric")