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


scheduler = APScheduler()



login_manager = LoginManager()
login_manager.login_view = 'login_bp.login'


#@scheduler.task('cron', id='process_ddso')
def process_ddso_payments():
    with app.app_context():
        today = datetime.today().date()
        pending_payments = DDSO.query.filter(DDSO.next_payment_date <= today).all()
        
        if len(pending_payments) > 0:
            # Wyświetl ilość rekordów w pending_payments
            print("Liczba oczekujących płatności:", len(pending_payments))

            for payment in pending_payments:
                recipient_name = payment.recipient
                
                # Pobierz ID odbiorcy (użytkownika) na podstawie recipient_name
                recipient_user = Users.query.filter_by(username=recipient_name).first()
                if recipient_user:
                    recipient_id = recipient_user.id

                    # Teraz możesz użyć recipient_id do dalszych operacji, np. do wyszukania transakcji
                    last_recipient_transaction = Transaction.query.filter_by(user_id=recipient_id).order_by(Transaction.transaction_date.desc()).first()

                    # Jeśli istnieje ostatnia transakcja, wykonaj dalsze działania
                    if last_recipient_transaction:
                        # Logika przetwarzania płatności
                        # ...
                        print(last_recipient_transaction.balance)
                
                # Zaktualizuj next_payment_date
                # (Załóżmy, że płatność jest miesięczna)
                payment.next_payment_date = payment.next_payment_date + timedelta(days=30)

                db.session.commit()
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
    scheduler.add_job(id='process_ddso', func=process_ddso_payments, trigger='date', run_date=datetime.now() + timedelta(seconds=20))



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



@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Zostałeś wylogowany.', 'success')
    return redirect(url_for('index'))



@app.route('/dashboard' , methods=['GET', 'POST'])
@login_required
def dashboard():
    
    user_transactions = Transaction.query.filter_by(user_id=current_user.id).all()
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
    user_transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    user_recipients = Recipient.query.filter_by(user_id=current_user.id).all()
    last_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
    
    form = AddRecipientForm()
    if form.validate_on_submit():
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



def plot_to_html_img(plt):
    # Zapisz wykres w buforze pamięci
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    # Koduj jako base64
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8').replace('\n', '')
    buf.close()

    return f'<img src="data:image/png;base64,{image_base64}"/>'


@app.route('/admin_dashboard', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_dashboard():
    user = current_user
    if user.role != 'admin':
        
        logger.error(f"Brak dostępu do chronionego zasobu - /admin_dashboard  '{user.username}' ")
    # Pobierz wszystkich użytkowników z bazy danych
    all_users = Users.query.count()
    locked_users = LockedUsers.query.count()
    
    # Grupowanie wiadomości według priorytetu i liczenie ich
    priority_counts = (SupportTickets.query
                       .with_entities(SupportTickets.priority, func.count(SupportTickets.reference_number.distinct()))
                       .group_by(SupportTickets.priority)
                       .all())

    # Inicjalizacja zmiennych dla każdego priorytetu
    normal_count = high_count = urgent_count = 0

    # Przypisanie wyników do odpowiednich zmiennych
    for priority, count in priority_counts:
        if priority == 'normal':
            normal_count = count
        elif priority == 'high':
            high_count = count
        elif priority == 'urgent':
            urgent_count = count
    
    # Renderuj szablon, przekazując dane
    return render_template('admin_dashboard.html', users = all_users, locked_users = locked_users, normal_count=normal_count, high_count=high_count, urgent_count=urgent_count)







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
    
    
@app.route('/find_tickets', methods=['GET', 'POST'])
@login_required
@admin_required
def find_tickets():
    
    if request.method == 'POST':
        priority = request.form.get('priority')
        
        # Podzapytanie do znalezienia najnowszej daty dla każdego reference_number
        subquery = (db.session.query(SupportTickets.reference_number,
                                     func.max(SupportTickets.created_at).label('latest_date'))
                              .group_by(SupportTickets.reference_number)
                              .subquery())

        # Zewnętrzne zapytanie do pobrania pełnych rekordów
        query = (db.session.query(SupportTickets)
                            .join(subquery, and_(SupportTickets.reference_number == subquery.c.reference_number,
                                                 SupportTickets.created_at == subquery.c.latest_date)))

        # Filtracja po priorytecie
        if priority:
            query = query.filter(SupportTickets.priority == priority)

        query = query.order_by(case((SupportTickets.priority == 'urgent', 1),
                                    (SupportTickets.priority == 'high', 2),
                                    else_=3))

        tickets = query.all()
        return render_template('communication_with_clients_sorting.html', tickets=tickets)
       
    
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
         
@app.route('/unlock_access/<username>', methods=['GET', 'POST'])  
@login_required
@admin_required
def unlock_access(username):
    
    user = LockedUsers.query.filter_by(username=username).first()
    
    if user:
        db.session.delete(user)
        db.session.commit()
        flash('User account: ' + user.username + '  unlocked successfully!', 'success')
    else:
        flash('User not found.', 'error')
    
    
    all_locked_users = LockedUsers.query.all()
    
    return render_template('admin_dashboard_cam.html', all_locked_users = all_locked_users)
    



@app.route('/transaction_management', methods=['GET', 'POST'])
@login_required
@admin_required
def transaction_management():
    
    all_users = Users.query.all()
    all_transactions = Transaction.query.all()
    ddso_transactions = DDSO.query.all()

    return render_template('transaction_management.html', all_users=all_users, all_transactions=all_transactions, ddso_transactions=ddso_transactions)

    
    
@app.route('/transactions_filter', methods=['GET', 'POST'])
@login_required
@admin_required  
def transactions_filter():
    all_transactions = Transaction.query.all()
    
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        date_from = request.form.get('date_from')
        date_until = request.form.get('date_until')
        transaction_type = request.form.get('transaction_type')

        query = Transaction.query

        # Filtracja po ID użytkownika, jeśli podano
        if user_id:
            query = query.filter(Transaction.user_id == user_id)

        # Filtracja po zakresie dat
        if date_from:
            query = query.filter(Transaction.transaction_date >= date_from)
        if date_until:
            query = query.filter(Transaction.transaction_date <= date_until)

        # Filtracja po typie transakcji, jeśli wybrano inny niż 'all'
        if transaction_type and transaction_type != 'all':
            query = query.filter(Transaction.transaction_type == transaction_type)

        # Pobranie wyników
        transactions = query.all()

        return render_template('transaction_management.html', transactions=transactions, all_transactions=all_transactions)

    return render_template('transaction_management.html', transactions=transactions)
    


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







@app.route('/block_customer', methods=['GET', 'POST'])
@login_required
@admin_required
def block_customer():
    form = LockUser()
    
    if form.validate_on_submit():
        # Sprawdź, czy użytkownik o podanej nazwie istnieje
        user_exists = Users.query.filter_by(username=form.username.data).first()
        if user_exists:
            # Użytkownik istnieje, kontynuuj z blokowaniem
            user_for_lock = LockedUsers(username=form.username.data)
            
            db.session.add(user_for_lock)
            db.session.commit()

            flash('User account for: ' + user_for_lock.username + '  locked successfully!', 'success')
        else:
            # Użytkownik nie istnieje, wyświetl komunikat
            flash('User account: ' + form.username.data + ' does not exist!', 'error')

        # Pobierz aktualną listę zablokowanych użytkowników
        all_locked_users = LockedUsers.query.all()
        return render_template('admin_dashboard_cam.html', all_locked_users=all_locked_users)

    # Renderuj formularz, jeśli nie nastąpiła walidacja
    return render_template('admin_dashboard_cam.html', form=form)


    
@app.route('/find_customer_by_role', methods=['GET', 'POST'])
@login_required
@admin_required    
def find_customer_by_role():
    if request.method == 'POST':
        role = request.form.get('role')
        
    users = Users.query.filter_by(role=role).all()
    all_locked_users = LockedUsers.query.all()

    return render_template('admin_dashboard_cam.html', users = users, all_locked_users = all_locked_users)
        


@app.route('/update_customer_information/<username>', methods=['GET', 'POST'])
@login_required
@admin_required
def update_customer_information(username):
    user = Users.query.filter_by(username=username).first()
    form = EditUserForm()

    if form.validate_on_submit():
        user.email = form.email.data
        user.phone_number = form.phone_number.data
        user.country = form.country.data
        
        db.session.commit()
        flash('Customer profile for ' + user.username + ' has been updated.')
        return render_template('edit_customer_information.html', user = user)

    
    else:
        print(form.errors) 

    
    return render_template('edit_customer_information.html', user = user)




@app.route('/delete_user', methods=['GET', 'POST'])
@login_required
@admin_required
def delete_user():
    all_users = Users.query.all()
    if current_user.role != 'admin':
        flash('Brak uprawnień do wykonania tej operacji.', 'danger')
        return redirect(url_for('index'))

    form = DeleteUserForm()
    if form.validate_on_submit():
        username = form.username.data
        user_to_delete = Users.query.filter_by(username=username).first()

        if user_to_delete:
            db.session.delete(user_to_delete)
            db.session.commit()
            flash('Użytkownik został pomyślnie usunięty.', 'success')
        else:
            flash('Użytkownik nie został znaleziony.', 'danger')

        return redirect(url_for('admin_dashboard_cm'))

    return render_template('admin_dashboard_cm.html', form=form, all_users=all_users)














# Funkcja zliczająca ile logów o danym poziomie jest zapisanych w pliku z logami
def count_log_levels(file_path):
    log_levels = {"INFO": 0, "ERROR": 0, "WARNING": 0, "CRITICAL": 0}

    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            if "INFO" in line:
                log_levels["INFO"] += 1
            elif "ERROR" in line:
                log_levels["ERROR"] += 1
            elif "WARNING" in line:
                log_levels["WARNING"] += 1
            elif "CRITICAL" in line:
                log_levels["CRITICAL"] += 1

    return log_levels











def create_transactions_pdf(transactions, username):
    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=letter)
    
    
    # Styl dla paragrafu
    styles = getSampleStyleSheet()
    
    # Tekst do umieszczenia przed tabelą
    
    intro_text = f"Poniżej znajduje się lista wszystkich transakcji dokonanych na Twoim koncie, {username}: "
    intro = Paragraph(intro_text, styles['Normal'])
    epmty_space = Paragraph("<br/><br/>", styles['Normal'])  # Pusty paragraf jako odstęp


    data = [["Date", "Type", "Description", "Debit amount", "Credit amount", "Balance"]]  # Nagłówki kolumn
    for transaction in transactions:
        data.append([str(transaction.transaction_date), str(transaction.transaction_type), str(transaction.transaction_description), str(transaction.debit_amount), str(transaction.credit_amount), str(transaction.balance)])

    # Tworzenie tabeli
    table = Table(data)

    # Styl tabeli (opcjonalnie)
    style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND',(0,1),(-1,-1),colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ])
    table.setStyle(style)

    # Dodawanie tabeli do elementów PDF
    
    elems = [intro, epmty_space, table]
    pdf.build(elems)

    buffer.seek(0)
    return buffer







@app.route('/download_transactions/<int:user_id>')
@login_required
def download_transactions(user_id):
    # Sprawdzenie, czy zalogowany użytkownik ma uprawnienia do pobrania transakcji
    if current_user.id != user_id and not current_user.is_admin:
        abort(403)

    # Pobranie transakcji użytkownika z bazy danych
    transactions = Transaction.query.filter_by(user_id=user_id).all()

    # Tworzenie PDF
    
    buffer = create_transactions_pdf(transactions, current_user.username)

    # Utworzenie odpowiedzi HTTP z plikiem PDF
    response = make_response(buffer.getvalue())
    buffer.close()
    response.headers['Content-Disposition'] = 'attachment; filename=transactions.pdf'
    response.mimetype = 'application/pdf'

    return response





def save_transactions_to_csv(transactions, filename):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        # Nagłówki kolumn
        writer.writerow(["Date", "Type", "Description", "Debit amount", "Credit amount", "Balance"])

        # Zapisz dane transakcji
        for transaction in transactions:
            writer.writerow([transaction.transaction_date, transaction.transaction_type, transaction.transaction_description, transaction.debit_amount, transaction.credit_amount, transaction.balance])
            
            
@app.route('/download_transactions_csv')
@login_required
def download_transactions_csv():
    # Pobierz dane transakcji (możesz tu dodać filtr na transakcje aktualnego użytkownika)
    transactions = Transaction.query.filter_by(user_id=current_user.id).all()

    # Tworzenie nazwy pliku
    filename = f"transactions_{current_user.username}.csv"

    # Zapisz dane do CSV
    save_transactions_to_csv(transactions, filename)

    # Utworzenie odpowiedzi z plikiem CSV
    return send_file(filename, as_attachment=True)

























            
            

    




























@app.route('/reports_and_statistics', methods=['GET', 'POST'])
@login_required
@admin_required
def reports_and_statistics():
    
    # Pobranie danych o rolach użytkowników
    roles_count = Users.query.with_entities(Users.role, func.count(Users.role)).group_by(Users.role).all()

    # Tworzenie DataFrame
    roles_df = pd.DataFrame(roles_count, columns=['Role', 'Count'])

    # Tworzenie wykresu kołowego
    fig, ax = plt.subplots(figsize=(4, 3))  # Utworzenie figury i osi
    ax.pie(roles_df['Count'], labels=roles_df['Role'], autopct='%1.1f%%', startangle=140)
    ax.set_title('Rozkład ról użytkowników w systemie')

    # Zmiana koloru tła
    ax.set_facecolor('black')  # Możesz wybrać dowolny kolor
    fig.patch.set_facecolor('lightgrey')  # Zmiana koloru tła figury
    
    # Konwertuj wykres na HTML img
    chart1 = plot_to_html_img(plt)
    
    
    
    
    # Pobieranie danych o narodowościach użytkownków
    countries_count = Users.query.with_entities(Users.country, func.count(Users.country)).group_by(Users.country).all()
    
    #Tworzenie dataframe
    countries_df = pd.DataFrame(countries_count, columns = ['Country', 'Count'])
    
    # Tworzenie wykresu kołowego
    fig, ax = plt.subplots(figsize=(4, 3))  # Utworzenie figury i osi
    ax.pie(countries_df['Count'], labels=countries_df['Country'], autopct='%1.1f%%', startangle=140)
    ax.set_title('Rozkład narodowości użytkowników w systemie')

    # Zmiana koloru tła
    ax.set_facecolor('black')  # Możesz wybrać dowolny kolor
    fig.patch.set_facecolor('lightgrey')  # Zmiana koloru tła figury
    
    # Konwertuj wykres na HTML img
    chart2 = plot_to_html_img(plt)
    
    
    
    # Podzapytanie do wyodrębnienia unikalnych numerów referencyjnych z ich priorytetami
    subquery = (db.session.query(SupportTickets.reference_number, SupportTickets.priority)
                .distinct(SupportTickets.reference_number)
                .subquery())

    # Zapytanie główne - grupowanie i zliczanie priorytetów na podstawie unikalnych numerów referencyjnych
    tickets_count = (db.session.query(subquery.c.priority, func.count(subquery.c.priority))
                    .group_by(subquery.c.priority)
                    .all())

    # Reszta kodu pozostaje bez zmian
    tickets_df = pd.DataFrame(tickets_count, columns=['Priority', 'Count'])

    fig, ax = plt.subplots(figsize=(6, 3))
    ax.pie(tickets_df['Count'], labels=tickets_df['Priority'], autopct='%1.1f%%', startangle=140)
    ax.set_title('Rozkład ilości wiadomości z określonym priorytetem w systemie')
    ax.set_facecolor('black')
    fig.patch.set_facecolor('lightgrey')

    chart3 = plot_to_html_img(plt)
    
    
    
    
    
    
    # Pobieranie danych o narodowościach użytkownków
    transaction_types_count = Transaction.query.with_entities(Transaction.transaction_type, func.count(Transaction.transaction_type)).group_by(Transaction.transaction_type).all()
    
    #Tworzenie dataframe
    transaction_types_df = pd.DataFrame(transaction_types_count, columns = ['Transaction type', 'Count'])
    
    # Tworzenie wykresu kołowego
    fig, ax = plt.subplots(figsize=(6, 3))  # Utworzenie figury i osi
    ax.pie(transaction_types_df['Count'], labels=transaction_types_df['Transaction type'], autopct='%1.1f%%', startangle=140)
    ax.set_title('Rozkład typów tranzakcji w systemie tranzakcji')

    # Zmiana koloru tła
    ax.set_facecolor('black')  # Możesz wybrać dowolny kolor
    fig.patch.set_facecolor('lightgrey')  # Zmiana koloru tła figury
    
    # Konwertuj wykres na HTML img
    chart4 = plot_to_html_img(plt)
    
    
    
    
    
    
    # Zapytanie do obliczenia średniej wartości transakcji dla każdego typu
    avg_transactions = (db.session.query(Transaction.transaction_type,func.avg(Transaction.debit_amount + Transaction.credit_amount).label('average_value'))
                    .filter((Transaction.debit_amount + Transaction.credit_amount) <= 10000).group_by(Transaction.transaction_type).all())

    # Tworzenie DataFrame z wyników
    transactions_df = pd.DataFrame(avg_transactions, columns=['TransactionType', 'AverageValue'])

    # Tworzenie wykresu słupkowego
    fig, ax = plt.subplots(figsize=(8, 6))
    transactions_df.plot(kind='bar', x='TransactionType', y='AverageValue', ax=ax, color='skyblue')

    ax.set_title('Średnia Wartość Transakcji dla Każdego Typu Transakcji')
    ax.set_xlabel('Typ Transakcji')
    ax.set_ylabel('Średnia Wartość')
    plt.xticks(rotation=45)
    
    # Dodawanie wartości liczbowych na wykresie
    for bar in ax.patches:
        ax.annotate(format(bar.get_height(), '.2f'), 
                (bar.get_x() + bar.get_width() / 2, 
                    bar.get_height()), ha='center', va='center',
                size=10, xytext=(0, 8),
                textcoords='offset points')
    
    # Konwertuj wykres na HTML img
    chart5 = plot_to_html_img(plt)
    
    
    response_times = []
    
    # Znajdź unikalne numery referencyjne
    unique_reference_numbers = (SupportTickets.query.with_entities(SupportTickets.reference_number).distinct().all())

    # Wyświetl ilość unikalnych numerów referencyjnych
    print(f"Ilość unikalnych numerów referencyjnych: {len(unique_reference_numbers)}")

    # Wyświetl numery referencyjne
    for ref_number in unique_reference_numbers:
        print(ref_number[0])

        dates = (db.session.query(SupportTickets.created_at)
            .filter(SupportTickets.reference_number == ref_number[0])  # Użyj [0], aby pobrać numer referencyjny
            .order_by(asc(SupportTickets.created_at))
            .limit(2)  # Ograniczenie do pierwszych dwóch rekordów
            .all())
        
        

        # Obliczenie różnicy czasu
        if len(dates) == 2:
            first_record, second_record = dates[0][0], dates[1][0]  # Zakładając, że dates zawiera daty
            time_difference = second_record - first_record
            response_times.append(time_difference)
            print("Czas, jaki upłynął między rekordami:", time_difference)
        else:
            print("Nie znaleziono wystarczającej liczby rekordów.")
    
    if response_times:
        total_time = sum(response_times, timedelta())  # Sumowanie timedelta
        average_time_seconds = total_time.total_seconds() / len(response_times)  # Średni czas w sekundach

        # Obliczenie godzin i minut
        hours, remainder = divmod(average_time_seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        # Wyświetlenie średniego czasu w godzinach i minutach
        print("Średni czas odpowiedzi: {} godzin {} minut".format(int(hours), int(minutes)))
    else:
        print("Nie znaleziono wystarczającej liczby rekordów do obliczenia średniego czasu odpowiedzi.")
    
    
    if response_times:
        average_time_seconds = total_time.total_seconds() / len(response_times)
        hours, remainder = divmod(average_time_seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        average_response_time = "{} godzin {} minut".format(int(hours), int(minutes))
    else:
        average_response_time = "Brak danych"
    
    
    
    # Grupowanie wiadomości według priorytetu i liczenie ich
    priority_counts = (SupportTickets.query
                       .with_entities(SupportTickets.priority, func.count(SupportTickets.reference_number.distinct()))
                       .group_by(SupportTickets.priority)
                       .all())

    # Inicjalizacja zmiennych dla każdego priorytetu
    normal_count = high_count = urgent_count = 0

    # Przypisanie wyników do odpowiednich zmiennych
    for priority, count in priority_counts:
        if priority == 'normal':
            normal_count = count
        elif priority == 'high':
            high_count = count
        elif priority == 'urgent':
            urgent_count = count
    total_count = normal_count + high_count + urgent_count
    
    
    # Wywołanie funkcji zliczającej lofi
    
    log_file_path = 'app.log'  # Ścieżka do Twojego pliku logów
    log_counts = count_log_levels(log_file_path)
    
    
    # Tworzenie DataFrame dla wyjresu logów w pliku app.log
    #log_counts = count_log_levels(log_file_path) # załóżmy, że log_counts to twoje dane
    log_counts_df = pd.DataFrame(list(log_counts.items()), columns=['Log Level', 'Count'])

    # Tworzenie wykresu kołowego
    fig, ax = plt.subplots(figsize=(6, 3))  # Utworzenie figury i osi
    ax.pie(log_counts_df['Count'], labels=log_counts_df['Log Level'], autopct='%1.1f%%', startangle=140)
    ax.set_title('Rozkład typów logów w systemie')

    # Zmiana koloru tła
    ax.set_facecolor('black')  # Możesz wybrać dowolny kolor
    fig.patch.set_facecolor('lightgrey')  # Zmiana koloru tła figury

    # Konwertowanie wykresu na HTML img
    chart6 = plot_to_html_img(plt)
    
    
    return render_template('reports_and_statistics.html', chart1 = chart1, chart2 = chart2, chart3 = chart3, chart4=chart4, chart5=chart5, average_response_time=average_response_time, 
                           normal_count = normal_count, high_count = high_count, urgent_count = urgent_count, total_count=total_count, log_counts = log_counts, chart6 = chart6)
    


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




@app.route('/branch_locator', methods=['GET', 'POST'])
def branch_locator():
    return render_template('branch_locator.html')


@app.route('/service_status', methods=['GET', 'POST'])
def service_status():
    return render_template('service_status.html')


@app.route('/privacy', methods=['GET', 'POST'])
def privacy():
    return render_template('privacy.html')

@app.route('/careers', methods=['GET', 'POST'])
def careers():
    return render_template('careers.html')

@app.route('/contact_us', methods=['GET', 'POST'])
def contact_us():
    return render_template('contact_us.html')

'''
665 linii 
'''

if __name__ == "__main__":
    initialize_app()
    
    app.run(debug=True)