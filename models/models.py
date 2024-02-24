from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import date, datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Users(db.Model, UserMixin):
    """
    User model for storing user-related data and handling authentication in a Flask application.

    Inherits from:
    - db.Model: Base class for all models in Flask-SQLAlchemy.
    - UserMixin: Provides default implementations for Flask-Login required methods.

    Attributes:
        id (db.Column): Unique identifier for the user, serves as the primary key.
        username (db.Column): Unique username for the user. It is a required field.
        password_hash (db.Column): Hashed password for secure storage. It is a required field.
        role (db.Column): Role of the user in the system. Defaults to 'client'. It is a required field.
        email (db.Column): Unique email address for the user. It is a required field.
        phone_number (db.Column): Contact phone number for the user. It is a required field.
        country (db.Column): Country of residence for the user. Optional.
        transactions (db.relationship): One-to-many relationship linking users to their transactions.

    Methods:
        set_password(self, password): Hashes the password and stores it.
            Args:
                password (str): Plain text password to be hashed and stored.

        check_password(self, password): Verifies if the provided password matches the stored hash.
            Args:
                password (str): Plain text password to be verified against the stored hash.
            Returns:
                bool: True if the password matches the hash, False otherwise.
    """
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
    """
    Transaction model for storing details about financial transactions in a Flask application.

    This model is designed to keep track of various types of transactions (e.g., transfers, standing orders)
    associated with users. It links each transaction to a specific user in the system via a foreign key.

    Attributes:
        user_id (db.Column): Foreign key linking the transaction to a user. It is a required field.
        id (db.Column): Unique identifier for the transaction, serves as the primary key.
        transaction_date (db.Column): Date when the transaction occurred. Defaults to the current date.
        transaction_type (db.Column): Type of the transaction (e.g., deposit, withdrawal). It is a required field.
        sort_code (db.Column): Bank sort code associated with the transaction. It is a required field.
        account_number (db.Column): Account number associated with the transaction. It is a required field.
        transaction_description (db.Column): Description or memo for the transaction. It is a required field.
        debit_amount (db.Column): The amount debited in the transaction. Optional.
        credit_amount (db.Column): The amount credited in the transaction. Optional.
        balance (db.Column): The resulting balance after the transaction. It is a required field.

    The model includes fields for both debit and credit amounts to accommodate different types of financial transactions.
    The balance field reflects the account balance after the transaction has been processed.
    """
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
    
    

    
class Recipient(db.Model):
    """
    Recipient model for storing information about the recipients of transactions in a Flask application.

    This model is designed to record details of individuals or entities that receive payments from
    users of the application. Each recipient is linked to a user, indicating who has added the recipient
    for transaction purposes. This linkage facilitates tracking and managing user-specific transaction
    recipients.

    Attributes:
        id (db.Column): Unique identifier for the recipient, serves as the primary key.
        user_id (db.Column): Foreign key linking the recipient to a user. It is a required field.
        name (db.Column): Name of the recipient. It is a required field.
        sort_code (db.Column): Bank sort code associated with the recipient's account. It is a required field.
        account_number (db.Column): Account number of the recipient. It is a required field.
        user (db.relationship): Relationship linking recipients back to the associated user. This relationship
                                allows for the retrieval of all recipients associated with a specific user.

    The relationship between `Recipient` and `Users` is defined to allow users to manage their list of
    recipients easily, enabling functionality such as adding, deleting, or selecting recipients for transactions.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) 
    name = db.Column(db.String(100), nullable=False)
    sort_code = db.Column(db.String(10), nullable=False)
    account_number = db.Column(db.String(20), nullable=False)
    user = db.relationship('Users', backref=db.backref('recipients', lazy=True))
    

    
    
class DDSO(db.Model): 
    """
    Model for Direct Debits and Standing Orders (DDSO) in a Flask application.

    This model is designed to store information about recurring financial transactions such as direct debits
    and standing orders set up by users. It tracks the details of these transactions, including the recipient,
    amount, frequency, and next payment date.

    Attributes:
        id (db.Column): Unique identifier for the DDSO record, serves as the primary key.
        user_id (db.Column): Foreign key linking the DDSO to a user. Indicates the user who has set up the DDSO. It is a required field.
        recipient (db.Column): The name or identifier of the recipient of the DDSO. It is a required field.
        reference_number (db.Column): A unique reference number for the DDSO, possibly used by the bank or financial institution. It is a required field.
        amount (db.Column): The amount of money to be transferred in each transaction. It is a required field.
        transaction_type (db.Column): Specifies whether the DDSO is a direct debit or a standing order. It is a required field.
        frequency (db.Column): The frequency of the DDSO payments (e.g., 'daily', 'monthly'). This field is optional and can be left blank if not applicable.
        next_payment_date (db.Column): The date when the next payment is due. It is a required field.

    This model facilitates the management of automatic, recurring payments from a user's account, providing a way
    to automate regular payments for bills, subscriptions, or any other recurring financial obligations.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient = db.Column(db.String(50),  nullable=False) 
    reference_number = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)
    frequency = db.Column(db.String(50))  # 'daily' 'monthly' etc
    next_payment_date = db.Column(db.Date, nullable=False)
    
    
    
class SupportTickets(db.Model):
    """
    Model for storing and managing support tickets in a Flask application.

    This model is designed to facilitate the creation, tracking, and management of user-generated support tickets.
    It includes information such as the user who submitted the ticket, the issue's title and detailed description,
    and the ticket's current status and priority level. This allows for an organized approach to addressing user
    concerns and requests.

    Attributes:
        id (db.Column): Unique identifier for the support ticket, serves as the primary key.
        user_id (db.Column): Foreign key linking the support ticket to a user. Represents the user who submitted the ticket. It is a required field.
        title (db.Column): Title of the support ticket, providing a brief overview of the issue. It is a required field.
        description (db.Column): Detailed description of the issue or request submitted by the user. It is a required field.
        reference_number (db.Column): A unique reference number assigned to the support ticket for tracking purposes. It is a required field.
        status (db.Column): Current status of the ticket, with possible values including 'new', 'in progress', 'closed', 'rejected'. Defaults to 'new'.
        priority (db.Column): Priority level of the ticket, with possible values including 'normal', 'high', 'urgent'. Defaults to 'normal'.
        category (db.Column): Category of the issue, helping to classify the ticket for better management. Possible values include 'general', 'fraud', 'service problem', 'money transfer'. Defaults to 'general'.
        created_at (db.Column): Timestamp when the ticket was created, defaulting to the current UTC time.

    The model supports a comprehensive ticketing system, allowing for efficient communication and resolution of user issues within the application.
    """
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
    """
    Model for tracking and managing locked user accounts in a Flask application.

    This model is essential for maintaining the security and integrity of the application by keeping a record
    of users whose accounts have been locked due to reasons such as failed login attempts, suspicious activity,
    or administrative actions. It stores the status of the account lock, the username of the locked account,
    and a unique identifier for each record.

    Attributes:
        id (db.Column): Unique identifier for the locked user record, serves as the primary key.
        is_account_locked (db.Column): Boolean flag indicating whether the account is locked. Defaults to True, indicating the account is actively locked.
        username (db.Column): The username of the locked account. This field is unique and required, ensuring that each locked account is distinctly identified.

    The model serves as a straightforward mechanism for administrators to review, manage, and unlock user accounts, thereby providing a layer of security management within the application.
    """
    id = db.Column(db.Integer, primary_key=True)
    is_account_locked = db.Column(db.Boolean, default = True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    
    
class Loans(db.Model):
    """
    Model for managing loan details in a Flask application.

    This model stores comprehensive information about loans issued to users, including the loan amount, 
    interest rate, payment schedule, and current status. It facilitates the tracking and management of 
    all aspects of loan transactions, from issuance to fulfillment, and supports various loan types and
    repayment strategies.

    Attributes:
        id (db.Column): Unique identifier for the loan record, serves as the primary key.
        user_id (db.Column): Foreign key linking the loan to a user. Represents the borrower. It is a required field.
        recipient (db.Column): The name or identifier of the loan recipient. It is a required field.
        product_id (db.Column): Identifier for the loan product type. It is a required field.
        transaction_type (db.Column): Type of transaction, defaulting to 'LOAN'. It is a required field.
        nominal_amount (db.Column): The original amount of the loan. It is a required field.
        interest (db.Column): The interest rate applied to the loan. It is a required field.
        installment_amount (db.Column): Amount to be paid in each installment. It is a required field.
        installments_number (db.Column): Total number of installments for the loan repayment. It is a required field.
        installments_paid (db.Column): Number of installments already paid. It is a required field.
        installments_to_be_paid (db.Column): Number of remaining installments to be paid. It is a required field.
        total_amount_to_be_repaid (db.Column): Total amount that will be paid after all installments, including interest. It is a required field.
        remaining_amount_to_be_repaid (db.Column): Amount still owed by the borrower. It is a required field.
        loan_cost (db.Column): Total cost of the loan to the borrower, including all fees and interest. It is a required field.
        interest_type (db.Column): Type of interest (e.g., fixed, variable). It is a required field.
        loan_status (db.Column): Current status of the loan (e.g., active, paid off). It is a required field.
        frequency (db.Column): Frequency of repayment installments (e.g., daily=1, monthly=30). It is a required field.
        loan_start_date (db.Column): Date when the loan was issued. Defaults to today. It is a required field.
        loan_end_date (db.Column): Date by which the loan should be fully repaid. It is a required field.
        next_payment_date (db.Column): Date of the next installment payment. It is a required field.
        currency_code (db.Column): Currency code for the loan amount (e.g., GBP, USD, EUR). It is a required field.
        loan_purpose (db.Column): Purpose for which the loan was issued. It is a required field.
        notes (db.Column): Additional notes or comments about the loan. Optional.

    The model supports detailed tracking of loans, including repayment progress and financial terms,
    aiding both users and administrators in monitoring and managing loan obligations.
    """
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
    frequency = db.Column(db.Integer, nullable=False) # eg. 1 = daily, 30 = monthly
    loan_start_date = db.Column(db.Date, nullable=False, default=date.today)
    loan_end_date = db.Column(db.Date, nullable=False)
    next_payment_date = db.Column(db.Date, nullable=False)
    currency_code = db.Column(db.String(3), nullable=False)
    loan_purpose = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.Text)