import uuid
from abc import abstractmethod
from threading import Thread
from typing import Optional, Any, Iterator

from langchain_core.language_models import BaseLanguageModel
from langchain_core.load import Serializable
from pydantic import PrivateAttr
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.graph.state import CompiledStateGraph

from internal.core.agent.entities.agent_entity import AgentConfig, AgentState
from internal.core.agent.entities.queue_entity import AgentResult, AgentThought
from internal.exception import FailException
from .agent_queue_manager import AgentQueueManager


class BaseAgent(Serializable, Runnable):
    """基于Runnable的基础智能体基类"""

    name: str = "base_agent"

    llm: BaseLanguageModel
    agent_config: AgentConfig
    _agent: CompiledStateGraph = PrivateAttr(None)
    _agent_queue_manager: AgentQueueManager = PrivateAttr(None)

    class Config:
        # 字段允许接收任意类型，且不需要校验器
        arbitrary_types_allowed = True

    def __init__(
        self,
        llm: BaseLanguageModel,
        agent_config: AgentConfig,
        *args,
        **kwargs,
    ):
        """构造函数，初始化智能体图结构程序"""
        super().__init__(*args, llm=llm, agent_config=agent_config, **kwargs)
        self._agent = self._build_agent()
        self._agent_queue_manager = AgentQueueManager(
            user_id=agent_config.user_id,
            invoke_from=agent_config.invoke_from,
        )

    @abstractmethod
    def _build_agent(self) -> CompiledStateGraph:
        """构建智能体函数，等待子类实现"""
        raise NotImplementedError("_build_agent()未实现")

    def invoke(
        self, input: AgentState, config: Optional[RunnableConfig] = None
    ) -> AgentResult:
        """块内容响应，一次性生成完整内容后返回"""
        pass

    def stream(
        self,
        input: AgentState,
        config: Optional[RunnableConfig] = None,
        **kwargs: Optional[Any],
    ) -> Iterator[AgentThought]:
        """流式输出，每个Not节点或者LLM每生成一个token时则会返回相应内容"""
        # 1.检测子类是否已构建Agent智能体，如果未构建则抛出错误
        if not self._agent:
            raise FailException("智能体未成功构建，请核实后尝试")

        # 2.构建对应的任务id及数据初始化
        input["task_id"] = input.get("task_id", uuid.uuid4())
        input["history"] = input.get("history", [])
        input["iteration_count"] = input.get("iteration_count", 0)

        # 3.创建子线程并执行
        thread = Thread(target=self._agent.invoke, args=(input,))
        thread.start()

        # 4.调用队列管理器监听数据并返回迭代器
        yield from self._agent_queue_manager.listen(input["task_id"])

    @property
    def agent_queue_manager(self) -> AgentQueueManager:
        """只读属性，返回智能体队列管理器"""
        return self._agent_queue_manager
