import pycurl
from io import BytesIO
import json
import time
import base64
import sys
import concurrent.futures
from utils.data import SQLiteDatabase

def get_gpt_resources(option1=None, option2=None):
    # option1: 选择读取方式file、 db
    # option2: 处理内容类型img、text
    if option1.lower() == 'db' or option1 is None:
        db = SQLiteDatabase()
    
        select_sql = """SELECT
        resource_name,
        region,
        resource_key,
        deployment_name,
        deployment_type,
        model_name,
        model_version
    FROM gpt_resource_list
    where (model_name like 'gpt-4%' or model_name like 'gpt-35%') and model_name != 'gpt-35-turbo-instruct';"""
        if option2.lower() == 'img' or option2.lower() == 'image' or option2 is None:
            select_sql = """SELECT
        resource_name,
        region,
        resource_key,
        deployment_name,
        deployment_type,
        model_name,
        model_version
    from gpt_resource_list
    where model_name = "gpt-4o"
    or (model_name = 'gpt-4' and (model_version = 'turbo-2024-04-09' or model_version = 'vision-preview'))
    """
        gpt_list = db.query(select_sql)
        return gpt_list
    
    else:
        import pandas as pd
        import os
        resource_file = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + os.sep + "data" + os.sep + "all_openai_resources.xlsx"
        df = pd.read_excel(resource_file)
        data = df
        if option2.lower() == 'img' or option2.lower() == 'image' or option2 is None:
            data = df.query('(model_name == "gpt-4o") or (model_name == "gpt-4" and model_version in ["turbo-2024-04-09", "vision-preview"])')
        else:
            data = df[df['model_name'].str.startswith(('gpt-35', 'gpt-4'))] 
        return data.to_dict(orient='records')

def gpt_request(sys_msg, resource_name, key, engine, user_msg):
    retries = 3
    data = {
        # "content": None,
        "input_tokens": None,
        "output_tokens": None,
        "input_content_length": None,
        "output_content_length": None,
        "status": None,
        "total_time": None,
        "namelookup_time": None,
        "connect_time": None,
        "pretransfer_time": None,
        "starttransfer_time": None,
        "redirect_time": None,
        "size_upload": None,
        "speed_upload": None,
        "size_download": None,
        "speed_download": None,
        "header_size": None,
        "request_size": None
    }

    print(f"{resource_name} - {engine} start time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
    for i in range(retries):
        buffer,buffer2 = BytesIO(), BytesIO()
        response_body = ""
        try:
            url = f"https://{resource_name}.openai.azure.com/openai/deployments/{engine}/chat/completions?api-version=2024-05-01-preview"
            headers = ["Content-Type: Application/json", f"api-key: {key}"]
            body_data = { # 计算文本长度非流式比较方便
                "messages": [
                    {"role": "system", "content": sys_msg},
                    {"role": "user", "content": user_msg}
                ],
                "max_tokens": 60
            }

            request_client = pycurl.Curl()
            request_client.setopt(pycurl.SSL_VERIFYPEER, False)
            request_client.setopt(pycurl.SSL_VERIFYHOST, False)
            request_client.setopt(request_client.URL, url) # 设置请求的 URL
            request_client.setopt(request_client.HTTPHEADER, headers)  # 设置请求的 HTTP 头部
            request_client.setopt(request_client.POSTFIELDS, json.dumps(body_data)) # 设置请求的 POST 数据
            request_client.setopt(request_client.WRITEDATA, buffer) # 设置一个回调函数，数据将被写入这个回调函数的参数
            request_client.perform() # 执行请求

            response_body = buffer.getvalue().decode('utf-8')  # 获取响应体内容
            data["status"] = request_client.getinfo(pycurl.RESPONSE_CODE) # 获取响应状态码
            # data["total_time"] = request_client.getinfo(pycurl.TOTAL_TIME)
            # data["namelookup_time"] = request_client.getinfo(pycurl.NAMELOOKUP_TIME)
            # data["connect_time"] = request_client.getinfo(pycurl.CONNECT_TIME)
            # data["pretransfer_time"] = request_client.getinfo(pycurl.PRETRANSFER_TIME)
            # data["starttransfer_time"] = request_client.getinfo(pycurl.STARTTRANSFER_TIME)
            data["redirect_time"] = request_client.getinfo(pycurl.REDIRECT_TIME)
            data["size_upload"] = request_client.getinfo(pycurl.SIZE_UPLOAD)
            data["speed_upload"] = request_client.getinfo(pycurl.SPEED_UPLOAD)
            data["size_download"] = request_client.getinfo(pycurl.SIZE_DOWNLOAD)
            data["speed_download"] = request_client.getinfo(pycurl.SPEED_DOWNLOAD)
            data["header_size"] = request_client.getinfo(pycurl.HEADER_SIZE)
            data["request_size"] = request_client.getinfo(pycurl.REQUEST_SIZE)
            request_client.close()

            
            body_data2 = { # 获取首token流式比较方便
                "messages": [
                    {"role": "system", "content": sys_msg},
                    {"role": "user", "content": user_msg}
                ],
                "stream": True,
                "max_tokens": 60
            }
            request_client2 = pycurl.Curl()
            request_client2.setopt(pycurl.SSL_VERIFYPEER, False)
            request_client2.setopt(pycurl.SSL_VERIFYHOST, False)
            request_client2.setopt(request_client.URL, url) # 设置请求的 URL
            request_client2.setopt(request_client.HTTPHEADER, headers)  # 设置请求的 HTTP 头部
            request_client2.setopt(request_client.POSTFIELDS, json.dumps(body_data2)) # 设置请求的 POST 数据
            request_client2.setopt(request_client.WRITEDATA, buffer2) # 设置一个回调函数，数据将被写入这个回调函数的参数
            request_client2.perform() # 执行请求
            # response_body = buffer2.getvalue().decode('utf-8')  # 获取响应体内容
            data["total_time"] = request_client2.getinfo(pycurl.TOTAL_TIME)
            data["namelookup_time"] = request_client2.getinfo(pycurl.NAMELOOKUP_TIME)
            data["connect_time"] = request_client2.getinfo(pycurl.CONNECT_TIME)
            data["pretransfer_time"] = request_client2.getinfo(pycurl.PRETRANSFER_TIME)
            data["starttransfer_time"] = request_client2.getinfo(pycurl.STARTTRANSFER_TIME)
            request_client2.close()


            res = json.loads(response_body)
            content = res["choices"][0]["message"]["content"]
            data["input_tokens"] = res["usage"]["prompt_tokens"]
            data["output_tokens"] = res["usage"]["completion_tokens"]
            data["output_content_length"] = len(content)
            # data["content"] = content
            return data
        except Exception as e:
            print(f"{i} error", e, response_body)
            print(f"Retry {i+1} times...")
            if "InternalServerError" in response_body:
                time.sleep(1)
            else:
                time.sleep(5)
        finally:
            print(f"{resource_name} - {engine} end time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")

    return data
    
def process_image_resource():
    start_time = time.time()
    print(f"Begin request image at {time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(start_time))} ------------------------------------------------")
    gpt4_list = get_gpt_resources("file", "img")
    print(f"get {len(gpt4_list)} gpt resource") 
    

    images = ['https://xxxx.blob.core.windows.net/imagetest/mingpian1.jpg?se=2024-08-29T09%3A39%3A38Z&sp=r&sv=2024-05-04&sr=b&sig=U6vzU/LRMij0bpwGXIivuzImGNIVr2FOEyM1glC4oJk%3D',
         'https://xxxxx.blob.core.windows.net/imagetest/mingpian10.jpg?se=2024-08-29T09%3A39%3A41Z&sp=r&sv=2024-05-04&sr=b&sig=ClZKIBuzGWcT7pknzNcXg6z3YWPE%2Bz8MTrdx7LIUbmE%3D',
         'https://xxxxx.blob.core.windows.net/imagetest/mingpian2.jpg?se=2024-08-29T09%3A39%3A44Z&sp=r&sv=2024-05-04&sr=b&sig=2t41zdAiLgwvsSM9sZJpUa696TWw3jgeE8eIJ6LKk7c%3D'
    ]

    sys_msg = """你是一个名片识别助手，用来提取用户上传的名片照片上的信息；
        你需要提取如下项目，并使用Json格式返回。
        {
        "公司名称": string,
        "姓名": string,
        "职位": String
        }
        """

    def process_single_gpt4(gpt4):
        length = 0
        resource_key = gpt4["resource_key"]
        try:
            if resource_key.startswith("b'"):
                resource_key = resource_key[2:-1]
            key = base64.b64decode(resource_key).decode("utf-8")
        except Exception as e:
            key = resource_key

        for index, img in enumerate(images[:]):

            import requests
            try:  
                response = requests.get(img, timeout=10)  # 设置超时时间，防止请求挂起  
                if response.status_code == 200:  
                    print(f"Image {img} found successfully.")  
                else:  
                    print(f"Image {img} not found, status code: {response.status_code}. Please check the URL.")  
                    sys.exit(2)  
            except requests.exceptions.RequestException as e:  
                print(f"An error occurred while trying to fetch the image {img}: {e}")  
                sys.exit(2)

            user_msg = [
                        {"type": "text", "text": "提取文本："},
                        {"type": "image_url",
                            "image_url": {"url" : img}
                        }
                    ]
            res = gpt_request(sys_msg, gpt4["resource_name"], key , gpt4["deployment_name"], user_msg)
            res["input_content_length"] = len(sys_msg) + len(json.dumps(user_msg))
            res["region"] = gpt4["region"]
            res["resource_name"] = gpt4["resource_name"]
            res["deployment_name"] = gpt4["deployment_name"]
            res["deployment_type"] = gpt4["deployment_type"]
            res["model_name"] = gpt4["model_name"]
            res["model_version"] = gpt4["model_version"]
            res["type"] = "IMAGE"
            res["request_times"] = index + 1

            keys = res.keys()
            insert_sql = f"""INSERT OR REPLACE INTO gpt_latency_data ({', '.join(keys)}, update_time)
                VALUES ({', '.join(['?' for _ in keys])}, CURRENT_TIMESTAMP);
                """
            values = [tuple(res[key] for key in keys)]
            SQLiteDatabase().modify(insert_sql, values)
            length += len(values)
        print(f"response image data {length} rows")

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_single_gpt4, gpt4) for gpt4 in gpt4_list[:]]
        concurrent.futures.wait(futures)

    end_time = time.time()
    print(f"Image data inserted done at {time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(end_time))}, elapsed time: {round(end_time - start_time, 4)} seconds --------------------------------")

def process_text_resource():
    start_time = time.time()
    print(f"Begin request text at {time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(start_time))} ------------------------------------------------")
    gpt_list = get_gpt_resources("file", "text")
    print(f"get {len(gpt_list)} gpt resource") 
    questions = [
        "什么是合同法？",
        "员工在工作中受到伤害，公司需要承担哪些法律责任？",
        "公司如何确保其行为符合数据保护法律法规？"
    ]

    sys_msg = """你是一个法律援助助手,请简要回答以下问题。"""

    def process_single_gpt4(gpt4):
        length = 0
        resource_key = gpt4["resource_key"]
        try:
            if resource_key.startswith("b'"):
                resource_key = resource_key.replace("b'", "").replace("'", "")
            key = base64.b64decode(resource_key).decode("utf-8")
        except Exception as e:
            key = resource_key
        for index, text in enumerate(questions):
            user_msg = text
            res = gpt_request(sys_msg, gpt4["resource_name"], key, gpt4["deployment_name"], user_msg)
            res["input_content_length"] = len(sys_msg) + len(json.dumps(user_msg))
            res["region"] = gpt4["region"]
            res["resource_name"] = gpt4["resource_name"]
            res["deployment_name"] = gpt4["deployment_name"]
            res["deployment_type"] = gpt4["deployment_type"]
            res["model_name"] = gpt4["model_name"]
            res["model_version"] = gpt4["model_version"]
            res["type"] = "TEXT"
            res["request_times"] = index + 1

            keys = res.keys()
            insert_sql = f"""INSERT OR REPLACE INTO gpt_latency_data ({', '.join(keys)}, update_time)
                            VALUES ({', '.join(['?' for _ in keys])}, CURRENT_TIMESTAMP);"""
            values = [tuple(res[key] for key in keys)]
            SQLiteDatabase().modify(insert_sql, values)
            length += len(values)
        print(f"response text data {length} rows")

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_single_gpt4, gpt4) for gpt4 in gpt_list[:]]
        concurrent.futures.wait(futures)

    end_time = time.time()
    print(f"Text data inserted done at {time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(end_time))}, elapsed time: {round(end_time - start_time, 4)} seconds --------------------------------")

def main():
    # process_image_resource()
    # process_text_resource()
    pass


if __name__ == "__main__":
    main()
