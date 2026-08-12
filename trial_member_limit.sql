-- Enforces: a gym with subscription_status = 'trial' cannot have more
-- than 30 members. This runs INSIDE Postgres, at insert time, so it
-- applies no matter which application inserts the row — your gym-admin
-- dashboard's "Add Member" flow, this dev dashboard, a future app,
-- anything. I don't have the gym-admin dashboard's own source code in
-- this conversation, so I can't add a friendly in-app message there —
-- but this guarantees the 31st member is rejected regardless, and
-- whatever app attempted it will receive a Postgres error back that it
-- can choose to surface nicely.
--
-- Safe to re-run (drops and recreates both objects first).

create or replace function enforce_trial_member_limit()
returns trigger as $$
declare
  gym_status text;
  current_count integer;
begin
  select subscription_status into gym_status from gyms where id = new.gym_id;

  if gym_status = 'trial' then
    select count(*) into current_count from members where gym_id = new.gym_id;
    if current_count >= 30 then
      raise exception 'Trial gyms are limited to 30 members — upgrade the gym''s plan to add more.'
        using errcode = 'P0001';
    end if;
  end if;

  return new;
end;
$$ language plpgsql;

drop trigger if exists trial_member_limit on members;

create trigger trial_member_limit
before insert on members
for each row execute function enforce_trial_member_limit();
