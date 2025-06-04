-- Create follows table if it doesn't exist
create table if not exists public.follows (
    id uuid default gen_random_uuid() primary key,
    follower_id uuid references auth.users(id) on delete cascade,
    following_id uuid references auth.users(id) on delete cascade,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    unique(follower_id, following_id)
);

-- Make sure RLS is enabled
alter table public.follows enable row level security;

CREATE POLICY "Allow all users to view all follows" 
ON public.follows 
FOR SELECT 
TO authenticated, anon 
USING (true);

CREATE POLICY "Allow users to insert their own follows" 
ON public.follows 
FOR INSERT 
TO authenticated 
WITH CHECK ((select auth.uid()) = follower_id);

CREATE POLICY "Allow users to delete their own follows" 
ON public.follows 
FOR DELETE 
TO authenticated 
USING ((select auth.uid()) = follower_id);

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
