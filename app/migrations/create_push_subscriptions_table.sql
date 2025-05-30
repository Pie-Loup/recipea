-- Create push_subscriptions table
create table if not exists public.push_subscriptions (
    id uuid default gen_random_uuid() primary key,
    user_id uuid references auth.users(id) on delete cascade,
    endpoint text not null,
    p256dh text not null,
    auth text not null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    updated_at timestamp with time zone default timezone('utc'::text, now()) not null,
    unique(user_id, endpoint)
);

-- Enable RLS
alter table public.push_subscriptions enable row level security;

-- Policies
create policy "Users can insert their own push subscriptions"
    on public.push_subscriptions for insert
    with check (auth.uid() = user_id);

create policy "Users can view their own push subscriptions"
    on public.push_subscriptions for select
    using (auth.uid() = user_id);

create policy "Users can update their own push subscriptions"
    on public.push_subscriptions for update
    using (auth.uid() = user_id);

create policy "Users can delete their own push subscriptions"
    on public.push_subscriptions for delete
    using (auth.uid() = user_id);

-- Function to handle following notifications
create or replace function public.handle_new_follow()
returns trigger as $$
begin
    -- Insert into a notifications table if you want to keep track of them
    -- You would need to create this table separately
    
    -- The notification will be sent via your backend webhook
    -- This function just ensures the webhook is called
    perform net.http_post(
        'https://your-backend-url.com/notify',  -- You'll need to update this URL
        jsonb_build_object(
            'type', 'new_follow',
            'follower_id', auth.uid(),
            'followed_id', new.following_id,
            'created_at', now()
        )::text,
        'application/json'
    );
    
    return new;
end;
$$ language plpgsql security definer;

-- Trigger for new follows
drop trigger if exists on_new_follow on public.follows;
create trigger on_new_follow
    after insert on public.follows
    for each row
    execute function public.handle_new_follow();
