from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Словарь для хранения данных пользователей
user_data = {}
ADMIN_IDS = [1406491528, 6108824933]  # Укажите ID обоих администраторов




async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветствие и автоматический переход в меню"""
    first_name = update.effective_user.first_name
    last_name = update.effective_user.last_name or "Фамилия не указана"
    user_id = update.effective_user.id

    # Сохраняем данные пользователя
    user_data[user_id] = {
        'name': first_name,
        'surname': last_name
    }

    # Приветствие
    await update.message.reply_text(
        f"👋 Привет, {first_name} {last_name}! Добро пожаловать в бота для заказа кофе ☕️!"
    )
    await show_menu(update, context)



async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    await update.message.reply_text(
        "📋 Команды бота:\n"
        "/start - начать работу с ботом\n"
        "/menu - показать меню\n"
        "/help - помощь"
    )


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /menu"""
    await show_menu(update, context)


async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вывод меню с кнопками"""
    keyboard = [
        [InlineKeyboardButton("🛎 Заказ 🛎", callback_data='order')],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text("Выберите опцию:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text("Выберите опцию:", reply_markup=reply_markup)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == 'order':
        await ask_coffee_type(query, context)
    elif query.data == 'help':
        await query.edit_message_text(
            "📋 Команды бота:\n"
            "/start - начать работу с ботом\n"
            "/menu - показать меню\n"
            "/help - помощь"
        )
    elif query.data == 'pay':
        await pay(query, context)

async def ask_coffee_type(query, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Cappuccino", callback_data='Cappuccino')],
        [InlineKeyboardButton("Espresso", callback_data='Espresso')],
        [InlineKeyboardButton("Coffee", callback_data='Coffee')],
        [InlineKeyboardButton("🔙 Отмена 🔙", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Выберите вид кофе:", reply_markup=reply_markup)

async def handle_order_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == 'cancel':
        await query.edit_message_text("Заказ отменён.")
        await show_menu(update, context)
        return

    if query.data in ['Cappuccino', 'Espresso', 'Coffee']:
        user_data[user_id]['coffee'] = query.data
        await query.edit_message_text(f"Вы выбрали {query.data}.")
        await ask_sugar(query, context)

async def ask_sugar(query, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Без сахара", callback_data='Без сахара')],
        [InlineKeyboardButton("1 ложка", callback_data='1 ложка')],
        [InlineKeyboardButton("2 ложки", callback_data='2 ложки')],
        [InlineKeyboardButton("3 ложки", callback_data='3 ложки')],
        [InlineKeyboardButton("🔙 Отмена 🔙", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Сколько ложек сахара положить в кофе?", reply_markup=reply_markup)

async def handle_sugar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == 'cancel':
        await query.edit_message_text("Заказ отменён.")
        await show_menu(update, context)
        return

    if query.data in ['Без сахара', '1 ложка', '2 ложки', '3 ложки']:
        user_data[user_id]['sugar'] = query.data
        await ask_payment(query, context)

async def ask_payment(query, context: ContextTypes.DEFAULT_TYPE):
    user_id = query.from_user.id
    keyboard = [
        [InlineKeyboardButton("Наличные", callback_data='cash')],
        [InlineKeyboardButton("Онлайн (click на кассе)", callback_data='online')],
        [InlineKeyboardButton("🔙 Отмена 🔙", callback_data='cancel')]
    ]
    if user_id in ADMIN_IDS:  # Кнопка "Пропустить" доступна для обоих администраторов
        keyboard.append([InlineKeyboardButton("Пропустить оплату", callback_data='skip')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Как будете 💸 оплачивать💸? 3 000 сум 986019010149374", reply_markup=reply_markup)

async def handle_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == 'cancel':
        await query.edit_message_text("Заказ отменён.")
        await show_menu(update, context)
        return

    if query.data in ['cash', 'online', 'skip']:
        payment = 'Наличные' if query.data == 'cash' else 'Онлайн' if query.data == 'online' else 'Пропущено'
        user_data[user_id]['payment'] = payment

        # Уведомление админу
        await context.bot.send_message(
            ADMIN_IDS[0],
            f"☕️ Новый заказ:\n"
            f"Клиент: {user_data[user_id]['name']} {user_data[user_id]['surname']}\n"
            f"Кофе: {user_data[user_id]['coffee']}\n"
            f"Сахар: {user_data[user_id]['sugar']}\n"
            f"Оплата: {payment}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Готово", callback_data=f"ready_{user_id}")],
                [InlineKeyboardButton("Отменить", callback_data=f"cancel_{user_id}")]
            ])
        )
        
        await context.bot.send_message(
            ADMIN_IDS[1],
            f"☕️ Новый заказ:\n"
            f"Клиент: {user_data[user_id]['name']} {user_data[user_id]['surname']}\n"
            f"Кофе: {user_data[user_id]['coffee']}\n"
            f"Сахар: {user_data[user_id]['sugar']}\n"
            f"Оплата: {payment}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Готово", callback_data=f"ready_{user_id}")],
                [InlineKeyboardButton("Отменить", callback_data=f"cancel_{user_id}")]
            ])
        )

        # Уведомление пользователю
        await query.message.reply_text(
            f"Ваш заказ принят, {user_data[user_id]['name']}! Ваш кофе будет готов через 5 минут. 9860190101149374"
        )
        await show_menu(update, context)

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data.split('_')
    action = data[0]
    user_id = int(data[1])

    if action == 'ready':
        await context.bot.send_message(user_id, "😁 Ваш заказ готов! Приятного аппетита ☕️.")
        await query.answer("Пользователь уведомлён, что заказ готов.")
    elif action == 'cancel':
        await context.bot.send_message(user_id, "😞 Извините, ваш заказ отменён.")
        await query.answer("Пользователь уведомлён, что заказ отменён.")

def main():
    TOKEN = "7982381260:AAGkAt7u-eEMYtiaYQL17fWgKgs978_3Gpg"
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CallbackQueryHandler(handle_callback, pattern="^(order|help)$"))
    app.add_handler(CallbackQueryHandler(handle_order_callback, pattern="^(Cappuccino|Espresso|Coffee|cancel)$"))
    app.add_handler(CallbackQueryHandler(handle_sugar_callback, pattern="^(Без сахара|1 ложка|2 ложки|3 ложки|cancel)$"))
    app.add_handler(CallbackQueryHandler(handle_payment_callback, pattern="^(cash|online|cancel|skip)$"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^(ready|cancel)_\\d+$"))

    print("Бот запущен! Нажмите Ctrl+C для остановки.")
    app.run_polling()

if __name__ == "__main__":
    main()
