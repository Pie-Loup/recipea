-- Fonction simple pour le follow
create or replace function public.handle_new_follow()
returns trigger as $$
begin
    -- Pour l'instant on ne fait rien de spécial, juste valider le follow
    return new;
end;
$$ language plpgsql security definer;

-- S'assurer que le trigger existe
drop trigger if exists on_new_follow on public.follows;
create trigger on_new_follow
    after insert on public.follows
    for each row
    execute function public.handle_new_follow();
