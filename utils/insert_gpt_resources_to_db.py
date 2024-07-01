import base64
import json
import time
import pandas as pd
import os, sys
import sqlite3

sqlite_db_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + os.sep + "data" + os.sep + "data.db"
data_file = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + os.sep + "data" + os.sep + "all_openai_resources.xlsx"

df = pd.read_excel(data_file)

insert_sql = """
INSERT OR REPLACE INTO gpt_resource_list (
    type,
    region,
    resource_name,
    resource_key,
    deployment_name,
    deployment_type,
    model_name,
    model_version,
    update_time
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP);
"""

# data = [{
#     'type': 'OpenAI', 
#     'resource_name': 'xxxx',  # Azure上的资源名称
#     'region': 'westus',  # Azure上的区域
#     'resource_key': 'xxxx', # Azure上的资源密钥
#     'deployment_type':'Standard', 
#     'deployment_name': 'gpt-4-vision-preview', # 部署名称
#     'model_name': 'gpt-4',  # 模型名称
#     'model_version': 'vision-preview' # 模型版本
#     }, {
#     'type': 'OpenAI', 
#     'resource_name': 'xxxxx', 
#     'region': 'westus', 
#     'resource_key': 'xxx',
#     'deployment_type':'Standard', 
#     'deployment_name': 'gpt-4o-standard', 
#     'model_name': 'gpt-4o', 
#     'model_version': '2024-05-13'       
#     },
#     ........
#     ]
# df = pd.DataFrame(data)

values = []
for index, row in df.iterrows():
    key_str = row["resource_key"]
    row["resource_key"] = base64.b64encode(key_str.encode("utf-8"))
    insert_sql_data = row.values.tolist()
    values.append(insert_sql_data)

conn = sqlite3.connect(sqlite_db_path)
cursor = conn.cursor() 
cursor.execute("DELETE FROM gpt_resource_list;")  
# cursor.execute("DELETE FROM sqlite_sequence WHERE name='gpt_resource_list';")   # 重置自增主键
cursor.executemany(insert_sql, values)
conn.commit()
cursor.close()
conn.close()
