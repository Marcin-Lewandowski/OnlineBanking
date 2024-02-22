from flask import Flask, render_template, flash, request, url_for, redirect, session
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, logout_user, current_user, login_required
from forms.forms import ChangePasswordForm, AddRecipientForm
from datetime import timedelta, date, datetime
from routes.transfer import transfer_bp, login_bp, ddso_bp, create_transaction_bp, edit_profile_bp, add_recipient_bp
from routes.my_routes import grocery1_bp, grocery2_bp, grocery3_bp, grocery4_bp, gas_bp, power_bp, petrol_bp, clothes_bp, water_bp, add_customer_bp
from routes.my_routes_hc import send_query_bp, process_query_bp, read_message_bp, send_message_for_query_bp, send_message_for_message_bp, delete_messages_for_query_bp
from routes.my_routes_hc import delete_query_confirmation_bp, show_statement_for_customer_bp, edit_customer_information_bp
from routes.my_routes_statement import download_transactions_bp, download_transactions_csv_bp
from routes.my_routes_admin import transactions_filter_bp, reports_and_statistics_bp, delete_user_bp, update_customer_information_bp, find_tickets_bp, block_customer_bp, unlock_access_bp
from routes.my_routes_admin import admin_dashboard_bp, logs_filtering_bp
from routes.my_routes_loans import apply_consumer_loan_bp, apply_car_loan_bp, apply_home_renovation_loan_bp, apply_test_loan_bp
from models.models import Users, Transaction, db, Recipient, DDSO, SupportTickets, LockedUsers, Loans
from sqlalchemy import func, and_, case
from routes.transfer import admin_required
from flask_apscheduler import APScheduler
from flask_talisman import Talisman
import traceback

scheduler = APScheduler()


login_manager = LoginManager()
login_manager.login_view = 'login_bp.login'



def process_ddso_payments():
    with app.app_context():
        today = datetime.today().date()
        pending_payments = DDSO.query.filter(DDSO.next_payment_date <= today).all()
        
        if len(pending_payments) > 0:
            # Display the number of records in pending_payments
            print("Liczba oczekujących płatności:", len(pending_payments))

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
    
    app.register_blueprint(apply_consumer_loan_bp)
    app.register_blueprint(apply_car_loan_bp)
    app.register_blueprint(apply_home_renovation_loan_bp)
    app.register_blueprint(apply_test_loan_bp)
    
    return app



app = create_app()
  
def initialize_app():
    
    with app.app_context():
        db.create_all()
        create_sample_user()
        
        
@app.before_request
def initialize_database():
    db.create_all()
    session.permanent = True
    
    
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))
    
# The following code is optional and is used to add an example user during database initialization
def create_sample_user():
    # Check if the user already exists in the database
    existing_user = Users.query.filter_by(username='admin').first()

    if not existing_user:
        # Creating an admin account
        admin = Users(username='admin', role='admin', email='admin@ib.co.uk', phone_number='+447710989456', country='UK')
        admin.set_password('admin_password')
        db.session.add(admin)
        db.session.commit()  
        

    

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/main', methods=['GET', 'POST'])
def main():
    return render_template('index.html')

@app.route('/about_the_project', methods=['GET', 'POST'])
def about_the_project():
    return render_template('about_the_project.html')

@app.route('/author', methods=['GET', 'POST'])
def author():
    return render_template('author.html')

@app.route('/privacy', methods=['GET', 'POST'])
def privacy():
    return render_template('privacy.html')

@app.route('/contact_us', methods=['GET', 'POST'])
def contact_us():
    return render_template('contact_us.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))




@app.route('/dashboard/', defaults={'page': 1})
@app.route('/dashboard/<int:page>' , methods=['GET', 'POST'])
@login_required
def dashboard(page=1):
    PER_PAGE = 20
    user_transactions = Transaction.query.filter_by(user_id=current_user.id).paginate(page=page, per_page=PER_PAGE, error_out=False)
    last_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()

    return render_template('dashboard.html', user=current_user, all_transactions=user_transactions, last_transaction=last_transaction)



@app.route('/make_payment' , methods=['GET', 'POST'])
@login_required
def make_payment():
    user_transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    last_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
    user_recipients = Recipient.query.filter_by(user_id=current_user.id).all()

    return render_template('make_payment.html', user=current_user, all_transactions=user_transactions, last_transaction=last_transaction, all_recipients=user_recipients)
    


@app.route('/loans', methods=['GET', 'POST'])
@login_required
def loans():
    last_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
    
    return render_template('loans.html', last_transaction=last_transaction)


@app.route('/my_loans', methods=['GET', 'POST'])
@login_required
def my_loans():
    last_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
    user_loans = Loans.query.filter_by(user_id=current_user.id).all()
    
    return render_template('my_loans.html', last_transaction=last_transaction, user_loans=user_loans)


@app.route('/consumer_loan', methods=['GET', 'POST'])
@login_required
def consumer_loan():
    last_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
    
    return render_template('consumer_loan.html', last_transaction=last_transaction)


@app.route('/car_loan', methods=['GET', 'POST'])
@login_required
def car_loan():
    last_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
    
    return render_template('car_loan.html', last_transaction=last_transaction)


@app.route('/home_renovation_loan', methods=['GET', 'POST'])
@login_required
def home_renovation_loan():
    last_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
    
    return render_template('home_renovation_loan.html', last_transaction=last_transaction)


@app.route('/test_loan', methods=['GET', 'POST'])
@login_required
def test_loan():
    last_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
    
    return render_template('test_loan.html', last_transaction=last_transaction)


@app.route('/delete_all_loans', methods=['POST'])
@login_required
@admin_required
def delete_all_loans():
    try:
        # Deletes all records from the Loans table
        num_deleted = db.session.query(Loans).delete()
        db.session.commit()
        print(f"Deleted {num_deleted} loans.")
        return redirect(url_for('products_and_service_management'))
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting loans: {e}")
        
    


# For testing purposes
@app.route('/add_one_day', methods=['GET', 'POST'])
@login_required
def add_one_day():
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
    
    user_transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    last_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()

    return render_template('online_shop.html', user=current_user, all_transactions=user_transactions, last_transaction=last_transaction)
    

@app.route('/account_data', methods=['GET', 'POST'])
@login_required
def account_data():
    
    user_transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    last_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()

    return render_template('account_data.html', user=current_user, all_transactions=user_transactions, last_transaction=last_transaction)




@app.route('/communication_with_clients', methods=['GET', 'POST'])
@login_required
@admin_required
def cwc():
    all_queries = SupportTickets.query.all()
    
    # A subquery to find the latest date for each reference number
    subquery = (db.session.query(SupportTickets.reference_number,
                                 func.max(SupportTickets.created_at).label('latest_date'))
                          .group_by(SupportTickets.reference_number)
                          .subquery())

    # External query to retrieve full records
    latest_tickets_query = (db.session.query(SupportTickets)
                            .join(subquery, and_(SupportTickets.reference_number == subquery.c.reference_number,
                                                 SupportTickets.created_at == subquery.c.latest_date))
                            .order_by(case((SupportTickets.priority == 'urgent', 1),
                                           (SupportTickets.priority == 'high', 2),
                                           else_=3))
                            .all())

    return render_template('communication_with_clients.html', all_queries = all_queries, latest_tickets=latest_tickets_query)
    
    
@app.route('/communication_with_clients_sorting', methods=['GET', 'POST'])
@login_required
@admin_required
def cwcs():
    
    return render_template('communication_with_clients_sorting.html')
    
    
@app.route('/admin_dashboard_cm', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_dashboard_cm():
    all_users = Users.query.all()
    all_transactions = Transaction.query.all()

    return render_template('admin_dashboard_cm.html', all_users=all_users, all_transactions=all_transactions)


@app.route('/admin_dashboard_cam', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_dashboard_cam():
    all_users = Users.query.all()
    all_locked_users = LockedUsers.query.all()

    return render_template('admin_dashboard_cam.html', all_users=all_users, all_locked_users = all_locked_users)
         

@app.route('/transaction_management', methods=['GET', 'POST'])
@login_required
@admin_required
def transaction_management():
    all_users = Users.query.all()
    all_transactions = Transaction.query.all()
    ddso_transactions = DDSO.query.all()

    return render_template('transaction_management.html', all_users=all_users, all_transactions=all_transactions, ddso_transactions=ddso_transactions)

    
@app.route('/help_center', methods=['GET', 'POST']) 
@login_required
def help_center():
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
    if request.method == 'POST':
        role = request.form.get('role')
        
    users = Users.query.filter_by(role=role).all()
    all_locked_users = LockedUsers.query.all()

    return render_template('admin_dashboard_cam.html', users = users, all_locked_users = all_locked_users)
        


@app.route('/products_and_service_management', methods=['GET', 'POST'])
@login_required
@admin_required
def products_and_service_management():
    
    return render_template('products_and_service_management.html')


@app.route('/safety_settings', methods=['GET', 'POST'])
@login_required
@admin_required
def safety_settings():
    
    return render_template('safety_settings.html')


@app.route('/team', methods=['GET', 'POST'])
@login_required
@admin_required
def team():
    # The view displays board members, management and bank employees
    all_users = Users.query.all()
    
    return render_template('team.html', all_users=all_users)
    

@app.route('/admin/users')
@login_required
@admin_required
def list_users():
    all_users = Users.query.all()
    return render_template('list_users.html', all_users=all_users)


@app.route('/admin/change-password/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def change_password(user_id):
    user = Users.query.get_or_404(user_id)
    form = ChangePasswordForm()

    if form.validate_on_submit():
        user.set_password(form.new_password.data)
        db.session.commit()
        flash('Password has been updated.', 'success')
        return redirect(url_for('list_users'))

    return render_template('change_password.html', form=form, user=user)


if __name__ == "__main__":
    initialize_app()
    
    app.run(debug=True)