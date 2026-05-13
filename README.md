# README: HarvestHUB
## Complete Execution Guide + Frontend + Reports

---

## TABLE OF CONTENTS

1. [Quick Start](#quick-start)
2. [System Requirements](#system-requirements)
3. [Installation Steps](#installation-steps)
4. [Running the Software](#running-the-software)
5. [API Documentation](#api-documentation)
6. [Frontend Integration](#frontend-integration)
7. [Report Generation](#report-generation)
8. [Troubleshooting](#troubleshooting)

---

## QUICK START

**For impatient people - 10 minutes to running API:**

```bash
# 1. Clone/Download project

# 2. Install Python dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary bcrypt python-jose python-dotenv

# 3. Create .env file
cat > .env << EOF
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=cropdb
SECRET_KEY=your-secret-key-change-in-production
EOF

# 4. Create PostgreSQL database
psql -U postgres -c "CREATE DATABASE cropdb;"

# 5. Run DDL (create tables)
psql -U postgres -d cropdb < database/ddl.sql

# 6. Run seed data
psql -U postgres -d cropdb < database/seed_data.sql

# 7. Start API
python main.py

# 8. Open browser
http://localhost:5000/docs
```

Done! API is running. 🚀

---

## SYSTEM REQUIREMENTS

### Software Requirements
- **Python**: 3.8+
- **PostgreSQL**: 12+
- **pip**: Package manager

### Hardware Requirements
- **RAM**: 1GB minimum
- **Disk**: 100MB for database + code
- **CPU**: Any modern processor

### Optional (for frontend)
- **Node.js**: 14+ (for React/Vue development)
- **npm**: Latest version

---

## INSTALLATION STEPS

### Step 1: Install PostgreSQL

**Windows:**
```
Download from: https://www.postgresql.org/download/windows/
Use installer, remember password
```

**Mac:**
```bash
brew install postgresql@14
brew services start postgresql@14
```

**Linux (Ubuntu):**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo service postgresql start
```

### Step 2: Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# In psql shell, run:
CREATE DATABASE cropdb;
\q
```

### Step 3: Install Python Dependencies

```bash
# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

**requirements.txt content:**
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
bcrypt==4.1.1
python-jose[cryptography]==3.3.0
python-dotenv==1.0.0
pydantic==2.5.0
```

### Step 4: Create .env File

```bash
# In project root directory
cat > .env << EOF
# Database Configuration
DB_USER=postgres
DB_PASSWORD=your_postgres_password_here
DB_HOST=localhost
DB_PORT=5432
DB_NAME=cropdb

# Security
SECRET_KEY=super-secret-key-change-in-production
ALGORITHM=HS256

# Debug (set to False in production)
DEBUG=False
EOF
```

**Replace `your_postgres_password_here` with your actual password!**

### Step 5: Create Database Schema

```bash
# Run DDL to create all tables
psql -U postgres -d cropdb -f database/ddl.sql

# Run seed data to populate initial records
psql -U postgres -d cropdb -f database/seed_data.sql

# Verify
psql -U postgres -d cropdb -c "\dt"
# Should show: users, regions, fields, satellites, crop_cycles, observations, band_values, weather_records, derived_metrics, alerts
```

### Step 6: Project Structure

Your project should look like this:

```
DBMS/
├── database/
│   ├── __init__.py
│   ├── database.py           ← Connection pooling
│   ├── queries.py            ← All DML operations
│   ├── ddl.sql               ← Table creation (run in PgAdmin)
│   └── seed_data.sql         ← Initial data (run in PgAdmin)
├── routes/
│   ├── __init__.py
│   ├── helpers.py            ← Token extraction helper
│   ├── auth.py               ← Login/Register
│   ├── fields.py             ← Field CRUD + analytics
│   ├── crop_cycles.py        ← Crop CRUD + analytics
│   ├── users.py              ← User management
│   ├── alerts.py             ← Alert management (optional)
│   └── analytics.py          ← Reports + dashboards (optional)
├── auth.py                   ← RBAC + password hashing
├── schemas.py                ← Pydantic models
├── main.py                   ← FastAPI app
├── .env                       ← Environment variables
├── requirements.txt           ← Python dependencies
└── README.md                  ← This file
```

---

## RUNNING THE SOFTWARE

### Step 1: Activate Virtual Environment (Optional)

```bash
# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### Step 2: Start the API Server

```bash
python main.py
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:5000
INFO:     Application startup complete
```

### Step 3: Access the API

**Swagger UI (Interactive API Documentation):**
```
Browser: http://localhost:5000/docs
```

**Alternative: ReDoc**
```
Browser: http://localhost:5000/redoc
```

### Step 4: Test First Endpoint

**In Swagger UI:**
1. Click "POST /api/auth/register"
2. Click "Try it out"
3. Enter:
   ```json
   {
     "name": "Test User",
     "email": "test@example.com",
     "password": "test123",
     "role": "farmer"
   }
   ```
4. Click "Execute"
5. Should see: 201 Created

**Or via curl:**
```bash
curl -X POST "http://localhost:5000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "test123",
    "role": "farmer"
  }'
```

---

## API DOCUMENTATION

### Authentication Endpoints

**1. Register User**
```
POST /api/auth/register
Body: {
  "name": "Ali",
  "email": "ali@test.com",
  "password": "test123",
  "role": "farmer"
}
Response: 201 Created
```

**2. Login User**
```
POST /api/auth/login
Body: {
  "email": "ali@test.com",
  "password": "test123"
}
Response: 200 OK
{
  "access_token": "eyJhbGc...",
  "token_type": "Bearer",
  "user": {
    "user_id": 1,
    "email": "ali@test.com",
    "role": "farmer"
  }
}
```

**3. Get Current User**
```
GET /api/auth/me
Headers: Authorization: Bearer {token}
Response: 200 OK
{
  "user": {
    "user_id": 1,
    "name": "Ali",
    "email": "ali@test.com",
    "role": "farmer"
  }
}
```

### Fields Endpoints

**Get All Fields**
```
GET /api/fields/
Headers: Authorization: Bearer {token}
Response: 200 OK
{
  "count": 8,
  "user_role": "farmer",
  "fields": [...]
}
```

**Get Field Details (with JOIN)**
```
GET /api/fields/1/details
Headers: Authorization: Bearer {token}
Response: 200 OK
{
  "field_id": 1,
  "field_name": "North Field",
  "farmer_name": "Ali",
  "region": "Punjab",
  "climate": "Subtropical"
}
```

**Create Field**
```
POST /api/fields/
Headers: Authorization: Bearer {token}
Body: {
  "field_name": "West Field",
  "user_id": 1,
  "region_id": 1,
  "latitude": 31.5,
  "longitude": 74.3,
  "area": 50.0,
  "soil_type": "Loamy"
}
Response: 201 Created
```

**Update Field Cell (Single Column)**
```
PATCH /api/fields/1/cell
Headers: Authorization: Bearer {token}
Body: {
  "column_name": "area",
  "value": 75.0
}
Response: 200 OK
```

**Delete Field**
```
DELETE /api/fields/1
Headers: Authorization: Bearer {token}
Response: 200 OK
```

### Crop Cycles Endpoints

**Get All Crop Cycles**
```
GET /api/crop-cycles/
Headers: Authorization: Bearer {token}
```

**Create Crop Cycle**
```
POST /api/crop-cycles/
Headers: Authorization: Bearer {token}
Body: {
  "field_id": 1,
  "crop_name": "Wheat",
  "start_date": "2024-03-01",
  "expected_harvest_date": "2024-06-30",
  "yield_prediction": 45.5
}
Response: 201 Created
```

**Get Yield Analysis (GROUP BY)**
```
GET /api/crop-cycles/analytics/yield-analysis
Headers: Authorization: Bearer {token}
Response: 200 OK
{
  "data": [
    {
      "crop_name": "Wheat",
      "total_cycles": 3,
      "average_yield": 45.0,
      "best_yield": 48.0,
      "worst_yield": 42.0
    },
    ...
  ]
}
```

### Analytics Endpoints (If created)

**Field Health Dashboard (7-table JOIN)**
```
GET /api/analytics/dashboard/health
Headers: Authorization: Bearer {token}
Response: 200 OK
{
  "data": [
    {
      "field_id": 1,
      "field_name": "North Field",
      "farmer_name": "Ali",
      "current_crop": "Wheat",
      "health_score": 85.0,
      "active_alerts": 1
    }
  ]
}
```

**Farmer Performance Metrics**
```
GET /api/analytics/farmer-performance
Headers: Authorization: Bearer {token}
Response: 200 OK
{
  "data": [
    {
      "farmer_id": 1,
      "farmer_name": "Ali",
      "total_fields": 3,
      "avg_yield": 45.2,
      "active_cycles": 2
    }
  ]
}
```

### Report Endpoints

**Get Field Report Data**
```
GET /api/reports/field/1
Headers: Authorization: Bearer {token}
Response: 200 OK
{
  "report": {
    "field_name": "North Field",
    "farmer_name": "Ali",
    "region": "Punjab",
    "total_cycles": 5,
    "average_yield": 45.2,
    "total_alerts": 2
  }
}
```

---

## FRONTEND INTEGRATION

### Is It Easy to Add Frontend?

**YES! Very easy! Here's why:**

✅ **RESTful API**: Standard HTTP requests
✅ **JSON Responses**: Easy to parse
✅ **Swagger UI**: Auto-generated API docs
✅ **CORS Support**: Can add easily (see below)
✅ **JWT Auth**: Standard token-based auth
✅ **Clear Endpoints**: Consistent naming

**Difficulty: EASY ⭐⭐**

### Step 1: Enable CORS in main.py

Add this to your main.py:

```python
from fastapi.middleware.cors import CORSMiddleware

# After app = FastAPI() line, add:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Step 2: React Frontend Example

**Install React:**
```bash
npx create-react-app crop-dbms-frontend
cd crop-dbms-frontend
npm install axios
npm start
```

**Create API Service (api.js):**

```javascript
import axios from 'axios';

const API_URL = 'http://localhost:5000/api';

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// API Functions
export const authAPI = {
  register: (name, email, password, role) =>
    api.post('/auth/register', { name, email, password, role }),
  
  login: (email, password) =>
    api.post('/auth/login', { email, password }),
  
  getMe: () => api.get('/auth/me'),
};

export const fieldsAPI = {
  getAll: () => api.get('/fields/'),
  
  getById: (id) => api.get(`/fields/${id}`),
  
  getDetails: (id) => api.get(`/fields/${id}/details`),
  
  create: (fieldData) => api.post('/fields/', fieldData),
  
  update: (id, fieldData) => api.put(`/fields/${id}`, fieldData),
  
  updateCell: (id, columnName, value) =>
    api.patch(`/fields/${id}/cell`, { column_name: columnName, value }),
  
  delete: (id) => api.delete(`/fields/${id}`),
};

export const cropsAPI = {
  getAll: () => api.get('/crop-cycles/'),
  
  getById: (id) => api.get(`/crop-cycles/${id}`),
  
  create: (cropData) => api.post('/crop-cycles/', cropData),
  
  update: (id, cropData) => api.put(`/crop-cycles/${id}`, cropData),
  
  updateCell: (id, columnName, value) =>
    api.patch(`/crop-cycles/${id}/cell`, { column_name: columnName, value }),
  
  delete: (id) => api.delete(`/crop-cycles/${id}`),
  
  getYieldAnalysis: () => api.get('/crop-cycles/analytics/yield-analysis'),
};

export const reportsAPI = {
  getFieldReport: (id) => api.get(`/reports/field/${id}`),
  
  getSeasonalYield: () => api.get('/reports/seasonal-yield'),
  
  getHealthSummary: () => api.get('/reports/health-summary'),
};

export default api;
```

**Create Login Component (Login.jsx):**

```javascript
import { useState } from 'react';
import { authAPI } from '../api';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await authAPI.login(email, password);
      localStorage.setItem('token', response.data.access_token);
      window.location.href = '/dashboard';
    } catch (err) {
      setError('Login failed: ' + err.response.data.detail);
    }
  };

  return (
    <div className="login-container">
      <h1>HarvestHUB</h1>
      <form onSubmit={handleSubmit}>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <button type="submit">Login</button>
        {error && <p className="error">{error}</p>}
      </form>
    </div>
  );
}
```

**Create Fields Dashboard (FieldsDashboard.jsx):**

```javascript
import { useState, useEffect } from 'react';
import { fieldsAPI } from '../api';

export default function FieldsDashboard() {
  const [fields, setFields] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fieldsAPI
      .getAll()
      .then((response) => {
        setFields(response.data.fields);
        setLoading(false);
      })
      .catch((error) => {
        console.error('Error fetching fields:', error);
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <div className="fields-dashboard">
      <h1>My Fields</h1>
      <table>
        <thead>
          <tr>
            <th>Field Name</th>
            <th>Area</th>
            <th>Soil Type</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {fields.map((field) => (
            <tr key={field.id}>
              <td>{field.field_name}</td>
              <td>{field.area}</td>
              <td>{field.soil_type}</td>
              <td>
                <button onClick={() => viewField(field.id)}>View</button>
                <button onClick={() => editField(field.id)}>Edit</button>
                <button onClick={() => deleteField(field.id)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

### Step 3: Vue.js Frontend Alternative

If you prefer Vue.js:

```bash
npm create vite@latest crop-dbms -- --template vue
cd crop-dbms
npm install axios
```

**Vue API Service (api.js):**
```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5000/api'
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
```

### Step 4: Mobile Frontend (React Native / Flutter)

Same API endpoints work for mobile!

**React Native Example:**
```javascript
import axios from 'axios';

const loginUser = async (email, password) => {
  try {
    const response = await axios.post(
      'http://your-server:5000/api/auth/login',
      { email, password }
    );
    await AsyncStorage.setItem('token', response.data.access_token);
    return response.data;
  } catch (error) {
    console.error('Login error:', error);
  }
};
```

---

## REPORT GENERATION

### Is It Easy to Add Report Generation?

**YES! Very easy! Here's why:**

✅ **Pre-built Report Queries**: ReportQueries class ready
✅ **JSON Data**: Already structured for reports
✅ **Multiple Formats**: PDF, Excel, Charts all possible
✅ **Existing Endpoints**: /api/reports/* already created

**Difficulty: MEDIUM ⭐⭐⭐**

### Step 1: Install Report Libraries

```bash
pip install reportlab openpyxl matplotlib pandas
```

### Step 2: Create Report Generator Module

Create `reports/generator.py`:

```python
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from database.queries import ReportQueries
import io
from datetime import datetime

class ReportGenerator:
    """Generate PDF and Excel reports from database queries"""
    
    @staticmethod
    def generate_field_pdf(field_id):
        """Generate PDF report for a field"""
        # Get report data
        report_data = ReportQueries.get_field_report_data(field_id)
        
        # Create PDF
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            title=f"Field Report: {report_data['field_name']}"
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title = Paragraph(
            f"<b>Field Report: {report_data['field_name']}</b>",
            styles['Title']
        )
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Field Information
        field_data = [
            ['Field Name', report_data['field_name']],
            ['Farmer', report_data['farmer_name']],
            ['Region', report_data['region']],
            ['Area (ha)', str(report_data['area'])],
            ['Soil Type', report_data['soil_type']],
        ]
        
        field_table = Table(field_data)
        field_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(field_table)
        elements.append(Spacer(1, 12))
        
        # Crop Cycles Summary
        summary_data = [
            ['Metric', 'Value'],
            ['Total Cycles', str(report_data['total_cycles'])],
            ['Average Yield', f"{report_data['average_yield']:.2f} tons"],
            ['Total Alerts', str(report_data['total_alerts'])],
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(summary_table)
        
        # Footer
        elements.append(Spacer(1, 12))
        footer = Paragraph(
            f"<i>Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>",
            styles['Normal']
        )
        elements.append(footer)
        
        # Build PDF
        doc.build(elements)
        
        pdf_buffer.seek(0)
        return pdf_buffer
    
    @staticmethod
    def generate_yield_excel():
        """Generate Excel report for seasonal yields"""
        # Get report data
        yield_data = ReportQueries.get_seasonal_yield_report()
        
        # Create Excel
        wb = Workbook()
        ws = wb.active
        ws.title = "Seasonal Yield"
        
        # Headers
        headers = ['Crop', 'Season', 'Count', 'Average Yield', 'Total Yield']
        ws.append(headers)
        
        # Style headers
        for cell in ws[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        
        # Add data
        for row in yield_data:
            ws.append([
                row['crop'],
                f"Q{row['season']}",
                row['count'],
                f"{row['average_yield']:.2f}",
                f"{row['total_yield']:.2f}"
            ])
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 15
        ws.column_dimensions['B'].width = 10
        ws.column_dimensions['C'].width = 10
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 15
        
        # Save to buffer
        excel_buffer = io.BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)
        
        return excel_buffer
    
    @staticmethod
    def generate_health_summary():
        """Generate health summary visualization"""
        import matplotlib.pyplot as plt
        
        # Get data
        health_data = ReportQueries.get_health_summary_report()
        
        # Create figure
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        
        # Chart 1: Total Fields
        ax1.bar(['Fields'], [health_data['total_fields']], color='green')
        ax1.set_title('Total Active Fields')
        ax1.set_ylabel('Count')
        
        # Chart 2: Total Farmers
        ax2.bar(['Farmers'], [health_data['total_farmers']], color='blue')
        ax2.set_title('Total Active Farmers')
        ax2.set_ylabel('Count')
        
        # Chart 3: Average Health Score
        ax3.bar(['Health'], [health_data['average_health_score']], color='orange')
        ax3.set_ylim([0, 100])
        ax3.set_title('Average Crop Health Score')
        ax3.set_ylabel('Score')
        
        # Chart 4: Alerts
        alerts = [health_data['high_severity_alerts'], health_data['unresolved_alerts']]
        ax4.bar(['High', 'Unresolved'], alerts, color=['red', 'yellow'])
        ax4.set_title('Alert Summary')
        ax4.set_ylabel('Count')
        
        plt.tight_layout()
        
        # Save to buffer
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)
        
        return img_buffer
```

### Step 3: Add Report Endpoints

Add to `routes/reports.py`:

```python
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import FileResponse, StreamingResponse
from reports.generator import ReportGenerator
from database.queries import ReportQueries
from auth import RoleBasedAccessControl
from routes.helpers import extract_user_id
import io

router = APIRouter()

@router.get("/field/{field_id}/pdf", tags=["Reports"])
async def get_field_pdf(field_id: int, authorization: str = Header(None)):
    """Download field report as PDF"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        user_id = extract_user_id(authorization)
        user = RoleBasedAccessControl.check_permission(user_id, 'fields', 'read')
        
        # Generate PDF
        pdf_buffer = ReportGenerator.generate_field_pdf(field_id)
        
        return StreamingResponse(
            iter([pdf_buffer.getvalue()]),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=field_report.pdf"}
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        return {"error": str(e)}, 500

@router.get("/yield/excel", tags=["Reports"])
async def get_yield_excel(authorization: str = Header(None)):
    """Download yield analysis as Excel"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        user_id = extract_user_id(authorization)
        user = RoleBasedAccessControl.check_permission(user_id, 'crop_cycles', 'read')
        
        # Generate Excel
        excel_buffer = ReportGenerator.generate_yield_excel()
        
        return StreamingResponse(
            iter([excel_buffer.getvalue()]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=yield_analysis.xlsx"}
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        return {"error": str(e)}, 500

@router.get("/health/image", tags=["Reports"])
async def get_health_image(authorization: str = Header(None)):
    """Get health summary as image"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        user_id = extract_user_id(authorization)
        user = RoleBasedAccessControl.check_permission(user_id, 'fields', 'read')
        
        # Generate image
        img_buffer = ReportGenerator.generate_health_summary()
        
        return StreamingResponse(
            iter([img_buffer.getvalue()]),
            media_type="image/png"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        return {"error": str(e)}, 500
```

### Step 4: Add Report Routes to main.py

```python
from routes.reports import router as reports_router

# Include router
app.include_router(reports_router, prefix="/api/reports-download", tags=["Reports"])
```

### Step 5: Frontend Integration

```javascript
// Download PDF Report
const downloadFieldPDF = async (fieldId) => {
  try {
    const response = await axios.get(`/api/reports-download/field/${fieldId}/pdf`, {
      responseType: 'blob',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    // Create download link
    const url = window.URL.createObjectURL(response.data);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `field_${fieldId}_report.pdf`);
    document.body.appendChild(link);
    link.click();
  } catch (error) {
    console.error('Download failed:', error);
  }
};

// Download Excel Report
const downloadYieldExcel = async () => {
  try {
    const response = await axios.get('/api/reports-download/yield/excel', {
      responseType: 'blob',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    const url = window.URL.createObjectURL(response.data);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'yield_analysis.xlsx');
    document.body.appendChild(link);
    link.click();
  } catch (error) {
    console.error('Download failed:', error);
  }
};
```

---

## TROUBLESHOOTING

### Problem: "Connection refused" or "PostgreSQL not running"

**Solution:**
```bash
# Check if PostgreSQL is running
# Linux:
sudo service postgresql status
sudo service postgresql start

# Mac:
brew services list
brew services start postgresql@14

# Windows:
# Use Windows Services manager or PostgreSQL installer
```

### Problem: "Database does not exist"

**Solution:**
```bash
# Create database
createdb -U postgres cropdb

# Or in psql:
psql -U postgres
CREATE DATABASE cropdb;
\q
```

### Problem: "Table does not exist"

**Solution:**
```bash
# Run DDL to create tables
psql -U postgres -d cropdb -f database/ddl.sql

# Verify:
psql -U postgres -d cropdb -c "\dt"
```

### Problem: "Invalid credentials" on login

**Solution:**
1. Check .env file has correct DB_PASSWORD
2. Verify PostgreSQL user password
3. Check DB_USER is correct

### Problem: "401 Unauthorized" on API calls

**Solution:**
1. Make sure you're passing Authorization header
2. Token format: `Authorization: Bearer {token}`
3. Token might be expired (lasts 24 hours)
4. Get new token by logging in again

### Problem: "403 Forbidden" on API calls

**Solution:**
1. You don't have permission for that action
2. Check your user role (farmer, agronomist, admin)
3. Farmers can only access their own data
4. Agronomists cannot delete anything
5. Only admins can manage other users

### Problem: "CORS Error" when calling from frontend

**Solution:**
Add CORS middleware to main.py (see Frontend Integration section)

---

## DEPLOYMENT

### Simple Deployment to Cloud

**Heroku:**
```bash
# Install Heroku CLI
# Login
heroku login

# Create app
heroku create your-app-name

# Add PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Deploy
git push heroku main

# Check logs
heroku logs --tail
```

**AWS/Digital Ocean:**
```bash
# Create EC2/Droplet with Ubuntu
# Install Python, PostgreSQL
# Clone repository
# Run: python main.py
# Use Nginx as reverse proxy
```

---

## QUICK REFERENCE

### Important Endpoints

```
POST   /api/auth/register          - Create new user
POST   /api/auth/login             - Get JWT token
GET    /api/auth/me                - Get current user

GET    /api/fields/                - List all fields
POST   /api/fields/                - Create field
GET    /api/fields/{id}            - Get field
PUT    /api/fields/{id}            - Update field
PATCH  /api/fields/{id}/cell       - Update cell
DELETE /api/fields/{id}            - Delete field
GET    /api/fields/{id}/details    - Field + farmer + region (JOIN)
GET    /api/fields/{id}/crops      - Field + crops (LEFT JOIN)

GET    /api/crop-cycles/           - List cycles
POST   /api/crop-cycles/           - Create cycle
GET    /api/crop-cycles/{id}       - Get cycle
PUT    /api/crop-cycles/{id}       - Update cycle
PATCH  /api/crop-cycles/{id}/cell  - Update cell
DELETE /api/crop-cycles/{id}       - Delete cycle
GET    /api/crop-cycles/analytics/yield-analysis  - GROUP BY query

GET    /api/reports/field/{id}     - Field report data
GET    /api/reports/seasonal-yield - Seasonal analysis
GET    /api/reports/health-summary - Health metrics

GET    /api/analytics/dashboard/health        - Health dashboard
GET    /api/analytics/farmer-performance     - Farmer metrics
GET    /api/analytics/weather-trends         - Weather analysis
```

### Default Test Credentials

Use these to test after seeding database:

```
Email:    ali@farm.com
Password: (Use the hash from seed_data.sql to set a password)

Or register a new user:
POST /api/auth/register
{
  "name": "Test",
  "email": "test@test.com",
  "password": "test123",
  "role": "farmer"
}
```

---

## NEXT STEPS

1. ✅ Follow installation steps
2. ✅ Run the software
3. ✅ Test API endpoints in Swagger UI
4. ✅ Add React/Vue frontend
5. ✅ Integrate report generation
6. ✅ Deploy to cloud

---

## SUPPORT

### Common Resources

- **API Docs**: http://localhost:5000/docs
- **PostgreSQL Docs**: https://www.postgresql.org/docs/
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **React Docs**: https://react.dev/
- **ReportLab Docs**: https://www.reportlab.com/docs/reportlab-userguide.pdf

### Issues?

Check the **Troubleshooting** section above or:
1. Check logs: `python main.py` output
2. Check database: `psql -U postgres -d cropdb -c "SELECT * FROM users;"`
3. Check .env file
4. Check API in Swagger UI

---

## LICENSE & CREDITS

Built with:
- **FastAPI**: Modern Python web framework
- **PostgreSQL**: Open source database
- **SQLAlchemy**: Python ORM/SQL toolkit
- **bcrypt**: Secure password hashing
- **python-jose**: JWT token handling

---

**Ready to manage crops like a pro! 🚀**

Last Updated: 2024