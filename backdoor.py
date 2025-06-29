from database import Database
from ya_gpt import get_embedding, ask_ya_gpt
import numpy as np
from scipy.spatial.distance import cosine
from collections import Counter
import threading
import io

K = 3
DIST = 0.82
CNT_GEN = 6
db = Database("qdb.db")

class Answer:
    answer = None
    priority = None
    doctor = None
    
    def __init__(self, answer_=None, priority_=None, doctor_=None):
        self.answer = answer_
        self.priority = priority_
        self.doctor = doctor_
        
class Response:
    question = None
    priority = 0
    index = 0
    answer = None
    doctor = None
    
    def __init__(self, index_, question_=None, priority_=None, answer_=None, doctor_=None):
        self.index = index_
        self.question = question_
        self.priority = priority_
        self.answer = answer_
        self.doctor = doctor_


def cosine_similarity(embedding1, embedding2):
    return 1 - cosine(embedding1, embedding2)

def find_nearest_answer(embedding) -> Answer:
    all_emb_data = db.get_embeddings()
    all_emb_data = np.array(all_emb_data).reshape(-1, 2)
    all_inds = [int(x) for x in all_emb_data[:, 0]]
    all_emb = list(all_emb_data[:, 1])
    
    # Вычисляем nearest
    nearest = []
    for i in range(len(all_emb)):
        # Преобразование бинарных данных обратно в NumPy массив
        buffer = io.BytesIO(all_emb[i])  # Создаем буфер из бинарных данных
        array = np.load(buffer, allow_pickle=False) # Восстанавливаем массив из буфера
        
        cur_dist = cosine_similarity(array, embedding) # Считаем косинусное расстояние
        # Пересчитываем nearest
        if len(nearest) < K:
            nearest.append((all_inds[i], cur_dist))
        else:
            min_index, min_dist = min(enumerate(nearest), key=lambda x: x[1][1])
            if min_dist[1] < cur_dist:
                nearest[min_index] = (all_inds[i], cur_dist)

    # если ничего не нашли пересылаем врачу
    if len(nearest) == 0:
        return Answer()

    # выписываем все вопросы
    nearest_questions = []
    for index, dist in nearest:
        nearest_questions.append(db.get_question(index))
    
    # вычисляем средний priority
    priority = 0
    for question in nearest_questions:
        priority = priority + int(question[3])
    priority //= len(nearest_questions)
    
    # смотри если самый близкий далеко, или пока мало ответов просим ответить врача (не находим норм ответ)
    max_index, max_dist = max(enumerate(nearest), key=lambda x: x[1][1])
    print(max_dist)
    if max_dist[1] < DIST or len(nearest) < K:
        return Answer(priority_=priority)
    
    # Ищем самого частого врача
    # Извлекаем строки из позиции с индексом 1
    doctor_strings = [t[5] for t in nearest_questions]
    # Подсчитываем частоту каждой строки
    frequency = Counter(doctor_strings)
    # Нахождение наиболее частой строки
    doctor, count = frequency.most_common(1)[0]
    
    # Формируем ответ
    system = "переформулируй ответ на вопрос."
    text = ""
    for question in nearest_questions:
        text += question[6] + '\n'
    
    print(text + "\nsdfsdfdsfsdfsdf")
    # пытаемся сделать выжимку ответов
    result_answer = ""
    # try:
    #    result_answer = ask_ya_gpt(system, text)['result']['alternatives'][0]['message']['text']
    # except:
    #    result_answer = nearest_questions[0][6]
    result_answer = nearest_questions[0][6]
    return Answer(answer_=result_answer, doctor_=doctor, priority_=priority)

def gen_alternative_question(question) -> str:
    system = "Ты врач, тебе нужно переформулировать вопрос пациента."
    try:
        return ask_ya_gpt(system=system, text=question)['result']['alternatives'][0]['message']['text']
    except:
        return question


def create_similar_questions(username, question, index, result, cnt_gen=CNT_GEN):
    # генерируем CNT_GEN похожих вопросов
    question_new = question
    index_new = index
    for i in range(cnt_gen):
        question_new = gen_alternative_question(question_new) # получаем новый вопрос
        index_new = db.add_question(username, question_new) # получаем id впороса
        print(f"Вопроос {i} c id {index_new} сгенерирован: {question_new}")
        
        # получаем вектор чисел
        embedding_new = get_embedding(question_new)
        
        # преобразуем вектор в blob
        buffer = io.BytesIO()
        np.save(buffer, embedding_new, allow_pickle=False)  # Сохраняем массив в буфер
        embedding_new_binary = buffer.getvalue()  # Получаем бинарные данные из буфера
        
        # записываем в базу
        db.set_question(index=index_new,
                        embedding=embedding_new_binary,
                        priority=result.priority,
                        doctor=result.doctor,
                        answer=result.answer
        )
        print(f"Cгенерированный вопрос {i} записан в базу.")

def main_start(username, question) -> Response:
    # добавляем вопрос в базу
    index = db.add_question(username, question)
    print(f"Вопрос в базу добавлен, id {index}")
    
    # получаем вектор чисел
    embedding = get_embedding(question)
    # преобразуем вектор в blob
    buffer = io.BytesIO()
    np.save(buffer, embedding, allow_pickle=False)  # Сохраняем массив в буфер
    embedding_binary = buffer.getvalue()  # Получаем бинарные данные из буфера
    
    # сохраняем этот binary embedding в базу
    db.set_question(index=index, embedding=embedding_binary)
    print(f"Embedding в базу записан, id {index}")
    
    # получаем объект Answer (priority, answer, doctor)
    result = find_nearest_answer(embedding)
    print(f"Ответ получен: ", result.__dict__)
    
    # если ответ не нашли, то выходим и отсылаем боту
    if result.answer == None:
        print("Пока у нас не достаточно данных, отправляем вопрос врачу.")
        print(db.get_question(index=index))
        return Response(index_=index, priority_=result.priority, question_=question)
    # если ответ нашли
    # записываем в базу
    db.set_question(index=index, answer=result.answer, doctor=result.doctor, priority=result.priority)
    print(f"Ответ записан в базу.")
    
    # генерируем CNT_GEN похожих вопросов (запускаем отдельный поток)
    create_similar_questions(username, question, index, result, CNT_GEN//3)
    
    print("Выдаём боту ответ.")
    return Response(index_=index, question_=question, priority_=result.priority, answer_=result.answer, doctor_=result.doctor)

def get_doctor_answer(index, answer, priority, doctor):
    # записываем ответ в базу
    db.set_question(index=index, answer=answer, doctor=doctor, priority=priority)
    print(f"Ответ записан в базу.")
    
    # получаем данные по id вопроса
    question_tuple = db.get_question(index)
    
    # приводим в удобный формат данные
    username = question_tuple[1]
    question = question_tuple[2]
    result = Answer(answer_=answer, priority_=priority, doctor_=doctor)
    
    # генерируем CNT_GEN похожих вопросов (запускаем отдельный поток)
    create_similar_questions(username, question, index, result)

#if __name__ == "__main__":
#    pass
    # main_start("sdfsd", "Что делать если оторвало руку?")
    # get_doctor_answer(141, "Надо срочно остановить кровотечение, и вызывать скорую помощь.", 10, None)

    
    
    
    
    
    
    
    