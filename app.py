from flask import Flask, render_template, flash, request, url_for, redirect, session
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from forms.forms import LoginForm, TransferForm, AddCustomerForm, CreateTransactionForm, DeleteUserForm, EditUserForm, ChangePasswordForm, AddRecipientForm
from datetime import timedelta, date

from routes.transfer import transfer_bp, login_bp
from models.models import Users, Transaction, db, Recipient

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

    # ... Rejestracja Blueprintów, inne konfiguracje ...
    app.register_blueprint(transfer_bp)
    app.register_blueprint(login_bp)

    

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


 
        
    
    
    
def handle_grocery_transaction(amount, recipient_id, description, description2, description3):
    # Twoja istniejąca logika sprawdzania salda i transakcji
    #user_transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    
    # Pobierz ostatnią transakcję kupującego, aby sprawdzić jego saldo
    last_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
    
    if current_user.id == recipient_id:
        flash('You cannot buy your own products and services !!!', 'danger') 
        return redirect(url_for('online_shop'))
        
        
    if last_transaction.balance < amount:
            flash('Insufficient funds.', 'danger')
            return redirect(url_for('online_shop'))
        
    else:    
        # Logika wykonania przelewu
        try:
            # Przygotowanie wspólnych danych dla transakcji
            transaction_date = date.today()
            
            # Aktualizacja salda nadawcy
            sender_balance = last_transaction.balance - amount
            new_sender_transaction = Transaction(user_id=current_user.id, 
                                                transaction_date=transaction_date,
                                                transaction_type='DD',
                                                sort_code=last_transaction.sort_code,
                                                account_number=last_transaction.account_number,
                                                transaction_description=description,
                                                debit_amount=amount,
                                                credit_amount = 0,
                                                balance=sender_balance)
            db.session.add(new_sender_transaction)
            
            # Znajdź ostatnią transakcję odbiorcy - sklepu FreshFood
            last_recipient_transaction = Transaction.query.filter_by(user_id=recipient_id).order_by(Transaction.id.desc()).first()
            
            recipient_balance = last_recipient_transaction.balance + amount
            
            new_recipient_transaction = Transaction(user_id=recipient_id,
                                                        transaction_date=transaction_date,
                                                        transaction_type='FPI',
                                                        sort_code=last_recipient_transaction.sort_code,
                                                        account_number=last_recipient_transaction.account_number,
                                                        transaction_description=description2,
                                                        debit_amount = 0,
                                                        credit_amount=amount,
                                                        balance=recipient_balance)
            db.session.add(new_recipient_transaction)
            
            # Zatwierdzenie zmian w bazie danych
            db.session.commit()
            
            flash(f'{description3} purchase completed successfully!', 'success')
            return redirect(url_for('online_shop'))
        
        except Exception as e:
                print(7)
                db.session.rollback()
                flash('An error occurred. Purchase failed.', 'danger')
                return render_template('online_shop.html', user=current_user, last_transaction=last_transaction)
            
            
 
    
    
    
    
    
    
@app.route('/grocery1', methods=['GET', 'POST'])
@login_required
def grocery1():
    amount = 65
    recipient_id = 16
    description = 'Grocery - Dairy purchase'
    description2 = 'Grocery - Dairy sale'
    description3 = 'Dairy'
    
    return handle_grocery_transaction(amount, recipient_id, description, description2, description3)

   
@app.route('/grocery2', methods=['GET', 'POST'])
@login_required
def grocery2():
    amount = 50
    recipient_id = 16 
    description = 'Grocery - Fruits & veggies purchase'
    description2 = 'Grocery - Fruits & veggies sale'
    description3 = 'Fruits & veggies'
    
    return handle_grocery_transaction(amount, recipient_id, description, description2, description3)    

@app.route('/grocery3', methods=['GET', 'POST'])
@login_required
def grocery3():
    amount = 45
    recipient_id = 16  
    description = 'Grocery - Fish & meat purchase'
    description2 = 'Grocery - Fish & meat sale'
    description3 = 'Fish & meat'
    
    return handle_grocery_transaction(amount, recipient_id, description, description2, description3)


@app.route('/grocery4', methods=['GET', 'POST'])
@login_required
def grocery4():
    amount = 25
    recipient_id = 16  
    description = 'Grocery - Bread and rolls purchase'
    description2 = 'Grocery - Bread and rolls sale'
    description3 = 'Bread & rolls'
    
    return handle_grocery_transaction(amount, recipient_id, description, description2, description3)


@app.route('/gas', methods=['GET', 'POST'])
@login_required
def gas():
    amount = 50
    recipient_id = 18  
    description = 'Gas purchase'
    description2 = 'Gas sale'
    description3 = 'Gas'
    
    return handle_grocery_transaction(amount, recipient_id, description, description2, description3)


@app.route('/power', methods=['GET', 'POST'])
@login_required
def power():
    amount = 60
    recipient_id = 18  
    description = 'Electric purchase'
    description2 = 'Electric sale'
    description3 = 'Electric '
    
    return handle_grocery_transaction(amount, recipient_id, description, description2, description3)


@app.route('/water', methods=['GET', 'POST'])
@login_required
def water():
    amount = 110
    recipient_id = 17  
    description = 'Water purchase'
    description2 = 'Water sale'
    description3 = 'Water'
    
    return handle_grocery_transaction(amount, recipient_id, description, description2, description3)

@app.route('/clothes', methods=['GET', 'POST'])
@login_required
def clothes():
    amount = 150
    recipient_id = 22
    description = 'Clothes purchase'
    description2 = 'Clothes sale'
    description3 = 'Clothes'
    
    return handle_grocery_transaction(amount, recipient_id, description, description2, description3)


@app.route('/petrol', methods=['GET', 'POST'])
@login_required
def petrol():
    amount = 120
    recipient_id = 21
    description = 'Petrol purchase'
    description2 = 'Petrol sale'
    description3 = 'Petrol'
    
    return handle_grocery_transaction(amount, recipient_id, description, description2, description3)









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
def admin_dashboard():
    if current_user.role != 'admin':
        return 'Access denied'
    
    # Tutaj dodaj logikę wyświetlania informacji o wszystkich kontach klientów
    # Możesz pobierać dane z bazy danych przy użyciu SQLAlchemy
    # Pobierz wszystkich użytkowników z bazy danych
    all_users = Users.query.all()

    # Renderuj szablon, przekazując dane o użytkownikach
    return render_template('admin_dashboard.html', all_users=all_users)


@app.route('/admin_dashboard_cm', methods=['GET', 'POST'])
@login_required
def admin_dashboard_cm():
    if current_user.role != 'admin':
        return 'Access denied'
    
    # Tutaj dodaj logikę wyświetlania informacji o wszystkich kontach klientów
    # Możesz pobierać dane z bazy danych przy użyciu SQLAlchemy
    # Pobierz wszystkich użytkowników z bazy danych
    all_users = Users.query.all()
    all_transactions = Transaction.query.all()

    # Renderuj szablon, przekazując dane o użytkownikach
    return render_template('admin_dashboard_cm.html', all_users=all_users, all_transactions=all_transactions)
    


@app.route('/create_transaction', methods=['GET', 'POST'])      # nie ma zabezpieczenia , sprawdzic czy istnieje już taki sam sort code i account number
@login_required
def create_transaction():
    if current_user.role != 'admin':
        return 'Access denied'
    
    all_users = Users.query.all()
    all_transactions = Transaction.query.all()
    form = CreateTransactionForm()
    print(1)

    # Ładowanie użytkowników do wyboru
    form.user_id.choices = [(user.id, user.username) for user in Users.query.all()]

    if form.validate_on_submit():
        # Tworzenie obiektu transakcji
        print(2)
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
        print(3)
        return redirect(url_for('admin_dashboard_cm'))  # Przekierowanie do odpowiedniej strony

    print(4)
    return render_template('admin_dashboard_cm.html', all_users=all_users, form=form, all_transactions=all_transactions)                   



# Dodaj trasę do obsługi formularza dodawania klienta
@app.route('/add_customer', methods=['GET', 'POST'])
@login_required
def add_customer():
    
    if current_user.role != 'admin':
        return 'Access denied'

    form = AddCustomerForm(request.form)
    
    if form.validate_on_submit():
        # Uzyskaj dane z formularza
        username = form.username.data
        password = form.password.data
        email = form.email.data
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        
        # Sprawdź, czy użytkownik o podanym username lub email już istnieje
        existing_user = Users.query.filter((Users.username == username) | (Users.email == email)).first()

        if existing_user:
            
            # Użytkownik o podanym username lub email już istnieje
            flash('User with given username or email already exists.', 'error')
            return render_template('user_exist.html')
        else:
            # Utwórz nowego użytkownika i dodaj go do bazy danych
            
            role = form.role.data
            country = form.country.data
            email = form.email.data
            phone_number = form.phone_number.data

            new_user = Users(username=username, password_hash=password_hash, role=role, email=email, phone_number=phone_number, country=country)
            db.session.add(new_user)
            db.session.commit()

            flash('User added successfully.', 'success')
            return redirect(url_for('admin_dashboard_cm'))
    
    # Jeśli formularz nie jest poprawny, ponów renderowanie strony z błędami
    #return render_template('admin_dashboard', form=form)



@app.route('/delete_user', methods=['GET', 'POST'])
@login_required
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



@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required  # Upewnij się, że tylko zalogowani użytkownicy mogą edytować profil
def edit_profile():
    form = EditUserForm()

    if form.validate_on_submit():
        current_user.email = form.email.data
        current_user.phone_number = form.phone_number.data
        current_user.country = form.country.data
        
        db.session.commit()
        flash('Your profile has been updated.')
        return redirect(url_for('dashboard'))

    elif request.method == 'GET':
        form.email.data = current_user.email
        form.phone.data = current_user.phone
        form.country.data = current_user.country
        # Załaduj inne pola
    else:
        print(form.errors) 

    user_transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', user=current_user, all_transactions=user_transactions)




@app.route('/team', methods=['GET', 'POST'])
@login_required
def team():
    if current_user.role != 'admin':
        return 'Access denied'
    
    # Tutaj dodaj logikę wyświetlania informacji o wszystkich kontach klientów
    # Pobierz wszystkich użytkowników z bazy danych
    all_users = Users.query.all()
    
    return render_template('team.html', all_users=all_users)
    

@app.route('/admin/users')
@login_required
def list_users():
    all_users = Users.query.all()
    return render_template('list_users.html', all_users=all_users)


@app.route('/admin/change-password/<int:user_id>', methods=['GET', 'POST'])
@login_required  # Upewnij się, że tylko administratorzy mają dostęp

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

520
'''

if __name__ == "__main__":
    initialize_app()
    app.run(debug=True)

