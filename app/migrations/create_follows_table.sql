-- Create follows table if it doesn't exist
create table if not exists public.follows (
    id uuid default gen_random_uuid() primary key,
    follower_id uuid references auth.users(id) on delete cascade,
    following_id uuid references auth.users(id) on delete cascade,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    unique(follower_id, following_id)
);

-- Drop existing policies if any
drop policy if exists "Enable insert for authenticated users following others" on public.follows;
drop policy if exists "Enable delete for users to unfollow" on public.follows;
drop policy if exists "Enable read access for authenticated users" on public.follows;

-- Make sure RLS is enabled
alter table public.follows enable row level security;

-- Create or update policies
create policy "Enable insert for authenticated users following others"
    on public.follows for insert
    with check (auth.role() = 'authenticated' and auth.uid() = follower_id);

create policy "Enable delete for users to unfollow"
    on public.follows for delete
    using (auth.role() = 'authenticated' and auth.uid() = follower_id);

create policy "Enable read access for authenticated users"
    on public.follows for select
    using (auth.role() = 'authenticated');

-- Create followers count function
create or replace function get_followers_count(user_id uuid)
returns bigint
language sql
security definer
set search_path = public
stable
as $$
    select count(*)
    from public.follows
    where following_id = user_id;
$$;

-- Create following count function
create or replace function get_following_count(user_id uuid)
returns bigint
language sql
security definer
set search_path = public
stable
as $$
    select count(*)
    from public.follows
    where follower_id = user_id;
$$;

-- Create function to check if user is following another user
create or replace function is_following(follower uuid, following uuid)
returns boolean
language sql
security definer
set search_path = public
stable
as $$
    select exists(
        select 1
        from public.follows
        where follower_id = follower
        and following_id = following
    );
$$;
