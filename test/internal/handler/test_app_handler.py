import pytest

from pkg.response import HttpCode


class TestAppHandler:
    """app控制器的测试类"""

    @pytest.mark.parametrize(
        "app_id, query",
        [
            ("2b2a4e9d-cfc5-4021-bcce-6f098b6c940b", None),
            ("2b2a4e9d-cfc5-4021-bcce-6f098b6c940b", "你好，你是?"),
        ],
    )
    def test_completion(self, app_id, query, client):
        resp = client.post(f"/apps/{app_id}/debug", json={"query": query})
        assert resp.status_code == 200
        if query is None:
            assert resp.json.get("code") == HttpCode.VALIDATE_ERROR
        else:
            assert resp.json.get("code") == HttpCode.SUCCESS
