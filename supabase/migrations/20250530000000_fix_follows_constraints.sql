-- First, let's drop the individual unique constraints
ALTER TABLE follows DROP CONSTRAINT IF EXISTS follows_pkey CASCADE;
ALTER TABLE follows DROP CONSTRAINT IF EXISTS follows_follower_id_key CASCADE;
ALTER TABLE follows DROP CONSTRAINT IF EXISTS follows_following_id_key CASCADE;

-- Recreate the primary key constraint
ALTER TABLE follows 
ADD CONSTRAINT follows_pkey PRIMARY KEY (id);

-- Create the composite unique constraint
ALTER TABLE follows 
ADD CONSTRAINT follows_follower_following_unique 
UNIQUE (follower_id, following_id);
