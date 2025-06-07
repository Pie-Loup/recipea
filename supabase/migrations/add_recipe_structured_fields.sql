-- Migration pour ajouter les champs structurés aux recettes
-- Temps de préparation, temps de cuisson, quantité et difficulté

-- Ajouter les nouveaux champs à la table recipes
ALTER TABLE recipes 
ADD COLUMN IF NOT EXISTS preparation_time VARCHAR(255),
ADD COLUMN IF NOT EXISTS cooking_time VARCHAR(255),
ADD COLUMN IF NOT EXISTS quantity VARCHAR(255),
ADD COLUMN IF NOT EXISTS difficulty INTEGER;

-- Ajouter des contraintes pour la difficulté (entre 1 et 4)
ALTER TABLE recipes 
ADD CONSTRAINT check_difficulty_range 
CHECK (difficulty IS NULL OR (difficulty >= 1 AND difficulty <= 4));

-- Ajouter des commentaires pour documenter les champs
COMMENT ON COLUMN recipes.preparation_time IS 'Temps de préparation en string (ex: "30 minutes")';
COMMENT ON COLUMN recipes.cooking_time IS 'Temps de cuisson en string (ex: "45 minutes")';
COMMENT ON COLUMN recipes.quantity IS 'Quantité/nombre de personnes en string (ex: "4 personnes")';
COMMENT ON COLUMN recipes.difficulty IS 'Difficulté de 1 à 4';

-- Créer des index pour améliorer les performances de recherche
CREATE INDEX IF NOT EXISTS idx_recipes_difficulty ON recipes(difficulty);
CREATE INDEX IF NOT EXISTS idx_recipes_preparation_time ON recipes(preparation_time);
CREATE INDEX IF NOT EXISTS idx_recipes_cooking_time ON recipes(cooking_time);
