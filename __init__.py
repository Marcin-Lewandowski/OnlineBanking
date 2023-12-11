# YourApp/__init__.py


# Dodaj tutaj konfiguracje, inicjalizacje, itp.

# Przykładowa konfiguracja dla SQLAlchemy
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'

# Importuj i zarejestruj moduły, np. routes, forms, itp.
'''
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Ustaw klucz CSRF, zmień na coś bardziej bezpiecznego
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'
db = SQLAlchemy(app)
csrf = CSRFProtect(app)

'''


#from .routes import *
