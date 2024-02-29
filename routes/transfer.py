from flask import Blueprint, render_template, request, session, flash, url_for, redirect, abort
from flask_login import current_user, login_required, login_user
from forms.forms import TransferForm, LoginForm, DDSOForm, CreateTransactionForm, EditUserForm, AddRecipientForm
from datetime import date
from models.models import Users, Transaction, db, DDSO, LockedUsers, Recipient
from functools import wraps
import logging
import re


# Creating a logger
logger = logging.getLogger(__name__)

# Setting the logging level
logger.setLevel(logging.INFO)  

# Definition of your own formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Creating and configuring the handler
handler = logging.FileHandler('app.log')
handler.setFormatter(formatter)

# Adding a handler to the logger
logger.addHandler(handler)


def admin_required(func):
    """
    Decorator function to restrict access to routes to only administrators.

    This decorator checks if the current user is authenticated and has an 'admin' role. If the user
    does not meet these criteria, it logs an unauthorized access attempt with the user's username and
    the attempted access path. Then, it aborts the request with a 403 Forbidden HTTP status code, indicating
    that the server understands the request but refuses to authorize it.

    Usage:
        Simply decorate view functions that should be accessible only to administrators with `@admin_required`.

    Args:
        func (function): The view function to be decorated.

    Returns:
        function: The decorated view function with admin access control.
    """
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            # Logging an attempt to access a resource by an unauthorized user
            logger.error(f"No access to the resource - {request.path}  '{current_user.username}' ")
            # Returns a 403 Forbidden error
            abort(403)
        return func(*args, **kwargs)
    return decorated_view



transfer_bp = Blueprint('transfer_bp', __name__)

@transfer_bp.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer():
    """
    Handles money transfer operations between users.

    This route allows authenticated users to transfer money to another user's account. 
    It requires users to fill out a form providing details of the recipient's sort code 
    and account number, the amount to transfer, a description of the transaction, 
    and confirmation of the user's password for security purposes.

    The function performs several checks to ensure the security and validity of the transfer:
    - Validates the user's password to confirm their identity.
    - Checks if the recipient account exists based on the provided sort code and account number.
    - Ensures the user cannot transfer money to their own account.
    - Verifies the sender has sufficient funds for the transfer.

    If any of these checks fail, appropriate error messages are flashed, and the user is 
    redirected to a dashboard. Upon a successful transfer, the transaction details 
    are recorded for both the sender and recipient, balances are updated accordingly, 
    and the user is notified of the successful transfer.

    Args:
        None

    Returns:
        A redirection to the dashboard with a success message on successful transfer, 
        or back to the transfer form with an error message if the transfer cannot be completed.
    """
    form = TransferForm()

    if form.validate_on_submit():
        recipient_sort_code = form.recipient_sort_code.data
        recipient_account_number = form.recipient_account_number.data
        amount = form.amount.data
        transaction_description = form.transaction_description.data
        confirm_password = form.confirm_password.data
        
        # Check if the password is correct
        if not current_user.check_password(confirm_password):
            flash('Invalid password.', 'danger')
            return redirect(url_for('dashboard'))
     
        # Check whether the recipient exists by sort code and account number
        recipient = Users.query.join(Transaction).filter(Transaction.account_number == recipient_account_number, Transaction.sort_code == recipient_sort_code).first()
        
        
        if not recipient:
            flash('Recipient account not found.', 'danger')
            return redirect(url_for('dashboard')) 

        
        # Download the sender's last transaction to check their balance
        last_sender_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
        
        # Check if the sort code and account_number are the sender's data
        if recipient_sort_code == last_sender_transaction.sort_code and recipient_account_number == last_sender_transaction.account_number:
            flash('You can not send money to your own account!', 'danger')
            return redirect(url_for('dashboard'))
        
        
        if not last_sender_transaction or last_sender_transaction.balance < amount:
            flash('Insufficient funds.', 'danger')
            return redirect(url_for('dashboard')) 
        
        # The logic of making a transfer
        try:
            # Preparation of data for transactions
            transaction_date = date.today()
            
            # Sender balance update
            last_sender_balance = last_sender_transaction.balance - amount
            new_sender_transaction = Transaction(user_id=current_user.id, 
                                                transaction_date=transaction_date,
                                                transaction_type='FPO',
                                                sort_code=last_sender_transaction.sort_code,
                                                account_number=last_sender_transaction.account_number,
                                                transaction_description=transaction_description,
                                                debit_amount=amount,
                                                credit_amount = 0,
                                                balance=last_sender_balance)
            db.session.add(new_sender_transaction)
            
            
            # Find the customer's last transaction
            last_recipient_transaction = Transaction.query.filter_by(user_id=recipient.id).order_by(Transaction.id.desc()).first()
            
            
            # Recipient balance update
            last_recipient_balance = last_recipient_transaction.balance
            new_recipient_transaction = Transaction(user_id=recipient.id, 
                                                    transaction_date=transaction_date,
                                                    transaction_type='FPI',
                                                    sort_code=last_recipient_transaction.sort_code,
                                                    account_number=last_recipient_transaction.account_number,
                                                    transaction_description=transaction_description,
                                                    debit_amount = 0,
                                                    credit_amount=amount,
                                                    balance=last_recipient_balance + amount)
            db.session.add(new_recipient_transaction)
            db.session.commit()
            flash('Transfer successful!', 'success')
            return redirect(url_for('dashboard'))
        
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Transfer failed.', 'danger')
            return render_template('transfer.html', form=form)
    
    else:
        print(form.errors)      
    user_transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', user=current_user, all_transactions=user_transactions)





login_bp = Blueprint('login_bp', __name__)

@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handles the login process for users.

    This function serves the login page and processes login attempts. On a GET request, it simply renders the login form. 
    On a POST request, it validates the submitted form and attempts to log the user in. It checks if the user exists and 
    whether their password matches. It also handles cases where the user has been locked out due to too many failed login 
    attempts by checking against the `LockedUsers` table.

    If the user is already logged in, it redirects them to the appropriate dashboard based on their role. For an admin, it 
    redirects to the admin dashboard, otherwise to the user dashboard.

    The function implements a security measure to prevent brute force attacks by tracking the number of failed login attempts. 
    If a user exceeds a predefined number of failed attempts, their account is locked, and they are redirected to an account 
    locked page. The counter of failed attempts is reset when a user successfully logs in or when a different user attempts to 
    log in.

    Returns:
        On GET: Renders and returns the login form.
        On POST: If form validation fails, or if the user cannot be authenticated, re-renders the login form with an error message.
                 If the user is authenticated, redirects to the appropriate dashboard based on the user's role.
                 If the user's account is locked, renders and returns the account locked page.
        If the user is already logged in, redirects to the appropriate dashboard immediately without rendering the login form.
    """
    form = LoginForm()
    if request.method == "POST":
        if form.validate_on_submit():
            username = form.username.data
            
            # Check if the user trying to log in has changed
            if session.get('last_login_attempt_user') != username:
                # Reset login attempt counter for new user
                session['login_attempts'] = 0  
                # Record the name of the user trying to log in
                session['last_login_attempt_user'] = username  
            
            # First, check if the user is blocked
            locked_user = LockedUsers.query.filter_by(username=username).first()
            if locked_user:
                # If the user is blocked, immediately redirect to the blocked account page
                return render_template('account_locked.html', locked_user=locked_user)

            user = Users.query.filter_by(username=username).first()
            if user:
                if user.check_password(form.password.data): 
                    # Continue the login process if your password is correct
                    login_user(user)
                    flash("Login successful!", 'success')
                    logger.info(f"User '{user.username}' logged in to the system.")
                    # Reset login attempt counter
                    session['login_attempts'] = 0
                    return redirect(url_for('admin_dashboard_bp.admin_dashboard') if user.role == 'admin' else url_for('dashboard'))
                else:
                    flash('Invalid username or password.', 'danger')
                    #Increase the login attempt counter
                    session['login_attempts'] = session.get('login_attempts', 0) + 1
                    logger.warning(f"Failed login attempt for user '{user.username}'.")
                    if session['login_attempts'] >= 3 and user:
                        locked_user = LockedUsers(username=user.username)
                        db.session.add(locked_user)
                        db.session.commit()
                        logger.critical(f"Account for user '{user.username}' has been locked.")
                        session['login_attempts'] = 0
                        flash("Your account has been locked after exceeding the maximum number of failed login attempts.")
                        return render_template('account_locked.html', locked_user=locked_user)
            else:
                flash('User not found.', 'danger')

        # In case of validation errors or user not found, re-render the form
        return render_template('login.html', form=form)
    
    # If the user is already logged in, redirect to the appropriate page
    if current_user.is_authenticated:
        flash("You are already logged in.", 'info')
        return redirect(url_for('admin_dashboard_bp.admin_dashboard') if current_user.role == 'admin' else url_for('dashboard'))

    return render_template('login.html', form=form)




ddso_bp = Blueprint('ddso_bp', __name__)

@ddso_bp.route('/direct_debit_standing_orders', methods=['GET', 'POST'])
@login_required
def ddso():
    """
    Handles the creation and display of direct debits and standing orders (DDSO) for the current user.

    This view function performs multiple tasks based on the HTTP method:
    - GET: Retrieves and displays a list of the user's transactions, direct debits, and standing orders,
           along with a form to create a new DDSO.
    - POST: Processes the submitted form to create a new DDSO. It performs several checks such as
           validating the form data, verifying the user's password, and ensuring the recipient exists.
           If validation passes, a new DDSO is created and saved to the database.

    Form validation and submission:
    - Upon form submission, the function checks if the provided password matches the current user's password.
    - It then checks if the specified recipient exists in the database.
    - If both checks pass, it attempts to create and save a new DDSO record.
    - Successful creation of a DDSO results in a redirection to the DDSO page with a success message.
    - If any step fails, the user is redirected back to the DDSO page with an appropriate error message.

    Returns:
        - A rendered template ('ddso.html') displaying the DDSO form and the user's existing DDSOs and transactions
          if the method is GET.
        - A redirection to the DDSO page, either with a success message upon successful DDSO creation or
          with an error message if any part of the process fails when the method is POST.
    """
    user_transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    user_dd_so = DDSO.query.filter_by(user_id=current_user.id).all()
    last_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
    
    form = DDSOForm()
    
    if form.validate_on_submit():
        
        confirm_password = form.confirm_password.data
        
        # Check if the password is correct
        if not current_user.check_password(confirm_password):
            flash('Invalid password.', 'danger')
            return redirect(url_for('ddso_bp.ddso'))
        
        # Check if the recipient exists
        recipient_exist = Users.query.filter_by(username=form.recipient.data).first()
        
        
        if not recipient_exist:
            flash('Recipient account not found.', 'danger')
            return redirect(url_for('ddso_bp.ddso')) 
        
        try:
            # Creating a new order based on data from the form
            new_dd_so = DDSO(
                            user_id=current_user.id,  
                            recipient=form.recipient.data,
                            reference_number=form.reference_number.data,
                            amount=form.amount.data,
                            next_payment_date=form.next_payment_date.data,
                            transaction_type=form.transaction_type.data,
                            frequency=form.frequency.data)
            
            db.session.add(new_dd_so)
            db.session.commit()
            flash('New Direct Debit / Standing Order added successfully!')
            return redirect(url_for('ddso_bp.ddso'))  
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to add DDSO: {e}")
            flash('An error occurred. Please try again.', 'danger')
            return redirect(url_for('ddso_bp.ddso')) 

    return render_template('ddso.html', form=form, user=current_user, all_transactions=user_transactions, all_dd_so=user_dd_so,  last_transaction=last_transaction)
    






create_transaction_bp = Blueprint('create_transaction_bp', __name__)

@create_transaction_bp.route('/create_transaction', methods=['GET', 'POST'])  
@login_required
@admin_required
def create_transaction():
    """
    Creates first transaction with specified details, ensuring uniqueness.

    This route handles the creation of first transaction by an admin. It presents a form to input transaction details,
    and upon submission, performs several validations: it checks that the 'sort_code' is in the format XX-XX-XX,
    the 'account_number' consists of 8 digits, and that no existing transaction matches the provided 'user_id',
    'sort_code', or 'account_number' to ensure the uniqueness of the transaction.

    If the submitted form data passes all validations, a new Transaction object is created and saved to the database.
    A success message is flashed, and the admin is redirected to the dashboard. If the form submission fails any validation,
    an error message is flashed, and the form is re-rendered for correction.

    The function is accessible only to logged-in users with admin privileges, enforced by decorators.

    Returns:
        On GET request: Renders and returns the transaction creation form with a list of all users.
        On POST request: If form validation is successful and the transaction is unique, redirects to the admin dashboard.
                         If form validation fails or the transaction is not unique, re-renders the form with an error message.
    """
    all_users = Users.query.all()
    form = CreateTransactionForm()

    # Loading users to choose from
    form.user_id.choices = [(user.id, user.username) for user in Users.query.all()]

    if form.validate_on_submit():
        # Checking the sort_code format
        if not re.match(r'^\d{2}-\d{2}-\d{2}$', form.sort_code.data):
            flash('Sort code must be in the format XX-XX-XX.', 'error')
            return render_template('admin_dashboard_cm.html', all_users=all_users, form=form)
        
        # Checking the account_number format
        if not re.match(r'^\d{8}$', form.account_number.data):
            flash('Account number must be 8 digits format.', 'error')
            return render_template('admin_dashboard_cm.html', all_users=all_users, form=form)
        
        
        # Checking if transaction with the same user_id, sort_code, or account_number already exists
        existing_transaction = Transaction.query.filter(
            (Transaction.user_id == form.user_id.data) |
            (Transaction.sort_code == form.sort_code.data) |
            (Transaction.account_number == form.account_number.data)).first()

        if existing_transaction:
            flash('A transaction with the provided user ID, sort code, or account number already exists.', 'error')
            return render_template('admin_dashboard_cm.html', all_users=all_users, form=form)
        
        
        # Creating a transaction object
        new_transaction = Transaction(user_id=form.user_id.data,
                                        transaction_date=form.transaction_date.data,
                                        transaction_type=form.transaction_type.data,
                                        sort_code=form.sort_code.data,
                                        account_number=form.account_number.data,
                                        transaction_description=form.transaction_description.data,
                                        debit_amount=form.debit_amount.data,
                                        credit_amount=form.credit_amount.data,
                                        balance=form.balance.data)

        db.session.add(new_transaction)
        db.session.commit()

        flash('Transaction created successfully!', 'success')
        return redirect(url_for('admin_dashboard_cm')) 

    return render_template('admin_dashboard_cm.html', all_users=all_users, form=form) 



edit_profile_bp = Blueprint('edit_profile_bp', __name__)

@edit_profile_bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required  
def edit_profile():
    """
    Allows the current logged-in user to edit and update their profile information.

    This route handler supports two HTTP methods: GET and POST. On a GET request, it pre-populates the 
    EditUserForm with the current user's existing profile information, including email, phone number, 
    and country. On a POST request, it processes the submitted form to update the user's profile data.

    Steps:
    1. On GET request: The form fields are pre-filled with the current user's profile information for
       email, phone number, and country, allowing the user to see their current settings and make any
       desired changes.
    2. On POST request: The form is validated, and if the validation is successful, the current user's
       profile information is updated in the database with the provided values. A flash message is shown
       to inform the user of the successful update. In case of an exception (e.g., database error), the
       transaction is rolled back, an error flash message is shown, and the error is logged.

    Parameters:
    - None directly, but operates on the data submitted through the EditUserForm and the current user's 
      session information.

    Returns:
    - On GET request: displaying the form pre-filled with the current user's profile data.
    - On POST request (successful update): Redirects to the 'account_data' route with a success flash message.
    - On POST request (validation failure or exception): Redirects to the 'account_data' route with an 
      error flash message and does not update the user's profile.

    Security:
    - The route is protected with the @login_required decorator, ensuring that only authenticated users 
      can access and modify their own profile information.
    - Input validation is performed through the EditUserForm to protect against invalid or malicious data.
    - Changes in personal data are logged for auditing purposes.
    """
    form = EditUserForm()
    if request.method == 'GET':
        form.email.data = current_user.email
        form.phone_number.data = current_user.phone_number
        form.country.data = current_user.country

    if form.validate_on_submit():
        current_user.email = form.email.data
        current_user.phone_number = form.phone_number.data
        current_user.country = form.country.data
        
        try:
            db.session.commit()
            flash('Your profile has been updated.')
            logger.warning(f"Change of personal data -  '{current_user.username}' ")
            return redirect(url_for('account_data'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.')
            logger.error(f"Error updating profile: {e}")
            return redirect(url_for('account_data'))
    

    #user_transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    #return render_template('dashboard.html', user=current_user, all_transactions=user_transactions)




add_recipient_bp = Blueprint('add_recipient_bp', __name__)

@add_recipient_bp.route('/add_recipient', methods=['GET', 'POST'])
@login_required
def add_recipient():
    """
    Add a new recipient for the current user.

    This view function handles both GET and POST requests to add a new recipient
    to the current user's list of recipients. It utilizes an `AddRecipientForm` 
    to collect recipient details from the user. Upon submission, the function
    checks for the existence of both the specified user and transaction in the database 
    to ensure the recipient's details are valid and associated with a known transaction.

    If the recipient's details are valid and the user and transaction exist, 
    a new `Recipient` instance is created and added to the database. The user 
    is then redirected back to the same page with a success message. If there are 
    errors, such as the user or transaction not existing, or a database error during 
    the creation of the new recipient, appropriate error messages are displayed to the user.

    Additionally, the function retrieves and displays all recipients associated with 
    the current user.

    Returns:
        A rendered template (`add_recipient.html`) displaying the form for adding a
        new recipient, along with a list of existing recipients. Flash messages are used 
        to convey the outcome of the form submission (success or error).
    """
    form = AddRecipientForm()
    if form.validate_on_submit():
        # Check if there is a transaction with the given sort_code and account_number 
        transaction_exists = Transaction.query.filter_by(sort_code=form.sort_code.data, account_number=form.account_number.data).first()
        # Check if user exist in Users table
        user_exists = Users.query.filter_by(username = form.name.data).first()
        
        if user_exists and transaction_exists:
            try:
                new_recipient = Recipient(
                    user_id=current_user.id,
                    name=form.name.data,
                    sort_code=form.sort_code.data,
                    account_number=form.account_number.data
                )
                db.session.add(new_recipient)
                db.session.commit()
                flash('New recipient added successfully!', 'success')
                return redirect(url_for('add_recipient_bp.add_recipient'))
            except Exception as e:
                db.session.rollback()
                flash('An error occurred. Please try again.', 'danger')
                logger.error(f"Error adding new recipient: {e}")
        else:
            # The user does not exist, display an error message
            flash('The user with the given sort code and account number does not exist.', 'danger')
            
   

    # Get the user's transactions and customers to display on the page
    user_recipients = Recipient.query.filter_by(user_id=current_user.id).all()
    last_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
    
    return render_template('add_recipient.html', form=form, user=current_user, last_transaction=last_transaction, all_recipients=user_recipients)

