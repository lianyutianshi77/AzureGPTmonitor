#!/bin/bash
app_home=`pwd`
app_port="80"
start_app()
{
pid=`ps -elf|grep ${app_home}|grep -v grep|awk '{print $4}' 2>/dev/null`
if [ ! -z "${pid}" ];then
        echo "service is already running, PID: ${pid}"
else   
        cd ${app_home}
        . .venv/bin/activate
        streamlit run app.py --server.port ${app_port} --server.enableXsrfProtection false > ${app_home}/app.logs 2>&1 &
        deactivate
        sleep 3
        pid=`ps -elf|grep ${app_home}|grep -v grep|awk '{print $4}' 2>/dev/null`
        if [ ! -z "${pid}" ];then
                echo "Success to start service, PID: ${pid}"
                curl http://127.0.0.1:${app_port} > /dev/null
        else
                echo "Failed to start service, PID: ${pid}, plz retry"
        fi
fi
}
stop_app()
{
pid0=`ps -elf|grep ${app_home}|grep -v grep|awk '{print $4}' 2>/dev/null`
if [ ! -z "${pid0}" ];then
        kill -9 ${pid0}
        cd ${app_home} && rm scheduler.lock >/dev/null 2>&1
        find . -name 'venv' -prune -o -type d -name "__pycache__" -exec rm -r {} \; >/dev/null 2>&1
        pid=`ps -elf|grep ${app_home}|grep -v grep|awk '{print $4}' 2>/dev/null`
        if [ -z "${pid}" ];then
                echo "Success to stop service, PID: ${pid0}"
        else
                echo "Failed to stop service, PID: ${pid0}, plz retry"
        fi
else
        echo "service is already stopped"
fi
}
check_app()
{
pid=`ps -elf|grep ${app_home}|grep -v grep|awk '{print $4}' 2>/dev/null`
if [ ! -z "${pid}" ];then
      echo "service is running, PID: ${pid}"
else
      echo "service is stopped"
fi
}

case "$1" in
    start)
        start_app
        ;;
    stop)
        stop_app
        ;;
    restart)
        stop_app
        start_app
        ;;
    status)
        check_app
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
