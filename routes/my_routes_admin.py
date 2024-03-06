from flask import Blueprint, flash, url_for, redirect
from flask_login import current_user, login_required
from forms.forms import DeleteUserForm, LockUser, EditUserForm
from datetime import timedelta
from models.models import Users, Transaction, db, SupportTickets, LockedUsers, Loans
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
    """
    Renders a transaction management page with functionality to filter transactions based on various criteria.

    On a POST request it filters transactions based on the specified criteria, including user ID, date range, and transaction type.
    The function requires the user to be logged in and have administrative privileges to access and perform the filtering.

    The filtering criteria are provided through form inputs and include:
    - User ID: Filters transactions for a specific user.
    - Date range (From and Until): Filters transactions within the specified date range.
    - Transaction type: Filters transactions of a specific type.

    After applying the filters, the function renders the transaction management page, displaying the filtered results
    alongside all transactions for comparison and review.

    Returns:
        render_template: The 'transaction_management.html' template populated with the filtered transactions.
    """
    
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

        return render_template('transaction_management.html', transactions=transactions)

    return render_template('transaction_management.html')





def count_log_levels(file_path):
    """
    Counts the occurrences of different log levels in a log file.

    This function reads a log file specified by `file_path` and counts the occurrences of log levels such as INFO,
    ERROR, WARNING, and CRITICAL within the file. It returns a dictionary with the log levels as keys and the counts
    as values.

    Parameters:
    - file_path (str): The path to the log file to be analyzed.

    Returns:
    - dict: A dictionary with keys corresponding to the log levels ("INFO", "ERROR", "WARNING", "CRITICAL") and
      integer values representing the number of times each log level appears in the file.

    Example:
    If the log file contains two INFO messages, one ERROR message, and one WARNING message, the function will return:
    {"INFO": 2, "ERROR": 1, "WARNING": 1, "CRITICAL": 0}

    Note:
    The function assumes that each line in the log file contains at most one log level. It does not count multiple
    occurrences of log levels within a single line. The search for log level strings is case-sensitive.
    """
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
    """
    Converts a matplotlib plot to an HTML image tag with a base64-encoded PNG image.

    This function takes a matplotlib plot object, saves it as a PNG image to a bytes buffer, then encodes the image
    to a base64 string. This string is embedded into an HTML image tag, allowing the plot to be displayed directly
    in web browsers or any HTML-supporting environment without needing a separate file.

    Parameters:
    - plt (matplotlib.pyplot): The plot object created using matplotlib that needs to be converted.

    Returns:
    - str: An HTML image tag containing the base64-encoded PNG image of the plot.

    Note:
    - This function requires the `io` and `base64` modules to be imported.
    - It's important to call plt.close() after using this function to release memory if you're generating many plots.
    """
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
    """
    Generates a comprehensive report and statistics for various aspects of the system, including user roles, nationalities,
    support ticket priorities, transaction types, average transaction values, response times for support tickets,
    priority counts for support tickets, log levels, and loan types. It visualizes this data using pie charts and bar charts,
    converting them into HTML images for easy display in a web interface.

    This function queries the database for specific data sets, processes and analyzes the data using Pandas, and then
    visualizes the results using Matplotlib. The visualizations are converted to HTML images that can be directly embedded
    in the web page rendered by Flask. Additionally, the function calculates average response times for support tickets
    and categorizes support tickets by priority, preparing all necessary information for display on the reports and statistics page.

    Operations performed:
    1. Queries and visualizes the distribution of user roles.
    2. Queries and visualizes the distribution of user nationalities.
    3. Queries and visualizes the distribution of support ticket priorities based on unique reference numbers.
    4. Queries and visualizes the distribution of transaction types.
    5. Calculates and visualizes the average transaction value for each transaction type.
    6. Calculates the average response time between the first and second records for unique support ticket reference numbers.
    7. Counts and prepares support tickets by priority level for display.
    8. Counts the occurrences of different log levels in a log file and visualizes this distribution.
    9. Queries and visualizes the distribution of loan types.

    The results of these operations are passed to the 'reports_and_statistics.html' template, along with additional data
    like average response time, priority counts, log counts, and visualizations as context variables for rendering.

    Returns:
    - render_template: Renders the 'reports_and_statistics.html' template with context variables including
      charts (as HTML images), average response time, counts of support tickets by priority, log counts, and more.

    Requires:
    - Flask login_required and admin_required decorators to ensure that only logged-in and authorized (admin) users
      can access this function.
    - SQLAlchemy for database queries.
    - Pandas for data processing and analysis.
    - Matplotlib for data visualization.
    """
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
    
    
    
    
    
    
    # Retrieving data about loan types
    loan_types_count = Loans.query.with_entities(Loans.product_id, func.count(Loans.product_id)).group_by(Loans.product_id).all()
    
    # Creating dataframe
    loan_types_df = pd.DataFrame(loan_types_count, columns = ['Loan type', 'Count'])
    
    # Create a pie chart
    fig, ax = plt.subplots(figsize=(6, 3)) 
    ax.pie(loan_types_df['Count'], labels = loan_types_df['Loan type'], autopct='%1.1f%%', startangle=140)
    ax.set_title('Distribution of loan types in the system')

    
    ax.set_facecolor('black')
    fig.patch.set_facecolor('lightgrey')
    
    # Convert chart to HTML img
    chart7 = plot_to_html_img(plt)
    
    
    return render_template('reports_and_statistics.html', chart1 = chart1, chart2 = chart2, chart3 = chart3, chart4=chart4, chart5=chart5, average_response_time=average_response_time, 
                           normal_count = normal_count, high_count = high_count, urgent_count = urgent_count, total_count=total_count, log_counts = log_counts, chart6 = chart6, chart7=chart7)
    
    
    
    
   
    
delete_user_bp = Blueprint('delete_user_bp', __name__)    
    
@delete_user_bp.route('/delete_user', methods=['GET', 'POST'])
@login_required
@admin_required
def delete_user():
    """
    Facilitates the deletion of a user account from the system by an admin.

    This route allows an administrator to delete a user account from the database. 
    The function uses a form (DeleteUserForm) to capture the username of the
    user to be deleted. If the form is submitted and valid, the function attempts to find the user in the database.
    If the user is found, they are deleted from the database, and a success message is flashed. If the user is not found,
    an error message is flashed.

    Before proceeding with the deletion process, the function checks if the current user has an admin role. If not,
    it flashes a permission error message and redirects to the index page.

    Parameters:
    - None

    Returns:
    - render_template: Renders the 'admin_dashboard_cm.html' template on GET requests or unsuccessful POST requests.
      On successful deletion, redirects to 'admin_dashboard_cm' route.

    Requires:
    - A Flask login_required decorator to ensure that only logged-in users can access this function.
    - An admin_required decorator to ensure that only users with an admin role can delete user accounts.
    - The DeleteUserForm to capture the username of the user to be deleted.
    """
    all_users = Users.query.all()
    

    form = DeleteUserForm()
    if form.validate_on_submit():
        username = form.username.data
        user_to_delete = Users.query.filter_by(username=username).first()

        if user_to_delete:
            try:
                db.session.delete(user_to_delete)
                db.session.commit()
                flash('The user has been successfully deleted.', 'success')
            except Exception as e:
                db.session.rollback()
                print(f'Error deleting user: {e}')
                flash('An error occurred. The user could not be deleted.', 'danger')
        else:
            flash('User not found.', 'danger')

        return redirect(url_for('admin_dashboard_cm'))

    return render_template('admin_dashboard_cm.html', form=form, all_users=all_users)
    
    
    
    
update_customer_information_bp = Blueprint('update_customer_information_bp', __name__)
    
@update_customer_information_bp.route('/update_customer_information/<username>', methods=['GET', 'POST'])
@login_required
@admin_required
def update_customer_information(username):
    """
    This route handler facilitates the process of updating a customer's profile information, such as email, phone number,
    and country. It first queries the database for the user with the specified username. If the user exists, an
    EditUserForm is presented, allowing an admin to submit updated information.

    On form submission (POST request) and successful validation, the user's information in the database is updated
    with the form data. The function then flashes a message indicating the successful update and re-renders the
    'edit_customer_information.html' template with the updated user information.

    If the form is not submitted or validation fails, the function prints form errors to the console (for debugging
    purposes) and renders the 'edit_customer_information.html' template with the existing user information, allowing
    for corrections and resubmission.

    Parameters:
    - username (str): The username of the customer whose information is to be updated.

    Returns:
    - render_template: On a GET request or if form validation fails, renders the 'edit_customer_information.html' template
      with the user's current information. On a successful POST request (form submission and validation), re-renders
      the same template with updated information and a success message.

    Requires:
    - A Flask login_required decorator to ensure that only logged-in users can access this function.
    - An admin_required decorator to ensure that only users with an admin role can update customer information.
    - The EditUserForm for capturing and validating the updated customer information.
    """
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
    """
    Searches and filters support tickets based on their priority.

    This function is accessible to administrators and allows them to find support tickets by priority. Upon receiving
    a POST request, it captures the 'priority' value from the form submitted. It then constructs a subquery to find
    the latest created_at date for each support ticket's reference number, allowing it to identify the most recent
    tickets.

    An external query then joins the subquery to retrieve full records of the latest tickets, optionally filtering
    them by the priority specified in the form. The tickets are ordered by priority, with 'urgent' tickets shown first,
    followed by 'high' and then all other tickets.

    Parameters:
    - None explicitly; however, the function processes 'priority' from POST request form data to filter the tickets.

    Returns:
    - render_template: Renders the 'communication_with_clients_sorting.html' template. On a POST request, it passes
      the filtered and ordered tickets to the template. On a GET request or if no priority is specified, it may render
      the template without passing any tickets, depending on the implementation details.

    Requires:
    - Flask login_required decorator to ensure that only logged-in users can access this route.
    - admin_required decorator to restrict the functionality to users with admin privileges.
    """
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
    """
    Blocks a user account based on the provided username.

    This route is accessible only to logged-in administrators. It allows an
    administrator to block a user's access to the system by adding them to the
    list of locked users. The process is triggered by submitting a form with the
    username of the user to be blocked. If the user exists and is not already
    locked, their account will be locked, and a success message will be flashed.
    If the user does not exist or is already locked, an appropriate error message
    will be displayed instead.

    Upon successful submission and action, the page displays a list of all
    currently locked users. If accessed via a GET request, it simply displays
    the form to submit a username for locking.

    Returns:
        A rendered template of the admin dashboard, either with the form for
        blocking a user or the list of all locked users, depending on the
        form submission and action results.
    """
    form = LockUser()
    
    if form.validate_on_submit():
        # Check if a user with the given name exists
        user_exists = Users.query.filter_by(username=form.username.data).first()
        if user_exists:
            is_user_locked = LockedUsers.query.filter_by(username = user_exists.username).first()
            if is_user_locked:
                flash('User account for: ' + is_user_locked.username + '  is already locked!', 'error')
            else:
                
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
    """
    Unlocks a previously locked user account based on the username provided in the URL.

    This route is accessible only to logged-in administrators. It facilitates an
    administrator in unlocking a user's access to the system by removing them from
    the list of locked users. The action is initiated either through a GET or POST
    request, where the username of the user to be unlocked is specified in the URL.

    If the specified user is found in the list of locked users, their account is
    unlocked, and a success message is flashed. If the user is not found in the
    locked users list (either because they were never locked or have already been
    unlocked), an error message is displayed.

    After the operation, whether successful or not, the page displays a list of all
    currently locked users, allowing the administrator to manage other locked
    accounts easily.

    Args:
        username (str): The username of the user to be unlocked, provided in the URL.

    Returns:
        A rendered template of the admin dashboard, with the list of all currently
        locked users, updated to reflect the result of the unlock operation.
    """
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
    """
    Displays the admin dashboard with statistics on users and support tickets.

    Accessible only to logged-in users with an admin role, this route presents
    a comprehensive overview of the application's current state from an
    administrative perspective. It includes the total number of users, the count
    of locked users, and a breakdown of support tickets by priority levels (normal,
    high, urgent).

    The function first verifies the role of the current user to ensure they have
    admin privileges. It then aggregates data from the Users and LockedUsers models
    to provide counts of all users and locked users, respectively.

    Additionally, it groups and counts support tickets by their priority, assigning
    these counts to separate variables for normal, high, and urgent priority tickets.
    This data is used to inform the admin about the volume and nature of support
    queries being handled.

    If the user attempting to access this route does not have admin privileges, an
    error is logged, and they are prevented from accessing the dashboard information.

    Returns:
        A rendered template ('admin_dashboard.html') that displays the admin
        dashboard, populated with the aggregate data on users and support tickets.
        The template includes the total count of users, locked users, and a
        breakdown of support tickets by their priority levels.
    """
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
    """
    Filters and displays logs based on the selected log level from a web form.

    This route is accessible only to logged-in administrators and provides
    functionality for filtering application logs by severity level (CRITICAL, ERROR,
    WARNING, INFO). The user selects a log level via a POST request through a form
    on the 'safety_settings.html' page. The selected log level is used to filter
    log entries from a specified log file ('app.log').

    The function reads the log file line by line, expecting each line to be in the
    format: '%(asctime)s - %(levelname)s - %(message)s'. It then filters the logs
    to include only those that match the selected level. The filtered log entries
    are stored in a list of dictionaries, each dictionary representing a single
    log entry with 'date', 'level', and 'message' keys.

    After filtering, it uses pandas to create a DataFrame from the list of log
    entries. This DataFrame is then passed to the 'safety_settings.html' template
    as a list of dictionaries via the 'all_logs' variable, allowing for display
    of the filtered log data in the web interface.

    If the request is of type GET, the page will simply display the form without
    any filtered log results. This allows administrators to select a log level for
    filtering each time they access the page.

    Args:
        None

    Returns:
        A rendered template ('safety_settings.html') that displays either the form
        for selecting a log level (on GET request) or the results of the log
        filtering (on POST request), based on the selected log level.
    """
    if request.method == 'POST':
        selected_level = request.form['level'].upper()

        # List for storing log data
        logs_data = []

        # Read logs from file
        log_file_path = 'app.log'
        with open(log_file_path, 'r') as file:
            for line in file:
                # Log's format: '%(asctime)s - %(levelname)s - %(message)s'
                parts = line.strip().split(' - ', 2)
                if len(parts) == 3:
                    date, level, message = parts
                    if level.upper() == selected_level:
                        # We add data to the list
                        logs_data.append({'date': date, 'level': level, 'message': message})

        # Creating a DataFrame from filtered data
        logs_df = pd.DataFrame(logs_data)

        # Transferring filtered logs to the template
        return render_template('safety_settings.html', all_logs=logs_df.to_dict('records'))
    else:
        # If the request is of type GET, just display the form without the results
        return render_template('safety_settings.html')
    
    
    
cwc_bp = Blueprint('cwc_bp', __name__)    
    
@cwc_bp.route('/communication_with_clients', methods=['GET', 'POST'])
@login_required
@admin_required
def cwc():
    """
    Retrieves and displays support ticket information for communication with clients.

    This route, accessible only to logged-in administrators, provides a view for
    managing communications with clients through support tickets. It displays all
    support tickets and specifically highlights the latest tickets based on the
    unique reference number for each ticket thread.

    The function performs two main queries:
    1. Retrieves all support tickets to be displayed.
    2. Utilizes a subquery to identify the latest date for each reference number,
       allowing the identification of the most recent ticket in each thread. This
       is achieved by grouping tickets by their reference number and selecting the
       maximum creation date. An external query then joins this subquery to retrieve
       full records of the latest tickets.

    The results of these queries are passed to the 'communication_with_clients.html'
    template. This setup allows administrators to view all tickets and specifically
    focus on the latest updates in ongoing conversations with clients.

    The latest tickets are ordered by priority, ensuring that urgent tickets are
    addressed first, followed by high and then lower priority tickets. This ordering
    is achieved using the SQL `CASE` statement within the order_by clause.

    Args:
        None

    Returns:
        A rendered template ('communication_with_clients.html') that displays both
        all queries and the latest tickets, facilitating effective communication
        management with clients by the administration team.
    """
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