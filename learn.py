import os
from backdoor import db, Answer
from ya_gpt import get_embedding, ask_ya_gpt
import io
import numpy as np

CNT_GEN = 3
directory = os.getcwd() + "/learn_q"
print(f"Текущая рабочая директория: {directory}")

def gen_alternative_question(question) -> str:
    system = "Переформулируй предложение."
    try:
        return ask_ya_gpt(system=system, text=question)['result']['alternatives'][0]['message']['text']
    except:
        return question

def create_similar_questions(username, question, result, cnt_gen=CNT_GEN):
    # генерируем CNT_GEN похожих вопросов
    question_new = question
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


for filename in os.listdir(directory):
    file_path = os.path.join(directory, filename)
    if os.path.isfile(file_path) and filename.endswith('.txt'):  # Проверяем расширение
        if "ответы" in filename:
            continue
        doctor = filename.split('.')[0]
        if db.check_doctor(doctor):
            print("YAAAAAA\n\n\n")
            continue
        with open(file_path, 'r') as f:
            questions = [line.strip() for line in f if line.strip()]
        file_path_answers = os.path.join(directory, doctor + " — ответы.txt")
        with open(file_path_answers, 'r') as f:
            answers = [line.strip() for line in f if line.strip()]
        
        for question, answer in zip(questions, answers):
            index = db.add_question("None", question) # получаем id впороса
            # получаем вектор чисел
            try:
                embedding = get_embedding(question)
            except:
                continue
            
            # преобразуем вектор в blob
            buffer = io.BytesIO()
            np.save(buffer, embedding, allow_pickle=False)  # Сохраняем массив в буфер
            embedding_binary = buffer.getvalue()  # Получаем бинарные данные из буфера
            
            db.set_question(index=index,
                            embedding=embedding_binary,
                            priority=4,
                            doctor=doctor,
                            answer=answer
            )
            
            create_similar_questions("None", question, Answer(answer, 4, doctor), 2)
        
        
        
        
        