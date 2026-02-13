# scripts/supabase_db_setup.py

# SQL Queries for Supabase DB setup

# Create lender_interactions table
create_table_query = """
CREATE TABLE lender_interactions (
    id SERIAL PRIMARY KEY,
    lender_id INT NOT NULL,
    request_id INT NOT NULL,
    interaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    interaction_type VARCHAR(255),
    interaction_notes TEXT
);
"""

# Update loan_requests status values
update_loan_requests_query = """
UPDATE loan_requests
SET status = 'updated' -- Change this to the desired status
WHERE status IN ('pending', 'active'); -- Add conditions as necessary
"""

# Function to execute queries would go here