-- Update RLS policies for push_subscriptions table
alter table public.push_subscriptions enable row level security;

-- Drop existing policies if any
drop policy if exists "Allow user to manage their own subscriptions" on public.push_subscriptions;

-- Create policies
create policy "Allow user to manage their own subscriptions"
    on public.push_subscriptions
    for all -- this means INSERT, SELECT, UPDATE, and DELETE
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);
-- Create a policy that allows service role to bypass RLS
create policy "Allow service role access"
    on public.push_subscriptions
    for all
    to service_role
    using (true)
    with check (true);

-- Create a policy for authenticated users (frontend clients)
create policy "Allow user to manage their own subscriptions"
    on public.push_subscriptions
    for all
    to authenticated
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

-- Enable anon and authenticated roles to use the table
grant usage on schema public to anon, authenticated, service_role;
grant all on public.push_subscriptions to anon, authenticated, service_role;
