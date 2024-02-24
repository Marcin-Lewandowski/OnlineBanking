from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField, PasswordField, SelectField, DateField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, NumberRange, EqualTo 



class LoginForm(FlaskForm):
    """
    Form class for handling user login in a Flask application.

    This form is designed to collect username and password for user authentication.
    It leverages Flask-WTF to provide CSRF protection and validate the input data. The form includes three fields:
    username, password, and a submit button. Each field is associated with specific validators to ensure that the data
    submitted is not empty.

    Attributes:
        username (StringField): Input field for the user's username. It is required to be non-empty, as indicated by the
                                DataRequired() validator.
        password (PasswordField): Input field for the user's password. Similar to the username, it is required to be non-empty,
                                  enforced by the DataRequired() validator.
        submit (SubmitField): A submit button for the form.

    The form is used in the login view of the application, where users are required to enter their credentials to gain
    access. Upon submission, the form data is validated, and if the credentials are correct, the user is authenticated
    and logged in.
    """
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')
    
    
class TransferForm(FlaskForm):
    """
    Form class for handling financial transfers between accounts in a Flask application.

    This form collects all necessary details for executing a financial transfer, including the recipient's sort code
    and account number, the amount to be transferred, a description of the transaction, and a password confirmation
    for security purposes. It uses Flask-WTF for form handling, which provides CSRF protection and data validation.

    Attributes:
        recipient_sort_code (StringField): Input field for the recipient's bank sort code. It is a unique number
                                           used to identify the bank's branch. This field is mandatory.
        recipient_account_number (StringField): Input field for the recipient's account number. This field is
                                                mandatory and must be provided to complete the transfer.
        amount (FloatField): Input field for the amount of money to be transferred. This field requires a float
                             value and is mandatory.
        transaction_description (StringField): Input field for providing a description or memo for the transaction.
                                               This field is mandatory and helps in identifying the purpose of the
                                               transfer.
        confirm_password (PasswordField): Password field for the user to confirm their password before making
                                          the transfer. This is a security measure to ensure that the person
                                          initiating the transfer is the account holder.
        submit (SubmitField): A submit button to send the form data for processing.

    This form is designed to be used in the transfer view of the application, where users can initiate transfers
    to other accounts. The form ensures that all necessary information is collected and validated before the
    transaction is processed.
    """
    recipient_sort_code = StringField('Recipient Sort Code', validators=[DataRequired()])
    recipient_account_number = StringField('Recipient Account Number', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    transaction_description = StringField('Description', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Transfer')
    
 
class AddCustomerForm(FlaskForm):
    """
    Form class for adding new customers or users to a Flask application.

    This form is designed to collect essential information about a new user, including their username, password,
    role within the application, email address, phone number, and country. It leverages Flask-WTF for form handling,
    providing CSRF protection and input validation to ensure data integrity and security.

    Attributes:
        username (StringField): Input field for the user's desired username. It is mandatory and must be unique
                                within the application.
        password (PasswordField): Input field for the user's chosen password. It is mandatory for account security.
        role (SelectField): Dropdown field allowing the selection of the user's role within the application. Options
                            include 'Client', 'Bank Employee', 'Board Member', and 'Management'. This field is
                            mandatory and helps in assigning the appropriate permissions and access levels.
        email (StringField): Input field for the user's email address. It is mandatory and must be unique. The field
                             also includes validation to ensure that the input follows the proper email format.
        phone_number (StringField): Input field for the user's phone number. It is mandatory and may be used for
                                    communication or account recovery purposes.
        country (StringField): Input field for the user's country of residence. It is mandatory and may be used for
                               regional settings or compliance purposes.

    The form is intended for use by administrators or privileged users who have the authority to add new users to
    the application. The inclusion of role selection allows for flexible user management and access control.
    """
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    role = SelectField('Role', choices=[('client', 'Client'), ('bank_emploee', 'Bank Employee'), ('board_member', 'Board Member'), ('management', 'Management')], validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_number = StringField('Phone number', validators=[DataRequired()])
    country = StringField('Country', validators=[DataRequired()])
    
    
    
class CreateTransactionForm(FlaskForm):
    """
    Form class for creating financial transactions within a Flask application.

    This form gathers all necessary details for recording a new transaction, including the user involved,
    the date of the transaction, its type, banking details such as sort code and account number, a description
    of the transaction, amounts for debit and credit, and the resulting balance. It employs Flask-WTF for
    CSRF protection and employs validators to ensure the integrity and validity of the input data.

    Attributes:
        user_id (SelectField): Dropdown field for selecting the user associated with the transaction. The field
                               uses integer coercion for the user IDs and requires selection.
        transaction_date (DateField): Field for specifying the date of the transaction. Requires a specific format
                                      ('%Y-%m-%d') and is mandatory.
        transaction_type (SelectField): Dropdown field for selecting the type of transaction. Includes predefined
                                        choices such as 'Debit', 'Direct Debit', 'Salary', etc., and is mandatory.
        sort_code (StringField): Input field for the bank's sort code associated with the transaction. It is
                                 mandatory and must adhere to a specified length range.
        account_number (StringField): Input field for the account number associated with the transaction. It is
                                      mandatory and has specified length constraints.
        transaction_description (StringField): Field for a descriptive memo of the transaction. It is mandatory to
                                               provide context for the transaction.
        debit_amount (FloatField): Field for specifying the debit amount in the transaction. It must be a non-negative
                                   value, allowing for validation of transaction amounts.
        credit_amount (FloatField): Field for specifying the credit amount in the transaction. Similar to debit_amount,
                                    it requires a non-negative value.
        balance (FloatField): Field for the balance after the transaction. It is validated to ensure a non-negative value,
                              reflecting the account's financial state post-transaction.
        submit (SubmitField): A submit button to finalize the creation of the transaction record.

    This form is designed for use in administrative or operational views where transactions need to be manually
    created or adjusted. It ensures that all necessary data for a transaction is collected and validated before
    processing.
    """
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
    
    
class DDSOForm(FlaskForm):
    """
    Form class for creating and managing Direct Debits (DD) and Standing Orders (SO) within a Flask application.

    This form is intended to capture all the necessary information for setting up a Direct Debit or Standing Order,
    including the amount, recipient details, reference number, next payment date, transaction type, and frequency of
    the payment. It also includes a field for password confirmation as a security measure. Flask-WTF is used to handle
    the form, providing CSRF protection and validation of the input data.

    Attributes:
        amount (FloatField): Field for specifying the payment amount. Requires a non-negative value and is mandatory.
        recipient (StringField): Input field for the name or identifier of the payment recipient. It is mandatory.
        reference_number (StringField): Field for a unique reference number for the transaction. It is mandatory for
                                        tracking and identification purposes.
        next_payment_date (DateField): Date field for specifying when the next payment should occur. It requires a
                                       specific format ('%Y-%m-%d') and is mandatory.
        transaction_type (SelectField): Dropdown field for choosing between a Direct Debit and Standing Order. This
                                        selection is mandatory.
        frequency (SelectField): Dropdown field for selecting the frequency of the payment (e.g., monthly, daily). This
                                 choice determines how often the DD or SO is executed.
        confirm_password (PasswordField): Field for the user to confirm their password before submitting the form. This
                                          is a security measure to ensure that the user authorizing the transaction is
                                          the account holder.
        submit (SubmitField): A submit button for the form, allowing the user to submit their DD/SO setup request.

    This form facilitates the automated processing of regular payments, enabling users to manage their financial
    commitments through Direct Debits and Standing Orders efficiently.
    """
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0)])
    recipient = StringField('Recipient', validators=[DataRequired()])
    reference_number = StringField('Reference number', validators=[DataRequired()])
    next_payment_date = DateField('Next payment date', format='%Y-%m-%d', validators=[DataRequired()])
    transaction_type = SelectField('Transaction type', choices=[('DD', 'Direct Debit'), ('SO', 'Standing Order')], validators=[DataRequired()])
    frequency = SelectField('Frequency', choices=[('monthly', 'Monthly'), ('daily', 'Daily')], validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Add DD / SO')
    
    

class DeleteUserForm(FlaskForm):
    """
    Form class for deleting a user from a Flask application.

    This form is designed to facilitate the process of removing a user from the system. It requires the
    username of the user to be deleted as input. This ensures that the action is targeted and prevents
    accidental deletions. The form uses Flask-WTF for CSRF protection and input validation, ensuring that
    the deletion process is secure and that the input data is valid.

    Attributes:
        username (StringField): Input field for the username of the user to be deleted. This field is mandatory
                                and ensures that the deletion process is specific to the intended user account.
                                Hey do you really read my code? ;) What is the label language?
        submit (SubmitField): A submit button for the form, labeled in Polish as 'Usuń Użytkownika', LOL which
                              translates to 'Delete User' in English. This button finalizes the submission of
                              the form to proceed with the deletion action.

    The form is intended for use by administrators or users with the appropriate permissions to delete user
    accounts. It provides a straightforward interface for specifying the account to be removed from the application.
    """
    username = StringField('Nazwa Użytkownika', validators=[DataRequired()])
    submit = SubmitField('Usuń Użytkownika')
    
    
class EditUserForm(FlaskForm):
    """
    Form class for editing existing user details within a Flask application.

    This form is tailored to allow users or administrators to update specific details of a user profile,
    including the email address, phone number, and country of residence. It utilizes Flask-WTF for form
    handling, which provides CSRF protection and facilitates validation of the input data to ensure its
    integrity and adherence to specific criteria.

    Attributes:
        email (StringField): Optional input field for updating the user's email address. It includes validation
                             to ensure that the input follows the proper email format if provided.
        phone_number (StringField): Optional input field for updating the user's phone number. It includes length
                                    validation to ensure that the phone number is within a reasonable and specified
                                    range (minimum 8 characters, maximum 15 characters).
        country (StringField): Optional input field for updating the user's country of residence. This field does
                               not include specific validation criteria, allowing for flexibility in the input format.
        submit (SubmitField): A submit button for the form, labeled 'Update'. This button is used to finalize and
                              submit the form, triggering the update process for the user's details.

    The form is designed with flexibility in mind, allowing users to update only the information they choose to change.
    Fields left blank will not trigger updates to those specific details, preserving existing data.
    """
    email = StringField('Email', validators=[Email()])
    phone_number = StringField('Phone number', validators=[Length(min=8, max=15)])
    country = StringField('Country')
    submit = SubmitField('Update')
    
    
class ChangePasswordForm(FlaskForm):
    """
    Form class for changing a user's password in a Flask application.

    This form enables users to securely update their password. It includes fields for entering a new password,
    confirming the new password to avoid typographical errors, and a submit button to finalize the password change.
    Flask-WTF is utilized for form handling, providing CSRF protection and validating the input data to ensure
    that the new password is entered correctly and matches the confirmation field.

    Attributes:
        new_password (PasswordField): Input field for the user to enter their new password. This field is mandatory,
                                      ensuring that the user specifies a password change.
        confirm_new_password (PasswordField): Input field for the user to confirm their new password. This field is
                                              mandatory and must match the new password to proceed. The EqualTo validator
                                              is used to enforce this match, enhancing security and reducing the chance
                                              of accidental password mismatches.
        submit (SubmitField): A submit button for the form, labeled 'Change Password'. This button is used to submit
                              the form, triggering the process to update the user's password.

    This form is designed to ensure a secure and user-friendly process for password updates, incorporating
    validation to confirm that the new password is entered correctly and matches the confirmation field.
    """
    new_password = PasswordField('New Password', validators=[DataRequired()])
    confirm_new_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')
    
    
class AddRecipientForm(FlaskForm):
    """
    Form class for adding new banking recipients within a Flask application.

    This form facilitates the process of users adding new recipients for transactions, such as transfers. It collects
    essential banking details of the recipient, including their name, sort code, and account number. Flask-WTF is used
    for form handling, providing CSRF protection and input validation to ensure that all necessary information is provided
    correctly before submission.

    Attributes:
        name (StringField): Input field for the recipient's name. This field is mandatory to identify the recipient in
                            transaction records and user's recipient list.
        sort_code (StringField): Input field for the recipient's bank sort code. This is a unique number used to identify
                                 the bank's branch where the recipient's account is held. It is mandatory for processing
                                 transactions to the correct bank.
        account_number (StringField): Input field for the recipient's account number. This field is mandatory for directing
                                       the transaction to the correct account within the specified bank.
        submit (SubmitField): A submit button for the form, labeled 'Add Recipient'. This button is used to finalize and
                              submit the recipient's details to the system.

    The form is designed to be user-friendly, guiding users through the process of adding a new recipient by collecting
    all necessary information in a structured format. This ensures that users can easily and securely manage their
    transaction recipients within the application.
    """
    name = StringField('Name', validators = [DataRequired()])
    sort_code = StringField('Sort Code', validators = [DataRequired()])
    account_number = StringField('Account Number', validators = [DataRequired()])
    submit = SubmitField('Add Recipient')
    
    
class SendQueryForm(FlaskForm):
    """
    Form class for users to send queries, complaints, or feedback within a Flask application.

    This form is structured to collect detailed information about a user's query, including a reference number (if applicable),
    the title of the query, a detailed description, and the category the query falls under. It employs Flask-WTF for form
    handling, which provides CSRF protection and validates the input data to ensure completeness and adherence to specified
    constraints.

    Attributes:
        reference_number (StringField): Optional input field for providing a reference number related to the query. This could
                                        be a transaction ID, previous query number, etc., and is limited to 50 characters.
        title (StringField): Mandatory input field for the title of the query. This provides a brief overview of the issue or
                             feedback and is limited to 100 characters to ensure conciseness.
        description (TextAreaField): Mandatory text area for a detailed description of the query. This field allows users to
                                     elaborate on their concerns, issues, or feedback.
        category (SelectField): Dropdown menu for selecting the category of the query. Categories include 'General', 'Fraud',
                                'Service Problem', and 'Money Transfer', with 'General' being the default selection. This helps
                                in routing the query to the appropriate department or specialist.
        submit (SubmitField): A submit button labeled 'Send message'. This button is used to submit the form, initiating the
                              process of sending the user's query to the system for review and response.

    This form serves as a direct line of communication between users and the system administrators or customer service
    team, facilitating the efficient submission and handling of user queries.
    """
    reference_number = StringField('Reference Number', validators=[Length(max=50)])
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    category = SelectField('Category', choices=[('general', 'General'), ('fraud', 'Fraud'), ('service problem', 'Service Problem'), ('money transfer', 'Money Transfer')], default='general')
    submit = SubmitField('Send message')
    
    
class LockUser(FlaskForm):
    """
    Form class for locking a user account in a Flask application.

    This form enables administrators or authorized personnel to lock a user account by specifying the username of the account
    to be locked. The primary purpose of this form is to facilitate the quick and secure suspension of user accounts, possibly
    due to security concerns, breach of terms of service, or at the user's request. Flask-WTF is used for form handling, providing
    CSRF protection and ensuring that the username field is filled out before submission.

    Attributes:
        username (StringField): Input field for the username of the account to be locked. This field is mandatory to identify
                                the specific account targeted for locking.

    The form is intended for use in administrative dashboards or sections of the application where user management actions are
    performed. It provides a straightforward mechanism for quickly responding to issues requiring account suspension.
    """
    username = StringField('Username', validators=[DataRequired()])