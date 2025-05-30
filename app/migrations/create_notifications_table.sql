-- Create notifications table
create table if not exists public.notifications (
    id uuid default gen_random_uuid() primary key,
    user_id uuid references auth.users(id) on delete cascade,
    actor_id uuid references auth.users(id) on delete cascade,
    type text not null,
    data jsonb,
    read boolean default false,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS
alter table public.notifications enable row level security;

-- Policies
create policy "Users can view their own notifications"
    on public.notifications for select
    using (auth.uid() = user_id);

create policy "Users can update their own notifications"
    on public.notifications for update
    using (auth.uid() = user_id);

-- Update the handle_new_follow function to insert notifications
create or replace function public.handle_new_follow()
returns trigger as $$
begin
    -- Insert into notifications table
    insert into public.notifications (user_id, actor_id, type, data)
    values (
        new.following_id,
        new.follower_id,
        'new_follow',
        jsonb_build_object(
            'follower_id', new.follower_id,
            'following_id', new.following_id
        )
    );
    
    -- Send push notification via backend webhook
    perform net.http_post(
        current_setting('app.push_notification_webhook_url'),
        jsonb_build_object(
            'type', 'new_follow',
            'follower_id', new.follower_id,
            'followed_id', new.following_id,
            'created_at', now()
        )::text,
        'application/json'
    );
    
    return new;
end;
$$ language plpgsql security definer;
