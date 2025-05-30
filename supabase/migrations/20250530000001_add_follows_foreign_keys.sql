-- Add foreign key constraints for the follows table
ALTER TABLE follows
ADD CONSTRAINT follows_follower_id_fkey
FOREIGN KEY (follower_id)
REFERENCES profiles(id)
ON DELETE CASCADE;

ALTER TABLE follows
ADD CONSTRAINT follows_following_id_fkey
FOREIGN KEY (following_id)
REFERENCES profiles(id)
ON DELETE CASCADE;
