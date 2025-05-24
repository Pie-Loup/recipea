
def get_recipe_transcription_prompt(transcription: str) -> str:
    """
    Returns a prompt for transcribing a text into a recipe format.
    This prompt is designed to extract ingredients, preparation steps, and any questions
    that might arise from the text.
    """

    return f"""
    Tu es un expert en transcription de texte vers recette. Voici un texte de recette. Peux-tu me retourner :
    - La liste des ingrédients (avec quantités si disponibles),
    - Les étapes de préparation, claires et numérotées,
    - Les questions éventuelles que tu pourrais te poser si des éléments manquent ou sont ambigus ?

    Voici le texte :
    ______________________________
    {transcription}
    ______________________________

    ✅ Exemple de sortie attendue :
    Ingrédients :
    - 200g de farine
    - 100g de sucre
    - 2 œufs
    - 1 sachet de levure chimique
    - 10cl de lait

    Étapes de la recette :

    1. Préchauffer le four à 180°C.
    2. Mélanger la farine, le sucre et la levure.
    3. Ajouter les œufs un à un, puis le lait.
    4. Verser la pâte dans un moule.
    5. Enfourner pendant 30 minutes.

    Questions éventuelles :
    - Quelle taille de moule utiliser ?
    - Faut-il beurrer le moule avant de verser la pâte ?
    - Peut-on ajouter un arôme (ex : vanille) ?
    """
