# routes/crop_cycles.py
# Crop cycles CRUD routes with raw DML queries, RBAC, and token extraction helper

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
import logging
from typing import Optional
from database.queries import CropCycleQueries, FieldQueries, ComplexQueries
from auth import RoleBasedAccessControl
from routes.helpers import extract_user_id

logger = logging.getLogger(__name__)
router = APIRouter()

# ============ PYDANTIC SCHEMAS ============

class CropCycleCreate(BaseModel):
    """Create crop cycle schema"""
    field_id: int
    crop_name: str
    start_date: str
    expected_harvest_date: str
    yield_prediction: float

class CropCycleUpdate(BaseModel):
    """Update crop cycle schema"""
    status: Optional[str] = None  # active, completed, abandoned
    actual_harvest_date: Optional[str] = None
    actual_yield: Optional[float] = None
from typing import Any 
class CropCycleCellUpdate(BaseModel):
    """Update single cell schema"""
    column_name: str
    value: Any

# ============ CROP CYCLE ROUTES ============

@router.get("/", tags=["Crop Cycles"])
async def get_all_crop_cycles(authorization: str = Header(None)):
    """
    GET all crop cycles - SELECT operation with RBAC
    
    Args:
        authorization: JWT token
    
    Returns:
        List of crop cycles based on user role
    """
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        
        # Extract user_id from token using helper
        user_id = extract_user_id(authorization)
        
        # Check permission
        user = RoleBasedAccessControl.check_permission(user_id, 'crop_cycles', 'read')
        
        # GET crop cycles based on role using DML
        if user['role'] == 'farmer':
            # Farmer sees only cycles from their fields
            all_cycles = CropCycleQueries.get_all_crop_cycles()
            user_fields = FieldQueries.get_fields_by_user(user_id)
            user_field_ids = [f['id'] for f in user_fields]
            cycles = [c for c in all_cycles if c['field_id'] in user_field_ids]
            visibility = "own field cycles only"
        else:
            # Agronomist and admin see all cycles
            cycles = CropCycleQueries.get_all_crop_cycles()
            visibility = "all cycles"
        
        logger.info(f"User {user_id} ({user['role']}) retrieved {len(cycles)} crop cycles")

        return {
            "count": len(cycles),
            "user_role": user['role'],
            "visibility": visibility,
            "crop_cycles": cycles
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting crop cycles: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve crop cycles")

@router.get("/{cycle_id}", tags=["Crop Cycles"])
async def get_crop_cycle_by_id(cycle_id: int, authorization: str = Header(None)):
    """
    GET crop cycle by ID - SELECT operation with RBAC
    
    Args:
        cycle_id: Crop cycle ID
        authorization: JWT token
    
    Returns:
        Crop cycle details
    """
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        
        # Extract user_id from token using helper
        user_id = extract_user_id(authorization)
        
        # Check permission
        user = RoleBasedAccessControl.check_permission(user_id, 'crop_cycles', 'read')
        
        # GET cycle using DML
        cycle = CropCycleQueries.get_crop_cycle_by_id(cycle_id)
        
        if not cycle:
            raise HTTPException(status_code=404, detail="Crop cycle not found")
        
        # Check access for farmer
        if user['role'] == 'farmer':
            field = FieldQueries.get_field_by_id(cycle['field_id'])
            if not field or field['user_id'] != user_id:
                raise HTTPException(status_code=403, detail="Access denied")
        
        logger.info(f"Crop cycle {cycle_id} retrieved by user {user_id}")

        return cycle

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting crop cycle: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve crop cycle")

@router.get("/field/{field_id}", tags=["Crop Cycles"])
async def get_cycles_by_field(field_id: int, authorization: str = Header(None)):
    """
    GET all cycles for a specific field - SELECT operation with RBAC
    
    Args:
        field_id: Field ID
        authorization: JWT token
    
    Returns:
        List of cycles in field
    """
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        
        # Extract user_id from token using helper
        user_id = extract_user_id(authorization)
        
        # Check permission
        user = RoleBasedAccessControl.check_permission(user_id, 'crop_cycles', 'read')
        
        # Check field exists
        field = FieldQueries.get_field_by_id(field_id)
        if not field:
            raise HTTPException(status_code=404, detail="Field not found")
        
        # Check access for farmer
        if user['role'] == 'farmer' and field['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # GET cycles for field using DML
        cycles = CropCycleQueries.get_cycles_by_field(field_id)
        
        logger.info(f"Retrieved {len(cycles)} cycles for field {field_id}")

        return {
            "field_name": field['field_name'],
            "field_id": field_id,
            "count": len(cycles),
            "crop_cycles": cycles
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cycles by field: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cycles")

@router.post("/", status_code=201, tags=["Crop Cycles"])
async def create_crop_cycle(cycle_data: CropCycleCreate, authorization: str = Header(None)):
    """
    CREATE new crop cycle - INSERT operation with RBAC
    
    Args:
        cycle_data: Crop cycle creation data
        authorization: JWT token
    
    Returns:
        Created crop cycle with 201 status
    """
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        
        # Extract user_id from token using helper
        user_id = extract_user_id(authorization)
        
        # Check permission
        user = RoleBasedAccessControl.check_permission(user_id, 'crop_cycles', 'create')
        
        # Verify field exists
        field = FieldQueries.get_field_by_id(cycle_data.field_id)
        if not field:
            raise HTTPException(status_code=404, detail="Field not found")
        
        # Check access for farmer
        if user['role'] == 'farmer' and field['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Cannot create cycle for others' field")
        
        # INSERT crop cycle using DML
        result = CropCycleQueries.create_crop_cycle(
            field_id=cycle_data.field_id,
            crop_name=cycle_data.crop_name,
            start_date=cycle_data.start_date,
            expected_harvest_date=cycle_data.expected_harvest_date,
            yield_prediction=cycle_data.yield_prediction
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create crop cycle")

        logger.info(f"Crop cycle created: {cycle_data.crop_name} in field {cycle_data.field_id}")

        return {
            "message": "Crop cycle created successfully",
            "cycle": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating crop cycle: {e}")
        raise HTTPException(status_code=400, detail="Failed to create crop cycle")

@router.put("/{cycle_id}", tags=["Crop Cycles"])
async def update_crop_cycle(cycle_id: int, cycle_data: CropCycleUpdate, authorization: str = Header(None)):
    """
    UPDATE crop cycle - UPDATE operation with RBAC
    
    Args:
        cycle_id: Crop cycle ID
        cycle_data: Update data
        authorization: JWT token
    
    Returns:
        Updated crop cycle details
    """
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        
        # Extract user_id from token using helper
        user_id = extract_user_id(authorization)
        
        # Check permission
        user = RoleBasedAccessControl.check_permission(user_id, 'crop_cycles', 'update')
        
        # Check cycle exists
        cycle = CropCycleQueries.get_crop_cycle_by_id(cycle_id)
        if not cycle:
            raise HTTPException(status_code=404, detail="Crop cycle not found")
        
        # Check access
        if user['role'] == 'farmer':
            field = FieldQueries.get_field_by_id(cycle['field_id'])
            if not field or field['user_id'] != user_id:
                raise HTTPException(status_code=403, detail="Cannot update others' cycles")
        
        # UPDATE crop cycle using DML
        CropCycleQueries.update_crop_cycle(
            cycle_id=cycle_id,
            status=cycle_data.status,
            actual_harvest_date=cycle_data.actual_harvest_date,
            actual_yield=cycle_data.actual_yield
        )
        
        updated_cycle = CropCycleQueries.get_crop_cycle_by_id(cycle_id)

        logger.info(f"Crop cycle {cycle_id} updated by user {user_id}")

        return {
            "message": "Crop cycle updated successfully",
            "cycle": updated_cycle
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating crop cycle: {e}")
        raise HTTPException(status_code=400, detail="Failed to update crop cycle")

@router.patch("/{cycle_id}/cell", tags=["Crop Cycles"])
async def update_cycle_cell(cycle_id: int, update_data: CropCycleCellUpdate, authorization: str = Header(None)):
    """
    UPDATE single cell in crop cycle - CELL-LEVEL UPDATE operation
    
    Args:
        cycle_id: Crop cycle ID
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
        user = RoleBasedAccessControl.check_permission(user_id, 'crop_cycles', 'update')
        
        # Check cycle exists
        cycle = CropCycleQueries.get_crop_cycle_by_id(cycle_id)
        if not cycle:
            raise HTTPException(status_code=404, detail="Crop cycle not found")
        
        # Check access
        if user['role'] == 'farmer':
            field = FieldQueries.get_field_by_id(cycle['field_id'])
            if not field or field['user_id'] != user_id:
                raise HTTPException(status_code=403, detail="Cannot update others' cycles")
        
        # Allowed columns
        allowed_columns = ['crop_name', 'start_date', 'expected_harvest_date', 
                          'actual_harvest_date', 'status', 'yield_prediction', 'actual_yield']
        if update_data.column_name not in allowed_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot update column. Allowed: {', '.join(allowed_columns)}"
            )
        
        # UPDATE single cell using DML
        CropCycleQueries.update_crop_cycle_cell(
            cycle_id=cycle_id,
            column_name=update_data.column_name,
            value=update_data.value
        )
        
        logger.info(f"Crop cycle {cycle_id} cell updated: {update_data.column_name}")

        return {
            "message": f"Crop cycle {update_data.column_name} updated successfully",
            "cycle_id": cycle_id,
            "column": update_data.column_name,
            "new_value": update_data.value
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating cycle cell: {e}")
        raise HTTPException(status_code=400, detail="Failed to update crop cycle")

@router.delete("/{cycle_id}", tags=["Crop Cycles"])
async def delete_crop_cycle(cycle_id: int, authorization: str = Header(None)):
    """
    DELETE crop cycle - DELETE operation with RBAC
    
    Args:
        cycle_id: Crop cycle ID
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
        user = RoleBasedAccessControl.check_permission(user_id, 'crop_cycles', 'delete')
        
        # Check cycle exists
        cycle = CropCycleQueries.get_crop_cycle_by_id(cycle_id)
        if not cycle:
            raise HTTPException(status_code=404, detail="Crop cycle not found")
        
        # Check access
        if user['role'] == 'agronomist':
            raise HTTPException(status_code=403, detail="Agronomists cannot delete cycles")
        
        if user['role'] == 'farmer':
            field = FieldQueries.get_field_by_id(cycle['field_id'])
            if not field or field['user_id'] != user_id:
                raise HTTPException(status_code=403, detail="Cannot delete others' cycles")
        
        CropCycleQueries.delete_crop_cycle(cycle_id)

        logger.info(f"Crop cycle {cycle_id} deleted by user {user_id}")

        return {"message": "Crop cycle deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting crop cycle: {e}")
        raise HTTPException(status_code=400, detail="Failed to delete crop cycle")

# ============ COMPLEX QUERY ROUTES (JOINs & GROUP BY) ============

@router.get("/analytics/active", tags=["Crop Cycles - Analytics"])
async def get_active_cycles(authorization: str = Header(None)):
    """
    GET all active crop cycles - SELECT with WHERE clause
    
    Args:
        authorization: JWT token
    
    Returns:
        Active crop cycles
    """
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        
        # Extract user_id from token using helper
        user_id = extract_user_id(authorization)
        
        # Check permission
        user = RoleBasedAccessControl.check_permission(user_id, 'crop_cycles', 'read')
        
        # GET active cycles
        if user['role'] == 'farmer':
            all_active = CropCycleQueries.get_active_cycles()
            user_fields = FieldQueries.get_fields_by_user(user_id)
            user_field_ids = [f['id'] for f in user_fields]
            cycles = [c for c in all_active if c['field_id'] in user_field_ids]
        else:
            cycles = CropCycleQueries.get_active_cycles()
        
        logger.info(f"Retrieved {len(cycles)} active crop cycles")

        return {
            "count": len(cycles),
            "status": "active",
            "crop_cycles": cycles
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting active cycles: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cycles")

@router.get("/analytics/yield-analysis", tags=["Crop Cycles - Analytics"])
async def get_yield_analysis(authorization: str = Header(None)):
    """
    GET crop yield analysis using GROUP BY + AGGREGATION
    
    Args:
        authorization: JWT token
    
    Returns:
        Yield statistics by crop
    """
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        
        # Extract user_id from token using helper
        user_id = extract_user_id(authorization)
        
        # Check permission
        user = RoleBasedAccessControl.check_permission(user_id, 'crop_cycles', 'read')
        
        # GROUP BY + AGGREGATION query
        analysis = ComplexQueries.get_crop_yield_analysis()
        
        logger.info("Crop yield analysis retrieved")

        return {
            "message": "Crop yield analysis",
            "data": analysis,
            "total_crops": len(analysis)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting yield analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analysis")