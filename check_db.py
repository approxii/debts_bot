import sqlite3
import os


def check_database():
    db_name = 'expenses.db'
    print(f"🔍 Проверка базы данных: {os.path.abspath(db_name)}")
    print(f"📁 Файл существует: {os.path.exists(db_name)}")

    if os.path.exists(db_name):
        print("📊 Содержимое базы данных:")
        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"Таблицы: {tables}")

            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()
            print(f"Пользователи: {users}")

            cursor.execute("SELECT * FROM expenses")
            expenses = cursor.fetchall()
            print(f"Расходы: {expenses}")
            print(f"Всего расходов: {len(expenses)}")

            conn.close()

        except Exception as e:
            print(f"Ошибка при проверке базы: {e}")
    else:
        print("Файл базы данных не найден!")


if __name__ == "__main__":
    check_database()