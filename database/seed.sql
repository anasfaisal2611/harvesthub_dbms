


INSERT INTO regions (region_id, region_name, climate_type, latitude, longitude) VALUES
(1, 'Punjab', 'Subtropical', 31.5204, 74.3587),
(2, 'Sindh', 'Desert', 24.9056, 67.0822),
(3, 'KPK', 'Temperate', 34.5553, 72.8479),
(4, 'Balochistan', 'Arid', 29.1850, 66.9135),
(5, 'Gilgit-Baltistan', 'Alpine', 35.7849, 74.3092),
(6, 'Azad Kashmir', 'Temperate', 33.7294, 73.3787),
(7, 'Islamabad', 'Subtropical', 33.7340, 73.0701),
(8, 'Northern Areas', 'Alpine', 36.0000, 75.0000);


INSERT INTO users (name, email, password_hash, role, is_active) VALUES
('Ali Khan', 'ali@farm.com', '$2b$12$aRBwbXglo.VtFRZOmyEiMOKRWSBWmy9UjuSzObrM025WP83YB11VW', 'farmer', TRUE),
('Zainab Malik', 'zainab@farm.com', '$2b$12$aRBwbXglo.VtFRZOmyEiMOKRWSBWmy9UjuSzObrM025WP83YB11VW', 'farmer', TRUE),
('Muhammad Hassan', 'hassan@farm.com', '$2b$12$aRBwbXglo.VtFRZOmyEiMOKRWSBWmy9UjuSzObrM025WP83YB11VW', 'farmer', TRUE),
('Fatima Ahmed', 'fatima@farm.com', '$2b$12$aRBwbXglo.VtFRZOmyEiMOKRWSBWmy9UjuSzObrM025WP83YB11VW', 'farmer', TRUE),
('Dr. Sajid Ahmed', 'sajid@agri.com', '$2b$12$aRBwbXglo.VtFRZOmyEiMOKRWSBWmy9UjuSzObrM025WP83YB11VW', 'agronomist', TRUE),
('Prof. Ayesha Khan', 'ayesha@agri.com', '$2b$12$aRBwbXglo.VtFRZOmyEiMOKRWSBWmy9UjuSzObrM025WP83YB11VW', 'agronomist', TRUE),
('Admin User', 'admin@system.com', '$2b$12$aRBwbXglo.VtFRZOmyEiMOKRWSBWmy9UjuSzObrM025WP83YB11VW', 'admin', TRUE);

INSERT INTO fields (field_id, field_name, user_id, region_id, latitude, longitude, area, soil_type, is_active) VALUES
(1, 'North Field', 1, 1, 31.5204, 74.3587, 50.5, 'Loamy', TRUE),
(2, 'South Field', 1, 1, 31.4204, 74.3487, 45.0, 'Sandy', TRUE),
(3, 'East Field', 2, 1, 31.5304, 74.3687, 60.0, 'Clay', TRUE),
(4, 'West Field', 2, 2, 24.9056, 67.0822, 55.0, 'Loamy', TRUE),
(5, 'Valley Field', 3, 3, 34.5553, 72.8479, 40.0, 'Rocky', TRUE),
(6, 'Mountain Field', 3, 3, 34.6553, 72.9479, 35.0, 'Sandy', TRUE),
(7, 'Desert Field', 4, 2, 24.8056, 67.1822, 70.0, 'Sandy', TRUE),
(8, 'Plains Field', 4, 1, 31.3204, 74.2587, 48.0, 'Loamy', TRUE);


INSERT INTO satellites (satellite_id, satellite_name, provider, resolution) VALUES
(1, 'Sentinel-2A', 'ESA', 10.0),
(2, 'Sentinel-2B', 'ESA', 10.0),
(3, 'Landsat 8', 'USGS', 30.0),
(4, 'MODIS', 'NASA', 250.0),
(5, 'PlanetScope', 'Planet Labs', 3.0);


INSERT INTO crop_cycles (field_id, crop_name, start_date, expected_harvest_date, status, yield_prediction) VALUES
(1, 'Wheat', '2024-03-01', '2024-06-30', 'active', 45.5),
(1, 'Rice', '2024-07-01', '2024-10-31', 'completed', 52.0),
(2, 'Corn', '2024-05-15', '2024-09-15', 'active', 38.0),
(2, 'Sugarcane', '2023-11-01', '2024-11-01', 'completed', 60.0),
(3, 'Cotton', '2024-04-01', '2024-09-30', 'active', 35.5),
(3, 'Chickpea', '2023-10-15', '2024-03-15', 'completed', 28.0),
(4, 'Date Palm', '2024-01-01', '2024-08-31', 'active', 55.0),
(4, 'Wheat', '2024-02-01', '2024-05-31', 'active', 42.0),
(5, 'Apple', '2023-03-01', '2024-09-01', 'completed', 25.0),
(5, 'Walnut', '2023-05-01', '2024-10-01', 'active', 18.5),
(6, 'Apricot', '2024-02-15', '2024-07-15', 'active', 22.0),
(6, 'Almond', '2023-01-01', '2024-08-01', 'completed', 15.0),
(7, 'Date Palm', '2024-01-01', '2024-08-31', 'active', 58.0),
(7, 'Barley', '2024-03-01', '2024-06-30', 'completed', 38.0),
(8, 'Wheat', '2024-03-15', '2024-07-15', 'active', 46.5);


INSERT INTO observations (observation_id, field_id, satellite_id, cycle_id, observation_date, cloud_cover, processed) VALUES
(1, 1, 1, 1, '2024-04-15', 5.0, TRUE),
(2, 1, 1, 1, '2024-05-01', 2.0, TRUE),
(3, 1, 2, 1, '2024-05-20', 10.0, TRUE),
(4, 2, 1, 3, '2024-06-10', 8.0, TRUE),
(5, 2, 3, 3, '2024-06-25', 0.0, TRUE),
(6, 3, 1, 5, '2024-04-20', 12.0, TRUE),
(7, 3, 2, 5, '2024-05-10', 3.0, TRUE),
(8, 4, 1, 8, '2024-03-15', 0.0, TRUE),
(9, 4, 3, 8, '2024-04-01', 5.0, TRUE),
(10, 5, 2, 9, '2023-05-15', 2.0, TRUE),
(11, 6, 1, 11, '2024-03-20', 4.0, TRUE),
(12, 7, 3, 13, '2024-02-15', 15.0, TRUE),
(13, 8, 1, 15, '2024-04-10', 6.0, TRUE),
(14, 1, 1, 2, '2024-08-15', 8.0, TRUE),
(15, 2, 2, 4, '2024-08-20', 0.0, TRUE);

INSERT INTO band_values (band_id, observation_id, band_name, band_value) VALUES
(1, 1, 'Red', 0.1234),
(2, 1, 'Green', 0.1567),
(3, 1, 'Blue', 0.1890),
(4, 1, 'NIR', 0.4567),
(5, 2, 'Red', 0.1345),
(6, 2, 'Green', 0.1678),
(7, 2, 'Blue', 0.1901),
(8, 2, 'NIR', 0.4678),
(9, 3, 'Red', 0.1400),
(10, 3, 'Green', 0.1750),
(11, 3, 'Blue', 0.1950),
(12, 3, 'NIR', 0.4750),
(13, 4, 'Red', 0.1200),
(14, 4, 'Green', 0.1500),
(15, 4, 'Blue', 0.1800),
(16, 4, 'NIR', 0.4300),
(17, 5, 'Red', 0.1500),
(18, 5, 'Green', 0.1800),
(19, 5, 'Blue', 0.2000),
(20, 5, 'NIR', 0.4900);

INSERT INTO weather_records (weather_id, field_id, date, temperature, rainfall, humidity, wind_speed, wind_direction, pressure) VALUES
(1, 1, '2024-04-15', 28.5, 12.5, 65.0, 15.0, 'North', 1013.25),
(2, 1, '2024-04-16', 29.0, 0.0, 60.0, 12.0, 'NE', 1012.50),
(3, 1, '2024-04-17', 27.5, 5.0, 70.0, 18.0, 'West', 1011.75),
(4, 2, '2024-06-10', 32.0, 0.0, 45.0, 20.0, 'South', 1010.00),
(5, 2, '2024-06-11', 31.5, 2.5, 50.0, 16.0, 'SW', 1010.50),
(6, 3, '2024-04-20', 26.0, 8.0, 72.0, 14.0, 'East', 1013.00),
(7, 3, '2024-04-21', 27.0, 0.0, 68.0, 11.0, 'NE', 1012.75),
(8, 4, '2024-03-15', 25.0, 0.0, 55.0, 10.0, 'North', 1012.00),
(9, 4, '2024-03-16', 26.5, 15.0, 75.0, 20.0, 'West', 1010.25),
(10, 5, '2023-05-15', 22.0, 25.0, 80.0, 12.0, 'South', 1012.50),
(11, 6, '2024-03-20', 18.0, 5.0, 70.0, 8.0, 'North', 1013.75),
(12, 7, '2024-02-15', 35.0, 0.0, 30.0, 25.0, 'North', 1011.00),
(13, 8, '2024-04-10', 28.0, 10.0, 68.0, 14.0, 'NW', 1012.50);

INSERT INTO derived_metrics (metric_id, observation_id, ndvi, evi, soil_moisture, crop_health_score) VALUES
(1, 1, 0.65, 0.45, 0.55, 0.78),
(2, 2, 0.72, 0.52, 0.60, 0.85),
(3, 3, 0.68, 0.48, 0.58, 0.82),
(4, 4, 0.70, 0.50, 0.62, 0.80),
(5, 5, 0.75, 0.55, 0.65, 0.88),
(6, 6, 0.62, 0.42, 0.52, 0.75),
(7, 7, 0.68, 0.48, 0.57, 0.81),
(8, 8, 0.71, 0.51, 0.61, 0.84),
(9, 9, 0.73, 0.53, 0.63, 0.86),
(10, 10, 0.58, 0.38, 0.48, 0.70),
(11, 11, 0.64, 0.44, 0.54, 0.77),
(12, 12, 0.59, 0.39, 0.49, 0.72),
(13, 13, 0.69, 0.49, 0.59, 0.83),
(14, 14, 0.76, 0.56, 0.66, 0.89),
(15, 15, 0.74, 0.54, 0.64, 0.87);


INSERT INTO alerts (alert_id, field_id, observation_id, alert_type, severity, message, is_resolved) VALUES
(1, 1, 1, 'High Soil Moisture', 'high', 'Immediate irrigation needed', FALSE),
(2, 2, 4, 'Low Crop Health', 'medium', 'NDVI score below threshold', FALSE),
(3, 3, 6, 'Disease Risk', 'high', 'Fungal infection risk detected', FALSE),
(4, 4, 8, 'Drought Stress', 'high', 'Water availability critical', TRUE),
(5, 5, 10, 'Frost Warning', 'medium', 'Temperature dropping below frost point', TRUE),
(6, 6, 11, 'Pest Infestation', 'medium', 'Insect activity detected', FALSE),
(7, 7, 12, 'Extreme Heat', 'high', 'Temperature exceeds optimal range', FALSE),
(8, 8, 13, 'Poor Air Quality', 'low', 'High pollution levels', TRUE),
(9, 1, NULL, 'Maintenance Due', 'low', 'Irrigation system maintenance required', FALSE),
(10, 2, NULL, 'Fertilizer Application', 'medium', 'Nutrient levels declining', FALSE),
(11, 3, NULL, 'Weed Control', 'medium', 'Weed growth detected', FALSE),
(12, 4, NULL, 'Pest Control', 'high', 'Pest population threshold exceeded', FALSE),
(13, 5, NULL, 'Weather Warning', 'low', 'Rainfall expected tomorrow', FALSE),
(14, 6, NULL, 'Harvest Ready', 'low', 'Crop ready for harvest', FALSE),
(15, 7, NULL, 'Soil Test', 'medium', 'Periodic soil testing due', FALSE);

