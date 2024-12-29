from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# Словарь для хранения данных пользователей
user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    first_name = update.effective_user.first_name
    user_id = update.effective_user.id
    user_data[user_id] = {}
    await notify_all_users(context)
    await update.message.reply_text(f"Привет, {first_name}, это бот для заказа кофе☕️☕️.")
    await update.message.reply_text("✍️Введите имя.")
    user_data[user_id]['step'] = 'name'

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_data or 'step' not in user_data[user_id]:
        await update.message.reply_text("Пожалуйста, начните с команды /start.")
        return

    step = user_data[user_id]['step']

    if step == 'name':
        user_data[user_id]['name'] = text
        user_data[user_id]['step'] = 'surname'
        await update.message.reply_text("✍️Введите фамилию.")

    elif step == 'surname':
        user_data[user_id]['surname'] = text
        user_data[user_id]['step'] = 'phone'
        await update.message.reply_text("📱Введите номер телефона.")

    elif step == 'phone':
        user_data[user_id]['phone'] = text
        name = user_data[user_id]['name']
        surname = user_data[user_id]['surname']
        user_data[user_id]['step'] = 'menu'
        await update.message.reply_text(f"👋 Здравствуйте, {name} {surname}, добро пожаловать!")
        await show_menu(update, context)

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🛎Заказ🛎", callback_data='order')]
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

async def ask_coffee_type(query: Update, context: ContextTypes.DEFAULT_TYPE):
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
        user_data[user_id]['step'] = 'menu'
        await show_menu(update, context)
        return

    if query.data in ['Cappuccino', 'Espresso', 'Coffee']:
        user_data[user_id]['coffee'] = query.data
        await query.edit_message_text(f"Вы выбрали {query.data}.")
        await ask_sugar(query, context)

async def ask_sugar(query: Update, context: ContextTypes.DEFAULT_TYPE):
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
        user_data[user_id]['step'] = 'menu'
        await show_menu(update, context)
        return

    if query.data in ['Без сахара', '1 ложка', '2 ложки', '3 ложки']:
        user_data[user_id]['sugar'] = query.data
        await ask_payment(query, context)

async def ask_payment(query: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Наличные", callback_data='cash')],
        [InlineKeyboardButton("Онлайн (click на кассе)", callback_data='online')],
        [InlineKeyboardButton("🔙 Отмена 🔙", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Как будете 💸 оплачивать💸?", reply_markup=reply_markup)

async def handle_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == 'cancel':
        await query.edit_message_text("Заказ отменён.")
        user_data[user_id]['step'] = 'menu'
        await show_menu(update, context)
        return

    if query.data in ['cash', 'online']:
        user_data[user_id]['payment'] = 'Наличные' if query.data == 'cash' else 'Онлайн'
        user_data[user_id]['step'] = 'menu'
        await send_order_to_admin(context.bot, user_id)
        await query.edit_message_text(f"Ваш заказ принят, {user_data[user_id]['name']}!")
        await show_menu(update, context)

async def send_order_to_admin(bot, user_id):
    admin_id = "1406491528"
    order = user_data[user_id]
    order_message = (
        f"**Заказ 🛎**\n\n"
        f"Имя: {order['name']}\n"
        f"Фамилия: {order['surname']}\n"
        f"Телефон: {order['phone']}\n"
        f"Вид кофе: {order['coffee']}\n"
        f"Сахар: {order['sugar']}\n"
        f"Оплата: {order['payment']}\n"
    )
    keyboard = [
        [InlineKeyboardButton("Готово", callback_data=f"ready_{user_id}")],
        [InlineKeyboardButton("Отмена", callback_data=f"cancel_{user_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await bot.send_message(chat_id=admin_id, text=order_message, parse_mode="Markdown", reply_markup=reply_markup)

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data.startswith("ready_"):
        user_id = int(data.split("_")[1])
        name = user_data[user_id]['name']
        surname = user_data[user_id]['surname']
        await context.bot.send_message(chat_id=user_id, text=f"Здравствуйте, {name} {surname}! Ваш 🛎Заказ🛎 готов.")
        del user_data[user_id]
        await query.edit_message_text("Заказ помечен как выполненный.")

    elif data.startswith("cancel_"):
        user_id = int(data.split("_")[1])
        name = user_data[user_id]['name']
        surname = user_data[user_id]['surname']
        await context.bot.send_message(chat_id=user_id, text=f"Здравствуйте, {name} {surname}, извините, ваш 🛎Заказ🛎 отменён.")
        del user_data[user_id]
        await query.edit_message_text("Заказ отменён.")

async def notify_all_users(context: ContextTypes.DEFAULT_TYPE):
    message = (
        "🎉 Привет, друзья! 🎉\n"
        "Мы снова с вами! ☕️✨\n"
        "Сервер готов принимать ваши заказы! 🛎️\n"
        "Заходите в меню и выбирайте свой идеальный кофе! ❤️"
    )
    for user_id in list(user_data.keys()):
        try:
            await context.bot.send_message(chat_id=user_id, text=message)
        except Exception as e:
            print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

async def notify_server_start(context: ContextTypes.DEFAULT_TYPE):
    print("Оповещение: сервер запущен, рассылаем уведомления.")
    await notify_all_users(context)

# Основная функция с вызовом JobQueue:
def main():
    TOKEN = "7982381260:AAGkAt7u-eEMYtiaYQL17fWgKgs978_3Gpg"
    app = Application.builder().token(TOKEN).build()

    # Создаём JobQueue
    job_queue = app.job_queue

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", show_menu))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback, pattern="^(order)$"))
    app.add_handler(CallbackQueryHandler(handle_order_callback, pattern="^(Cappuccino|Espresso|Coffee|cancel)$"))
    app.add_handler(CallbackQueryHandler(handle_sugar_callback, pattern="^(Без сахара|1 ложка|2 ложки|3 ложки|cancel)$"))
    app.add_handler(CallbackQueryHandler(handle_payment_callback, pattern="^(cash|online|cancel)$"))
    app.add_handler(CallbackQueryHandler(handle_admin_callback, pattern="^(ready_|cancel_)"))

    # Запуск уведомления после старта
    job_queue.run_once(notify_server_start, when=0)

    print("Бот запущен! Нажмите Ctrl+C для остановки.")
    app.run_polling()



if __name__ == "__main__":
    main()
