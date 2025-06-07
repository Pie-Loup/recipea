-- Script SQL pour créer la relation entre recipes et profiles
-- À exécuter dans l'éditeur SQL de Supabase

-- 1. D'abord, vérifions la structure actuelle de la table recipes
-- (vous pouvez commenter cette ligne après vérification)
SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'recipes';

-- 2. Créer la contrainte de clé étrangère entre recipes.user_id et profiles.id
ALTER TABLE recipes 
ADD CONSTRAINT fk_recipes_user_id 
FOREIGN KEY (user_id) REFERENCES profiles(id) 
ON DELETE CASCADE ON UPDATE CASCADE;

-- 3. Créer un index pour améliorer les performances des jointures
CREATE INDEX IF NOT EXISTS idx_recipes_user_id ON recipes(user_id);

-- 4. Vérifier que la relation a été créée correctement
SELECT 
  tc.constraint_name, 
  tc.table_name, 
  kcu.column_name, 
  ccu.table_name AS foreign_table_name,
  ccu.column_name AS foreign_column_name 
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = 'recipes';
