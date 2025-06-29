import sqlite3
import numpy as np


class Database:
    db_name = ""
    def __init__(self, db_name_):
        self.db_name = db_name_
        # Устанавливаем соединение с базой данных
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()

        # Создаем таблицу Users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Questions (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                question TEXT NOT NULL,
                priority INTEGER DEFAULT 0,
                embedding BLOB,
                doctor VARCHAR(256),
                answer TEXT
            )
        ''')

        # Сохраняем изменения и закрываем соединение
        connection.commit()
        connection.close()
    
    def get_embeddings(self) -> list:
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()

        # Берём все уже существующие embeddings
        cursor.execute('SELECT id, embedding FROM Questions WHERE answer IS NOT NULL AND embedding IS NOT NULL')
        results = cursor.fetchall()
        
        connection.close()
        
        return np.array(results)
        
    def add_question(self, username, question) -> int:
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()

        # Добавляем новый вопрос
        cursor.execute('INSERT INTO Questions (username, question) VALUES (?, ?)', (username, question))

        # Сохраняем изменения и закрываем соединение
        connection.commit()
        lst_index = cursor.lastrowid
        connection.close()
        
        return lst_index
    
    def get_question(self, index):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        
         # Берём все уже существующие embeddings
        cursor.execute('SELECT * FROM Questions WHERE id = ?', (index, ))
        results = cursor.fetchone()
        
        connection.close()
        
        return results
    
    def set_question(self, index, **kwargs):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()

        # Обновляем запись
        for key, value in kwargs.items():
            if key not in ["embedding", "doctor", "priority", "answer"] or value == None:
                continue
            cursor.execute(f'UPDATE Questions SET {key} = ? WHERE id = ?', (value, index))
        
        # Сохраняем изменения и закрываем соединение
        connection.commit()
        connection.close()
    
    def check_doctor(self, doctor) -> bool:
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()

        ans = False
        # Проверяем, есть ли такой доктор
        cursor.execute('SELECT id FROM Questions WHERE doctor = ?', (doctor, ))
        results = cursor.fetchall()
        if len(results) > 0:
            ans = True
        
        # Сохраняем изменения и закрываем соединение
        connection.commit()
        connection.close()
        return ans