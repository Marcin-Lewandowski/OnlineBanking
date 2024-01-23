from flask import Blueprint, render_template, request, session, flash, url_for, redirect, abort

from flask_login import current_user, login_required, login_user
from forms.forms import TransferForm, LoginForm, DDSOForm, CreateTransactionForm, EditUserForm
from datetime import date
from models.models import Users, Transaction, db, DDSO, LockedUsers
from functools import wraps



def admin_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)  # Zwraca błąd 403 Forbidden, jeśli użytkownik nie jest adminem
        return func(*args, **kwargs)
    return decorated_view



transfer_bp = Blueprint('transfer_bp', __name__)

@transfer_bp.route('/transfer', methods=['GET', 'POST'])
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
        last_sender_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
        
        # Sprawdź czy sort code i account_number są danymi wysyłającego
        if recipient_sort_code == last_sender_transaction.sort_code and recipient_account_number == last_sender_transaction.account_number:
            flash('You can not send money to your own account!', 'danger')
            return redirect(url_for('dashboard'))
        
        
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
            last_recipient_transaction = Transaction.query.filter_by(user_id=recipient.id).order_by(Transaction.id.desc()).first()
            last_recipient_balance = last_recipient_transaction.balance
            
            # Aktualizacja salda odbiorcy
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
            

            # Zatwierdzenie zmian w bazie danych
            db.session.commit()
            flash('Transfer successful!', 'success')
            return redirect(url_for('dashboard'))
        
        except Exception as e:
            print(7)
            db.session.rollback()
            flash('An error occurred. Transfer failed.', 'danger')
            return render_template('transfer.html', form=form)
    
    else:
        print(form.errors)   
    print(8)    
    user_transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', user=current_user, all_transactions=user_transactions)





login_bp = Blueprint('login_bp', __name__)

@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    
    form = LoginForm()
    if request.method == "POST":
        session.permanent = True # Ustawienie sesji jako trwałej
        if form.validate_on_submit():
            user = Users.query.filter_by(username=form.username.data).first()
            if user and user.check_password(form.password.data):
                # Sprawdzenie, czy użytkownik o tej nazwie istnieje jest zablokowany
                
                
                print("Sprawdza czy user jest zablokowany")
            
                locked_user = LockedUsers.query.filter_by(username=user.username).first()

                if locked_user:
                    print("User jest zablokowany")
                    return render_template('account_locked.html', locked_user = locked_user)
                else:
                    
                    login_user(user)
                    flash("Login succesful!")
                    print(user.username)
                    session['login_attempts'] = 0
                    
                    # Przekieruj do strony admin_dashboard dla administratora
                    if user.role == 'admin':
                        return redirect(url_for('admin_dashboard'))
                    # Przekieruj do strony dashboard dla klienta
                    else:
                        return redirect(url_for('dashboard'))
            else:
                flash('Login unsuccessful. Please check your username and password.', 'danger')     
                
                #session['login_attempts'] = 0

                # Zwiększenie liczby nieudanych prób logowania
                session['login_attempts'] += 1
                print("Logowal sie tyle razy - ", session['login_attempts'])
                
                # Sprawdzenie, czy przekroczono maksymalną liczbę prób
                if session['login_attempts'] >= 3:
                    # Zablokuj konto
                    locked_user = LockedUsers(username=user.username)
                    session['login_attempts'] = 0
                    
                    print("User zablokowany: licznik nieudanych prob logowania zresetowany i wynosi: - ", session['login_attempts'])
                    
                    
                    db.session.add(locked_user)
                    db.session.commit()
                    
                    
                    flash("Twoje konto zostało zablokowane po przekroczeniu maksymalnej liczby nieudanych prób logowania.")
                    return render_template('account_locked.html', locked_user = locked_user)
                
                
                
                
                
        return render_template('login.html', form = form)   
        
    # Jeśli użytkownik jest już zalogowany, przekieruj go do odpowiedniej strony
    if current_user.is_authenticated:
        flash("Already Logged In")
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('dashboard'))


    return render_template('login.html', form = form)


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
        
        # Sprawdź, czy hasło jest poprawne
        if not current_user.check_password(confirm_password):
            print(3)
            flash('Invalid password.', 'danger')
            return redirect(url_for('dashboard'))
        
        # Sprawdź, czy odbiorca istnieje, po username
        recipient_exist = Users.query.filter_by(username=form.recipient.data).first()
        
        
        if not recipient_exist:
            print(4)
            flash('Recipient account not found.', 'danger')
            return redirect(url_for('dashboard')) 
        
        
        # Tworzenie nowego zlecenia na podstawie danych z formularza
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
        return redirect(url_for('dashboard'))  # Przekierowanie do strony głównej lub innej strony

    return render_template('ddso.html', form=form, user=current_user, all_transactions=user_transactions, all_dd_so=user_dd_so,  last_transaction=last_transaction)
    


create_transaction_bp = Blueprint('create_transaction_bp', __name__)

@create_transaction_bp.route('/create_transaction', methods=['GET', 'POST'])      # nie ma zabezpieczenia , sprawdzic czy istnieje już taki sam sort code i account number
@login_required
@admin_required
def create_transaction():
    
    all_users = Users.query.all()
    all_transactions = Transaction.query.all()
    form = CreateTransactionForm()

    # Ładowanie użytkowników do wyboru
    form.user_id.choices = [(user.id, user.username) for user in Users.query.all()]

    if form.validate_on_submit():
        # Tworzenie obiektu transakcji
        
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