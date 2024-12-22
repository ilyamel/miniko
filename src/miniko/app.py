"""
A simple daily tasks journal for productivity
"""
import os
import toga
import sqlite3
from toga import MainWindow, Box, Button, Table, TextInput, Label
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from datetime import datetime as dt

DATABASE_NAME = "miniko.db"

class SQLite:
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self.connection: sqlite3.Connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.cursor: sqlite3.Cursor = self.connection.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.connection.commit()
        else:
            self.connection.rollback()
        self.connection.close()

class StorageHandler:
    def __init__(self, app_path):
        self.db_path = app_path + "/" + DATABASE_NAME
        with SQLite(self.db_path) as db:
            db.cursor.execute("""CREATE TABLE IF NOT EXISTS todo_items
                              (id INTEGER PRIMARY KEY, task TEXT, is_done TEXT, created TEXT, done TEXT)""")

    def add_task(self, task, created):
        with SQLite(self.db_path) as db:
            db.cursor.execute(f"""INSERT INTO todo_items (task, is_done, created)
                           VALUES ('{task}', 'N', '{created}')""")
            task_id = db.cursor.lastrowid
        return task_id

    def get_all_tasks(self):
        with SQLite(self.db_path) as db:
            db.cursor.execute(f"""SELECT id, task, is_done, created, done FROM todo_items""")
            in_progress_tasks, finished_tasks = [], []
            for row in db.cursor.fetchall():
                if row["is_done"] == "N":
                    in_progress_tasks.append([row["id"], row["task"], row["created"]])
                else:
                    finished_tasks.append([row["id"], row["task"], row["created"], row["done"]])

        return in_progress_tasks, finished_tasks

    def move_task_to_done(self, task_id, done):
        with SQLite(self.db_path) as db:
            db.cursor.execute(f"""UPDATE todo_items SET is_done = 'Y', done = '{done}'
                           WHERE id = {task_id}""")
        return task_id

    def delete_task(self, task_id):
        with SQLite(self.db_path) as db:
            db.cursor.execute(f"""DELETE FROM todo_items
                           WHERE id = {task_id}""")
        return task_id


class Miniko(toga.App):
    def __init__(self):
        super().__init__()


    def startup(self):
        app_path = os.path.dirname(os.path.abspath(__file__))
        print(app_path)
        self.storageHandler = StorageHandler(app_path)
        # Get persisted data
        in_progress_tasks, finished_tasks = self.storageHandler.get_all_tasks()

        # Main box
        main_box = Box(style=Pack(direction=COLUMN, padding=20, background_color='#f1f1f1'))

        # Input box
        input_box = Box(style=Pack(direction=ROW, padding=5))
        self.input_text = TextInput(style=Pack(flex=1, padding=(0, 0, 5, 0)), on_confirm=self.add_todo_item)
        input_box.add(self.input_text)

        # Lists box
        lists_box = Box(style=Pack(direction=ROW, flex=1, padding=5))

        # To Do list
        todo_box = Box(style=Pack(direction=COLUMN, flex=1, padding=(0, 0, 0, 5)))
        todo_label = Label('To Do', style=Pack(padding=(0, 0, 5, 0), font_weight='bold'))
        self.todo_list = Table(
            headings=["Task ID", "Task", "Created"],
            data=[],
            style=Pack(flex=1),
            on_activate=self.move_to_done
        )
        todo_box.add(todo_label)
        todo_box.add(self.todo_list)

        self.display_in_progress_tasks(in_progress_tasks)

        # Small span
        span = Box(style=Pack(width=10))

        # Done list
        done_box = Box(style=Pack(direction=COLUMN, flex=1, padding=(5, 0, 0, 0)))
        done_label = Label('Done', style=Pack(padding=(0, 5, 0, 0), font_weight='bold'))
        self.done_list = Table(
            headings=["Task ID", "Task", "Created", "Done"],
            data=[],
            style=Pack(flex=1),
            on_activate=self.delete_task
        )
        done_box.add(done_label)
        done_box.add(self.done_list)

        lists_box.add(todo_box)
        lists_box.add(span)
        lists_box.add(done_box)

        self.display_finished_tasks(finished_tasks)

        main_box.add(input_box)
        main_box.add(lists_box)

        self.main_window = MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()

    def display_in_progress_tasks(self, todo_items):
        for item in todo_items:
            self.todo_list.data.append(item)

    def display_finished_tasks(self, done_items):
        for item in done_items:
            self.done_list.data.append(item)

    def add_todo_item(self, widget):
        if self.input_text.value:
            now = dt.now().strftime("%Y/%m/%d, %H:%M")

            task_id = self.storageHandler.add_task(self.input_text.value, now)

            self.todo_list.data.append([task_id, self.input_text.value, now])
            self.input_text.value = ''
            self.todo_list.refresh()

    def move_to_done(self, widget, row):
        now = dt.now().strftime("%Y/%m/%d, %H:%M")

        self.storageHandler.move_task_to_done(row.task_id, now)

        self.done_list.data.append([row.task_id, row.task, row.created, now])
        self.todo_list.data.remove(row)
        self.todo_list.refresh()
        self.done_list.refresh()
        return True  # Confirm the deletion

    def delete_task(self, widget, row):
        if row is not None:
            self.storageHandler.delete_task(row.task_id)

            widget.data.remove(row)
            widget.refresh()


def main():
    return Miniko()
