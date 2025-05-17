from dataclasses import dataclass
from typing import Any, Union

from flask import request
from injector import inject
from langchain_core.tools import BaseTool

from internal.core.language_model import LanguageModelManager
from internal.core.tools.api_tools.entites import ToolEntity
from internal.core.tools.api_tools.providers import ApiProviderManager
from internal.core.tools.builtin_tools.providers import BuiltinProviderManager
from internal.entity.app_entity import DEFAULT_APP_CONFIG
from internal.lib.helper import datetime_to_timestamp, get_value_type
from internal.model import (
    App,
    ApiTool,
    Dataset,
    AppConfig,
    AppConfigVersion,
    AppDatasetJoin,
)
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from ..core.language_model.entities.model_entity import ModelParameterType


@inject
@dataclass
class AppConfigService(BaseService):
    """应用配置服务"""

    db: SQLAlchemy
    api_provider_manager: ApiProviderManager
    builtin_provider_manager: BuiltinProviderManager
    language_model_manager: LanguageModelManager

    def get_draft_app_config(self, app: App) -> dict[str, Any]:
        """根据传递的应用获取该应用的草稿配置"""
        # 1.提取应用的草稿配置
        draft_app_config = app.draft_app_config

        # 2.校验model_config配置信息，等待多LLM实现的时候再来完成
        validate_model_config = self._process_and_validate_model_config(
            draft_app_config.model_config
        )
        if draft_app_config.model_config != validate_model_config:
            self.update(draft_app_config, model_config=validate_model_config)

        # 3.循环遍历工具列表删除已经被删除的工具信息
        tools, validate_tools = self._process_and_validate_tools(draft_app_config.tools)

        # 4.判断是否需要更新草稿配置中的工具列表信息
        if draft_app_config.tools != validate_tools:
            # 14.更新草稿配置中的工具列表
            self.update(draft_app_config, tools=validate_tools)

        # 5.校验知识库列表，如果引用了不存在/被删除的知识库，需要剔除数据并更新，同时获取知识库的额外信息
        datasets, validate_datasets = self._process_and_validate_datasets(
            draft_app_config.datasets
        )

        # 6.判断是否存在已删除的知识库，如果存在则更新
        if set(validate_datasets) != set(draft_app_config.datasets):
            self.update(draft_app_config, datasets=validate_datasets)

        # todo:7.校验工作流列表对应的数据
        workflows = []

        # 20.将数据转换成字典后返回
        return self._process_and_transformer_app_config(
            tools, workflows, datasets, draft_app_config
        )

    def get_app_config(self, app: App) -> dict[str, Any]:
        """根据传递的应用获取该应用的运行配置"""
        # 1.提取应用的草稿配置
        app_config = app.app_config

        # 2.校验model_config配置信息，等待多LLM实现的时候再来完成
        validate_model_config = self._process_and_validate_model_config(
            app_config.model_config
        )
        if app_config.model_config != validate_model_config:
            self.update(app_config, model_config=validate_model_config)

        # 3.循环遍历工具列表删除已经被删除的工具信息
        tools, validate_tools = self._process_and_validate_tools(app_config.tools)

        # 4.判断是否需要更新草稿配置中的工具列表信息
        if app_config.tools != validate_tools:
            # 14.更新草稿配置中的工具列表
            self.update(app_config, tools=validate_tools)

        # 5.校验知识库列表，如果引用了不存在/被删除的知识库，需要剔除数据并更新，同时获取知识库的额外信息
        app_dataset_joins = app_config.app_dataset_joins
        origin_datasets = [
            str(app_dataset_join.dataset_id) for app_dataset_join in app_dataset_joins
        ]
        datasets, validate_datasets = self._process_and_validate_datasets(
            origin_datasets
        )

        # 6.判断是否存在已删除的知识库，如果存在则更新
        for dataset_id in set(origin_datasets) - set(validate_datasets):
            with self.db.auto_commit():
                self.db.session.query(AppDatasetJoin).filter(
                    AppDatasetJoin.dataset_id == dataset_id
                ).delete()

        # todo:7.校验工作流列表对应的数据
        workflows = []

        # 20.将数据转换成字典后返回
        return self._process_and_transformer_app_config(
            tools, workflows, datasets, app_config
        )

    def get_langchain_tools_by_tools_config(
        self, tools_config: list[dict]
    ) -> list[BaseTool]:
        """根据传递的工具配置列表获取langchain工具列表"""
        # 1.循环遍历所有工具配置列表信息
        tools = []
        for tool in tools_config:
            # 2.根据不同的工具类型执行不同的操作
            if tool["type"] == "builtin_tool":
                # 3.内置工具，通过builtin_provider_manager获取工具实例
                builtin_tool = self.builtin_provider_manager.get_tool(
                    tool["provider"]["id"], tool["tool"]["name"]
                )
                if not builtin_tool:
                    continue
                tools.append(builtin_tool(**tool["tool"]["params"]))
            else:
                # 4.API工具，首先根据id找到ApiTool记录，然后创建示例
                api_tool = self.get(ApiTool, tool["tool"]["id"])
                if not api_tool:
                    continue
                tools.append(
                    self.api_provider_manager.get_tool(
                        ToolEntity(
                            id=str(api_tool.id),
                            name=api_tool.name,
                            url=api_tool.url,
                            method=api_tool.method,
                            description=api_tool.description,
                            headers=api_tool.provider.headers,
                            parameters=api_tool.parameters,
                        )
                    )
                )

        return tools

    @classmethod
    def _process_and_transformer_app_config(
        cls,
        tools: list[dict],
        workflows: list[dict],
        datasets: list[dict],
        app_config: Union[AppConfig, AppConfigVersion],
    ) -> dict[str, Any]:
        """根据传递的插件列表、工作流列表、知识库列表以及应用配置创建字典信息"""
        return {
            "id": str(app_config.id),
            "model_config": app_config.model_config,
            "dialog_round": app_config.dialog_round,
            "preset_prompt": app_config.preset_prompt,
            "tools": tools,
            "workflows": workflows,
            "datasets": datasets,
            "retrieval_config": app_config.retrieval_config,
            "long_term_memory": app_config.long_term_memory,
            "opening_statement": app_config.opening_statement,
            "opening_questions": app_config.opening_questions,
            "speech_to_text": app_config.speech_to_text,
            "text_to_speech": app_config.text_to_speech,
            "suggested_after_answer": app_config.suggested_after_answer,
            "review_config": app_config.review_config,
            "updated_at": datetime_to_timestamp(app_config.updated_at),
            "created_at": datetime_to_timestamp(app_config.created_at),
        }

    def _process_and_validate_tools(
        self, origin_tools: list[dict]
    ) -> tuple[list[dict], list[dict]]:
        """根据传递的原始工具信息进行处理和校验"""
        # 1.循环遍历工具列表删除已被删除的工具
        validate_tools = []
        tools = []
        for tool in origin_tools:
            if tool["type"] == "builtin_tool":
                # 2.查询内置工具提供者，并检测是否存在
                provider = self.builtin_provider_manager.get_provider(
                    tool["provider_id"]
                )
                if not provider:
                    continue

                # 3.获取提供者下的工具实体，并检测是否存在
                tool_entity = provider.get_tool_entity(tool["tool_id"])
                if not tool_entity:
                    continue

                # 4.判断工具的params和草稿中的params是否一致，如果不一致则全部重置为默认值（或者考虑删除这个工具的引用）
                param_keys = set([param.name for param in tool_entity.params])
                params = tool["params"]
                if set(tool["params"].keys()) - param_keys:
                    params = {
                        param.name: param.default
                        for param in tool_entity.params
                        if param.default is not None
                    }

                # 5.数据都存在，并且参数已经校验完毕，可以将数据添加到validate_tools
                validate_tools.append({**tool, "params": params})

                # 6.组装内置工具展示信息
                provider_entity = provider.provider_entity
                tools.append(
                    {
                        "type": "builtin_tool",
                        "provider": {
                            "id": provider_entity.name,
                            "name": provider_entity.name,
                            "label": provider_entity.label,
                            "icon": f"{request.scheme}://{request.host}/builtin-tools/{provider_entity.name}/icon",
                            "description": provider_entity.description,
                        },
                        "tool": {
                            "id": tool_entity.name,
                            "name": tool_entity.name,
                            "label": tool_entity.label,
                            "description": tool_entity.description,
                            "params": tool["params"],
                        },
                    }
                )
            elif tool["type"] == "api_tool":
                # 7.查询数据库获取对应的工具记录，并检测是否存在
                tool_record = (
                    self.db.session.query(ApiTool)
                    .filter(
                        ApiTool.provider_id == tool["provider_id"],
                        ApiTool.name == tool["tool_id"],
                    )
                    .one_or_none()
                )
                if not tool_record:
                    continue

                # 8.数据校验通过，往validate_tools中添加数据
                validate_tools.append(tool)

                # 9.组装api工具展示信息
                provider = tool_record.provider
                tools.append(
                    {
                        "type": "api_tool",
                        "provider": {
                            "id": str(provider.id),
                            "name": provider.name,
                            "label": provider.name,
                            "icon": provider.icon,
                            "description": provider.description,
                        },
                        "tool": {
                            "id": str(tool_record.id),
                            "name": tool_record.name,
                            "label": tool_record.name,
                            "description": tool_record.description,
                            "params": {},
                        },
                    }
                )

        return tools, validate_tools

    def _process_and_validate_datasets(
        self, origin_datasets: list[dict]
    ) -> tuple[list[dict], list[dict]]:
        """根据传递的知识库并返回知识库配置与校验后的数据"""
        # 1.校验知识库配置列表，如果引用了不存在的/被删除的知识库，则需要剔除数据并更新，同时获取知识库的额外信息
        datasets = []
        dataset_records = (
            self.db.session.query(Dataset).filter(Dataset.id.in_(origin_datasets)).all()
        )
        dataset_dict = {
            str(dataset_record.id): dataset_record for dataset_record in dataset_records
        }
        dataset_sets = set(dataset_dict.keys())

        # 2.计算存在的知识库id列表，为了保留原始顺序，使用列表循环的方式来判断
        validate_datasets = [
            dataset_id for dataset_id in origin_datasets if dataset_id in dataset_sets
        ]

        # 3.循环获取知识库数据
        for dataset_id in validate_datasets:
            dataset = dataset_dict.get(str(dataset_id))
            datasets.append(
                {
                    "id": str(dataset.id),
                    "name": dataset.name,
                    "icon": dataset.icon,
                    "description": dataset.description,
                }
            )

        return datasets, validate_datasets

    def _process_and_validate_model_config(
        self, origin_model_config: dict[str, Any]
    ) -> dict[str, Any]:
        """根据传递的模型配置处理并校验，随后返回校验后的信息"""
        # 1.判断model_config是否为字典，如果不是则直接返回默认值
        if not isinstance(origin_model_config, dict):
            return DEFAULT_APP_CONFIG["model_config"]

        # 2.提取origin_model_config中provider、model、parameters对应的信息
        model_config = {
            "provider": origin_model_config.get("provider", ""),
            "model": origin_model_config.get("model", ""),
            "parameters": origin_model_config.get("parameters", {}),
        }

        # 3.判断provider是否存在、类型是否正确，如果不符合规则则返回默认值
        if not model_config["provider"] or not isinstance(
            model_config["provider"], str
        ):
            return DEFAULT_APP_CONFIG["model_config"]
        provider = self.language_model_manager.get_provider(model_config["provider"])
        if not provider:
            return DEFAULT_APP_CONFIG["model_config"]

        # 4.判断model是否存在、类型是否正确，如果不符合则返回默认值
        if not model_config["model"] or not isinstance(model_config["model"], str):
            return DEFAULT_APP_CONFIG["model_config"]
        model_entity = provider.get_model_entity(model_config["model"])
        if not model_entity:
            return DEFAULT_APP_CONFIG["model_config"]

        # 5.判断parameters信息类型是否错误，如果错误则设置为默认值
        if not isinstance(model_config["parameters"], dict):
            model_config["parameters"] = {
                parameter.name: parameter.default
                for parameter in model_entity.parameters
            }

        # 6.剔除传递的多余的parameter，亦或者是少传递的参数使用默认值补上
        parameters = {}
        for parameter in model_entity.parameters:
            # 7.从model_config中获取参数值，如果不存在则设置为默认值
            parameter_value = model_config["parameters"].get(
                parameter.name, parameter.default
            )

            # 8.判断参数是否必填
            if parameter.required:
                # 9.参数必填，则值不允许为None，如果为None则设置默认值
                if parameter_value is None:
                    parameter_value = parameter.default
                else:
                    # 10.值非空则校验数据类型是否正确，不正确则设置默认值
                    if get_value_type(parameter_value) != parameter.type.value:
                        parameter_value = parameter.default
            else:
                # 11.参数非必填，数据非空的情况下需要校验
                if parameter_value is not None:
                    if get_value_type(parameter_value) != parameter.type.value:
                        parameter_value = parameter.default

            # 12.判断参数是否存在options，如果存在则数值必须在options中选择
            if parameter.options and parameter_value not in parameter.options:
                parameter_value = parameter.default

            # 13.参数类型为int/float，如果存在min/max时候需要校验
            if (
                parameter.type in [ModelParameterType.INT, ModelParameterType.FLOAT]
                and parameter_value is not None
            ):
                # 14.校验数值的min/max
                if (parameter.min and parameter_value < parameter.min) or (
                    parameter.max and parameter_value > parameter.max
                ):
                    parameter_value = parameter.default

            parameters[parameter.name] = parameter_value

        # 15.完成数据校验，赋值parameters参数
        model_config["parameters"] = parameters

        return model_config
