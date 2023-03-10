from flask import Flask, render_template, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email
from flask_login import LoginManager, current_user, login_user, login_required, UserMixin, logout_user

app = Flask(__name__, static_url_path="/static")
app.config['SECRET_KEY'] = '8f42a73054b1749f8f58848be5e6502c'
login_manager = LoginManager(app)

class User(UserMixin):
    def __init__(self, id):
        self.id = id

    @staticmethod
    def get(user_id):
        return User(user_id)

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        if username == 'root' and password == 'root':
            user = User(username)
            login_user(user)
            return redirect(url_for('home'))

    return render_template('login.html', form=form)

@app.route('/home')
@login_required
def home():
    return "This is the home page!"

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

if __name__ == "__main__":
    app.run(debug=True, port=8080, use_reloader=False)