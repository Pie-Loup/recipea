prompt_voice = """
Tu es un expert en structuration de recettes. Voici un clip audio de recette. Peux-tu me retourner :
- Un titre pour la recette,
- La liste des ingrédients (avec quantités si disponibles),
- Les étapes de préparation, claires et numérotées,
- Le temps de préparation (string, ex: "30 minutes"),
- Le temps de cuisson (string, ex: "45 minutes"),
- La quantité/nombre de personnes (string, ex: "4 personnes"),
- La difficulté de 1 à 4 (1=très facile, 2=facile, 3=moyen, 4=difficile),
- D'autres éléments pertinents de la recette (ex : température, matériel, etc.),
- Les questions éventuelles que tu pourrais te poser si des éléments manquent ou sont ambigus ?

Merci de structurer la réponse en utilisant un json avec les clés suivantes :
"title", "ingredients", "steps", "preparation_time", "cooking_time", "quantity", "difficulty", "other_elements", "questions", "is_recipe"

Exemple de réponse :
{
    "title": "Gâteau au yaourt",
    "ingredients": [
        "200g de farine",
        "100g de sucre",
        "2 œufs",
        "1 sachet de levure chimique",
        "10cl de lait"
    ],
    "steps": [
        "1. Préchauffer le four à 180°C.",
        "2. Mélanger la farine, le sucre et la levure.",
        "3. Ajouter les œufs un à un, puis le lait.",
        "4. Verser la pâte dans un moule.",
        "5. Enfourner pendant 30 minutes."
    ],
    "preparation_time": "15 minutes",
    "cooking_time": "30 minutes",
    "quantity": "4 personnes",
    "difficulty": 2,
    "other_elements": [
        "Température du four : 180°C",
        "Moule rond de 24cm"
    ],
    "questions": [
        "Quelle taille de moule utiliser ?",
        "Faut-il beurrer le moule avant de verser la pâte ?",
        "Peut-on ajouter un arôme (ex : vanille) ?"
    ],
    "is_recipe": true
}

Si les informations ne sont pas suffisantes ou si ce n'est pas un clip de recette, merci de me le signaler clairement dans la réponse.
par exemple :
{
    "title": "",
    "ingredients": [],
    "steps": [],
    "preparation_time": null,
    "cooking_time": null,
    "quantity": null,
    "difficulty": null,
    "other_elements": [],
    "questions": [],
    "is_recipe": false
}
  }
"""

prompt_photo = """
Tu es un expert en structuration de recettes. Voici une photo de recette. Peux-tu me retourner :
- Un titre pour la recette,
- La liste des ingrédients (avec quantités si disponibles),
- Les étapes de préparation, claires et numérotées,
- Le temps de préparation (string, ex: "30 minutes"),
- Le temps de cuisson (string, ex: "45 minutes"),
- La quantité/nombre de personnes (string, ex: "4 personnes"),
- La difficulté de 1 à 4 (1=très facile, 2=facile, 3=moyen, 4=difficile),
- D'autres éléments pertinents de la recette (ex : température, matériel, etc.),
- Les questions éventuelles que tu pourrais te poser si des éléments manquent ou sont ambigus ?

Merci de structurer la réponse en utilisant un json avec les clés suivantes :
"title", "ingredients", "steps", "preparation_time", "cooking_time", "quantity", "difficulty", "other_elements", "questions", "is_recipe"

Exemple de réponse :
{
    "title": "Gâteau au yaourt",
    "ingredients": [
        "200g de farine",
        "100g de sucre",
        "2 œufs",
        "1 sachet de levure chimique",
        "10cl de lait"
    ],
    "steps": [
        "1. Préchauffer le four à 180°C.",
        "2. Mélanger la farine, le sucre et la levure.",
        "3. Ajouter les œufs un à un, puis le lait.",
        "4. Verser la pâte dans un moule.",
        "5. Enfourner pendant 30 minutes."
    ],
    "preparation_time": "15 minutes",
    "cooking_time": "30 minutes",
    "quantity": "4 personnes",
    "difficulty": 2,
    "other_elements": [
        "Température du four : 180°C",
        "Moule rond de 24cm"
    ],
    "questions": [
        "Quelle taille de moule utiliser ?",
        "Faut-il beurrer le moule avant de verser la pâte ?",
        "Peut-on ajouter un arôme (ex : vanille) ?"
    ],
    "is_recipe": true
}

Si les informations ne sont pas suffisantes ou si ce n'est pas une photo de recette, merci de me le signaler clairement dans la réponse.
par exemple :
{
    "title": "",
    "ingredients": [],
    "steps": [],
    "preparation_time": null,
    "cooking_time": null,
    "quantity": null,
    "difficulty": null,
    "other_elements": [],
    "questions": [],
    "is_recipe": false
}
"""

prompt_text = """
Tu es un expert en proposition de recettes. Voici une demande de recette. Peux-tu me retourner :
- Un titre pour la recette,
- La liste des ingrédients (avec quantités si disponibles),
- Les étapes de préparation, claires et numérotées,
- Le temps de préparation (string, ex: "30 minutes"),
- Le temps de cuisson (string, ex: "45 minutes"),
- La quantité/nombre de personnes (string, ex: "4 personnes"),
- La difficulté de 1 à 4 (1=très facile, 2=facile, 3=moyen, 4=difficile),
- D'autres éléments pertinents de la recette (ex : température, matériel, etc.),
- Des questions pour clarifier les préférences ou options de la recette,
- Un indicateur si c'est bien une recette valide.

Merci de structurer la réponse en utilisant un json avec les clés suivantes :
"title", "ingredients", "steps", "preparation_time", "cooking_time", "quantity", "difficulty", "other_elements", "questions", "is_recipe"

Exemple de réponse :
{
    "title": "Gâteau au yaourt",
    "ingredients": [
        "200g de farine",
        "100g de sucre",
        "2 œufs",
        "1 sachet de levure chimique",
        "10cl de lait"
    ],
    "steps": [
        "1. Préchauffer le four à 180°C.",
        "2. Mélanger la farine, le sucre et la levure.",
        "3. Ajouter les œufs un à un, puis le lait.",
        "4. Verser la pâte dans un moule.",
        "5. Enfourner pendant 30 minutes."
    ],
    "preparation_time": "15 minutes",
    "cooking_time": "30 minutes",
    "quantity": "4 personnes",
    "difficulty": 2,
    "other_elements": [
        "Température du four : 180°C",
        "Moule rond de 24cm"
    ],
    "questions": [
        "Est-ce que tu préfères un gâteau moelleux ou croustillant ?",
        "Quelle est la taille du moule que tu souhaites utiliser ?",
        "As-tu des allergies ou des restrictions alimentaires ?"
    ],
    "is_recipe": true
}

Si les informations ne sont pas suffisantes ou si ce n'est pas une demande de recette, merci de me le signaler clairement dans la réponse.
par exemple :
{
    "title": "",
    "ingredients": [],
    "steps": [],
    "preparation_time": null,
    "cooking_time": null,
    "quantity": null,
    "difficulty": null,
    "other_elements": [],
    "questions": [],
    "is_recipe": false
}
"""

prompt_update = """
Tu es un expert en proposition de recettes. Voici une proposition de recette. Peux-tu adapter la recette en fonction de la demande jointe ?:

  Merci de structurer la réponse en utilisant un json avec les clés suivantes :
  "title", "ingredients", "steps", "other_elements", "questions", "is_recipe"
  Exemple de réponse :
  {
      "title": "Gâteau au yaourt",
      "ingredients": [
          "200g de farine",
          "100g de sucre",
          "2 œufs",
          "1 sachet de levure chimique",
          "10cl de lait"
      ],
      "steps": [
          "1. Préchauffer le four à 180°C.",
          "2. Mélanger la farine, le sucre et la levure.",
          "3. Ajouter les œufs un à un, puis le lait.",
          "4. Verser la pâte dans un moule.",
          "5. Enfourner pendant 30 minutes."
      ],
      "other_elements": [
          "Pour 4 personnes",
          "Temps de préparation : 15 minutes",
          "Temps de cuisson : 30 minutes",
          "Température du four : 180°C"
      ],
      "questions": [
          "Est-ce que tu préfères un gâteau moelleux ou croustillant ?",
          "Quelle est la taille du moule que tu souhaites utiliser ?",
          "As-tu des allergies ou des restrictions alimentaires ?"
      ],
      "is_recipe": true
  }

  Si les informations ne sont pas suffisantes ou si ce n'est pas une demande de recette, merci de me le signaler clairement dans la réponse.
  par exemple :
  {
      "title": "",
      "ingredients": [],
      "steps": [],
      "other_elements": [],
      "questions": [],
      "is_recipe": false
  }
"""
