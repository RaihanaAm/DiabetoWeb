from flask import Flask, render_template, request, redirect, url_for ,flash ,session
from sqlalchemy import Table, MetaData, insert
from sqlalchemy.exc import IntegrityError 
from werkzeug.security import generate_password_hash ,check_password_hash


import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData , Table,Column ,Integer , String ,Float ,DateTime ,ForeignKey ,insert ,select

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

if __name__ == "__main__":
    app.run(debug=True)