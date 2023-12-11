from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField, PasswordField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo


class TransferForm(FlaskForm):
    recipient_account = StringField('Recipient Account', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    submit = SubmitField('Transfer')
    
    
    
class MyForm(FlaskForm):
    name = StringField('Name')
    submit = SubmitField('Submit')    

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    #password = PasswordField('Password', validators=[DataRequired()])
    #confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')
    
    
class TransferForm(FlaskForm):
    recipient_account = StringField('Recipient Account', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Transfer')
    
class AddCustomerForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    role = SelectField('Role', choices=[('client', 'Client'), ('bank_emploee', 'Bank Employee'), ('board_member', 'Board Member'), ('management', 'Management')], validators=[DataRequired()])
    country = StringField('Country', validators=[DataRequired()])