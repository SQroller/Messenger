from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from forms import RegistrationForm, LoginForm

app = Flask(__name__)
app.config['SECRET_KEY'] = '1111'  # Replace with your secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # SQLite database for example
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class Count(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer, nullable=False, default=1)
    queue = db.Column(db.Integer, nullable=False, default=1)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='messages')


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/index')
def index():
    messages = Message.query.order_by(Message.id).all()
    username = current_user.username if current_user.is_authenticated else None
    email = current_user.email if current_user.is_authenticated else None
    count_record = Count.query.first()  # Получаем первую запись из таблицы Count
    queue_value = count_record.queue if count_record else None  # Получаем значение queue из count_record или None, если count_record не существует
    return render_template('index.html', messages=messages, username=username, email=email, queue_value=queue_value)



@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('This username is already taken. Please choose a different one.', 'danger')
        elif existing_email:
            flash('This email is already taken. Please choose a different one.', 'danger')
        else:
            user = User(username=form.username.data, email=form.email.data, password=form.password.data)
            db.session.add(user)
            db.session.commit()
            count = Count.query.first()
            if count:
                count.value = user.id
                db.session.commit()
            else:
                count = Count(value=user.id)
                db.session.add(count)
                db.session.commit()
            flash('Your account has been created! You are now able to log in', 'success')
            return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    message_content = request.form.get('message')
    db.session.add(Message(content=message_content, user=current_user))
    db.session.commit()

    # Увеличиваем значение очереди на 1
    count_record = Count.query.first()
    count_record.queue += 1

    # Если очередь достигает значения count, устанавливаем ее в 1
    if count_record.queue == count_record.value:
        count_record.queue = 1


    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
