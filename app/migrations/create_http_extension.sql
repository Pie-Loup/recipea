-- Enable http schema access from public
create extension if not exists "pg_net";
grant usage on schema net to postgres, authenticated, anon;

-- Create the webhook call function
create or replace function public.handle_new_follow()
returns trigger as $$
declare
    follower_username text;
begin
    -- Get the follower's username
    select username into follower_username
    from public.profiles
    where id = new.follower_id;

    -- Send the notification using http_post from pg_net
    perform http_post(
        url := 'https://helping-pumped-gobbler.ngrok-free.app/notify',
        body := jsonb_build_object(
            'type', 'new_follow',
            'follower_id', new.follower_id,
            'followed_id', new.following_id,
            'follower_username', follower_username,
            'created_at', now()
        ),
        headers := jsonb_build_object(
            'Content-Type', 'application/json'
        )
    );
    
    return new;
end;
$$ language plpgsql security definer;
