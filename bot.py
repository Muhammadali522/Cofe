from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

user_data = {}
ADMIN_IDS = [1406491528, 6108824933]  # Проверь ID админов!
pending_messages = {}  # Хранение сообщений для отправки клиенту

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветствие пользователя"""
    first_name = update.effective_user.first_name
    last_name = update.effective_user.last_name or "Фамилия не указана"
    user_id = update.effective_user.id

    user_data[user_id] = {'name': first_name, 'surname': last_name}
    await update.message.reply_text(f"👋 Привет, {first_name} {last_name}! Добро пожаловать в бота ☕️!")
    await show_menu(update, context)

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню"""
    keyboard = [[InlineKeyboardButton("🛎 Заказ", callback_data='order')],
                [InlineKeyboardButton("ℹ️ Помощь", callback_data='help')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("Выберите опцию:", reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text("Выберите опцию:", reply_markup=reply_markup)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'order':
        await ask_coffee_type(query, context)
    elif query.data == 'help':
        await query.edit_message_text("📋 Команды бота:\n/start - начать\n/menu - меню\n/help - помощь")

async def ask_coffee_type(query, context: ContextTypes.DEFAULT_TYPE):
    """Выбор вида кофе"""
    keyboard = [[InlineKeyboardButton("Cappuccino", callback_data='Cappuccino')],
                [InlineKeyboardButton("Espresso", callback_data='Espresso')],
                [InlineKeyboardButton("Coffee", callback_data='Coffee')],
                [InlineKeyboardButton("🔙 Отмена", callback_data='cancel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Выберите кофе:", reply_markup=reply_markup)

async def handle_order_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == 'cancel':
        await show_menu(update, context)
        return

    user_data[user_id]['coffee'] = query.data
    await ask_cups(query, context)

async def ask_cups(query, context: ContextTypes.DEFAULT_TYPE):
    """Выбор количества чашек"""
    keyboard = [[InlineKeyboardButton("1 чашка", callback_data='1')],
                [InlineKeyboardButton("2 чашки", callback_data='2')],
                [InlineKeyboardButton("3 чашки", callback_data='3')],
                [InlineKeyboardButton("🔙 Назад", callback_data='order')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Сколько чашек заказать?", reply_markup=reply_markup)

async def handle_cups_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == 'order':
        await ask_coffee_type(query, context)
        return

    user_data[user_id]['cups'] = int(query.data)
    await ask_payment(query, context)

async def ask_payment(query, context: ContextTypes.DEFAULT_TYPE):
    """Оплата"""
    user_id = query.from_user.id
    price = 10000 * user_data[user_id]['cups']
    keyboard = [[InlineKeyboardButton("Наличные", callback_data='cash')],
                [InlineKeyboardButton("Онлайн", callback_data='online')],
                [InlineKeyboardButton("🔙 Назад", callback_data='cups')]]

    if user_id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("Пропустить оплату", callback_data='skip')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"💸 Оплатите {price} сум. Как будете платить? ", reply_markup=reply_markup)

async def handle_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка оплаты и отправка заказа админу"""
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == 'cups':
        await ask_cups(query, context)
        return

    payment = 'Наличные' if query.data == 'cash' else 'Онлайн' if query.data == 'online' else 'Пропущено'
    user_data[user_id]['payment'] = payment

    order_text = (f"☕️ Новый заказ:\n"
                  f"Клиент: {user_data[user_id]['name']} {user_data[user_id]['surname']}\n"
                  f"Кофе: {user_data[user_id]['coffee']}\n"
                  f"Количество: {user_data[user_id]['cups']} чашек\n"
                  f"Оплата: {payment}")

    keyboard = [[InlineKeyboardButton("Готово", callback_data=f"ready_{user_id}")],
                [InlineKeyboardButton("Отменить", callback_data=f"cancel_{user_id}")],
                [InlineKeyboardButton("📩 Отправить сообщение", callback_data=f"message_{user_id}")]]

    for admin in ADMIN_IDS:
        try:
            await context.bot.send_message(admin, order_text, reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e:
            print(f"⚠ Ошибка отправки админу {admin}: {e}")

    await query.message.reply_text(f"✅ Ваш заказ принят! Ожидайте ☕️. 9860190101149374")
    await show_menu(update, context)

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка действий админа"""
    query = update.callback_query
    data = query.data.split('_')
    action, user_id = data[0], int(data[1])

    if action == 'ready':
        await context.bot.send_message(user_id, "✅ Ваш заказ готов! Приятного аппетита ☕️.")
        await query.answer("Уведомление отправлено.")
    elif action == 'cancel':
        await context.bot.send_message(user_id, "❌ Ваш заказ отменён.")
        await query.answer("Уведомление отправлено.")
    elif action == 'message':
        pending_messages[query.from_user.id] = user_id
        await query.message.reply_text("📩 Введите сообщение для клиента:")
        await query.answer()

async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ввод сообщения от админа"""
    admin_id = update.message.from_user.id
    if admin_id in pending_messages:
        user_id = pending_messages.pop(admin_id)
        await context.bot.send_message(user_id, f"📩 Сообщение от администратора:\n{update.message.text}")
        await update.message.reply_text("✅ Сообщение отправлено!")
    else:
        await update.message.reply_text("❌ Ошибка: Вы не выбирали клиента для сообщения.")

def main():
    TOKEN = "7982381260:AAGkAt7u-eEMYtiaYQL17fWgKgs978_3Gpg"
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_IDS), handle_admin_message))
    app.add_handler(CallbackQueryHandler(handle_callback, pattern="^(order|help)$"))
    app.add_handler(CallbackQueryHandler(handle_order_callback, pattern="^(Cappuccino|Espresso|Coffee|cancel)$"))
    app.add_handler(CallbackQueryHandler(handle_cups_callback, pattern="^[123]$"))
    app.add_handler(CallbackQueryHandler(handle_payment_callback, pattern="^(cash|online|skip|cups)$"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^(ready|cancel|message)_\\d+$"))

    print("✅ Бот запущен! Нажмите Ctrl + C для отключения ")
    app.run_polling()

if __name__ == "__main__":
    main()
