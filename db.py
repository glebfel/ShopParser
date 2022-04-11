import psycopg2


class WriteToDatabase():
    """Write category to database using PostgreSQL"""

    def __init__(self, config_file):
        """
        Class constructor
        :param config_file: string with config file location
        """
        try:
            self.conf_info = WriteToDatabase.read_config(config_file)
            self.connection = psycopg2.connect(database=self.conf_info['database'],
                                               user=self.conf_info['user'],
                                               password=self.conf_info['password'],
                                               host=self.conf_info['host'],
                                               port=self.conf_info['port'])

            # create schema "Ozon" if not exists
            with self.connection.cursor() as cursor:
                cursor.execute("CREATE SCHEMA IF NOT EXISTS ozon")
                self.connection.commit()
        except Exception as e:
            print(e)

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

    def write_to_db(self, category):
        """
        Creates table with collected data for given category
        :param category: list of dicts contains subcategories and items in it
        """
        try:
            self.connection.autocommit = True
            # create table
            name = category[0]
            columns = list(category[1][0].keys())
            start = f"CREATE TABLE IF NOT EXISTS ozon.{name} ("
            end = ");"
            for i in columns:
                start += f'"{i}" TEXT,'
            start = start[0:len(start) - 1]
            with self.connection.cursor() as cursor:
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
            with self.connection.cursor() as cursor:
                cursor.execute(insert_query)
        except Exception as e:
            print(e)
        finally:
            self.connection.cursor().close()



