import os
import logging
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes,
    ConversationHandler, filters
)
from database import Database
from calculator import DebtCalculator

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

AMOUNT, DESCRIPTION = range(2)

db_path = os.path.join(os.getcwd(), 'data', 'expenses.db')
db = Database(db_path)
calculator = DebtCalculator()

TOKEN = os.getenv('BOT_TOKEN')

if not TOKEN:
    logger.error("BOT_TOKEN не найден в переменных окружения")
    exit(1)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    db.add_user(user.id, user.username, user.full_name)

    keyboard = [
        ['💳 Добавить расход', '📊 Баланс'],
        ['📝 Мои расходы', '📋 Все расходы'],
        ['🗑️ Очистить БД']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Управление общими расходами\nВыберите действие:",
        reply_markup=reply_markup
    )


async def add_expense_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало добавления расхода"""
    await update.message.reply_text(
        "Введите сумму расхода:",
        reply_markup=ReplyKeyboardRemove()
    )
    return AMOUNT


async def add_expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка суммы расхода"""
    try:
        amount = float(update.message.text.replace(',', '.'))
        if amount <= 0:
            await update.message.reply_text("Сумма должна быть положительной:")
            return AMOUNT

        context.user_data['amount'] = amount

        skip_keyboard = ReplyKeyboardMarkup([['➖ Без описания']], resize_keyboard=True)
        await update.message.reply_text(
            "Введите описание расхода:",
            reply_markup=skip_keyboard
        )
        return DESCRIPTION

    except ValueError:
        await update.message.reply_text("Введите корректную сумму:")
        return AMOUNT


async def add_expense_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка описания расхода"""
    if update.message.text == '➖ Без описания':
        return await skip_description(update, context)

    description = update.message.text
    context.user_data['description'] = description
    return await finish_expense(update, context)


async def skip_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пропуск описания"""
    context.user_data['description'] = None

    keyboard = [
        ['💳 Добавить расход', '📊 Баланс'],
        ['📝 Мои расходы', '📋 Все расходы'],
        ['🗑️ Очистить БД']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    amount = context.user_data['amount']
    db.add_expense(update.effective_user.id, amount, None)

    await update.message.reply_text(
        f"✅ Расход добавлен\nСумма: {amount:.2f} руб.",
        reply_markup=reply_markup
    )

    context.user_data.clear()
    return ConversationHandler.END


async def finish_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение добавления расхода"""
    user = update.effective_user
    amount = context.user_data['amount']
    description = context.user_data.get('description')

    db.add_expense(user.id, amount, description)

    keyboard = [
        ['💳 Добавить расход', '📊 Баланс'],
        ['📝 Мои расходы', '📋 Все расходы'],
        ['🗑️ Очистить БД']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    desc_text = f" ({description})" if description else ""
    await update.message.reply_text(
        f"✅ Расход добавлен\nСумма: {amount:.2f} руб.{desc_text}",
        reply_markup=reply_markup
    )

    context.user_data.clear()
    return ConversationHandler.END


async def show_debts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать текущие балансы"""
    expenses = db.get_all_expenses()
    total_spent = sum(expense[3] for expense in expenses)

    balances, debts = calculator.calculate_debts(expenses)
    message = calculator.format_debts_message(balances, debts, total_spent)

    await update.message.reply_text(message, parse_mode='Markdown')


async def show_my_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать расходы текущего пользователя"""
    user = update.effective_user
    expenses = db.get_user_expenses(user.id)

    if not expenses:
        await update.message.reply_text("У вас пока нет расходов")
        return

    message = [f"📝 Ваши расходы:", ""]
    total = 0

    for expense in expenses[:15]:
        amount = expense[0]
        description = f" - {expense[1]}" if expense[1] else ""
        date = expense[2].split()[0] if expense[2] else ""

        message.append(f"• {amount:.2f} руб.{description} ({date})")
        total += amount

    message.extend([
        "",
        f"Всего: {total:.2f} руб.",
        f"Ваша доля: {total/3:.2f} руб." if total > 0 else ""
    ])

    await update.message.reply_text("\n".join(message))


async def show_all_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать все расходы"""
    expenses = db.get_all_expenses()

    if not expenses:
        await update.message.reply_text("Расходы отсутствуют")
        return

    message = ["📋 Все расходы:", ""]
    total = 0
    user_totals = {}

    for expense in expenses[:15]:
        user_name = expense[2]
        amount = expense[3]
        description = f" - {expense[4]}" if expense[4] else ""
        date = expense[5].split()[0] if expense[5] else ""

        message.append(f"• {user_name}: {amount:.2f} руб.{description} ({date})")
        total += amount

        if user_name in user_totals:
            user_totals[user_name] += amount
        else:
            user_totals[user_name] = amount

    message.extend(["", "📊 Итоги:"])
    for user_name, user_total in user_totals.items():
        message.append(f"• {user_name}: {user_total:.2f} руб.")

    message.extend([
        "",
        f"Общая сумма: {total:.2f} руб.",
        f"Доля каждого: {total/3:.2f} руб." if total > 0 else ""
    ])

    await update.message.reply_text("\n".join(message))


async def clear_database(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Очистка базы данных"""
    confirm_keyboard = ReplyKeyboardMarkup([
        ['✅ Подтвердить', '❌ Отмена']
    ], resize_keyboard=True)

    await update.message.reply_text(
        "Очистить всю базу данных?\nЭто действие нельзя отменить.",
        reply_markup=confirm_keyboard
    )


async def handle_clear_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка подтверждения очистки"""
    if update.message.text == '✅ Подтвердить':
        db.clear_all_data()

        keyboard = [
            ['💳 Добавить расход', '📊 Баланс'],
            ['📝 Мои расходы', '📋 Все расходы'],
            ['🗑️ Очистить БД']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text(
            "База данных очищена",
            reply_markup=reply_markup
        )
    else:
        keyboard = [
            ['💳 Добавить расход', '📊 Баланс'],
            ['📝 Мои расходы', '📋 Все расходы'],
            ['🗑️ Очистить БД']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text(
            "Действие отменено",
            reply_markup=reply_markup
        )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена текущей операции"""
    keyboard = [
        ['💳 Добавить расход', '📊 Баланс'],
        ['📝 Мои расходы', '📋 Все расходы'],
        ['🗑️ Очистить БД']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Операция отменена",
        reply_markup=reply_markup
    )
    context.user_data.clear()
    return ConversationHandler.END


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    text = update.message.text

    if text == '💳 Добавить расход':
        return await add_expense_start(update, context)
    elif text == '📊 Баланс':
        return await show_debts(update, context)
    elif text == '📝 Мои расходы':
        return await show_my_expenses(update, context)
    elif text == '📋 Все расходы':
        return await show_all_expenses(update, context)
    elif text == '🗑️ Очистить БД':
        return await clear_database(update, context)
    elif text in ['✅ Подтвердить', '❌ Отмена']:
        return await handle_clear_confirmation(update, context)
    else:
        if context.user_data.get('amount') and not context.user_data.get('description'):
            return await add_expense_description(update, context)

        await update.message.reply_text("Выберите действие из меню:")


def main():
    """Запуск бота"""
    if not TOKEN:
        logger.error("Токен бота не найден! Создайте файл .env с BOT_TOKEN=your_token")
        return

    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^💳 Добавить расход$'), add_expense_start)],
        states={
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_expense_amount)],
            DESCRIPTION: [MessageHandler(filters.TEXT, add_expense_description)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(CommandHandler('start', start))
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен...")
    application.run_polling()


if __name__ == '__main__':
    main()