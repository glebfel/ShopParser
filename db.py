import psycopg2
import json


class WriteToDatabase:
    """Write category to database using PostgreSQL"""

    @staticmethod
    def read_config(config_file):
        """
        Parses config file disposed in same folder as this script
        and returns database info.
        :param config_file: string with config file location
        """
        try:
            with open(config_file, 'r') as f:
                data = f.read().split('\n')
                conf_info = {line.split(': ')[0]: line.split(': ')[1] for line in data if line != ''}
                return conf_info
        except FileNotFoundError:
            print("Config file is absent! Check your project folder!")
            return {}

    @staticmethod
    def write_to_db(category):
        """
        Creates table with collected data for given category
        :param category: list of dicts contains subcategories and items in it
        """
        try:
            conf_info = WriteToDatabase.read_config("config.conf")
            connection = psycopg2.connect(database=conf_info['database'],
                                               user=conf_info['user'],
                                               password=conf_info['password'],
                                               host=conf_info['host'],
                                               port=conf_info['port'])

            # create schema if not exists
            if 'ozon' in category[2]:
                with connection.cursor() as cursor:
                    cursor.execute("CREATE SCHEMA IF NOT EXISTS ozon")
                    connection.commit()
                connection.autocommit = True
                # create table with categories
                name = category[0]
                c_query = f'CREATE TABLE IF NOT EXISTS ozon.category ("Категория" TEXT,"Количество товара" TEXT, "Ссылка" TEXT);'
                # insert category in categories table
                i_query = f"INSERT INTO ozon.category VALUES ('{name}','{len(category[1])}', '{category[2]}');"
                with connection.cursor() as cursor:
                    cursor.execute(c_query)
                    cursor.execute(i_query)
                # create table
                columns = list(max(category[1], key=len).keys())
                start = f"CREATE TABLE IF NOT EXISTS ozon.{name} ("
                end = ");"
                for i in columns:
                    start += f'"{i}" TEXT,'
                start = start[0:len(start) - 1]
                with connection.cursor() as cursor:
                    cursor.execute(start + end)

                # insert values in table
                insert_query = f"INSERT INTO ozon.{name} VALUES "
                for row in category[1]:
                    insert_query += "("
                    n_row = list(row.keys())
                    n_row_clean = [""]*len(columns)
                    for i in n_row:
                        if i in columns:
                            ind = columns.index(i)
                            n_row_clean[ind] = i

                    for i in n_row_clean:
                        if i == "":
                            insert_query += f"' ',"
                        else:
                            insert_query += f"'{row[i]}',"
                    insert_query = insert_query[0:len(insert_query) - 1]
                    insert_query += "),"
                insert_query = insert_query[0:len(insert_query) - 1]
                with connection.cursor() as cursor:
                    cursor.execute(insert_query)
                print(f"Table {name} was successfully created at 'ozon' schema and all parsed data saved!")
            else:
                with connection.cursor() as cursor:
                    cursor.execute("CREATE SCHEMA IF NOT EXISTS wildberries")
                    connection.commit()
                connection.autocommit = True
                # create table with categories
                name = category[0]
                c_query = f'CREATE TABLE IF NOT EXISTS wildberries.category ("Категория" TEXT,"Количество товара" TEXT, "Ссылка" TEXT);'
                # insert category in categories table
                i_query = f"INSERT INTO wildberries.category VALUES ('{name}','{len(category[1])}', '{category[2]}');"
                with connection.cursor() as cursor:
                    cursor.execute(c_query)
                    cursor.execute(i_query)
                # create table
                columns = list(max(category[1], key=len).keys())
                start = f"CREATE TABLE IF NOT EXISTS wildberries.{name} ("
                end = ");"
                for i in columns:
                    start += f'"{i}" TEXT,'
                start = start[0:len(start) - 1]
                with connection.cursor() as cursor:
                    cursor.execute(start + end)

                # insert values in table
                insert_query = f"INSERT INTO wildberries.{name} VALUES "
                for row in category[1]:
                    insert_query += "("
                    n_row = list(row.keys())
                    n_row_clean = [""] * len(columns)
                    for i in n_row:
                        if i in columns:
                            ind = columns.index(i)
                            n_row_clean[ind] = i

                    for i in n_row_clean:
                        if i == "":
                            insert_query += f"' ',"
                        else:
                            insert_query += f"'{row[i]}',"
                    insert_query = insert_query[0:len(insert_query) - 1]
                    insert_query += "),"
                insert_query = insert_query[0:len(insert_query) - 1]
                with connection.cursor() as cursor:
                    cursor.execute(insert_query)
                print(f"Table {name} was successfully created at 'wildberries' schema and all parsed data saved!")
        except Exception as e:
            print(e)
        finally:
            connection.cursor().close()

    @staticmethod
    def write_from_json(path):
        """
        Creates table with collected data for given category
        :param path: path to json file
        """
        try:
            conf_info = WriteToDatabase.read_config("config.conf")
            connection = psycopg2.connect(database=conf_info['database'],
                                          user=conf_info['user'],
                                          password=conf_info['password'],
                                          host=conf_info['host'],
                                          port=conf_info['port'])

            # create schema "Ozon" if not exists
            with connection.cursor() as cursor:
                cursor.execute("CREATE SCHEMA IF NOT EXISTS ozon")
                connection.commit()
            connection.autocommit = True
            # Read JSON-file
            data = []
            with open(path) as json_file:
                data = json.load(json_file)
            if not data:
                return
            # create table
            name = data[0]
            columns = list(max(data[1], key=len).keys())
            start = f"CREATE TABLE IF NOT EXISTS ozon.{name} ("
            end = ");"
            for i in columns:
                start += f'"{i}" TEXT,'
            start = start[0:len(start) - 1]
            with connection.cursor() as cursor:
                cursor.execute(start + end)

            # insert values in table
            insert_query = f"INSERT INTO ozon.{name} VALUES "
            for row in data[1]:
                insert_query += "("
                n_row = list(row.keys())
                n_row_clean = [""]*len(columns)
                for i in n_row:
                    if i in columns:
                        ind = columns.index(i)
                        n_row_clean[ind] = i

                for i in n_row_clean:
                    if i == "":
                        insert_query += f"' ',"
                    else:
                        insert_query += f"'{row[i]}',"
                insert_query = insert_query[0:len(insert_query) - 1]
                insert_query += "),"
            insert_query = insert_query[0:len(insert_query) - 1]
            with connection.cursor() as cursor:
                cursor.execute(insert_query)
        except Exception as e:
            print(e)
        finally:
            connection.cursor().close()

    @staticmethod
    def update_to_db(category):
        """
        Update existing table with collected data for given category
        :param category: list of dicts contains subcategories and items in it
        """
        try:
            conf_info = WriteToDatabase.read_config("config.conf")
            connection = psycopg2.connect(database=conf_info['database'],
                                          user=conf_info['user'],
                                          password=conf_info['password'],
                                          host=conf_info['host'],
                                          port=conf_info['port'])

            # update table
            name = category[0]
            columns = list(max(category[1], key=len).keys())
            # delete old table
            drop_query = f"DROP TABLE ozon.{{name}}"
            # create new table
            start = f"CREATE TABLE ozon.{name} ("
            end = ");"
            for i in columns:
                start += f'"{i}" TEXT,'
            start = start[0:len(start) - 1]
            with connection.cursor() as cursor:
                cursor.execute(start + end)

            insert_query = f"INSERT INTO ozon.{name} VALUES "
            for row in category[1]:
                insert_query += "("
                n_row = list(row.keys())
                n_row_clean = [""] * len(columns)
                for i in n_row:
                    if i in columns:
                        ind = columns.index(i)
                        n_row_clean[ind] = i

                for i in n_row_clean:
                    if i == "":
                        insert_query += f"' ',"
                    else:
                        insert_query += f"'{row[i]}',"
                insert_query = insert_query[0:len(insert_query) - 1]
                insert_query += "),"
            insert_query = insert_query[0:len(insert_query) - 1]
            with connection.cursor() as cursor:
                cursor.execute(insert_query)
            print(f"Table {name} was successfully updated!")
        except Exception as e:
            print(e)
        finally:
            connection.cursor().close()



