import sys
import sqlite3
import hashlib
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class PasswordHasher:
    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(password, hashed):
        return hashlib.sha256(password.encode()).hexdigest() == hashed

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('autoservice.db')
        self.cursor = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                full_name TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                last_name TEXT NOT NULL,
                first_name TEXT NOT NULL,
                middle_name TEXT,
                phone TEXT,
                email TEXT,
                address TEXT,
                created_date TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS cars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                brand TEXT NOT NULL,
                model TEXT NOT NULL,
                year INTEGER,
                vin TEXT UNIQUE,
                license_plate TEXT UNIQUE,
                color TEXT,
                mileage INTEGER,
                FOREIGN KEY (client_id) REFERENCES clients (id)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                last_name TEXT NOT NULL,
                first_name TEXT NOT NULL,
                middle_name TEXT,
                position TEXT,
                phone TEXT,
                email TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                name TEXT NOT NULL,
                price REAL,
                duration INTEGER,
                category TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS parts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                name TEXT NOT NULL,
                price REAL,
                quantity INTEGER DEFAULT 0,
                min_quantity INTEGER DEFAULT 5,
                supplier TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT UNIQUE,
                client_id INTEGER,
                car_id INTEGER,
                employee_id INTEGER,
                created_date TEXT,
                status TEXT,
                total_cost REAL,
                payment_status TEXT,
                notes TEXT,
                FOREIGN KEY (client_id) REFERENCES clients (id),
                FOREIGN KEY (car_id) REFERENCES cars (id),
                FOREIGN KEY (employee_id) REFERENCES employees (id)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                service_id INTEGER,
                quantity INTEGER DEFAULT 1,
                price REAL,
                FOREIGN KEY (order_id) REFERENCES orders (id),
                FOREIGN KEY (service_id) REFERENCES services (id)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_parts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                part_id INTEGER,
                quantity INTEGER DEFAULT 1,
                price REAL,
                FOREIGN KEY (order_id) REFERENCES orders (id),
                FOREIGN KEY (part_id) REFERENCES parts (id)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS parts_movement (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                part_id INTEGER,
                type TEXT,
                quantity INTEGER,
                date TEXT,
                order_id INTEGER,
                notes TEXT,
                FOREIGN KEY (part_id) REFERENCES parts (id),
                FOREIGN KEY (order_id) REFERENCES orders (id)
            )
        ''')
        
        self.conn.commit()
        self.create_default_admin()
    
    def create_default_admin(self):
        admin = self.fetch_one("SELECT * FROM users WHERE username = 'admin'")
        if not admin:
            hashed = PasswordHasher.hash_password('admin123')
            self.execute_query('''
                INSERT INTO users (username, password, role, full_name)
                VALUES (?, ?, ?, ?)
            ''', ('admin', hashed, 'admin', 'Главный администратор'))
    
    def execute_query(self, query, params=()):
        self.cursor.execute(query, params)
        self.conn.commit()
        return self.cursor
    
    def fetch_all(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()
    
    def fetch_one(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

class LoginDialog(QDialog):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("АВТОСЕРВИС")
        self.setFixedSize(400, 500)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                font-family: 'Segoe UI', Arial;
            }
            QLabel {
                color: white;
                font-size: 14px;
            }
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.95);
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                color: #333;
            }
            QLineEdit:focus {
                background-color: white;
                border: 2px solid #ffd166;
            }
            QPushButton {
                background-color: #ffd166;
                color: #333;
                border: none;
                border-radius: 8px;
                padding: 14px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffc233;
            }
            QPushButton#registerBtn {
                background-color: #6c757d;
                color: white;
            }
            QPushButton#registerBtn:hover {
                background-color: #5a6268;
            }
        """)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 40, 30, 30)
        
        logo = QLabel("🚗 АВТОСЕРВИС")
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: white;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        """)
        layout.addWidget(logo)
        
        form = QFormLayout()
        form.setSpacing(15)
        form.setLabelAlignment(Qt.AlignRight)
        
        self.username = QLineEdit()
        self.username.setText("")
        self.username.setPlaceholderText("Введите логин")
        form.addRow("Логин:", self.username)
        
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setText("")
        self.password.setPlaceholderText("Введите пароль")
        form.addRow("Пароль:", self.password)
        
        layout.addLayout(form)
        
        layout.addStretch()
        
        self.login_btn = QPushButton("🚪 ВОЙТИ В СИСТЕМУ")
        self.login_btn.clicked.connect(self.check_login)
        layout.addWidget(self.login_btn)
        
        self.change_btn = QPushButton("🔄 СМЕНИТЬ ПАРОЛЬ")
        self.change_btn.setObjectName("registerBtn")
        self.change_btn.clicked.connect(self.change_password)
        layout.addWidget(self.change_btn)
        
        self.exit_btn = QPushButton("✖ ВЫХОД")
        self.exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        self.exit_btn.clicked.connect(self.reject)
        layout.addWidget(self.exit_btn)
        
        self.setLayout(layout)
    
    def check_login(self):
        username = self.username.text().strip()
        password = self.password.text()
        
        if not username or not password:
            self.show_error("Ошибка", "Введите логин и пароль")
            return
        
        user = self.db.fetch_one('''
            SELECT id, username, password, role, full_name 
            FROM users WHERE LOWER(username) = LOWER(?)
        ''', (username,))
        
        if user and PasswordHasher.verify_password(password, user[2]):
            self.user_data = {
                'id': user[0],
                'username': user[1],
                'role': user[3],
                'full_name': user[4]
            }
            self.accept()
        else:
            self.show_error("Ошибка", "Неверный логин или пароль")
    
    def show_register(self):
        dialog = RegisterDialog(self.db)
        if dialog.exec_():
            QMessageBox.information(self, "Успех", "Пользователь зарегистрирован. Теперь вы можете войти.")
    
    def change_password(self):
        dialog = ChangePasswordDialog(self.db)
        dialog.exec_()
    
    def show_error(self, title, message):
        QMessageBox.warning(self, title, message)

class RegisterDialog(QDialog):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Регистрация нового пользователя")
        self.setFixedSize(400, 500)
        self.setStyleSheet(LoginDialog.styleSheet(self))
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("📝 РЕГИСТРАЦИЯ НОВОГО ПОЛЬЗОВАТЕЛЯ")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: white; margin-bottom: 10px;")
        layout.addWidget(title)
        
        form = QFormLayout()
        form.setSpacing(15)
        form.setLabelAlignment(Qt.AlignRight)
        
        self.full_name = QLineEdit()
        self.full_name.setPlaceholderText("Иванов Иван Иванович")
        form.addRow("ФИО:*", self.full_name)
        
        self.username = QLineEdit()
        self.username.setPlaceholderText("ivanov")
        form.addRow("Логин:*", self.username)
        
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("******")
        form.addRow("Пароль:*", self.password)
        
        self.confirm = QLineEdit()
        self.confirm.setEchoMode(QLineEdit.Password)
        self.confirm.setPlaceholderText("******")
        form.addRow("Подтверждение:*", self.confirm)
        
        self.role = QComboBox()
        self.role.addItems(["manager", "admin"])
        form.addRow("Роль:", self.role)
        
        layout.addLayout(form)
        
        layout.addStretch()
        
        info = QLabel("Поля, отмеченные *, обязательны для заполнения")
        info.setStyleSheet("color: #ffd166; font-size: 10px;")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)
        
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("✅ ЗАРЕГИСТРИРОВАТЬ")
        save_btn.setObjectName("addBtn")
        save_btn.clicked.connect(self.register)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("✖ ОТМЕНА")
        cancel_btn.setStyleSheet("background-color: #dc3545; color: white;")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def register(self):
        full_name = self.full_name.text().strip()
        username = self.username.text().strip()
        password = self.password.text()
        confirm = self.confirm.text()
        role = self.role.currentText()
        
        if not all([full_name, username, password, confirm]):
            QMessageBox.warning(self, "Ошибка", "Заполните все обязательные поля")
            return
        
        if password != confirm:
            QMessageBox.warning(self, "Ошибка", "Пароли не совпадают")
            return
        
        existing = self.db.fetch_one("SELECT id FROM users WHERE LOWER(username) = LOWER(?)", (username,))
        if existing:
            QMessageBox.warning(self, "Ошибка", "Пользователь с таким логином уже существует")
            return
        
        hashed = PasswordHasher.hash_password(password)
        self.db.execute_query('''
            INSERT INTO users (username, password, role, full_name)
            VALUES (?, ?, ?, ?)
        ''', (username, hashed, role, full_name))
        
        QMessageBox.information(self, "Успех", "Пользователь успешно зарегистрирован")
        self.accept()

class ChangePasswordDialog(QDialog):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Смена пароля")
        self.setFixedSize(350, 400)
        self.setStyleSheet(LoginDialog.styleSheet(self))
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("🔄 СМЕНА ПАРОЛЯ")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        layout.addWidget(title)
        
        form = QFormLayout()
        form.setSpacing(15)
        form.setLabelAlignment(Qt.AlignRight)
        
        self.username = QLineEdit()
        self.username.setPlaceholderText("Введите логин")
        form.addRow("Логин:", self.username)
        
        self.old_pass = QLineEdit()
        self.old_pass.setEchoMode(QLineEdit.Password)
        self.old_pass.setPlaceholderText("Старый пароль")
        form.addRow("Старый пароль:", self.old_pass)
        
        self.new_pass = QLineEdit()
        self.new_pass.setEchoMode(QLineEdit.Password)
        self.new_pass.setPlaceholderText("Новый пароль")
        form.addRow("Новый пароль:", self.new_pass)
        
        self.confirm = QLineEdit()
        self.confirm.setEchoMode(QLineEdit.Password)
        self.confirm.setPlaceholderText("Подтверждение")
        form.addRow("Подтверждение:", self.confirm)
        
        layout.addLayout(form)
        
        layout.addStretch()
        
        info = QLabel("Все поля обязательны для заполнения")
        info.setStyleSheet("color: #ffd166; font-size: 10px;")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)
        
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("✅ СОХРАНИТЬ")
        save_btn.clicked.connect(self.save_password)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("✖ ОТМЕНА")
        cancel_btn.setStyleSheet("background-color: #dc3545; color: white;")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def save_password(self):
        username = self.username.text().strip()
        old = self.old_pass.text()
        new = self.new_pass.text()
        confirm = self.confirm.text()
        
        if not all([username, old, new, confirm]):
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return
        
        if new != confirm:
            QMessageBox.warning(self, "Ошибка", "Новые пароли не совпадают")
            return
        
        user = self.db.fetch_one('''
            SELECT id, password FROM users WHERE LOWER(username) = LOWER(?)
        ''', (username,))
        
        if not user:
            QMessageBox.warning(self, "Ошибка", "Пользователь не найден")
            return
        
        if not PasswordHasher.verify_password(old, user[1]):
            QMessageBox.warning(self, "Ошибка", "Неверный старый пароль")
            return
        
        hashed = PasswordHasher.hash_password(new)
        self.db.execute_query('UPDATE users SET password = ? WHERE id = ?', (hashed, user[0]))
        
        QMessageBox.information(self, "Успех", "Пароль успешно изменен")
        self.accept()

class MainWindow(QMainWindow):
    def __init__(self, db, user_data):
        super().__init__()
        self.db = db
        self.user_data = user_data
        self.setWindowTitle(f"АВТОСЕРВИС - {user_data['full_name']} ({'Администратор' if user_data['role'] == 'admin' else 'Менеджер'})")
        self.setGeometry(100, 100, 1300, 800)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QMenuBar {
                background-color: #2c3e50;
                color: #ecf0f1;
                font-size: 13px;
                padding: 5px;
            }
            QMenuBar::item {
                padding: 8px 15px;
                border-radius: 5px;
            }
            QMenuBar::item:selected {
                background-color: #3498db;
                color: white;
            }
            QMenu {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #34495e;
                border-radius: 5px;
            }
            QMenu::item {
                padding: 8px 25px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #3498db;
                color: white;
            }
            QToolBar {
                background-color: white;
                border-bottom: 2px solid #3498db;
                padding: 8px;
                spacing: 10px;
            }
            QToolButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 12px;
                font-weight: bold;
            }
            QToolButton:hover {
                background-color: #2980b9;
            }
            QStatusBar {
                background-color: #2c3e50;
                color: #ecf0f1;
                font-size: 12px;
                padding: 5px;
            }
            QTableWidget {
                background-color: white;
                alternate-background-color: #f8f9fa;
                selection-background-color: #3498db;
                selection-color: white;
                gridline-color: #dee2e6;
                font-size: 12px;
                border: none;
                border-radius: 8px;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #2c3e50;
                color: white;
                padding: 10px;
                font-size: 12px;
                font-weight: bold;
                border: none;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton#addBtn {
                background-color: #27ae60;
            }
            QPushButton#addBtn:hover {
                background-color: #229954;
            }
            QPushButton#deleteBtn {
                background-color: #e74c3c;
            }
            QPushButton#deleteBtn:hover {
                background-color: #c0392b;
            }
            QGroupBox {
                background-color: white;
                border: 2px solid #3498db;
                border-radius: 8px;
                margin-top: 15px;
                font-size: 13px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                color: #3498db;
            }
            QComboBox {
                border: 2px solid #dee2e6;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 12px;
                min-width: 150px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #3498db;
            }
            QLineEdit {
                border: 2px solid #dee2e6;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
            QTabWidget::pane {
                background-color: white;
                border: 2px solid #3498db;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #e9ecef;
                color: #495057;
                border: none;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                padding: 10px 20px;
                margin-right: 2px;
                font-size: 12px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #5faee3;
                color: white;
            }
        """)
        
        self.setup_menu()
        self.setup_toolbar()
        self.setup_statusbar()
        self.setup_central()
        self.show_table("clients")
    
    def setup_menu(self):
    
        menubar = self.menuBar()
        
        ref_menu = menubar.addMenu("📋 СПРАВОЧНИКИ")
        
        clients = QAction("👥 Клиенты", self)
        clients.triggered.connect(lambda: self.show_table("clients"))
        ref_menu.addAction(clients)
        
        cars = QAction("🚗 Автомобили", self)
        cars.triggered.connect(lambda: self.show_table("cars"))
        ref_menu.addAction(cars)
        
        employees = QAction("👤 Сотрудники", self)
        employees.triggered.connect(lambda: self.show_table("employees"))
        ref_menu.addAction(employees)
        
        ref_menu.addSeparator()
        
        services = QAction("🔧 Услуги", self)
        services.triggered.connect(lambda: self.show_table("services"))
        ref_menu.addAction(services)
        
        parts = QAction("⚙️ Запчасти", self)
        parts.triggered.connect(lambda: self.show_table("parts"))
        ref_menu.addAction(parts)
        
        orders_menu = menubar.addMenu("📦 ЗАКАЗЫ")
        
        new_order = QAction("➕ Новый заказ", self)
        new_order.triggered.connect(self.new_order)
        orders_menu.addAction(new_order)
        
        orders_list = QAction("📋 Журнал заказов", self)
        orders_list.triggered.connect(lambda: self.show_table("orders"))
        orders_menu.addAction(orders_list)
        
        stock_menu = menubar.addMenu("🏭 СКЛАД")
        
        stock = QAction("📊 Остатки", self)
        stock.triggered.connect(self.show_stock)
        stock_menu.addAction(stock)
        
        movement = QAction("📈 Движение", self)
        movement.triggered.connect(self.show_movement)
        stock_menu.addAction(movement)
        
        reports_menu = menubar.addMenu("📊 ОТЧЕТЫ")
        
        revenue = QAction("💰 Выручка", self)
        revenue.triggered.connect(self.revenue_report)
        reports_menu.addAction(revenue)
        
        services_report = QAction("🔧 Услуги", self)
        services_report.triggered.connect(self.services_report)
        reports_menu.addAction(services_report)
        
        if self.user_data['role'] == 'admin':
            admin_menu = menubar.addMenu("⚙️ АДМИНИСТРИРОВАНИЕ")
            
            users = QAction("👥 Пользователи", self)
            users.triggered.connect(self.manage_users)
            admin_menu.addAction(users)
        
        service_menu = menubar.addMenu("🔧 СЕРВИС")
        
        change_pass = QAction("🔄 Сменить пароль", self)
        change_pass.triggered.connect(self.change_password)
        service_menu.addAction(change_pass)
        
        service_menu.addSeparator()
        
        logout = QAction("🚪 Выход", self)
        logout.triggered.connect(self.logout)
        service_menu.addAction(logout)
        

        exit_action = QAction("✖ Завершение работы", self)
        exit_action.triggered.connect(lambda: sys.exit()) 
        service_menu.addAction(exit_action)
    
    def setup_toolbar(self):
        toolbar = self.addToolBar("Панель инструментов")
        toolbar.setMovable(False)
        
        add_client = QAction("➕ НОВЫЙ КЛИЕНТ", self)
        add_client.triggered.connect(lambda: self.add_record("clients"))
        toolbar.addAction(add_client)
        
        add_car = QAction("➕ НОВЫЙ АВТО", self)
        add_car.triggered.connect(lambda: self.add_record("cars"))
        toolbar.addAction(add_car)
        
        add_order = QAction("➕ НОВЫЙ ЗАКАЗ", self)
        add_order.triggered.connect(self.new_order)
        toolbar.addAction(add_order)
        
        toolbar.addSeparator()
        
        refresh = QAction("🔄 ОБНОВИТЬ", self)
        refresh.triggered.connect(lambda: self.show_table(self.current_table))
        toolbar.addAction(refresh)
        
        toolbar.addSeparator()
        
        logout_btn = QAction("🚪 ВЫЙТИ", self)
        logout_btn.triggered.connect(self.logout)
        toolbar.addAction(logout_btn)
    
    def setup_statusbar(self):
        status = self.statusBar()
        
        user_label = QLabel(f"👤 {self.user_data['full_name']} | Роль: {'Администратор' if self.user_data['role'] == 'admin' else 'Менеджер'}")
        status.addPermanentWidget(user_label)
        
        self.time_label = QLabel()
        self.update_time()
        status.addPermanentWidget(self.time_label)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
    
    def update_time(self):
        self.time_label.setText(f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    
    def setup_central(self):
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        self.title = QLabel("📋 СПРАВОЧНИК: КЛИЕНТЫ")
        self.title.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
            color: #2c3e50;
            background: white;
            padding: 15px;
            border-radius: 8px;
            border-left: 5px solid #3498db;
        """)
        layout.addWidget(self.title)
        
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)
        
        panel = QWidget()
        panel.setStyleSheet("background-color: white; border-radius: 8px; padding: 10px;")
        panel_layout = QHBoxLayout(panel)
        panel_layout.setSpacing(5)  # Уменьшил расстояние между кнопками
        
        self.add_btn = QPushButton("➕ ДОБАВИТЬ")
        self.add_btn.setObjectName("addBtn")
        self.add_btn.setFixedHeight(40)
        self.add_btn.setFixedWidth(120)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        self.add_btn.clicked.connect(lambda: self.add_record(self.current_table))
        panel_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("✏️ РЕДАКТИРОВАТЬ")
        self.edit_btn.setFixedHeight(40)
        self.edit_btn.setFixedWidth(140)
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.edit_btn.clicked.connect(self.edit_record)
        panel_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("🗑️ УДАЛИТЬ")
        self.delete_btn.setObjectName("deleteBtn")
        self.delete_btn.setFixedHeight(40)
        self.delete_btn.setFixedWidth(120)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.delete_btn.clicked.connect(self.delete_record)
        panel_layout.addWidget(self.delete_btn)
        
        panel_layout.addStretch()
        
        layout.addWidget(panel)
        

    def show_table(self, table_name):
        self.current_table = table_name
        
        titles = {
            "clients": "КЛИЕНТЫ",
            "cars": "АВТОМОБИЛИ",
            "employees": "СОТРУДНИКИ",
            "services": "УСЛУГИ",
            "parts": "ЗАПЧАСТИ",
            "orders": "ЗАКАЗЫ"
        }
        self.title.setText(f"📋 СПРАВОЧНИК: {titles.get(table_name, '')}")
        
        if table_name == "clients":
            data = self.db.fetch_all("SELECT id, last_name, first_name, middle_name, phone, email, address FROM clients")
            headers = ["ID", "Фамилия", "Имя", "Отчество", "Телефон", "Email", "Адрес"]
        elif table_name == "cars":
            data = self.db.fetch_all('''
                SELECT cars.id, cars.brand, cars.model, cars.license_plate, cars.vin,
                       clients.last_name || ' ' || clients.first_name, cars.color, cars.mileage
                FROM cars LEFT JOIN clients ON cars.client_id = clients.id
            ''')
            headers = ["ID", "Марка", "Модель", "Госномер", "VIN", "Владелец", "Цвет", "Пробег"]
        elif table_name == "employees":
            data = self.db.fetch_all("SELECT id, last_name, first_name, middle_name, position, phone, email FROM employees")
            headers = ["ID", "Фамилия", "Имя", "Отчество", "Должность", "Телефон", "Email"]
        elif table_name == "services":
            data = self.db.fetch_all("SELECT id, code, name, price, duration, category FROM services")
            headers = ["ID", "Код", "Услуга", "Цена", "Мин", "Категория"]
        elif table_name == "parts":
            data = self.db.fetch_all("SELECT id, code, name, price, quantity, min_quantity, supplier FROM parts")
            headers = ["ID", "Код", "Запчасть", "Цена", "Кол-во", "Мин", "Поставщик"]
        elif table_name == "orders":
            data = self.db.fetch_all('''
                SELECT orders.id, orders.order_number, clients.last_name,
                       orders.total_cost, orders.status, orders.payment_status,
                       orders.created_date
                FROM orders LEFT JOIN clients ON orders.client_id = clients.id
                ORDER BY orders.id DESC
            ''')
            headers = ["ID", "Номер", "Клиент", "Сумма", "Статус", "Оплата", "Дата"]
        else:
            return
        
        self.table.setRowCount(len(data))
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        for i, row in enumerate(data):
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value if value is not None else ""))
                if j == 0:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                if table_name == "parts" and j == 4 and value < row[5]:
                    item.setBackground(QColor(255, 230, 230))
                self.table.setItem(i, j, item)
        
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)


    def add_record(self, table_name):
        if table_name == "clients":
            dlg = ClientDialog(self.db)
        elif table_name == "cars":
            dlg = CarDialog(self.db)
        elif table_name == "employees":
            dlg = EmployeeDialog(self.db)
        elif table_name == "services":
            dlg = ServiceDialog(self.db)
        elif table_name == "parts":
            dlg = PartDialog(self.db)
        else:
            return
        
        if dlg.exec_():
            self.show_table(table_name)
    
    def edit_record(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для редактирования")
            return
        
        record_id = int(self.table.item(row, 0).text())
        
        if self.current_table == "clients":
            dlg = ClientDialog(self.db, record_id)
        elif self.current_table == "cars":
            dlg = CarDialog(self.db, record_id)
        elif self.current_table == "employees":
            dlg = EmployeeDialog(self.db, record_id)
        elif self.current_table == "services":
            dlg = ServiceDialog(self.db, record_id)
        elif self.current_table == "parts":
            dlg = PartDialog(self.db, record_id)
        elif self.current_table == "orders":
            dlg = OrderDialog(self.db, record_id)
        else:
            return
        
        if dlg.exec_():
            self.show_table(self.current_table)
    
    def delete_record(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для удаления")
            return
        
        record_id = int(self.table.item(row, 0).text())
        
        reply = QMessageBox.question(self, "Подтверждение", 
                                     "Вы уверены, что хотите удалить запись?",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                self.db.execute_query(f"DELETE FROM {self.current_table} WHERE id = ?", (record_id,))
                self.show_table(self.current_table)
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Нельзя удалить запись: {str(e)}")
    
    def change_password(self):
        dlg = ChangePasswordDialog(self.db)
        dlg.exec_()
    
    def logout(self):
        reply = QMessageBox.question(self, "Выход", "Вы уверены, что хотите выйти?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.close()
    
    def new_order(self):
        dlg = OrderDialog(self.db)
        if dlg.exec_():
            self.show_table("orders")
    
    def show_stock(self):
        data = self.db.fetch_all("SELECT code, name, quantity, min_quantity, price, supplier FROM parts ORDER BY name")
        
        dlg = QDialog(self)
        dlg.setWindowTitle("Остатки на складе")
        dlg.setGeometry(200, 200, 900, 600)
        dlg.setStyleSheet(self.styleSheet())
        
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("📊 ОСТАТКИ НА СКЛАДЕ")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50; padding: 10px;")
        layout.addWidget(title)
        
        table = QTableWidget()
        table.setRowCount(len(data))
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Код", "Наименование", "Кол-во", "Мин", "Цена", "Поставщик"])
        table.setAlternatingRowColors(True)
        
        for i, row in enumerate(data):
            for j, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                if j == 2 and val < row[3]:
                    item.setBackground(QColor(255, 230, 230))
                table.setItem(i, j, item)
        
        table.resizeColumnsToContents()
        layout.addWidget(table)
        
        btn = QPushButton("Закрыть")
        btn.setFixedWidth(150)
        btn.clicked.connect(dlg.accept)
        layout.addWidget(btn, alignment=Qt.AlignCenter)
        
        dlg.exec_()
    
    def show_movement(self):
        data = self.db.fetch_all('''
            SELECT parts_movement.date, parts.name, parts_movement.type, 
                   parts_movement.quantity, orders.order_number
            FROM parts_movement 
            JOIN parts ON parts_movement.part_id = parts.id
            LEFT JOIN orders ON parts_movement.order_id = orders.id
            ORDER BY parts_movement.date DESC LIMIT 100
        ''')
        
        dlg = QDialog(self)
        dlg.setWindowTitle("Движение товаров")
        dlg.setGeometry(200, 200, 900, 600)
        dlg.setStyleSheet(self.styleSheet())
        
        layout = QVBoxLayout(dlg)
        
        title = QLabel("📈 ДВИЖЕНИЕ ТОВАРОВ")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50; padding: 10px;")
        layout.addWidget(title)
        
        table = QTableWidget()
        table.setRowCount(len(data))
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Дата", "Товар", "Тип", "Кол-во", "Заказ"])
        table.setAlternatingRowColors(True)
        
        for i, row in enumerate(data):
            for j, val in enumerate(row):
                item = QTableWidgetItem(str(val if val is not None else ""))
                table.setItem(i, j, item)
        
        table.resizeColumnsToContents()
        layout.addWidget(table)
        
        btn = QPushButton("Закрыть")
        btn.setFixedWidth(150)
        btn.clicked.connect(dlg.accept)
        layout.addWidget(btn, alignment=Qt.AlignCenter)
        
        dlg.exec_()
    
    def revenue_report(self):
        data = self.db.fetch_all('''
            SELECT date(orders.created_date), orders.order_number, 
                   clients.last_name || ' ' || clients.first_name,
                   orders.total_cost
            FROM orders 
            LEFT JOIN clients ON orders.client_id = clients.id
            WHERE orders.payment_status = 'оплачен'
            ORDER BY orders.created_date DESC
        ''')
        
        dlg = QDialog(self)
        dlg.setWindowTitle("Отчет по выручке")
        dlg.setGeometry(200, 200, 800, 600)
        dlg.setStyleSheet(self.styleSheet())
        
        layout = QVBoxLayout(dlg)
        
        title = QLabel("💰 ОТЧЕТ ПО ВЫРУЧКЕ")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50; padding: 10px;")
        layout.addWidget(title)
        
        table = QTableWidget()
        table.setRowCount(len(data))
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Дата", "Номер", "Клиент", "Сумма"])
        table.setAlternatingRowColors(True)
        
        total = 0
        for i, row in enumerate(data):
            for j, val in enumerate(row):
                if j == 3:
                    item = QTableWidgetItem(f"{val:,.2f} ₽")
                    total += val
                else:
                    item = QTableWidgetItem(str(val))
                table.setItem(i, j, item)
        
        table.resizeColumnsToContents()
        layout.addWidget(table)
        
        total_label = QLabel(f"ИТОГО: {total:,.2f} ₽")
        total_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; padding: 10px;")
        layout.addWidget(total_label)
        
        btn = QPushButton("Закрыть")
        btn.setFixedWidth(150)
        btn.clicked.connect(dlg.accept)
        layout.addWidget(btn, alignment=Qt.AlignCenter)
        
        dlg.exec_()
    
    def services_report(self):
        data = self.db.fetch_all('''
            SELECT services.name, COUNT(*), SUM(order_services.price * order_services.quantity)
            FROM order_services
            JOIN services ON order_services.service_id = services.id
            GROUP BY services.id
            ORDER BY COUNT(*) DESC
        ''')
        
        dlg = QDialog(self)
        dlg.setWindowTitle("Отчет по услугам")
        dlg.setGeometry(200, 200, 700, 500)
        dlg.setStyleSheet(self.styleSheet())
        
        layout = QVBoxLayout(dlg)
        
        title = QLabel("🔧 ОТЧЕТ ПО УСЛУГАМ")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50; padding: 10px;")
        layout.addWidget(title)
        
        table = QTableWidget()
        table.setRowCount(len(data))
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Услуга", "Кол-во", "Сумма"])
        table.setAlternatingRowColors(True)
        
        for i, row in enumerate(data):
            table.setItem(i, 0, QTableWidgetItem(row[0]))
            table.setItem(i, 1, QTableWidgetItem(str(row[1])))
            table.setItem(i, 2, QTableWidgetItem(f"{row[2]:,.2f} ₽"))
        
        table.resizeColumnsToContents()
        layout.addWidget(table)
        
        btn = QPushButton("Закрыть")
        btn.setFixedWidth(150)
        btn.clicked.connect(dlg.accept)
        layout.addWidget(btn, alignment=Qt.AlignCenter)
        
        dlg.exec_()
    
    def manage_users(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Управление пользователями")
        dlg.setGeometry(200, 200, 700, 500)
        dlg.setStyleSheet(self.styleSheet())
        
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("👥 УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50; padding: 10px;")
        layout.addWidget(title)
        
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["ID", "Логин", "Роль", "ФИО"])
        table.setAlternatingRowColors(True)
        
        users = self.db.fetch_all("SELECT id, username, role, full_name FROM users")
        table.setRowCount(len(users))
        
        for i, user in enumerate(users):
            for j, val in enumerate(user):
                item = QTableWidgetItem(str(val if val is not None else ""))
                table.setItem(i, j, item)
        
        table.resizeColumnsToContents()
        layout.addWidget(table)
        
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ ДОБАВИТЬ ПОЛЬЗОВАТЕЛЯ")
        add_btn.setObjectName("addBtn")
        add_btn.clicked.connect(lambda: self.add_user(table))
        btn_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("✏️ РЕДАКТИРОВАТЬ")
        edit_btn.clicked.connect(lambda: self.edit_user(table))
        btn_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️ УДАЛИТЬ")
        delete_btn.setObjectName("deleteBtn")
        delete_btn.clicked.connect(lambda: self.delete_user(table))
        btn_layout.addWidget(delete_btn)
        
        layout.addLayout(btn_layout)
        
        close_btn = QPushButton("ЗАКРЫТЬ")
        close_btn.setFixedWidth(150)
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
        
        dlg.exec_()
    
    def add_user(self, table):
        dlg = RegisterDialog(self.db)
        if dlg.exec_():
            self.refresh_users_table(table)
    
    def edit_user(self, table):
        row = table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя")
            return
        
        user_id = int(table.item(row, 0).text())
        username = table.item(row, 1).text()
        role = table.item(row, 2).text()
        full_name = table.item(row, 3).text()
        
        dlg = QDialog(self)
        dlg.setWindowTitle("Редактирование пользователя")
        dlg.setFixedSize(400, 450)
        dlg.setStyleSheet(self.styleSheet())
        
        layout = QVBoxLayout(dlg)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("✏️ РЕДАКТИРОВАНИЕ ПОЛЬЗОВАТЕЛЯ")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #3498db; margin-bottom: 10px;")
        layout.addWidget(title)
        
        form = QFormLayout()
        form.setSpacing(15)
        form.setLabelAlignment(Qt.AlignRight)
        
        full_name_edit = QLineEdit()
        full_name_edit.setText(full_name)
        full_name_edit.setPlaceholderText("Иванов Иван Иванович")
        form.addRow("ФИО:*", full_name_edit)
        
        username_edit = QLineEdit()
        username_edit.setText(username)
        username_edit.setEnabled(False)
        form.addRow("Логин:", username_edit)
        
        role_combo = QComboBox()
        role_combo.addItems(["manager", "admin"])
        role_combo.setCurrentText(role)
        form.addRow("Роль:", role_combo)
        
        password = QLineEdit()
        password.setEchoMode(QLineEdit.Password)
        password.setPlaceholderText("Оставьте пустым, если не меняете")
        form.addRow("Новый пароль:", password)
        
        layout.addLayout(form)
        
        info = QLabel("Оставьте пароль пустым, если не хотите его менять")
        info.setStyleSheet("color: #6c757d; font-size: 10px;")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("✅ СОХРАНИТЬ")
        save_btn.clicked.connect(lambda: self.save_user_edit(dlg, user_id, full_name_edit.text(), role_combo.currentText(), password.text()))
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("✖ ОТМЕНА")
        cancel_btn.setStyleSheet("background-color: #e74c3c; color: white;")
        cancel_btn.clicked.connect(dlg.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        dlg.exec_()
    
    def save_user_edit(self, dlg, user_id, full_name, role, password):
        if not full_name:
            QMessageBox.warning(dlg, "Ошибка", "Введите ФИО")
            return
        
        if password:
            hashed = PasswordHasher.hash_password(password)
            self.db.execute_query('''
                UPDATE users SET full_name = ?, role = ?, password = ? WHERE id = ?
            ''', (full_name, role, hashed, user_id))
        else:
            self.db.execute_query('''
                UPDATE users SET full_name = ?, role = ? WHERE id = ?
            ''', (full_name, role, user_id))
        
        dlg.accept()
    
    def delete_user(self, table):
        row = table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя")
            return
        
        user_id = int(table.item(row, 0).text())
        username = table.item(row, 1).text()
        
        if username == 'admin':
            QMessageBox.warning(self, "Ошибка", "Нельзя удалить администратора")
            return
        
        reply = QMessageBox.question(self, "Подтверждение", 
                                     f"Удалить пользователя {username}?",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.db.execute_query("DELETE FROM users WHERE id = ?", (user_id,))
            self.refresh_users_table(table)
    
    def refresh_users_table(self, table):
        users = self.db.fetch_all("SELECT id, username, role, full_name FROM users")
        table.setRowCount(len(users))
        for i, user in enumerate(users):
            for j, val in enumerate(user):
                table.setItem(i, j, QTableWidgetItem(str(val if val is not None else "")))
        table.resizeColumnsToContents()

class ClientDialog(QDialog):
    def __init__(self, db, client_id=None):
        super().__init__()
        self.db = db
        self.client_id = client_id
        self.setWindowTitle("Клиент" if client_id else "Новый клиент")
        self.setFixedSize(450, 550)
        self.setStyleSheet(MainWindow.styleSheet(self))
        self.setup_ui()
        
        if client_id:
            self.load_data()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("👤 " + ("РЕДАКТИРОВАНИЕ КЛИЕНТА" if self.client_id else "НОВЫЙ КЛИЕНТ"))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #3498db; margin-bottom: 10px;")
        layout.addWidget(title)
        
        form = QFormLayout()
        form.setSpacing(15)
        form.setLabelAlignment(Qt.AlignRight)
        
        self.last_name = QLineEdit()
        self.last_name.setPlaceholderText("Иванов")
        form.addRow("Фамилия:*", self.last_name)
        
        self.first_name = QLineEdit()
        self.first_name.setPlaceholderText("Иван")
        form.addRow("Имя:*", self.first_name)
        
        self.middle_name = QLineEdit()
        self.middle_name.setPlaceholderText("Иванович")
        form.addRow("Отчество:", self.middle_name)
        
        self.phone = QLineEdit()
        self.phone.setPlaceholderText("+7 (999) 123-45-67")
        form.addRow("Телефон:*", self.phone)
        
        self.email = QLineEdit()
        self.email.setPlaceholderText("ivanov@mail.ru")
        form.addRow("Email:", self.email)
        
        self.address = QTextEdit()
        self.address.setMaximumHeight(80)
        self.address.setPlaceholderText("г. Москва, ул. Ленина, д. 1")
        form.addRow("Адрес:", self.address)
        
        layout.addLayout(form)
        
        layout.addStretch()
        
        info = QLabel("Поля, отмеченные *, обязательны для заполнения")
        info.setStyleSheet("color: #6c757d; font-size: 10px;")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)
        
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("✅ СОХРАНИТЬ")
        save_btn.setObjectName("addBtn")
        save_btn.clicked.connect(self.save)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("✖ ОТМЕНА")
        cancel_btn.setStyleSheet("background-color: #e74c3c; color: white;")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def load_data(self):
        data = self.db.fetch_one('''
            SELECT last_name, first_name, middle_name, phone, email, address 
            FROM clients WHERE id = ?
        ''', (self.client_id,))
        
        if data:
            self.last_name.setText(data[0])
            self.first_name.setText(data[1])
            self.middle_name.setText(data[2] or "")
            self.phone.setText(data[3] or "")
            self.email.setText(data[4] or "")
            self.address.setText(data[5] or "")
    
    def save(self):
        if not self.last_name.text() or not self.first_name.text() or not self.phone.text():
            QMessageBox.warning(self, "Ошибка", "Заполните обязательные поля")
            return
        
        if self.client_id:
            query = '''
                UPDATE clients 
                SET last_name=?, first_name=?, middle_name=?, phone=?, email=?, address=?
                WHERE id=?
            '''
            params = (self.last_name.text(), self.first_name.text(), self.middle_name.text(),
                     self.phone.text(), self.email.text(), self.address.toPlainText(), self.client_id)
        else:
            query = '''
                INSERT INTO clients (last_name, first_name, middle_name, phone, email, address, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            '''
            params = (self.last_name.text(), self.first_name.text(), self.middle_name.text(),
                     self.phone.text(), self.email.text(), self.address.toPlainText(),
                     datetime.now().strftime("%Y-%m-%d"))
        
        self.db.execute_query(query, params)
        self.accept()

class CarDialog(QDialog):
    def __init__(self, db, car_id=None):
        super().__init__()
        self.db = db
        self.car_id = car_id
        self.setWindowTitle("Автомобиль" if car_id else "Новый автомобиль")
        self.setFixedSize(500, 600)
        self.setStyleSheet(MainWindow.styleSheet(self))
        self.setup_ui()
        
        if car_id:
            self.load_data()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("🚗 " + ("РЕДАКТИРОВАНИЕ АВТОМОБИЛЯ" if self.car_id else "НОВЫЙ АВТОМОБИЛЬ"))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #3498db; margin-bottom: 10px;")
        layout.addWidget(title)
        
        form = QFormLayout()
        form.setSpacing(15)
        form.setLabelAlignment(Qt.AlignRight)
        
        self.client_combo = QComboBox()
        self.load_clients()
        form.addRow("Владелец:*", self.client_combo)
        
        self.brand = QLineEdit()
        self.brand.setPlaceholderText("Toyota")
        form.addRow("Марка:*", self.brand)
        
        self.model = QLineEdit()
        self.model.setPlaceholderText("Camry")
        form.addRow("Модель:*", self.model)
        
        self.year = QSpinBox()
        self.year.setRange(1900, datetime.now().year + 1)
        self.year.setValue(2020)
        form.addRow("Год выпуска:", self.year)
        
        self.vin = QLineEdit()
        self.vin.setPlaceholderText("VIN номер")
        form.addRow("VIN:", self.vin)
        
        self.license = QLineEdit()
        self.license.setPlaceholderText("А123ВС777")
        form.addRow("Госномер:*", self.license)
        
        self.color = QLineEdit()
        self.color.setPlaceholderText("Черный")
        form.addRow("Цвет:", self.color)
        
        self.mileage = QSpinBox()
        self.mileage.setRange(0, 999999)
        self.mileage.setSingleStep(1000)
        self.mileage.setSuffix(" км")
        form.addRow("Пробег:", self.mileage)
        
        layout.addLayout(form)
        
        layout.addStretch()
        
        info = QLabel("Поля, отмеченные *, обязательны для заполнения")
        info.setStyleSheet("color: #6c757d; font-size: 10px;")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)
        
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("✅ СОХРАНИТЬ")
        save_btn.setObjectName("addBtn")
        save_btn.clicked.connect(self.save)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("✖ ОТМЕНА")
        cancel_btn.setStyleSheet("background-color: #e74c3c; color: white;")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def load_clients(self):
        clients = self.db.fetch_all("SELECT id, last_name || ' ' || first_name || ' (' || phone || ')' FROM clients")
        self.client_combo.clear()
        self.client_combo.addItem("-- Выберите владельца --", None)
        for cid, name in clients:
            self.client_combo.addItem(name, cid)
    
    def load_data(self):
        data = self.db.fetch_one('''
            SELECT client_id, brand, model, year, vin, license_plate, color, mileage
            FROM cars WHERE id = ?
        ''', (self.car_id,))
        
        if data:
            idx = self.client_combo.findData(data[0])
            if idx >= 0:
                self.client_combo.setCurrentIndex(idx)
            self.brand.setText(data[1])
            self.model.setText(data[2])
            self.year.setValue(data[3] or 2020)
            self.vin.setText(data[4] or "")
            self.license.setText(data[5] or "")
            self.color.setText(data[6] or "")
            self.mileage.setValue(data[7] or 0)
    
    def save(self):
        if not self.brand.text() or not self.model.text() or not self.license.text():
            QMessageBox.warning(self, "Ошибка", "Заполните обязательные поля")
            return
        
        client_id = self.client_combo.currentData()
        if not client_id:
            QMessageBox.warning(self, "Ошибка", "Выберите владельца")
            return
        
        if self.car_id:
            query = '''
                UPDATE cars 
                SET client_id=?, brand=?, model=?, year=?, vin=?, license_plate=?, color=?, mileage=?
                WHERE id=?
            '''
            params = (client_id, self.brand.text(), self.model.text(), self.year.value(),
                     self.vin.text(), self.license.text(), self.color.text(),
                     self.mileage.value(), self.car_id)
        else:
            query = '''
                INSERT INTO cars (client_id, brand, model, year, vin, license_plate, color, mileage)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            '''
            params = (client_id, self.brand.text(), self.model.text(), self.year.value(),
                     self.vin.text(), self.license.text(), self.color.text(),
                     self.mileage.value())
        
        try:
            self.db.execute_query(query, params)
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", "Автомобиль с таким номером уже существует")

class EmployeeDialog(QDialog):
    def __init__(self, db, emp_id=None):
        super().__init__()
        self.db = db
        self.emp_id = emp_id
        self.setWindowTitle("Сотрудник" if emp_id else "Новый сотрудник")
        self.setFixedSize(450, 500)
        self.setStyleSheet(MainWindow.styleSheet(self))
        self.setup_ui()
        
        if emp_id:
            self.load_data()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("👤 " + ("РЕДАКТИРОВАНИЕ СОТРУДНИКА" if self.emp_id else "НОВЫЙ СОТРУДНИК"))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #3498db; margin-bottom: 10px;")
        layout.addWidget(title)
        
        form = QFormLayout()
        form.setSpacing(15)
        form.setLabelAlignment(Qt.AlignRight)
        
        self.last_name = QLineEdit()
        self.last_name.setPlaceholderText("Петров")
        form.addRow("Фамилия:*", self.last_name)
        
        self.first_name = QLineEdit()
        self.first_name.setPlaceholderText("Петр")
        form.addRow("Имя:*", self.first_name)
        
        self.middle_name = QLineEdit()
        self.middle_name.setPlaceholderText("Петрович")
        form.addRow("Отчество:", self.middle_name)
        
        self.position = QLineEdit()
        self.position.setPlaceholderText("Мастер")
        form.addRow("Должность:*", self.position)
        
        self.phone = QLineEdit()
        self.phone.setPlaceholderText("+7 (999) 123-45-67")
        form.addRow("Телефон:*", self.phone)
        
        self.email = QLineEdit()
        self.email.setPlaceholderText("petrov@autoservice.ru")
        form.addRow("Email:", self.email)
        
        layout.addLayout(form)
        
        layout.addStretch()
        
        info = QLabel("Поля, отмеченные *, обязательны для заполнения")
        info.setStyleSheet("color: #6c757d; font-size: 10px;")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)
        
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("✅ СОХРАНИТЬ")
        save_btn.setObjectName("addBtn")
        save_btn.clicked.connect(self.save)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("✖ ОТМЕНА")
        cancel_btn.setStyleSheet("background-color: #e74c3c; color: white;")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def load_data(self):
        data = self.db.fetch_one('''
            SELECT last_name, first_name, middle_name, position, phone, email
            FROM employees WHERE id = ?
        ''', (self.emp_id,))
        
        if data:
            self.last_name.setText(data[0])
            self.first_name.setText(data[1])
            self.middle_name.setText(data[2] or "")
            self.position.setText(data[3])
            self.phone.setText(data[4])
            self.email.setText(data[5] or "")
    
    def save(self):
        if not all([self.last_name.text(), self.first_name.text(), 
                   self.position.text(), self.phone.text()]):
            QMessageBox.warning(self, "Ошибка", "Заполните обязательные поля")
            return
        
        if self.emp_id:
            query = '''
                UPDATE employees 
                SET last_name=?, first_name=?, middle_name=?, position=?, phone=?, email=?
                WHERE id=?
            '''
            params = (self.last_name.text(), self.first_name.text(), self.middle_name.text(),
                     self.position.text(), self.phone.text(), self.email.text(), self.emp_id)
        else:
            query = '''
                INSERT INTO employees (last_name, first_name, middle_name, position, phone, email)
                VALUES (?, ?, ?, ?, ?, ?)
            '''
            params = (self.last_name.text(), self.first_name.text(), self.middle_name.text(),
                     self.position.text(), self.phone.text(), self.email.text())
        
        self.db.execute_query(query, params)
        self.accept()

class ServiceDialog(QDialog):
    def __init__(self, db, service_id=None):
        super().__init__()
        self.db = db
        self.service_id = service_id
        self.setWindowTitle("Услуга" if service_id else "Новая услуга")
        self.setFixedSize(450, 450)
        self.setStyleSheet(MainWindow.styleSheet(self))
        self.setup_ui()
        
        if service_id:
            self.load_data()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("🔧 " + ("РЕДАКТИРОВАНИЕ УСЛУГИ" if self.service_id else "НОВАЯ УСЛУГА"))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #3498db; margin-bottom: 10px;")
        layout.addWidget(title)
        
        form = QFormLayout()
        form.setSpacing(15)
        form.setLabelAlignment(Qt.AlignRight)
        
        self.code = QLineEdit()
        self.code.setPlaceholderText("S001")
        form.addRow("Код:", self.code)
        
        self.name = QLineEdit()
        self.name.setPlaceholderText("Замена масла")
        form.addRow("Название:", self.name)
        
        self.price = QDoubleSpinBox()
        self.price.setRange(0, 100000)
        self.price.setPrefix("₽ ")
        self.price.setValue(1000)
        form.addRow("Цена:", self.price)
        
        self.duration = QSpinBox()
        self.duration.setRange(0, 1000)
        self.duration.setSuffix(" мин")
        self.duration.setValue(60)
        form.addRow("Длительность:", self.duration)
        
        self.category = QLineEdit()
        self.category.setPlaceholderText("ТО")
        form.addRow("Категория:", self.category)
        
        layout.addLayout(form)
        
        layout.addStretch()
        
        info = QLabel("Поля, отмеченные , обязательны для заполнения")
        info.setStyleSheet("color: #6c757d; font-size: 10px;")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)
        
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("✅ СОХРАНИТЬ")
        save_btn.setObjectName("addBtn")
        save_btn.clicked.connect(self.save)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("✖ ОТМЕНА")
        cancel_btn.setStyleSheet("background-color: #e74c3c; color: white;")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def load_data(self):
        data = self.db.fetch_one('''
            SELECT code, name, price, duration, category
            FROM services WHERE id = ?
        ''', (self.service_id,))
        
        if data:
            self.code.setText(data[0])
            self.name.setText(data[1])
            self.price.setValue(data[2])
            self.duration.setValue(data[3] or 0)
            self.category.setText(data[4] or "")
    
    def save(self):
        if not self.code.text() or not self.name.text() or self.price.value() <= 0:
            QMessageBox.warning(self, "Ошибка", "Заполните обязательные поля")
            return
        
        if self.service_id:
            query = '''
                UPDATE services 
                SET code=?, name=?, price=?, duration=?, category=?
                WHERE id=?
            '''
            params = (self.code.text(), self.name.text(), self.price.value(),
                     self.duration.value(), self.category.text(), self.service_id)
        else:
            query = '''
                INSERT INTO services (code, name, price, duration, category)
                VALUES (?, ?, ?, ?, ?)
            '''
            params = (self.code.text(), self.name.text(), self.price.value(),
                     self.duration.value(), self.category.text())
        
        try:
            self.db.execute_query(query, params)
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", "Услуга с таким кодом уже существует")

class PartDialog(QDialog):
    def __init__(self, db, part_id=None):
        super().__init__()
        self.db = db
        self.part_id = part_id
        self.setWindowTitle("Запчасть" if part_id else "Новая запчасть")
        self.setFixedSize(450, 500)
        self.setStyleSheet(MainWindow.styleSheet(self))
        self.setup_ui()
        
        if part_id:
            self.load_data()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("⚙️ " + ("РЕДАКТИРОВАНИЕ ЗАПЧАСТИ" if self.part_id else "НОВАЯ ЗАПЧАСТЬ"))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #3498db; margin-bottom: 10px;")
        layout.addWidget(title)
        
        form = QFormLayout()
        form.setSpacing(15)
        form.setLabelAlignment(Qt.AlignRight)
        
        self.code = QLineEdit()
        self.code.setPlaceholderText("P001")
        form.addRow("Код:*", self.code)
        
        self.name = QLineEdit()
        self.name.setPlaceholderText("Масляный фильтр")
        form.addRow("Название:*", self.name)
        
        self.price = QDoubleSpinBox()
        self.price.setRange(0, 100000)
        self.price.setPrefix("₽ ")
        self.price.setValue(500)
        form.addRow("Цена:*", self.price)
        
        self.quantity = QSpinBox()
        self.quantity.setRange(0, 99999)
        self.quantity.setValue(10)
        form.addRow("Количество:", self.quantity)
        
        self.min_qty = QSpinBox()
        self.min_qty.setRange(0, 99999)
        self.min_qty.setValue(5)
        form.addRow("Мин. количество:", self.min_qty)
        
        self.supplier = QLineEdit()
        self.supplier.setPlaceholderText("ООО Автозапчасти")
        form.addRow("Поставщик:", self.supplier)
        
        layout.addLayout(form)
        
        layout.addStretch()
        
        info = QLabel("Поля, отмеченные , обязательны для заполнения")
        info.setStyleSheet("color: #6c757d; font-size: 10px;")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)
        
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("✅ СОХРАНИТЬ")
        save_btn.setObjectName("addBtn")
        save_btn.clicked.connect(self.save)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("✖ ОТМЕНА")
        cancel_btn.setStyleSheet("background-color: #e74c3c; color: white;")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def load_data(self):
        data = self.db.fetch_one('''
            SELECT code, name, price, quantity, min_quantity, supplier
            FROM parts WHERE id = ?
        ''', (self.part_id,))
        
        if data:
            self.code.setText(data[0])
            self.name.setText(data[1])
            self.price.setValue(data[2])
            self.quantity.setValue(data[3])
            self.min_qty.setValue(data[4])
            self.supplier.setText(data[5] or "")
    
    def save(self):
        if not self.code.text() or not self.name.text() or self.price.value() <= 0:
            QMessageBox.warning(self, "Ошибка", "Заполните обязательные поля")
            return
        
        if self.part_id:
            query = '''
                UPDATE parts 
                SET code=?, name=?, price=?, quantity=?, min_quantity=?, supplier=?
                WHERE id=?
            '''
            params = (self.code.text(), self.name.text(), self.price.value(),
                     self.quantity.value(), self.min_qty.value(), self.supplier.text(),
                     self.part_id)
        else:
            query = '''
                INSERT INTO parts (code, name, price, quantity, min_quantity, supplier)
                VALUES (?, ?, ?, ?, ?, ?)
            '''
            params = (self.code.text(), self.name.text(), self.price.value(),
                     self.quantity.value(), self.min_qty.value(), self.supplier.text())
        
        try:
            self.db.execute_query(query, params)
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", "Запчасть с таким кодом уже существует")

class OrderDialog(QDialog):
    def __init__(self, db, order_id=None):
        super().__init__()
        self.db = db
        self.order_id = order_id
        self.setWindowTitle("Заказ-наряд" if order_id else "Новый заказ-наряд")
        self.setGeometry(200, 200, 1000, 700)
        self.setStyleSheet(MainWindow.styleSheet(self))
        self.setup_ui()
        
        if order_id:
            self.load_order()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("📋 " + ("РЕДАКТИРОВАНИЕ ЗАКАЗА" if self.order_id else "НОВЫЙ ЗАКАЗ-НАРЯД"))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #3498db; margin-bottom: 10px;")
        layout.addWidget(title)
        
        info_group = QGroupBox("Информация о заказе")
        info_group.setStyleSheet("QGroupBox { font-weight: bold; color: #3498db; }")
        info_layout = QGridLayout(info_group)
        
        info_layout.addWidget(QLabel("Клиент:"), 0, 0)
        self.client_combo = QComboBox()
        self.client_combo.currentIndexChanged.connect(self.load_cars)
        info_layout.addWidget(self.client_combo, 0, 1)
        
        info_layout.addWidget(QLabel("Автомобиль:"), 0, 2)
        self.car_combo = QComboBox()
        info_layout.addWidget(self.car_combo, 0, 3)
        
        info_layout.addWidget(QLabel("Статус:"), 1, 2)
        self.status_combo = QComboBox()
        self.status_combo.addItems(["новый", "в работе", "готов", "закрыт"])
        info_layout.addWidget(self.status_combo, 1, 3)
        
        info_layout.addWidget(QLabel("Оплата:"), 2, 2)
        self.payment_combo = QComboBox()
        self.payment_combo.addItems(["не оплачен", "оплачен"])
        info_layout.addWidget(self.payment_combo, 2, 3)
        
        layout.addWidget(info_group)
        
        tabs = QTabWidget()
        
        services_tab = QWidget()
        services_layout = QVBoxLayout(services_tab)
        
        services_layout.addWidget(QLabel("🔧 Доступные услуги (нажмите ➕ для добавления):"))
        
        self.services_table = QTableWidget()
        self.services_table.setColumnCount(5)
        self.services_table.setHorizontalHeaderLabels(["ID", "Код", "Услуга", "Цена", ""])
        self.services_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.services_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.load_services()
        services_layout.addWidget(self.services_table)
        
        services_layout.addWidget(QLabel("✅ Выбранные услуги:"))
        self.selected_services = QTableWidget()
        self.selected_services.setColumnCount(5)
        self.selected_services.setHorizontalHeaderLabels(["ID", "Услуга", "Кол-во", "Цена", ""])
        self.selected_services.setSelectionBehavior(QTableWidget.SelectRows)
        self.selected_services.itemChanged.connect(self.calc_total)
        services_layout.addWidget(self.selected_services)
        
        tabs.addTab(services_tab, "🔧 Услуги")
        
        parts_tab = QWidget()
        parts_layout = QVBoxLayout(parts_tab)
        
        parts_layout.addWidget(QLabel("⚙️ Доступные запчасти (нажмите ➕ для добавления):"))
        
        self.parts_table = QTableWidget()
        self.parts_table.setColumnCount(6)
        self.parts_table.setHorizontalHeaderLabels(["ID", "Код", "Запчасть", "Цена", "В наличии", ""])
        self.parts_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.parts_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.load_parts()
        parts_layout.addWidget(self.parts_table)
        
        parts_layout.addWidget(QLabel("✅ Выбранные запчасти:"))
        self.selected_parts = QTableWidget()
        self.selected_parts.setColumnCount(5)
        self.selected_parts.setHorizontalHeaderLabels(["ID", "Запчасть", "Кол-во", "Цена", ""])
        self.selected_parts.setSelectionBehavior(QTableWidget.SelectRows)
        self.selected_parts.itemChanged.connect(self.calc_total)
        parts_layout.addWidget(self.selected_parts)
        
        tabs.addTab(parts_tab, "⚙️ Запчасти")
        
        layout.addWidget(tabs)
        
        total_widget = QWidget()
        total_widget.setStyleSheet("background-color: #2c3e50; color: white; border-radius: 8px; padding: 10px;")
        total_layout = QHBoxLayout(total_widget)
        total_layout.addStretch()
        total_layout.addWidget(QLabel("ИТОГО:"))
        self.total_label = QLabel("0.00 ₽")
        self.total_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffd166;")
        total_layout.addWidget(self.total_label)
        total_layout.addStretch()
        
        layout.addWidget(total_widget)
        
        notes_layout = QHBoxLayout()
        notes_layout.addWidget(QLabel("Примечание:"))
        self.notes = QLineEdit()
        self.notes.setPlaceholderText("Дополнительная информация по заказу")
        notes_layout.addWidget(self.notes)
        layout.addLayout(notes_layout)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        save_btn = QPushButton("✅ СОХРАНИТЬ ЗАКАЗ")
        save_btn.setObjectName("addBtn")
        save_btn.clicked.connect(self.save_order)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("✖ ОТМЕНА")
        cancel_btn.setStyleSheet("background-color: #e74c3c; color: white;")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
        self.load_clients()
    
    def load_clients(self):
        clients = self.db.fetch_all("SELECT id, last_name || ' ' || first_name FROM clients ORDER BY last_name")
        self.client_combo.clear()
        self.client_combo.addItem("-- Выберите клиента --", None)
        for cid, name in clients:
            self.client_combo.addItem(name, cid)
    
    def load_cars(self):
        self.car_combo.clear()
        client_id = self.client_combo.currentData()
        if client_id:
            cars = self.db.fetch_all("SELECT id, brand || ' ' || model || ' (' || license_plate || ')' FROM cars WHERE client_id = ?", (client_id,))
            self.car_combo.addItem("-- Выберите автомобиль --", None)
            for cid, name in cars:
                self.car_combo.addItem(name, cid)
        else:
            self.car_combo.addItem("-- Сначала выберите клиента --", None)
    
    def load_services(self):
        services = self.db.fetch_all("SELECT id, code, name, price FROM services ORDER BY name")
        self.services_table.setRowCount(len(services))
        for i, s in enumerate(services):
            self.services_table.setItem(i, 0, QTableWidgetItem(str(s[0])))
            self.services_table.setItem(i, 1, QTableWidgetItem(s[1]))
            self.services_table.setItem(i, 2, QTableWidgetItem(s[2]))
            self.services_table.setItem(i, 3, QTableWidgetItem(f"{s[3]:.2f} ₽"))
            
            add_btn = QPushButton("➕")
            add_btn.setFixedSize(30, 30)
            add_btn.clicked.connect(lambda checked, sid=s[0], name=s[2], price=s[3]: self.add_service(sid, name, price))
            self.services_table.setCellWidget(i, 4, add_btn)
        
        self.services_table.resizeColumnsToContents()
        self.services_table.setColumnWidth(4, 40)
    
    def load_parts(self):
        parts = self.db.fetch_all("SELECT id, code, name, price, quantity FROM parts WHERE quantity > 0 ORDER BY name")
        self.parts_table.setRowCount(len(parts))
        for i, p in enumerate(parts):
            self.parts_table.setItem(i, 0, QTableWidgetItem(str(p[0])))
            self.parts_table.setItem(i, 1, QTableWidgetItem(p[1]))
            self.parts_table.setItem(i, 2, QTableWidgetItem(p[2]))
            self.parts_table.setItem(i, 3, QTableWidgetItem(f"{p[3]:.2f} ₽"))
            self.parts_table.setItem(i, 4, QTableWidgetItem(str(p[4])))
            
            add_btn = QPushButton("➕")
            add_btn.setFixedSize(30, 30)
            add_btn.clicked.connect(lambda checked, pid=p[0], name=p[2], price=p[3], qty=p[4]: self.add_part(pid, name, price, qty))
            self.parts_table.setCellWidget(i, 5, add_btn)
        
        self.parts_table.resizeColumnsToContents()
        self.parts_table.setColumnWidth(5, 40)
    
    def add_service(self, service_id, service_name, service_price):
        for i in range(self.selected_services.rowCount()):
            if self.selected_services.cellWidget(i, 4) and int(self.selected_services.item(i, 0).text()) == service_id:
                qty = int(self.selected_services.item(i, 2).text()) + 1
                self.selected_services.item(i, 2).setText(str(qty))
                self.calc_total()
                return
        
        row = self.selected_services.rowCount()
        self.selected_services.setRowCount(row + 1)
        
        self.selected_services.setItem(row, 0, QTableWidgetItem(str(service_id)))
        self.selected_services.setItem(row, 1, QTableWidgetItem(service_name))
        
        qty_item = QTableWidgetItem("1")
        qty_item.setFlags(qty_item.flags() | Qt.ItemIsEditable)
        self.selected_services.setItem(row, 2, qty_item)
        
        price_item = QTableWidgetItem(f"{service_price:.2f} ₽")
        price_item.setFlags(price_item.flags() & ~Qt.ItemIsEditable)
        self.selected_services.setItem(row, 3, price_item)
        
        del_btn = QPushButton("🗑️")
        del_btn.setFixedSize(30, 30)
        del_btn.setStyleSheet("background-color: #e74c3c; color: white;")
        del_btn.clicked.connect(lambda: self.remove_selected_row(self.selected_services, row))
        self.selected_services.setCellWidget(row, 4, del_btn)
        
        self.calc_total()
    
    def add_part(self, part_id, part_name, part_price, available):
        for i in range(self.selected_parts.rowCount()):
            if self.selected_parts.cellWidget(i, 4) and int(self.selected_parts.item(i, 0).text()) == part_id:
                qty = int(self.selected_parts.item(i, 2).text()) + 1
                if qty > available:
                    QMessageBox.warning(self, "Ошибка", f"Доступно только {available} шт.")
                    return
                self.selected_parts.item(i, 2).setText(str(qty))
                self.calc_total()
                return
        
        row = self.selected_parts.rowCount()
        self.selected_parts.setRowCount(row + 1)
        
        self.selected_parts.setItem(row, 0, QTableWidgetItem(str(part_id)))
        self.selected_parts.setItem(row, 1, QTableWidgetItem(part_name))
        
        qty_item = QTableWidgetItem("1")
        qty_item.setFlags(qty_item.flags() | Qt.ItemIsEditable)
        self.selected_parts.setItem(row, 2, qty_item)
        
        price_item = QTableWidgetItem(f"{part_price:.2f} ₽")
        price_item.setFlags(price_item.flags() & ~Qt.ItemIsEditable)
        self.selected_parts.setItem(row, 3, price_item)
        
        del_btn = QPushButton("🗑️")
        del_btn.setFixedSize(30, 30)
        del_btn.setStyleSheet("background-color: #e74c3c; color: white;")
        del_btn.clicked.connect(lambda: self.remove_selected_row(self.selected_parts, row))
        self.selected_parts.setCellWidget(row, 4, del_btn)
        
        self.calc_total()
    
    def remove_selected_row(self, table, row):
        table.removeRow(row)
        self.calc_total()
    
    def calc_total(self):
        total = 0
        
        for i in range(self.selected_services.rowCount()):
            qty_item = self.selected_services.item(i, 2)
            price_item = self.selected_services.item(i, 3)
            if qty_item and price_item:
                try:
                    qty = int(qty_item.text() or "1")
                    price = float(price_item.text().replace('₽', '').replace(',', '').strip() or "0")
                    total += qty * price
                except:
                    pass
        
        for i in range(self.selected_parts.rowCount()):
            qty_item = self.selected_parts.item(i, 2)
            price_item = self.selected_parts.item(i, 3)
            if qty_item and price_item:
                try:
                    qty = int(qty_item.text() or "1")
                    price = float(price_item.text().replace('₽', '').replace(',', '').strip() or "0")
                    total += qty * price
                except:
                    pass
        
        self.total_label.setText(f"{total:,.2f} ₽")
    
    def save_order(self):
        if not self.client_combo.currentData():
            QMessageBox.warning(self, "Ошибка", "Выберите клиента")
            return
        
        if not self.car_combo.currentData():
            QMessageBox.warning(self, "Ошибка", "Выберите автомобиль")
            return
        
        if self.selected_services.rowCount() == 0 and self.selected_parts.rowCount() == 0:
            QMessageBox.warning(self, "Ошибка", "Добавьте услуги или запчасти")
            return
        
        reply = QMessageBox.question(self, "Подтверждение", "Сохранить заказ?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        
        try:
            number = f"ЗН-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            total_text = self.total_label.text().replace('₽', '').replace(',', '').strip()
            total = float(total_text) if total_text else 0
            
            employee = self.db.fetch_one("SELECT id FROM employees LIMIT 1")
            employee_id = employee[0] if employee else None
            
            if self.order_id:
                query = '''
                    UPDATE orders SET
                        client_id=?, car_id=?, employee_id=?, status=?, payment_status=?, total_cost=?, notes=?
                    WHERE id=?
                '''
                params = (self.client_combo.currentData(), self.car_combo.currentData(), employee_id,
                         self.status_combo.currentText(), self.payment_combo.currentText(),
                         total, self.notes.text(), self.order_id)
            else:
                query = '''
                    INSERT INTO orders 
                    (order_number, client_id, car_id, employee_id, created_date, status, payment_status, total_cost, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                '''
                params = (number, self.client_combo.currentData(), self.car_combo.currentData(), employee_id,
                         datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                         self.status_combo.currentText(), self.payment_combo.currentText(), total, self.notes.text())
            
            self.db.execute_query(query, params)
            
            if not self.order_id:
                self.order_id = self.db.cursor.lastrowid
            
            self.db.execute_query("DELETE FROM order_services WHERE order_id = ?", (self.order_id,))
            for i in range(self.selected_services.rowCount()):
                sid_item = self.selected_services.item(i, 0)
                qty_item = self.selected_services.item(i, 2)
                price_item = self.selected_services.item(i, 3)
                
                if sid_item and qty_item and price_item:
                    sid = int(sid_item.text())
                    qty = int(qty_item.text())
                    price = float(price_item.text().replace('₽', '').replace(',', '').strip())
                    self.db.execute_query('''
                        INSERT INTO order_services (order_id, service_id, quantity, price)
                        VALUES (?, ?, ?, ?)
                    ''', (self.order_id, sid, qty, price))
            
            self.db.execute_query("DELETE FROM order_parts WHERE order_id = ?", (self.order_id,))
            for i in range(self.selected_parts.rowCount()):
                pid_item = self.selected_parts.item(i, 0)
                qty_item = self.selected_parts.item(i, 2)
                price_item = self.selected_parts.item(i, 3)
                
                if pid_item and qty_item and price_item:
                    pid = int(pid_item.text())
                    qty = int(qty_item.text())
                    price = float(price_item.text().replace('₽', '').replace(',', '').strip())
                    
                    current = self.db.fetch_one("SELECT quantity FROM parts WHERE id = ?", (pid,))[0]
                    if current < qty:
                        QMessageBox.warning(self, "Ошибка", f"Недостаточно запчастей на складе")
                        return
                    
                    self.db.execute_query("UPDATE parts SET quantity = ? WHERE id = ?", (current - qty, pid))
                    
                    self.db.execute_query('''
                        INSERT INTO parts_movement (part_id, type, quantity, date, order_id, notes)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (pid, 'расход', qty, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                          self.order_id, f"Заказ {number}"))
                    
                    self.db.execute_query('''
                        INSERT INTO order_parts (order_id, part_id, quantity, price)
                        VALUES (?, ?, ?, ?)
                    ''', (self.order_id, pid, qty, price))
            
            QMessageBox.information(self, "Успех", f"Заказ сохранен\nНомер: {number}")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
    
    def load_order(self):
        order = self.db.fetch_one('''
            SELECT client_id, car_id, status, payment_status, notes
            FROM orders WHERE id = ?
        ''', (self.order_id,))
        
        if order:
            idx = self.client_combo.findData(order[0])
            if idx >= 0:
                self.client_combo.setCurrentIndex(idx)
            
            self.load_cars()
            car_idx = self.car_combo.findData(order[1])
            if car_idx >= 0:
                self.car_combo.setCurrentIndex(car_idx)
            
            status_idx = self.status_combo.findText(order[2])
            if status_idx >= 0:
                self.status_combo.setCurrentIndex(status_idx)
            
            pay_idx = self.payment_combo.findText(order[3])
            if pay_idx >= 0:
                self.payment_combo.setCurrentIndex(pay_idx)
            
            self.notes.setText(order[4] or "")
            
            services = self.db.fetch_all('''
                SELECT order_services.service_id, services.name, order_services.quantity, order_services.price
                FROM order_services
                JOIN services ON order_services.service_id = services.id
                WHERE order_services.order_id = ?
            ''', (self.order_id,))
            
            for s in services:
                row = self.selected_services.rowCount()
                self.selected_services.setRowCount(row + 1)
                self.selected_services.setItem(row, 0, QTableWidgetItem(str(s[0])))
                self.selected_services.setItem(row, 1, QTableWidgetItem(s[1]))
                self.selected_services.setItem(row, 2, QTableWidgetItem(str(s[2])))
                self.selected_services.setItem(row, 3, QTableWidgetItem(f"{s[3]:.2f} ₽"))
                
                del_btn = QPushButton("🗑️")
                del_btn.setFixedSize(30, 30)
                del_btn.setStyleSheet("background-color: #e74c3c; color: white;")
                del_btn.clicked.connect(lambda checked, r=row: self.remove_selected_row(self.selected_services, r))
                self.selected_services.setCellWidget(row, 4, del_btn)
            
            parts = self.db.fetch_all('''
                SELECT order_parts.part_id, parts.name, order_parts.quantity, order_parts.price
                FROM order_parts
                JOIN parts ON order_parts.part_id = parts.id
                WHERE order_parts.order_id = ?
            ''', (self.order_id,))
            
            for p in parts:
                row = self.selected_parts.rowCount()
                self.selected_parts.setRowCount(row + 1)
                self.selected_parts.setItem(row, 0, QTableWidgetItem(str(p[0])))
                self.selected_parts.setItem(row, 1, QTableWidgetItem(p[1]))
                self.selected_parts.setItem(row, 2, QTableWidgetItem(str(p[2])))
                self.selected_parts.setItem(row, 3, QTableWidgetItem(f"{p[3]:.2f} ₽"))
                
                del_btn = QPushButton("🗑️")
                del_btn.setFixedSize(30, 30)
                del_btn.setStyleSheet("background-color: #e74c3c; color: white;")
                del_btn.clicked.connect(lambda checked, r=row: self.remove_selected_row(self.selected_parts, r))
                self.selected_parts.setCellWidget(row, 4, del_btn)
            
            self.calc_total()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    db = Database()
    
    while True:
        login = LoginDialog(db)
        if login.exec_() == QDialog.Accepted:
            window = MainWindow(db, login.user_data)
            window.show()
            app.exec_()
        else:
            break
    
    sys.exit()

if __name__ == '__main__':
    main()