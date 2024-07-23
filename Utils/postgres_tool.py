import psycopg2
from tabulate import tabulate
import pandas as pd
import emoji
from tqdm import tqdm
from Utils.logger import logger


class PostgresTool():
    
    def __init__(self, host, user, port, password, database):
        self.host = host
        self.user = user
        self.port = port
        self.password = password
        self.database = database

        self.conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            port=port,
            password=password
        )
        self.cur = self.conn.cursor()
    
    def close(self):
        self.cur.close()
        self.conn.close()

    # def query(self, sql_query, show=True):
    #     try:
    #         self.cur.execute("ROLLBACK")
    #         self.cur.execute(sql_query)
    #         if show:
    #             rows = self.cur.fetchall()
    #             print(tabulate(rows, headers=[desc[0] for desc in self.cur.description], tablefmt='psql'))
    #         else:
    #             return self.cur.fetchall()
    #     except Exception as e:
    #         pass

    def query(self, sql_query, show=True):
        try:
            self.cur.execute("ROLLBACK")
            self.cur.execute(sql_query)
            if sql_query.strip().upper().startswith("SELECT"):
                if show:
                    rows = self.cur.fetchall()
                    print(tabulate(rows, headers=[desc[0] for desc in self.cur.description], tablefmt='psql'))
                else:
                    return self.cur.fetchall()
            # else:
            #     self.conn.commit()  # Commit giao dịch cho các truy vấn không phải SELECT
        except Exception as e:
            logger.error(f"Có lỗi xảy ra: {e}")
            pass

    def get_columns(self, table_name):
        query = f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
        """
        self.cur.execute(query)
        columns = [row[0] for row in self.cur.fetchall()]
        return columns

    def get_all_table(self,):
        self.cur.execute("ROLLBACK")
        self.cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'")
        tables = [i[0] for i in self.cur.fetchall()]
        return tables
    
    def insert_data(self, path_csv):
        try:
            df = pd.read_csv(path_csv)
            table_name = path_csv.split('/')[-1].split('\\')[-1].split('//')[-1].split('.')[0]
            list_columns = list(df.columns)

            primary_keys = {
                "match": "id",
                "predict": "match_id",
                # Add additional primary keys as needed
            }
            primary_key = primary_keys.get(table_name, None)
            if primary_key is None:
                primary_key = "id"
            
            for index, row in df.iterrows():
                try:
                    row = row.where(pd.notnull(row), None)
                    columns = ', '.join([f'"{col}"' for col in list_columns])
                    values = ', '.join(['%s' for _ in range(len(list_columns))])
                    conflict_target = f'"{primary_key}"'
                    updates = ', '.join([f'"{col}" = EXCLUDED."{col}"' for col in list_columns])
                    insert_stmt = f"""
                        INSERT INTO "{table_name}" ({columns})
                        VALUES ({values})
                        ON CONFLICT ({conflict_target})
                        DO UPDATE SET {updates};
                    """
                    self.cur.execute(insert_stmt, tuple(row))
                    self.conn.commit()
                    logger(f'./logs/insert_{table_name}.log', emoji.emojize(f":check_mark_button: {table_name} Data inserted successfully! {tuple(row)} :check_mark_button:"))
                except psycopg2.Error as e:
                    self.conn.rollback()
                    error_message = f":cross_mark: {str(e)}"
                    logger(f'./logs/insert_{table_name}.log', emoji.emojize(error_message))
                    continue  
        except FileNotFoundError:
            error_message = ":cross_mark: No file csv :>>"
            logger(f'./logs/insert_{table_name}.log', emoji.emojize(error_message))
        except pd.errors.EmptyDataError:
            error_message = ":cross_mark: File csv is empty :>>"
            logger(f'./logs/insert_{table_name}.log', emoji.emojize(error_message))
        except Exception as e:
            error_message = f":cross_mark: Error read csv : {str(e)}"
            logger(f'./logs/insert_{table_name}.log', emoji.emojize(error_message))

    def check_for_ascending_primary_key(self, table_name):
        query = f"""SELECT CASE
                    WHEN MAX(id) = COUNT(id) THEN 'Ascending'
                    ELSE 'Not Ascending'
                    END AS result
                    FROM (
                        SELECT id, ROW_NUMBER() OVER (ORDER BY id) AS rn
                        FROM "match" 
                    ) subquery
                    WHERE id <> rn;
                """
        self.cur.execute(query)
        result = self.cur.fetchone()[0]
        return result

    def push_data(self, table_name, data):
        '''
        function push data for table "match", "expert_ats" and "expert_ou"
        '''
        try:
            columns = self.get_columns(table_name)
            if table_name == "match":
                columns_without_id = [col for col in columns]
                primary_key = "id"
            elif table_name == "prediction":
                columns_without_id = [col for col in columns]
                primary_key = "match_id"
            else :
                columns_without_id = [col for col in columns if col != 'id']
                primary_key = "id"
            col_names = ', '.join([f'"{col}"' for col in columns_without_id])
            placeholders = ', '.join(['%s'] * len(columns_without_id))

            update_statement = ', '.join([f'"{col}" = EXCLUDED."{col}"' for col in columns_without_id])
            query = f"""
            INSERT INTO "{table_name}" ({col_names})
            VALUES ({placeholders})
            ON CONFLICT ({primary_key}) DO UPDATE SET
            {update_statement};
            """
            
            data_tuple = tuple(data[col] for col in columns_without_id)
            # print(data_tuple)
            self.cur.execute(query, data_tuple)
            self.conn.commit()
            logger(f'./logs/insert_{table_name}.log', emoji.emojize(f":check_mark_button: Data inserted successfully into {data_tuple}! :check_mark_button:"))

        except Exception as e:
            self.conn.rollback()
            error_message = f":cross_mark: {str(e)} in table {data_tuple}"
            logger(f'./logs/insert_{table_name}.log', emoji.emojize(error_message))

    def export_to_csv(self, table_name, output_path):
        try:
            query = f'SELECT * FROM "{table_name}";'
            self.cur.execute(query)
            rows = self.cur.fetchall()
            columns = [desc[0] for desc in self.cur.description]

            df = pd.DataFrame(rows, columns=columns)
            df.to_csv(output_path, index=False)
            logger(f'./logs/export_{table_name}.log', emoji.emojize(f":check_mark_button: Data exported successfully to {output_path}! :check_mark_button:"))
        except Exception as e:
            error_message = f":cross_mark: {str(e)}"
            logger(f'./logs/export_{table_name}.log', emoji.emojize(error_message))