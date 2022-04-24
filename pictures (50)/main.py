from __future__ import unicode_literals
import json
from flask import Flask, request
from flask_cors import CORS
from pymongo import MongoClient
from random import choice

app = Flask(__name__)
app.debug = True
CORS(app)

client = MongoClient(
    "mongodb://vcodebackend:vcodebackend@194.67.111.141:27017/vcodebackend?authSource=vcodebackend&readPreference"
    "=primary&directConnection=true&ssl=false")
quiz_collecion = client["vcodebackend"]["quiz"]


@app.route('/')
def index():
    return '<h1>Webhook URL = https://127.0.0.1:5000/webhook</h1>'


@app.route('/marusya', methods=['POST', 'GET'])
def marusya():
    return "Marusya"


questions = [
    "Вам нравится gamedev?",
    "Вам нравится Java?",
    "Вам нравится Mobile?",
    "Вам нравится PHP?",
    "Вам нравится Backend?",
    "Вам нравится Маруся?",
    "Вам нравятся чат-боты?",
    "Вам нравятся VK Mini Apps?",
    "Квиз окончен!"
]
quiz_answers = [
    "Gamedev",
    "Java",
    "Mobile",
    "PHP",
    "Backend",
    "Маруся",
    "Чат-боты",
    "VK Mini Apps"
]
quiz_images = {
    "Gamedev": 457239019,
    "Java": 457239024,
    "Mobile": 457239021,
    "PHP": 457239023,
    "Backend": 457239017,
    "Маруся": 457239020,
    "Чат-боты": 457239018,
    "VK Mini Apps": 457239022
}


@app.route('/webhook', methods=['POST'])
def webhook():
    card = {}
    button = {}
    end_session = False
    text = ''

    user_id = request.json["session"]["user_id"]
    if quiz_collecion.count_documents({"user_id": user_id}) == 0:
        quiz_collecion.insert_one({'user_id': user_id, "status": 0})
        text = "Привет! Я чат-бот Маруся, созданный командой FTIT. Ты можешь посмотреть, что я умею с помощью команд:\n" \
               "FTIT вездекод, квиз, мини-приложение"
    else:
        if request.json['request']['command'].lower() == "квиз" and \
                not quiz_collecion.find_one({"user_id": user_id})["status"]:
            quiz_collecion.update_one({'user_id': user_id},
                                      {'$set': {"user_id": user_id,
                                                "status": 2,
                                                "answers": [],
                                                "question": 0}},
                                      upsert=True)
            text = "Квиз начался! Отвечайте на вопросы да/нет. Или введите 'квиз', чтобы остановить квиз.\n"
        if quiz_collecion.find_one({"user_id": user_id})["status"] in [1, 2]:
            question_num = quiz_collecion.find_one({"user_id": user_id})["question"]
            user_answer = request.json['request']['command'].lower().strip()
            if quiz_collecion.find_one({"user_id": user_id})["status"] == 1:
                question_num += 1
            if user_answer in ["да", "нет", "квиз"]:
                if question_num == 8:
                    text = "<speaker audio='marusia-sounds/game-win-1'/>Вам подходит следующая категория:\n"
                else:
                    text += f"Вопрос {question_num + 1}. " + questions[question_num]

                quiz_collecion.update_one({'user_id': user_id},
                                          {'$inc': {"question": 1}})
                if user_answer == "да":
                    quiz_collecion.update_one({'user_id': user_id},
                                              {'$push': {"answers": 1}})
                elif user_answer == "нет":
                    quiz_collecion.update_one({'user_id': user_id},
                                              {'$push': {"answers": 0}})
                if question_num == 8:
                    answers = quiz_collecion.find_one({"user_id": user_id})["answers"]
                    if sum(answers):
                        chosen_answers = []
                        for i in range(8):
                            if answers[i]:
                                chosen_answers.append(quiz_answers[i])
                        chosen_answer = choice(chosen_answers)
                    else:
                        chosen_answer = choice(quiz_answers)

                    card = {"type": "BigImage",
                            "image_id": quiz_images[chosen_answer]
                            }
                    text += chosen_answer
                    text += "\nУдачи на вездекоде!"
                    quiz_collecion.update_one({'user_id': user_id},
                                              {'$set': {"user_id": user_id,
                                                        "status": 0}})

                elif user_answer == "квиз" and quiz_collecion.find_one({"user_id": user_id})["status"] in [1, 2]:
                    if quiz_collecion.find_one({"user_id": user_id})["status"] == 1:
                        text = "Квиз завершен!"
                    quiz_collecion.update_one({'user_id': user_id},
                                              {'$set': {"user_id": user_id,
                                                        "status": quiz_collecion.find_one({"user_id": user_id})[
                                                                      "status"] - 1,
                                                        "answers": [],
                                                        "question": 0}},
                                              upsert=True)
            else:
                text = "Неверный формат ответа! Отвечайте только да/нет или введите 'квиз', чтоб остановить квиз."

        elif {"ftit", "вездеход"}.issubset(request.json['request']['command'].lower().split()):
            text = "Привет вездекодерам!"
        elif request.json['request']['command'].lower().replace('-', ' ') == "мини приложение":
            text = "Прикрепляю ссылку на мини-приложение и мой любимый и очень жизненный мем."

            card = {
                'type': 'BigImage',
                'image_id': 457239025
            }
            button = {
                "title": "Открыть мини-приложение",
                "action": {
                    "type": "open_mini_app",
                    "app_id": 7543093,
                    "url": "https://vk.com/app7543093"
                }
            }
        elif request.json['request']['command'].lower() == "открыть мини-приложение":
            card = {
                'type': 'MiniApp',
                'url': 'https://vk.com/app7543093'}
            text = "Открываю мини-приложение..."
        else:
            text = "Вы ввели: " + request.json['request']['command'].lower() \
                   + "\nАктуальные команды: квиз, мини-приложение, FTIT вездекод"

    tts = ""
    brackets_count = 0
    for i in text:
        if i == "<":
            brackets_count += 1
        elif i == ">":
            brackets_count -= 1
        elif brackets_count == 0:
            tts += i

    tts, text = text, tts
    response = {
        "version": request.json['version'],
        "session": request.json['session'],
        "response": {
            "end_session": end_session,
            "text": text,
            "tts": tts,
            "card": card,
            "buttons": [button]
        }
    }
    if not button:
        response["response"]["buttons"] = []
    return json.dumps(response, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    app.run(port=7000)
