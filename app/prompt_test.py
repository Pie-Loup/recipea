transcription_prompt = """
La recette pâte tomates cerises feta, c'est une petite recette d'été assez sympa, pas trop compliquée à faire,
et ça permet aussi de faire pour beaucoup de monde à la fois.
Donc c'est une bonne petite recette d'été.
alors pour cette recette j'ai pas les quantités exactes de tomates cerises mais là disons que
pour pour on va prendre environ 150 g de tomates cerises par personne donc pour six personnes on
va faire environ 800 g de tomates cerises on met environ 125 g de pâte par personne et puis on met
un bloc de feta pour deux à trois voire quatre personnes beaucoup de basilic et de l'huile
d'olive et puis on va prendre ici quatre oignons rouges
Alors pour commencer c'est assez simple on prend les tomates cerises et puis on va les laver les unes après les autres
ou tout ensemble
Donc là je les prends, je les mets dans ma passoire
Une fois qu'on les a lavé on va les couper en deux, c'est pas très compliqué
La petite astuce c'est aussi d'enlever toutes les petites branches et les petits feuillets des tomates cerises
puisqu'on n'en aura pas besoin pour les cuire.
Donc il suffit de les rincer, de les égoutter et après on va les couper en deux et les disposer dans un grand plat.
Donc avant de les disposer on va les sécher dans un petit torchon pour ne pas mélanger l'huile et l'eau.
ensuite on vient couper les oignons rouges en lamelles
on dispose les tomates avec de l'huile des oignons rouges dans le plat
on met un petit peu de sel, de poivre, on peut être généreux sur le poivre
et on met les feta par dessus et on enfourne à 180° pendant une bonne heure
15-20 minutes avant la fin de la cuisson, ce qu'on vient faire c'est qu'on vient faire
bouillir de l'eau et mettre des pâtes à gratin dedans qu'on cuit al dente
Ensuite on égoutte les pâtes, on garde l'eau de la cuisson c'est très important
et on vient mettre les pâtes dans le plat à gratin avec les tomates cerises
qui sont cuites. On sort ça du four et on met les pâtes dedans. On mélange et on
rajoute de l'eau de cuisson jusqu'à former une pâte, une sauce pour les pâtes.
voilà quand on est satisfait de la consistance ensuite ce qu'on vient faire
c'est qu'on on rajoute plein de basilic dedans on peut mettre ça dans un plat ou
laisser dans le plat gratin d'ailleurs et servir bien chaud la dernière astuce
c'est que ce plat se mange aussi froid donc les restes sont excellents en
salade
"""

prompt_text = """
Tu es un expert en transcription de texte vers recette. Voici un texte de recette. Peux-tu me retourner :
- La liste des ingrédients (avec quantités si disponibles),
- Les étapes de préparation, claires et numérotées,
- Les questions éventuelles que tu pourrais te poser si des éléments manquent ou sont ambigus ?

Voici le texte :
______________________________

La recette pâte tomates cerises feta, c'est une petite recette d'été assez sympa, pas trop compliquée à faire,
et ça permet aussi de faire pour beaucoup de monde à la fois.
Donc c'est une bonne petite recette d'été.
alors pour cette recette j'ai pas les quantités exactes de tomates cerises mais là disons que
pour pour on va prendre environ 150 g de tomates cerises par personne donc pour six personnes on
va faire environ 800 g de tomates cerises on met environ 125 g de pâte par personne et puis on met
un bloc de feta pour deux à trois voire quatre personnes beaucoup de basilic et de l'huile
d'olive et puis on va prendre ici quatre oignons rouges
Alors pour commencer c'est assez simple on prend les tomates cerises et puis on va les laver les unes après les autres
ou tout ensemble
Donc là je les prends, je les mets dans ma passoire
Une fois qu'on les a lavé on va les couper en deux, c'est pas très compliqué
La petite astuce c'est aussi d'enlever toutes les petites branches et les petits feuillets des tomates cerises
puisqu'on n'en aura pas besoin pour les cuire.
Donc il suffit de les rincer, de les égoutter et après on va les couper en deux et les disposer dans un grand plat.
Donc avant de les disposer on va les sécher dans un petit torchon pour ne pas mélanger l'huile et l'eau.
ensuite on vient couper les oignons rouges en lamelles
on dispose les tomates avec de l'huile des oignons rouges dans le plat
on met un petit peu de sel, de poivre, on peut être généreux sur le poivre
et on met les feta par dessus et on enfourne à 180° pendant une bonne heure
15-20 minutes avant la fin de la cuisson, ce qu'on vient faire c'est qu'on vient faire
bouillir de l'eau et mettre des pâtes à gratin dedans qu'on cuit al dente
Ensuite on égoutte les pâtes, on garde l'eau de la cuisson c'est très important
et on vient mettre les pâtes dans le plat à gratin avec les tomates cerises
qui sont cuites. On sort ça du four et on met les pâtes dedans. On mélange et on
rajoute de l'eau de cuisson jusqu'à former une pâte, une sauce pour les pâtes.
voilà quand on est satisfait de la consistance ensuite ce qu'on vient faire
c'est qu'on on rajoute plein de basilic dedans on peut mettre ça dans un plat ou
laisser dans le plat gratin d'ailleurs et servir bien chaud la dernière astuce
c'est que ce plat se mange aussi froid donc les restes sont excellents en
salade

______________________________
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
"""