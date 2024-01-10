from flask import Flask, render_template, flash, request, url_for, redirect, session, abort
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from forms.forms import AddCustomerForm, DeleteUserForm, ChangePasswordForm, AddRecipientForm, SendQueryForm, LockUser
from datetime import timedelta, date, datetime
from routes.transfer import transfer_bp, login_bp, ddso_bp, create_transaction_bp, edit_profile_bp
from routes.my_routes import grocery1_bp, grocery2_bp, grocery3_bp, grocery4_bp, gas_bp, power_bp, petrol_bp, clothes_bp, water_bp, add_customer_bp
from models.models import Users, Transaction, db, Recipient, DDSO, SupportTickets, LockedUsers
from functools import wraps
from urllib.parse import quote
from flask_migrate import Migrate
from sqlalchemy import func

login_manager = LoginManager()
login_manager.login_view = 'login_bp.login'

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'bc684cf3981dbcacfd60fc34d6985095'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ib_database_users.db'  # Ustawienie nazwy bazy danych
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Zalecane dla wydajności
    app.permanent_session_lifetime = timedelta(minutes = 45)
    
    csrf = CSRFProtect(app)
    
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Inicjalizacja db z obiektem app
    db.init_app(app)
    #migrate = Migrate(app, db)

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
        
def admin_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)  # Zwraca błąd 403 Forbidden, jeśli użytkownik nie jest adminem
        return func(*args, **kwargs)
    return decorated_view
    

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



@app.route('/admin_dashboard', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_dashboard():
    
    
    # Tutaj dodaj logikę wyświetlania informacji o wszystkich kontach klientów
    # Możesz pobierać dane z bazy danych przy użyciu SQLAlchemy
    # Pobierz wszystkich użytkowników z bazy danych
    all_users = Users.query.all()

    # Renderuj szablon, przekazując dane o użytkownikach
    return render_template('admin_dashboard.html', all_users=all_users)

@app.route('/communication_with_clients', methods=['GET', 'POST'])
@login_required
@admin_required
def cwc():
    all_queries = SupportTickets.query.all()

    
    return render_template('communication_with_clients.html', all_queries = all_queries)
    


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

    return render_template('transaction_management.html', all_users=all_users, all_transactions=all_transactions)

    
    
@app.route('/transactions_filter', methods=['GET', 'POST'])
@login_required
@admin_required  
def transactions_filter():
    all_users = Users.query.all()
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

        return render_template('transaction_management.html', transactions=transactions)

    return render_template('transaction_management.html', all_users=all_users, all_transactions=all_transactions)


@app.route('/help_center', methods=['GET', 'POST']) # pracujemy Panie szanowny :]
@login_required
def help_center():
    #user_queries = SupportTickets.query.filter_by(user_id=current_user.id).all()
    
    # Najpierw tworzymy subzapytanie, aby znaleźć najnowsze daty dla każdego unikalnego numeru referencyjnego
    subquery = db.session.query(SupportTickets.reference_number,func.max(SupportTickets.created_at).label('max_date')).group_by(SupportTickets.reference_number).subquery()

    # Następnie dołączamy to subzapytanie do głównego zapytania, aby pobrać ostatnie rekordy
    user_queries = db.session.query(SupportTickets).join(subquery,(SupportTickets.reference_number == subquery.c.reference_number) &
        (SupportTickets.created_at == subquery.c.max_date)).filter(SupportTickets.user_id == current_user.id).all()

    
    return render_template('help_center.html', all_queries = user_queries)


def generate_unique_reference_number(username):
    """
    Generuje unikalny numer referencyjny dla użytkownika.

    :param username: Nazwa użytkownika, która ma zostać dołączona do numeru referencyjnego.
    :return: Unikalny numer referencyjny.
    """
    new_reference_number = SupportTickets.query.count() + 1

    while True:
        # Tworzenie potencjalnie unikalnego numeru referencyjnego
        potential_ref_number = f'{new_reference_number:06}{username}'
        
        # Sprawdzanie, czy numer referencyjny już istnieje
        existing_ticket = SupportTickets.query.filter_by(reference_number=potential_ref_number).first()
        
        if not existing_ticket:
            return potential_ref_number  # Unikalny numer referencyjny został znaleziony
        else:
            new_reference_number += 1  # Zwiększenie liczby i ponowna próba
            print(potential_ref_number)


@app.route('/block_customer', methods=['GET', 'POST'])
@login_required
@admin_required
def block_customer():
    form = LockUser()
    
    if form.validate_on_submit():
        user_for_lock = LockedUsers(username = form.username.data)
        
        db.session.add(user_for_lock)
        print(user_for_lock)
        
        db.session.commit()
        
        all_locked_users = LockedUsers.query.all()
        flash('User account locked successfully!', 'success')
        return render_template('admin_dashboard_cam.html', all_locked_users = all_locked_users)  



@app.route('/query_sended', methods=['GET', 'POST']) 
@login_required
def send_query():
    form = SendQueryForm()
    
    if form.validate_on_submit():
        
        if form.category.data == 'general' or form.category.data == 'service problem':
            current_priority = 'normal'
        elif form.category.data == 'money transfer':
            current_priority = 'high'
        elif form.category.data == 'fraud':
            current_priority = 'urgent'
            
        new_query = SupportTickets(user_id = current_user.id,
                                  title = form.title.data,
                                  description = form.description.data,
                                  category = form.category.data,
                                  reference_number = generate_unique_reference_number(current_user.username),
                                  #reference_number = formatted_reference_number,
                                  created_at = datetime.utcnow(),
                                  status = 'new',
                                  priority = current_priority)
        
        db.session.add(new_query)
        print(new_query)
            
        # Zatwierdzenie zmian w bazie danych
        db.session.commit()
        
        flash('Message sent successfully!', 'success')
        return redirect(url_for('help_center'))
    
    else:
        print(form.errors)  # Wydrukuj błędy formularza
    return render_template('help_center.html', form=form)
        
    
    
    
    
    
    
    

@app.route('/process_query/<query_ref>', methods=['GET', 'POST'])
@login_required
@admin_required
def process_query(query_ref):
    print("Received reference number:", query_ref)  # Wydruk kontrolny
    # Pobieranie zapytania z bazy danych za pomocą ID
    
    user_queries = SupportTickets.query.filter_by(reference_number=query_ref).all()
    last_query = SupportTickets.query.filter_by(reference_number=query_ref).order_by(SupportTickets.created_at.desc()).first()
    
    # Jeśli metoda to GET, renderuj szablon z detalami zapytania do przetworzenia
    return render_template('processing_clients_query.html', all_queries=user_queries, query=last_query)



@app.route('/read_message/<query_ref>', methods=['GET', 'POST'])
@login_required
def read_message(query_ref):
    print("Received reference number:", query_ref)  # Wydruk kontrolny
    
    user_queries = SupportTickets.query.filter_by(reference_number=query_ref).all()
    last_query = SupportTickets.query.filter_by(reference_number=query_ref).order_by(SupportTickets.created_at.desc()).first()
    
    return render_template('reading_my_messages.html', all_queries=user_queries, query=last_query)





@app.route('/send_message_for_query/<query_ref>', methods=['GET', 'POST'])
@login_required
@admin_required
def send_message_for_query(query_ref):
    print('query ref = ', query_ref)
    
    # Pobieranie zapytania z bazy danych za pomocą ID
    
    last_query = SupportTickets.query.filter_by(reference_number=query_ref).order_by(SupportTickets.created_at.desc()).first()
    
    # Pobranie danych z formularza
    new_query = SupportTickets(user_id = last_query.user_id,
                                title = last_query.title,
                                description = request.form['description'],
                                category = last_query.category,
                                reference_number = last_query.reference_number,
                                created_at = datetime.utcnow(),
                                status = request.form['status'],
                                priority = last_query.priority)
        
    db.session.add(new_query)
    
    #db.session.delete(SupportTickets.query.get(3))  # - kasuje rekord o ID 3
    #db.session.delete(SupportTickets.query.get(4))

    # Zapisanie zmian w bazie danych
    db.session.commit()
    
    flash('Your response has been sent successfully', 'success')
    return redirect(url_for('process_query', query_ref=last_query.reference_number))
    
    
    
@app.route('/send_message_for_message/<query_ref>', methods=['GET', 'POST'])
@login_required
def send_message_for_message(query_ref):
    print("Klient odpowiada na wiadomosc z nr ref: ", query_ref)
    
    last_query = SupportTickets.query.filter_by(reference_number=query_ref).order_by(SupportTickets.created_at.desc()).first()
    # Pobranie danych z formularza
    new_query = SupportTickets(user_id = last_query.user_id,
                                title = last_query.title,
                                description = request.form['description'],
                                category = last_query.category,
                                reference_number = last_query.reference_number,
                                created_at = datetime.utcnow(),
                                status = last_query.status,
                                priority = last_query.priority)
        
    db.session.add(new_query)
    db.session.commit()
    user_queries = SupportTickets.query.filter_by(reference_number=query_ref).all()
    flash('Your response has been sent successfully', 'success')
    return render_template('reading_my_messages.html', query_ref=last_query.reference_number, all_queries=user_queries, query=last_query)
    


@app.route('/delete_messages_for_query/<query_ref>', methods=['GET', 'POST'])
@login_required
def delete_messages_for_query(query_ref):
    print("Kasuję wszystkie wiadomości dla nr ref: ", query_ref)
    
    last_query = SupportTickets.query.filter_by(reference_number=query_ref).order_by(SupportTickets.created_at.desc()).first()
    user_queries = SupportTickets.query.filter_by(reference_number=query_ref).all()
    
    
    messages_quantity = SupportTickets.query.filter_by(reference_number=query_ref).count()
    print(messages_quantity)
    
    return render_template('dmfq.html', query_ref=last_query.reference_number, all_queries=user_queries, query=last_query, messages_quantity = messages_quantity)
    
    
@app.route('/delete_query_confirmation/<query_ref>', methods=['GET', 'POST'])  
@login_required
def delete_query_confirmation(query_ref):
    
    last_query = SupportTickets.query.filter_by(reference_number=query_ref).order_by(SupportTickets.created_at.desc()).first()
    user_queries = SupportTickets.query.filter_by(reference_number=query_ref).all()
    
    
    # Sprawdzenie, czy użytkownik ma uprawnienia do usunięcia tych rekordów
    # (to jest ważne, aby uniknąć usuwania rekordów przez nieautoryzowane osoby)
    if last_query.user_id == current_user.id:
        # Usunięcie wszystkich rekordów z danym numerem referencyjnym
        for query in user_queries:
            db.session.delete(query)
        db.session.commit()

        flash('Your query has been deleted successfully', 'success')
    else:
        flash('You do not have permission to delete this query', 'error')

    # Odświeżenie listy rekordów do wyświetlenia
    user_queries = SupportTickets.query.filter_by(user_id=current_user.id).all()

    
    # flash('Your query has been deleted successfully', 'success')
    return redirect(url_for('help_center', query_ref=last_query.reference_number, all_queries = user_queries))
    #return render_template('help_center.html', all_queries = user_queries)

    
    







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
430
511 - 08.01.2024
'''

if __name__ == "__main__":
    initialize_app()
    
    app.run(debug=True)