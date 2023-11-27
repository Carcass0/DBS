"""
OVERALL TO-DO:

REFORMAT
INCREASE READABILITY
IMPLEMENT LOGGING
TEST PERFORMANCE WITH MAXIMIZED SERVER SIDE EXECUTION
ADD CRUD WITH PARENT TABLES
REMOVE NOT NULL RESTRICTIONS IN THE DATABASE
"""

from dotenv import load_dotenv
from os import getenv
from sys import argv
from typing import Any
from time import sleep

import psycopg2
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QTableWidgetItem
from PyQt6.QtCore import Qt

from interface import Ui_MainWindow


BOOK_TABLE: tuple[str, ...] = ('book', 'unique_id', 'fam', 'name', 'otch', 'street', 'house', 'korp', 'apart', 'mob')
FAMILY_TABLE: tuple[str, ...] = ('family', 'f_id', 'f_val')
NAME_TABLE: tuple[str, ...] = ('name', 'n_id', 'n_val')
OTCHESTVO_TABLE: tuple[str, ...] = ('otchestvo', 'o_id', 'o_val')
STREETS_TABLE: tuple[str, ...] = ('streets', 's_id', 's_val')
PARENT_TABLES: tuple[tuple[str,...], ...] = (FAMILY_TABLE, NAME_TABLE, OTCHESTVO_TABLE, STREETS_TABLE)


class mainwindow(QtWidgets.QMainWindow):
    """
    TO-DO:
    SWITCH TABLEWIDGET TO TABLEVIEW
    MERGE GET_FKEY_VALUES AND GET_SPECIFIC_FKEY
    MAINTAIN CONSISTENT ORDER OF ENTRIES WHEN UPDATING
    """
    def __init__(self, myconnection:psycopg2.extensions.connection, mycursor: psycopg2.extensions.cursor) -> None:
        super(mainwindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.book_table.setRowCount(0)
        self.ui.book_table.setColumnCount(8)
        self.ui.book_table.setHorizontalHeaderLabels(('Фамилия', 'Имя', 'Отчество', 'Улица', 'Дом', 'Корпус', 'Квартира',
                                                       'Телефон'))
        self.ui.book_table.setColumnWidth(0, 200)
        self.ui.book_table.setColumnWidth(1, 200)
        self.ui.book_table.setColumnWidth(2, 200)
        self.ui.book_table.setColumnWidth(3, 200)
        self.ui.book_table.setColumnWidth(4, 80)
        self.ui.book_table.setColumnWidth(5, 80)
        self.ui.book_table.setColumnWidth(6, 80)
        self.ui.book_table.setColumnWidth(7, 200)
        self.mycursor:psycopg2.extensions.cursor = mycursor
        self.myconnection: psycopg2.extensions.connection = myconnection
        self.__populate()
        self.ui.add_button.clicked.connect(lambda: self.__add_entry())
        self.ui.book_table.itemChanged.connect(lambda x: self.__update_entry(x))
        self.ui.delete_button.clicked.connect(lambda: self.__deletion_mode())
        self.ui.search_button.clicked.connect(lambda: self.__perform_search())
        self.ui.search_reset_button.clicked.connect(lambda: self.__reset_search())
        self.lines: list[QtWidgets.QLineEdit] = (self.ui.last_name_line, self.ui.name_line, self.ui.middle_name_line, self.ui.street_line,
                       self.ui.house_line, self.ui.korp_line, self.ui.apart_line)
        self.ui.action_2.triggered.connect(lambda: self.__update_in_parents())
        self.ui.add_action.triggered.connect(lambda: self.__add_to_parents())
        self.ui.search_reset_button.setEnabled(False)

    def __populate(self) -> None:
        self.mycursor.execute(f'SELECT count(*) AS exact_count FROM {BOOK_TABLE[0]};')
        tablesize = self.mycursor.fetchall()[0][0]
        self.ui.book_table.setRowCount(tablesize)
        self.mycursor.execute("""SELECT family.f_val, n_val, o_val, s_val, house, korp, apart, mob
                                FROM book JOIN family ON book.fam=family.f_id JOIN name ON book.name=n_id
                                JOIN otchestvo ON book.otch=o_id JOIN streets ON book.street=s_id""")
        data: list[tuple[Any, ...]] = self.mycursor.fetchall()
        a: function = lambda x: x.strip() if type(point)==str else "{0:.0f}".format(x)
        for i,entry in enumerate(data):
            for j, point in enumerate(entry):
                self.ui.book_table.setItem(i, j, QTableWidgetItem(a(point)))
                self.ui.book_table.item(i,j).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    
    def __get_fkey_values(self, data: list[str, str, str, str, str, str, str, str, str]) -> list[int, int, int, int]:
        numbers: list[int, int, int, int] = []
        values: list[str, str, str, str] = [data[1], data[2], data[3], data[4]]
        for i, parent_table in enumerate(PARENT_TABLES):
            self.mycursor.execute(f"SELECT {parent_table[1]} FROM {parent_table[0]} WHERE {parent_table[2]} = '{values[i]}';")
            print(self.mycursor.fetchall())
            if self.mycursor.fetchall():
                numbers.append(self.mycursor.fetchall()[0][0])
            else:
                self.mycursor.execute(f"""INSERT INTO {parent_table[0]} ({parent_table[1]}, {parent_table[2]}) VALUES 
                                        (DEFAULT, '{values[i]}')""")
                self.myconnection.commit()
                self.mycursor.execute(f"SELECT last_value FROM {parent_table[0]}_{parent_table[1]}_seq;")
                numbers.append(self.mycursor.fetchall()[0][0])
        return numbers
            
    def __add_entry(self) -> None:
        """TO-DO: SANITIZE INPUTS, ADD CLIENTSIDE TYPECHECKING, ADD SUPPORT FOR INCOMPLETE ADDITION, SWAP TO COMBO BOXES"""
        self.ui.book_table.itemChanged.disconnect()
        new_data = (self.ui.book_table.rowCount()+1, self.ui.last_name_line.text(), self.ui.name_line.text(),
                    self.ui.middle_name_line.text(), self.ui.street_line.text(), self.ui.house_line.text(),
                    self.ui.korp_line.text(), int(self.ui.apart_line.text()), self.ui.phone_line.text())
        fkey_values: list[int, int, int, int] = self.__get_fkey_values(new_data)
        self.mycursor.execute(f"""INSERT INTO {BOOK_TABLE[0]} ({BOOK_TABLE[1]}, {BOOK_TABLE[2]}, {BOOK_TABLE[3]}, 
                              {BOOK_TABLE[4]}, {BOOK_TABLE[5]}, {BOOK_TABLE[6]}, {BOOK_TABLE[7]}, {BOOK_TABLE[8]}, 
                              {BOOK_TABLE[9]}) VALUES (DEFAULT, {fkey_values[0]}, {fkey_values[1]}, {fkey_values[2]}, 
                              {fkey_values[3]}, '{new_data[5]}', '{new_data[6]}', {new_data[7]}, '{new_data[8]}')""")
        self.myconnection.commit()
        self.ui.book_table.setRowCount(new_data[0])
        for i, entry in enumerate(new_data[1:]):
            self.ui.book_table.setItem(new_data[0]-1, i, QTableWidgetItem(entry))
            self.ui.book_table.item(new_data[0]-1, i).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ui.book_table.itemChanged.connect(lambda x:  self.__update_entry(x))
    
    def __get_specific_fkey(self, data: list[str]) -> int:
        parent_table: list[str] = PARENT_TABLES[data[0]]
        self.mycursor.execute(f"SELECT {parent_table[1]} FROM {parent_table[0]} WHERE {parent_table[2]} = '{data[2]}';")
        print(self.mycursor.fetchall())
        if self.mycursor.fetchall():
            return self.mycursor.fetchall()[0][0]
        else:
            self.mycursor.execute(f"""INSERT INTO {parent_table[0]} ({parent_table[1]}, {parent_table[2]}) VALUES 
                                    (DEFAULT, '{data[2]}')""")
            self.myconnection.commit()
            self.mycursor.execute(f"SELECT last_value FROM {parent_table[0]}_{parent_table[1]}_seq;")
            return self.mycursor.fetchall()[0][0]

    def __update_entry(self, item:QTableWidgetItem) -> None:
        new_data: list[int, int, str] = [item.column(), item.row(), item.text()]
        if new_data[0] < 4:
            new_data[2] = self.__get_specific_fkey(new_data)
        self.mycursor.execute(f"""UPDATE {BOOK_TABLE[0]} SET {BOOK_TABLE[new_data[0]+2]} = {"" if new_data[0]==7 else "'"}{new_data[2]}{"" if new_data[0]==7 else "'"}
                               WHERE {BOOK_TABLE[1]} = {new_data[1]+1};""")
        self.myconnection.commit()

    def __deletion_mode(self) -> None:
        """TO-DO: ADD A CONFIRMATION OF INTENT"""
        def __delete_item(window: mainwindow, item: QTableWidgetItem) -> None:
            req_id: int = item.row()
            window.mycursor.execute(f"DELETE FROM {BOOK_TABLE[0]} WHERE {BOOK_TABLE[1]} = {req_id}")
            window.myconnection.commit()
            window.ui.book_table.cellDoubleClicked.disconnect()
        self.ui.book_table.cellDoubleClicked.connect(lambda x: __delete_item(self, x))

    def __update_table(self, query_result: list[tuple[Any]]) -> None:
        self.ui.book_table.setRowCount(len(query_result))
        a: function = lambda x: x.strip() if type(point)==str else "{0:.0f}".format(x)
        for i,entry in enumerate(query_result):
            for j, point in enumerate(entry):
                self.ui.book_table.setItem(i, j, QTableWidgetItem(a(point)))
                self.ui.book_table.item(i,j).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    
    def __perform_search(self) -> None:
        """IMPERFECTION: REPEATED CODE. CURRENTLY NO IDEA HOW TO OPTIMISE IT."""
        self.ui.book_table.itemChanged.disconnect()
        query: str = """SELECT family.f_val, n_val, o_val, s_val, house, korp, apart, mob
                                FROM book JOIN family ON book.fam=family.f_id JOIN name ON book.name=n_id
                                JOIN otchestvo ON book.otch=o_id JOIN streets ON book.street=s_id WHERE """
        is_first: bool = True
        if self.ui.last_name_line.text():
            query = query + f"f_val = '{self.ui.last_name_line.text()}'"
            is_first = False
        if self.ui.name_line.text():
            if not(is_first):
                query = query + " AND "
            query = query + f"n_val = '{self.ui.name_line.text()}'"
            is_first = False
        if self.ui.middle_name_line.text():
            if not(is_first):
                query = query + " AND "
            query = query + f"o_val = '{self.ui.middle_name_line.text()}'"
            is_first = False
        if self.ui.street_line.text():
            if not(is_first):
                query = query + " AND "
            query = query + f"s_val = '{self.ui.street_line.text()}'"
            is_first = False
        if self.ui.house_line.text():
            if not(is_first):
                query = query + " AND "
            query = query + f"house = '{self.ui.house_line.text()}'"
            is_first = False
        if self.ui.korp_line.text():
            if not(is_first):
                query = query + " AND "
            query = query + f"house = '{self.ui.korp_line.text()}'"
            is_first = False
        if self.ui.apart_line.text():
            if not(is_first):
                query = query + " AND "
            query = query + f"house = {self.ui.apart_line.text()}"
            is_first = False
        if self.ui.phone_line.text():
            if not(is_first):
                query = query + " AND "
            query = query + f"house = '{self.ui.phone_line.text()}'"
            is_first = False
        query = query + ";"
        self.mycursor.execute(query)
        search_results: list[tuple[Any]] = self.mycursor.fetchall()
        self.__update_table(search_results)
        self.ui.search_reset_button.setEnabled(True)

    def __reset_search(self) -> None:
        self.__populate()
        self.ui.search_reset_button.setEnabled(False)
        self.ui.book_table.itemChanged.connect(lambda x: self.__update_entry(x))
    
    def __add_to_parents(self) -> None:
        for i in range(3):
           if self.lines[i].text():
               self.mycursor.execute(f"""INSERT INTO {PARENT_TABLES[i][0]} ({PARENT_TABLES[i][1]}, {PARENT_TABLES[i][2]}) VALUES
                                     (DEFAULT, '{self.lines[i].text()}')""")
               self.myconnection.commit()
    
    def __update_in_parents(self) -> None:
        old_text = 0
        def get_old_text(item: QTableWidgetItem):
            nonlocal old_text
            old_text = item.text()
            self.ui.book_table.itemDoubleClicked.disconnect()
        self.ui.book_table.itemDoubleClicked.connect(lambda x: get_old_text(x))
        self.ui.book_table.itemChanged.disconnect()
        self.ui.book_table.itemChanged.connect(lambda x: update_parents(self, x))
        def update_parents(window: mainwindow, item: QTableWidgetItem) -> None:
            window.ui.book_table.itemChanged.disconnect()
            column: int = item.column()
            row: int = item.row()
            self.mycursor.execute(f"""UPDATE {PARENT_TABLES[column][0]} SET {PARENT_TABLES[column][2]} = 
                              '{self.ui.book_table.currentItem().text()}' WHERE {PARENT_TABLES[column][2]} = '{old_text}';""")
            window.myconnection.commit()
            window.__populate()
            window.ui.book_table.itemChanged.connect(lambda x: window.__update_entry(x))

        

       

def db_connection_setup() -> psycopg2.extensions.connection:
    load_dotenv()
    user_name: str = getenv('USER')
    password: str = getenv('PASSWORD')
    host_name: str = getenv('HOST')
    port_number: str = getenv('PORT')
    db_name: str = getenv('DATABASE')
    connection: psycopg2.extensions.connection = psycopg2.connect(user=user_name,
                                                                    password=password,    
                                                                    host=host_name,
                                                                    port=port_number,
                                                                    database=db_name)
    return connection


def main():
    myconnection: psycopg2.extensions.connection = db_connection_setup()
    mycursor: psycopg2.extensions.cursor = myconnection.cursor()
    app: QtWidgets.QApplication = QtWidgets.QApplication(argv)
    window: QtWidgets.QMainWindow = mainwindow(myconnection, mycursor)
    window.showMaximized()
    app.exec()


if __name__=='__main__':
    main()
