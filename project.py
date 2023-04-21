import random
import traceback

import openai
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from googletrans import Translator

try:
    API_KEY = "API_KEY"
    openai.api_key = "openai.api_key"

    users_and_they_topics = {}

    bot = Bot(token=API_KEY)
    dp = Dispatcher(bot)
    bot_messages = {}

    getMnKeyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False).add(
        KeyboardButton('Get Meaning'),
    )


    async def store_bot_message(user_id, message):
        global bot_messages

        if user_id not in bot_messages:
            bot_messages[user_id] = []
        bot_messages[user_id].append(message)


    async def clear_bot_message(user_id):
        global bot_messages
        bot_messages[user_id] = []


    async def translate_bot_messages(user_id):
        global bot_messages

        if user_id in bot_messages:
            translator = Translator()
            for message in bot_messages[user_id]:
                translated = translator.translate(message, dest='ru')
                await bot.send_message(user_id, translated.text)


    @dp.message_handler(commands=['start'])
    async def start(message: types.Message):
        await bot.send_message(message.chat.id,
                               "Welcome to the AI Teacher Bot! Please select a topic:")
        await store_bot_message(message.from_id, "Welcome to the AI Teacher Bot! Please select a topic:")
        keyboard = InlineKeyboardMarkup()
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f"Create me 5 base material thing themes. Return nouns. Example:"
                   f"1. Cats\n"
                   f"2. Cars\n"
                   f"3. Nature\n"
                   f"4. Space\n"
                   f"5. Technology",
            max_tokens=1000,
            n=1,
            stop=None,
            temperature=0.5,
        )
        topics = response["choices"][0]["text"].strip().split("\n")
        if len(topics) > 5:
            for i in topics[:5]:
                keyboard.add(InlineKeyboardButton(i, callback_data=f"set_topic:{i}"))
        else:
            for i in topics:
                keyboard.add(InlineKeyboardButton(i, callback_data=f"set_topic:{i}"))
        keyboard.add(InlineKeyboardButton("Set your Topic", callback_data="set_topic"))
        await bot.send_message(message.chat.id, "Select an topic:", reply_markup=keyboard)
        await store_bot_message(message.from_id, "Select an topic:")


    async def translate(user_id):
        global bot_messages

        if user_id in bot_messages:
            translator = Translator()
            for message in bot_messages[user_id]:
                translated = translator.translate(message, src='en', dest='ru')
                await bot.send_message(user_id, translated.text)


    @dp.callback_query_handler(lambda c: c.data == 'set_topic')
    async def start_topic(callback_query: types.CallbackQuery):
        await bot.answer_callback_query(callback_query.id)
        await clear_bot_message(callback_query.from_user.id)
        await bot.send_message(callback_query.message.chat.id,
                               "Okay, now write the topic of the lesson, please.")
        await store_bot_message(callback_query.from_user.id, "Okay, now write the topic of the lesson, please.")


    @dp.callback_query_handler(lambda c: c.data[:10] == 'set_topic:')
    async def start_topic(callback_query: types.CallbackQuery):
        await bot.answer_callback_query(callback_query.id)
        await clear_bot_message(callback_query.from_user.id)
        await bot.send_message(callback_query.message.chat.id,
                               f"Okay, the topic of the lesson: {callback_query.data[10:]}")
        await store_bot_message(callback_query.from_user.id,
                                f"Okay, the topic of the lesson: {callback_query.data[10:]}")
        await set_topic(callback_query.message, callback_query.data[10:], callback_query.from_user.id)


    '''@dp.callback_query_handler(lambda c: c.data == 'set_topic_command')
    async def set_topic_command(callback_query: types.CallbackQuery):
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.message.chat.id,
                               "Okay, now type /topic followed by your desired topic, please.")'''


    async def set_topic(message, data='', tid=0):
        if data:
            topic = data
        else:
            topic = message.text.lower().replace("topic ", "")
            tid = message.from_id
        global users_and_they_topics

        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f"Provide a list(30 words. VERY IMPORTANT!!!: they have serial numbers, FORMAT EXAMPLE!!!: 1. Cat\n 2. Dog))"
                   f" of basic and most popular words related to {topic}."
                   f" Make the maximum sure that all words are chosen to study the topic."
                   f" let the words not be repeated:",
            max_tokens=1000,
            n=1,
            stop=None,
            temperature=0.5,
        )
        words = response["choices"][0]["text"].strip().split("\n")
        ws = words.copy()
        words = []

        try:
            for i in ws:
                txt = i
                txt = txt.replace(' ', '@')
                for j in txt:
                    if not j.isalpha() and j != '@':
                        txt = txt.replace(j, '')

                txt = ' '.join(txt.split('@'))

                if txt[0] == ' ':
                    txt = txt[1:]

                words.append(txt.capitalize())
        except IndexError:
            pass

        users_and_they_topics[tid] = [words, topic, False, '']

        str_ = '\n'.join(words)

        # question = await get_question(topic, words)
        await bot.send_message(message.chat.id,
                               f"Here are the words on the topic of the lesson:\n{str_}")
        await bot.send_message(message.chat.id,
                               f"If you have questions about the meanings of words,"
                               f" then click the 'Get Meaning' button below,"
                               f" and enter words separated by commas and spaces that you do not understand, and put them in the correct order. You can enter up to 5 words at a time.")
        await bot.send_message(message.chat.id, "Click 'Get Meaning' to get started.", reply_markup=getMnKeyboard)

        startButton = KeyboardButton("Start Generating Questions")

        getQnKeyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False).add(startButton,
                                                                                               KeyboardButton(
                                                                                                   'Get Meaning'),
                                                                                               KeyboardButton(
                                                                                                   'Translate previous bot message')
                                                                                               )

        await bot.send_message(message.chat.id, "Click 'Start Generating Questions' to start generating questions.",
                               reply_markup=getQnKeyboard)
        await store_bot_message(tid, f"Here are the words on the topic of the lesson:\n{str_}")
        await store_bot_message(tid, "Click 'Get Meaning' to get started.")
        await store_bot_message(tid, f"If you have questions about the meanings of words,"
                                     f" then click the 'Get Meaning' button below,"
                                     f" and enter words separated by commas and spaces that you do not understand")
        await store_bot_message(tid, "Click 'Start Generating Questions' to start generating questions.")


    @dp.message_handler(lambda message: message.text == "Get Meaning")
    async def get_meaning(message):
        await clear_bot_message(message.from_id)
        await bot.send_message(message.chat.id,
                               "Enter words separated by commas and spaces that you do not understand,"
                               " and put them in the correct order")
        await store_bot_message(message.from_id,
                                "Enter words separated by commas and spaces that you do not understand,"
                                " and put them in the correct order")


    @dp.message_handler()
    async def process_text(message):
        user_id = message.from_user.id
        global users_and_they_topics

        if user_id not in users_and_they_topics:
            await set_topic(message)
            return

        words = users_and_they_topics[user_id][0]

        if message.text == "Get Meaning":
            await get_meaning(message)
            return

        elif message.text == "Start Generating Questions":
            await clear_bot_message(message.from_id)
            await generate_question(message)
            return

        elif message.text == 'Translate previous bot message':
            await translate(message.from_id)

        elif users_and_they_topics[user_id][2] == False:
            await clear_bot_message(message.from_id)

            words_to_define = [word.capitalize().strip() for word in message.text.split(",")]

            defined_words = []
            undefined_words = []
            for word in words_to_define:
                defined_words.append(word)

            for word in defined_words:
                response = openai.Completion.create(
                    engine="text-davinci-002",
                    prompt=f"Provide a definition for the word '{word}'.",
                    max_tokens=1000,
                    n=1,
                    stop=None,
                    temperature=0.5,
                )
                definition = response["choices"][0]["text"].strip()

                await bot.send_message(message.chat.id, f"{word}: {definition}")
                await store_bot_message(message.from_id, f"{word}: {definition}")

        else:
            question = users_and_they_topics[user_id][3][0]
            ans = users_and_they_topics[user_id][3][1]
            cancelButton = KeyboardButton("Cancel")
            getQKeyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False).add(cancelButton,
                                                                                                  KeyboardButton(
                                                                                                      'Translate previous bot message'))
            if message.text == "Cancel":
                users_and_they_topics[2] = False
                await clear_bot_message(message.from_id)
                await bot.send_message(message.chat.id, f"The lesson is completed, thanks for using,"
                                                        f" You answered correctly on {users_and_they_topics[user_id][3][2]}"
                                                        f" of {users_and_they_topics[user_id][3][3] - 1} questions. "
                                                        "if you want to start a new one, just select the topic of a new lesson")
                users_and_they_topics.pop(message.from_id)
                #print(users_and_they_topics)

                keyboard = InlineKeyboardMarkup()
                response = openai.Completion.create(
                    engine="text-davinci-002",
                    prompt=f"Create me 5 base thing themes",
                    max_tokens=1000,
                    n=1,
                    stop=None,
                    temperature=0.5,
                )
                users_and_they_topics[user_id][3] = []
                topics = response["choices"][0]["text"].strip().split("\n")
                if len(topics) > 5:
                    for i in topics[:5]:
                        keyboard.add(InlineKeyboardButton(i, callback_data=f"set_topic:{i}"))
                else:
                    for i in topics:
                        keyboard.add(InlineKeyboardButton(i, callback_data=f"set_topic:{i}"))
                keyboard.add(InlineKeyboardButton("Set your Topic", callback_data="set_topic"))
                await bot.send_message(message.chat.id, "Select an topic:", reply_markup=keyboard)
                await store_bot_message(message.from_id, "The lesson is completed, thanks for using,"
                                                         " if you want to start a new one, just select the topic of a new lesson")
                await store_bot_message(message.from_id, "Select an topic:")
                return
            user_ans = message.text
            '''response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=f"Is this answer: {user_ans.lower()} correct for the given question:"
                       f" {question}? If not, write the correct answer",
                max_tokens=100,
                n=1,
                stop=None,
                temperature=0.5,
            )
            answer = response["choices"][0]["text"].strip()'''
            if user_ans.lower() == ans.lower():
                if len(users_and_they_topics[user_id][3]) == 2:
                    users_and_they_topics[user_id][3].append(1)
                else:
                    users_and_they_topics[user_id][3][2] = users_and_they_topics[user_id][3][2] + 1
                    users_and_they_topics[user_id][3][3] = users_and_they_topics[user_id][3][3] + 1
                await clear_bot_message(message.from_id)
                await bot.send_message(message.chat.id, f"Your answer is correct", reply_markup=getQKeyboard)
                await store_bot_message(message.from_id, f"Your answer is correct")
                await generate_question(message)
                return
            else:
                await clear_bot_message(message.from_id)
                users_and_they_topics[user_id][3][3] = users_and_they_topics[user_id][3][3] + 1
                await bot.send_message(message.chat.id,
                                       f"Your answer is not correct, the correct answer is {ans}",
                                       reply_markup=getQKeyboard)
                await store_bot_message(message.from_id, f"Your answer is not correct, the correct answer is {ans}")
                await generate_question(message)
                return


    async def generate_question(message):
        user_id = message.from_user.id
        global users_and_they_topics

        if user_id not in users_and_they_topics:
            await bot.send_message(message.chat.id, "You haven't set a topic yet. Please select an option:",
                                   reply_markup=InlineKeyboardMarkup().add(
                                       InlineKeyboardButton("Set Topic", callback_data="set_topic")
                                   ))
            return

        words = users_and_they_topics[user_id][0]
        topic = users_and_they_topics[user_id][1]
        users_and_they_topics[user_id][2] = True
        word = random.choice(words)
        prompt = f"Word: {word}. Without naming this word, generate a question on it and ask what it is"

        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=100,
            n=1,
            stop=None,
            temperature=0.65,
        )
        question = response["choices"][0]["text"].strip()

        if len(users_and_they_topics[user_id][3]) == 4:
            users_and_they_topics[user_id][3] = [question, word, users_and_they_topics[user_id][3][2], users_and_they_topics[user_id][3][3]]
        else:
            users_and_they_topics[user_id][3] = [question, word, 0, 1]

        await bot.send_message(message.chat.id, question)
        await store_bot_message(message.from_id, question)


    @dp.message_handler(lambda message: message.text == "Start Generating Questions")
    async def start_generating_questions(message):
        await generate_question(message)


    @dp.message_handler(lambda message: message.text == "Cancel")
    async def cancel_generating_questions(message):
        await clear_bot_message(message.from_id)
        await bot.send_message(message.chat.id, "Canceled.")
        await store_bot_message(message.from_id, "Canceled.")




except openai.Error as e:
    # handle OpenAI-specific errors here
    print(f"Error occurred on OpenAI server: {e}")
except Exception as e:
    # handle all other exceptions here
    print(f"An error occurred: {e}")
    print(traceback.format_exc())

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
