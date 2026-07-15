-- Run this against the SAME Supabase project as the gym admin dashboard.
-- Idempotent — safe to run multiple times. Only ADDS columns, touches
-- nothing that admin-dashboard-backend already depends on.

alter table gyms add column if not exists owner_name text;
alter table gyms add column if not exists phone text;
alter table gyms add column if not exists contact_email text;
alter table gyms add column if not exists city text;
alter table gyms add column if not exists address text;
alter table gyms add column if not exists approx_members int;

-- admins.role already exists with default 'gym_admin' — this console just
-- filters/writes 'developer' as an additional value, no migration needed.
-- To create your OWN first developer login, run once (via psql or Supabase
-- SQL editor), then log in and change the password immediately:
--
-- insert into admins (email, password_hash, role, disabled)
-- values ('you@example.com', '<bcrypt-hash-here>', 'developer', false);
--
-- Generate the bcrypt hash with:
--   python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('yourpassword'))"
