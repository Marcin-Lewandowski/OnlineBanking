from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField, PasswordField, SelectField, DateField
from wtforms.validators import DataRequired, Length, Email, NumberRange, EqualTo 



class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')
    
    
class TransferForm(FlaskForm):
    recipient_sort_code = StringField('Recipient Sort Code', validators=[DataRequired()])
    recipient_account_number = StringField('Recipient Account Number', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    transaction_description = StringField('Description', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Transfer')
    
 
class AddCustomerForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    role = SelectField('Role', choices=[('client', 'Client'), ('bank_emploee', 'Bank Employee'), ('board_member', 'Board Member'), ('management', 'Management')], validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_number = StringField('Phone number', validators=[DataRequired()])
    country = StringField('Country', validators=[DataRequired()])
    
    
    
class CreateTransactionForm(FlaskForm):
    user_id = SelectField('User', coerce=int, validators=[DataRequired()])
    transaction_date = DateField('Transaction Date', format='%Y-%m-%d', validators=[DataRequired()])
    transaction_type = SelectField('Transaction Type', choices=[('DEB', 'Debit'), ('DD', 'Direct Debit'), ('SAL', 'Salary'), ('CSH', 'Cash'), ('SO', 'Standing Order'), ('FPI', 'Faster Payment Incoming'), ('FPO', 'Faster Payment Outgoing'), ('MTG', 'Mortgage')], validators=[DataRequired()])
    sort_code = StringField('Sort Code', validators=[DataRequired(), Length(min=6, max=10)])
    account_number = StringField('Account Number', validators=[DataRequired(), Length(min=5, max=20)])
    transaction_description = StringField('Description', validators=[DataRequired()])
    debit_amount = FloatField('Debit Amount', validators=[NumberRange(min=0)])
    credit_amount = FloatField('Credit Amount', validators=[NumberRange(min=0)])
    balance = FloatField('Balance', validators=[NumberRange(min=0)])
    submit = SubmitField('Create Transaction')
    

class DeleteUserForm(FlaskForm):
    username = StringField('Nazwa Użytkownika', validators=[DataRequired()])
    submit = SubmitField('Usuń Użytkownika')
    
class EditUserForm(FlaskForm):
    email = StringField('Email', validators=[Email()])
    phone_number = StringField('Phone number', validators=[Length(min=8, max=15)])
    country = StringField('Country')
    submit = SubmitField('Update')
    
class ChangePasswordForm(FlaskForm):
    new_password = PasswordField('New Password', validators=[DataRequired()])
    confirm_new_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')
    
    
class AddRecipientForm(FlaskForm):
    name = StringField('Name', validators = [DataRequired()])
    sort_code = StringField('Sort Code', validators = [DataRequired()])
    account_number = StringField('Account Number', validators = [DataRequired()])
    submit = SubmitField('Add Recipient')