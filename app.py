###################################################################################
#
#
# This is the main python file for this project. It contains routing information
# and setting up of the SQLite database.
#
#
###################################################################################

# import the flask class and necessary functions from the class
from flask import Flask, redirect, url_for, render_template, request, flash
# import hashing method
from werkzeug.security import generate_password_hash, check_password_hash
# import sqlalchemy to manage the database
from flask_sqlalchemy import SQLAlchemy
# import flask_login to manage logged in user sessions
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required

# creating an instance of the flask class
app = Flask(__name__)

# configure the secret key and the connection with the database
app.config['SECRET_KEY'] = 'mySecretKey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# connect the database to the Flask app
db = SQLAlchemy(app)
# create a login manager through flask-login and connect it to the app
login_manager = LoginManager(app)

# table to store users
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String, unique=True)
    firstname = db.Column(db.String)
    lastname = db.Column(db.String)
    password = db.Column(db.String)
    classYear = db.Column(db.Integer)

# table to store reviews
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    user = db.Column(db.String(200), nullable=False)
    place = db.Column(db.String(200), default=0)
    content = db.Column(db.String(200), nullable=False)
    rating = db.Column(db.Integer, default=0)
    budget = db.Column(db.Integer, default=0)

# table to store places
class Place(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    av_rating = db.Column(db.Integer, default=0)
    av_budget = db.Column(db.Integer, default=0)
    category= db.Column(db.String(200), nullable=False)


# function to load the user from the database when they log in
@login_manager.user_loader
def loadUser(id_user):
    return User.query.get(int(id_user))

# using route to specify the URLs that will trigger the home() function
@app.route('/home')
@app.route('/')
# function to display 'index.html', aka the homepage of the webapp
def home():
    return render_template("index.html")

# function to collect the form information when a user signs up
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # if the user submitted their signup information
    if request.method == "POST":
        email = request.form.get('email')
        firstname = request.form.get('fname')
        lastname = request.form.get('lname')
        password = request.form.get('pass')
        confirmPassword = request.form.get('confirmPass')
        classYear = request.form.get('classYear')

        # ensure all fields were entered
        if email == "" or firstname == "" or lastname == "" or password == "" or confirmPassword == "" or classYear == "":
            flash('All fields are required.')
            return render_template('signup.html')

        # ensure passwords match
        if password != confirmPassword:
            flash('Passwords do not match.')
            return render_template('signup.html')

        # search for a user with the same address
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists')
            return render_template('signup.html')

        # add the new user to the database
        newUser = User(email=email, firstname=firstname, lastname=lastname,
                       password=generate_password_hash(password, method='sha256'), classYear=classYear)
        db.session.add(newUser)
        db.session.commit()

        # redirect the user to the login page
        return redirect(url_for('signin'))

    # if the user just navigated to the signup page
    else:
        # display the signup page
        return render_template("signup.html")


# using route to specify the URL that will trigger the signin() function
@app.route('/signin', methods=['GET', 'POST'])
# function to display 'signin.html' where the user can log in
def signin():
    # if the user submitted their login information
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('pass')

        # ensure all fields were entered
        if email == "" or password == "":
            flash('All fields are required.')
            return render_template('signin.html')

        # search for the user in the database
        user = User.query.filter_by(email=email).first()
        # if the user exists and the password is correct
        if user and check_password_hash(user.password, password):
            # login the user
            login_user(user)
            flash('Successfully logged in.')
            return redirect(url_for("places"))
        else:
            # show an alert that login was not successful and display the login page again
            flash('Login credentials incorrect. Please try again.')
            return render_template('signin.html')

    # if the user just navigated to the login page
    else:
        # display the login page
        return render_template("signin.html")

# using route to specify the URL that will trigger the logout() function
@app.route('/logout', methods=['GET', 'POST'])
# function to display logout the user
def logout():
    logout_user()
    return render_template("index.html")

# using route to specify the URLs that will trigger the settings() function
@app.route('/account')
# function to display 'account.html'
def account():
    if(current_user.is_anonymous):
        flash('You are not logged in.')
        return render_template( "index.html")
    return render_template("account.html", fname=current_user.firstname,
                           lname=current_user.lastname,
                           email=current_user.email,
                           classYear=current_user.classYear)

# function to get the place name and description from the database
def getPlaces():
    places = Place.query.with_entities(Place.name, Place.description).order_by(Place.name).all()
    return places

# using route to specify the URLs that will trigger the places() function
@app.route('/places')
# function to display 'places.html'
def places():
    return render_template("places.html", places=getPlaces())

# function to get a place from the database filtered by name
def getPlace(placeName):
    place = Place.query.with_entities(Place.name, Place.location, Place.description,Place.av_rating, Place.av_budget, Place.category).filter_by(name=placeName).first()
    return place

# function to get a review from the database filtered by place
def getReviews(placeName):
    reviews = Review.query.with_entities(Review.user, Review.content, Review.rating, Review.budget).filter_by(place=placeName).all()
    return reviews

# using route to specify the URLs that will trigger the place() function
@app.route('/<string:placeName>')
# function to display 'place.html'
def place(placeName):
    found_place = getPlace(placeName)
    found_reviews = getReviews(placeName)
    ratesum=0
    budgetsum =0
    count=0
    for found_review in found_reviews:
        count=count+1
        ratesum =ratesum+found_review[2]
        budgetsum = budgetsum + found_review[3]
    if count ==0:
        avg_rating =0
        avg_budget=0
    else:
        avg_rating=ratesum/count
        avg_budget=budgetsum/count
    return render_template("place.html", placeName=found_place[0],  placeLocation=found_place[1], placeDescription=found_place[2], placeRating=avg_rating, placeBudget=avg_budget, placeCategory=found_place[5],  reviews=found_reviews )


@app.route('/newplace',methods=['GET', 'POST'])
@login_required
def newplace():
    if  request.method == 'GET':
        return render_template("newplace.html")
    if request.method=='POST':
        place_name=request.form['name']
        place_location=request.form['loc']
        place_category=request.form['category']
        place_description=request.form['desc']

        # ensure all fields were entered
        if place_name == "" or place_location == "" or place_category == "Choose..." or place_description == "":
            flash('All fields are required.')
            return render_template('newplace.html')
        new_task=Place( name=place_name, location=place_location, av_rating= 0, av_budget = 0, category=place_category, description=place_description)
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('places'))
    
@app.route('/<placeName>/newReview',methods=['GET', 'POST'])
@login_required
def newreview(placeName):
    if request.method == 'GET':
        return render_template("newReview.html")
    if request.method == 'POST':
        review_user = current_user.firstname
        review_budget = request.form['budget']
        review_rating = request.form['rating']
        review_content = request.form['content']

        # ensure all fields were entered
        if review_user == "" or review_budget == "" or review_rating == "Choose..." or review_content == "":
            flash('All fields are required.')
            return render_template('newReview.html')

        new_task=Review( user=review_user, place = placeName, budget=review_budget, rating=review_rating, content=review_content)
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('place', placeName=placeName))


# using route to specify the URLs that will trigger the outings() function
@app.route('/outings')
# function to display 'outings.html'
def outings():
    return render_template("outings.html")

# main code
if __name__ == '__main__':
    # create database and run 'app' defined above in debugging mode
    db.create_all()
    app.run(debug=True)

