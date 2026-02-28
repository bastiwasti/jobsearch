-- Create read-only user for pgweb
CREATE USER jobsearch_readonly WITH PASSWORD 'r3RH5VDnNjetajGRE/BaAH2k77BcsFtG';

-- Grant connection to database
GRANT CONNECT ON DATABASE jobsearch TO jobsearch_readonly;

-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO jobsearch_readonly;

-- Grant SELECT on all existing tables
GRANT SELECT ON ALL TABLES IN SCHEMA public TO jobsearch_readonly;

-- Grant SELECT on future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO jobsearch_readonly;
