# routes/fields.py
# Fields CRUD routes with raw DML queries, RBAC, and token extraction helper

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
import logging
from typing import Optional
from database.queries import FieldQueries, RegionQueries, ComplexQueries
from auth import RoleBasedAccessControl
from routes.helpers import extract_user_id

logger = logging.getLogger(__name__)
router = APIRouter()

# ============ PYDANTIC SCHEMAS ============

class FieldCreate(BaseModel):
    """Create field schema"""
    field_name: str
    user_id: int
    region_id: int
    latitude: float
    longitude: float
    area: float
    soil_type: str

class FieldUpdate(BaseModel):
    """Update field schema"""
    field_name: Optional[str] = None
    area: Optional[float] = None
    soil_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
from typing import Any
class FieldCellUpdate(BaseModel):
    """Update single cell schema"""
    column_name: str
    value: Any

# ============ FIELD ROUTES ============

@router.get("/", tags=["Fields"])
async def get_all_fields(authorization: str = Header(None)):
    """
    GET all fields - SELECT operation with RBAC
    
    Args:
        authorization: JWT token
    
    Returns:
        List of fields based on user role
    """
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        
        # Extract user_id from token using helper
        user_id = extract_user_id(authorization)
        
        # Check permission
        user = RoleBasedAccessControl.check_permission(user_id, 'fields', 'read')
        
        # GET fields based on role using DML SELECT
        if user['role'] == 'farmer':
            # Farmer sees only their own fields
            fields = FieldQueries.get_fields_by_user(user_id)
            visibility = "own fields only"
        else:
            # Agronomist and admin see all fields
            fields = FieldQueries.get_all_fields()
            visibility = "all fields"
        
        logger.info(f"User {user_id} ({user['role']}) retrieved {len(fields)} fields")

        return {
            "count": len(fields),
            "user_role": user['role'],
            "visibility": visibility,
            "fields": fields
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting fields: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve fields")

@router.get("/{field_id}", tags=["Fields"])
async def get_field_by_id(field_id: int, authorization: str = Header(None)):
    """
    GET field by ID - SELECT operation with RBAC
    
    Args:
        field_id: Field ID
        authorization: JWT token
    
    Returns:
        Field details
    """
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        
        # Extract user_id from token using helper
        user_id = extract_user_id(authorization)
        
        # Check permission
        user = RoleBasedAccessControl.check_permission(user_id, 'fields', 'read')
        
        # GET field using DML
        field = FieldQueries.get_field_by_id(field_id)
        
        if not field:
            raise HTTPException(status_code=404, detail="Field not found")
        
        # Check access for farmer
        if user['role'] == 'farmer' and field['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Cannot access others' fields")
        
        logger.info(f"Field {field_id} retrieved by user {user_id}")

        return field

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting field: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve field")

@router.post("/", status_code=201, tags=["Fields"])
async def create_field(field_data: FieldCreate, authorization: str = Header(None)):
    """
    CREATE new field - INSERT operation with RBAC
    
    Args:
        field_data: Field creation data
        authorization: JWT token
    
    Returns:
        Created field details with 201 status
    """
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        
        # Extract user_id from token using helper
        user_id = extract_user_id(authorization)
        
        # Check permission
        user = RoleBasedAccessControl.check_permission(user_id, 'fields', 'create')
        
        # Farmer can only create for themselves
        if user['role'] == 'farmer' and field_data.user_id != user_id:
            raise HTTPException(status_code=403, detail="Cannot create fields for others")
        
        # Agronomist cannot create fields
        if user['role'] == 'agronomist':
            raise HTTPException(status_code=403, detail="Agronomists cannot create fields")
        
        # Verify region exists
        region = RegionQueries.get_region_by_id(field_data.region_id)
        if not region:
            raise HTTPException(status_code=404, detail="Region not found")
        
        # INSERT field using DML
        result = FieldQueries.create_field(
            field_name=field_data.field_name,
            user_id=field_data.user_id,
            region_id=field_data.region_id,
            latitude=field_data.latitude,
            longitude=field_data.longitude,
            area=field_data.area,
            soil_type=field_data.soil_type
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create field")

        logger.info(f"Field created: {field_data.field_name} by user {user_id}")

        return {
            "message": "Field created successfully",
            "field": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating field: {e}")
        raise HTTPException(status_code=400, detail="Failed to create field")

@router.put("/{field_id}", tags=["Fields"])
async def update_field(field_id: int, field_data: FieldUpdate, authorization: str = Header(None)):
    """
    UPDATE field - UPDATE operation with RBAC
    
    Args:
        field_id: Field ID
        field_data: Field update data
        authorization: JWT token
    
    Returns:
        Updated field details
    """
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        
        # Extract user_id from token using helper
        user_id = extract_user_id(authorization)
        
        # Check permission
        user = RoleBasedAccessControl.check_permission(user_id, 'fields', 'update')
        
        # Check if field exists
        field = FieldQueries.get_field_by_id(field_id)
        if not field:
            raise HTTPException(status_code=404, detail="Field not found")
        
        # Check access
        if user['role'] == 'farmer' and field['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Cannot update others' fields")
        
        # UPDATE field using DML
        FieldQueries.update_field(
            field_id=field_id,
            field_name=field_data.field_name,
            area=field_data.area,
            soil_type=field_data.soil_type,
            latitude=field_data.latitude,
            longitude=field_data.longitude
        )
        
        updated_field = FieldQueries.get_field_by_id(field_id)

        logger.info(f"Field {field_id} updated by user {user_id}")

        return {
            "message": "Field updated successfully",
            "field": updated_field
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating field: {e}")
        raise HTTPException(status_code=400, detail="Failed to update field")

@router.patch("/{field_id}/cell", tags=["Fields"])
async def update_field_cell(field_id: int, update_data: FieldCellUpdate, authorization: str = Header(None)):
    """
    UPDATE single cell in field - CELL-LEVEL UPDATE operation
    
    Args:
        field_id: Field ID
        update_data: Column name and value to update
        authorization: JWT token
    
    Returns:
        Success message
    """
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        
        # Extract user_id from token using helper
        user_id = extract_user_id(authorization)
        
        # Check permission
        user = RoleBasedAccessControl.check_permission(user_id, 'fields', 'update')
        
        # Check field exists
        field = FieldQueries.get_field_by_id(field_id)
        if not field:
            raise HTTPException(status_code=404, detail="Field not found")
        
        # Check access
        if user['role'] == 'farmer' and field['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Cannot update others' fields")
        
        # Allowed columns for update
        allowed_columns = ['field_name', 'area', 'soil_type', 'latitude', 'longitude', 'is_active']
        if update_data.column_name not in allowed_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot update column '{update_data.column_name}'. Allowed: {', '.join(allowed_columns)}"
            )
        
        # UPDATE single cell using DML
        FieldQueries.update_field_cell(
            field_id=field_id,
            column_name=update_data.column_name,
            value=update_data.value
        )
        
        logger.info(f"Field {field_id} cell updated: {update_data.column_name} by user {user_id}")

        return {
            "message": f"Field {update_data.column_name} updated successfully",
            "field_id": field_id,
            "column": update_data.column_name,
            "new_value": update_data.value
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating field cell: {e}")
        raise HTTPException(status_code=400, detail="Failed to update field")

@router.delete("/{field_id}", tags=["Fields"])
async def delete_field(field_id: int, authorization: str = Header(None)):
    """
    DELETE field - DELETE operation (soft delete) with RBAC
    
    Args:
        field_id: Field ID
        authorization: JWT token
    
    Returns:
        Success message
    """
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        
        # Extract user_id from token using helper
        user_id = extract_user_id(authorization)
        
        # Check permission
        user = RoleBasedAccessControl.check_permission(user_id, 'fields', 'delete')
        
        # Check field exists
        field = FieldQueries.get_field_by_id(field_id)
        if not field:
            raise HTTPException(status_code=404, detail="Field not found")
        
        # Check access
        if user['role'] == 'farmer' and field['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Cannot delete others' fields")
        
        # Agronomist cannot delete
        if user['role'] == 'agronomist':
            raise HTTPException(status_code=403, detail="Agronomists cannot delete fields")
        
        FieldQueries.delete_field(field_id)

        logger.info(f"Field {field_id} deleted by user {user_id}")

        return {"message": "Field deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting field: {e}")
        raise HTTPException(status_code=400, detail="Failed to delete field")

# ============ COMPLEX QUERY ROUTES (JOINs) ============

@router.get("/{field_id}/details", tags=["Fields - Analytics"])
async def get_field_details(field_id: int, authorization: str = Header(None)):
    """
    GET field with complete details using JOIN
    
    Includes: Field info + Farmer details + Region info
    
    Args:
        field_id: Field ID
        authorization: JWT token
    
    Returns:
        Field with details
    """
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        
        # Extract user_id from token using helper
        user_id = extract_user_id(authorization)
        
        # Check permission
        user = RoleBasedAccessControl.check_permission(user_id, 'fields', 'read')
        
        # JOIN query
        details = ComplexQueries.get_field_with_details(field_id)
        
        if not details:
            raise HTTPException(status_code=404, detail="Field not found")
        
        logger.info(f"Field details retrieved for field {field_id}")

        return {
            "message": "Field details retrieved",
            "data": details
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting field details: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve field details")

@router.get("/{field_id}/crops", tags=["Fields - Analytics"])
async def get_field_crops(field_id: int, authorization: str = Header(None)):
    """
    GET field with all crop cycles using LEFT JOIN
    
    Args:
        field_id: Field ID
        authorization: JWT token
    
    Returns:
        Field with associated crops
    """
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        
        # Extract user_id from token using helper
        user_id = extract_user_id(authorization)
        
        # Check permission
        user = RoleBasedAccessControl.check_permission(user_id, 'fields', 'read')
        
        # LEFT JOIN query
        field_crops = ComplexQueries.get_field_with_crops(field_id)
        
        if not field_crops:
            raise HTTPException(status_code=404, detail="Field not found")
        
        logger.info(f"Field crops retrieved for field {field_id}")

        return {
            "message": "Field crops retrieved",
            "data": field_crops
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting field crops: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve field crops")

@router.get("/region/{region_id}/all", tags=["Fields - Analytics"])
async def get_fields_by_region(region_id: int, authorization: str = Header(None)):
    """
    GET all fields in a region
    
    Args:
        region_id: Region ID
        authorization: JWT token
    
    Returns:
        Fields in region
    """
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        
        # Extract user_id from token using helper
        user_id = extract_user_id(authorization)
        
        # Check permission
        user = RoleBasedAccessControl.check_permission(user_id, 'fields', 'read')
        
        # Get all fields and filter
        all_fields = FieldQueries.get_all_fields()
        fields_in_region = [f for f in all_fields if f['region_id'] == region_id]
        
        # Farmer sees only own fields
        if user['role'] == 'farmer':
            fields_in_region = [f for f in fields_in_region if f['user_id'] == user_id]
        
        logger.info(f"Retrieved {len(fields_in_region)} fields from region {region_id}")

        return {
            "count": len(fields_in_region),
            "region_id": region_id,
            "fields": fields_in_region
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting fields by region: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve fields")