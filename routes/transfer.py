from flask import Blueprint, render_template, request, session, flash, url_for, redirect, abort
from flask_login import current_user, login_required, login_user
from forms.forms import TransferForm, LoginForm, DDSOForm, CreateTransactionForm, EditUserForm, AddRecipientForm
from datetime import date
from models.models import Users, Transaction, db, DDSO, LockedUsers, Recipient
from functools import wraps
import logging


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
    form = LoginForm()
    if request.method == "POST":
        if form.validate_on_submit():
            username = form.username.data
            
            # Sprawdź, czy zmienił się użytkownik próbujący się zalogować
            if session.get('last_login_attempt_user') != username:
                session['login_attempts'] = 0  # Resetuj licznik prób logowania dla nowego użytkownika
                session['last_login_attempt_user'] = username  # Zapisz nazwę użytkownika próbującego się zalogować
            
            # Najpierw sprawdź, czy użytkownik jest zablokowany
            locked_user = LockedUsers.query.filter_by(username=username).first()
            if locked_user:
                # Jeśli użytkownik jest zablokowany, od razu przekieruj do strony zablokowanego konta
                return render_template('account_locked.html', locked_user=locked_user)

            user = Users.query.filter_by(username=username).first()
            if user:
                if user.check_password(form.password.data): 
                    # Kontynuuj proces logowania, jeśli hasło jest poprawne
                    login_user(user)
                    flash("Login successful!", 'success')
                    logger.info(f"User '{user.username}' logged in to the system.")
                    # Resetuj licznik prób logowania
                    session['login_attempts'] = 0
                    return redirect(url_for('admin_dashboard_bp.admin_dashboard') if user.role == 'admin' else url_for('dashboard'))
                else:
                    flash('Invalid username or password.', 'danger')
                    # Zwiększ licznik prób logowania
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

        # W przypadku błędów walidacji lub nieznalezienia użytkownika, renderuj formularz ponownie
        return render_template('login.html', form=form)
    
    # Jeśli użytkownik jest już zalogowany, przekieruj do odpowiedniej strony
    if current_user.is_authenticated:
        flash("You are already logged in.", 'info')
        return redirect(url_for('admin_dashboard_bp.admin_dashboard') if current_user.role == 'admin' else url_for('dashboard'))

    return render_template('login.html', form=form)









ddso_bp = Blueprint('ddso_bp', __name__)

@ddso_bp.route('/direct_debit_standing_orders', methods=['GET', 'POST'])
@login_required
def ddso():
    
    user_transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    user_dd_so = DDSO.query.filter_by(user_id=current_user.id).all()
    last_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
    
    form = DDSOForm()
    
    if form.validate_on_submit():
        
        confirm_password = form.confirm_password.data
        
        # Check if the password is correct
        if not current_user.check_password(confirm_password):
            flash('Invalid password.', 'danger')
            return redirect(url_for('dashboard'))
        
        # Check if the recipient exists
        recipient_exist = Users.query.filter_by(username=form.recipient.data).first()
        
        
        if not recipient_exist:
            flash('Recipient account not found.', 'danger')
            return redirect(url_for('dashboard')) 
        
        
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
        return redirect(url_for('dashboard'))  

    return render_template('ddso.html', form=form, user=current_user, all_transactions=user_transactions, all_dd_so=user_dd_so,  last_transaction=last_transaction)
    


create_transaction_bp = Blueprint('create_transaction_bp', __name__)

@create_transaction_bp.route('/create_transaction', methods=['GET', 'POST'])  
@login_required
@admin_required
def create_transaction():
    
    all_users = Users.query.all()
    all_transactions = Transaction.query.all()
    form = CreateTransactionForm()

    # Loading users to choose from
    form.user_id.choices = [(user.id, user.username) for user in Users.query.all()]

    if form.validate_on_submit():
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

    return render_template('admin_dashboard_cm.html', all_users=all_users, form=form, all_transactions=all_transactions) 


edit_profile_bp = Blueprint('edit_profile_bp', __name__)

@edit_profile_bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required  
def edit_profile():
    form = EditUserForm()

    if form.validate_on_submit():
        current_user.email = form.email.data
        current_user.phone_number = form.phone_number.data
        current_user.country = form.country.data
        
        db.session.commit()
        flash('Your profile has been updated.')
        
        logger.warning(f"Change of personal data -  '{current_user.username}' ")
        return redirect(url_for('account_data'))

    elif request.method == 'GET':
        form.email.data = current_user.email
        form.phone.data = current_user.phone
        form.country.data = current_user.country
    else:
        print(form.errors) 

    user_transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', user=current_user, all_transactions=user_transactions)


add_recipient_bp = Blueprint('add_recipient_bp', __name__)

@add_recipient_bp.route('/add_recipient', methods=['GET', 'POST'])
@login_required
def add_recipient():
    form = AddRecipientForm()
    if form.validate_on_submit():
        # Check if there is a user with the given sort_code and account_number in the Users table
        user_exists = Transaction.query.filter_by(sort_code=form.sort_code.data, account_number=form.account_number.data).first()
        
        if user_exists:
            # The user exists, so we add a new recipient
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
        else:
            # The user does not exist, display an error message
            flash('The user with the given sort code and account number does not exist.', 'danger')

    # Get the user's transactions and customers to display on the page
    user_transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    user_recipients = Recipient.query.filter_by(user_id=current_user.id).all()
    last_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
    
    return render_template('add_recipient.html', form=form, user=current_user, all_transactions=user_transactions, last_transaction=last_transaction, all_recipients=user_recipients)

