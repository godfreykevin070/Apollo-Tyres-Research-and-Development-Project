-- ============================================================
-- Apollo Tyres Simulation Database Schema
-- PostgreSQL 12+
-- ============================================================

-- Drop existing tables in correct order (CASCADE handles dependencies)
DROP TABLE IF EXISTS activity_logs CASCADE;
DROP TABLE IF EXISTS tydex_files CASCADE;
DROP TABLE IF EXISTS protocol_drafts CASCADE;
DROP TABLE IF EXISTS custom_project_data CASCADE;
DROP TABLE IF EXISTS ftire_project_data CASCADE;
DROP TABLE IF EXISTS cdtire_project_data CASCADE;
DROP TABLE IF EXISTS mf52_project_data CASCADE;
DROP TABLE IF EXISTS mf62_project_data CASCADE;
DROP TABLE IF EXISTS custom_data CASCADE;
DROP TABLE IF EXISTS ftire_data CASCADE;
DROP TABLE IF EXISTS cdtire_data CASCADE;
DROP TABLE IF EXISTS mf52_data CASCADE;
DROP TABLE IF EXISTS mf62_data CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ============================================================
-- 1. USERS TABLE
-- ============================================================
CREATE TABLE users (
    id VARCHAR(20) PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'engineer',
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Create indexes for users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_created_at ON users(created_at);

-- ============================================================
-- 2. PROJECTS TABLE
-- ============================================================
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    project_name VARCHAR(255) NOT NULL,
    region VARCHAR(100) NOT NULL,
    department VARCHAR(100) NOT NULL,
    tyre_size VARCHAR(100) NOT NULL,
    protocol VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'Not Started',
    previous_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    user_email VARCHAR(255) REFERENCES users(email) ON DELETE SET NULL,
    inputs JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for projects
CREATE INDEX idx_projects_user_email ON projects(user_email);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_protocol ON projects(protocol);
CREATE INDEX idx_projects_created_at ON projects(created_at);
CREATE INDEX idx_projects_project_name ON projects(project_name);

-- ============================================================
-- 3. SCRATCH TABLES (Temporary data from Excel import)
-- ============================================================

-- MF6.2 Data
CREATE TABLE mf62_data (
    number_of_runs INT PRIMARY KEY,
    tests VARCHAR(255),
    inflation_pressure VARCHAR(255),
    loads VARCHAR(255),
    inclination_angle VARCHAR(255),
    slip_angle VARCHAR(255),
    slip_ratio VARCHAR(255),
    test_velocity VARCHAR(255),
    job VARCHAR(255),
    old_job VARCHAR(255),
    template_tydex VARCHAR(255),
    tydex_name VARCHAR(255),
    p VARCHAR(255),
    l VARCHAR(255),
    foltran VARCHAR(255),
    python_script VARCHAR(255),
    run_start_time TIMESTAMP,
    run_end_time TIMESTAMP,
    run_duration_seconds INTEGER,
    run_status VARCHAR(50) DEFAULT 'not_started',
    error_message TEXT,
    odb_path TEXT
);

CREATE INDEX idx_mf62_data_runs ON mf62_data(number_of_runs);
CREATE INDEX idx_mf62_data_job ON mf62_data(job);
CREATE INDEX idx_mf62_data_p_l ON mf62_data(p, l);

-- MF5.2 Data
CREATE TABLE mf52_data (
    number_of_runs INT PRIMARY KEY,
    tests VARCHAR(255),
    inflation_pressure VARCHAR(255),
    loads VARCHAR(255),
    inclination_angle VARCHAR(255),
    slip_angle VARCHAR(255),
    slip_ratio VARCHAR(255),
    test_velocity VARCHAR(255),
    job VARCHAR(255),
    old_job VARCHAR(255),
    template_tydex VARCHAR(255),
    tydex_name VARCHAR(255),
    p VARCHAR(255),
    l VARCHAR(255),
    foltran VARCHAR(255),
    python_script VARCHAR(255),
    run_start_time TIMESTAMP,
    run_end_time TIMESTAMP,
    run_duration_seconds INTEGER,
    run_status VARCHAR(50) DEFAULT 'not_started',
    error_message TEXT,
    odb_path TEXT
);

CREATE INDEX idx_mf52_data_runs ON mf52_data(number_of_runs);
CREATE INDEX idx_mf52_data_job ON mf52_data(job);
CREATE INDEX idx_mf52_data_p_l ON mf52_data(p, l);

-- FTire Data
CREATE TABLE ftire_data (
    number_of_runs INT PRIMARY KEY,
    tests VARCHAR(255),
    loads VARCHAR(255),
    inflation_pressure VARCHAR(255),
    test_velocity VARCHAR(255),
    longitudinal_slip VARCHAR(255),
    slip_angle VARCHAR(255),
    inclination_angle VARCHAR(255),
    cleat_orientation VARCHAR(255),
    job VARCHAR(255),
    old_job VARCHAR(255),
    template_tydex VARCHAR(255),
    tydex_name VARCHAR(255),
    p VARCHAR(255),
    l VARCHAR(255),
    foltran VARCHAR(255),
    python_script VARCHAR(255),
    run_start_time TIMESTAMP,
    run_end_time TIMESTAMP,
    run_duration_seconds INTEGER,
    run_status VARCHAR(50) DEFAULT 'not_started',
    error_message TEXT,
    odb_path TEXT
);

CREATE INDEX idx_ftire_data_runs ON ftire_data(number_of_runs);
CREATE INDEX idx_ftire_data_job ON ftire_data(job);
CREATE INDEX idx_ftire_data_p_l ON ftire_data(p, l);

-- CDTire Data
CREATE TABLE cdtire_data (
    number_of_runs INT PRIMARY KEY,
    tests VARCHAR(255),
    inflation_pressure VARCHAR(255),
    velocity VARCHAR(255),
    loads VARCHAR(255),
    camber VARCHAR(255),
    slip_angle VARCHAR(255),
    slip_range VARCHAR(255),
    cleat VARCHAR(255),
    road_surface VARCHAR(255),
    job VARCHAR(255),
    old_job VARCHAR(255),
    template_tydex VARCHAR(255),
    tydex_name VARCHAR(255),
    p VARCHAR(255),
    l VARCHAR(255),
    foltran VARCHAR(255),
    python_script VARCHAR(255),
    run_start_time TIMESTAMP,
    run_end_time TIMESTAMP,
    run_duration_seconds INTEGER,
    run_status VARCHAR(50) DEFAULT 'not_started',
    error_message TEXT,
    odb_path TEXT
);

CREATE INDEX idx_cdtire_data_runs ON cdtire_data(number_of_runs);
CREATE INDEX idx_cdtire_data_job ON cdtire_data(job);
CREATE INDEX idx_cdtire_data_p_l ON cdtire_data(p, l);

-- Custom Data
CREATE TABLE custom_data (
    number_of_runs INT PRIMARY KEY,
    tests VARCHAR(255),
    inflation_pressure VARCHAR(255),
    loads VARCHAR(255),
    inclination_angle VARCHAR(255),
    slip_angle VARCHAR(255),
    slip_ratio VARCHAR(255),
    test_velocity VARCHAR(255),
    cleat_orientation VARCHAR(255),
    displacement VARCHAR(255),
    job VARCHAR(255),
    old_job VARCHAR(255),
    template_tydex VARCHAR(255),
    tydex_name VARCHAR(255),
    p VARCHAR(255),
    l VARCHAR(255),
    foltran VARCHAR(255),
    python_script VARCHAR(255),
    run_start_time TIMESTAMP,
    run_end_time TIMESTAMP,
    run_duration_seconds INTEGER,
    run_status VARCHAR(50) DEFAULT 'not_started',
    error_message TEXT,
    odb_path TEXT
);

CREATE INDEX idx_custom_data_runs ON custom_data(number_of_runs);
CREATE INDEX idx_custom_data_job ON custom_data(job);
CREATE INDEX idx_custom_data_p_l ON custom_data(p, l);

-- ============================================================
-- 4. PERMANENT PROJECT DATA TABLES
-- ============================================================

-- MF6.2 Project Data
CREATE TABLE mf62_project_data (
    id BIGSERIAL PRIMARY KEY,
    project_id INT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    number_of_runs INT,
    tests VARCHAR(255),
    inflation_pressure VARCHAR(255),
    loads VARCHAR(255),
    inclination_angle VARCHAR(255),
    slip_angle VARCHAR(255),
    slip_ratio VARCHAR(255),
    test_velocity VARCHAR(255),
    job VARCHAR(255),
    old_job VARCHAR(255),
    template_tydex VARCHAR(255),
    tydex_name VARCHAR(255),
    p VARCHAR(255),
    l VARCHAR(255),
    foltran VARCHAR(255),
    python_script VARCHAR(255),
    run_start_time TIMESTAMP,
    run_end_time TIMESTAMP,
    run_duration_seconds INTEGER,
    run_status VARCHAR(50) DEFAULT 'not_started',
    error_message TEXT,
    odb_path TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT mf62_project_data_uniq_run UNIQUE (project_id, number_of_runs)
);

CREATE INDEX idx_mf62_proj_project_id ON mf62_project_data(project_id);
CREATE INDEX idx_mf62_proj_runs ON mf62_project_data(project_id, number_of_runs);

-- MF5.2 Project Data
CREATE TABLE mf52_project_data (
    id BIGSERIAL PRIMARY KEY,
    project_id INT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    number_of_runs INT,
    tests VARCHAR(255),
    inflation_pressure VARCHAR(255),
    loads VARCHAR(255),
    inclination_angle VARCHAR(255),
    slip_angle VARCHAR(255),
    slip_ratio VARCHAR(255),
    test_velocity VARCHAR(255),
    job VARCHAR(255),
    old_job VARCHAR(255),
    template_tydex VARCHAR(255),
    tydex_name VARCHAR(255),
    p VARCHAR(255),
    l VARCHAR(255),
    foltran VARCHAR(255),
    python_script VARCHAR(255),
    run_start_time TIMESTAMP,
    run_end_time TIMESTAMP,
    run_duration_seconds INTEGER,
    run_status VARCHAR(50) DEFAULT 'not_started',
    error_message TEXT,
    odb_path TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT mf52_project_data_uniq_run UNIQUE (project_id, number_of_runs)
);

CREATE INDEX idx_mf52_proj_project_id ON mf52_project_data(project_id);
CREATE INDEX idx_mf52_proj_runs ON mf52_project_data(project_id, number_of_runs);

-- FTire Project Data
CREATE TABLE ftire_project_data (
    id BIGSERIAL PRIMARY KEY,
    project_id INT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    number_of_runs INT,
    tests VARCHAR(255),
    loads VARCHAR(255),
    inflation_pressure VARCHAR(255),
    test_velocity VARCHAR(255),
    longitudinal_slip VARCHAR(255),
    slip_angle VARCHAR(255),
    inclination_angle VARCHAR(255),
    cleat_orientation VARCHAR(255),
    job VARCHAR(255),
    old_job VARCHAR(255),
    template_tydex VARCHAR(255),
    tydex_name VARCHAR(255),
    p VARCHAR(255),
    l VARCHAR(255),
    foltran VARCHAR(255),
    python_script VARCHAR(255),
    run_start_time TIMESTAMP,
    run_end_time TIMESTAMP,
    run_duration_seconds INTEGER,
    run_status VARCHAR(50) DEFAULT 'not_started',
    error_message TEXT,
    odb_path TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT ftire_project_data_uniq_run UNIQUE (project_id, number_of_runs)
);

CREATE INDEX idx_ftire_proj_project_id ON ftire_project_data(project_id);
CREATE INDEX idx_ftire_proj_runs ON ftire_project_data(project_id, number_of_runs);

-- CDTire Project Data
CREATE TABLE cdtire_project_data (
    id BIGSERIAL PRIMARY KEY,
    project_id INT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    number_of_runs INT,
    tests VARCHAR(255),
    inflation_pressure VARCHAR(255),
    velocity VARCHAR(255),
    loads VARCHAR(255),
    camber VARCHAR(255),
    slip_angle VARCHAR(255),
    slip_range VARCHAR(255),
    cleat VARCHAR(255),
    road_surface VARCHAR(255),
    job VARCHAR(255),
    old_job VARCHAR(255),
    template_tydex VARCHAR(255),
    tydex_name VARCHAR(255),
    p VARCHAR(255),
    l VARCHAR(255),
    foltran VARCHAR(255),
    python_script VARCHAR(255),
    run_start_time TIMESTAMP,
    run_end_time TIMESTAMP,
    run_duration_seconds INTEGER,
    run_status VARCHAR(50) DEFAULT 'not_started',
    error_message TEXT,
    odb_path TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT cdtire_project_data_uniq_run UNIQUE (project_id, number_of_runs)
);

CREATE INDEX idx_cdtire_proj_project_id ON cdtire_project_data(project_id);
CREATE INDEX idx_cdtire_proj_runs ON cdtire_project_data(project_id, number_of_runs);

-- Custom Project Data
CREATE TABLE custom_project_data (
    id BIGSERIAL PRIMARY KEY,
    project_id INT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    number_of_runs INT,
    tests VARCHAR(255),
    inflation_pressure VARCHAR(255),
    loads VARCHAR(255),
    inclination_angle VARCHAR(255),
    slip_angle VARCHAR(255),
    slip_ratio VARCHAR(255),
    test_velocity VARCHAR(255),
    cleat_orientation VARCHAR(255),
    displacement VARCHAR(255),
    job VARCHAR(255),
    old_job VARCHAR(255),
    template_tydex VARCHAR(255),
    tydex_name VARCHAR(255),
    p VARCHAR(255),
    l VARCHAR(255),
    foltran VARCHAR(255),
    python_script VARCHAR(255),
    run_start_time TIMESTAMP,
    run_end_time TIMESTAMP,
    run_duration_seconds INTEGER,
    run_status VARCHAR(50) DEFAULT 'not_started',
    error_message TEXT,
    odb_path TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT custom_project_data_uniq_run UNIQUE (project_id, number_of_runs)
);

CREATE INDEX idx_custom_proj_project_id ON custom_project_data(project_id);
CREATE INDEX idx_custom_proj_runs ON custom_project_data(project_id, number_of_runs);

-- ============================================================
-- 5. PROTOCOL DRAFTS TABLE
-- ============================================================
CREATE TABLE protocol_drafts (
    id SERIAL PRIMARY KEY,
    project_id INT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    protocol VARCHAR(50) NOT NULL,
    inputs_json JSONB DEFAULT '{}'::jsonb,
    matrix_json JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_id, protocol)
);

CREATE INDEX idx_protocol_drafts_project ON protocol_drafts(project_id);

-- ============================================================
-- 6. TYDEX FILES TABLE
-- ============================================================
CREATE TABLE tydex_files (
    id SERIAL PRIMARY KEY,
    project_id INT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    protocol VARCHAR(50) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    content TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT tydex_files_unique_file UNIQUE (project_id, filename)
);

CREATE INDEX idx_tydex_files_project ON tydex_files(project_id);
CREATE INDEX idx_tydex_files_created ON tydex_files(created_at);

-- ============================================================
-- 7. ACTIVITY LOGS TABLE
-- ============================================================
CREATE TABLE activity_logs (
    id SERIAL PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL REFERENCES users(email) ON DELETE CASCADE,
    user_name VARCHAR(255),
    activity_type VARCHAR(100),
    action VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'success',
    ip_address VARCHAR(100),
    browser VARCHAR(100),
    device_type VARCHAR(50),
    related_entity_id INT,
    related_entity_type VARCHAR(100),
    project_name VARCHAR(255),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for activity logs
CREATE INDEX idx_activity_logs_user_email ON activity_logs(user_email);
CREATE INDEX idx_activity_logs_created_at ON activity_logs(created_at);
CREATE INDEX idx_activity_logs_type ON activity_logs(activity_type);
CREATE INDEX idx_activity_logs_project_name ON activity_logs(project_name);

-- ============================================================
-- 8. VIEWS FOR EASY QUERYING
-- ============================================================

-- View: Project Summary with Run Statistics
CREATE OR REPLACE VIEW project_summary AS
SELECT 
    p.id,
    p.project_name,
    p.protocol,
    p.status,
    p.created_at,
    p.completed_at,
    p.user_email,
    u.name as user_name,
    COUNT(pd.id) as total_runs,
    COUNT(CASE WHEN pd.run_status = 'completed' THEN 1 END) as completed_runs,
    COUNT(CASE WHEN pd.run_status = 'failed' THEN 1 END) as failed_runs,
    COUNT(CASE WHEN pd.run_status = 'running' THEN 1 END) as running_runs,
    COALESCE(AVG(pd.run_duration_seconds), 0) as avg_duration_seconds
FROM projects p
LEFT JOIN users u ON p.user_email = u.email
LEFT JOIN mf62_project_data pd ON p.id = pd.project_id AND p.protocol = 'MF62'
WHERE p.protocol = 'MF62'
GROUP BY p.id, p.project_name, p.protocol, p.status, p.created_at, p.completed_at, p.user_email, u.name

UNION ALL

SELECT 
    p.id,
    p.project_name,
    p.protocol,
    p.status,
    p.created_at,
    p.completed_at,
    p.user_email,
    u.name as user_name,
    COUNT(pd.id) as total_runs,
    COUNT(CASE WHEN pd.run_status = 'completed' THEN 1 END) as completed_runs,
    COUNT(CASE WHEN pd.run_status = 'failed' THEN 1 END) as failed_runs,
    COUNT(CASE WHEN pd.run_status = 'running' THEN 1 END) as running_runs,
    COALESCE(AVG(pd.run_duration_seconds), 0) as avg_duration_seconds
FROM projects p
LEFT JOIN users u ON p.user_email = u.email
LEFT JOIN mf52_project_data pd ON p.id = pd.project_id AND p.protocol = 'MF52'
WHERE p.protocol = 'MF52'
GROUP BY p.id, p.project_name, p.protocol, p.status, p.created_at, p.completed_at, p.user_email, u.name

UNION ALL

SELECT 
    p.id,
    p.project_name,
    p.protocol,
    p.status,
    p.created_at,
    p.completed_at,
    p.user_email,
    u.name as user_name,
    COUNT(pd.id) as total_runs,
    COUNT(CASE WHEN pd.run_status = 'completed' THEN 1 END) as completed_runs,
    COUNT(CASE WHEN pd.run_status = 'failed' THEN 1 END) as failed_runs,
    COUNT(CASE WHEN pd.run_status = 'running' THEN 1 END) as running_runs,
    COALESCE(AVG(pd.run_duration_seconds), 0) as avg_duration_seconds
FROM projects p
LEFT JOIN users u ON p.user_email = u.email
LEFT JOIN ftire_project_data pd ON p.id = pd.project_id AND p.protocol = 'FTire'
WHERE p.protocol = 'FTire'
GROUP BY p.id, p.project_name, p.protocol, p.status, p.created_at, p.completed_at, p.user_email, u.name

UNION ALL

SELECT 
    p.id,
    p.project_name,
    p.protocol,
    p.status,
    p.created_at,
    p.completed_at,
    p.user_email,
    u.name as user_name,
    COUNT(pd.id) as total_runs,
    COUNT(CASE WHEN pd.run_status = 'completed' THEN 1 END) as completed_runs,
    COUNT(CASE WHEN pd.run_status = 'failed' THEN 1 END) as failed_runs,
    COUNT(CASE WHEN pd.run_status = 'running' THEN 1 END) as running_runs,
    COALESCE(AVG(pd.run_duration_seconds), 0) as avg_duration_seconds
FROM projects p
LEFT JOIN users u ON p.user_email = u.email
LEFT JOIN cdtire_project_data pd ON p.id = pd.project_id AND p.protocol = 'CDTire'
WHERE p.protocol = 'CDTire'
GROUP BY p.id, p.project_name, p.protocol, p.status, p.created_at, p.completed_at, p.user_email, u.name

UNION ALL

SELECT 
    p.id,
    p.project_name,
    p.protocol,
    p.status,
    p.created_at,
    p.completed_at,
    p.user_email,
    u.name as user_name,
    COUNT(pd.id) as total_runs,
    COUNT(CASE WHEN pd.run_status = 'completed' THEN 1 END) as completed_runs,
    COUNT(CASE WHEN pd.run_status = 'failed' THEN 1 END) as failed_runs,
    COUNT(CASE WHEN pd.run_status = 'running' THEN 1 END) as running_runs,
    COALESCE(AVG(pd.run_duration_seconds), 0) as avg_duration_seconds
FROM projects p
LEFT JOIN users u ON p.user_email = u.email
LEFT JOIN custom_project_data pd ON p.id = pd.project_id AND p.protocol = 'Custom'
WHERE p.protocol = 'Custom'
GROUP BY p.id, p.project_name, p.protocol, p.status, p.created_at, p.completed_at, p.user_email, u.name;

-- ============================================================
-- 9. FUNCTIONS AND TRIGGERS
-- ============================================================

-- Function: Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-update updated_at for users
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger: Auto-update updated_at for projects
CREATE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function: Update project status when all runs complete
CREATE OR REPLACE FUNCTION check_project_completion()
RETURNS TRIGGER AS $$
DECLARE
    total_runs INT;
    completed_runs INT;
    failed_runs INT;
BEGIN
    -- Get run statistics for the project
    SELECT 
        COUNT(*),
        COUNT(CASE WHEN run_status = 'completed' THEN 1 END),
        COUNT(CASE WHEN run_status = 'failed' THEN 1 END)
    INTO total_runs, completed_runs, failed_runs
    FROM mf62_project_data
    WHERE project_id = NEW.project_id;
    
    -- If all runs are completed or failed, update project status
    IF total_runs = completed_runs THEN
        UPDATE projects 
        SET status = 'Completed', completed_at = NOW() 
        WHERE id = NEW.project_id;
    ELSIF total_runs = completed_runs + failed_runs AND failed_runs > 0 THEN
        UPDATE projects 
        SET status = 'In Progress' 
        WHERE id = NEW.project_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- 10. GRANT PERMISSIONS
-- ============================================================

-- Grant permissions to application user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- ============================================================
-- 111. VERIFICATION QUERIES
-- ============================================================

-- Check all tables created
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Check user count
SELECT COUNT(*) as user_count FROM users;

-- Check project count
SELECT COUNT(*) as project_count FROM projects;

-- Verify table structure
SELECT 
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position;