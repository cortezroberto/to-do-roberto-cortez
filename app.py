from flask import Flask, request, render_template, url_for, redirect, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, UserMixin, login_required, current_user, logout_user
import os
import smtplib
from flask_mail import Mail, Message

app = Flask(__name__)

# POSTGRESS CONECCTION 
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SQLALCHEMY_DATABASE_URI']='postgres://kcbngmnemhoxxq:a068f05edef1310223b77d272a1fbeb3ac62eb726a5667a58f76e83aac96219a@ec2-54-144-45-5.compute-1.amazonaws.com:5432/debmil49qirpo4'
# app.config['SQLALCHEMY_DATABASE_URI']='postgresql+psycopg2://postgres:12345@localhost:5432/db_todolist'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']= False
db = SQLAlchemy(app) # SQLAlchemy Object

# LOGIN MANAGER
login_manager =  LoginManager(app)
login_manager.login_view = "login"

# EMAIL
# app.config['MAIL_SERVER'] = 'smtp.gmail.com'
# app.config['MAIL_PORT'] = 465
# app.config['MAIL_USERNAME'] = 'todolist2021s@gmail.com'
# app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
# app.config['MAIL_USE_TLS'] = False
# app.config['MAIL_USE_SSL'] = True
# mail = Mail(app)

#DATA MODEL
# USER
class User(UserMixin,db.Model):
    __tablename__ = 'user'
    idUser = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique = True)
    password = db.Column(db.String(100))
    userName = db.Column(db.String(100))
    def get_id(self):
           return (self.idUser)

# CATEGORY
class Category(db.Model):
    __tablename__ = 'category'
    idCategory = db.Column(db.Integer,primary_key=True)
    categoryName = db.Column(db.String(30), nullable=False)
    categoryStatus = db.Column(db.Boolean)

    # def __init__(self, categoryName, categoryStatus):
    #     self.categoryName = categoryName
    #     self.categoryStatus = categoryStatus

# TASK
class Task(db.Model):
    __tablename__ = 'task'
    idTask = db.Column(db.Integer,primary_key=True)
    taskName = db.Column(db.String(30), nullable=False)
    taskStatus = db.Column(db.Boolean)
    idCat = db.Column(db.Integer, db.ForeignKey('category.idCategory'))

    # def __init__(self, taskName, taskStatus, idCat):
    #     self.taskName = taskName
    #     self.taskStatus = taskStatus
    #     self.idCat = idCat

# FUNCTIONS

# INDEX
@app.route('/')
def index():
    return render_template("index.html")

# TO-DO
@app.route('/todo')
@login_required
def todo():
    qry = Category.query.all()
    qryT = Task.query.all()
    return render_template("todo.html",categories = qry, tasks = qryT)

# SIGN UP
@app.route('/signup')
def signup():
    return render_template("signup.html")

# SIGN UP
@app.route('/signup', methods=["POST"])
def signup_post():
    email = request.form["email"]
    userName = request.form["userName"]
    password = request.form["password"]
    user = User.query.filter_by(email=email).first()
    if user:
        flash("Email already exists!")
        return redirect(url_for("signup"))
    new_user = User(email=email,userName=userName, password = generate_password_hash(password, method="sha256"))
    db.session.add(new_user)
    db.session.commit()
    # msg = Message("Thanks for registering!", sender="todolist2021s@gmail.com", recipients=[email])
    # msg.body = "To-Do"
    # msg.html = "<p>Start creating to-do's!</p>"
    # mail.send(msg)
    msg = "Thanks for registering!"
    server = smtplib.SMTP("smtp.gmail.com",587)
    server.starttls()
    server.login("todolist2021s@gmail.com","Todolist21")
    server.sendmail("todolist2021s@gmail.com",email,msg)
    return redirect(url_for("login"))

# PROFILE
@app.route('/profile',methods=['GET','POST'])
@login_required
def profile():
    return render_template("profile.html",id = current_user.idUser, name= current_user.userName, email = current_user.email)

# UPDATE PPROFILE
@app.route('/updateProfile', methods=['GET','POST'])
@login_required
def updateProfile():
    if request.method == 'POST':
        password = request.form["password"]
        password2 = request.form["password2"]
        if password != password2:
            flash("Check your password!")
            return redirect(url_for("profile"))

        qry = User.query.get(request.form['idUser'])
        qry.userName = request.form['userName']
        qry.email = request.form['email']
        qry.password = generate_password_hash(request.form['password'], method="sha256")
        db.session.commit()
        logout()
        return redirect(url_for('login'))

# LOGIN MANAGER
@login_manager.user_loader
def load_user(idUser):
    return User.query.get(int(idUser))

# LOGIN
@app.route('/login')
def login():
    return render_template("login.html")

# LOGIN
@app.route('/login', methods=["POST"])
def login_post():
    email = request.form['email']
    password = request.form['password']
    remember = True if request.form.get('remember') else False
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        flash('Please check your login credentials and try again.')
        return redirect(url_for('login'))
    #Creates coockie and session
    login_user(user, remember=remember)
    return redirect(url_for('todo'))

# LOGOUT
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# ADD TASK METHOD
@app.route("/add", methods=["POST"])
@login_required
def add():
    name = request.form['name']
    category = request.form['category']
    new_todo = Task(taskName=name,taskStatus=False, idCat=category)
    db.session.add(new_todo)
    db.session.commit()
    return redirect(url_for("todo"))

# CROSS TASK METHOD
@app.route("/cross/<int:task_id>")
@login_required
def cross(task_id):
    task = Task.query.filter_by(idTask=task_id).first()
    task.taskStatus = not task.taskStatus
    db.session.commit()
    return redirect(url_for("todo"))

# EDIT TASK METHOD
@app.route("/editTask/<idTask>")
@login_required
def editTask(idTask):
    task = Task.query.filter_by(idTask=int(idTask)).first()
    return render_template("editTask.html",tasks = task)

# UPDATE TASK METHOD
@app.route('/updateTask', methods=['GET','POST'])
@login_required
def updateTask():
    if request.method == 'POST':
        qry = Task.query.get(request.form['idTask'])
        qry.taskName = request.form['taskName']
        db.session.commit()
        return redirect(url_for('todo'))

# DELETE TASK METHOD
@app.route("/delete/<int:task_id>")
@login_required
def delete(task_id):
    task = Task.query.filter_by(idTask=task_id).first()
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for("todo"))

# ADD CATEGORY METHOD
@app.route("/addCategory", methods=["POST"])
@login_required
def addCategory():
    name = request.form['nameCat']
    new_cat = Category(categoryName=name,categoryStatus=False)
    db.session.add(new_cat)
    db.session.commit()
    return redirect(url_for("todo"))

# EDIT CATEGORY METHOD
@app.route("/editCategory/<idCategory>")
@login_required
def editCategory(idCategory):
    cat = Category.query.filter_by(idCategory=int(idCategory)).first()
    return render_template("editCategory.html",categories = cat)

# UPDATE CATEGORY METHOD
@app.route('/updateCategory', methods=['GET','POST'])
@login_required
def updateCategory():
    if request.method == 'POST':
        qry = Category.query.get(request.form['idCategory'])
        qry.categoryName = request.form['categoryName']
        db.session.commit()
        return redirect(url_for('todo'))

# DELETE CATEGORY METHOD
@app.route("/deleteCategory/<int:cat_id>")
@login_required
def deleteCategory(cat_id):
    cat = Category.query.filter_by(idCategory=cat_id).first()
    task= Task.query.filter_by(idCat=cat_id).first()
    try:
        if task != cat:
            db.session.delete(cat)
            db.session.commit()
            return redirect(url_for("todo"))
    except:
        flash("You can't delete a List unless it doesn't has tasks!")
        return redirect(url_for("todo"))    

# MAIN APP
if __name__=='__main__':
    db.create_all()
    app.run(debug=True)