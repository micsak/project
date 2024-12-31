import os


from flask import Flask, flash, redirect, render_template, request, session, g
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import errormessage, login_required
from distutils.log import debug
from fileinput import filename
from flask import *



app = Flask(__name__)
app.config["SESSION_FILE_DIR"] = "./flask_session_cache"
Session(app)


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


db = SQL("sqlite:///pet.db")





@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response




@app.before_request
def load_current_user():
    if "user_id" not in session:
        g.user = "No name"
    else:
        thisuser = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])
        currentuser = thisuser[0]["username"]
        g.user = currentuser




@app.route("/", methods=["GET", "POST"])
#@login_required
def index():
    if "user_id" not in session:
        return render_template("/about.html")
    #mypets = db.execute("SELECT  pet_users.id as pet_id ,pets.id ,pets.name, pets.species, pets.breed,pets.image_path,pets.image_file,pet_users.user_id as pet_user_id,pets.user_id as pets_user_id ,pet_users.status,pet_users.type FROM pets join pet_users on pets.id=pet_users.pet_id WHERE  pets.status=0  and pet_users.status=0 and pet_users.user_id =? order by pet_users.type", session["user_id"])
    mypets = db.execute("SELECT  pets.id ,pets.name, pets.species, pets.breed,pets.image_path,pets.image_file,pets.user_id ,pets.status FROM pets WHERE  pets.status=0  and pets.user_id =? ", session["user_id"])
    mypetrequest = db.execute("SELECT  pet_users.id as pet_id ,pets.id ,pets.name, pets.species, pets.breed,pets.image_path,pets.image_file,pet_users.user_id as pet_user_id,pets.user_id as pets_user_id ,pet_users.status,pet_users.type FROM pets join pet_users on pets.id=pet_users.pet_id WHERE  pets.status=0  and pet_users.status=0 and pet_users.type=? and pet_users.user_id =? order by pet_users.type", "R",session["user_id"])
    #return render_template("/pets.html", mypets=mypets )
    print(mypets)

    #thisuser= currentuser()
    return render_template("/index.html",mypets=mypets,mypetrequest=mypetrequest,thisuser=g.user)





@app.route('/photo/<int:pet_id>')
@login_required
def photo(pet_id):

    if "user_id" not in session:
        return render_template("/about.html")
    mypets = db.execute("SELECT  pets.id,pets.name, pets.species, pets.breed,pets.image_path,pets.image_file,pet_users.user_id,pet_users.status,pet_users.type FROM pets join pet_users on pets.id=pet_users.pet_id WHERE  pet_users.status=0 and pet_users.user_id =? and pets.id=?", session["user_id"],pet_id)
    thisuser= currentuser()
    if mypets:
        return render_template("/photo.html", mypets=mypets[0] )
    else:
        return errormessage("Photo not found", 404)
    #return redirect("/")

@app.route("/pets")
@login_required
def pets():
    if "user_id" not in session:
        return render_template("/about.html")

    #pets = db.execute("SELECT  pets.id,pets.name, pets.species, pets.breed,pets.image_path,pets.image_file,pet_users.user_id,pet_users.status,pet_users.type FROM pets join pet_users on pets.id=pet_users.pet_id WHERE type='O' and pets.status=0")
    pets = db.execute("SELECT  pets.id,pets.name, pets.species, pets.status, pets.date,pets.breed,pets.image_path,pets.image_file FROM pets  WHERE pets.status=0")
    if  pets:
        return render_template("/pets.html", pets=pets,thisuser=g.user)
        #return render_template("/pets.html", pets=pets[0] )
    else:
        return render_template("/pets.html")
    #return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():

    """Register user"""
    if request.method == "POST":
        # Ensure username was submitted
        username = request.form.get("username")
        if not username:
            return errormessage("You must provide a username", 400)

        password = request.form.get("password")
        if not password:
            return errormessage("You must provide a password", 400)

        password2 = request.form.get("confirmation")
        if not password2:
            return errormessage("You must provide password again", 400)

        if password != password2:
            return errormessage("You should enter same password twice", 400)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )
        if len(rows) == 1:
            return errormessage("Sorry the username already exists", 400)


        password = generate_password_hash(password)
        db.execute("INSERT INTO users (username,hash) VALUES(?,?)",username,password)
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )
        session["user_id"] = rows[0]["id"]
        return redirect("/")

        #return apology("TODO")
    else:
        return render_template("/register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted

        if not request.form.get("username"):
            return errormessage("You must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return errormessage("You must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        request.form.get("username")


        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return errormessage("invalid username and/or password", 403)

        # Remember which user has logged in

        session["user_id"] = rows[0]["id"]
        # Redirect user to home page
        #return render_template("/hello.html")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")



@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if "user_id" not in session:
        return render_template("about.html")

    if request.method == "POST":

        oldPassword = db.execute("SELECT hash FROM users WHERE id = ?", session["user_id"])
        currentPassword = request.form.get("oldPassword")
        newPassword = request.form.get("password")
        newConfirmation = request.form.get("2password")
        # Check for user error
        if not currentPassword or not newPassword or not newConfirmation:
            return apology("missing fields")
        elif not check_password_hash(oldPassword[0]["hash"], currentPassword):
            return apology("invalid current password")
        elif newPassword != newConfirmation:
            return apology("passwords do not match")

        # Generate new password hash
        newPasswordHash = generate_password_hash(newPassword)

        # Update password
        db.execute("UPDATE users SET hash = ? WHERE id = ?", newPasswordHash, session["user_id"])

        flash("Password Changed!")
        return redirect("/profile")
    else:
        userName = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])
        return render_template("profile.html", userName=userName[0]["username"],thisuser=g.user)


@app.route("/myoffers", methods=["GET", "POST"])
@login_required
def myoffers():
    if "user_id" not in session:
        return render_template("about.html")


    if request.method == "POST":
        # Ensure pet name  was submitter
        petname = request.form.get("petname")
        if not petname:
            return errormessage("You must pet name", 403)

        # Ensure species  was submitter
        species = request.form.get("species")
        if not species:
            return errormessage("You must provide species of your pet", 403)

        # Ensure breed  was submitter
        breed = request.form.get("breed")
        if not breed:
            return errormessage("You must select breed of your pet", 403)

        #Insert new pet to pet libraries
        f = request.files['file']
        new_filename = petname + "_" + f.filename
        path = r"static/images/"

        pet_user_id = session["user_id"]

        db.execute("INSERT INTO pets (name,species,breed,image_path,image_file,user_id) VALUES(?,?,?,?,?,?)",petname,species,breed,path,new_filename,pet_user_id)
        pets = db.execute( "SELECT * FROM pets" )



        #insert pet to users pet
        last_pet_id = db.execute("SELECT max(id) FROM pets")[0]['max(id)']



        db.execute("INSERT INTO pet_users (pet_id,user_id,type) VALUES(?,?,?)",last_pet_id,pet_user_id,'O')
        pet_users = db.execute( "SELECT * FROM pet_users WHERE user_id = ?", session["user_id"])

        f.save(os.path.join('static', 'images', new_filename))

        return redirect("/")
    return render_template("myoffers.html",thisuser=g.user)

@app.route("/requests", methods=["GET", "POST"])
@login_required
def requests():
    if "user_id" not in session:
        return render_template("about.html")


    if request.method == "POST":
        selectedvalue = request.form.get("selectedValue")
        pet_user_id = session["user_id"]
        db.execute("INSERT INTO pet_users (pet_id,user_id,type) VALUES(?,?,?)",selectedvalue,pet_user_id,'R')
        flash('Request has been submitted succesfuly')

        return redirect("/pets")
    else:
        return render_template("pets.html")




@app.route("/remove", methods=["GET", "POST"])
@login_required
def remove():
    if "user_id" not in session:
        return render_template("about.html")


    if request.method == "POST":

        selectedvalue = request.form.get("selectedValue")
        print("selectedvalue: ",selectedvalue)
        rowtype = request.form.get("rowtype")
        pets_user_id = request.form.get("pets_user_id")
        pet_user_id = request.form.get("pet_user_id")
        offer = request.form.get("offer")
        print("pets_user_id: ", pets_user_id)
        print("pet_user_id: ", pet_user_id)
        print("rowtype: ", rowtype)

        print("offer: ",offer)
        print("pet_user_id", pet_user_id)
        print("pets_user_id", pets_user_id)

        if offer == "Offer":
            db.execute("UPDATE pets SET status = 1 where id=?",selectedvalue)
            db.execute("UPDATE pet_users SET status = 1 where pet_id=?",selectedvalue)

        else:
            print("update pet_users")
            db.execute("UPDATE pet_users SET status = 1 where id=?",selectedvalue)

            flash('Pet with ID = ' + selectedvalue + ' has been removed succccesfully')

        return redirect("/")
    else:
        return render_template("index.html")




@app.route("/offer", methods=["GET", "POST"])
@login_required
def offer():
    if "user_id" not in session:
        return render_template("about.html")

    if request.method == "POST":
        return render_template("myoffers.html")
    return redirect("/pets")

@app.route("/about")
#@login_required
def about():
    return render_template("/about.html",thisuser=g.user)
