import logging
from datetime import datetime

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InputFile, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler

import AdminUser
import fileUpdater
import message
import re

import siteInf

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

adm = AdminUser.Admin()
token = adm.getToken()


def receive_date(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if adm.isAdmin(user_id):
        adm.setDate(update.message.text)
        update.message.reply_text(f'Вы ввели дату: {adm.printDate()}')
        update.message.reply_text(f'Вы ввели дату: {adm.isLate()}')
    else:
        update.message.reply_text('Извините, у вас нет прав для выполнения этой команды.')


# Функция для обработки команды /start
def start(update: Update, context: CallbackContext) -> None:
    if adm.isLate():
        update.message.reply_text(
            'Здравствуйте! Данный бот предназначен для оформление заявки на закупку.\n' +
            'Пожалуйста, отправляйте информацию в формате: "ссылка [пробел] количество". \n\n'
            'Перед отправкой следующего запроса, дождитесь ответного сообщения об успешной записи информации.\n\n' +
            'Запросы принимаются до ' + adm.printDate() + '\n\n'
            'Если вы хотите удалить последнюю заявку - нажмите /change\n'
        )
    else:
        update.message.reply_text(message.MESSAGE_END)



# Функция для обработки текстовых сообщений
def handle_message(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    if adm.isLate():
        n = extract_number_and_link(text)
        if isinstance(n, str):
            update.message.reply_text(n)
            return
        else:
            quantity, link = n[0], n[1]
            user = update.message.from_user
            s = siteInf.SiteParts(link)
            user_name = user.full_name
            profile_link = f'https://t.me/{user.username}' if user.username else 'Нет ссылки'
            price, price_best, name = s.get_inf()
            d = datetime.now().date()
            # Сохраните данные в Excel файл
            fileUpdater.save_to_excel([name, price_best,price, int(quantity), link, profile_link, user_name, d])
            update.message.reply_text('Информация сохранена в Excel файл.')

    else:
        update.message.reply_text('Извините, прием заявок закрыт!')



def extract_number_and_link(text):
    # Регулярное выражение для поиска ссылки
    url_pattern = r'https?://[^\s,\.]+(?:\.[^\s,\.]+)+'
    # Регулярное выражение для поиска числа (целое число)
    number_pattern = r'\b\d+\b'

    # Поиск ссылки
    url_match = re.search(url_pattern, text)
    if url_match:
        url = url_match.group()
    else:
        return "Ссылка не найдена"

    # Удаление ссылки из текста для поиска числа
    text_without_url = re.sub(url_pattern, '', text)

    # Поиск числа
    number_matches = re.findall(number_pattern, text_without_url)

    # Проверка наличия единственного корректного числа
    if len(number_matches) == 1:
        number = number_matches[0]
    else:
        return 'Некорректный ввод числа'

    return number, url


# Функция для обработки команды /getfile
def get_file(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if adm.isAdmin(user_id):
        try:
            with open('data.xlsx', 'rb') as file:
                update.message.reply_document(document=InputFile(file), filename='data.xlsx')
        except FileNotFoundError:
            update.message.reply_text('Файл data.xlsx не найден.')
    else:
        update.message.reply_text('У вас нет прав для выполнения этой команды.')


def set_status(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if adm.isAdmin(user_id):
        update.message.reply_text('Введите дату окончания приема данных (дд.мм.гггг). Текущая дата: ' + adm.printDate() )

    else:
        update.message.reply_text('У вас нет прав для выполнения этой команды.')


def reset_file(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if adm.isAdmin(user_id):
        keyboard = [
            [
                InlineKeyboardButton("Да", callback_data='Да'),
                InlineKeyboardButton("Нет", callback_data='Нет'),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Вы уверены, что хотите обновить файл?', reply_markup=reply_markup)

    else:
        update.message.reply_text('У вас нет прав для выполнения этой команды.')


def change_file(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [
            InlineKeyboardButton("Да", callback_data='Удалить'),
            InlineKeyboardButton("Нет", callback_data='НеУдалить'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Вы уверенны, что хотите удалить последнюю заявку?', reply_markup=reply_markup)


def show_user_req(update: Update, context: CallbackContext) -> None:
    user = f'https://t.me/{update.message.from_user.username}'
    text = fileUpdater.show_all_req(user)
    update.message.reply_text(text)



def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user = update.callback_query.from_user
    # Обработка нажатия кнопки
    query.answer()
    if query.data == 'Да':
        fileUpdater.delete_inf()
        query.edit_message_text(text='Файл обновлен')
    elif query.data == 'Нет':
        query.edit_message_text(text='Файл не обновлен')
    elif query.data == 'Удалить':
        profile_link = f'https://t.me/{user.username}' if user.username else 'Нет ссылки'
        fileUpdater.delete_last_inf(profile_link)
        query.edit_message_text(text='Запись удалена')
    elif query.data == 'НеУдалить':
        query.edit_message_text(text='Запись НЕ удалена')




    # Основная функция для запуска бота
def main():
    # Создание объекта Updater и Dispatcher
    updater = Updater(token, use_context=True)
    dispatcher = updater.dispatcher

    # Регистрация обработчиков команд и сообщений

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("file", get_file))
    dispatcher.add_handler(CommandHandler("status", set_status))
    dispatcher.add_handler(CommandHandler("reset", reset_file))
    dispatcher.add_handler(CommandHandler("change", change_file))
    dispatcher.add_handler(CommandHandler("show", show_user_req))


    dispatcher.add_handler(CallbackQueryHandler(button))

    dispatcher.add_handler(MessageHandler(Filters.regex(r'^\d{2}.\d{2}.\d{4}$'), receive_date))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Запуск бота
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
