-- Drop existing objects if they exist
DROP TABLE IF EXISTS recipes;
DROP TYPE IF EXISTS recipe_state;
DROP TYPE IF EXISTS recipe_origin;

-- Create the enum types for state and origin
CREATE TYPE recipe_state AS ENUM ('to_test', 'approved', 'not_approved');
CREATE TYPE recipe_origin AS ENUM ('photo', 'text_ia', 'voice');

-- Create the recipes table
CREATE TABLE recipes (
    recipe_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    title TEXT NOT NULL,
    ingredients JSONB NOT NULL,
    steps JSONB NOT NULL,
    other_elements JSONB,
    state recipe_state NOT NULL DEFAULT 'to_test',
    origin recipe_origin NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()

);

-- Add indexes
CREATE INDEX recipes_user_id_idx ON recipes(user_id);
CREATE INDEX recipes_state_idx ON recipes(state);
CREATE INDEX recipes_created_at_idx ON recipes(created_at DESC);

-- Add Row Level Security (RLS) policies
ALTER TABLE recipes ENABLE ROW LEVEL SECURITY;

-- Policy for inserting: users can only insert their own recipes
CREATE POLICY insert_own_recipes ON recipes
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Policy for selecting: anyone can see all recipes
CREATE POLICY select_all_recipes ON recipes
    FOR SELECT
    USING (true);

-- Policy for updating: users can only update their own recipes
CREATE POLICY update_own_recipes ON recipes
    FOR UPDATE
    USING (auth.uid() = user_id);

-- Policy for deleting: users can only delete their own recipes
CREATE POLICY delete_own_recipes ON recipes
    FOR DELETE
    USING (auth.uid() = user_id);
