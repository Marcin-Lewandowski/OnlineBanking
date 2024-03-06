# Copyright (c) 2024 Marcin Lewandowski
# 
# This software is licensed under the MIT License. See the LICENSE file in the
# top-level directory of this distribution for the full license text.


from flask import Flask, render_template, flash, request, url_for, redirect, session
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, logout_user, current_user, login_required
from forms.forms import ChangePasswordForm
from datetime import timedelta, date, datetime
from routes.transfer import transfer_bp, login_bp, ddso_bp, create_transaction_bp, edit_profile_bp, add_recipient_bp
from routes.my_routes import grocery1_bp, grocery2_bp, grocery3_bp, grocery4_bp, gas_bp, power_bp, petrol_bp, clothes_bp, water_bp, add_customer_bp
from routes.my_routes_hc import send_query_bp, process_query_bp, read_message_bp, send_message_for_query_bp, send_message_for_message_bp, delete_messages_for_query_bp
from routes.my_routes_hc import delete_query_confirmation_bp, show_statement_for_customer_bp, edit_customer_information_bp
from routes.my_routes_statement import download_transactions_bp, download_transactions_csv_bp
from routes.my_routes_admin import transactions_filter_bp, reports_and_statistics_bp, delete_user_bp, update_customer_information_bp, find_tickets_bp, block_customer_bp, unlock_access_bp
from routes.my_routes_admin import admin_dashboard_bp, logs_filtering_bp, cwc_bp
from routes.my_routes_loans import apply_consumer_loan_bp, apply_car_loan_bp, apply_home_renovation_loan_bp, apply_test_loan_bp
from models.models import Users, Transaction, db, Recipient, DDSO, SupportTickets, LockedUsers, Loans
from sqlalchemy import func
from routes.transfer import admin_required
from flask_apscheduler import APScheduler
from flask_talisman import Talisman
import traceback

scheduler = APScheduler()

login_manager = LoginManager()
login_manager.login_view = 'login_bp.login'



def process_ddso_payments():
    """
    Processes pending Direct Debit Standing Order (DDSO) payments for the current day.
    
    For each pending payment, the function looks up the sender and recipient in the user database,
    updates their balances by adding new transactions, and updates the next payment date depending
    on the payment frequency (daily or monthly). This process also includes exception handling for
    transaction-related errors, committing changes to the database only if all operations are successful.
    
    Exceptions:
        Raises an Exception if any database operation fails. The function rolls back all changes
        and prints an appropriate error message.
    
    Returns:
        None. Outputs processing information to the standard output.
    """
    with app.app_context():
        today = datetime.today().date()
        pending_payments = DDSO.query.filter(DDSO.next_payment_date <= today).all()
        
        if len(pending_payments) > 0:
            # Display the number of records in pending_payments
            print("Number of pending payments:", len(pending_payments))

            for payment in pending_payments:
                recipient_name = payment.recipient
                
                # Get the recipient ID based on recipient_name
                recipient_user = Users.query.filter_by(username=recipient_name).first()
                print("Recipient: ", recipient_user.username)
                sender = Users.query.filter_by(id = payment.user_id).first()
                print("Sender: ", sender.username)
                
                if recipient_user:
                    recipient_id = recipient_user.id

                    # Now you can use recipient_id for further operations, e.g. to search for a transaction
                    last_recipient_transaction = Transaction.query.filter_by(user_id=recipient_id).order_by(Transaction.id.desc()).first()
                    
                    print("Recipient ID: ", last_recipient_transaction.user_id)
                    print("Recipient balance: ", last_recipient_transaction.balance)
                    last_sender_transaction = Transaction.query.filter_by(user_id=payment.user_id).order_by(Transaction.id.desc()).first()
                    print("Sender ID: ", last_sender_transaction.user_id)
                    print("Sender balance: ", last_sender_transaction.balance)
                    

                    # If there is a recent transaction, proceed further
                    if last_recipient_transaction:
                        # Payment processing logic
                        
                        print(last_recipient_transaction.balance)
                        try:
                            # Preparation of data for transactions
                            transaction_date = date.today()
                            
                            # Sender balance update
                            new_sender_balance = last_sender_transaction.balance - payment.amount
                            print("New sender balance: ", new_sender_balance)
                            new_sender_transaction = Transaction(user_id=payment.user_id, 
                                                transaction_date=transaction_date,
                                                transaction_type=payment.transaction_type,
                                                sort_code=last_sender_transaction.sort_code,
                                                account_number=last_sender_transaction.account_number,
                                                transaction_description=payment.reference_number,
                                                debit_amount=payment.amount,
                                                credit_amount = 0,
                                                balance=new_sender_balance)
                            db.session.add(new_sender_transaction)
                            
                            
                            # Recipient balance update
                            new_recipient_balance = last_recipient_transaction.balance + payment.amount
                            print("New recipient balance: ", new_recipient_balance)
                            new_recipient_transaction = Transaction(user_id=recipient_id, 
                                                                    transaction_date=transaction_date,
                                                                    transaction_type='FPI',
                                                                    sort_code=last_recipient_transaction.sort_code,
                                                                    account_number=last_recipient_transaction.account_number,
                                                                    transaction_description=payment.reference_number,
                                                                    debit_amount = 0,
                                                                    credit_amount=payment.amount,
                                                                    balance=new_recipient_balance)
                            db.session.add(new_recipient_transaction)
                            
                            #(Let's assume the payment is monthly - timedelta(days=30), but for tests daily timedelta(days=1))
                            if payment.frequency == 'daily':
                                payment.next_payment_date = payment.next_payment_date + timedelta(days=1)
                                
                            if payment.frequency == 'monthly':
                                payment.next_payment_date = payment.next_payment_date + timedelta(days=30)
                                
                            db.session.commit()
                            print('Direct debit sended successful!')
                            
                            
                        except Exception as e:
                            db.session.rollback()
                            # Print the error message and the full call stack
                            print('An error occurred. Transfer failed:', e)
                            traceback.print_exc()   
                
        else:
            print("No pending payments.")
            # End of function if there is no payment to process
            return  
        
        
        
        
        
        
def process_loans_payments():
    """
    Processes pending loan payment transactions for the current day. It updates the balances of both 
    the sender (loan borrower) and the recipient (typically a bank) for each loan payment due today.
    
    For each pending loan payment:
    - Retrieves the recipient (bank) and sender (borrower) details from the Users table.
    - Calculates the new balances for both the sender and recipient based on the loan installment amount.
    - Updates the transaction records for both parties.
    - Updates loan payment details such as the number of installments paid, remaining installments, 
      remaining amount to be repaid, and the next payment date.
    - If all installments are paid, the loan record is deleted.
    
    The function commits all changes to the database and handles any exceptions by rolling back the 
    transaction to ensure data integrity. It outputs the status of the transaction processing to the console.
    
    Exceptions:
        Raises an Exception and rolls back the database changes if an error occurs during the transaction 
        processing, printing the error message and a stack trace to the console.
    
    Returns:
        None. This function prints the status of loan payment processing, including any errors, 
        directly to the console.
    """
    with app.app_context():
        today = datetime.today().date()
        pending_loans_payments = Loans.query.filter(Loans.next_payment_date <= today).all()
        
        if len(pending_loans_payments) > 0:
            # Display the number of records in pending_loans_payments
            print()
            print('LOANS: ')
            print()
            print()
            print("Number of loan installments pending: ", len(pending_loans_payments))
            
            for loan_payment in pending_loans_payments:
                
                # Get the recipient ID (Imperial Bank ) based on id
                recipient = Users.query.filter_by(id = 25).first()
                print("Recipient: ", recipient.username)
                
                # Get the sender ID based on id as user_id from the Loans table
                sender = Users.query.filter_by(id = loan_payment.user_id).first()
                print("Sender: ", sender.username)
                
                if recipient:
                    # Searches for the last Imperial bank transaction
                    last_recipient_transaction = Transaction.query.filter_by(user_id = 25).order_by(Transaction.id.desc()).first()
                    
                    # Search for the last sender's transaction of the loan installment
                    last_sender_transaction = Transaction.query.filter_by(user_id = loan_payment.user_id).order_by(Transaction.id.desc()).first()
                    
                    # If there is a recent bank transaction, proceed further
                    if last_recipient_transaction:
                        # Payment processing logic
                        try:
                            # Preparation of data for transactions
                            transaction_date = date.today()
                            
                            # Sender balance update
                            new_sender_balance = last_sender_transaction.balance - loan_payment.installment_amount
                            print("New sender balance: ", new_sender_balance)
                            new_sender_transaction = Transaction(user_id=loan_payment.user_id, 
                                                transaction_date=transaction_date,
                                                transaction_type=loan_payment.transaction_type,
                                                sort_code=last_sender_transaction.sort_code,
                                                account_number=last_sender_transaction.account_number,
                                                transaction_description=loan_payment.loan_purpose,
                                                debit_amount=loan_payment.installment_amount,
                                                credit_amount = 0,
                                                balance=new_sender_balance)
                            db.session.add(new_sender_transaction)
                            
                            
                            # Recipient balance update - Imperial Bank
                            new_recipient_balance = last_recipient_transaction.balance + loan_payment.installment_amount
                            print("New recipient balance: ", new_recipient_balance)
                            new_recipient_transaction = Transaction(user_id=25, 
                                                                    transaction_date=transaction_date,
                                                                    transaction_type='FPI',
                                                                    sort_code=last_recipient_transaction.sort_code,
                                                                    account_number=last_recipient_transaction.account_number,
                                                                    transaction_description=loan_payment.loan_purpose,
                                                                    debit_amount = 0,
                                                                    credit_amount = loan_payment.installment_amount,
                                                                    balance=new_recipient_balance)
                            db.session.add(new_recipient_transaction)
                            
                            # update the number of paid and unpaid installments, update the remaining amount to be repaid
                            # setting the date of the next transfer
                            
                            loan_payment.installments_paid += 1
                            loan_payment.installments_to_be_paid -= 1
                            loan_payment.remaining_amount_to_be_repaid -= loan_payment.installment_amount
                            loan_payment.next_payment_date += timedelta(days = loan_payment.frequency)
                            
                            if loan_payment.installments_to_be_paid == 0:
                                db.session.delete(loan_payment)
                                print('Loan paid !!!')
                            
                            db.session.commit()
                            print('Loans standing orders sended successful!')
                            
                        except Exception as e:
                            db.session.rollback()
                            # Print the error message and the full call stack
                            print('An error occurred. Transfer failed:', e)
                            traceback.print_exc()
                            
                else:
                    print('Recipient not found')
                    # End of the function if the recipient - Bank - has not been found, which is unrealistic ;)
                    return          
        else:
            print("No pending loan payments.")
            # Terminate the function if there is no payment to process
            return  
        
        
        
        
        

def create_app():
    """
    Initializes and configures the Flask application, setting up security, database connections,
    scheduled tasks, and blueprints for different parts of the application.
    
    The function configures:
    - Flask application instance with secret key and database URI.
    - Content Security Policy (CSP) through Talisman for enhancing security.
    - CSRF protection to safeguard against Cross-Site Request Forgery attacks.
    - Login manager for handling user authentication.
    - SQLAlchemy database instance for ORM-based database interactions.
    - APScheduler for scheduling background tasks.
    - Flask blueprints for modularizing the application into distinct components, each responsible
      for a set of routes and functionalities.
    
    Scheduled tasks for processing payments and loan installments are added with a delay after 
    the application start, demonstrating how to execute background operations at specific times.
    
    Returns:
        Flask app: The configured Flask application instance ready to run.
    
    Note:
        This function must be called to create a Flask application instance before running the app.
        The `SECRET_KEY`, `SQLALCHEMY_DATABASE_URI`, and other configurations should be customized 
        and secured as per the deployment environment.
    """
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'bc684cf3981dbcacfd60fc34d6985095'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ib_database_users.db'  # Setting the database name
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Recommended for performance
    
    
    csp = {
    'default-src': '\'self\'',
    'script-src': [
        '\'self\'',
        '\'nonce\''
    ],
    'img-src': [
        '\'self\'',
        'data:'
    ],
    'style-src': '\'self\'',
}


    # Initialize Talisman with your CSP configuration
    
    Talisman(app, content_security_policy=None, 
             content_security_policy_nonce_in=['script-src'], 
             session_cookie_secure=False, # Forces cookies to be used only via HTTPS
             force_https=False, # Redirects all requests to HTTPS if True
             # force_https_permanent=True, # Adds a Strict-Transport-Security header with includeSubDomains and max-age
             frame_options='SAMEORIGIN', # Sets X-Frame-Options to SAMEORIGIN, protecting against clickjacking
             # strict_transport_security=True, # enables HSTS
             # strict_transport_security_max_age=31536000,  # for example for a year
             # strict_transport_security_include_subdomains=True, # HSTS links also for subdomains,
             # strict_transport_security_preload=True  # adds a preload directive to the HSTS header
             )

    app.permanent_session_lifetime = timedelta(minutes = 45)
    
    csrf = CSRFProtect(app)
    
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Initializing db with app object
    db.init_app(app)
    
    # Scheduler initialization
    scheduler.init_app(app)
    scheduler.start()
    
    # Add a task to the scheduler cyclically trigger='cron'
    
    # Run the task only once, shortly after starting the application trigger='date'
    scheduler.add_job(id='process_ddso', func=process_ddso_payments, trigger = 'date', run_date = datetime.now() + timedelta(seconds = 5))
    scheduler.add_job(id='process_loans', func=process_loans_payments, trigger = 'date', run_date = datetime.now() + timedelta(seconds = 10))

    # Blueprint registration
    app.register_blueprint(transfer_bp)
    app.register_blueprint(login_bp)
    app.register_blueprint(ddso_bp)
    app.register_blueprint(create_transaction_bp)
    app.register_blueprint(edit_profile_bp)
    app.register_blueprint(add_customer_bp)
    app.register_blueprint(add_recipient_bp)
    app.register_blueprint(grocery1_bp)
    app.register_blueprint(grocery2_bp)
    app.register_blueprint(grocery3_bp)
    app.register_blueprint(grocery4_bp)
    app.register_blueprint(gas_bp)
    app.register_blueprint(power_bp)
    app.register_blueprint(petrol_bp)
    app.register_blueprint(clothes_bp)
    app.register_blueprint(water_bp)
    
    app.register_blueprint(send_query_bp)
    app.register_blueprint(process_query_bp) 
    app.register_blueprint(read_message_bp)
    app.register_blueprint(send_message_for_query_bp)
    app.register_blueprint(send_message_for_message_bp)
    app.register_blueprint(delete_messages_for_query_bp)
    app.register_blueprint(delete_query_confirmation_bp)
    app.register_blueprint(show_statement_for_customer_bp)
    app.register_blueprint(edit_customer_information_bp)
    
    app.register_blueprint(download_transactions_bp)
    app.register_blueprint(download_transactions_csv_bp)
    
    app.register_blueprint(transactions_filter_bp)
    app.register_blueprint(reports_and_statistics_bp)
    app.register_blueprint(delete_user_bp)
    app.register_blueprint(update_customer_information_bp)
    app.register_blueprint(find_tickets_bp)
    app.register_blueprint(block_customer_bp)
    app.register_blueprint(unlock_access_bp)
    app.register_blueprint(admin_dashboard_bp)
    app.register_blueprint(logs_filtering_bp)
    app.register_blueprint(cwc_bp)
    
    app.register_blueprint(apply_consumer_loan_bp)
    app.register_blueprint(apply_car_loan_bp)
    app.register_blueprint(apply_home_renovation_loan_bp)
    app.register_blueprint(apply_test_loan_bp)
    
    return app



app = create_app()
  
def initialize_app():
    """
    Initializes the application's database and populates it with sample data.
    
    This function performs the following actions within the application's context:
    - Creates all database tables based on the SQLAlchemy models defined elsewhere in the application.
    - Calls a function to create a sample user, demonstrating how to pre-populate the database with 
      initial data for development or testing purposes.
    
    Note:
        This function should be called after the Flask application and its configurations have been 
        initialized, but before the application starts serving requests. It requires the application 
        context to be pushed, ensuring that the database operations are performed within the correct 
        context.
        
        The `create_sample_user` function must be defined elsewhere and is responsible for inserting 
        a predefined user or set of users into the database, which can be useful for testing or 
        initial setup purposes.
        
        It is important to ensure that `db.create_all()` does not overwrite existing data when called 
        in a production environment. Consider using migrations for managing database schema changes 
        in a more controlled manner, especially for applications already in production.
    """
    with app.app_context():
        db.create_all()
        create_sample_user()
        
        
        
@app.before_request
def initialize_database():
    """
    Ensures that all database tables are created before handling any request and makes the session permanent.
    
    This function is executed before each request within the Flask application context. It performs
    two primary actions:
    - Calls `db.create_all()` to ensure that all database tables defined by the SQLAlchemy models are 
      created. This operation is idempotent, meaning it will not attempt to recreate tables that already exist.
    - Sets `session.permanent` to True, making the session permanent. This extends the session lifetime
      beyond the default duration, requiring manual session termination or expiration based on the 
      `PERMANENT_SESSION_LIFETIME` configuration.
    
    Note:
        Using `db.create_all()` on every request can impact performance and is not recommended for production 
        environments. It is typically used during development or testing for convenience. For production, 
        consider using database migrations to manage schema changes.
        
        The permanent session feature is useful for extending user sessions, but session management should 
        be carefully designed to balance user experience with security considerations.
        
        Ensure that the Flask application is properly configured to handle permanent sessions, including 
        configuring the `PERMANENT_SESSION_LIFETIME` as needed.
    """
    db.create_all()
    session.permanent = True
    
    
@login_manager.user_loader
def load_user(user_id):
    """
    Retrieves a user object from the database for the given user_id, facilitating user session management in Flask-Login.
    
    This callback function is used by Flask-Login to load a user's object from the user ID stored in the session. It is 
    essential for managing user sessions in Flask applications that utilize Flask-Login for authentication. The function 
    queries the database for the user ID and returns the user object if found, or None if no user is found with that ID.
    
    Parameters:
    - user_id (str): The user ID that Flask-Login seeks to reload from the session. It is assumed to be a string that 
      can be converted to an integer, representing the user's unique identifier in the database.
    
    Returns:
    - A user instance if a user with the provided user_id exists in the database; otherwise, None.
    
    Note:
        It is important that the user_id used and stored in the session is unique to each user and corresponds directly 
        to the user's ID in the database. This function must be able to handle the conversion of the user_id from a string 
        (as Flask-Login stores it in the session) to the appropriate type expected by the database query method (typically an integer).
        
        The Users model and query method used should be defined elsewhere in the application, with Users.query.get() 
        being an SQLAlchemy ORM query for fetching a user by their ID from the Users table.
    """
    return Users.query.get(int(user_id))
    
# The following code is optional and is used to add an example user during database initialization
def create_sample_user():
    """
    Adds an example user to the database, specifically an admin account, if it doesn't already exist.
    
    This function performs a check in the database for an existing user with the username 'admin'. If no such user 
    exists, it proceeds to create a new admin user with predefined credentials and roles, and then saves this new user 
    to the database.
    
    The purpose of this function is to ensure that there is at least one user (in this case, an administrator) 
    in the database upon initialization, allowing for immediate access to the system for testing or administrative 
    purposes. 
    
    Attributes for the admin user, such as username, role, email, phone number, and country, are hardcoded within 
    the function, with a method called to set the user's password securely.
    
    Note:
        This function should be used with caution, especially in production environments, to prevent creating 
        default accounts that could be exploited. It's recommended to modify or remove this function before deploying 
        the application publicly or to ensure that the account's password is changed immediately after creation.
        
        The `Users` model and the `set_password` method must be defined elsewhere in the application. The `Users` 
        model should include fields for username, role, email, phone number, and country, and the `set_password` 
        method should handle password hashing.
    """

    existing_user = Users.query.filter_by(username='admin').first()

    if not existing_user:
        # Creating an admin account
        admin = Users(username='admin', role='admin', email='admin@ib.co.uk', phone_number='+447710989456', country='UK')
        admin.set_password('admin_password')
        db.session.add(admin)
        db.session.commit()  
        

    

@app.route('/', methods=['GET'])
def index():
    """
    Renders and serves the home page of the application for HTTP GET requests.
    
    This view function is mapped to the root URL ("/") and is responsible for handling HTTP GET requests by 
    rendering and returning the 'index.html' template. It acts as the entry point for users accessing the 
    web application, presenting the initial user interface or landing page.
    
    The function exclusively handles GET requests, reflecting its primary role in delivering the static content 
    of the home page without processing any form submissions or other data sent via POST requests.
    
    Returns:
        The rendered 'index.html' template as an HTTP response to the client, providing the markup and content 
        of the application's home page.
    
    
    """
    return render_template('index.html')

@app.route('/main', methods=['GET'])
def main():
    """
    Similar to index function
    """
    return render_template('index.html')

@app.route('/about_the_project', methods=['GET'])
def about_the_project():
    """
    Renders and serves the "About the Project" page of the application for HTTP GET requests.
    
    """
    return render_template('about_the_project.html')

@app.route('/author', methods=['GET'])
def author():
    return render_template('author.html')

@app.route('/privacy', methods=['GET'])
def privacy():
    return render_template('privacy.html')

@app.route('/contact_us', methods=['GET'])
def contact_us():
    return render_template('contact_us.html')

@app.route('/register', methods=['GET'])
def register():
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    """
    Logs out the current user and redirects them to the home page.

    This function is accessible via the "/logout" URL and requires that a user be authenticated to perform the logout
    operation, ensured by the @login_required decorator. Upon invocation, it performs the following actions:
    - Utilizes the `logout_user` function from Flask-Login to terminate the current user's session.
    - Displays a flash message indicating successful logout, categorized as 'success'.
    - Redirects the user to the home page of the application, typically the index view.

    The primary purpose of this function is to provide a secure and user-friendly way for users to end their session,
    ensuring that their authentication state is cleared and any session-specific data is properly disposed of.

    Returns:
        A redirection to the 'index' view function, which serves the application's home page. This ensures that the
        user is navigated away from protected areas of the application after logging out.
    """
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))




@app.route('/dashboard/', defaults={'page': 1})
@app.route('/dashboard/<int:page>' , methods=['GET', 'POST'])
@login_required
def dashboard(page=1):
    """
    Renders the dashboard page for the authenticated user, displaying a paginated list of their transactions
    and the most recent transaction.

    This view function is accessible through two routes: '/dashboard/' and '/dashboard/<int:page>', where 'page'
    allows for pagination of transaction records. It requires user authentication, as indicated by the
    @login_required decorator. The function queries the database for transactions associated with the current
    authenticated user, paginates these transactions with a specified number of items per page (PER_PAGE), and
    retrieves the most recent transaction for display.

    Parameters:
    - page (int): The current page number for pagination. Defaults to 1 if not specified in the route.

    The function then passes the current user, the paginated transaction records, and the most recent transaction
    to the 'dashboard.html' template for rendering.

    Returns:
        The rendered 'dashboard.html' template with the current user, their paginated transactions, and their
        last transaction passed as context variables.

    """
    PER_PAGE = 20
    user_transactions = Transaction.query.filter_by(user_id=current_user.id).paginate(page=page, per_page=PER_PAGE, error_out=False)
    last_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()

    return render_template('dashboard.html', user=current_user, all_transactions=user_transactions, last_transaction=last_transaction)



@app.route('/make_payment' , methods=['GET', 'POST'])
@login_required
def make_payment():
    """
    Renders the payment creation page for the authenticated user, displaying their transaction history and list of recipients.

    This view function is mapped to the '/make_payment' URL and is accessible only to authenticated users, as enforced
    by the @login_required decorator. It supports both GET and POST requests: GET requests for fetching and displaying
    the payment form along with relevant data, and POST requests for submitting the payment information (not detailed here).

    Upon access, the function queries the database for all transactions and recipients associated with the current user.
    It retrieves all transactions for the user, the most recent transaction, and all defined recipients for displaying
    on the 'make_payment.html' template. This setup allows users to view their past transactions and select recipients
    from a predefined list when making a new payment.

    Returns:
        The rendered 'make_payment.html' template with the current user, their transactions, the most recent transaction,
        and their recipients passed as context variables.

    """
    user_transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    last_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
    user_recipients = Recipient.query.filter_by(user_id=current_user.id).all()

    return render_template('make_payment.html', user=current_user, all_transactions=user_transactions, last_transaction=last_transaction, all_recipients=user_recipients)
    


@app.route('/loans', methods=['GET', 'POST'])
@login_required
def loans():
    """
    Renders the loans page for the authenticated user, displaying information related to their loans and transactions.

    This view function is mapped to the '/loans' URL and is accessible only to authenticated users, as enforced by the
    @login_required decorator. It is designed to handle both GET and POST requests: GET requests for fetching and
    displaying loan-related information, and POST requests for actions such as applying for a new loan or managing
    existing loans (the specific POST functionality is not detailed here and would depend on the form implementation
    within the 'loans.html' template).

    The function queries the database for the most recent transaction associated with the current user to display on
    the loans page. This may be used to provide context or relevant transactional information related to the user's loan
    activities.

    Returns:
        The rendered 'loans.html' template with the most recent transaction passed as a context variable. This setup
        allows users to have a snapshot of their recent financial activity alongside loan information.

    """
    last_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
    
    return render_template('loans.html', last_transaction=last_transaction)


@app.route('/my_loans', methods=['GET', 'POST'])
@login_required
def my_loans():
    """
    Renders the "My Loans" page for the authenticated user, displaying their current loans and the most recent transaction.

    This view function is accessible through the '/my_loans' URL and requires user authentication, as enforced by the
    @login_required decorator. It supports both GET and POST requests, with GET requests aimed at fetching and displaying
    the user's loan information, and POST requests potentially handling actions related to loan management (though the
    specifics of POST actions are not detailed here).

    Upon access, the function queries the database for:
    - The most recent transaction made by the current user, providing a context of their latest financial activity.
    - All loan records associated with the current user, allowing them to view the details of their loans.

    The retrieved information is then passed to the 'my_loans.html' template for rendering, offering users a comprehensive
    overview of their loan status and recent transactions.

    Returns:
        The rendered 'my_loans.html' template with the user's most recent transaction and their loans passed as context
        variables. This enables the user to monitor their financial commitments and activities directly from the "My Loans"
        page.

    
    """
    last_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
    user_loans = Loans.query.filter_by(user_id=current_user.id).all()
    
    return render_template('my_loans.html', last_transaction=last_transaction, user_loans=user_loans)


@app.route('/consumer_loan', methods=['GET', 'POST'])
@login_required
def consumer_loan():
    """
    Renders the consumer loan application page for the authenticated user, displaying their most recent transaction.

    This view function is mapped to the '/consumer_loan' URL and requires user authentication, ensuring that only
    logged-in users can access the consumer loan information and application form. It is designed to support both
    GET and POST requests: GET requests for fetching and displaying the page, and POST requests for handling the
    submission of the consumer loan application (although the specifics of processing POST requests are not detailed
    here).

    Returns:
        The rendered 'consumer_loan.html' template with the user's most recent transaction as a context variable.
        This setup enables users to have a snapshot of their latest financial activity while considering or applying
        for a consumer loan.

    """
    last_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
    
    return render_template('consumer_loan.html', last_transaction=last_transaction)


@app.route('/car_loan', methods=['GET', 'POST'])
@login_required
def car_loan():
    """
    Renders the car loan application page for authenticated users, displaying their most recent transaction.

    Returns:
        The 'car_loan.html' template rendered with the user's most recent transaction as a context variable. This
        arrangement offers users a snapshot of their financial status, which can be helpful when considering applying
        for a car loan.
    """
    last_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
    
    return render_template('car_loan.html', last_transaction=last_transaction)


@app.route('/home_renovation_loan', methods=['GET', 'POST'])
@login_required
def home_renovation_loan():
    """
    Renders the home renovation loan page for authenticated users.

    Returns:
        The 'home_renovation_loan.html' template, rendered with the user's latest transaction as a contextual variable.
        This setup is intended to give users insight into their current financial status, potentially aiding in their
        decision to apply for a home renovation loan.
    """
    last_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
    
    return render_template('home_renovation_loan.html', last_transaction=last_transaction)


@app.route('/test_loan', methods=['GET', 'POST'])
@login_required
def test_loan():
    """
    Renders the test loan page for authenticated users.

    Returns:
        The 'test_loan.html' template rendered with the user's latest transaction as a context variable, offering
        a glimpse into their recent financial activities. This is intended to assist users in making informed
        decisions related to the test loan product.

    """
    last_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
    
    return render_template('test_loan.html', last_transaction=last_transaction)


@app.route('/delete_all_loans', methods=['POST'])
@login_required
@admin_required
def delete_all_loans():
    """
    For testing purposes only !!!
    Deletes all loan records from the database, accessible only by authenticated administrators via a POST request.

    Upon invocation, the function attempts to delete all records from the Loans table. It then commits the
    changes to the database and redirects the user to the 'products_and_service_management' page, indicating
    successful completion of the operation. In the event of an exception, the database transaction is rolled
    back, and an error message is logged, maintaining data integrity.

    Returns:
        A redirection to the 'products_and_service_management' view function, signaling the successful deletion
        of all loan records. In case of failure, the user remains on the current page with an error message
        indicating the failure of the operation.

    Note:
        - This function performs a critical operation that irreversibly deletes all loan records. It should be
          used with caution and ideally be accompanied by mechanisms such as user confirmation prompts and
          logging of the deletion activity.
        - The exclusive use of POST requests for this function mitigates the risk of accidental deletions through
          methods like GET, which can be triggered by web crawlers or inadvertently by users.
        - Proper error handling is crucial to prevent partial deletions and to ensure the database's state remains
          consistent in case of operation failure.
        - Access control is enforced through the @admin_required decorator, limiting this function's usage to
          users with administrative privileges, which helps prevent unauthorized data modifications.
    """
    try:
        # Deletes all records from the Loans table
        num_deleted = db.session.query(Loans).delete()
        db.session.commit()
        print(f"Deleted {num_deleted} loans.")
        return redirect(url_for('products_and_service_management'))
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting loans: {e}")
        
    



@app.route('/add_one_day', methods=['GET', 'POST'])
@login_required
def add_one_day():
    """
    For testing purposes only !!!
    Adjusts the next payment date for all loan records in the database by subtracting one day, accessible to authenticated users.

    This view function is mapped to the '/add_one_day' URL and is protected by the @login_required decorator to ensure
    that only authenticated users can initiate the adjustment of loan payment dates. It handles both GET and POST requests,
    though its primary action—modifying loan payment dates—is performed irrespective of the request method. 

    Upon invocation, the function iterates over all loan records, decrementing the 'next_payment_date' by one day for each
    loan. It aims to provide flexibility in managing loan payment schedules, possibly to accommodate for holidays or other
    special circumstances. After successfully updating the dates, changes are committed to the database.

    In the event of an exception, the operation is rolled back to preserve data integrity, and an error message is logged.
    The user is then redirected to the 'my_loans' page, which displays their loan information, including any updated payment dates.

    Returns:
        A redirection to the 'my_loans' view function, indicating either the successful completion of the date adjustment
        process or the occurrence of an error that prevented the operation from completing.

    Note:
        - This function performs a bulk update operation that could potentially impact all loan records in the database.
          It should be used with caution and ideally incorporate user confirmation to prevent unintended consequences.
        - The actual implementation does not differentiate between GET and POST requests; however, using POST for
          operations that modify data is a best practice to prevent unintended actions from web crawlers or accidental
          navigation.
        - Adequate error handling and feedback mechanisms are essential for informing the user of the operation's
          outcome and for debugging purposes.
        - The use case for this function might be specific to scenarios requiring global adjustments to loan payment
          schedules, such as end-of-year processing or responding to legislative changes affecting loan repayment terms.
    """
    try:
        loans = Loans.query.all()
        print(len(loans))
        
        for loan in loans:
            loan.next_payment_date -= timedelta(days = 1)
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting loans: {e}")
        
    return redirect(url_for('my_loans'))



@app.route('/find_loans_by_product_id', methods=['GET', 'POST'])
@login_required
@admin_required
def find_loans_by_product_id():
    """
    Searches and displays loans filtered by a specific product ID for authenticated administrators.

    This view function, bound to the '/find_loans_by_product_id' URL, ensures that only authenticated users with
    administrator privileges can access and perform the search functionality, as dictated by the @login_required and
    @admin_required decorators. It supports both GET and POST requests: GET requests for initially rendering the search
    form and POST requests for submitting the search criteria (product ID) and displaying filtered results.

    When a POST request is made, the function retrieves the 'product_id' from the submitted form data. If a specific
    product ID is provided (and it is not the placeholder value 'all'), the function filters the Loans records by the
    given product ID. It then renders the 'products_and_service_management.html' template, passing the filtered (or
    unfiltered, in case 'all' is selected) loans records as context for display.

    Returns:
        The 'products_and_service_management.html' template, rendered with the loans records filtered by the specified
        product ID as a context variable. This allows administrators to view loans associated with a particular product,
        facilitating management tasks.

    Note:
        - The function initializes the 'loans' variable in the scope of the POST request handling. There is a logical
          mistake in the return statement outside the 'if request.method == 'POST'' block, as 'loans' might not be
          defined if a GET request is processed. It's recommended to ensure 'loans' is defined or handled appropriately
          outside the conditional block to avoid NameError.
        - This function demonstrates basic filtering logic that can be extended or modified based on additional
          requirements, such as incorporating multiple filter criteria or enhancing user input validation.
        - Proper error handling and user feedback mechanisms should be implemented, especially for informing users
          about the absence of records matching the search criteria or handling invalid input data.
        - The use of 'product_id' as a filter assumes that each loan record is associated with a product identified
          by a unique ID, which should be reflected in the Loans model and the database schema.
    """
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        query = Loans.query
        
        # Filtering by product id if other than 'all' is selected
        if product_id and product_id != 'all':
            query = query.filter(Loans.product_id == product_id)

        # Results
        loans = query.all()
        
        return render_template('products_and_service_management.html', loans = loans)
    
    return render_template('products_and_service_management.html', loans = loans)


 
@app.route('/online_shop', methods=['GET', 'POST'])
@login_required
def online_shop():
    """
    Renders the online shop page for authenticated users.

    This view function, associated with the '/online_shop' URL, requires user authentication, as indicated by the
    @login_required decorator, to ensure that the page is accessible only to logged-in users. It is designed to
    accommodate both GET and POST requests, allowing for a dynamic interaction within the online shop, such as
    reviewing recent purchases or engaging with new shopping actions (the handling of POST requests is abstract and
    depends on further implementation details).

    Returns:
        The 'online_shop.html' template, rendered with the current user's most recent transaction as a context variable.
        This design aims to offer users insight into their latest interaction with the online shop, potentially influencing
        further shopping decisions.
    """
    last_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()

    return render_template('online_shop.html', user=current_user, last_transaction=last_transaction)
    

@app.route('/account_data', methods=['GET', 'POST'])
@login_required
def account_data():
    """
    Displays the account data page for authenticated users, fe.

    User can change personal details.

    The primary action within this function is querying the database for the most recent transaction associated with
    the current user. This recent transaction, along with the user's details, is then passed to the 'account_data.html'
    template for rendering, thus providing a personalized snapshot of the user's financial activities.

    Returns:
        The 'account_data.html' template rendered with the current user's details.
    """
    last_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()

    return render_template('account_data.html', user=current_user, last_transaction=last_transaction)

    
    
@app.route('/communication_with_clients_sorting', methods=['GET', 'POST'])
@login_required
@admin_required
def cwcs():
    """
    Renders a page for administrators to sort and manage communications with clients.

    This view function, accessible via the '/communication_with_clients_sorting' URL, is secured with the
    @login_required and @admin_required decorators, restricting access to authenticated administrators only. It
    is designed to handle both GET and POST requests, accommodating various interactions such as viewing, sorting,
    and potentially filtering communications based on specific criteria (though the implementation details of these
    interactions are not specified here).

    The primary goal of this function is to provide a dedicated interface for administrators to efficiently manage
    and oversee communications with clients, enhancing the ability to respond to client needs and maintain organized
    records of interactions.

    Returns:
        The 'communication_with_clients_sorting.html' template without any predefined context variables, serving as
        a basis for administrators to engage with communication management tasks. Future implementations might pass
        sorted or filtered communication records as context variables to this template based on user inputs or
        predefined sorting/filtering criteria.

    Note:
        - While the current function setup does not specify context variables for the template, it lays the groundwork
          for adding dynamic content based on administrative actions or client communication data.
        - Extending this function to include POST request handling for sorting or filtering actions will require
          additional backend logic to process user inputs and update the displayed communication records accordingly.
        - Ensuring a user-friendly and responsive interface for this page is crucial, as it directly impacts the
          administrative efficiency in managing client communications.
        - Implementing robust security measures and data validation is essential to protect sensitive client
          information and prevent unauthorized access or manipulation.
    """
    return render_template('communication_with_clients_sorting.html')
    
    
@app.route('/admin_dashboard_cm', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_dashboard_cm():
    """
    Displays an administrative dashboard for customer management.

    

    Returns:
        The 'admin_dashboard_cm.html' template rendered.

    Note:
        - admin can add customers and transaction to the database
        - admin can wiev users data, delete existing customer and change password for customer
    """
    all_users = Users.query.all()
    

    return render_template('admin_dashboard_cm.html', all_users=all_users)


@app.route('/admin_dashboard_cam', methods=['GET'])
@login_required
@admin_required
def admin_dashboard_cam():
    """
    Displays an administrative dashboard dedicated to client account management (CAM), focusing on locked user accounts.

    The primary action within this function is to retrieve all locked user accounts from the database, using the
    LockedUsers model. These accounts are then presented on the 'admin_dashboard_cam.html' template, providing
    administrators with a comprehensive view of users whose accounts have been locked due to various reasons, such as
    security concerns or policy violations.

    Returns:
        The 'admin_dashboard_cam.html' template, rendered with the list of all locked user accounts as a context
        variable. This enables administrators to easily review and manage these accounts, supporting efficient
        resolution of account issues and enhancing overall security and user experience.

    Note:
        - The function focuses on locked user accounts, emphasizing the importance of security and account integrity
          within the application. Future enhancements could include more detailed information on the reasons for account
          locking and options for administrators to take corrective actions.
        - Ensuring data privacy and protection is crucial, especially when handling sensitive user information related
          to account locking and unlocking procedures.
        - Implementing user-friendly and intuitive interfaces for this dashboard is essential for administrative
          efficiency, enabling quick identification and resolution of issues with locked accounts.
        - Robust security measures should be in place to safeguard this functionality, preventing unauthorized
          access or actions that could compromise user accounts or application integrity.
    """
    all_locked_users = LockedUsers.query.all()

    return render_template('admin_dashboard_cam.html', all_locked_users = all_locked_users)
         

@app.route('/transaction_management', methods=['GET'])
@login_required
@admin_required
def transaction_management():
    """
    Renders the transaction management page.

    This view is accessible only to logged-in users with administrative privileges. It's intended to display the transaction
    management interface, where administrators can view, filter, and manage transactions. The function handles only GET requests
    and serves as the entry point for transaction management within the application.

    No transaction data is fetched or passed to the template by this function itself; rather, it sets up the framework for other
    functions or client-side scripts to populate the page dynamically or through subsequent form submissions for filtering.

    Returns:
        render_template: The 'transaction_management.html' template without any initial transaction data. The template is expected
        to provide functionalities for displaying and filtering transactions based on various criteria.
    """
    return render_template('transaction_management.html')

    
    
@app.route('/help_center', methods=['GET']) 
@login_required
def help_center():
    """
    Displays the help center page for authenticated users, featuring their latest support ticket queries.

    Accessible through the '/help_center' URL, this view function requires user authentication, as indicated by the
    @login_required decorator, to ensure that only logged-in users can access their support ticket history. It is
    designed to handle GET requests, presenting users with the most current status of each of their inquiries based
    on unique reference numbers.

    The function achieves this by executing a two-step query process:
    1. A subquery that groups support tickets by their reference number and identifies the latest date of submission
       for each group, representing the most recent update for each unique inquiry.
    2. A main query that joins this subquery to retrieve the full records of the latest tickets, filtering them by
       the current user's ID to personalize the data presented on the help center page.

    This method ensures that users are shown the most up-to-date information regarding their submitted tickets,
    enhancing the user experience by providing clear and current insights into the resolution status of their inquiries.

    Returns:
        The 'help_center.html' template, rendered with the user's latest support ticket queries as a context variable.
        This setup allows users to review their recent inquiries and their current statuses, offering a user-friendly
        interface for tracking support interactions.

    Note:
        - This function's implementation of SQL subqueries and joins demonstrates an effective approach to retrieving
          complex, user-specific data in applications requiring personalized user interactions.
        - Future enhancements could include the implementation of filtering or sorting options, allowing users to
          navigate their support ticket history more efficiently.
        - Ensuring the privacy and security of user data in this context is paramount, especially given the potentially
          sensitive nature of support ticket contents.
        - The clarity and usability of the help center interface are crucial for user satisfaction, suggesting that the
          design should facilitate easy access to detailed ticket information and support resources.
    """
    # First, we create a subquery to find the latest dates for each unique reference number
    subquery = db.session.query(SupportTickets.reference_number,func.max(SupportTickets.created_at).label('max_date')).group_by(SupportTickets.reference_number).subquery()

    # We then append this subquery to the main query to retrieve the latest records
    user_queries = db.session.query(SupportTickets).join(subquery,(SupportTickets.reference_number == subquery.c.reference_number) &
        (SupportTickets.created_at == subquery.c.max_date)).filter(SupportTickets.user_id == current_user.id).all()

    return render_template('help_center.html', all_queries = user_queries)





@app.route('/find_customer_by_role', methods=['GET', 'POST'])
@login_required
@admin_required    
def find_customer_by_role():
    """
    Handle the retrieval and display of users based on their role for an admin dashboard.

    This route is protected and requires the user to be logged in and have administrative privileges.
    It supports both GET and POST requests. On a POST request, it fetches users that match a specific
    role provided by the client through a form submission. It always retrieves all locked users
    regardless of the request method.

    The function queries the database for users with the specified role (via POST request) and
    for all locked users. It then renders the admin dashboard template, passing the queried users
    and all locked users to the template.

    Returns:
        A rendered template ('admin_dashboard_cam.html') with two contexts:
        - users: A list of users that match the specified role (empty if the request method is GET).
        - all_locked_users: A list of all users who are currently locked.
    """
    if request.method == 'POST':
        role = request.form.get('role')
        
    users = Users.query.filter_by(role=role).all()
    all_locked_users = LockedUsers.query.all()

    return render_template('admin_dashboard_cam.html', users = users, all_locked_users = all_locked_users)
        


@app.route('/products_and_service_management', methods=['GET', 'POST'])
@login_required
@admin_required
def products_and_service_management():
    """
    Display the products and service management page for administrators.

    This route is protected and requires the user to be logged in with administrative privileges.
    It serves as a management interface for products and services, allowing administrators to
    view and manage them. This function handles both GET and POST requests but does not differentiate
    between them, as its primary purpose is to display the management page.

    Returns:
        A rendered template ('products_and_service_management.html') for managing products and services.
        This template is intended to be used by administrators for overseeing product and service listings,
        modifications, and other related administrative tasks.
    """
    return render_template('products_and_service_management.html')


@app.route('/safety_settings', methods=['GET', 'POST'])
@login_required
@admin_required
def safety_settings():
    """
    Renders the safety settings page for administrators.

    This route is secured and accessible only to users who are logged in with administrative rights.
    It is designed to provide an interface for administrators to access and manage safety-related
    settings of the application. 
    The function's primary role is to render a template for the safety settings page, where administrators
    can view and modify settings related to the safety and security of the application and its users.

    Returns:
        A rendered template ('safety_settings.html') for the safety settings page, intended for administrative
        use in managing application safety and security settings.
    """
    return render_template('safety_settings.html')


@app.route('/team', methods=['GET', 'POST'])
@login_required
@admin_required
def team():
    """
    Serve the team management page, displaying board members, management, and bank employees.

    This route is protected, requiring the user to be logged in and have administrative privileges
    to access. It is designed to provide an overview of all the team members, including board members,
    management, and bank employees, to the administrators. The function fetches all users from the
    database and passes them to the 'team.html' template for display.

    Returns:
        A rendered template ('team.html'). This enables administrators to view and manage team members across different
        roles and departments.
    """
    all_users = Users.query.all()
    
    return render_template('team.html', all_users=all_users)
    

@app.route('/admin/users')
@login_required
@admin_required
def list_users():
    """
    This wiev presents usernames of users and link to website to change user's password

    Returns:
        A rendered template ('list_users.html') with the context 'all_users', containing a list of
        all users fetched from the database. This list is intended for administrative purposes, offering
        a comprehensive overview of users for management and oversight.
    """
    all_users = Users.query.all()
    return render_template('list_users.html', all_users=all_users)


@app.route('/admin/change-password/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def change_password(user_id):
    """
    Allows administrators to change the password for a specific user.

    This route is secured and can only be accessed by users who are logged in with administrative
    privileges. It is designed to facilitate the process of changing a user's password from the
    administrative dashboard. The function identifies the user by their unique ID, which is passed
    in the URL. If the user does not exist, a 404 error is raised.

    The function uses a form (ChangePasswordForm) to collect the new password. If the form is
    successfully validated upon submission (indicating a POST request and valid form data), the
    user's password is updated in the database. A flash message is displayed to confirm the update,
    and the administrator is redirected back to the list of users.

    Parameters:
        user_id (int): The unique identifier of the user whose password is being changed.

    Returns:
        On GET request: A rendered template ('change_password.html') with the form for entering a new password.
        On successful POST request (form submission and validation): A redirection to the 'list_users' view,
        along with a success message indicating that the password has been updated.
    """
    user = Users.query.get_or_404(user_id)
    form = ChangePasswordForm()

    if form.validate_on_submit():
        user.set_password(form.new_password.data)
        db.session.commit()
        flash('Password has been updated.', 'success')
        return redirect(url_for('list_users'))

    return render_template('change_password.html', form=form, user=user)




@app.route('/find_ddso_by_user_id', methods=['POST'])
@login_required
@admin_required
def find_ddso_by_user_id():
    """
    Filters and displays Direct Debits and Standing Orders (DDSO) for a specific user.

    This view is accessible only to logged-in users with administrative privileges and handles POST requests to filter DDSO
    transactions based on a provided user ID. It retrieves the user's name from the Users model to display alongside their
    transactions for a more personalized management experience.

    The function collects the user ID from the form submission, uses it to filter DDSO transactions from the database, and
    retrieves the corresponding user's name for display. It then renders the 'products_and_service_management.html' template,
    passing the filtered DDSO transactions and the user's name for presentation.

    Parameters:
        None directly; relies on form data submitted via POST request.

    Returns:
        render_template: Renders the 'products_and_service_management.html' template with context variables 'ddso_transactions',
        containing the list of filtered DDSO transactions, and 'name', the username associated with the provided user ID. If
        accessed without a POST request or if no user ID is provided, it renders the template without DDSO transactions.
    """
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        query = DDSO.query
        sender = Users.query.filter_by(id = user_id).first()
        name = sender.username
        
        # Filtering by user id 
        if user_id:
            query = query.filter(DDSO.user_id == user_id)

        # Results
        ddso_transactions = query.all()
        
        return render_template('products_and_service_management.html', ddso_transactions = ddso_transactions, name = name)
    
    return render_template('products_and_service_management.html')




@app.route('/delete_recipient/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_recipient(id):
    """
    Delete a recipient record from the database.

    This route handler will attempt to delete a recipient based on the given ID. If the recipient is found,
    it will be deleted from the database. On successful deletion, the user will be redirected to the add_recipient
    page with a success message. If an error occurs during the deletion process, a rollback is performed, and
    the user is redirected back to the add_recipient page with an error message.

    Parameters:
    - id (int): The ID of the recipient to be deleted.

    Returns:
    - Redirect: A redirection to the 'add_recipient' route. The redirection will be accompanied by a flash message
      indicating either the successful deletion of the recipient or an error in the process.

    Note:
    This function requires the user to be logged in to access this route. If not logged in, the user will be redirected
    to the login page.
    """
    recipient = Recipient.query.get_or_404(id) 

    try:
        db.session.delete(recipient)  
        db.session.commit()  
        flash('Recipient successfully deleted.', 'success') 
        return redirect(url_for('add_recipient_bp.add_recipient'))
    except Exception as e:
        db.session.rollback()  
        flash('Error deleting recipient.', 'error')
        print(e)  
        return redirect(url_for('add_recipient_bp.add_recipient'))
    



@app.route('/delete_ddso/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_ddso(id):
    """
    Delete a Direct Debit/Standing Order (DDSO) record from the database.

    This route handler will attempt to delete a DDSO based on the given ID. It first retrieves the DDSO
    by ID and, if found, proceeds to delete it from the database. Upon successful deletion, the user is redirected
    to the DDSO page with a success message indicating the specific DDSO (by reference number and recipient name)
    that was deleted. If an error occurs during the deletion process, the transaction is rolled back, and
    the user is redirected back to the DDSO page with an error message.

    Parameters:
    - id (int): The ID of the DDSO to be deleted.

    Returns:
    - Redirect: A redirection to the 'ddso_bp.ddso' route. The redirection will be accompanied by a flash message
      indicating either the successful deletion of the DDSO or an error in the process.

    Note:
    This function requires the user to be logged in to access this route. If not logged in, the user will be
    redirected to the login page. The function extracts and utilizes the DDSO's reference number and recipient's
    name for a more descriptive success message upon deletion.
    """
    ddso_to_delete = DDSO.query.get_or_404(id)
    reference_number = ddso_to_delete.reference_number
    recipient_name = ddso_to_delete.recipient
    
    try:
        db.session.delete(ddso_to_delete)
        db.session.commit()
        flash(f'Direct debit / standing order {reference_number} for {recipient_name} successfully deleted.', 'success')
        return redirect(url_for('ddso_bp.ddso'))
    except Exception as e:
        db.session.rollback()  
        flash('Error deleting recipient.', 'error')
        print(e)  
        return redirect(url_for('ddso_bp.ddso'))
    
 

if __name__ == "__main__":
    initialize_app()
    app.run(debug=True)