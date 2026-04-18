DROP TABLE IF EXISTS alerts CASCADE;
DROP TABLE IF EXISTS derived_metrics CASCADE;
DROP TABLE IF EXISTS band_values CASCADE;
DROP TABLE IF EXISTS observations CASCADE;
DROP TABLE IF EXISTS weather_records CASCADE;
DROP TABLE IF EXISTS crop_cycles CASCADE;
DROP TABLE IF EXISTS satellites CASCADE;
DROP TABLE IF EXISTS fields CASCADE;
DROP TABLE IF EXISTS regions CASCADE;
DROP TABLE IF EXISTS users CASCADE;

CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('farmer', 'agronomist', 'admin')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
 
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

CREATE TABLE regions (
    id SERIAL PRIMARY KEY,
    region_id INTEGER UNIQUE,
    region_name VARCHAR(100) NOT NULL,
    climate_type VARCHAR(50),
    latitude DECIMAL(9, 6),
    longitude DECIMAL(9, 6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
 
CREATE INDEX idx_regions_name ON regions(region_name);

CREATE TABLE fields (
    id SERIAL PRIMARY KEY,
    field_id INTEGER UNIQUE,
    field_name VARCHAR(100) NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    region_id INTEGER NOT NULL REFERENCES regions(id) ON DELETE RESTRICT,
    latitude DECIMAL(10, 6),
    longitude DECIMAL(10, 6),
    area DECIMAL(10, 2),
    soil_type VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
 
CREATE INDEX idx_fields_user_id ON fields(user_id);
CREATE INDEX idx_fields_region_id ON fields(region_id);
CREATE INDEX idx_fields_name ON fields(field_name);

CREATE TABLE satellites (
    id SERIAL PRIMARY KEY,
    satellite_id INTEGER UNIQUE,
    satellite_name VARCHAR(100) NOT NULL,
    provider VARCHAR(100),
    resolution DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
 
CREATE INDEX idx_satellites_name ON satellites(satellite_name);
CREATE TABLE crop_cycles (
    id SERIAL PRIMARY KEY,
    field_id INTEGER NOT NULL REFERENCES fields(id) ON DELETE CASCADE,
    crop_name VARCHAR(100) NOT NULL,
    start_date VARCHAR(20),
    expected_harvest_date VARCHAR(20),
    actual_harvest_date VARCHAR(20),
    status VARCHAR(50) CHECK (status IN ('active', 'completed', 'abandoned')) DEFAULT 'active',
    yield_prediction DECIMAL(10, 2),
    actual_yield DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
 
CREATE INDEX idx_crop_cycles_field_id ON crop_cycles(field_id);
CREATE INDEX idx_crop_cycles_status ON crop_cycles(status);

CREATE TABLE observations (
    id SERIAL PRIMARY KEY,
    observation_id INTEGER UNIQUE,
    field_id INTEGER NOT NULL REFERENCES fields(id) ON DELETE CASCADE,
    satellite_id INTEGER NOT NULL REFERENCES satellites(id) ON DELETE RESTRICT,
    cycle_id INTEGER REFERENCES crop_cycles(id) ON DELETE SET NULL,
    observation_date VARCHAR(50),
    cloud_cover DECIMAL(5, 2),
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
 
CREATE INDEX idx_observations_field_id ON observations(field_id);
CREATE INDEX idx_observations_satellite_id ON observations(satellite_id);
CREATE INDEX idx_observations_date ON observations(observation_date);

CREATE TABLE band_values (
    id SERIAL PRIMARY KEY,
    band_id INTEGER UNIQUE,
    observation_id INTEGER NOT NULL REFERENCES observations(id) ON DELETE CASCADE,
    band_name VARCHAR(50),
    band_value DECIMAL(10, 6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
 
CREATE INDEX idx_band_values_observation_id ON band_values(observation_id);
CREATE TABLE weather_records (
    id SERIAL PRIMARY KEY,
    weather_id INTEGER UNIQUE,
    field_id INTEGER NOT NULL REFERENCES fields(id) ON DELETE CASCADE,
    date VARCHAR(50),
    temperature DECIMAL(5, 2),
    rainfall DECIMAL(10, 2),
    humidity DECIMAL(5, 2),
    wind_speed DECIMAL(10, 2),
    wind_direction VARCHAR(20),
    pressure DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
 
CREATE INDEX idx_weather_field_id ON weather_records(field_id);
CREATE INDEX idx_weather_date ON weather_records(date);

CREATE TABLE derived_metrics (
    id SERIAL PRIMARY KEY,
    metric_id INTEGER UNIQUE,
    observation_id INTEGER NOT NULL REFERENCES observations(id) ON DELETE CASCADE,
    ndvi DOUBLE PRECISION,
    evi DOUBLE PRECISION,
    soil_moisture DOUBLE PRECISION,
    crop_health_score DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
 
CREATE INDEX idx_derived_metrics_observation_id ON derived_metrics(observation_id);

CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    alert_id INTEGER UNIQUE,
    field_id INTEGER NOT NULL REFERENCES fields(id) ON DELETE CASCADE,
    observation_id INTEGER REFERENCES observations(id) ON DELETE SET NULL,
    alert_type VARCHAR(100),
    severity VARCHAR(50) CHECK (severity IN ('low', 'medium', 'high')) DEFAULT 'medium',
    message TEXT,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
 
CREATE INDEX idx_alerts_field_id ON alerts(field_id);
CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_alerts_resolved ON alerts(is_resolved);
