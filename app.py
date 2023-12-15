from flask import Flask, render_template, flash, request, url_for, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
#from forms.forms import TransferForm, RegistrationForm, LoginForm, AddCustomerForm
from datetime import timedelta, date
from flask_migrate import Migrate



from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField, PasswordField, SelectField, DateField
from wtforms.validators import DataRequired, Length, EqualTo, NumberRange

    
class MyForm(FlaskForm):
    name = StringField('Name')
    submit = SubmitField('Submit')    

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    #password = PasswordField('Password', validators=[DataRequired()])
    #confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')
    
    
class TransferForm(FlaskForm):
    recipient_sort_code = StringField('Recipient Sort Code', validators=[DataRequired()])
    recipient_account_number = StringField('Recipient Account Number', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    transaction_description = StringField('Description', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Transfer')
    
 
    
    
class AddCustomerForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    role = SelectField('Role', choices=[('client', 'Client'), ('bank_emploee', 'Bank Employee'), ('board_member', 'Board Member'), ('management', 'Management')], validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    phone_number = StringField('Phone number', validators=[DataRequired()])
    country = StringField('Country', validators=[DataRequired()])
    
    
    
class CreateTransactionForm(FlaskForm):
    user_id = SelectField('User', coerce=int, validators=[DataRequired()])
    transaction_date = DateField('Transaction Date', format='%Y-%m-%d', validators=[DataRequired()])
    transaction_type = SelectField('Transaction Type', choices=[('DEB', 'Debit'), ('DD', 'Direct Debit'), ('SAL', 'Salary'), ('CSH', 'Cash'), ('SO', 'Standing Order'), ('FPI', 'Faster Payment Incoming'), ('FPO', 'Faster Payment Outgoing'), ('MTG', 'Mortgage')], validators=[DataRequired()])
    sort_code = StringField('Sort Code', validators=[DataRequired(), Length(min=6, max=10)])
    account_number = StringField('Account Number', validators=[DataRequired(), Length(min=5, max=20)])
    transaction_description = StringField('Description', validators=[DataRequired()])
    debit_amount = FloatField('Debit Amount', validators=[NumberRange(min=0)])
    credit_amount = FloatField('Credit Amount', validators=[NumberRange(min=0)])
    balance = FloatField('Balance', validators=[NumberRange(min=0)])
    submit = SubmitField('Create Transaction')
    

class DeleteUserForm(FlaskForm):
    username = StringField('Nazwa Użytkownika', validators=[DataRequired()])
    submit = SubmitField('Usuń Użytkownika')


app = Flask(__name__)

app.config['SECRET_KEY'] = 'bc684cf3981dbcacfd60fc34d6985095'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ib_database_users.db'  # Ustawienie nazwy bazy danych
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Zalecane dla wydajności
app.permanent_session_lifetime = timedelta(minutes = 45)

db = SQLAlchemy(app)

csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
csrf.init_app(app)


migrate = Migrate(app, db)


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
    
    
# obiekt w bazie danych reprezentujący transakcje
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
    

@app.before_request
def initialize_database():
    db.create_all()
    
    

def initialize_app():
    with app.app_context():
        db.create_all()
        create_sample_user()
        create_sample_client()
        
    
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
         
         
       
    
         
         
def create_sample_client():
    # Sprawdź, czy klient o nazwie 'Janek' już istnieje
    existing_client = Users.query.filter_by(username='Janek').first()

    if not existing_client:
        client = Users(username='Janek', role='client', email='janek@serwis.pl', phone_number='+48606675555', country='Poland')
        client.set_password('haslo')
        db.session.add(client)
        db.session.commit()
        
        
       
        

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/base', methods=['GET'])
def base():
    return render_template('base.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        user = Users(username=form.username.data)
        user.set_password(form.password.data)

        #db.session.add(user)
        #db.session.commit()

        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)






@app.route('/login', methods=['GET', 'POST'])
def login():
    
    form = LoginForm()
    
    if request.method == "POST":
        session.permanent = True
        if form.validate_on_submit():
            user = Users.query.filter_by(username=form.username.data).first()
            if user and user.check_password(form.password.data):
                login_user(user)
                flash("Login succesful!")
                
                # Przekieruj do strony admin_dashboard dla administratora
                if user.role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                # Przekieruj do strony dashboard dla klienta
                else:
                    return redirect(url_for('dashboard'))
            else:
                flash('Login unsuccessful. Please check your username and password.', 'danger')     
                
        return render_template('login.html', form = form)   
        
    # Jeśli użytkownik jest już zalogowany, przekieruj go do odpowiedniej strony
    if current_user.is_authenticated:
        flash("Already Logged In")
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('dashboard'))


    return render_template('login.html', form = form)




@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Zostałeś wylogowany.', 'success')
    return redirect(url_for('index'))




@app.route('/dashboard')
@login_required
def dashboard():
    
    user_transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', user=current_user, all_transactions=user_transactions)





@app.route('/admin_dashboard')
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


@app.route('/admin_dashboard_cm')
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
    


@app.route('/create_transaction', methods=['GET', 'POST'])
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




















@app.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer():
    form = TransferForm()
    print(1)

    if form.validate_on_submit():
        print(2)
        recipient_sort_code = form.recipient_sort_code.data
        recipient_account_number = form.recipient_account_number.data
        amount = form.amount.data
        transaction_description = form.transaction_description.data
        confirm_password = form.confirm_password.data
        
        # Sprawdź, czy hasło jest poprawne
        if not current_user.check_password(confirm_password):
            print(3)
            flash('Invalid password.', 'danger')
            return redirect(url_for('dashboard')) 
        
        
        # Sprawdź, czy odbiorca istnieje, sprawdza po sort code i account number
        recipient = Users.query.join(Transaction).filter(Transaction.account_number == recipient_account_number, Transaction.sort_code == recipient_sort_code).first()
        if not recipient:
            print(4)
            flash('Recipient account not found.', 'danger')
            return redirect(url_for('dashboard')) 

        
        
        # Pobierz ostatnią transakcję nadawcy, aby sprawdzić jego saldo
        last_sender_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.transaction_date.desc()).first()
        if not last_sender_transaction or last_sender_transaction.balance < amount:
            print(5)
            flash('Insufficient funds.', 'danger')
            return redirect(url_for('dashboard')) 
        
        # Logika wykonania przelewu
        try:
            print(6)
            # Przygotowanie wspólnych danych dla transakcji
            transaction_date = date.today()
            
            
            # Aktualizacja salda nadawcy
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
            
            
            

            # Znajdź ostatnią transakcję odbiorcy
            last_recipient_transaction = Transaction.query.filter_by(user_id=recipient.id).order_by(Transaction.transaction_date.desc()).first()
            last_recipient_balance = last_recipient_transaction.balance
            # last_recipient_balance = last_recipient_transaction.balance if last_recipient_transaction else 0
            
            # Aktualizacja salda odbiorcy
            new_recipient_transaction = Transaction(user_id=recipient.id, 
                                                    transaction_date=transaction_date,
                                                    transaction_type='FPI',
                                                    sort_code=last_recipient_transaction.sort_code,
                                                    account_number=last_recipient_transaction.account_number,
                                                    transaction_description=transaction_description,
                                                    debit_amount = 0,
                                                    credit_amount=amount,
                                                    balance=last_recipient_balance + amount
            )
            db.session.add(new_recipient_transaction)
            

            # Zatwierdzenie zmian w bazie danych
            db.session.commit()
            flash('Transfer successful!', 'success')
            return redirect(url_for('dashboard'))
        
        except Exception as e:
            print(7)
            db.session.rollback()
            flash('An error occurred. Transfer failed.', 'danger')
            return render_template('transfer.html', form=form)

        # Obsługa procesu przesyłania środków
        # Sprawdzenie dostępności środków: Przed zrealizowaniem transferu należy sprawdzić, czy nadawca ma wystarczające środki na swoim koncie do wykonania przelewu.
        # Walidacja danych odbiorcy: Upewnij się, że dane odbiorcy (np. numer konta) są poprawne i istnieje w systemie.
        # Sprawdzenie kwoty przelewu: Sprawdź, czy kwota przelewu jest dodatnia i nie przekracza ustalonych limitów i jest niższa niż saldo konta
        # Walidacja hasła: Jeśli w formularzu jest pole do potwierdzenia hasła, upewnij się, że hasło jest poprawne przed zatwierdzeniem transakcji.
        #  zaktualizuj saldo,
        #   dodaj transakcję do bazy danych danego klienta
    
    else:
        print(form.errors)   
    print(8)    
    user_transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', user=current_user, all_transactions=user_transactions)    
    



















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
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        
        # Sprawdź, czy użytkownik o podanym username lub email już istnieje
        existing_user = Users.query.filter((Users.username == username) | (Users.password_hash == password_hash)).first()

        if existing_user:
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
Nagłówki Bezpieczeństwa:
Rozważ dodanie nagłówków bezpieczeństwa do odpowiedzi, takich jak nagłówki Content Security Policy (CSP), aby zwiększyć bezpieczeństwo Twojej aplikacji internetowej.

@app.route('/transactions')
@login_required
def transactions_history():
    transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    return render_template('transactions_history.html', transactions=transactions)
    
'''


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


if __name__ == "__main__":
    initialize_app()
    app.run(debug=True)

# 293