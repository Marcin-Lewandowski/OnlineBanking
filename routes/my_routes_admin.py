from flask import Blueprint, flash, url_for, redirect
from flask_login import current_user, login_required
from forms.forms import DeleteUserForm, LockUser, EditUserForm
from datetime import timedelta
from models.models import Users, Transaction, db, SupportTickets, LockedUsers
from sqlalchemy import func, and_, case, asc
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from routes.transfer import admin_required, logger
from flask import render_template, request



transactions_filter_bp = Blueprint('transactions_filter_bp', __name__)

@transactions_filter_bp.route('/transactions_filter', methods=['GET', 'POST'])
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

        # Filtering by user ID
        if user_id:
            query = query.filter(Transaction.user_id == user_id)

        # Filter by date range
        if date_from:
            query = query.filter(Transaction.transaction_date >= date_from)
        if date_until:
            query = query.filter(Transaction.transaction_date <= date_until)

        # Filtering by transaction type if other than 'all' is selected
        if transaction_type and transaction_type != 'all':
            query = query.filter(Transaction.transaction_type == transaction_type)

        # Results
        transactions = query.all()

        return render_template('transaction_management.html', transactions=transactions, all_transactions=all_transactions)

    return render_template('transaction_management.html', transactions=transactions)




# A function that counts how many logs of a given level are saved in the log file
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



def plot_to_html_img(plt):
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8').replace('\n', '')
    buf.close()

    return f'<img src="data:image/png;base64,{image_base64}"/>'




reports_and_statistics_bp = Blueprint('reports_and_statistics_bp', __name__)

@reports_and_statistics_bp.route('/reports_and_statistics', methods=['GET', 'POST'])
@login_required
@admin_required
def reports_and_statistics():
    
    # Downloading data about user roles
    roles_count = Users.query.with_entities(Users.role, func.count(Users.role)).group_by(Users.role).all()

    # Creting DataFrame
    roles_df = pd.DataFrame(roles_count, columns=['Role', 'Count'])

    # Create a pie chart
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.pie(roles_df['Count'], labels=roles_df['Role'], autopct='%1.1f%%', startangle=140)
    ax.set_title('Distribution of user roles in the system')

    # Changing the background color
    ax.set_facecolor('black')
    # Changing the background color of the figure
    fig.patch.set_facecolor('lightgrey')
    
    # Convert chart to HTML img
    chart1 = plot_to_html_img(plt)
    
    
    
    
    # Retrieving data about user nationalities
    countries_count = Users.query.with_entities(Users.country, func.count(Users.country)).group_by(Users.country).all()
    
    #Creating dataframe
    countries_df = pd.DataFrame(countries_count, columns = ['Country', 'Count'])
    
    # Create a pie chart
    fig, ax = plt.subplots(figsize=(4, 3)) 
    ax.pie(countries_df['Count'], labels=countries_df['Country'], autopct='%1.1f%%', startangle=140)
    ax.set_title('Distribution of user nationalities in the system')

    
    ax.set_facecolor('black') 
    fig.patch.set_facecolor('lightgrey')  
    
    # Convert chart to HTML img
    chart2 = plot_to_html_img(plt)
    
    
    # Subquery to extract unique reference numbers with their priorities
    # Podzapytanie do wyodrębnienia unikalnych numerów referencyjnych z ich priorytetami
    subquery = (db.session.query(SupportTickets.reference_number, SupportTickets.priority)
                .distinct(SupportTickets.reference_number)
                .subquery())
    
    # Master Query - Priority grouping and counting based on unique reference numbers
    # Zapytanie główne - grupowanie i zliczanie priorytetów na podstawie unikalnych numerów referencyjnych
    tickets_count = (db.session.query(subquery.c.priority, func.count(subquery.c.priority))
                    .group_by(subquery.c.priority)
                    .all())

    tickets_df = pd.DataFrame(tickets_count, columns=['Priority', 'Count'])

    fig, ax = plt.subplots(figsize=(7, 3))
    ax.pie(tickets_df['Count'], labels=tickets_df['Priority'], autopct='%1.1f%%', startangle=140)
    ax.set_title('Distribution of the number of messages with a specific priority in the system')
    ax.set_facecolor('black')
    fig.patch.set_facecolor('lightgrey')

    chart3 = plot_to_html_img(plt)
    
    
    
    
    
    # Retrieving data about transaction types
    transaction_types_count = Transaction.query.with_entities(Transaction.transaction_type, func.count(Transaction.transaction_type)).group_by(Transaction.transaction_type).all()
    
    # Creating dataframe
    transaction_types_df = pd.DataFrame(transaction_types_count, columns = ['Transaction type', 'Count'])
    
    # Create a pie chart
    fig, ax = plt.subplots(figsize=(6, 3)) 
    ax.pie(transaction_types_df['Count'], labels=transaction_types_df['Transaction type'], autopct='%1.1f%%', startangle=140)
    ax.set_title('Distribution of transaction types in the transaction system')

    
    ax.set_facecolor('black')
    fig.patch.set_facecolor('lightgrey')
    
    # Convert chart to HTML img
    chart4 = plot_to_html_img(plt)
    
    
    
    
    
    
    # A query to calculate the average transaction value for each type
    avg_transactions = (db.session.query(Transaction.transaction_type,func.avg(Transaction.debit_amount + Transaction.credit_amount).label('average_value'))
                    .filter((Transaction.debit_amount + Transaction.credit_amount) <= 10000).group_by(Transaction.transaction_type).all())

    # Creating DataFrame from result
    transactions_df = pd.DataFrame(avg_transactions, columns=['TransactionType', 'AverageValue'])

    # Create a bar chart
    fig, ax = plt.subplots(figsize=(8, 6))
    transactions_df.plot(kind='bar', x='TransactionType', y='AverageValue', ax=ax, color='skyblue')

    ax.set_title('Average Transaction Value for Each Transaction Type')
    ax.set_xlabel('Transaction type')
    ax.set_ylabel('Average value')
    plt.xticks(rotation=45)
    
    # Adding numeric values in a chart
    for bar in ax.patches:
        ax.annotate(format(bar.get_height(), '.2f'), 
                (bar.get_x() + bar.get_width() / 2, 
                    bar.get_height()), ha='center', va='center',
                size=10, xytext=(0, 8),
                textcoords='offset points')
    
    # Convert chart to HTML img
    chart5 = plot_to_html_img(plt)
    
    
    
    
    
    
    response_times = []
    
    # Find unique reference numbers
    unique_reference_numbers = (SupportTickets.query.with_entities(SupportTickets.reference_number).distinct().all())

    # Print the number of unique reference numbers
    print(f"Number of unique reference numbers: {len(unique_reference_numbers)}")

    # View reference numbers
    for ref_number in unique_reference_numbers:
        print(ref_number[0])

        dates = (db.session.query(SupportTickets.created_at)
            .filter(SupportTickets.reference_number == ref_number[0])  
            .order_by(asc(SupportTickets.created_at))
            .limit(2)  # Limited to the first two records
            .all())
        
        

        # Time difference calculation
        if len(dates) == 2:
            first_record, second_record = dates[0][0], dates[1][0]  
            time_difference = second_record - first_record
            response_times.append(time_difference)
            print("The time elapsed between records:", time_difference)
        else:
            print("Not enough records found.")
    
    if response_times:
        total_time = sum(response_times, timedelta())  # Timedelta summation
        average_time_seconds = total_time.total_seconds() / len(response_times)  # Average time in seconds

        # Calculation of hours and minutes
        hours, remainder = divmod(average_time_seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        # Display of average time in hours and minutes
        print("Average response time: {} hours {} minutes".format(int(hours), int(minutes)))
    else:
        print("Not enough records were found to calculate the average response time.")
    
    
    if response_times:
        average_time_seconds = total_time.total_seconds() / len(response_times)
        hours, remainder = divmod(average_time_seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        average_response_time = "{} hours {} minutes".format(int(hours), int(minutes))
    else:
        average_response_time = "Brak danych"
    
    
    
    # Group messages by priority and count them
    priority_counts = (SupportTickets.query
                       .with_entities(SupportTickets.priority, func.count(SupportTickets.reference_number.distinct()))
                       .group_by(SupportTickets.priority)
                       .all())

    # Initialization of variables for each priority
    normal_count = high_count = urgent_count = 0

    # Assigning results to appropriate variables
    for priority, count in priority_counts:
        if priority == 'normal':
            normal_count = count
        elif priority == 'high':
            high_count = count
        elif priority == 'urgent':
            urgent_count = count
    total_count = normal_count + high_count + urgent_count
    
    
    
    
    
    
    
    
    # Path to your log file
    log_file_path = 'app.log'
    
    # Calling the log counting function
    log_counts = count_log_levels(log_file_path)
    
    
    # Creating a DataFrame for the log graph in the app.log file
    
    log_counts_df = pd.DataFrame(list(log_counts.items()), columns=['Log Level', 'Count'])

    # Pie chart
    fig, ax = plt.subplots(figsize=(6, 3))  # Utworzenie figury i osi
    ax.pie(log_counts_df['Count'], labels=log_counts_df['Log Level'], autopct='%1.1f%%', startangle=140)
    ax.set_title('Distribution of log types in the system')

    ax.set_facecolor('black')  
    fig.patch.set_facecolor('lightgrey')  

    chart6 = plot_to_html_img(plt)
    
    
    return render_template('reports_and_statistics.html', chart1 = chart1, chart2 = chart2, chart3 = chart3, chart4=chart4, chart5=chart5, average_response_time=average_response_time, 
                           normal_count = normal_count, high_count = high_count, urgent_count = urgent_count, total_count=total_count, log_counts = log_counts, chart6 = chart6)
    
    
    
    
   
    
delete_user_bp = Blueprint('delete_user_bp', __name__)    
    
@delete_user_bp.route('/delete_user', methods=['GET', 'POST'])
@login_required
@admin_required
def delete_user():
    all_users = Users.query.all()
    if current_user.role != 'admin':
        flash('You do not have permission to perform this operation.', 'danger')
        return redirect(url_for('index'))

    form = DeleteUserForm()
    if form.validate_on_submit():
        username = form.username.data
        user_to_delete = Users.query.filter_by(username=username).first()

        if user_to_delete:
            db.session.delete(user_to_delete)
            db.session.commit()
            flash('The user has been successfully deleted.', 'success')
        else:
            flash('User not found.', 'danger')

        return redirect(url_for('admin_dashboard_cm'))

    return render_template('admin_dashboard_cm.html', form=form, all_users=all_users)
    
    
update_customer_information_bp = Blueprint('update_customer_information_bp', __name__)
    
@update_customer_information_bp.route('/update_customer_information/<username>', methods=['GET', 'POST'])
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



find_tickets_bp = Blueprint('find_tickets_bp', __name__)

@find_tickets_bp.route('/find_tickets', methods=['GET', 'POST'])
@login_required
@admin_required
def find_tickets():
    if request.method == 'POST':
        priority = request.form.get('priority')
        
        # A subquery to find the latest date for each reference number
        # Podzapytanie do znalezienia najnowszej daty dla każdego reference_number
        subquery = (db.session.query(SupportTickets.reference_number,
                                     func.max(SupportTickets.created_at).label('latest_date'))
                              .group_by(SupportTickets.reference_number)
                              .subquery())
        
        # External query to retrieve full records
        # Zewnętrzne zapytanie do pobrania pełnych rekordów
        query = (db.session.query(SupportTickets)
                            .join(subquery, and_(SupportTickets.reference_number == subquery.c.reference_number,
                                                 SupportTickets.created_at == subquery.c.latest_date)))
        # Filtration by priority
        if priority:
            query = query.filter(SupportTickets.priority == priority)

        query = query.order_by(case((SupportTickets.priority == 'urgent', 1),
                                    (SupportTickets.priority == 'high', 2),
                                    else_=3))
        tickets = query.all()
        return render_template('communication_with_clients_sorting.html', tickets=tickets)
       
    return render_template('communication_with_clients_sorting.html')



block_customer_bp = Blueprint('block_customer_bp', __name__)

@block_customer_bp.route('/block_customer', methods=['GET', 'POST'])
@login_required
@admin_required
def block_customer():
    form = LockUser()
    
    if form.validate_on_submit():
        # Check if a user with the given name exists
        user_exists = Users.query.filter_by(username=form.username.data).first()
        if user_exists:
            user_for_lock = LockedUsers(username=form.username.data)
            
            db.session.add(user_for_lock)
            db.session.commit()

            flash('User account for: ' + user_for_lock.username + '  locked successfully!', 'success')
        else:
            flash('User account: ' + form.username.data + ' does not exist!', 'error')

        # Download the current list of blocked users
        all_locked_users = LockedUsers.query.all()
        return render_template('admin_dashboard_cam.html', all_locked_users=all_locked_users)

    return render_template('admin_dashboard_cam.html', form=form)



unlock_access_bp = Blueprint('unlock_access_bp', __name__)

@unlock_access_bp.route('/unlock_access/<username>', methods=['GET', 'POST'])  
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



admin_dashboard_bp = Blueprint('admin_dashboard_bp', __name__)

@admin_dashboard_bp.route('/admin_dashboard', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_dashboard():
    user = current_user
    if user.role != 'admin':
        logger.error(f"No access to the protected resource - /admin_dashboard  '{user.username}' ")
        
    all_users = Users.query.count()
    locked_users = LockedUsers.query.count()
    
    # Group messages by priority and count them
    priority_counts = (SupportTickets.query
                       .with_entities(SupportTickets.priority, func.count(SupportTickets.reference_number.distinct()))
                       .group_by(SupportTickets.priority)
                       .all())

    # Initialization of variables for each priority
    normal_count = high_count = urgent_count = 0

    # Assigning results to appropriate variables
    for priority, count in priority_counts:
        if priority == 'normal':
            normal_count = count
        elif priority == 'high':
            high_count = count
        elif priority == 'urgent':
            urgent_count = count
    
    # Render template by passing data
    return render_template('admin_dashboard.html', users = all_users, locked_users = locked_users, normal_count=normal_count, high_count=high_count, urgent_count=urgent_count)



logs_filtering_bp = Blueprint('logs_filtering_bp', __name__)

@logs_filtering_bp.route('/logs_filtering', methods=['GET', 'POST'])
@login_required
@admin_required
def logs_filtering():
    if request.method == 'POST':
        selected_level = request.form['level'].upper()

        # Lista do przechowywania danych logów
        logs_data = []

        # Odczytaj logi z pliku
        log_file_path = 'app.log'
        with open(log_file_path, 'r') as file:
            for line in file:
                # Załóżmy, że logi są w formacie: '%(asctime)s - %(levelname)s - %(message)s'
                parts = line.strip().split(' - ', 2)
                if len(parts) == 3:
                    date, level, message = parts
                    if level.upper() == selected_level:
                        # Dodajemy dane do listy
                        logs_data.append({'date': date, 'level': level, 'message': message})

        # Tworzenie DataFrame z przefiltrowanych danych
        logs_df = pd.DataFrame(logs_data)

        # Przekazanie przefiltrowanych logów do szablonu
        return render_template('safety_settings.html', all_logs=logs_df.to_dict('records'))
    else:
        # Jeśli żądanie jest typu GET, po prostu wyświetl formularz bez wyników
        return render_template('safety_settings.html')