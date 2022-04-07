import pymysql
import json
import psycopg2


class WriteToDatabase():
    """Write JSON-file to database using PostgreSQL"""

    def __init__(self, config_file):
        """
        Class constructor
        :param config_file: string with config file location
        """
        self.conf_info = WriteToDatabase.read_config(config_file)

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
        Creates schema 'Ozon' if not exists and table with collected data for given category
        :param category: list of dicts contains subcategories and items in it
        """
        connection = psycopg2.connect(database=self.conf_info['database'],
                                      user=self.conf_info['user'],
                                      password=self.conf_info['password'],
                                      host=self.conf_info['host'],
                                      port=self.conf_info['port'])
        # Read JSON-file
        profi_data = []
        with open(file_name) as json_file:
            profi_data = json.load(json_file)
        # Check if profi_data is empty
        if not profi_data:
            return
        # collect all columns
        columns = list(profi_data[0].keys())
        for profi in profi_data[1:]:
            for key in profi.keys():
                if (key not in columns):
                    columns.append(key)
        # Create table name
        table_name = file_name.split('_')[3]
        table_name = table_name.split('\\')[1]
        # Create table and insert columns
        column_insert = " TEXT, ".join([f"`{column}`" for column in columns])
        query_text = f'create table `{table_name}` ({column_insert} TEXT)'
        connection.cursor().execute(query_text)
        # Insert every person
        for person in profi_data:
            person_columns = list(person.keys())
            person_column_insert = ", ".join([f"`{column}`" for column in person_columns])
            person_values = list(person.values())
            person_values_insert = ", ".join([f"{connection.escape(value)}" for value in person_values])
            person_query = f"insert into `{table_name}` ({person_column_insert}) values ({person_values_insert})"
            connection.cursor().execute(person_query)
            connection.commit()
        connection.cursor().close()
