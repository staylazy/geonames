import os
import re
import sqlite3
from googletrans import Translator
from flask import Flask, jsonify, request, make_response

app = Flask(__name__)


class Geobase:
    def __init__(self):
        self.pdir = os.path.dirname(os.path.abspath(__file__))

    def connect_db(self):
        self.conn = sqlite3.connect(self.pdir + '\geonames.db')
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.__check_db_existance()

    def disconnect_db(self):
        self.conn.close()

    def __get_table_from_file(self):
        table = []
        with open(f"{self.pdir}/RU.txt", encoding="utf-8") as file:
            for line in file:
                table.append(tuple(line.split("\t")))
        return table

    def __check_db_existance(self):
        self.cursor.execute("SELECT name FROM sqlite_master "
                            "WHERE type='table' AND name='geonames'")
        table_exists = self.cursor.fetchall()
        if table_exists:
            return
        self.__init_db()

    def __insert(self, table: str, values):
        # названия полей как в базе
        columns = "geonameid, name, asciiname, alternatenames, latitude, \
                    longitude, feature_class, feature_code, country_code, cc2, \
                    admin1_code, admin2_code, admin3_code, admin4_code, \
                    population, elevation, dem, timezone, modification_date"
        # количество полей
        placeholders = ', '.join("?" * len(values[0]))
        # заполнить
        self.cursor.executemany(
            f"INSERT INTO {table} "
            f"({columns})"
            f"VALUES ({placeholders})",
            values
        )
        self.conn.commit()

    def __init_db(self):
        # инициализация таблицы в бд
        self.cursor.executescript("""create table geonames(
                                id integer primary key,
                                geonameid integer,
                                name text,
                                asciiname text,
                                alternatenames text,
                                latitude real,
                                longitude real,
                                feature_class text,
                                feature_code text,
                                country_code text,
                                cc2 text,
                                admin1_code text,
                                admin2_code text,
                                admin3_code text,
                                admin4_code text,
                                population integer,
                                elevation integer,
                                dem integer,
                                timezone text,
                                modification_date text);""")
        self.__insert("geonames", self.__get_table_from_file())
        self.conn.commit()

    # преобразовывавет sqliterow в словарь
    def __to_dict(self, rows):
        # словарь ключ - поле
        # значения - записи
        for i in range(len(rows)):
            rows[i] = dict(zip(rows[i].keys(), list(rows[i])))
        return rows

    def get_by_geonameid(self, geonameid):
        self.cursor.execute(
            f"SELECT * FROM geonames WHERE geonameid = {geonameid}"
        )
        rows = self.__to_dict(self.cursor.fetchall())
        return rows

    def __amount_of_geonames(self):
        # максимальный id будет обзим количеством записей
        self.cursor.execute("SELECT MAX(id) FROM geonames")
        return self.cursor.fetchall()[0][0]

    def get_page(self, page, on_page):  # некорректные данные
        # всего элементов
        max_id = self.__amount_of_geonames()
        # арифметическая прогрессия чтобы
        # посчитать id начального и конечного на странице
        cur_page_start = 1 + (int(page) - 1) * int(on_page)
        cur_page_end = cur_page_start + int(on_page) - 1
        # если id последнего на странице больше общего количества записей
        # то id последнего на странице равен общему колчиеству записей
        if cur_page_end > max_id:
            cur_page_end = max_id
        self.cursor.execute(
            f"SELECT * FROM geonames WHERE id >= {cur_page_start} AND id <= {cur_page_end}"
        )
        rows = self.__to_dict(self.cursor.fetchall())
        return rows

    def city_compare(self, city1, city2):
        # перевести название
        translator = Translator()
        city1_en = translator.translate(city1, src="ru", dest="en").text
        city2_en = translator.translate(city2, src="ru", dest="en").text
        # найти в базе по максимальному населению и названию
        self.cursor.execute(
            f"SELECT *, MAX(population) FROM geonames WHERE name='{city1_en}'")
        cities1 = self.__to_dict(self.cursor.fetchall())
        # убрать лишнее поле
        cities1[0].pop('MAX(population)')
        self.cursor.execute(
            f"SELECT *, MAX(population) FROM geonames WHERE name='{city2_en}'")
        cities2 = self.__to_dict(self.cursor.fetchall())
        # убрать лишнее поле
        cities2[0].pop('MAX(population)')
        # если такие города есть в базе вернуть информацию
        # более северным будет город с большей широтой
        if cities1[0]["name"] != None and cities1[0]["name"] != None:
            northern = city1 if (
                cities1[0]['latitude'] > cities2[0]['latitude']) else city2
            # если временная зона одинакова - True
            timezone = True if (
                cities1[0]['timezone'] == cities2[0]['timezone']) else False
            # упаковать ответ
            return dict(zip(['northern', 'timezone'], [northern, timezone]))
        else:
            # если записи нет в базе
            return "Incorrect request"

    def regexp(self, expr, item):
        r = re.compile(expr)
        return r.search(item) is not None

    def get_prompts(self, beg):
        # найти в базе имена по регулярному выражению 
        # функция регулярного выражения для sql 
        self.conn.create_function("REGEXP", 2, self.regexp)
        self.cursor.execute(f"SELECT * FROM geonames WHERE name REGEXP '{beg}'")
        prompts = []
        promts_dict = self.__to_dict(self.cursor.fetchall())
        for i in promts_dict:
            prompts.append(i['name'])
        # список возможных продолжений
        return prompts

geobase = Geobase()

@app.route("/geonames/api/get_by_geonameid", methods=['GET'])
def get_city_by_geonameid():
    geobase.connect_db()
    resp = geobase.get_by_geonameid(request.args["geonameid"])
    geobase.disconnect_db()
    return jsonify(resp)


@app.route("/geonames/api/get_page", methods=['GET'])
def get_page():
    geobase.connect_db()
    resp = geobase.get_page(request.args["page"], request.args["on_page"])
    geobase.disconnect_db()
    return jsonify(resp)


@app.route("/geonames/api/city_compare", methods=['GET'])
def city_compare():
    geobase.connect_db()
    resp = geobase.city_compare(request.args["geoname1"], request.args["geoname2"])
    geobase.disconnect_db()
    return jsonify(resp)


@app.route("/geonames/api/get_prompts", methods=['GET'])
def get_prompt():
    geobase.connect_db()
    resp = geobase.get_prompts(request.args["beginning"])
    geobase.disconnect_db()
    return jsonify(resp)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8000)
