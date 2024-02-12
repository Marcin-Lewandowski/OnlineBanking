from flask import Flask, render_template, flash, request, url_for, redirect, session, abort
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from forms.forms import AddCustomerForm, DeleteUserForm, ChangePasswordForm, AddRecipientForm, SendQueryForm, LockUser, EditUserForm
from datetime import timedelta, date, datetime
from routes.transfer import transfer_bp, login_bp, ddso_bp, create_transaction_bp, edit_profile_bp
from routes.my_routes import grocery1_bp, grocery2_bp, grocery3_bp, grocery4_bp, gas_bp, power_bp, petrol_bp, clothes_bp, water_bp, add_customer_bp
from routes.my_routes_hc import send_query_bp, process_query_bp, read_message_bp, send_message_for_query_bp, send_message_for_message_bp, delete_messages_for_query_bp
from routes.my_routes_hc import delete_query_confirmation_bp, show_statement_for_customer_bp, edit_customer_information_bp
from routes.my_routes_statement import download_transactions_bp, download_transactions_csv_bp
from routes.my_routes_admin import transactions_filter_bp, reports_and_statistics_bp, delete_user_bp, update_customer_information_bp, find_tickets_bp, block_customer_bp, unlock_access_bp, admin_dashboard_bp
from models.models import Users, Transaction, db, Recipient, DDSO, SupportTickets, LockedUsers
from functools import wraps
from urllib.parse import quote
from flask_migrate import Migrate
from sqlalchemy import func, and_, case, asc
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64, csv
import logging
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from flask import make_response, send_file
from io import BytesIO
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from routes.transfer import logger, admin_required
from flask_apscheduler import APScheduler
import traceback


scheduler = APScheduler()



login_manager = LoginManager()
login_manager.login_view = 'login_bp.login'



def process_ddso_payments():
    with app.app_context():
        today = datetime.today().date()
        pending_payments = DDSO.query.filter(DDSO.next_payment_date <= today).all()
        
        if len(pending_payments) > 0:
            # Wyświetl ilość rekordów w pending_payments
            print("Liczba oczekujących płatności:", len(pending_payments))

            for payment in pending_payments:
                recipient_name = payment.recipient
                
                # Pobierz ID odbiorcy (użytkownika np. Global Cars, Bauron INC ) na podstawie recipient_name
                recipient_user = Users.query.filter_by(username=recipient_name).first()
                print("Recipient: ", recipient_user.username)
                sender = Users.query.filter_by(id = payment.user_id).first()
                print("Sender: ", sender.username)
                
                if recipient_user:
                    recipient_id = recipient_user.id

                    # Teraz możesz użyć recipient_id do dalszych operacji, np. do wyszukania transakcji
                    last_recipient_transaction = Transaction.query.filter_by(user_id=recipient_id).order_by(Transaction.id.desc()).first()
                    
                    print("Recipient ID: ", last_recipient_transaction.user_id)
                    print("Recipient balance: ", last_recipient_transaction.balance)
                    last_sender_transaction = Transaction.query.filter_by(user_id=payment.user_id).order_by(Transaction.id.desc()).first()
                    print("Sender ID: ", last_sender_transaction.user_id)
                    print("Sender balance: ", last_sender_transaction.balance)
                    

                    # Jeśli istnieje ostatnia transakcja, wykonaj dalsze działania
                    if last_recipient_transaction:
                        # Logika przetwarzania płatności
                        
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
                            
                            # (Załóżmy, że płatność jest miesięczna - timedelta(days=30), ale dla testów codziennie timedelta(days=1))
                            if payment.frequency == 'daily':
                                payment.next_payment_date = payment.next_payment_date + timedelta(days=1)
                                
                            if payment.frequency == 'monthly':
                                payment.next_payment_date = payment.next_payment_date + timedelta(days=30)
                                
                            db.session.commit()
                            print('Direct debit sended successful!')
                            
                            
                        except Exception as e:
                            db.session.rollback()
                            # Wydrukuj komunikat o błędzie i pełny stos wywołań
                            print('An error occurred. Transfer failed:', e)
                            traceback.print_exc()   
                
        else:
            print("Brak oczekujących płatności.")
            return  # Zakończenie funkcji jeśli nie ma płatności do przetworzenia
        
        
        

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'bc684cf3981dbcacfd60fc34d6985095'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ib_database_users.db'  # Ustawienie nazwy bazy danych
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Zalecane dla wydajności
    #app.config['MAX_LOGIN_ATTEMPTS'] = 3  # Ustal maksymalną liczbę nieudanych prób logowania

    app.permanent_session_lifetime = timedelta(minutes = 45)
    
    csrf = CSRFProtect(app)
    
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Inicjalizacja db z obiektem app
    db.init_app(app)
    
    # Inicjalizacja schedulera
    scheduler.init_app(app)
    scheduler.start()
    
    # Dodaj zadanie do schedulera cyklicznie trigger='cron'
    # Uruchom zadanie tylko raz, krótko po starcie aplikacji trigger='date'
    #scheduler.add_job(id='process_ddso', func=process_ddso_payments, trigger='cron', hour=0, minute=0)
    
    
    # Uruchom zadanie tylko raz, krótko po starcie aplikacji trigger='date'
    scheduler.add_job(id='process_ddso', func=process_ddso_payments, trigger='date', run_date=datetime.now() + timedelta(seconds=10))

    # ... Rejestracja Blueprintów, inne konfiguracje ...
    app.register_blueprint(transfer_bp)
    app.register_blueprint(login_bp)
    app.register_blueprint(ddso_bp)
    app.register_blueprint(create_transaction_bp)
    app.register_blueprint(edit_profile_bp)
    app.register_blueprint(add_customer_bp)
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
    
# Poniższy kod jest opcjonalny i służy do dodania przykładowego użytkownika podczas inicjalizacji bazy danych
def create_sample_user():
    # Sprawdź, czy użytkownik już istnieje w bazie
    existing_user = Users.query.filter_by(username='admin').first()

    if not existing_user:
        # Tworzenie konta admina
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


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Zostałeś wylogowany.', 'success')
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
    


@app.route('/add_recipient', methods=['GET', 'POST'])
@login_required
def add_recipient():
    form = AddRecipientForm()
    if form.validate_on_submit():
        # Sprawdź, czy istnieje użytkownik z danym sort_code i account_number w tabeli Users
        user_exists = Transaction.query.filter_by(sort_code=form.sort_code.data, account_number=form.account_number.data).first()
        
        if user_exists:
            # Użytkownik istnieje, więc dodajemy nowego odbiorcę
            new_recipient = Recipient(
                user_id=current_user.id,
                name=form.name.data,
                sort_code=form.sort_code.data,
                account_number=form.account_number.data
            )
            db.session.add(new_recipient)
            db.session.commit()
            flash('New recipient added successfully!', 'success')
            return redirect(url_for('add_recipient'))
        else:
            # Użytkownik nie istnieje, wyświetl komunikat o błędzie
            flash('The user with the given sort code and account number does not exist.', 'danger')

    # Pobierz transakcje i odbiorców użytkownika do wyświetlenia na stronie
    user_transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    user_recipients = Recipient.query.filter_by(user_id=current_user.id).all()
    last_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
    
    return render_template('add_recipient.html', form=form, user=current_user, all_transactions=user_transactions, last_transaction=last_transaction, all_recipients=user_recipients)















 
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
    

@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('register.html')




@app.route('/communication_with_clients', methods=['GET', 'POST'])
@login_required
@admin_required
def cwc():
    all_queries = SupportTickets.query.all()
    
    # Podzapytanie do znalezienia najnowszej daty dla każdego reference_number
    subquery = (db.session.query(SupportTickets.reference_number,
                                 func.max(SupportTickets.created_at).label('latest_date'))
                          .group_by(SupportTickets.reference_number)
                          .subquery())

    # Zewnętrzne zapytanie do pobrania pełnych rekordów
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
    #user_queries = SupportTickets.query.filter_by(user_id=current_user.id).all()
    
    # Najpierw tworzymy subzapytanie, aby znaleźć najnowsze daty dla każdego unikalnego numeru referencyjnego
    subquery = db.session.query(SupportTickets.reference_number,func.max(SupportTickets.created_at).label('max_date')).group_by(SupportTickets.reference_number).subquery()

    # Następnie dołączamy to subzapytanie do głównego zapytania, aby pobrać ostatnie rekordy
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
    
    # Widok wyświetla członków zarządu, management, pracowników banku, logika na stronie html
    # Pobierz wszystkich użytkowników z bazy danych
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

'''
528
'''

if __name__ == "__main__":
    initialize_app()
    
    app.run(debug=True)