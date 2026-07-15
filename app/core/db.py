from supabase import create_client
from app.core.config import settings

# Same Supabase project as the gym admin dashboard — this console reads/writes
# the SAME gyms/admins/members/payments tables, just filtered to role='developer'.
supabase = create_client(settings.supabase_url, settings.supabase_key)
