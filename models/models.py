from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import date, datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='client')
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable = False)
    country = db.Column(db.String(50))
    transactions = db.relationship('Transaction', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    


class Transaction(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    id = db.Column(db.Integer, primary_key=True)
    transaction_date = db.Column(db.Date, default=date.today)
    transaction_type = db.Column(db.String(20), nullable=False)
    sort_code = db.Column(db.String(10), nullable=False)
    account_number = db.Column(db.String(20), nullable=False)
    transaction_description = db.Column(db.String(255) , nullable=False)
    debit_amount = db.Column(db.Float)
    credit_amount = db.Column(db.Float)
    balance = db.Column(db.Float, nullable=False)  
    
    
# an object in the database that represents the recipient of a bank transfer
    
class Recipient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) 
    name = db.Column(db.String(100), nullable=False)
    sort_code = db.Column(db.String(10), nullable=False)
    account_number = db.Column(db.String(20), nullable=False)
    user = db.relationship('Users', backref=db.backref('recipients', lazy=True))
    

    
    
class DDSO(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient = db.Column(db.String(50),  nullable=False) 
    reference_number = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)
    frequency = db.Column(db.String(50))  # 'daily' 'monthly' etc
    next_payment_date = db.Column(db.Date, nullable=False)
    
    
    
class SupportTickets(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    reference_number = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='new')  # values: new, in progress, closed, rejected
    priority = db.Column(db.String(50), nullable=False, default='normal')  # values: normal, high, urgent
    category = db.Column(db.String(50), nullable=False, default='general')  # values: general, fraud, service problem, money transfer
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    
class LockedUsers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    is_account_locked = db.Column(db.Boolean, default = True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    
    
class Loans(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient = db.Column(db.String(100), nullable=False)
    product_id = db.Column(db.String(50), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False, default='LOAN')
    nominal_amount = db.Column(db.Float, nullable=False)
    interest = db.Column(db.String(20), nullable=False)
    installment_amount = db.Column(db.Float, nullable=False)
    installments_number = db.Column(db.Integer, nullable=False)
    installments_paid = db.Column(db.Integer, nullable=False)
    installments_to_be_paid = db.Column(db.Integer, nullable=False)
    total_amount_to_be_repaid = db.Column(db.Float, nullable=False)
    remaining_amount_to_be_repaid = db.Column(db.Float, nullable=False)
    loan_cost = db.Column(db.Float, nullable=False)
    interest_type = db.Column(db.String(20), nullable=False)
    loan_status = db.Column(db.String(20), nullable=False)
    frequency = db.Column(db.Integer, nullable=False)
    loan_start_date = db.Column(db.Date, nullable=False, default=date.today)
    loan_end_date = db.Column(db.Date, nullable=False)
    next_payment_date = db.Column(db.Date, nullable=False)
    currency_code = db.Column(db.String(3), nullable=False)
    loan_purpose = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.Text)