from langchain_core.runnables import RunnableLambda
def get_weather(location, unit, name):
  print(f"获取{location}的{name}天气")
  print(f"单位：{unit}")
  print("获取天气成功")
  
  
get_weather_runnable = RunnableLambda(get_weather).bind(
  unit="摄氏度",
  name="今天"
)

resp = get_weather_runnable.invoke('北京')
