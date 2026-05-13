# database/queries.py
# Complete DML operations for all 10 tables with cell-level updates and JOIN queries

from database.database import SessionLocal
from sqlalchemy import text
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ============ USER QUERIES (TABLE 1) ============
class UserQueries:
    """Complete CRUD operations for users table"""
    
    @staticmethod
    def create_user(name, email, password_hash, role):
        """INSERT new user"""
        db = SessionLocal()
        try:
            query = text("""
                INSERT INTO users (name, email, password_hash, role, is_active, avatar_url)
                VALUES (:name, :email, :password_hash, :role, TRUE, NULL)
                RETURNING user_id, name, email, role, avatar_url, created_at
            """)
            result = db.execute(query, {
                "name": name,
                "email": email,
                "password_hash": password_hash,
                "role": role
            })
            db.commit()
            row = result.fetchone()
            return {
                "user_id": row[0],
                "name": row[1],
                "email": row[2],
                "role": row[3],
                "avatar_url": row[4],
                "created_at": row[5],
            } if row else None
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating user: {e}")
            raise
        finally:
            db.close()
    
    @staticmethod
    def get_user_by_email(email):
        """SELECT user by email"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT user_id, name, email, password_hash, role, is_active, avatar_url, created_at
                FROM users
                WHERE email = :email
            """)
            result = db.execute(query, {"email": email})
            row = result.fetchone()
            return {
                "user_id": row[0], 
                "name": row[1],
                "email": row[2], 
                "password_hash": row[3], 
                "role": row[4],
                "is_active": row[5],
                "avatar_url": row[6],
                "created_at": row[7]
            } if row else None
        finally:
            db.close()
    
    @staticmethod
    def get_user_by_id(user_id):
        """SELECT user by ID"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT user_id, name, email, role, is_active, avatar_url, created_at
                FROM users
                WHERE user_id = :user_id
            """)
            result = db.execute(query, {"user_id": user_id})
            row = result.fetchone()
            return {
                "user_id": row[0],
                "name": row[1],
                "email": row[2],
                "role": row[3],
                "is_active": row[4],
                "avatar_url": row[5],
                "created_at": row[6]
            } if row else None
        finally:
            db.close()
    
    @staticmethod
    def get_all_users():
        """SELECT all users"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT user_id, name, email, role, is_active, avatar_url, created_at
                FROM users
                ORDER BY created_at DESC
            """)
            result = db.execute(query)
            rows = result.fetchall()
            return [
                {
                    "user_id": row[0],
                    "name": row[1],
                    "email": row[2],
                    "role": row[3],
                    "is_active": row[4],
                    "avatar_url": row[5],
                    "created_at": row[6]
                }
                for row in rows
            ]
        finally:
            db.close()
    
    @staticmethod
    def update_user(user_id, name=None, email=None, avatar_url=None):
        """UPDATE user - full row update"""
        db = SessionLocal()
        try:
            if name is not None:
                query = text("UPDATE users SET name = :name WHERE user_id = :user_id")
                db.execute(query, {"name": name, "user_id": user_id})
            if email is not None:
                query = text("UPDATE users SET email = :email WHERE user_id = :user_id")
                db.execute(query, {"email": email, "user_id": user_id})
            if avatar_url is not None:
                query = text("UPDATE users SET avatar_url = :avatar_url WHERE user_id = :user_id")
                db.execute(query, {"avatar_url": avatar_url, "user_id": user_id})
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating user: {e}")
            raise
        finally:
            db.close()
    
    @staticmethod
    def update_user_cell(user_id, column_name, value):
        """UPDATE single cell in user table"""
        db = SessionLocal()
        try:
            # Whitelist allowed columns to prevent SQL injection
            allowed_columns = ['name', 'email', 'role', 'is_active', 'avatar_url']
            if column_name not in allowed_columns:
                raise ValueError(f"Invalid column: {column_name}")
            
            query = text(f"UPDATE users SET {column_name} = :value WHERE user_id = :user_id")
            db.execute(query, {"value": value, "user_id": user_id})
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating user cell: {e}")
            raise
        finally:
            db.close()

    @staticmethod
    def set_user_avatar(user_id, avatar_url):
        """Update avatar URL for a user"""
        db = SessionLocal()
        try:
            query = text("UPDATE users SET avatar_url = :avatar_url WHERE user_id = :user_id")
            db.execute(query, {"avatar_url": avatar_url, "user_id": user_id})
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating user avatar: {e}")
            raise
        finally:
            db.close()
    
    @staticmethod
    def delete_user(user_id):
        """DELETE user (cascades to fields and crops)"""
        db = SessionLocal()
        try:
            query = text("DELETE FROM users WHERE user_id = :user_id")
            db.execute(query, {"user_id": user_id})
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting user: {e}")
            raise
        finally:
            db.close()

# ============ REGION QUERIES (TABLE 2) ============
class RegionQueries:
    """Complete CRUD operations for regions table"""
    
    @staticmethod
    def get_all_regions():
        """SELECT all regions"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT id, region_name, climate_type, latitude, longitude, created_at
                FROM regions
                ORDER BY region_name
            """)
            result = db.execute(query)
            rows = result.fetchall()
            return [
                {
                    "id": row[0],
                    "region_name": row[1],
                    "climate_type": row[2],
                    "latitude": row[3],
                    "longitude": row[4],
                    "created_at": row[5]
                }
                for row in rows
            ]
        finally:
            db.close()
    
    @staticmethod
    def get_region_by_id(region_id):
        """SELECT region by ID"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT id, region_name, climate_type, latitude, longitude, created_at
                FROM regions
                WHERE id = :region_id
            """)
            result = db.execute(query, {"region_id": region_id})
            row = result.fetchone()
            return {
                "id": row[0],
                "region_name": row[1],
                "climate_type": row[2],
                "latitude": row[3],
                "longitude": row[4],
                "created_at": row[5]
            } if row else None
        finally:
            db.close()
    
    @staticmethod
    def create_region(region_name, climate_type, latitude=None, longitude=None):
        """INSERT new region"""
        db = SessionLocal()
        try:
            query = text("""
                INSERT INTO regions (region_name, climate_type, latitude, longitude)
                VALUES (:region_name, :climate_type, :latitude, :longitude)
                RETURNING id, region_name
            """)
            result = db.execute(query, {
                "region_name": region_name,
                "climate_type": climate_type,
                "latitude": latitude,
                "longitude": longitude
            })
            db.commit()
            row = result.fetchone()
            return {"id": row[0], "region_name": row[1]} if row else None
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating region: {e}")
            raise
        finally:
            db.close()
    
    @staticmethod
    def update_region_cell(region_id, column_name, value):
        """UPDATE single cell in region table"""
        db = SessionLocal()
        try:
            allowed_columns = ['region_name', 'climate_type', 'latitude', 'longitude']
            if column_name not in allowed_columns:
                raise ValueError(f"Invalid column: {column_name}")
            
            query = text(f"UPDATE regions SET {column_name} = :value WHERE id = :region_id")
            db.execute(query, {"value": value, "region_id": region_id})
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating region cell: {e}")
            raise
        finally:
            db.close()

    @staticmethod
    def delete_region(region_id):
        """DELETE region"""
        db = SessionLocal()
        try:
            query = text("DELETE FROM regions WHERE id = :region_id")
            db.execute(query, {"region_id": region_id})
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting region: {e}")
            raise
        finally:
            db.close()

# ============ FIELD QUERIES (TABLE 3) ============
class FieldQueries:
    """Complete CRUD operations for fields table"""
    
    @staticmethod
    def create_field(field_name, user_id, region_id, latitude, longitude, area, soil_type):
        """INSERT new field"""
        db = SessionLocal()
        try:
            query = text("""
                INSERT INTO fields (field_name, user_id, region_id, latitude, longitude, area, soil_type, is_active)
                VALUES (:field_name, :user_id, :region_id, :latitude, :longitude, :area, :soil_type, TRUE)
                RETURNING id, field_name, user_id, region_id
            """)
            result = db.execute(query, {
                "field_name": field_name,
                "user_id": user_id,
                "region_id": region_id,
                "latitude": latitude,
                "longitude": longitude,
                "area": area,
                "soil_type": soil_type
            })
            db.commit()
            row = result.fetchone()
            return {"id": row[0], "field_name": row[1], "user_id": row[2], "region_id": row[3]} if row else None
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating field: {e}")
            raise
        finally:
            db.close()
    
    @staticmethod
    def get_all_fields():
        """SELECT all active fields"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT id, field_name, user_id, region_id, latitude, longitude, area, soil_type, created_at
                FROM fields
                WHERE is_active = TRUE
                ORDER BY created_at DESC
            """)
            result = db.execute(query)
            rows = result.fetchall()
            return [
                {
                    "id": row[0],
                    "field_name": row[1],
                    "user_id": row[2],
                    "region_id": row[3],
                    "latitude": row[4],
                    "longitude": row[5],
                    "area": row[6],
                    "soil_type": row[7],
                    "created_at": row[8]
                }
                for row in rows
            ]
        finally:
            db.close()
    
    @staticmethod
    def get_field_by_id(field_id):
        """SELECT field by ID"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT id, field_name, user_id, region_id, latitude, longitude, area, soil_type, created_at
                FROM fields
                WHERE id = :field_id AND is_active = TRUE
            """)
            result = db.execute(query, {"field_id": field_id})
            row = result.fetchone()
            return {
                "id": row[0],
                "field_name": row[1],
                "user_id": row[2],
                "region_id": row[3],
                "latitude": row[4],
                "longitude": row[5],
                "area": row[6],
                "soil_type": row[7],
                "created_at": row[8]
            } if row else None
        finally:
            db.close()
    
    @staticmethod
    def get_fields_by_user(user_id):
        """SELECT fields by user"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT id, field_name, user_id, region_id, latitude, longitude, area, soil_type, created_at
                FROM fields
                WHERE user_id = :user_id AND is_active = TRUE
                ORDER BY created_at DESC
            """)
            result = db.execute(query, {"user_id": user_id})
            rows = result.fetchall()
            return [
                {
                    "id": row[0],
                    "field_name": row[1],
                    "user_id": row[2],
                    "region_id": row[3],
                    "latitude": row[4],
                    "longitude": row[5],
                    "area": row[6],
                    "soil_type": row[7],
                    "created_at": row[8]
                }
                for row in rows
            ]
        finally:
            db.close()
    
    @staticmethod
    def update_field(field_id, field_name=None, area=None, soil_type=None, latitude=None, longitude=None):
        """UPDATE field - full update"""
        db = SessionLocal()
        try:
            updates = []
            params = {"field_id": field_id}
            
            if field_name:
                updates.append("field_name = :field_name")
                params["field_name"] = field_name
            if area:
                updates.append("area = :area")
                params["area"] = area
            if soil_type:
                updates.append("soil_type = :soil_type")
                params["soil_type"] = soil_type
            if latitude:
                updates.append("latitude = :latitude")
                params["latitude"] = latitude
            if longitude:
                updates.append("longitude = :longitude")
                params["longitude"] = longitude
            
            if updates:
                query = text(f"UPDATE fields SET {', '.join(updates)} WHERE id = :field_id")
                db.execute(query, params)
                db.commit()
            
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating field: {e}")
            raise
        finally:
            db.close()
    
    @staticmethod
    def update_field_cell(field_id, column_name, value):
        """UPDATE single cell in field table"""
        db = SessionLocal()
        try:
            allowed_columns = ['field_name', 'area', 'soil_type', 'latitude', 'longitude', 'is_active']
            if column_name not in allowed_columns:
                raise ValueError(f"Invalid column: {column_name}")
            
            query = text(f"UPDATE fields SET {column_name} = :value WHERE id = :field_id")
            db.execute(query, {"value": value, "field_id": field_id})
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating field cell: {e}")
            raise
        finally:
            db.close()
    
    @staticmethod
    def delete_field(field_id):
        """DELETE field (soft delete)"""
        db = SessionLocal()
        try:
            query = text("UPDATE fields SET is_active = FALSE WHERE id = :field_id")
            db.execute(query, {"field_id": field_id})
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting field: {e}")
            raise
        finally:
            db.close()

# ============ SATELLITE QUERIES (TABLE 4) ============
class SatelliteQueries:
    """Complete CRUD operations for satellites table"""
    
    @staticmethod
    def get_all_satellites():
        """SELECT all satellites"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT id, satellite_name, provider, resolution, created_at
                FROM satellites
                ORDER BY satellite_name
            """)
            result = db.execute(query)
            rows = result.fetchall()
            return [
                {
                    "id": row[0],
                    "satellite_name": row[1],
                    "provider": row[2],
                    "resolution": row[3],
                    "created_at": row[4]
                }
                for row in rows
            ]
        finally:
            db.close()
    
    @staticmethod
    def get_satellite_by_id(satellite_id):
        """SELECT satellite by ID"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT id, satellite_name, provider, resolution
                FROM satellites
                WHERE id = :satellite_id
            """)
            result = db.execute(query, {"satellite_id": satellite_id})
            row = result.fetchone()
            return {
                "id": row[0],
                "satellite_name": row[1],
                "provider": row[2],
                "resolution": row[3]
            } if row else None
        finally:
            db.close()
    
    @staticmethod
    def create_satellite(satellite_name, provider, resolution):
        """INSERT new satellite"""
        db = SessionLocal()
        try:
            query = text("""
                INSERT INTO satellites (satellite_name, provider, resolution)
                VALUES (:satellite_name, :provider, :resolution)
                RETURNING id, satellite_name
            """)
            result = db.execute(query, {
                "satellite_name": satellite_name,
                "provider": provider,
                "resolution": resolution
            })
            db.commit()
            row = result.fetchone()
            return {"id": row[0], "satellite_name": row[1]} if row else None
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating satellite: {e}")
            raise
        finally:
            db.close()
    
    @staticmethod
    def update_satellite_cell(satellite_id, column_name, value):
        """UPDATE single cell in satellite table"""
        db = SessionLocal()
        try:
            allowed_columns = ['satellite_name', 'provider', 'resolution']
            if column_name not in allowed_columns:
                raise ValueError(f"Invalid column: {column_name}")
            
            query = text(f"UPDATE satellites SET {column_name} = :value WHERE id = :satellite_id")
            db.execute(query, {"value": value, "satellite_id": satellite_id})
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating satellite cell: {e}")
            raise
        finally:
            db.close()

    @staticmethod
    def delete_satellite(satellite_id):
        """DELETE satellite"""
        db = SessionLocal()
        try:
            query = text("DELETE FROM satellites WHERE id = :satellite_id")
            db.execute(query, {"satellite_id": satellite_id})
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting satellite: {e}")
            raise
        finally:
            db.close()

# ============ CROP CYCLE QUERIES (TABLE 5) ============
class CropCycleQueries:
    """Complete CRUD operations for crop_cycles table"""
    
    @staticmethod
    def create_crop_cycle(field_id, crop_name, start_date, expected_harvest_date, yield_prediction):
        """INSERT new crop cycle"""
        db = SessionLocal()
        try:
            query = text("""
                INSERT INTO crop_cycles (field_id, crop_name, start_date, expected_harvest_date, yield_prediction, status)
                VALUES (:field_id, :crop_name, :start_date, :expected_harvest_date, :yield_prediction, 'active')
                RETURNING id, crop_name, field_id, status
            """)
            result = db.execute(query, {
                "field_id": field_id,
                "crop_name": crop_name,
                "start_date": start_date,
                "expected_harvest_date": expected_harvest_date,
                "yield_prediction": yield_prediction
            })
            db.commit()
            row = result.fetchone()
            return {"id": row[0], "crop_name": row[1], "field_id": row[2], "status": row[3]} if row else None
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating crop cycle: {e}")
            raise
        finally:
            db.close()
    
    @staticmethod
    def get_all_crop_cycles():
        """SELECT all crop cycles"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT id, field_id, crop_name, start_date, expected_harvest_date, actual_harvest_date, 
                       status, yield_prediction, actual_yield, created_at
                FROM crop_cycles
                ORDER BY created_at DESC
            """)
            result = db.execute(query)
            rows = result.fetchall()
            return [
                {
                    "id": row[0],
                    "field_id": row[1],
                    "crop_name": row[2],
                    "start_date": row[3],
                    "expected_harvest_date": row[4],
                    "actual_harvest_date": row[5],
                    "status": row[6],
                    "yield_prediction": row[7],
                    "actual_yield": row[8],
                    "created_at": row[9]
                }
                for row in rows
            ]
        finally:
            db.close()
    
    @staticmethod
    def get_crop_cycle_by_id(cycle_id):
        """SELECT crop cycle by ID"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT id, field_id, crop_name, start_date, expected_harvest_date, actual_harvest_date,
                       status, yield_prediction, actual_yield, created_at
                FROM crop_cycles
                WHERE id = :cycle_id
            """)
            result = db.execute(query, {"cycle_id": cycle_id})
            row = result.fetchone()
            return {
                "id": row[0],
                "field_id": row[1],
                "crop_name": row[2],
                "start_date": row[3],
                "expected_harvest_date": row[4],
                "actual_harvest_date": row[5],
                "status": row[6],
                "yield_prediction": row[7],
                "actual_yield": row[8],
                "created_at": row[9]
            } if row else None
        finally:
            db.close()
    
    @staticmethod
    def get_cycles_by_field(field_id):
        """SELECT cycles by field"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT id, field_id, crop_name, start_date, expected_harvest_date, actual_harvest_date,
                       status, yield_prediction, actual_yield, created_at
                FROM crop_cycles
                WHERE field_id = :field_id
                ORDER BY created_at DESC
            """)
            result = db.execute(query, {"field_id": field_id})
            rows = result.fetchall()
            return [
                {
                    "id": row[0],
                    "field_id": row[1],
                    "crop_name": row[2],
                    "start_date": row[3],
                    "expected_harvest_date": row[4],
                    "actual_harvest_date": row[5],
                    "status": row[6],
                    "yield_prediction": row[7],
                    "actual_yield": row[8],
                    "created_at": row[9]
                }
                for row in rows
            ]
        finally:
            db.close()
    
    @staticmethod
    def get_active_cycles():
        """SELECT active cycles only"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT id, field_id, crop_name, start_date, expected_harvest_date, status, yield_prediction
                FROM crop_cycles
                WHERE status = 'active'
                ORDER BY created_at DESC
            """)
            result = db.execute(query)
            rows = result.fetchall()
            return [
                {
                    "id": row[0],
                    "field_id": row[1],
                    "crop_name": row[2],
                    "start_date": row[3],
                    "expected_harvest_date": row[4],
                    "status": row[5],
                    "yield_prediction": row[6]
                }
                for row in rows
            ]
        finally:
            db.close()
    
    @staticmethod
    def update_crop_cycle(cycle_id, status=None, actual_harvest_date=None, actual_yield=None):
        """UPDATE crop cycle - full update"""
        db = SessionLocal()
        try:
            updates = []
            params = {"cycle_id": cycle_id}
            
            if status:
                updates.append("status = :status")
                params["status"] = status
            if actual_harvest_date:
                updates.append("actual_harvest_date = :actual_harvest_date")
                params["actual_harvest_date"] = actual_harvest_date
            if actual_yield:
                updates.append("actual_yield = :actual_yield")
                params["actual_yield"] = actual_yield
            
            if updates:
                query = text(f"UPDATE crop_cycles SET {', '.join(updates)} WHERE id = :cycle_id")
                db.execute(query, params)
                db.commit()
            
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating crop cycle: {e}")
            raise
        finally:
            db.close()
    
    @staticmethod
    def update_crop_cycle_cell(cycle_id, column_name, value):
        """UPDATE single cell in crop_cycles table"""
        db = SessionLocal()
        try:
            allowed_columns = ['crop_name', 'start_date', 'expected_harvest_date', 'actual_harvest_date', 
                             'status', 'yield_prediction', 'actual_yield']
            if column_name not in allowed_columns:
                raise ValueError(f"Invalid column: {column_name}")
            
            query = text(f"UPDATE crop_cycles SET {column_name} = :value WHERE id = :cycle_id")
            db.execute(query, {"value": value, "cycle_id": cycle_id})
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating crop cycle cell: {e}")
            raise
        finally:
            db.close()
    
    @staticmethod
    def delete_crop_cycle(cycle_id):
        """DELETE crop cycle"""
        db = SessionLocal()
        try:
            query = text("DELETE FROM crop_cycles WHERE id = :cycle_id")
            db.execute(query, {"cycle_id": cycle_id})
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting crop cycle: {e}")
            raise
        finally:
            db.close()

# ============ OBSERVATION QUERIES (TABLE 6) ============
class ObservationQueries:
    """Complete CRUD operations for observations table"""
    
    @staticmethod
    def get_all_observations():
        """SELECT all observations"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT id, field_id, satellite_id, cycle_id, observation_date, cloud_cover, processed, created_at
                FROM observations
                ORDER BY created_at DESC
            """)
            result = db.execute(query)
            rows = result.fetchall()
            return [
                {
                    "id": row[0],
                    "field_id": row[1],
                    "satellite_id": row[2],
                    "cycle_id": row[3],
                    "observation_date": row[4],
                    "cloud_cover": row[5],
                    "processed": row[6],
                    "created_at": row[7]
                }
                for row in rows
            ]
        finally:
            db.close()
    
    @staticmethod
    def get_observation_by_id(observation_id):
        """SELECT observation by ID"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT id, field_id, satellite_id, cycle_id, observation_date, cloud_cover, processed, created_at
                FROM observations
                WHERE id = :observation_id
            """)
            result = db.execute(query, {"observation_id": observation_id})
            row = result.fetchone()
            return {
                "id": row[0],
                "field_id": row[1],
                "satellite_id": row[2],
                "cycle_id": row[3],
                "observation_date": row[4],
                "cloud_cover": row[5],
                "processed": row[6],
                "created_at": row[7]
            } if row else None
        finally:
            db.close()
    
    @staticmethod
    def create_observation(field_id, satellite_id, cycle_id, observation_date, cloud_cover):
        """INSERT new observation"""
        db = SessionLocal()
        try:
            query = text("""
                INSERT INTO observations (field_id, satellite_id, cycle_id, observation_date, cloud_cover, processed)
                VALUES (:field_id, :satellite_id, :cycle_id, :observation_date, :cloud_cover, FALSE)
                RETURNING id, observation_date
            """)
            result = db.execute(query, {
                "field_id": field_id,
                "satellite_id": satellite_id,
                "cycle_id": cycle_id,
                "observation_date": observation_date,
                "cloud_cover": cloud_cover
            })
            db.commit()
            row = result.fetchone()
            return {"id": row[0], "observation_date": row[1]} if row else None
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating observation: {e}")
            raise
        finally:
            db.close()
    
    @staticmethod
    def update_observation_cell(observation_id, column_name, value):
        """UPDATE single cell in observations table"""
        db = SessionLocal()
        try:
            allowed_columns = ['observation_date', 'cloud_cover', 'processed']
            if column_name not in allowed_columns:
                raise ValueError(f"Invalid column: {column_name}")
            
            query = text(f"UPDATE observations SET {column_name} = :value WHERE id = :observation_id")
            db.execute(query, {"value": value, "observation_id": observation_id})
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating observation cell: {e}")
            raise
        finally:
            db.close()

    @staticmethod
    def delete_observation(observation_id):
        """DELETE observation"""
        db = SessionLocal()
        try:
            query = text("DELETE FROM observations WHERE id = :observation_id")
            db.execute(query, {"observation_id": observation_id})
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting observation: {e}")
            raise
        finally:
            db.close()

# ============ BAND VALUES QUERIES (TABLE 7) ============
class BandValueQueries:
    """Complete CRUD operations for band_values table"""
    
    @staticmethod
    def get_all_band_values():
        """SELECT all band values"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT id, observation_id, band_name, band_value, created_at
                FROM band_values
                ORDER BY created_at DESC
            """)
            result = db.execute(query)
            rows = result.fetchall()
            return [
                {
                    "id": row[0],
                    "observation_id": row[1],
                    "band_name": row[2],
                    "band_value": row[3],
                    "created_at": row[4]
                }
                for row in rows
            ]
        finally:
            db.close()

    @staticmethod
    def get_band_value_by_id(band_id):
        """SELECT band value by ID"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT id, observation_id, band_name, band_value, created_at
                FROM band_values
                WHERE id = :band_id
            """)
            result = db.execute(query, {"band_id": band_id})
            row = result.fetchone()
            return {
                "id": row[0],
                "observation_id": row[1],
                "band_name": row[2],
                "band_value": row[3],
                "created_at": row[4]
            } if row else None
        finally:
            db.close()
    
    @staticmethod
    def create_band_value(observation_id, band_name, band_value):
        """INSERT new band value"""
        db = SessionLocal()
        try:
            query = text("""
                INSERT INTO band_values (observation_id, band_name, band_value)
                VALUES (:observation_id, :band_name, :band_value)
                RETURNING id, band_name
            """)
            result = db.execute(query, {
                "observation_id": observation_id,
                "band_name": band_name,
                "band_value": band_value
            })
            db.commit()
            row = result.fetchone()
            return {"id": row[0], "band_name": row[1]} if row else None
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating band value: {e}")
            raise
        finally:
            db.close()
    
    @staticmethod
    def update_band_value_cell(band_id, column_name, value):
        """UPDATE single cell in band_values table"""
        db = SessionLocal()
        try:
            allowed_columns = ['band_name', 'band_value']
            if column_name not in allowed_columns:
                raise ValueError(f"Invalid column: {column_name}")
            
            query = text(f"UPDATE band_values SET {column_name} = :value WHERE id = :band_id")
            db.execute(query, {"value": value, "band_id": band_id})
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating band value cell: {e}")
            raise
        finally:
            db.close()

    @staticmethod
    def delete_band_value(band_id):
        """DELETE band value"""
        db = SessionLocal()
        try:
            query = text("DELETE FROM band_values WHERE id = :band_id")
            db.execute(query, {"band_id": band_id})
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting band value: {e}")
            raise
        finally:
            db.close()

# ============ WEATHER RECORDS QUERIES (TABLE 8) ============
class WeatherQueries:
    """Complete CRUD operations for weather_records table"""
    
    @staticmethod
    def get_all_weather():
        """SELECT all weather records"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT id, field_id, date, temperature, rainfall, humidity, wind_speed, wind_direction, pressure, created_at
                FROM weather_records
                ORDER BY date DESC
            """)
            result = db.execute(query)
            rows = result.fetchall()
            return [
                {
                    "id": row[0],
                    "field_id": row[1],
                    "date": row[2],
                    "temperature": row[3],
                    "rainfall": row[4],
                    "humidity": row[5],
                    "wind_speed": row[6],
                    "wind_direction": row[7],
                    "pressure": row[8],
                    "created_at": row[9]
                }
                for row in rows
            ]
        finally:
            db.close()

    @staticmethod
    def get_weather_by_id(weather_id):
        """SELECT weather record by ID"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT id, field_id, date, temperature, rainfall, humidity, wind_speed, wind_direction, pressure, created_at
                FROM weather_records
                WHERE id = :weather_id
            """)
            result = db.execute(query, {"weather_id": weather_id})
            row = result.fetchone()
            return {
                "id": row[0],
                "field_id": row[1],
                "date": row[2],
                "temperature": row[3],
                "rainfall": row[4],
                "humidity": row[5],
                "wind_speed": row[6],
                "wind_direction": row[7],
                "pressure": row[8],
                "created_at": row[9]
            } if row else None
        finally:
            db.close()
    
    @staticmethod
    def get_weather_by_field(field_id):
        """SELECT weather by field"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT id, field_id, date, temperature, rainfall, humidity, wind_speed, wind_direction, pressure
                FROM weather_records
                WHERE field_id = :field_id
                ORDER BY date DESC
            """)
            result = db.execute(query, {"field_id": field_id})
            rows = result.fetchall()
            return [
                {
                    "id": row[0],
                    "field_id": row[1],
                    "date": row[2],
                    "temperature": row[3],
                    "rainfall": row[4],
                    "humidity": row[5],
                    "wind_speed": row[6],
                    "wind_direction": row[7],
                    "pressure": row[8]
                }
                for row in rows
            ]
        finally:
            db.close()
    
    @staticmethod
    def create_weather(field_id, date, temperature, rainfall, humidity, wind_speed, wind_direction, pressure):
        """INSERT new weather record"""
        db = SessionLocal()
        try:
            query = text("""
                INSERT INTO weather_records (field_id, date, temperature, rainfall, humidity, wind_speed, wind_direction, pressure)
                VALUES (:field_id, :date, :temperature, :rainfall, :humidity, :wind_speed, :wind_direction, :pressure)
                RETURNING id, date
            """)
            result = db.execute(query, {
                "field_id": field_id,
                "date": date,
                "temperature": temperature,
                "rainfall": rainfall,
                "humidity": humidity,
                "wind_speed": wind_speed,
                "wind_direction": wind_direction,
                "pressure": pressure
            })
            db.commit()
            row = result.fetchone()
            return {"id": row[0], "date": row[1]} if row else None
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating weather record: {e}")
            raise
        finally:
            db.close()
    
    @staticmethod
    def update_weather_cell(weather_id, column_name, value):
        """UPDATE single cell in weather_records table"""
        db = SessionLocal()
        try:
            allowed_columns = ['date', 'temperature', 'rainfall', 'humidity', 'wind_speed', 'wind_direction', 'pressure']
            if column_name not in allowed_columns:
                raise ValueError(f"Invalid column: {column_name}")
            
            query = text(f"UPDATE weather_records SET {column_name} = :value WHERE id = :weather_id")
            db.execute(query, {"value": value, "weather_id": weather_id})
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating weather cell: {e}")
            raise
        finally:
            db.close()

    @staticmethod
    def delete_weather(weather_id):
        """DELETE weather record"""
        db = SessionLocal()
        try:
            query = text("DELETE FROM weather_records WHERE id = :weather_id")
            db.execute(query, {"weather_id": weather_id})
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting weather record: {e}")
            raise
        finally:
            db.close()

# ============ DERIVED METRICS QUERIES (TABLE 9) ============
class DerivedMetricsQueries:
    """Complete CRUD operations for derived_metrics table"""
    
    @staticmethod
    def get_all_metrics():
        """SELECT all derived metrics"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT id, observation_id, ndvi, evi, soil_moisture, crop_health_score, created_at
                FROM derived_metrics
                ORDER BY created_at DESC
            """)
            result = db.execute(query)
            rows = result.fetchall()
            return [
                {
                    "id": row[0],
                    "observation_id": row[1],
                    "ndvi": row[2],
                    "evi": row[3],
                    "soil_moisture": row[4],
                    "crop_health_score": row[5],
                    "created_at": row[6]
                }
                for row in rows
            ]
        finally:
            db.close()

    @staticmethod
    def get_metric_by_id(metric_id):
        """SELECT derived metric by ID"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT id, observation_id, ndvi, evi, soil_moisture, crop_health_score, created_at
                FROM derived_metrics
                WHERE id = :metric_id
            """)
            result = db.execute(query, {"metric_id": metric_id})
            row = result.fetchone()
            return {
                "id": row[0],
                "observation_id": row[1],
                "ndvi": row[2],
                "evi": row[3],
                "soil_moisture": row[4],
                "crop_health_score": row[5],
                "created_at": row[6]
            } if row else None
        finally:
            db.close()
    
    @staticmethod
    def create_metric(observation_id, ndvi, evi, soil_moisture, crop_health_score):
        """INSERT new derived metric"""
        db = SessionLocal()
        try:
            query = text("""
                INSERT INTO derived_metrics (observation_id, ndvi, evi, soil_moisture, crop_health_score)
                VALUES (:observation_id, :ndvi, :evi, :soil_moisture, :crop_health_score)
                RETURNING id, observation_id
            """)
            result = db.execute(query, {
                "observation_id": observation_id,
                "ndvi": ndvi,
                "evi": evi,
                "soil_moisture": soil_moisture,
                "crop_health_score": crop_health_score
            })
            db.commit()
            row = result.fetchone()
            return {"id": row[0], "observation_id": row[1]} if row else None
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating derived metric: {e}")
            raise
        finally:
            db.close()
    
    @staticmethod
    def update_metric_cell(metric_id, column_name, value):
        """UPDATE single cell in derived_metrics table"""
        db = SessionLocal()
        try:
            allowed_columns = ['ndvi', 'evi', 'soil_moisture', 'crop_health_score']
            if column_name not in allowed_columns:
                raise ValueError(f"Invalid column: {column_name}")
            
            query = text(f"UPDATE derived_metrics SET {column_name} = :value WHERE id = :metric_id")
            db.execute(query, {"value": value, "metric_id": metric_id})
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating metric cell: {e}")
            raise
        finally:
            db.close()

    @staticmethod
    def delete_metric(metric_id):
        """DELETE derived metric"""
        db = SessionLocal()
        try:
            query = text("DELETE FROM derived_metrics WHERE id = :metric_id")
            db.execute(query, {"metric_id": metric_id})
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting derived metric: {e}")
            raise
        finally:
            db.close()

# ============ ALERT QUERIES (TABLE 10) ============
class AlertQueries:
    """Complete CRUD operations for alerts table"""
    
    @staticmethod
    def get_all_alerts():
        """SELECT all alerts"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT id, field_id, alert_type, severity, message, is_resolved, created_at
                FROM alerts
                ORDER BY created_at DESC
            """)
            result = db.execute(query)
            rows = result.fetchall()
            return [
                {
                    "id": row[0],
                    "field_id": row[1],
                    "alert_type": row[2],
                    "severity": row[3],
                    "message": row[4],
                    "is_resolved": row[5],
                    "created_at": row[6]
                }
                for row in rows
            ]
        finally:
            db.close()
    
    @staticmethod
    def get_unresolved_alerts():
        """SELECT unresolved alerts"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT id, field_id, alert_type, severity, message, created_at
                FROM alerts
                WHERE is_resolved = FALSE
                ORDER BY severity DESC, created_at DESC
            """)
            result = db.execute(query)
            rows = result.fetchall()
            return [
                {
                    "id": row[0],
                    "field_id": row[1],
                    "alert_type": row[2],
                    "severity": row[3],
                    "message": row[4],
                    "created_at": row[5]
                }
                for row in rows
            ]
        finally:
            db.close()
    
    @staticmethod
    def create_alert(field_id, alert_type, severity, message, observation_id=None):
        """INSERT new alert"""
        db = SessionLocal()
        try:
            query = text("""
                INSERT INTO alerts (field_id, observation_id, alert_type, severity, message, is_resolved)
                VALUES (:field_id, :observation_id, :alert_type, :severity, :message, FALSE)
                RETURNING id, alert_type
            """)
            result = db.execute(query, {
                "field_id": field_id,
                "observation_id": observation_id,
                "alert_type": alert_type,
                "severity": severity,
                "message": message
            })
            db.commit()
            row = result.fetchone()
            return {"id": row[0], "alert_type": row[1]} if row else None
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating alert: {e}")
            raise
        finally:
            db.close()
    
    @staticmethod
    def update_alert_cell(alert_id, column_name, value):
        """UPDATE single cell in alerts table"""
        db = SessionLocal()
        try:
            allowed_columns = ['alert_type', 'severity', 'message', 'is_resolved']
            if column_name not in allowed_columns:
                raise ValueError(f"Invalid column: {column_name}")
            
            query = text(f"UPDATE alerts SET {column_name} = :value WHERE id = :alert_id")
            db.execute(query, {"value": value, "alert_id": alert_id})
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating alert cell: {e}")
            raise
        finally:
            db.close()
    
    @staticmethod
    def resolve_alert(alert_id):
        """UPDATE alert status to resolved"""
        db = SessionLocal()
        try:
            query = text("""
                UPDATE alerts 
                SET is_resolved = TRUE, resolved_at = CURRENT_TIMESTAMP 
                WHERE id = :alert_id
            """)
            db.execute(query, {"alert_id": alert_id})
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error resolving alert: {e}")
            raise
        finally:
            db.close()

# ============ COMPLEX QUERIES (JOIN OPERATIONS) ============
class ComplexQueries:
    """Complex JOIN queries for analytics and reporting"""
    
    @staticmethod
    def get_field_with_details(field_id):
        """JOIN: Field with user and region details"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT 
                    f.id, f.field_name, f.area, f.soil_type,
                    u.name as farmer_name, u.email,
                    r.region_name, r.climate_type
                FROM fields f
                INNER JOIN users u ON f.user_id = u.user_id
                INNER JOIN regions r ON f.region_id = r.id
                WHERE f.id = :field_id AND f.is_active = TRUE
            """)
            result = db.execute(query, {"field_id": field_id})
            row = result.fetchone()
            return {
                "field_id": row[0],
                "field_name": row[1],
                "area": row[2],
                "soil_type": row[3],
                "farmer_name": row[4],
                "farmer_email": row[5],
                "region": row[6],
                "climate": row[7]
            } if row else None
        finally:
            db.close()
    
    @staticmethod
    def get_field_with_crops(field_id):
        """JOIN: Field with its crop cycles"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT 
                    f.field_name, f.area,
                    cc.id, cc.crop_name, cc.status, cc.yield_prediction, cc.actual_yield
                FROM fields f
                LEFT JOIN crop_cycles cc ON f.id = cc.field_id
                WHERE f.id = :field_id AND f.is_active = TRUE
                ORDER BY cc.created_at DESC
            """)
            result = db.execute(query, {"field_id": field_id})
            rows = result.fetchall()
            if not rows:
                return None
            
            field_name = rows[0][0]
            field_area = rows[0][1]
            cycles = [
                {
                    "cycle_id": row[2],
                    "crop_name": row[3],
                    "status": row[4],
                    "yield_prediction": row[5],
                    "actual_yield": row[6]
                }
                for row in rows if row[2] is not None
            ]
            
            return {
                "field_name": field_name,
                "area": field_area,
                "crop_cycles": cycles
            }
        finally:
            db.close()
    
    @staticmethod
    def get_crop_yield_analysis():
        """JOIN + GROUP BY: Crop yield analysis across all fields"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT 
                    cc.crop_name,
                    COUNT(*) as total_cycles,
                    AVG(cc.actual_yield) as avg_yield,
                    MAX(cc.actual_yield) as best_yield,
                    MIN(cc.actual_yield) as worst_yield,
                    SUM(cc.actual_yield) as total_yield
                FROM crop_cycles cc
                WHERE cc.status = 'completed' AND cc.actual_yield IS NOT NULL
                GROUP BY cc.crop_name
                ORDER BY avg_yield DESC
            """)
            result = db.execute(query)
            rows = result.fetchall()
            return [
                {
                    "crop_name": row[0],
                    "total_cycles": row[1],
                    "average_yield": float(row[2]) if row[2] else 0,
                    "best_yield": float(row[3]) if row[3] else 0,
                    "worst_yield": float(row[4]) if row[4] else 0,
                    "total_yield": float(row[5]) if row[5] else 0
                }
                for row in rows
            ]
        finally:
            db.close()
    
    @staticmethod
    def get_field_health_dashboard():
        """JOIN: Comprehensive field health dashboard"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT 
                    f.id, f.field_name, f.area,
                    u.name as farmer_name,
                    r.region_name,
                    cc.crop_name, cc.status as crop_status,
                    wr.temperature, wr.rainfall,
                    dm.crop_health_score,
                    COUNT(DISTINCT a.id) as alert_count
                FROM fields f
                LEFT JOIN users u ON f.user_id = u.user_id
                LEFT JOIN regions r ON f.region_id = r.id
                LEFT JOIN crop_cycles cc ON f.id = cc.field_id AND cc.status = 'active'
                LEFT JOIN weather_records wr ON f.id = wr.field_id
                LEFT JOIN observations o ON f.id = o.field_id
                LEFT JOIN derived_metrics dm ON o.id = dm.observation_id
                LEFT JOIN alerts a ON f.id = a.field_id AND a.is_resolved = FALSE
                WHERE f.is_active = TRUE
                GROUP BY f.id, f.field_name, f.area, u.name, r.region_name, 
                         cc.crop_name, cc.status, wr.temperature, wr.rainfall, dm.crop_health_score
                ORDER BY f.field_name
            """)
            result = db.execute(query)
            rows = result.fetchall()
            return [
                {
                    "field_id": row[0],
                    "field_name": row[1],
                    "area": row[2],
                    "farmer_name": row[3],
                    "region": row[4],
                    "current_crop": row[5],
                    "crop_status": row[6],
                    "temperature": row[7],
                    "rainfall": row[8],
                    "health_score": row[9],
                    "active_alerts": row[10]
                }
                for row in rows
            ]
        finally:
            db.close()
    
    @staticmethod
    def get_farmer_performance():
        """JOIN + GROUP BY: Farmer productivity report"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT 
                    u.user_id, u.name, u.email,
                    COUNT(DISTINCT f.id) as total_fields,
                    COUNT(DISTINCT cc.id) as total_cycles,
                    AVG(cc.actual_yield) as avg_yield,
                    COUNT(CASE WHEN cc.status = 'active' THEN 1 END) as active_cycles,
                    COUNT(CASE WHEN a.severity = 'high' THEN 1 END) as high_alerts
                FROM users u
                LEFT JOIN fields f ON u.user_id = f.user_id
                LEFT JOIN crop_cycles cc ON f.id = cc.field_id
                LEFT JOIN alerts a ON f.id = a.field_id
                WHERE u.role = 'farmer'
                GROUP BY u.user_id, u.name, u.email
                HAVING COUNT(DISTINCT f.id) > 0
                ORDER BY avg_yield DESC
            """)
            result = db.execute(query)
            rows = result.fetchall()
            return [
                {
                    "farmer_id": row[0],
                    "farmer_name": row[1],
                    "email": row[2],
                    "total_fields": row[3],
                    "total_cycles": row[4],
                    "avg_yield": float(row[5]) if row[5] else 0,
                    "active_cycles": row[6],
                    "high_alerts": row[7]
                }
                for row in rows
            ]
        finally:
            db.close()
    
    @staticmethod
    def get_region_weather_trends():
        """JOIN + GROUP BY: Regional weather trend analysis"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT 
                    r.region_name,
                    EXTRACT(MONTH FROM TO_DATE(wr.date, 'YYYY-MM-DD'))::INT as month,
                    ROUND(AVG(wr.temperature)::numeric, 2) as avg_temp,
                    ROUND(MAX(wr.temperature)::numeric, 2) as max_temp,
                    ROUND(MIN(wr.temperature)::numeric, 2) as min_temp,
                    ROUND(AVG(wr.rainfall)::numeric, 2) as avg_rainfall,
                    COUNT(*) as data_points
                FROM regions r
                JOIN fields f ON r.id = f.region_id
                JOIN weather_records wr ON f.id = wr.field_id
                GROUP BY r.region_name, EXTRACT(MONTH FROM TO_DATE(wr.date, 'YYYY-MM-DD'))
                ORDER BY r.region_name, month
            """)
            result = db.execute(query)
            rows = result.fetchall()
            return [
                {
                    "region": row[0],
                    "month": int(row[1]) if row[1] else None,
                    "avg_temperature": float(row[2]),
                    "max_temperature": float(row[3]),
                    "min_temperature": float(row[4]),
                    "avg_rainfall": float(row[5]),
                    "data_points": row[6]
                }
                for row in rows
            ]
        finally:
            db.close()

# ============ REPORT GENERATION SUPPORT ============
class ReportQueries:
    """Queries designed for future report generation features"""
    
    @staticmethod
    def get_field_report_data(field_id):
        """Get all data needed for field report generation"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT 
                    f.field_name, f.area, f.soil_type, f.latitude, f.longitude,
                    u.name as farmer_name, u.email,
                    r.region_name,
                    COUNT(DISTINCT cc.id) as total_cycles,
                    AVG(cc.actual_yield) as avg_yield,
                    COUNT(DISTINCT a.id) as total_alerts
                FROM fields f
                LEFT JOIN users u ON f.user_id = u.user_id
                LEFT JOIN regions r ON f.region_id = r.id
                LEFT JOIN crop_cycles cc ON f.id = cc.field_id
                LEFT JOIN alerts a ON f.id = a.field_id
                WHERE f.id = :field_id
                GROUP BY f.id, f.field_name, f.area, f.soil_type, f.latitude, f.longitude,
                         u.name, u.email, r.region_name
            """)
            result = db.execute(query, {"field_id": field_id})
            row = result.fetchone()
            return {
                "field_name": row[0],
                "area": row[1],
                "soil_type": row[2],
                "latitude": row[3],
                "longitude": row[4],
                "farmer_name": row[5],
                "farmer_email": row[6],
                "region": row[7],
                "total_cycles": row[8],
                "average_yield": float(row[9]) if row[9] else 0,
                "total_alerts": row[10]
            } if row else None
        finally:
            db.close()
    
    @staticmethod
    def get_seasonal_yield_report():
        """Get seasonal yield data for report generation"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT 
                    cc.crop_name,
                    EXTRACT(QUARTER FROM TO_DATE(cc.start_date, 'YYYY-MM-DD'))::INT as season,
                    COUNT(*) as total_count,
                    AVG(cc.actual_yield) as avg_yield,
                    SUM(cc.actual_yield) as total_yield
                FROM crop_cycles cc
                WHERE cc.status = 'completed' AND cc.actual_yield IS NOT NULL
                GROUP BY cc.crop_name, EXTRACT(QUARTER FROM TO_DATE(cc.start_date, 'YYYY-MM-DD'))
                ORDER BY cc.crop_name, season
            """)
            result = db.execute(query)
            rows = result.fetchall()
            return [
                {
                    "crop": row[0],
                    "season": int(row[1]) if row[1] else None,
                    "count": row[2],
                    "average_yield": float(row[3]) if row[3] else 0,
                    "total_yield": float(row[4]) if row[4] else 0
                }
                for row in rows
            ]
        finally:
            db.close()
    
    @staticmethod
    def get_health_summary_report():
        """Get overall health metrics for report generation"""
        db = SessionLocal()
        try:
            query = text("""
                SELECT 
                    COUNT(DISTINCT f.id) as total_fields,
                    COUNT(DISTINCT u.user_id) as total_farmers,
                    AVG(dm.crop_health_score) as avg_health_score,
                    COUNT(CASE WHEN a.severity = 'high' THEN 1 END) as high_severity_alerts,
                    COUNT(CASE WHEN a.is_resolved = FALSE THEN 1 END) as unresolved_alerts
                FROM fields f
                LEFT JOIN users u ON f.user_id = u.user_id AND u.role = 'farmer'
                LEFT JOIN observations o ON f.id = o.field_id
                LEFT JOIN derived_metrics dm ON o.id = dm.observation_id
                LEFT JOIN alerts a ON f.id = a.field_id
                WHERE f.is_active = TRUE
            """)
            result = db.execute(query)
            row = result.fetchone()
            return {
                "total_fields": row[0],
                "total_farmers": row[1],
                "average_health_score": float(row[2]) if row[2] else 0,
                "high_severity_alerts": row[3],
                "unresolved_alerts": row[4],
                "report_generated_at": datetime.now().isoformat()
            } if row else None
        finally:
            db.close()