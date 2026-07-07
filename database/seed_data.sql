-- ============================================================
-- Seed Data for Testing
-- ============================================================

-- Insert sample users if not exists
DO $$
BEGIN
    -- Check if users exist before inserting
    IF NOT EXISTS (SELECT 1 FROM users WHERE email = 'engineer1@apollotyres.com') THEN
        INSERT INTO users (id, email, password, role, name, created_at) VALUES
        ('USR-ENG001', 'engineer1@apollotyres.com', 
         '$2b$10$XQpXQpXQpXQpXQpXQpXQpOuXQpXQpXQpXQpXQpXQpXQpXQpXQ', 
         'engineer', 'John Doe', NOW()),
        ('USR-ENG002', 'engineer2@apollotyres.com', 
         '$2b$10$XQpXQpXQpXQpXQpXQpXQpOuXQpXQpXQpXQpXQpXQpXQpXQpXQ', 
         'engineer', 'Jane Smith', NOW());
    END IF;
END $$;

-- Insert sample projects
DO $$
DECLARE
    proj_id INT;
BEGIN
    -- Sample MF6.2 Project
    INSERT INTO projects (project_name, region, department, tyre_size, protocol, status, user_email, created_at)
    VALUES ('Test_Project_MF62', 'APMEA', 'PCR', '225/45R17', 'MF62', 'In Progress', 'engineer1@apollotyres.com', NOW())
    RETURNING id INTO proj_id;
    
    -- Insert sample matrix data
    INSERT INTO mf62_project_data (
        project_id, number_of_runs, tests, ips, loads, inclination_angle, 
        slip_angle, slip_ratio, test_velocity, job, old_job, 
        template_tydex, tydex_name, p, l, run_status
    ) VALUES
        (proj_id, 1, 'Test1', '32.0', '400', '0', '0', '0', '60', 'P1_L1_job01', '-', 
         'Template1.tdx', 'P1_L1_job01.tdx', '1', '1', 'completed'),
        (proj_id, 2, 'Test2', '32.0', '500', '2', '0', '0', '60', 'P1_L2_job02', '-',
         'Template1.tdx', 'P1_L2_job02.tdx', '1', '2', 'completed'),
        (proj_id, 3, 'Test3', '36.0', '600', '4', '2', '0', '60', 'P1_L3_job03', '-',
         'Template1.tdx', 'P1_L3_job03.tdx', '1', '3', 'not_started'),
        (proj_id, 4, 'Test4', '36.0', '700', '6', '2', '0', '80', 'P1_L4_job04', 'P1_L3_job03',
         'Template1.tdx', 'P1_L4_job04.tdx', '1', '4', 'not_started');
    
    -- Sample MF5.2 Project
    INSERT INTO projects (project_name, region, department, tyre_size, protocol, status, user_email, created_at)
    VALUES ('Test_Project_MF52', 'EUROPE', 'TBR', '315/70R22.5', 'MF52', 'Not Started', 'engineer2@apollotyres.com', NOW())
    RETURNING id INTO proj_id;
    
    INSERT INTO mf52_project_data (
        project_id, number_of_runs, tests, inflation_pressure, loads, inclination_angle, 
        slip_angle, slip_ratio, test_velocity, job, old_job, 
        template_tydex, tydex_name, p, l
    ) VALUES
        (proj_id, 1, 'Test1', '35.0', '450', '0', '0', '0', '60', 'P1_L1_job01', '-',
         'Template1.tdx', 'P1_L1_job01.tdx', '1', '1'),
        (proj_id, 2, 'Test2', '35.0', '550', '2', '0', '0', '60', 'P1_L2_job02', '-',
         'Template1.tdx', 'P1_L2_job02.tdx', '1', '2'),
        (proj_id, 3, 'Test3', '40.0', '650', '4', '2', '0', '60', 'P1_L3_job03', '-',
         'Template1.tdx', 'P1_L3_job03.tdx', '1', '3');
    
    -- Sample FTire Project
    INSERT INTO projects (project_name, region, department, tyre_size, protocol, status, user_email, created_at)
    VALUES ('Test_Project_FTire', 'USA', 'PCR', '245/40R18', 'FTire', 'Not Started', 'engineer1@apollotyres.com', NOW())
    RETURNING id INTO proj_id;
    
    INSERT INTO ftire_project_data (
        project_id, number_of_runs, tests, loads, inflation_pressure, test_velocity,
        longitudinal_slip, slip_angle, inclination_angle, cleat_orientation,
        job, old_job, template_tydex, tydex_name, p, l
    ) VALUES
        (proj_id, 1, 'Test1', '400', '32.0', '60', '0', '0', '0', '0',
         'P1_L1_job01', '-', 'Template1.tdx', 'P1_L1_job01.tdx', '1', '1'),
        (proj_id, 2, 'Test2', '500', '32.0', '60', '5', '0', '0', '0',
         'P1_L2_job02', '-', 'Template1.tdx', 'P1_L2_job02.tdx', '1', '2');
    
    -- Sample CDTire Project
    INSERT INTO projects (project_name, region, department, tyre_size, protocol, status, user_email, created_at)
    VALUES ('Test_Project_CDTire', 'APMEA', 'TBR', '295/80R22.5', 'CDTire', 'Not Started', 'engineer2@apollotyres.com', NOW())
    RETURNING id INTO proj_id;
    
    INSERT INTO cdtire_project_data (
        project_id, number_of_runs, test_name, inflation_pressure, velocity, preload,
        camber, slip_angle, displacement, slip_range, cleat, road_surface,
        job, old_job, template_tydex, tydex_name, p, l
    ) VALUES
        (proj_id, 1, 'Test1', '8.0', '60', '400', '0', '0', '20', '0', 'None', 'Dry',
         'P1_L1_job01', '-', 'Template1.tdx', 'P1_L1_job01.tdx', '1', '1'),
        (proj_id, 2, 'Test2', '8.0', '60', '500', '2', '0', '20', '0', 'None', 'Dry',
         'P1_L2_job02', 'P1_L1_job01', 'Template1.tdx', 'P1_L2_job02.tdx', '1', '2');
    
    -- Sample Custom Project
    INSERT INTO projects (project_name, region, department, tyre_size, protocol, status, user_email, created_at)
    VALUES ('Test_Project_Custom', 'EUROPE', 'PCR', '205/55R16', 'Custom', 'Not Started', 'engineer1@apollotyres.com', NOW())
    RETURNING id INTO proj_id;
    
    INSERT INTO custom_project_data (
        project_id, number_of_runs, tests, inflation_pressure, loads, inclination_angle,
        slip_angle, slip_ratio, test_velocity, cleat_orientation, displacement,
        job, old_job, template_tydex, tydex_name, p, l
    ) VALUES
        (proj_id, 1, 'Test1', '30.0', '300', '0', '0', '0', '60', '0', '20',
         'P1_L1_job01', '-', 'Template1.tdx', 'P1_L1_job01.tdx', '1', '1'),
        (proj_id, 2, 'Test2', '30.0', '400', '2', '0', '0', '60', '0', '20',
         'P1_L2_job02', '-', 'Template1.tdx', 'P1_L2_job02.tdx', '1', '2');
         
    -- Log the seed activity
    INSERT INTO activity_logs (user_email, user_name, activity_type, action, description, created_at)
    VALUES ('admin@apollotyres.com', 'System', 'System', 'Database Seeded', 'Sample data inserted for all protocols', NOW());
    
END $$;

-- Verify data insertion
SELECT 'Users:', COUNT(*) FROM users
UNION ALL
SELECT 'Projects:', COUNT(*) FROM projects
UNION ALL
SELECT 'MF62 Matrix:', COUNT(*) FROM mf62_project_data
UNION ALL
SELECT 'MF52 Matrix:', COUNT(*) FROM mf52_project_data
UNION ALL
SELECT 'FTire Matrix:', COUNT(*) FROM ftire_project_data
UNION ALL
SELECT 'CDTire Matrix:', COUNT(*) FROM cdtire_project_data
UNION ALL
SELECT 'Custom Matrix:', COUNT(*) FROM custom_project_data;