# Импорты библиотек
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram import F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import CallbackQuery

# Импорты из других файлов
from backdoor import main_start, get_doctor_answer

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

# Объект бота
bot = Bot(token="7559786010:AAHsA-nVQ8dVwv9BhC9iTpq1UeG-8j5N7gM")
# Диспетчер
dp = Dispatcher()

# Замените на ID чата, куда хотите пересылать сообщения
TARGET_CHAT_ID = -1002494968618

# Хранение ID пользователей и их сообщений
user_messages = dict()


# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="Записаться на приём",
        url="https://fomin-clinic.ru")
    )
    builder.add(types.InlineKeyboardButton(
        text="Задать вопрос",
        callback_data="question")
    )
    # Выравниваем кнопки по 4 в ряд, чтобы получилось 1 + 1
    builder.adjust(1)
    await message.answer(
        "Привет! Я твой виртуальный медицинский ассистент. Что тебя беспокоит?",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data == "question")
async def handle_callback_button1(callback_query: CallbackQuery):
    await bot.send_message(callback_query.from_user.id, "_Напиши мне свой вопрос_",
        parse_mode="MarkdownV2")

# Хэндлер для обработки текстовых сообщений
@dp.message(F.text)
async def handle_text(message: types.Message):
    user_input = message.text
    user_id = message.from_user.id

    # Проверяем, если сообщение не из целевого чата
    if message.chat.id != TARGET_CHAT_ID:
        sent_message = await bot.send_message(user_id, f"⏳ Я начинаю искать для тебя наиболее подходящий ответ")

        answer = main_start(user_id, user_input)
        #print(answer.index, answer.answer, answer.priority, answer.question)
        # Сохраняем ID пользователя и его сообщение
        if answer.answer == None:
            sent_message = await bot.send_message(user_id,
                                   f"😔 К сожалению, я не нашла у себя в базе подходящего ответа( \nТвой вопрос передан специалисту, время ожидание может быть увеличенным")
            await bot.send_message(TARGET_CHAT_ID, f"{answer.index}: {user_id}: {user_input}")

        else:
            await bot.send_message(user_id, f"🗣️Вот тебе мой совет:\n{answer.answer}")
            builder = InlineKeyboardBuilder()
            builder.add(types.InlineKeyboardButton(
                text="Записаться на приём",
                url="https://fomin-clinic.ru")
            )

            if answer.doctor != None:
                await bot.send_message(user_id, f"✍️ Также ты можешь записаться к специалисту: {answer.doctor}",
                    reply_markup=builder.as_markup()
                    )

            builder_recall = InlineKeyboardBuilder()
            builder_recall.add(types.InlineKeyboardButton(
                text="Задать вопрос",
                callback_data="question")
            )
            # Выравниваем кнопки по 4 в ряд, чтобы получилось 1 + 1
            builder_recall.adjust(1)
            await message.answer(
                "_Мы можем продолжить дальнейшее общение, так что пишите 😊_",
                parse_mode="MarkdownV2", reply_markup=builder_recall.as_markup()
            )


    if message.chat.id == TARGET_CHAT_ID and message.reply_to_message:
        # Проверяем, является ли сообщение, на которое ответили, сообщением от бота
        if message.reply_to_message.from_user.id == bot.id:
            user_id, index = extract_user_id(message.reply_to_message.text)
            # Удаляем сообщение, на которое ответили
            await bot.delete_message(chat_id=TARGET_CHAT_ID, message_id=message.reply_to_message.message_id)
            # Удаляем сообщение-ответ
            await bot.delete_message(chat_id=TARGET_CHAT_ID, message_id=message.message_id)
            if user_id != None:
                text, doctor, priority, status = doctor_answer_split(user_input)
                await bot.send_message(user_id, f"👨🏻 ‍Ответ врача:\n{text}")
                # await bot.send_message(user_id, f"{text}")
                builder = InlineKeyboardBuilder()
                builder.add(types.InlineKeyboardButton(
                    text="Записаться на приём",
                    url="https://fomin-clinic.ru")
                )
                if doctor != None:
                    await bot.send_message(user_id, f"✍️ Также ты можешь записаться к специалисту: {doctor}",
                                           reply_markup=builder.as_markup()
                                           )

                builder_recall = InlineKeyboardBuilder()
                builder_recall.add(types.InlineKeyboardButton(
                    text="Задать вопрос",
                    callback_data="question")
                )
                # Выравниваем кнопки по 4 в ряд, чтобы получилось 1 + 1
                builder_recall.adjust(1)
                await bot.send_message(user_id,
                    "_Мы можем продолжить дальнейшее общение, так что пишите 😊_", parse_mode="MarkdownV2",
                    reply_markup=builder_recall.as_markup()
                )



                # при статусе один отправляем в базу, иначе просто общение
                if status:
                    get_doctor_answer(index=index, answer=text, priority=priority, doctor=doctor)


# Функция для извлечения ID пользователя из текста
def extract_user_id(text):
    # Предполагается, что текст содержит ID пользователя в формате "пользователь: <id>"
    # Например, "Сообщение от пользователя 12345: ..."
    parts = text.split(': ')
    if len(parts) > 1:
        return int(parts[1]), int(parts[0])
    return None, None

# Функция для ответа врача
def doctor_answer_split(text):
    parts = text.split('Status: ')    # delete status
    status = int(parts[-1]) if len(parts) > 1 else 0
    
    parts = parts[0].split('Priority: ') # delete priority
    priority = int(parts[-1]) if len(parts) > 1 else 0

    parts = parts[0].split('Doctor: ')  # delete doctor
    doctor = parts[-1] if len(parts) > 1 else None
    answer = parts[0]
    return answer, doctor, priority, status

# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
