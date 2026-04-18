# routes/alerts.py
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
import logging
from database.queries import AlertQueries, FieldQueries
from auth import RoleBasedAccessControl
from routes.helpers import extract_user_id

logger = logging.getLogger(__name__)
router = APIRouter()

# ============ SCHEMAS ============

class AlertCreate(BaseModel):
    field_id: int
    alert_type: str
    severity: str
    message: str
    observation_id: Optional[int] = None

class AlertCellUpdate(BaseModel):
    column_name: str
    value: str

# ============ ROUTES ============

@router.get("/", tags=["Alerts"])
async def get_all_alerts(authorization: str = Header(None)):
    """GET all alerts with RBAC filtering"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        user = RoleBasedAccessControl.check_permission(user_id, 'alerts', 'read')
        all_alerts = AlertQueries.get_all_alerts()
        if user['role'] == 'farmer':
            user_fields = FieldQueries.get_fields_by_user(user_id)
            user_field_ids = {f['id'] for f in user_fields}
            alerts = [a for a in all_alerts if a['field_id'] in user_field_ids]
            visibility = "own field alerts only"
        else:
            alerts = all_alerts
            visibility = "all alerts"
        logger.info(f"User {user_id} ({user['role']}) retrieved {len(alerts)} alerts")
        return {"count": len(alerts), "user_role": user['role'], "visibility": visibility, "alerts": alerts}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")


@router.get("/unresolved", tags=["Alerts"])  # ✅ must be above /{alert_id}
async def get_unresolved_alerts(authorization: str = Header(None)):
    """GET all unresolved alerts with RBAC filtering"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        user = RoleBasedAccessControl.check_permission(user_id, 'alerts', 'read')
        all_unresolved = AlertQueries.get_unresolved_alerts()
        if user['role'] == 'farmer':
            user_fields = FieldQueries.get_fields_by_user(user_id)
            user_field_ids = {f['id'] for f in user_fields}
            alerts = [a for a in all_unresolved if a['field_id'] in user_field_ids]
        else:
            alerts = all_unresolved
        logger.info(f"User {user_id} retrieved {len(alerts)} unresolved alerts")
        return {"count": len(alerts), "status": "unresolved", "alerts": alerts}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting unresolved alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")


@router.get("/{alert_id}", tags=["Alerts"])
async def get_alert_by_id(alert_id: int, authorization: str = Header(None)):
    """GET alert by ID"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        user = RoleBasedAccessControl.check_permission(user_id, 'alerts', 'read')
        all_alerts = AlertQueries.get_all_alerts()
        alert = next((a for a in all_alerts if a['id'] == alert_id), None)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        if user['role'] == 'farmer':
            field = FieldQueries.get_field_by_id(alert['field_id'])
            if not field or field['user_id'] != user_id:
                raise HTTPException(status_code=403, detail="Access denied")
        return alert
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alert")


@router.post("/", status_code=201, tags=["Alerts"])
async def create_alert(alert_data: AlertCreate, authorization: str = Header(None)):
    """CREATE new alert - admin and agronomist"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        RoleBasedAccessControl.check_permission(user_id, 'alerts', 'create')
        if not FieldQueries.get_field_by_id(alert_data.field_id):
            raise HTTPException(status_code=404, detail="Field not found")
        result = AlertQueries.create_alert(
            field_id=alert_data.field_id,
            alert_type=alert_data.alert_type,
            severity=alert_data.severity,
            message=alert_data.message,
            observation_id=alert_data.observation_id
        )
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create alert")
        logger.info(f"Alert created for field {alert_data.field_id} by user {user_id}")
        return {"message": "Alert created successfully", "alert": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to create alert")


@router.patch("/{alert_id}/resolve", tags=["Alerts"])
async def resolve_alert(alert_id: int, authorization: str = Header(None)):
    """RESOLVE an alert - admin and agronomist"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        RoleBasedAccessControl.check_permission(user_id, 'alerts', 'update')
        all_alerts = AlertQueries.get_all_alerts()
        alert = next((a for a in all_alerts if a['id'] == alert_id), None)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        if alert['is_resolved']:
            raise HTTPException(status_code=400, detail="Alert is already resolved")
        AlertQueries.resolve_alert(alert_id)
        logger.info(f"Alert {alert_id} resolved by user {user_id}")
        return {"message": "Alert resolved successfully", "alert_id": alert_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to resolve alert")


@router.patch("/{alert_id}/cell", tags=["Alerts"])
async def update_alert_cell(alert_id: int, update_data: AlertCellUpdate, authorization: str = Header(None)):
    """UPDATE single cell in alert - admin and agronomist"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        RoleBasedAccessControl.check_permission(user_id, 'alerts', 'update')
        all_alerts = AlertQueries.get_all_alerts()
        alert = next((a for a in all_alerts if a['id'] == alert_id), None)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        AlertQueries.update_alert_cell(alert_id, update_data.column_name, update_data.value)
        logger.info(f"Alert {alert_id} updated: {update_data.column_name} by user {user_id}")
        return {
            "message": f"Alert {update_data.column_name} updated successfully",
            "alert_id": alert_id,
            "column": update_data.column_name,
            "new_value": update_data.value
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to update alert")