# create_tables.py
from app import app, db

# Pour exécuter db.create_all(), nous avons besoin du contexte de l'application Flask
with app.app_context():
    print("Création des tables de la base de données...")
    try:
        db.create_all()
        print("Tables créées avec succès (ou déjà existantes).")
        # Optionnel : Ajouter des données initiales si nécessaire
        # from app import Fabricant, Type
        # if not Fabricant.query.first(): # Ajoute seulement si la table est vide
        #     print("Ajout des fabricants initiaux...")
        #     db.session.add_all([Fabricant(nom='Dell'), Fabricant(nom='HP'), Fabricant(nom='Lenovo')])
        #     db.session.commit()
        # if not Type.query.first(): # Ajoute seulement si la table est vide
        #     print("Ajout des types initiaux...")
        #     db.session.add_all([Type(nom='Ordinateur portable'), Type(nom='Serveur'), Type(nom='Imprimante')])
        #     db.session.commit()
        #     print("Données initiales ajoutées.")

    except Exception as e:
        print(f"Erreur lors de la création des tables : {e}")

print("Script terminé.")
