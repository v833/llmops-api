from internal.core.workflow.entites.node_entity import (
    BaseNodeData,
    NodeResult,
    NodeStatus,
)
from internal.core.workflow.entites.variable_entity import (
    VARIABLE_TYPE_DEFAULT_VALUE_MAP,
    VariableValueType,
)
from internal.core.workflow.entites.workflow_entity import WorkflowState
from internal.core.workflow.nodes.base_node import BaseNode
from internal.core.workflow.nodes.end.end_entity import EndNodeData


class EndNode(BaseNode):
    node_data: BaseNodeData

    def invoke(self, state: WorkflowState, config=None, **kwargs) -> WorkflowState:
        outputs = self.node_data.outputs

        outputs_dict = {}

        for output in outputs:
            if output.value.type == VariableValueType.LITERAL:
                outputs_dict[output.name] = output.value.content
            else:
                for node_result in state["node_results"]:
                    if node_result.node_data.id == output.value.content.ref_node_id:
                        outputs_dict[output.name] = node_result.outputs.get(
                            output.value.content.ref_var_name,
                            VARIABLE_TYPE_DEFAULT_VALUE_MAP.get(output.type),
                        )

        return {
            "outputs": outputs_dict,
            "node_results": [
                NodeResult(
                    node_data=self.node_data,
                    status=NodeStatus.SUCCESSED,
                    inputs={},
                    outputs=outputs_dict,
                )
            ],
        }
