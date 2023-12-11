Struktura Katalogów:

your_app/ (Nazwij ten folder zgodnie z nazwą Twojej aplikacji)
static/: Katalog zawierający pliki statyczne, takie jak arkusze stylów CSS, pliki JavaScript, obrazy itp.
-- styles.css
templates/: Katalog zawierający szablony HTML.
-- base.html
-- index.html (strona główna)
-- login.html (strona logowania)
-- register.html (strona rejestracji)
-- dashboard.html (strona główna klienta)
-- transfer.html (strona do przesyłania środków)
-- transactions_history.html (strona historii transakcji)
-- admin_dashboard.html (strona administracyjna)
forms/: Katalog zawierający definicje formularzy Flask-WTF.
-- forms.py
models/: Katalog zawierający definicje modeli bazy danych SQLAlchemy.
-- models.py
config.py: Plik z ustawieniami konfiguracyjnymi aplikacji.
app.py: Plik zawierający instancję aplikacji i logikę routingu.
init.py: Pusty plik, który informuje Pythona, że ten katalog powinien być traktowany jako pakiet.