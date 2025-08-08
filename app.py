from flask import Flask, render_template, request, redirect, url_for ,flash ,session ,jsonify
from sqlalchemy import Table, MetaData, insert
from sqlalchemy.exc import IntegrityError 
from werkzeug.security import generate_password_hash ,check_password_hash


import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData , Table,Column ,Integer , String ,Float ,DateTime ,ForeignKey ,insert ,select

# Bibliotheque pour le module
import joblib
import numpy as np

# ** la connexion avec la base de données

load_dotenv()
    
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)   





# *** Debut de partie Routes
app = Flask(__name__)
app.secret_key = 'une_clé_très_secrète_et_complexe_ici'  # <-- Ajoutez cette ligne

# les  VAriable important
metadata = MetaData()
#autoload_with=engine  sert à charger automatiquement la structure d'une table existante depuis la base de données.
medecins = Table("medecins", metadata, autoload_with=engine)
patients = Table("patients", metadata, autoload_with=engine)

#^^ Page d'accueil 
@app.route("/")
def home():
    return redirect(url_for("login"))  


#^^ Page d'inscription

@app.route("/register", methods=["GET", "POST"])
def register():

    if "username" in session:
        flash("Vous êtes déjà connecté(e).")
        return redirect("/home")
            
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

       
        
        if password != confirm_password:
            flash("Les mots de passe ne correspondent pas.")
            return render_template("register.html")

        # Hachage du mot de passe
        hashed_password = generate_password_hash(password)

        try:
            with engine.connect() as conn:
                # Tentative d'insertion
                stmt = insert(medecins).values(
                    username=username,
                    password=hashed_password,
                    email=email
                )
                conn.execute(stmt)
                conn.commit()
           
            flash("Inscription réussie ! Vous pouvez maintenant vous connecter.")
            return redirect("/login")

        except IntegrityError as e:
            # Gestion des erreurs d'unicité
            if "username" in str(e.orig):
                #ERREUR: la valeur d'une clé dupliquée rompt la contrainte unique « unique_username » DETAIL: La clé « (username)=(medcin_raihana) » existe déjà.
                flash("Ce nom d'utilisateur est déjà pris.")
           
            elif "email" in str(e.orig):
                flash("Cet email est déjà utilisé.")
            else:
                flash("Une erreur s'est produite lors de l'inscription.")
            
            return render_template("register.html")

    return render_template("register.html")


#^^ Page de connexion
@app.route("/login", methods=["GET", "POST"])
def login():

    if "username" in session:
        flash("Vous êtes déjà connecté(e).")
        return redirect("/home")
    
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        with engine.connect() as conn:
            stmt = select(medecins).where(medecins.c.username == username)
            result = conn.execute(stmt).fetchone()
        
            if result:
                stored_password = result.password  

                if check_password_hash(stored_password, password):
                    # Connexion réussie → stocker le nom dans la session
                    session["username"] = username
                    
                    return redirect("/home")

                else:
                    flash("Mot de passe incorrect.")
            else:
                flash("Nom d'utilisateur introuvable.")
    
            

    return render_template("login.html")


# ^^ apres la connexion 
@app.route("/home")
def homee():
    username = session.get("username")
    if not username:
        flash("Veuillez vous connecter.")
        return redirect("/login")
    # flash(session)
    return render_template("home.html", username=username)

#^^ logout
@app.route("/logout")
def logout():
    session.clear()  
    flash("Déconnexion réussie.")
    return redirect("/login")

#^^ patient
@app.route("/patient" ,methods=["GET", "POST"])
def patient():
    return render_template("patient.html")


#^^ Ajouter patient
@app.route("/submit", methods=["POST"])
def submit_patient():
    if "username" not in session:
        flash("Veuillez vous connecter.")
        return redirect("/login")

    # Récupération des données du formulaire
    name = request.form.get("name")
    age = request.form.get("age")
    sex = request.form.get("sex")
    glucose = request.form.get("glucose")
    bmi = request.form.get("bmi")
    bloodpressure = request.form.get("bloodpressure")
    pedigree = request.form.get("pedigree")
    created_at = request.form.get("created_at") or None

    # Récupérer l'id du docteur connecté
    username = session["username"]


    with engine.connect() as conn:
        doctor_id_query = select(medecins.c.id).where(medecins.c.username == username)
        result = conn.execute(doctor_id_query).fetchone()

        if result:
            doctor_id = result[0]

            # Insérer dans patients
            stmt = insert(patients).values(
                doctor_id=doctor_id,
                name=name,
                age=age,
                sex=sex,
                glucose=glucose,
                bmi=bmi,
                bloodpressure=bloodpressure,
                pedigree=pedigree,
                created=created_at
            )
            conn.execute(stmt)
            conn.commit()

            flash("Patient ajouté avec succès.")
        else:
            flash("Erreur : médecin introuvable.")

    return redirect("/patients")


#^^ affichages de tout les patient 
@app.route("/patients")
def list_patients():
    if "username" not in session:
        flash("Veuillez vous connecter.")
        return redirect("/login")

    
    with engine.connect() as conn:
        doctor = conn.execute(select(medecins.c.id).where(medecins.c.username == session["username"])).fetchone()
        doctor_id = doctor[0] if doctor else None

        # if doctor_id is None:
        #     flash("Erreur : médecin introuvable.")
        #     return redirect("/login")

        query = select(patients).where(patients.c.doctor_id == doctor_id)
        result = conn.execute(query).fetchall()

    return render_template("patients.html", patients=result)


@app.route("/delete/<int:patient_id>")
def delete_patient(patient_id):
    
    with engine.connect() as conn:
        conn.execute(patients.delete().where(patients.c.id == patient_id))
        conn.commit()

    flash("Patient supprimé avec succès.")
    return redirect("/patients")



#** le modele
# Charger le modèle entraîné
model = joblib.load(r"C:\Users\ULTRAPC\Downloads\Dev_IA\challenges\sprint2\DiabetoWeb\Model\model.pkl") 

@app.route("/predict/<int:patient_id>")
def predict(patient_id):
    if "username" not in session:
        flash("Veuillez vous connecter.")
        return redirect("/login")

    try:
        # Connexion DB
        with engine.connect() as conn:
            # Récupération des données du patient
            query = select(
                patients.c.glucose,
                patients.c.bmi,
                patients.c.age,
                patients.c.pedigree
            ).where(patients.c.id == patient_id)

            patient = conn.execute(query).fetchone()

            if not patient:
                flash("Patient introuvable.")
                return redirect("/patients")

            # Features dans l’ordre attendu par le modèle
            features = [
                patient.glucose,
                patient.bmi,
                patient.age,
                patient.pedigree
            ]

            input_array = np.array(features).reshape(1, -1)

            # Prédiction
            cluster = model.predict(input_array)[0]
            risk_mapping = {
                0: "Faible/Modéré",
                1: "Haut Risque",
                2: "Faible/Modéré",
                3: "Haut Risque",
                4: "Faible/Modéré"
            }
            risk = risk_mapping.get(cluster, "Inconnu")

            flash(f"Résultat prédiction: {risk} (Cluster {cluster})")

    except Exception as e:
        flash(f"Erreur lors de la prédiction : {e}")

    return redirect("/patients")




# lancment du serveur
if __name__ == "__main__":
    app.run(debug=True)

