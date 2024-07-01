import atexit
import streamlit as st
import pandas as pd
from datetime import datetime  
import pytz 
from tzlocal import get_localzone  
from apscheduler.schedulers.background import BackgroundScheduler  
from apscheduler.triggers.cron import CronTrigger  
from pathlib import Path
from croniter import croniter
from io import StringIO
from utils.data import GPTdata
from utils.gpt_request import process_image_resource, process_text_resource

def get_image_data():
    select_sql = """SELECT   
        region as '区域',
        CASE
          WHEN model_name == 'gpt-4o' THEN deployment_name || ' ( ' ||  model_version || ' )' 
          ELSE model_name || ' ( ' ||  model_version || ' )' 
        END as '模型',
        MAX(update_time) AS '更新时间（+8）' ,
        status as '状态',
        CAST(ROUND(AVG(input_tokens), 0) AS INTEGER) AS '输入Tokens',
        input_content_length as '输入内容长度',
        CAST(ROUND(AVG(output_tokens), 0) AS INTEGER) AS '输出Tokens',
        output_content_length as '输出内容长度',
        ROUND(AVG(total_time), 4) AS '总时间',
        ROUND(AVG(pretransfer_time), 4) AS '首Token时间',
        ROUND(AVG(namelookup_time), 4) AS 'DNS解析时间',
        ROUND(AVG(connect_time), 4) AS 'TCP建立时间'
    FROM   
        gpt_latency_data  
    WHERE type = 'IMAGE'
    GROUP BY   
        region,  
        resource_name,  
        deployment_name,  
        model_name,  
        model_version,  
        type
    ORDER BY deployment_name; 
    """
    db = GPTdata()
    data = db.query(select_sql)
    return data

def get_text_data():
    select_sql = """SELECT   
        region as '区域',
        CASE
          WHEN model_name == 'gpt-4o' THEN deployment_name || ' ( ' ||  model_version || ' )' 
          ELSE model_name || ' ( ' ||  model_version || ' )' 
        END as '模型',
        MAX(update_time) AS '更新时间（+8）' ,
        status as '状态',
        CAST(ROUND(AVG(input_tokens), 0) AS INTEGER) AS '输入Tokens',
        input_content_length as '输入内容长度',
        CAST(ROUND(AVG(output_tokens), 0) AS INTEGER) AS '输出Tokens',
        output_content_length as '输出内容长度',
        ROUND(AVG(total_time), 4) AS '总时间',
        ROUND(AVG(pretransfer_time), 4) AS '首Token时间',
        ROUND(AVG(namelookup_time), 4) AS 'DNS解析时间',
        ROUND(AVG(connect_time), 4) AS 'TCP建立时间'
    FROM   
        gpt_latency_data  
    WHERE type = 'TEXT'
    GROUP BY   
        region,  
        resource_name,  
        deployment_name,  
        model_name,  
        model_version,  
        type
    ORDER BY deployment_name; 
    """
    db = GPTdata()
    data = db.query(select_sql)
    return data

def convert_to_utc_plus_8(utc_time_str):
    time_format = "%Y-%m-%d %H:%M:%S"  
    utc_time = datetime.strptime(utc_time_str, time_format)      
    utc_time = utc_time.replace(tzinfo=pytz.utc)  
    utc_plus_8_time = utc_time.astimezone(pytz.timezone("Asia/Shanghai"))    
    return utc_plus_8_time.strftime(time_format) 

st.set_page_config(
    page_title="Azure GPT Latency",  # 网页标题
    page_icon="🎪",                         # 网页图标，可以是 emoji
    layout="wide"                           # 网页布局，使用 "wide" 使内容占据整个宽度
)

st.title("Azure GPT 各区性能 (仅供参考)")
# 本地时区
local_timezone = get_localzone()
local_datetime = datetime.now(local_timezone)
local_time_str = local_datetime.strftime("%Y-%m-%d %H:%M:%S")  
st.write(f'客户端时间: {local_datetime.strftime("%Y-%m-%d %H:%M:%S %Z%z")} ( {local_timezone} ), 北京时间：{convert_to_utc_plus_8(local_time_str)} ( Asia/Shanghai )')
# st.write("每两时执行一次, 发起端在韩国，")
with st.expander(f"每两时执行一次, 发起端在韩国， 查看其他说明"):
    st.text("""
    1. 每两小时发起一次响应时间测试，每次请求返回限制在60个tokens，每次连续发送三个请求，结果取平均值
    2. 当前不保留历史测试结果，只保留最近一次请求结果。
    3. 状态：✅表示正常，❌表示异常（可能认证失败/超时/触发接口限制等）；
""")
# st.markdown("---")
st.subheader("图片任务：")
img_data = get_image_data()
if img_data is None or len(img_data) == 0:
    st.write("暂无数据")
else:
    img_df = pd.DataFrame(img_data)
    # st.table(df)  
    height = len(img_df) * 37
    img_max = img_df["总时间"].max()
    img_df["更新时间（+8）"] = img_df["更新时间（+8）"].apply(convert_to_utc_plus_8)
    img_df['状态'] = img_df['状态'].apply(lambda x: f'✅{x}' if x == 200 else f'❌{x}')  
    # 显示数据表格
    # st.dataframe(styled_df, hide_index=True)
    st.dataframe(
        img_df,
        column_config={
            "总时间": st.column_config.ProgressColumn(
                "总时间",
                help="取三次请求的平均值",
                format="%f",
                min_value=0,
                max_value=img_max,
            ),
            "首Token时间": st.column_config.ProgressColumn(
                "首Token时间",
                help="取三次请求的平均值",
                format="%f",
                min_value=0,
                max_value=img_max,
            ),
        },
        height=height,
        hide_index=True,
    )
st.markdown("---")
st.subheader("文本任务：")
text_data = get_text_data()
if text_data is None or len(text_data) == 0:
    st.write("暂无数据")
else:
    text_df = pd.DataFrame(text_data)
    # st.table(df)  
    text_height = len(text_df) * 38
    text_max = text_df["总时间"].max()
    text_df["更新时间（+8）"] = text_df["更新时间（+8）"].apply(convert_to_utc_plus_8)
    text_df['状态'] = text_df['状态'].apply(lambda x: f'✅{x}' if x == 200 else f'❌{x}')  
    # 显示数据表格
    # st.dataframe(styled_df, hide_index=True)
    st.dataframe(
        text_df,
        column_config={
            "总时间": st.column_config.ProgressColumn(
                "总时间",
                help="取三次请求的平均值",
                format="%f",
                min_value=0,
                max_value=text_max,
            ),
            "首Token时间": st.column_config.ProgressColumn(
                "首Token时间",
                help="取三次请求的平均值",
                format="%f",
                min_value=0,
                max_value=text_max,
            ),
        },
        height=text_height,
        hide_index=True,
    )

st.markdown("---")
st.write("Support by Min")
  
# 初始化调度器  
scheduler = BackgroundScheduler()  
cron_expression = "10 */2 * * *"  # crontab 表达式， 每两小时执行一次
scheduler_lock = "scheduler.lock"

def update_next_time():
    cron = croniter(cron_expression, datetime.now())
    next_time = cron.get_next(datetime).strftime("%Y-%m-%d %H:%M:%S")
    st.session_state['next_time'] = next_time
    print(f"下次任务执行时间: {next_time}")
    
    if Path(scheduler_lock).exists():
        df = pd.read_json(scheduler_lock, orient='records')
    else:
        df = pd.DataFrame(columns=["job", "next_time"])
    
    df["next_time"] = next_time
    df.to_json(scheduler_lock, orient='records')
  
def run_task(): 
    print(f"定时任务运行中... {datetime.now()}")
    process_image_resource()  
    process_text_resource()  
    print(f"定时任务结束... {datetime.now()}")  
    update_next_time()

def start_scheduler():  
    if 'job' not in st.session_state:  
        try:  
            update_next_time()
            trigger = CronTrigger.from_crontab(cron_expression)  
            job = scheduler.add_job(run_task, trigger)
            st.session_state['job'] = job 

            df = pd.DataFrame([{"job":  str(st.session_state['job']), "next_time": st.session_state['next_time']}])  
            df.to_json(scheduler_lock, orient='records')
            
            scheduler.start()  
            print(f"任务启动成功, 待执行时间: {st.session_state['next_time']}")  
        except Exception as e:  
            print(f"启动任务时出错: {e}")  
    else:  
        print(f"任务信息：{st.session_state['job']}")  
        print("已有任务在运行中!")  
  
def load_existing_scheduler():  
    if Path(scheduler_lock).exists():  
        df = pd.read_json(scheduler_lock, orient='records')  
        print(f"已有调度器在运行中! {df.to_dict()}")  
    else:  
        start_scheduler()  
  
def cleanup():  
    print("应用退出，清理资源...")  
    if scheduler.running:  
        scheduler.shutdown()  
  
atexit.register(cleanup)  
  
# 初始化  
load_existing_scheduler()  
