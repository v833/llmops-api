from wtforms import Field


class ListField(Field):
    """自定义list字段，用于存储列表型数据"""

    data: list = None

    def process_formdata(self, valuelist):
        if valuelist is not None and isinstance(valuelist, list):
            self.data = valuelist

    def _value(self):
        return self.data if self.data else []
