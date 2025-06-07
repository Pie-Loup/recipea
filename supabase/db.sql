CREATE TYPE "state" AS ENUM (
  'to_test',
  'approved',
  'not_approved'
);

CREATE TYPE "status" AS ENUM (
  'draft',
  'public',
  'private'
);

CREATE TYPE "origin" AS ENUM (
  'text_ia',
  'photo',
  'voice'
);

CREATE TABLE "follows" (
  "id" serial PRIMARY KEY,
  "following_user_id" string,
  "followed_user_id" string,
  "created_at" timestamp,
  PRIMARY KEY ("following_user_id", "followed_user_id")
);

CREATE TABLE "profiles" (
  "id" serial PRIMARY KEY,
  "username" varchar,
  "picture_url" varchar,
  "created_at" timestamp
);

CREATE TABLE "posts" (
  "id" serial PRIMARY KEY,
  "user_id" string NOT NULL,
  "created_at" timestamp DEFAULT (now()),
  "updated_at" timestamp DEFAULT (now()),
  "recipe_id" string,
  "repost_of_post_id" string,
  "is_repost" boolean DEFAULT false
);

CREATE TABLE "post_pictures" (
  "id" serial PRIMARY KEY,
  "post_id" string NOT NULL,
  "url" varchar NOT NULL,
  "created_at" timestamp DEFAULT (now())
);

CREATE TABLE "recipes" (
  "id" serial PRIMARY KEY,
  "user_id" string NOT NULL,
  "title" varchar NOT NULL,
  "ingredients" jsonb NOT NULL,
  "steps" jsonb NOT NULL,
  "other_elements" jsonb NOT NULL,
  "state" state NOT NULL,
  "origin" origin NOT NULL,
  "status" status NOT NULL,
  "created_at" timestamp
);

CREATE TABLE "recipe_pictures" (
  "id" serial PRIMARY KEY,
  "recipe_id" string NOT NULL,
  "url" varchar NOT NULL,
  "created_at" timestamp DEFAULT (now())
);

CREATE TABLE "recipe_reactions" (
  "id" serial PRIMARY KEY,
  "recipe_id" string NOT NULL,
  "user_id" string NOT NULL,
  "reactions" enum NOT NULL,
  "created_at" timestamp DEFAULT (now())
);

CREATE TABLE "recipe_saves" (
  "id" serial PRIMARY KEY,
  "recipe_id" string NOT NULL,
  "user_id" string NOT NULL,
  "created_at" timestamp DEFAULT (now())
);

CREATE TABLE "comments" (
  "id" serial PRIMARY KEY,
  "user_id" string NOT NULL,
  "content" text NOT NULL,
  "post_id" string,
  "recipe_id" string,
  "parent_comment_id" string,
  "is_main_content" boolean DEFAULT false,
  "created_at" timestamp DEFAULT (now()),
  "updated_at" timestamp DEFAULT (now())
);

CREATE TABLE "comment_likes" (
  "id" serial PRIMARY KEY,
  "comment_id" string NOT NULL,
  "user_id" string NOT NULL,
  "created_at" timestamp DEFAULT (now())
);

CREATE TABLE "comment_mentions" (
  "id" serial PRIMARY KEY,
  "comment_id" string NOT NULL,
  "mentioned_user_id" string NOT NULL,
  "position_start" integer NOT NULL,
  "position_end" integer NOT NULL,
  "created_at" timestamp DEFAULT (now())
);

ALTER TABLE "follows" ADD FOREIGN KEY ("following_user_id") REFERENCES "profiles" ("id");

ALTER TABLE "follows" ADD FOREIGN KEY ("followed_user_id") REFERENCES "profiles" ("id");

ALTER TABLE "posts" ADD FOREIGN KEY ("user_id") REFERENCES "profiles" ("id");

ALTER TABLE "posts" ADD FOREIGN KEY ("recipe_id") REFERENCES "recipes" ("id");

ALTER TABLE "posts" ADD FOREIGN KEY ("repost_of_post_id") REFERENCES "posts" ("id");

ALTER TABLE "post_pictures" ADD FOREIGN KEY ("post_id") REFERENCES "posts" ("id");

ALTER TABLE "recipes" ADD FOREIGN KEY ("user_id") REFERENCES "profiles" ("id");

ALTER TABLE "recipe_pictures" ADD FOREIGN KEY ("recipe_id") REFERENCES "recipes" ("id");

ALTER TABLE "recipe_reactions" ADD FOREIGN KEY ("recipe_id") REFERENCES "recipes" ("id");

ALTER TABLE "recipe_reactions" ADD FOREIGN KEY ("user_id") REFERENCES "profiles" ("id");

ALTER TABLE "recipe_saves" ADD FOREIGN KEY ("recipe_id") REFERENCES "recipes" ("id");

ALTER TABLE "recipe_saves" ADD FOREIGN KEY ("user_id") REFERENCES "profiles" ("id");

ALTER TABLE "comments" ADD FOREIGN KEY ("user_id") REFERENCES "profiles" ("id");

ALTER TABLE "comments" ADD FOREIGN KEY ("post_id") REFERENCES "posts" ("id");

ALTER TABLE "comments" ADD FOREIGN KEY ("recipe_id") REFERENCES "recipes" ("id");

ALTER TABLE "comments" ADD FOREIGN KEY ("parent_comment_id") REFERENCES "comments" ("id");

ALTER TABLE "comment_likes" ADD FOREIGN KEY ("comment_id") REFERENCES "comments" ("id");

ALTER TABLE "comment_likes" ADD FOREIGN KEY ("user_id") REFERENCES "profiles" ("id");

ALTER TABLE "comment_mentions" ADD FOREIGN KEY ("comment_id") REFERENCES "comments" ("id");

ALTER TABLE "comment_mentions" ADD FOREIGN KEY ("mentioned_user_id") REFERENCES "profiles" ("id");

CREATE INDEX "idx_posts_user" ON "posts" ("user_id");

CREATE INDEX "idx_posts_repost" ON "posts" ("repost_of_post_id");

CREATE UNIQUE INDEX "idx_recipe_reactions_unique" ON "recipe_reactions" ("recipe_id", "user_id");

CREATE INDEX "idx_recipe_reactions_recipe" ON "recipe_reactions" ("recipe_id");

CREATE INDEX "idx_recipe_reactions_user" ON "recipe_reactions" ("user_id");

CREATE UNIQUE INDEX "idx_recipe_saves_unique" ON "recipe_saves" ("recipe_id", "user_id");

CREATE INDEX "idx_recipe_saves_recipe" ON "recipe_saves" ("recipe_id");

CREATE INDEX "idx_recipe_saves_user" ON "recipe_saves" ("user_id");

CREATE INDEX "idx_comments_post" ON "comments" ("post_id");

CREATE INDEX "idx_comments_recipe" ON "comments" ("recipe_id");

CREATE INDEX "idx_comments_parent" ON "comments" ("parent_comment_id");

CREATE INDEX "idx_comments_user" ON "comments" ("user_id");

CREATE UNIQUE INDEX "idx_comment_likes_unique" ON "comment_likes" ("comment_id", "user_id");

CREATE INDEX "idx_comment_likes_comment" ON "comment_likes" ("comment_id");

CREATE INDEX "idx_comment_likes_user" ON "comment_likes" ("user_id");

CREATE UNIQUE INDEX "idx_mentions_unique" ON "comment_mentions" ("comment_id", "mentioned_user_id", "position_start");

CREATE INDEX "idx_mentions_user" ON "comment_mentions" ("mentioned_user_id");

CREATE INDEX "idx_mentions_comment" ON "comment_mentions" ("comment_id");

COMMENT ON COLUMN "posts"."repost_of_post_id" IS 'NULL si ce n"est pas un repost';

COMMENT ON COLUMN "posts"."is_repost" IS 'true si c"est un repost';

COMMENT ON TABLE "comments" IS 'CHECK: (post_id IS NOT NULL AND recipe_id IS NULL) OR (post_id IS NULL AND recipe_id IS NOT NULL)';

COMMENT ON COLUMN "comments"."content" IS 'Contenu du commentaire ou du post principal';

COMMENT ON COLUMN "comments"."post_id" IS 'NULL si commentaire sur recette';

COMMENT ON COLUMN "comments"."recipe_id" IS 'NULL si commentaire sur post';

COMMENT ON COLUMN "comments"."is_main_content" IS 'true pour le contenu principal du post/recette';

COMMENT ON COLUMN "comment_mentions"."position_start" IS 'Position de @ dans le texte';

COMMENT ON COLUMN "comment_mentions"."position_end" IS 'Fin du username';
