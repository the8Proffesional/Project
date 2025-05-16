from extensions import db

class Arrondissement(db.Model):
    __tablename__ = 'arrondissement'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False, unique=True)
    departements = db.relationship('Departement', backref='arrondissement', lazy=True)

    def __repr__(self):
        return f'<Arrondissement {self.nom}>'

class Departement(db.Model):
    __tablename__ = 'departement'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    arrondissement_id = db.Column(db.Integer, db.ForeignKey('arrondissement.id'), nullable=False)
    bureaux = db.relationship('Bureau', backref='departement', lazy=True)

    def __repr__(self):
        return f'<Departement {self.nom}>'

class Bureau(db.Model):
    __tablename__ = 'bureau'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), nullable=False) # Bureau number or name
    departement_id = db.Column(db.Integer, db.ForeignKey('departement.id'), nullable=False)
    utilisateurs = db.relationship('Utilisateur', backref='bureau', lazy=True)

    def __repr__(self):
        return f'<Bureau {self.numero}>'

class Utilisateur(db.Model):
    __tablename__ = 'utilisateur'
    id = db.Column(db.Integer, primary_key=True)
    nom_utilisateur = db.Column(db.String(80), nullable=False, unique=True)
    numero_telephone = db.Column(db.String(20), nullable=False, unique=True) # Assuming a max length of 20 for phone numbers
    # Add other user fields as needed, e.g., password_hash
    bureau_id = db.Column(db.Integer, db.ForeignKey('bureau.id'), nullable=False)

    def __repr__(self):
        return f'<Utilisateur {self.nom_utilisateur}>'

# Models to be moved from app.py
class Fabricant(db.Model):
    __tablename__ = 'fabricant'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(80), unique=True, nullable=False)
    modeles = db.relationship('Modele', backref='fabricant', lazy=True)

    def __repr__(self):
        return f'<Fabricant {self.nom}>'

class Type(db.Model):
    __tablename__ = 'type'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(80), unique=True, nullable=False)
    modeles = db.relationship('Modele', backref='type', lazy=True)

    def __repr__(self):
        return f'<Type {self.nom}>'

class Modele(db.Model):
    __tablename__ = 'modeles'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(120), nullable=False)
    fabricant_id = db.Column(db.Integer, db.ForeignKey('fabricant.id'), nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('type.id'), nullable=False)

    def __repr__(self):
        return f'<Modele {self.nom}>'
