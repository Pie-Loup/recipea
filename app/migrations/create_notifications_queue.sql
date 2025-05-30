-- Create notifications queue table
create table if not exists public.notifications_queue (
    id uuid default gen_random_uuid() primary key,
    type text not null,
    follower_id uuid not null references auth.users(id) on delete cascade,
    followed_id uuid not null references auth.users(id) on delete cascade,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    processed_at timestamp with time zone,
    error text
);

-- Enable RLS
alter table public.notifications_queue enable row level security;

-- Allow backend service to access the queue
grant all on public.notifications_queue to postgres, service_role;

-- Update the handle_new_follow function to use the queue
create or replace function public.handle_new_follow()
returns trigger as $$
begin
    -- Insert into notifications queue
    insert into public.notifications_queue (type, follower_id, followed_id)
    values ('new_follow', new.follower_id, new.following_id);
    
    return new;
end;
$$ language plpgsql security definer;
