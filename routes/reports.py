from fastapi import APIRouter, Header, HTTPException
from starlette.responses import StreamingResponse
from database.queries import ComplexQueries, FieldQueries, RegionQueries, ReportQueries
from auth import RoleBasedAccessControl
from routes.helpers import extract_user_id
import csv
import io

router = APIRouter()


def _require_user(authorization: str, resource: str = "fields", action: str = "read"):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    user_id = extract_user_id(authorization)
    user = RoleBasedAccessControl.check_permission(user_id, resource, action)
    return user_id, user


@router.get("/analytics/dashboard/health")
def get_health_dashboard(authorization: str = Header(None)):
    user_id, user = _require_user(authorization, "fields", "read")
    data = ComplexQueries.get_field_health_dashboard()
    if user["role"] == "farmer":
        user_fields = {field["id"] for field in FieldQueries.get_fields_by_user(user_id)}
        data = [row for row in data if row["field_id"] in user_fields]
    return {"count": len(data), "data": data}


@router.get("/analytics/farmer-performance")
def get_farmer_performance(authorization: str = Header(None)):
    user_id, user = _require_user(authorization, "users", "read")
    data = ComplexQueries.get_farmer_performance()
    if user["role"] == "farmer":
        data = [row for row in data if row["farmer_id"] == user_id]
    return {"count": len(data), "data": data}


@router.get("/analytics/weather-trends")
def get_weather_trends(authorization: str = Header(None)):
    user_id, user = _require_user(authorization, "weather", "read")
    data = ComplexQueries.get_region_weather_trends()
    if user["role"] == "farmer":
        user_fields = FieldQueries.get_fields_by_user(user_id)
        region_ids = {field["region_id"] for field in user_fields}
        region_names = {
            region["region_name"]
            for region in (RegionQueries.get_region_by_id(region_id) for region_id in region_ids)
            if region
        }
        data = [row for row in data if row["region"] in region_names]
    return {"count": len(data), "data": data}


@router.get("/reports/field/{field_id}")
def get_field_report(field_id: int, authorization: str = Header(None)):
    user_id, user = _require_user(authorization, "fields", "read")
    field = FieldQueries.get_field_by_id(field_id)
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    if user["role"] == "farmer" and field["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    report = ReportQueries.get_field_report_data(field_id)
    return {"report": report}

@router.get("/export/farmer-report")
def export_farmer_report():
    # 1. ComplexQueries se data fetch karo
    data = ComplexQueries.get_farmer_performance()

    # 2. Safety check: Agar data None ya khali hai, toh crash se bachne ke liye message return karo
    if data is None:
        return {"status": "error", "message": "No data found in database or query failed."}
    
    # 3. CSV file in-memory prepare karo
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header: Jo tumhare dictionary keys hain
    writer.writerow(['Farmer ID', 'Name', 'Email', 'Total Fields', 'Total Cycles', 'Avg Yield', 'Active Cycles', 'High Alerts'])

    # 4. Data Rows
    for row in data:
        # .get() use kar rahe hain taake agar koi field miss ho toh code crash na ho
        writer.writerow([
            row.get('farmer_id'), 
            row.get('farmer_name'), 
            row.get('email'), 
            row.get('total_fields'), 
            row.get('total_cycles'), 
            row.get('avg_yield'), 
            row.get('active_cycles'), 
            row.get('high_alerts')
        ])

    output.seek(0)
    
    # 5. Download response return karo
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=farmer_report.csv"}
    )