from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps # Pour le décorateur login_required
import os # Pour générer une SECRET_KEY si non définie
from collections import defaultdict # Importer defaultdict

from extensions import db # Import shared db instance
from models import Arrondissement, Departement, Bureau, Utilisateur, Fabricant, Type, Modele # Import new models

app = Flask(__name__)
# Configuration
# IMPORTANT: Changez cette clé en production! Utilisez os.urandom(24)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'une_cle_secrete_tres_difficile_a_deviner')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Identifiants Admin (NON SECURISE - À remplacer par une vraie gestion utilisateurs)
app.config['ADMIN_USERNAME'] = 'admin'
app.config['ADMIN_PASSWORD'] = 'password' # Changez ceci !

db.init_app(app) # Initialize db with the app

# --- Décorateur de Login --- 
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Routes Publiques ---
@app.route('/')
def index():
    """Affiche la liste publique des modèles, groupés par type."""
    # Récupérer tous les types pour pouvoir les afficher même s'ils n'ont pas de modèles
    all_types = Type.query.order_by(Type.nom).all()
    # Récupérer tous les modèles avec leurs informations de type et fabricant préchargées
    all_models = Modele.query.options(db.joinedload(Modele.type), db.joinedload(Modele.fabricant)).order_by(Modele.type_id, Modele.nom).all()

    # Grouper les modèles par type
    models_by_type = defaultdict(list)
    for model in all_models:
        models_by_type[model.type].append(model)

    # Créer une liste ordonnée pour le template, incluant les types sans modèles
    grouped_data = []
    for type_obj in all_types:
        grouped_data.append({
            'type': type_obj,
            'models': models_by_type.get(type_obj, []) # Utiliser get pour gérer les types sans modèles
        })

    # Renvoyer les données groupées au template
    return render_template('index.html', grouped_data=grouped_data)

# --- Routes pour la gestion des Modèles (Maintenant sous Admin) ---
@app.route('/admin/add_model', methods=['GET', 'POST'])
@login_required
def add_model():
    if request.method == 'POST':
        nom = request.form['nom']
        fabricant_id_str = request.form['fabricant_id']
        type_id_str = request.form['type_id']
        
        # Vérifier si les ID sont valides et convertir en entier
        try:
            fabricant_id = int(fabricant_id_str)
            type_id = int(type_id_str)
            fabricant = Fabricant.query.get(fabricant_id)
            type_item = Type.query.get(type_id)
        except ValueError:
            flash('ID de Fabricant ou de Type invalide.', 'danger')
            fabricant = None
            type_item = None
        
        if not nom or not fabricant or not type_item:
            flash('Erreur: Nom, Fabricant et Type valides sont requis.', 'danger')
            # Recharger les données pour le formulaire
            fabricants_all = Fabricant.query.order_by(Fabricant.nom).all()
            types_all = Type.query.order_by(Type.nom).all()
            return render_template('add_model.html', fabricants=fabricants_all, types=types_all)

        # Utiliser les ID convertis en entier
        nouveau_modele = Modele(nom=nom, fabricant_id=fabricant_id, type_id=type_id)
        try:
            db.session.add(nouveau_modele)
            db.session.commit()
            flash('Modèle ajouté avec succès!', 'success')
            return redirect(url_for('index')) # Rediriger vers la page d'accueil
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de l\'ajout du modèle: {e}', 'danger')

    # Si GET ou si erreur POST
    fabricants = Fabricant.query.order_by(Fabricant.nom).all()
    types = Type.query.order_by(Type.nom).all()
    return render_template('add_model.html', fabricants=fabricants, types=types)

@app.route('/admin/modele/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_edit_modele(id):
    modele_a_modifier = db.get_or_404(Modele, id)
    if request.method == 'POST':
        nom = request.form.get('nom')
        fabricant_id_str = request.form.get('fabricant_id')
        type_id_str = request.form.get('type_id')

        if not nom or not fabricant_id_str or not type_id_str:
            flash('Nom, Fabricant et Type sont requis.', 'danger')
        else:
            try:
                fabricant_id = int(fabricant_id_str)
                type_id = int(type_id_str)
                
                fabricant = Fabricant.query.get(fabricant_id)
                type_item = Type.query.get(type_id)

                if not fabricant or not type_item:
                    flash('Fabricant ou Type invalide.', 'danger')
                else:
                    modele_a_modifier.nom = nom
                    modele_a_modifier.fabricant_id = fabricant_id
                    modele_a_modifier.type_id = type_id
                    db.session.commit()
                    flash('Modèle mis à jour avec succès!', 'success')
                    return redirect(url_for('index')) # Redirect to the main index page
            except ValueError:
                flash('ID de Fabricant ou de Type invalide.', 'danger')
            except Exception as e:
                db.session.rollback()
                flash(f'Erreur lors de la mise à jour du modèle: {e}', 'danger')
        
    # For GET request or if POST had an error, re-render the form
    fabricants = Fabricant.query.order_by(Fabricant.nom).all()
    types = Type.query.order_by(Type.nom).all()
    return render_template('edit_model.html', modele=modele_a_modifier, fabricants=fabricants, types=types)

@app.route('/admin/modele/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_modele(id):
    modele_a_supprimer = db.get_or_404(Modele, id)
    try:
        db.session.delete(modele_a_supprimer)
        db.session.commit()
        flash(f'Modèle "{modele_a_supprimer.nom}" supprimé avec succès.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression du modèle: {e}', 'danger')
    return redirect(url_for('index')) # Redirect to the main index page

# --- Routes Administration --- 

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # Vérification (NON SECURISEE)
        if username == app.config['ADMIN_USERNAME'] and password == app.config['ADMIN_PASSWORD']:
            session['logged_in'] = True
            flash('Connexion réussie!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Identifiants incorrects.', 'danger')
    # Si GET ou échec de login, afficher le formulaire
    return render_template('admin_login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    session.pop('logged_in', None)
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    """Page d'accueil de l'administration."""
    return render_template('admin_dashboard.html')

# --- CRUD Fabricants ---
@app.route('/admin/fabricants', methods=['GET', 'POST'])
@login_required
def admin_fabricants():
    if request.method == 'POST': # Ajout d'un nouveau fabricant
        nom = request.form.get('nom')
        if nom:
            existing = Fabricant.query.filter_by(nom=nom).first()
            if not existing:
                nouveau_fabricant = Fabricant(nom=nom)
                db.session.add(nouveau_fabricant)
                db.session.commit()
                flash(f'Fabricant "{nom}" ajouté.', 'success')
            else:
                flash(f'Le fabricant "{nom}" existe déjà.', 'warning')
        else:
            flash('Le nom du fabricant est requis.', 'danger')
        return redirect(url_for('admin_fabricants')) # Recharge la page
    
    # Affichage de la liste (GET)
    tous_fabricants = Fabricant.query.order_by(Fabricant.nom).all()
    return render_template('admin_fabricants.html', fabricants=tous_fabricants)

@app.route('/admin/fabricant/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_edit_fabricant(id):
    fabricant_a_modifier = db.get_or_404(Fabricant, id)
    if request.method == 'POST':
        nouveau_nom = request.form.get('nom')
        if nouveau_nom and nouveau_nom != fabricant_a_modifier.nom:
            # Vérifier si le nouveau nom existe déjà (sauf pour l'enregistrement actuel)
            existing = Fabricant.query.filter(Fabricant.nom == nouveau_nom, Fabricant.id != id).first()
            if not existing:
                fabricant_a_modifier.nom = nouveau_nom
                db.session.commit()
                flash('Fabricant mis à jour.', 'success')
                return redirect(url_for('admin_fabricants'))
            else:
                flash(f'Le nom "{nouveau_nom}" est déjà utilisé par un autre fabricant.', 'danger')
        elif not nouveau_nom:
            flash('Le nom ne peut pas être vide.', 'danger')
        else: # Nom inchangé
             return redirect(url_for('admin_fabricants'))

    # Affichage du formulaire pré-rempli (GET)
    return render_template('admin_edit_fabricant.html', fabricant=fabricant_a_modifier)

@app.route('/admin/fabricant/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_fabricant(id):
    fabricant_a_supprimer = db.get_or_404(Fabricant, id)
    # Vérifier si des modèles utilisent ce fabricant (optionnel mais recommandé)
    if fabricant_a_supprimer.modeles:
        flash(f'Impossible de supprimer "{fabricant_a_supprimer.nom}". Des modèles l\'utilisent.', 'danger')
    else:
        db.session.delete(fabricant_a_supprimer)
        db.session.commit()
        flash(f'Fabricant "{fabricant_a_supprimer.nom}" supprimé.', 'success')
    return redirect(url_for('admin_fabricants'))

# --- CRUD Types ---
@app.route('/admin/types', methods=['GET', 'POST'])
@login_required
def admin_types():
    if request.method == 'POST': # Ajout
        nom = request.form.get('nom')
        if nom:
            existing = Type.query.filter_by(nom=nom).first()
            if not existing:
                nouveau_type = Type(nom=nom)
                db.session.add(nouveau_type)
                db.session.commit()
                flash(f'Type "{nom}" ajouté.', 'success')
            else:
                 flash(f'Le type "{nom}" existe déjà.', 'warning')
        else:
            flash('Le nom du type est requis.', 'danger')
        return redirect(url_for('admin_types'))
    
    # Affichage liste (GET)
    tous_types = Type.query.order_by(Type.nom).all()
    return render_template('admin_types.html', types=tous_types)

@app.route('/admin/type/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_edit_type(id):
    type_a_modifier = db.get_or_404(Type, id)
    if request.method == 'POST':
        nouveau_nom = request.form.get('nom')
        if nouveau_nom and nouveau_nom != type_a_modifier.nom:
            existing = Type.query.filter(Type.nom == nouveau_nom, Type.id != id).first()
            if not existing:
                type_a_modifier.nom = nouveau_nom
                db.session.commit()
                flash('Type mis à jour.', 'success')
                return redirect(url_for('admin_types'))
            else:
                 flash(f'Le nom "{nouveau_nom}" est déjà utilisé.', 'danger')
        elif not nouveau_nom:
             flash('Le nom ne peut pas être vide.', 'danger')
        else:
             return redirect(url_for('admin_types'))

    # Affichage formulaire (GET)
    return render_template('admin_edit_type.html', type=type_a_modifier)

@app.route('/admin/type/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_type(id):
    type_a_supprimer = db.get_or_404(Type, id)
    try:
        # Vérifier si le type est utilisé par des modèles
        modeles_utilisant = Modele.query.filter_by(type_id=id).count()
        if modeles_utilisant > 0:
             flash('Impossible de supprimer ce type car il est utilisé par des modèles.', 'warning')
             return redirect(url_for('admin_types'))
        
        db.session.delete(type_a_supprimer)
        db.session.commit()
        flash('Type supprimé avec succès.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression du type: {e}', 'danger')
    return redirect(url_for('admin_types'))

if __name__ == '__main__':
    # Créer les tables si elles n'existent pas (au cas où create_tables.py n'a pas été lancé)
    with app.app_context():
        db.create_all()
    app.run(debug=True)