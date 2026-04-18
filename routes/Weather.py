# routes/weather.py
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
import logging
from database.queries import WeatherQueries, FieldQueries
from auth import RoleBasedAccessControl
from routes.helpers import extract_user_id

logger = logging.getLogger(__name__)
router = APIRouter()

# ============ SCHEMAS ============

class WeatherCreate(BaseModel):
    field_id: int
    date: str
    temperature: str
    rainfall: str
    humidity: str
    wind_speed: Optional[str] = None
    wind_direction: Optional[str] = None
    pressure: Optional[str] = None

class WeatherCellUpdate(BaseModel):
    column_name: str
    value: str

# ============ ROUTES ============

@router.get("/", tags=["Weather"])
async def get_all_weather(authorization: str = Header(None)):
    """GET all weather records with RBAC filtering"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        user = RoleBasedAccessControl.check_permission(user_id, 'weather', 'read')
        all_weather = WeatherQueries.get_all_weather()
        if user['role'] == 'farmer':
            user_fields = FieldQueries.get_fields_by_user(user_id)
            user_field_ids = {f['id'] for f in user_fields}
            weather = [w for w in all_weather if w['field_id'] in user_field_ids]
            visibility = "own field weather only"
        else:
            weather = all_weather
            visibility = "all weather records"
        logger.info(f"User {user_id} ({user['role']}) retrieved {len(weather)} weather records")
        return {"count": len(weather), "user_role": user['role'], "visibility": visibility, "weather": weather}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting weather: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve weather records")


@router.get("/field/{field_id}", tags=["Weather"])
async def get_weather_by_field(field_id: int, authorization: str = Header(None)):
    """GET all weather records for a specific field"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        user = RoleBasedAccessControl.check_permission(user_id, 'weather', 'read')
        field = FieldQueries.get_field_by_id(field_id)
        if not field:
            raise HTTPException(status_code=404, detail="Field not found")
        if user['role'] == 'farmer' and field['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        weather = WeatherQueries.get_weather_by_field(field_id)
        return {"field_id": field_id, "field_name": field['field_name'], "count": len(weather), "weather": weather}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting field weather: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve weather records")


@router.post("/", status_code=201, tags=["Weather"])
async def create_weather(weather_data: WeatherCreate, authorization: str = Header(None)):
    """CREATE new weather record - admin only"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        RoleBasedAccessControl.check_permission(user_id, 'weather', 'create')
        if not FieldQueries.get_field_by_id(weather_data.field_id):
            raise HTTPException(status_code=404, detail="Field not found")
        result = WeatherQueries.create_weather(
            field_id=weather_data.field_id,
            date=weather_data.date,
            temperature=weather_data.temperature,
            rainfall=weather_data.rainfall,
            humidity=weather_data.humidity,
            wind_speed=weather_data.wind_speed,
            wind_direction=weather_data.wind_direction,
            pressure=weather_data.pressure
        )
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create weather record")
        logger.info(f"Weather record created for field {weather_data.field_id} by user {user_id}")
        return {"message": "Weather record created successfully", "weather": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating weather: {e}")
        raise HTTPException(status_code=500, detail="Failed to create weather record")


@router.patch("/{weather_id}/cell", tags=["Weather"])
async def update_weather_cell(weather_id: int, update_data: WeatherCellUpdate, authorization: str = Header(None)):
    """UPDATE single cell in weather record - admin only"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        RoleBasedAccessControl.check_permission(user_id, 'weather', 'update')
        WeatherQueries.update_weather_cell(weather_id, update_data.column_name, update_data.value)
        logger.info(f"Weather {weather_id} updated: {update_data.column_name} by user {user_id}")
        return {
            "message": f"Weather {update_data.column_name} updated successfully",
            "weather_id": weather_id,
            "column": update_data.column_name,
            "new_value": update_data.value
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating weather: {e}")
        raise HTTPException(status_code=500, detail="Failed to update weather record")