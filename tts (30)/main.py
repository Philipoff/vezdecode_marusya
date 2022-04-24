from __future__ import unicode_literals
import json
from flask import Flask, request
from flask_cors import CORS
from pymongo import MongoClient
import ssl

app = Flask(__name__)
app.debug = True
CORS(app)

ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
ctx.load_cert_chain('cert.pem', 'key.pem')

client = MongoClient(
    "mongodb://vcodebackend:vcodebackend@194.67.111.141:27017/vcodebackend?authSource=vcodebackend&readPreference"
    "=primary&directConnection=true&ssl=false")
quiz_collecion = client["vcodebackend"]["quiz"]


@app.route('/')
def index():
    return '<h1>Webhook URL = https://127.0.0.1:5000/webhook</h1>'


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


@app.route('/webhook', methods=['POST'])
def webhook():
    card = {}
    buttons = []
    end_session = False
    text = ''

    user_id = request.json["session"]["user_id"]
    if request.json["session"]["new"]:
        quiz_collecion.insert_one({'user_id': user_id, "status": 0})
    if request.json['request']['original_utterance'].lower() == "квиз" and \
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
        user_answer = request.json['request']['original_utterance'].lower().strip()
        if quiz_collecion.find_one({"user_id": user_id})["status"] == 1:
            question_num += 1
        if user_answer in ["да", "нет", "квиз"]:
            if question_num == 8:
                text = "Вам подходят следующие категории:\n"
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
                    for i in range(8):
                        if answers[i]:
                            text += quiz_answers[i] + ", "
                    text = text[:-2] + "\nУдачи на вездекоде!"
                else:
                    text = "Вам не подходит ни одна из категорий."
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

    elif {"ftit", "вездеход"}.issubset(request.json['request']['original_utterance'].lower().split()):
        text = "Привет вездекодерам!"
    else:
        text = request.json['request']['original_utterance'].lower()

    response = {
        "version": request.json['version'],
        "session": request.json['session'],
        "response": {
            "end_session": end_session,
            "text": text,
            "tts_type": "ssml",
            "tts": "Угадайте, чей это голос? <speaker audio=marusia-sounds/game-win-1>"
        }
    }

    return json.dumps(response, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    app.run(ssl_context=ctx, port=7000)
