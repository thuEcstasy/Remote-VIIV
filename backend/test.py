import datetime

# 创建datetime对象来获取当前时间
current_time = datetime.datetime.now()

# 打印出来
result = current_time.strftime('%Y-%m-%d %H:%M:%S')
print(result)