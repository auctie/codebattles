import sqlite3
import random
import json

class Database:
    def __init__(self, name: str = "tasks.db"):
        self.name = name
        self.create_table()

    def connect(self):
        return sqlite3.connect(self.name)

    def create_table(self):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task TEXT DEFAULT "",
                    num INTEGER DEFAULT -1,
                    answer FLOAT DEFAULT -1
                )
            """)

    def choose_random(self, task_num):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, task, answer FROM tasks WHERE num = ?", (task_num,))
            rows = cursor.fetchall()

            if not rows:
                return None

            return random.choice(rows)

    def add_task(self, tasks_list):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT OR IGNORE INTO tasks (task, num, answer) 
                VALUES (?, ?, ?)
            """, tasks_list)


if __name__ == "__main__":
    db = Database()
    tasks_dict = {
        1: ["""На вход алгоритма подаётся натуральное число N. Алгоритм строит по нему новое число R следующим образом.
1. Строится двоичная запись числа N.
2. Далее эта запись обрабатывается по следующему правилу:
a) если число чётное, то к двоичной записи числа слева дописывается 10;
б) если число нечётное, то к двоичной записи числа слева дописывается 1 и справа дописывается 01.
Полученная таким образом запись является двоичной записью искомого числа R.
3. Результат переводится в десятичную систему и выводится на экран.
Например, для исходного числа 410 = 1002 результатом является число 101002 = 2010, для исходного числа 510 = 1012 это число 1101012 = 5310
Укажите минимальное число R, которое может быть результатом работы данного алгоритма, при условии, что N больше, чем 18. В ответе запишите это число в десятичной системе счисления.""", 5, 84],
        2: ["""На вход алгоритма подаётся натуральное число N. Алгоритм строит по нему новое число R следующим образом.
1. Строится двоичная запись числа N.
2. Далее эта запись обрабатывается по следующему правилу:
a) если число N делится на 3, то к этой записи дописываются три последние двоичные цифры;
б) если число N на 3 не делится, то остаток от деления умножается на 3, переводится в двоичную запись и дописывается в конец числа.
Полученная таким образом запись является двоичной записью искомого числа R.
3. Результат переводится в десятичную систему и выводится на экран.
Например, для исходного числа 610 = 1102 результатом является число 1101102 = 5410, а для исходного числа 410 = 1002 это число 100112 = 1910
Укажите максимальное число N, после обработки которого с помощью этого алгоритма получается число R, ближайшее к 130.""", 5, 31]
    }

    with open("tasks.json", "w", encoding="utf-8") as f:
        json.dump(tasks_dict, f, ensure_ascii=False, indent=4)

    with open('tasks.json', 'r', encoding='utf-8') as f:
        data_list = [tuple(v) for v in json.load(f).values()]
    db.add_task(data_list)



