prompt_template = """
Tu es un expert en structuration de recettes. Voici un clip audio de recette. Peux-tu me retourner :
- La liste des ingrédients (avec quantités si disponibles),
- Les étapes de préparation, claires et numérotées,
- Les questions éventuelles que tu pourrais te poser si des éléments manquent ou sont ambigus ?


  Merci de structurer la réponse en utilisant un json avec les clés suivantes :
  "ingredients", "steps", "questions"
  Exemple de réponse :
  {
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
      "questions": [
          "Quelle taille de moule utiliser ?",
          "Faut-il beurrer le moule avant de verser la pâte ?",
          "Peut-on ajouter un arôme (ex : vanille) ?"
      ]
  }

  Si les informations ne sont pas suffisantes ou si ce n'est pas un clip de recette, merci de me le signaler clairement dans la réponse.
  par exemple :
  {
      "ingredients": [],
      "steps": [],
      "questions": ["Ce clip ne semble pas être une recette."]
  }
"""
