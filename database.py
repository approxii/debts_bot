import sqlite3
import os
from typing import List, Tuple


class Database:
    def __init__(self, db_name: str = 'expenses.db'):
        db_dir = os.path.dirname(db_name)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

        self.db_name = db_name
        print(f"📁 База данных: {os.path.abspath(self.db_name)}")
        self.init_db()

    def init_db(self):
        """Инициализация базы данных"""
        print(f"📁 Проверяем существование файла: {os.path.exists(self.db_name)}")

        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            # Проверим существование таблиц
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"📊 Существующие таблицы: {tables}")

            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT
                )
            ''')
            # Таблица расходов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS expenses (
                    expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    amount REAL NOT NULL,
                    description TEXT,
                    date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            conn.commit()

        print("✅ База данных инициализирована")

    def add_user(self, user_id: int, username: str, full_name: str):
        """Добавление пользователя"""
        print(f"👤 Добавление пользователя: {user_id}, {full_name}")
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?, ?, ?)',
                (user_id, username, full_name)
            )
            conn.commit()
        print(f"✅ Пользователь {user_id} добавлен")

    def add_expense(self, user_id: int, amount: float, description: str = None):
        """Добавление расхода"""
        print(f"💸 Добавление расхода: user_id={user_id}, amount={amount}, desc={description}")
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO expenses (user_id, amount, description) VALUES (?, ?, ?)',
                    (user_id, amount, description)
                )
                conn.commit()
            print("✅ Расход добавлен в базу")

            self._check_last_expense()

        except Exception as e:
            print(f"❌ Ошибка при добавлении расхода: {e}")

    def _check_last_expense(self):
        """Проверка последней добавленной записи"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM expenses')
                count = cursor.fetchone()[0]
                print(f"📊 Всего записей в expenses: {count}")

                cursor.execute('SELECT * FROM expenses ORDER BY expense_id DESC LIMIT 1')
                last_record = cursor.fetchone()
                print(f"📝 Последняя запись: {last_record}")
        except Exception as e:
            print(f"❌ Ошибка при проверке: {e}")

    def get_all_expenses(self) -> List[Tuple]:
        """Получение всех расходов"""
        print("📋 Запрос всех расходов из базы")
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT e.expense_id, u.user_id, u.full_name, e.amount, e.description, e.date
                    FROM expenses e
                    JOIN users u ON e.user_id = u.user_id
                    ORDER BY e.date DESC
                ''')
                result = cursor.fetchall()
                print(f"✅ Получено {len(result)} записей")
                return result
        except Exception as e:
            print(f"❌ Ошибка при получении расходов: {e}")
            return []

    def get_user_expenses(self, user_id: int) -> List[Tuple]:
        """Получение расходов конкретного пользователя"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT e.amount, e.description, e.date, u.full_name
                FROM expenses e
                JOIN users u ON e.user_id = u.user_id
                WHERE e.user_id = ? 
                ORDER BY e.date DESC
            ''', (user_id,))
            return cursor.fetchall()

    def clear_all_data(self):
        """Очистка всех данных (для сброса)"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM expenses')
            cursor.execute('DELETE FROM users')
            conn.commit()