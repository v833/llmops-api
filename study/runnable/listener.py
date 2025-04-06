import time
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables import RunnableConfig
from langchain_core.tracers.schemas import Run

def on_start(run_obj: Run, config: RunnableConfig):
  print(f"on_start: {run_obj} {config}")
  return

def on_end(run_obj: Run, config: RunnableConfig):
  print(f"on_end: {run_obj} {config}")
  return

def on_error(run_obj: Run, config: RunnableConfig):
  print(f"on_error: {run_obj} {config}")
  return

runnable = RunnableLambda(
  lambda x: time.sleep(x)
).with_listeners(
  on_start=on_start,
  on_end=on_end,
  on_error=on_error,
)

chain = runnable

chain.invoke(2, config={
  "configurable": {
    'name': 'wq'
  }
})