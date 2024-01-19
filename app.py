from flask import Flask, render_template, url_for, request, flash, session, redirect, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import StringField, SubmitField, PasswordField, BooleanField, ValidationError
from wtforms.validators import DataRequired, EqualTo, Length
import os
import uuid as uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///appusers.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "dfkfahdlkffjhadklfjfhasdlkfhjalsdkfjhfalsdkjfh"
UPLOAD_FOLDER = 'static/images/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return AppUsers.query.get(int(user_id))

class AppUsers(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    userName = db.Column(db.String(100), unique = True)
    email = db.Column(db.String(50),unique=True)
    password_hash = db.Column(db.String(128))
    hobby = db.Column(db.String(500),default = "")
    city = db.Column(db.String(100), default = "")
    date = db.Column(db.DateTime,default=datetime.utcnow)
    profile_pic = db.Column(db.String(), nullable=True)
    isAdmin = db.Column(db.Boolean, default = False)



    def __repr__(self):
        return f"<appusers {self.id}>"

# with app.app_context():
# db.create_all()

# app.app_context().push()


panelItems = [{'id': 1, 'isOpen': False, 'title': "Продукт", 'listOfChildItems': ['О продукте', "Обучение", "Видеокурс"]},
                 {'id': 2, 'isOpen': False, 'title': "Тарифы", 'listOfChildItems': ["Free", "Standart", "No limits"],},
                 {'id': 3, 'isOpen': False, 'title': "Компания", 'listOfChildItems': ["Лицензия", "Сотрудники",],},]

@app.route("/")
def index():
    return render_template('main.html', panelItems = panelItems )

@app.route("/registration", methods=['GET','POST'])
def registration():
    if request.method == 'POST':
        if (len(request.form['username'])>5 & (len(request.form['email'])>6)):
            flash('Данные отправлены', category='success')
        else:
            flash('Данные некорректны',category='error')
        try:
            hash = generate_password_hash(request.form['password'])
            appUsers = AppUsers(email = request.form['email'], password_hash = hash, userName = request.form['username'], profile_pic = 'avatar.jpg')
            db.session.add(appUsers)
            db.session.flush()
            db.session.commit()
        except:
            db.session.rollback()
            print('Ошибка добавления в БД')

    return render_template('registration.html', panelItems = panelItems, navbarOff = True)

@app.errorhandler(404)
def pageNotFount(error):
    return render_template('page404.html', title="Страница не найдена")

@app.route('/login', methods = ['GET','POST'])
def login():
    # if 'userLogged' in session:
    #     return redirect(url_for('profile',username=session['userLogged']))
    if request.method == 'POST':
        session['userLogged'] = request.form['username']
        user = AppUsers.query.filter_by(userName=request.form['username']).first()
        if user:
            login_user(user)
            print('success')
            if check_password_hash(user.password_hash,request.form['password']):
                return redirect(url_for('profile', username = request.form['username']))
            else:
                print('login error')
        # return redirect(url_for('profile',username=session['userLogged']))
    return render_template('login.html', title="Авторизация", navbarOff = True,)

# and request.form['username'] == 'admin' and request.form['password'] == '123'

@app.route("/profile/<username>")
@login_required
def profile(username):
    if 'userLogged' not in session or session['userLogged']!=username:
        abort(401)
    try:
        userData = AppUsers.query.filter_by(userName = username).first()
        print(userData)
        return render_template('profile.html', title="Профиль", navbarOff = True, userData = userData)
    except:
        print('something went wrong')
    return render_template('profile.html', title="Авторизация", navbarOff = True)

@app.route('/profile/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash("You have been logged out")
    return redirect(url_for('login'))

@app.route("/profile/update/<int:id>",methods=['GET','POST'])
@login_required
def update(id):
    try:
        userData = AppUsers.query.filter_by(id = id).first()
    except:
        print('error of getting data')
    try:
        userToUpdate = AppUsers.query.filter_by(id = id).first()
        if request.method == 'POST':
            # print(request.files['profile_pic'])
            if (request.form['username'] != ''):
                userToUpdate.userName = request.form['username']
            if (request.form['email'] != ''):
                userToUpdate.email = request.form['email']
            if (request.form['hobby'] != ''):
                userToUpdate.hobby = request.form['hobby']
            if (request.form['city'] != ''):
                userToUpdate.city = request.form['city']
            if (request.files['profile_pic']):
                print('its ok')
                userToUpdate.profile_pic = request.files['profile_pic']
                pic_filename = secure_filename(userToUpdate.profile_pic.filename)
                pic_name = str(uuid.uuid1()) + "_" + pic_filename
                saver = request.files['profile_pic']
                userToUpdate.profile_pic = pic_name
                saver.save(os.path.join(app.config['UPLOAD_FOLDER'], pic_name))
            db.session.commit()
            userData = AppUsers.query.filter_by(id = id).first()
            return render_template('profile.html', navbarOff = True, username = request.form['username'], userData = userData)
    except:
        print('Something went wrong')
    return render_template('profile.html', username = request.form['username'], userData = userData, navbarOff = True,)

@app.route("/admin",methods=['GET','POST'])
def admin():
    try:
        appUsers = AppUsers.query.filter_by(isAdmin = False).all()
    except:
        flash("Ошибка чтения из бд", category='success')
    return render_template('admin.html', title="Администратор", navbarOff = True, users = appUsers)

@app.route("/admin/<int:id>")
def delete(id):
    try:
        AppUsers.query.filter(AppUsers.id == id).delete()
        db.session.commit()
        appUsers = AppUsers.query.filter_by(isAdmin = False).all()
        flash('User has been deleted', category='success')
        return redirect(url_for('admin'))
    except:
        flash('Something has broken(', category='error')
        appUsers = AppUsers.query.filter_by(isAdmin = False).all()
        return render_template('admin.html', title="Администратор", navbarOff = True, users = appUsers)


if __name__ == "__main__":
    app.run(debug=True)
