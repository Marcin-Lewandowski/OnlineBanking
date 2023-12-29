from flask import Flask, render_template, flash, request, url_for, redirect, session, abort
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from forms.forms import AddCustomerForm, DeleteUserForm, ChangePasswordForm, AddRecipientForm
from datetime import timedelta, date
from routes.transfer import transfer_bp, login_bp, ddso_bp, create_transaction_bp, edit_profile_bp
from routes.my_routes import grocery1_bp, grocery2_bp, grocery3_bp, grocery4_bp, gas_bp, power_bp, petrol_bp, clothes_bp, water_bp, add_customer_bp
from models.models import Users, Transaction, db, Recipient, DDSO
from functools import wraps

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
@admin_required
def admin_dashboard():
    
    
    # Tutaj dodaj logikę wyświetlania informacji o wszystkich kontach klientów
    # Możesz pobierać dane z bazy danych przy użyciu SQLAlchemy
    # Pobierz wszystkich użytkowników z bazy danych
    all_users = Users.query.all()

    # Renderuj szablon, przekazując dane o użytkownikach
    return render_template('admin_dashboard.html', all_users=all_users)


@app.route('/admin_dashboard_cm', methods=['GET', 'POST'])
@admin_required
def admin_dashboard_cm():
    
    # Tutaj dodaj logikę wyświetlania informacji o wszystkich kontach klientów
    # Możesz pobierać dane z bazy danych przy użyciu SQLAlchemy
    # Pobierz wszystkich użytkowników z bazy danych
    all_users = Users.query.all()
    all_transactions = Transaction.query.all()

    # Renderuj szablon, przekazując dane o użytkownikach
    return render_template('admin_dashboard_cm.html', all_users=all_users, all_transactions=all_transactions)
                      



@app.route('/delete_user', methods=['GET', 'POST'])
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
@admin_required
def team():
    
    # Widok wyświetla członków zarządu, management, pracowników banku, logika na stronie html
    # Pobierz wszystkich użytkowników z bazy danych
    all_users = Users.query.all()
    
    return render_template('team.html', all_users=all_users)
    

@app.route('/admin/users')
@admin_required
def list_users():
    all_users = Users.query.all()
    return render_template('list_users.html', all_users=all_users)


@app.route('/admin/change-password/<int:user_id>', methods=['GET', 'POST'])
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
640 --> 300
'''

if __name__ == "__main__":
    initialize_app()
    
    app.run(debug=True)