from flask import Blueprint, render_template, request, flash, url_for, redirect
from flask_login import current_user, login_required
from forms.forms import AddCustomerForm
from datetime import date
from models.models import Users, Transaction, db
from routes.transfer import admin_required
from werkzeug.security import generate_password_hash


def handle_grocery_transaction(amount, recipient_id, description, description2, description3):
    
    # Download a buyer's last transaction to check their balance
    last_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).first()
    
    if current_user.id == recipient_id:
        flash('You cannot buy your own products and services !!!', 'danger') 
        return redirect(url_for('online_shop'))
        
        
    if last_transaction.balance < amount:
            flash('Insufficient funds.', 'danger')
            return redirect(url_for('online_shop'))
        
    else:    
        try:
            # Preparation of data for transactions
            transaction_date = date.today()
            
            # Sender balance update
            sender_balance = last_transaction.balance - amount
            new_sender_transaction = Transaction(user_id=current_user.id, 
                                                transaction_date=transaction_date,
                                                transaction_type='DEB',
                                                sort_code=last_transaction.sort_code,
                                                account_number=last_transaction.account_number,
                                                transaction_description=description,
                                                debit_amount=amount,
                                                credit_amount = 0,
                                                balance=sender_balance)
            db.session.add(new_sender_transaction)
            
            # Find the last transaction of the recipient - the FreshFood store
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
            db.session.commit()
            
            flash(f'{description3} purchase completed successfully!', 'success')
            return redirect(url_for('online_shop'))
        
        except Exception as e:
                print(7)
                db.session.rollback()
                flash('An error occurred. Purchase failed.', 'danger')
                return render_template('online_shop.html', user=current_user, last_transaction=last_transaction)
            
            
            
            
grocery1_bp = Blueprint('grocery1_bp', __name__)            

@grocery1_bp.route('/grocery1', methods=['GET', 'POST'])
@login_required
def grocery1():
    amount = 65
    recipient_id = 16
    description = 'Grocery - Dairy purchase'
    description2 = 'Grocery - Dairy sale'
    description3 = 'Dairy'
    
    return handle_grocery_transaction(amount, recipient_id, description, description2, description3)


grocery2_bp = Blueprint('grocery2_bp', __name__)   
   
@grocery2_bp.route('/grocery2', methods=['GET', 'POST'])
@login_required
def grocery2():
    amount = 50
    recipient_id = 16 
    description = 'Grocery - Fruits & veggies purchase'
    description2 = 'Grocery - Fruits & veggies sale'
    description3 = 'Fruits & veggies'
    
    return handle_grocery_transaction(amount, recipient_id, description, description2, description3)    


grocery3_bp = Blueprint('grocery3_bp', __name__) 

@grocery3_bp.route('/grocery3', methods=['GET', 'POST'])
@login_required
def grocery3():
    amount = 45
    recipient_id = 16  
    description = 'Grocery - Fish & meat purchase'
    description2 = 'Grocery - Fish & meat sale'
    description3 = 'Fish & meat'
    
    return handle_grocery_transaction(amount, recipient_id, description, description2, description3)


grocery4_bp = Blueprint('grocery4_bp', __name__) 

@grocery4_bp.route('/grocery4', methods=['GET', 'POST'])
@login_required
def grocery4():
    amount = 25
    recipient_id = 16  
    description = 'Grocery - Bread and rolls purchase'
    description2 = 'Grocery - Bread and rolls sale'
    description3 = 'Bread & rolls'
    
    return handle_grocery_transaction(amount, recipient_id, description, description2, description3)


gas_bp = Blueprint('gas_bp', __name__) 

@gas_bp.route('/gas', methods=['GET', 'POST'])
@login_required
def gas():
    amount = 50
    recipient_id = 18  
    description = 'Gas purchase'
    description2 = 'Gas sale'
    description3 = 'Gas'
    
    return handle_grocery_transaction(amount, recipient_id, description, description2, description3)


power_bp = Blueprint('power_bp', __name__) 

@power_bp.route('/power', methods=['GET', 'POST'])
@login_required
def power():
    amount = 60
    recipient_id = 18  
    description = 'Electric purchase'
    description2 = 'Electric sale'
    description3 = 'Electric '
    
    return handle_grocery_transaction(amount, recipient_id, description, description2, description3)


water_bp = Blueprint('water_bp', __name__) 

@water_bp.route('/water', methods=['GET', 'POST'])
@login_required
def water():
    amount = 110
    recipient_id = 17  
    description = 'Water purchase'
    description2 = 'Water sale'
    description3 = 'Water'
    
    return handle_grocery_transaction(amount, recipient_id, description, description2, description3)


clothes_bp = Blueprint('clothes_bp', __name__) 

@clothes_bp.route('/clothes', methods=['GET', 'POST'])
@login_required
def clothes():
    amount = 150
    recipient_id = 22
    description = 'Clothes purchase'
    description2 = 'Clothes sale'
    description3 = 'Clothes'
    
    return handle_grocery_transaction(amount, recipient_id, description, description2, description3)


petrol_bp = Blueprint('petrol_bp', __name__) 

@petrol_bp.route('/petrol', methods=['GET', 'POST'])
@login_required
def petrol():
    amount = 120
    recipient_id = 21
    description = 'Petrol purchase'
    description2 = 'Petrol sale'
    description3 = 'Petrol'
    
    return handle_grocery_transaction(amount, recipient_id, description, description2, description3)




add_customer_bp = Blueprint('add_customer_bp', __name__)

@add_customer_bp.route('/add_customer', methods=['GET', 'POST'])
@admin_required
def add_customer():

    form = AddCustomerForm(request.form)
    
    if form.validate_on_submit():
        
        username = form.username.data
        password = form.password.data
        email = form.email.data
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        
        # Check if a user with the given username or email already exists
        existing_user = Users.query.filter((Users.username == username) | (Users.email == email)).first()

        if existing_user:
            
            flash('User with given username or email already exists.', 'error')
            return render_template('user_exist.html')
        else:
            # Create a new user and add it to the database
            
            role = form.role.data
            country = form.country.data
            email = form.email.data
            phone_number = form.phone_number.data

            new_user = Users(username=username, password_hash=password_hash, role=role, email=email, phone_number=phone_number, country=country)
            db.session.add(new_user)
            db.session.commit()

            flash('User added successfully.', 'success')
            return redirect(url_for('admin_dashboard_cm'))
        
    else:
        flash('User has not been added, check the correctness of the data', 'danger')
        return redirect(url_for('admin_dashboard_cm'))
        
    