#!/bin/bash
# 按需执行

APP_HOME=`pwd`

echo "创建虚拟机环境 ... "
python3 -m venv --without-pip .venv

echo "进入虚拟环境 ... "
. .venv/bin/activate

python -m pip -V >/dev/null 2>&1
if [ $? -ne 0 ];then
    echo "安装PIP工具包 ... " && curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py  >/dev/null 2>&1 && python get-pip.py >/dev/null 2>&1
fi
echo "安装APP所需依赖包 ... "
python -m pip install --upgrade pip && pip install -r requirements.txt

echo "初始化数据库 ... "
python utils/data.py

echo "检查Azure登录状态， 获取Azure OpenAI资源列表时用到 ... "
eval `az account get-access-token --query "{subscription:subscription,access_token:accessToken,token_type:tokenType}" -o yaml 2>/dev/null |sed "s/: /=/g"`
if [ -z `echo "${access_token}"` ];then
  echo "get access token fail."
  echo "请先在本服务器上登录Azure"
  echo "用户登录方式： az login --use-device-code --tenant ${tenant_id}"
  echo "服务主体登录方式： az login --service-principal --username ${client_id} --password ${client_secret} -t ${tenant_id}"
  exit 2
fi
echo "获取Azure OpenAI Gpt 资源列表 ... "
python utils/fetch_all_aoai_resources.py
echo "将Azure OpenAI Gpt资源信息入库 ... "
# 若要从文件中读取配置，可不执行，将 utils/gpt_request.py 文件的 168 行和 251 行 的 'db' 改为 'file'
python utils/insert_gpt_resources_to_db.py

echo "# 修改图片的链接，可访问的图片的url, utils/gpt_request.py 的 171 行的 images = []"
