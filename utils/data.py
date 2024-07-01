import pandas as pd
import sqlite3
import os

sqlite_db_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + os.sep + "data" + os.sep + "data.db"

class SQLiteDatabase():
    def __init__(self):
        self.db_file = sqlite_db_path
        self.conn = sqlite3.connect(self.db_file)
        self.curs = self.conn.cursor()
                
    def query(self, sql, args=None):
        if sql is None or len(sql) == 0 or sql.isspace() or self.curs is None:
            print("sqlite_db.query() error: query is empty.")
            return
        try:
            if args is None:
                self.curs.execute(sql)
            else:
                self.curs.execute(sql, args)
            column_names = [desc[0] for desc in self.curs.description]
            data = [dict(zip(column_names, row)) for row in self.curs.fetchall()]
            print(f"sqlite_db.query() success, sql: {sql}, args: {args}, data: {len(data)} rows affected.")
            return data
        except Exception as e:
            print("sqlite_db.query() error: ", str(e))
            print(f"fail sql: {sql}, args: {args}")
            return
        
    # 执行单条SQL语句
    def modify(self, sql, args=None):
        retry = 3
        if self.curs is None:
            print("sqlite_db.moddify() error: No database connection established.")
            return
        while retry > 0:
            try:
                # 不带参数的完整的SQL语句
                if args is None:
                    self.curs.execute(sql)
                # 多参数列表的SQL语句
                elif isinstance(args, list) or isinstance(args, tuple):
                    self.curs.executemany(sql, args)
                # 单参数的SQL语句
                else:
                    self.curs.execute(sql, args)
                self.conn.commit()
                print(f"sqlite_db.moddify() success, sql: {sql}, data: {self.curs.arraysize} rows affected.")
                return self.curs.lastrowid
            except Exception as e:
                if "database is locked" in str(e):
                    retry -= 1
                    print(f"sqlite_db.moddify() retry: {retry}, error: {str(e)}")
                    print(f"retry insert sql: {sql}, args: {args}")
                else:
                    print("sqlite_db.moddify() error: ", str(e))
                    print(f"fail sql: {sql}, args: {args}")
                    return
        
    # 执行以逗号分隔多条SQL语句
    def script(self, sql):
        if self.curs is None:
            print("sqlite_db.script() error: No database connection established.")
            return
        try:
            self.curs.executescript(sql)
            self.conn.commit()
            print(f"sqlite_db.script() success, sql: {sql}, data: {self.curs.rowcount} rows affected.")
            return self.curs.lastrowid
        except Exception as e:
            print("sqlite_db.script() error: ", str(e))
            print(f"fail sql: {sql}")
            return

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.curs is not None:
            try:
                self.curs.close()
            except Exception as e:
                print("sqlite_db.__exit__() warn: ", str(e))

        if self.conn is not None:
            try:
                self.conn.close()
            except Exception as e:
                print("sqlite_db.__exit__() warn: ", str(e))

class GPTdata(SQLiteDatabase):
    def __init__(self):
        super().__init__()
    
    def create_gpt_resource_list(self):
        create_sql = """CREATE TABLE IF NOT EXISTS gpt_resource_list (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            type TEXT NOT NULL,
                            region TEXT NOT NULL,
                            resource_name TEXT NOT NULL,
                            resource_key TEXT NOT NULL,
                            deployment_name TEXT NOT NULL,
                            deployment_type TEXT NOT NULL,
                            model_name TEXT NOT NULL,
                            model_version TEXT NOT NULL,
                            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                            update_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                            unique(type, region, deployment_type, model_name, model_version)
                        );"""
        self.modify(create_sql)
        print("gpt_resource_list table created.")
    
    def gpt_latency_data(self):
        create_sql = """CREATE TABLE IF NOT EXISTS gpt_latency_data (
                id INTEGER PRIMARY KEY,
                region TEXT NOT NULL,
                resource_name TEXT NOT NULL,
                deployment_name TEXT NOT NULL,
                deployment_type TEXT NOT NULL,
                model_name TEXT NOT NULL,
                model_version TEXT NOT NULL,
                type TEXT NOT NULL,
                request_times INTEGER NOT NULL,
                content TEXT DEFAULT NULL,
                input_tokens INTEGER DEFAULT NULL,
                input_content_length INTEGER DEFAULT NULL,
                output_tokens INTEGER DEFAULT NULL,
                output_content_length INTEGER DEFAULT NULL,
                status INTEGER DEFAULT NULL,
                total_time REAL DEFAULT NULL,
                namelookup_time REAL DEFAULT NULL,
                connect_time REAL DEFAULT NULL,
                pretransfer_time REAL DEFAULT NULL,
                starttransfer_time REAL DEFAULT NULL,
                redirect_time REAL DEFAULT NULL,
                size_upload REAL DEFAULT NULL,
                speed_upload REAL DEFAULT NULL,
                size_download REAL DEFAULT NULL,
                speed_download REAL DEFAULT NULL,
                header_size INTEGER DEFAULT NULL,
                request_size INTEGER DEFAULT NULL,
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                update_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                unique(region, model_name, deployment_type, model_version, type, request_times)
                );"""
        self.modify(create_sql)
        print("gpt_latency_data table created.")

def main(): 
    import traceback
    try:  
        sql_db = GPTdata()  
        sql_db.create_gpt_resource_list()  
        sql_db.gpt_latency_data()   
    except Exception as e:  
        print(f"Err: {e}")  
        traceback.print_exc()
  
if __name__ == "__main__":  
    main()
