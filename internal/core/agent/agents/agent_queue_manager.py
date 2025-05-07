import uuid
import queue
from queue import Queue
from uuid import UUID
from redis import Redis
from typing import Generator
import time
from internal.entity.conversation_entity import InvokeFrom
from internal.core.agent.entities import AgentQueueEvent, QueueEvent


class AgentQueueManager:
    q: Queue
    user_id: UUID
    task_id: UUID
    invoke_from: InvokeFrom
    redis_client: Redis

    def __init__(
        self,
        user_id: UUID,
        task_id: UUID,
        invoke_from: InvokeFrom,
        redis_client: Redis,
    ) -> None:

        self.q = Queue()
        self.user_id = user_id
        self.task_id = task_id
        self.invoke_from = invoke_from
        self.redis_client = redis_client

        user_prefix = (
            "account"
            if invoke_from in [InvokeFrom.WEB_APP, InvokeFrom.DEBUGGER]
            else "end-user"
        )

        self.redis_client.setex(
            self.generate_task_belong_cache_key(task_id),
            1800,
            f"{user_prefix}-{str(user_id)}",
        )

    def listen(self) -> Generator[AgentQueueEvent, None, None]:
        """监听队列信息"""
        listen_timeout = 600
        start_time = time.time()
        last_ping_time = 0

        while True:
            try:
                item = self.q.get(timeout=1)
                if item is None:
                    break
                yield item
            except queue.Empty:
                continue
            finally:
                # 计算获取数据的总耗时
                elapsed_time = time.time() - start_time

                # 每10秒发起一个ping请求
                if elapsed_time // 10 > last_ping_time:
                    self.publish(
                        AgentQueueEvent(
                            id=uuid.uuid4(),
                            task_id=self.task_id,
                            event=QueueEvent.PING,
                        )
                    )
                    last_ping_time = elapsed_time // 10

                # 检测任务是否超时
                if elapsed_time > listen_timeout:
                    self.publish(
                        AgentQueueEvent(
                            id=uuid.uuid4(),
                            task_id=self.task_id,
                            event=QueueEvent.TIMEOUT,
                        )
                    )

                # 检测任务是否被停止
                if self._is_stopped():
                    self.publish(
                        AgentQueueEvent(
                            id=uuid.uuid4(),
                            task_id=self.task_id,
                            event=QueueEvent.STOP,
                        )
                    )

    def stop_listen(self) -> None:
        """停止监听队列信息"""
        self.q.put(None)

    def publish(self, agent_queue_event: AgentQueueEvent) -> None:
        """发布事件信息到队列"""
        # 1.将事件添加到队列中
        self.q.put(agent_queue_event)

        # 2.检测事件类型是否为需要停止的类型，涵盖STOP、ERROR、TIMEOUT、AGENT_END
        if agent_queue_event.event in [
            QueueEvent.STOP,
            QueueEvent.ERROR,
            QueueEvent.TIMEOUT,
            QueueEvent.AGENT_END,
        ]:
            self.stop_listen()

    def publish_error(self, error) -> None:
        """发布错误信息到队列"""
        self.publish(
            AgentQueueEvent(
                id=uuid.uuid4(),
                task_id=self.task_id,
                event=QueueEvent.ERROR,
                observation=str(error),
            )
        )

    def _is_stopped(self) -> bool:
        """检测任务是否停止"""
        task_stopped_cache_key = self.generate_task_stopped_cache_key(self.task_id)
        result = self.redis_client.get(task_stopped_cache_key)

        if result is not None:
            return True
        return False

    @classmethod
    def generate_task_belong_cache_key(cls, task_id: UUID) -> str:
        """生成任务专属的缓存键"""
        return f"generate_task_belong:{str(task_id)}"

    @classmethod
    def generate_task_stopped_cache_key(cls, task_id: UUID) -> str:
        """生成任务已停止的缓存键"""
        return f"generate_task_stopped:{str(task_id)}"
