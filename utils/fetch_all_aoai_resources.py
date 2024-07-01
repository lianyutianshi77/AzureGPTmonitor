import pandas as pd
import requests
import json
import os
from azure.identity import AzureCliCredential, DefaultAzureCredential
import openpyxl

# 认证
def getAccessToken(resource_scope=None):
    tokenCode = None
    try:
        # DefaultAzureCredential
        credential = AzureCliCredential()
        if credential:
            if resource_scope is None:
                resource_scope = "https://management.azure.com/.default"
            tokenCode = credential.get_token(resource_scope).token
        else:
            if resource_scope is None:
                resource_scope = "https://management.azure.com/"
            else:
                resource_scope = resource_scope.replace(".default", "")
            tenant_id = "xxxx"
            data = {
                "grant_type": "client_credentials",
                "client_id": "xxxx",
                "client_secret": "xxxx",
                "resource": resource_scope # 资源范围，中国区：https://management.chinacloudapi.cn/        
            }
            url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/token"
            retries = 3
            for i in range(retries):
                try:
                    response = requests.post(url=url, data=data)
                    res = response.json()
                    tokenCode = f"{res['access_token']}"
                    return tokenCode
                except Exception as e:
                    print(f'Failed to get access token: {e}')
                    print(f"Error: failed to get access token, retry: {i+1}")
    
        if tokenCode is None:
            print("Warn: Please login Azure CLI or verify config file.")
            print("      az login --use-device-code --tenant <tenant_id>")
            raise Exception("Err: Failed to get access token from Azure CLI.")
        return tokenCode
    
    except Exception as e:
        print(e)
        return tokenCode
    
token = getAccessToken()

def get_all_subscriptions():
    # 获取所有订阅
    subscriptions = []
    retry = 3
    for i in range(retry):
        try:
            
            headers =  {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            url = "https://management.azure.com/subscriptions?api-version=2016-06-01"
            response = requests.get(url, headers=headers)
            value = response.json()["value"]
            for item in value:
                subscriptions.append({"name": item["displayName"], "id": item["subscriptionId"]})
            return subscriptions
        except Exception as e:
            print(f"Error: {e}")
            print(f"Error: failed to get subscription list, retry: {i+1}")
    return subscriptions

def get_resource_key(subscription_id, resource_group, resource_name): 
    import base64 
    # 获取资源key    
    retry = 3
    for i in range(retry):
        try:
            headers =  {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            url = f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.CognitiveServices/accounts/{resource_name}/listKeys?api-version=2023-05-01"
            response = requests.post(url, headers=headers)
            key = response.json()["key1"]
            # key_str = base64.b64encode(key.encode("utf-8"))
            return key
        except Exception as e:
            print(f"Error: {e}")
            print(f"Error: failed to get resource key, retry: {i+1}")
    return None

def get_usage(subscription_id, resource_group, resource_name): 
    # 对于OpenAI资源，此API无效
    retry = 3
    for i in range(retry):
        try:
            headers =  {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            url = f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.CognitiveServices/accounts/{resource_name}/usages?api-version=2023-05-01"
            response = requests.get(url, headers=headers)
            return response.json()
        except Exception as e:
            print(f"Error: {e}")
            print(f"Error: failed to get usage, retry: {i+1}")
    return None

def get_all_locations(subscription_id):
    # 获取所有可用的位置
    locations = ()
    retry = 3
    for i in range(retry):
        try:

            headers =  {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            url = f"https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.CognitiveServices/skus?api-version=2023-05-01"
            response = requests.get(url, headers=headers)
            value = response.json()["value"]
            for item in value:
                locations.add(item["location"])
            return locations
        except Exception as e:
            print(f"Error: {e}")
            print(f"Error: failed to get locations, retry: {i+1}")
    return locations
def get_all_models_list(subscription_id, location):
    # 查看可部署的模型
    retry = 3
    models = []
    for i in range(retry):
        try:
            headers =  {"Authorization": f"Bearer {token}","Content-Type": "application/json"}
            url = f"https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.CognitiveServices/locations/{location}/models?api-version=2023-05-01"
            response = requests.get(url, headers=headers)
            value = [
                item for item in response.json()["value"]
                if item["kind"] == "OpenAI"
            ]
            for item in value:
                name = item["model"]["name"]
                version = item["model"]["version"]
                models.append({"model_name": name, "model_version": version})
            return models
        except Exception as e:
            print(f"Error: {e}")
            print(f"Error: failed to get models list, retry: {i+1}")
    return models

def get_all_models(subscription_id, resource_group, resource_name):
    # 查看可部署的模型
    retry = 3
    models = []
    for i in range(retry):
        try:
            headers =  {"Authorization": f"Bearer {token}","Content-Type": "application/json"}
            url = f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.CognitiveServices/accounts/{resource_name}/models?api-version=2023-05-01"
            response = requests.get(url, headers=headers)
            value = response.json()["value"]
            for item in value:
                name = item["baseModel"]["name"]
                version = item["baseModel"]["version"]
                models.append({"model_name": name, "model_version": version})
            return models
        except Exception as e:
            print(f"Error: {e}")
            print(f"Error: failed to get models, retry: {i+1}")
    return models

def get_all_deployments(subscription_id, resource_group, resource_name):
    # 查看所有部署
    deployments = []
    retry = 3
    for i in range(retry):
        try:
            headers =  {"Authorization": f"Bearer {token}","Content-Type": "application/json"}
            url = f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.CognitiveServices/accounts/{resource_name}/deployments?api-version=2023-05-01"
            response = requests.get(url, headers=headers)
            value = response.json()["value"]
            for item in value:
                name = item["name"]
                sku = item["sku"]["name"] if "sku" in item else None
                limits = item["sku"]["capacity"] if "sku" in item and "capacity" in item["sku"] else None
                model_name = item["properties"]["model"]["name"] if "model" in item["properties"] else None
                model_version = item["properties"]["model"]["version"] if "model" in item["properties"] else None
                deployments.append({"deployment_name": name, "deployment_type": sku, "model_name": model_name,"model_version": model_version,"limits": limits})
            return deployments
        except Exception as e:
            print(f"Error: {e}")
            print(f"Error: failed to get deployments, retry: {i+1}")
    return None

def get_all_oai_resources(subscription_id):
    retry = 3
    resources = []
    for i in range(retry):
        try:
            headers =  {"Authorization": f"Bearer {token}","Content-Type": "application/json"}
            url = f"https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.CognitiveServices/accounts?api-version=2023-05-01"
            response = requests.get(url, headers=headers)
            value = response.json()["value"]
            openai_resources = [
                item for item in value
                if item["kind"] == "OpenAI"
            ]
            for item in openai_resources:
                resource_group = item["id"].split("/")[4]
                resource_name = item["name"]
                resource_key = get_resource_key(subscription_id, resource_group, resource_name)
                deployment = get_all_deployments(subscription_id, resource_group, resource_name)
                for deploy in deployment:
                    resources.append({
                        "type": item["kind"], # 服务类型
                        "region": item["location"], # 服务所在区域
                        "resource_name": resource_name, # 服务的实例名称
                        "resource_key": resource_key, # 服务的key
                        "deployment_name": deploy["deployment_name"], # 部署名称
                        "deployment_type": deploy["deployment_type"], # 部署类型
                        "model_name": deploy["model_name"], # 模型名称
                        "model_version": deploy["model_version"], # 模型版本
                        # "limits": deploy["limits"] # 部署限制
                    })
            return resources
        except Exception as e:
            print(f"Error: {e}")
            print(f"Error: failed to get openai resource list, retry: {i+1}")
    return resources   

def main():
    save_file = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + os.sep + "data" + os.sep + "all_openai_resources.xlsx"
    all_subscriptions = get_all_subscriptions()
    data = []
    subscription = all_subscriptions[0] # 只需要一个订阅就可以
    if subscription:
        data = get_all_oai_resources(subscription["id"])
    # for subscription in all_subscriptions: 
    #     all_resources = get_all_oai_resources(subscription["id"])
    #     for resource in all_resources:
    #         resource["subscription_name"] = subscription["name"]
    #         data.append(resource)
    
    df = pd.DataFrame(data)
    # df_data = df
    # df_unique = df.drop_duplicates(subset=['subscription_name', 'region', 'deployment_type', 'model_name', 'model_version'])
    df_unique = df.drop_duplicates(subset=['region', 'deployment_type', 'model_name', 'model_version'])
    df_data = df_unique[(df_unique['model_name'].str.startswith(('gpt-35', 'gpt-4'))) & (df_unique['model_name'] != 'gpt-35-turbo-instruct')]  
    
    print(f"Total OpenAI Resources: {len(df_data)}")
    df_data.to_excel(save_file, index=False)
    print(f"GPT Resources List File: {save_file}")
    pass

if __name__ == "__main__":
    main()
