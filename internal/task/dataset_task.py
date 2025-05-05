from uuid import UUID

from celery import shared_task


@shared_task
def delete_dataset(dataset_id: UUID):
    """根据传递的知识库id删除特定的知识库信息"""
    from internal.extension.module_extension import injector
    from internal.service import IndexingService

    indexing_service = injector.get(IndexingService)
    indexing_service.delete_dataset(dataset_id)
