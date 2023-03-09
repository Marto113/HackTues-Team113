from flask import Flask, render_template, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email

app = Flask(__name__)
app.config['SECRET_KEY'] = '8f42a73054b1749f8f58848be5e6502c'

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        if email == 'kamen2109@gmail.com' and password == 'ivan1234':
            return redirect(url_for('home'))

    return render_template('login.html', form=form)
    
if __name__ == "__main__":
     app.run(debug=True ,port=8080,use_reloader=False)
