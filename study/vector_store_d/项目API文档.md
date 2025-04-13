# LLMOps 项目 API 文档

应用 API 接口统一以 JSON 格式返回，并且包含 3 个字段：`code`、`data` 和 `message`，分别代表`业务状态码`、`业务数据`和`接口附加信息`。

`业务状态码`共有 6 种，其中只有 `success(成功)` 代表业务操作成功，其他 5 种状态均代表失败，并且失败时会附加相关的信息：`fail(通用失败)`、`not_found(未找到)`、`unauthorized(未授权)`、`forbidden(无权限)`和`validate_error(数据验证失败)`。

接口示例：

```json
{
    "code": "success",
    "data": {
        "redirect_url": "https://github.com/login/oauth/authorize?client_id=f69102c6b97d90d69768&redirect_uri=http%3A%2F%2Flocalhost%3A5001%2Foauth%2Fauthorize%2Fgithub&scope=user%3Aemail"
    },
    "message": ""
}
```

带有分页数据的接口会在 `data` 内固定传递 `list` 和 `paginator` 字段，其中 `list` 代表分页后的列表数据，`paginator` 代表分页的数据。

`paginator` 内存在 4 个字段：`current_page(当前页数)` 、`page_size(每页数据条数)`、`total_page(总页数)`、`total_record(总记录条数)`，示例数据如下：

```json
{
    "code": "success",
    "data": {
        "list": [
            {
                "app_count": 0,
                "created_at": 1713105994,
                "description": "这是专门用来存储慕课LLMOps课程信息的知识库",
                "document_count": 13,
                "icon": "https://imooc-llmops-1257184990.cos.ap-guangzhou.myqcloud.com/2024/04/07/96b5e270-c54a-4424-aece-ff8a2b7e4331.png",
                "id": "c0759ca8-2d35-4480-83a8-1f41f29d1401",
                "name": "慕课LLMOps课程知识库",
                "updated_at": 1713106758,
                "word_count": 8850
            }
        ],
        "paginator": {
            "current_page": 1,
            "page_size": 20,
            "total_page": 1,
            "total_record": 2
        }
    },
    "message": ""
}
```

如果接口需要授权，需要在 `headers` 中添加 `Authorization` ，并附加 `access_token` 即可完成授权登录，示例：

```json
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MTY0NTY3OTgsImlzcyI6ImxsbW9wcyIsInN1YiI6ImM5MDljMWRiLWIyMmUtNGZlNi04OGIyLWIyZTkxZWFiMWE3YiJ9.JDAtWDBBGiXa_XFihfopRe4Cz-RQ9_TAcno9w81tNbE
```

## 01. 应用模块

### 1.1 [todo]获取应用基础信息

- **接口说明**：传递对应的应用 id，获取当前应用的基础信息+配置信息等内容。

- **接口信息**：`授权`+`GET:/apps/:app_id`

- **接口参数**：

  - 请求参数：
    - `app_id -> uuid`：路由参数，必填，需要获取的应用 id。
  - 响应参数：
    - `id -> uuid`：应用 id，类型为 uuid。
    - `name -> string`：应用名称。
    - `icon -> string`：应用图标。
    - `description -> string`：应用描述。
    - `published_app_config_id -> uuid`：已发布应用配置 id，如果不存在则为 null。
    - `drafted_app_config_id -> uuid`：草稿应用配置 id，如果不存在则为 null。
    - `debug_conversation_id -> uuid`：调试会话记录 id，如果不存在则为 null。
    - `published_app_config/drafted_app_config -> json`：应用配置信息，涵盖草稿配置、已发布配置，如果没有则为 null，两个配置的变量信息一致。
      - `id -> uuid`：应用配置 id。
      - `model_config -> json`：模型配置，类型为 json。
        - `dialog_round -> int`：携带上下文轮数，类型为非负整型。
      - `memory_mode -> string`：记忆类型，涵盖长记忆 `long_term_memory` 和 `none` 代表无。
      - `status -> string`：应用配置的状态，`drafted` 代表草稿、`published` 代表已发布配置。
      - `updated_at -> int`：应用配置的更新时间。
      - `created_at -> int`：应用配置的创建时间。
    - `updated_at -> int`：应用的更新时间。
    - `created_at -> int`：应用的创建时间。

- **响应示例**：

  ```json
  {
      "code": "success",
      "data": {
          "id": "5e7834dc-bbca-4ee5-9591-8f297f5acded",
          "name": "慕课LLMOps聊天机器人",
          "icon": "https://imooc-llmops-1257184990.cos.ap-guangzhou.myqcloud.com/2024/04/23/e4422149-4cf7-41b3-ad55-ca8d2caa8f13.png",
          "description": "这是一个慕课LLMOps的Agent应用",
          "published_app_config_id": null,
          "drafted_app_config_id": null,
          "debug_conversation_id": "1550b71a-1444-47ed-a59d-c2f080fbae94",
          "published_app_config": null,
          "drafted_app_config": {
              "id": "755dc464-67cd-42ef-9c56-b7528b44e7c8",
              "model_config": {
                  "dialog_round": 3
              },
              "memory_mode": "long_term_memory",
              "status": "draft",
              "updated_at": 1714053834,
              "created_at": 1714053834
          },
          "updated_at": 1714053834,
          "created_at": 1714053834
      },
      "message": ""
  }
  ```

### 1.2 [todo]更新应用草稿配置信息

- **接口说明**：更新应用的草稿配置信息，涵盖：模型配置、长记忆模式等，该接口会查找该应用原始的草稿配置并进行更新，如果没有原始草稿配置，则创建一个新配置作为草稿配置。

- **接口信息**：`授权`+`POST:/apps/:app_id/config`

- **接口参数**：

  - 请求参数：
    - `app_id -> str`：需要修改配置的应用 id。
    - `model_config -> json`：模型配置信息。
      - `dialog_round -> int`：携带上下文轮数，类型为非负整型。
    - `memory_mode -> string`：记忆类型，涵盖长记忆 `long_term_memory` 和 `none` 代表无。

- **请求示例**：

  ```json
  {
      "model_config": {
          "dialog_round": 10
      },
      "memory_mode": "long_term_memory"
  }
  ```

- **响应示例**：

  ```json
  {
      "code": "success",
      "data": {},
      "message": "更新AI应用配置成功"
  }
  ```

### 1.3 [todo]获取应用调试长记忆

- **接口说明**：用于获取指定应用的长记忆内容，如果该应用并没有开启长记忆，则会抛出错误信息。

- **接口信息**：`授权`+`GET:/apps/:app_id/long-term-memory`

- **接口参数**：

  - 请求参数：
    - `app_id -> str`：需要获取长记忆的应用 id。
  - 响应参数：
    - `summary -> str`：该应用最新调试会话的长记忆内容。

- **响应示例**：

  ```json
  {
      "code": "success",
      "data": {
          "summary": "人类自我介绍为慕小课，并要求人工智能解释LLM（大型语言模型）的概念。人工智能将LLM描述为一种基于深度学习的模型，通常建立在Transformer架构上，用于自然语言处理任务。LLM经历了一个预训练阶段，在那里他们从大量的文本数据中学习语言结构，比如维基百科的文章和书籍。它们利用自我注意机制来有效地处理长程依赖关系。经过预训练后，LLM可以针对特定的应用程序进行微调，使其功能适应文本生成、理解和分类等任务。LLM由于其多功能性和强大的语言理解和生成能力，被广泛应用于虚拟助理、翻译、情绪分析、医疗保健、金融等领域，代表了自然语言处理的前沿技术。"
      },
      "message": ""
  }
  ```

### 1.4 [todo]更新应用调试长记忆

- **接口说明**：用于更新对应应用的调试长记忆内容，如果应用没有开启长记忆功能，则调用接口会发生报错。

- **接口信息**：`授权`+`POST:/apps/:app_id/long-term-memory`

- **接口参数**：

  - 请求参数：
    - `app_id -> str`：路由参数，需要更新长记忆的应用 id。
    - `summary -> str`：需要更新的长记忆内容。

- **请求示例**：

  ```json
  {
      "summary": "人类介绍自己叫慕小课，喜欢打篮球。"
  }
  ```

- **响应示例**：

  ```json
  {
      "code": "success",
      "data": {},
      "message": "更新AI应用长记忆成功"
  }
  ```

### 1.5 [todo]应用调试对话

- **接口说明**：用于在编排 AI 应用时进行 debug 调试，如果当前应用没有草稿配置，则使用发布配置进行调试，如果有草稿配置则以草稿配置信息进行调试。

- **接口信息**：`授权`+`POST:/apps/:app_id/debug`

- **接口参数**：

  - 请求参数：
    - `app_id -> str`：路由参数，需要调试的 AI 应用 id，格式为 uuid。
    - `query -> str`：用户发起的提问信息。
  - 响应参数：
    - `id -> uuid`：响应消息的 id，类型为 uuid。
    - `conversation_id -> uuid`：消息关联会话的 id，类型为 uuid。
    - `query -> str`：人类的输入字符串。
    - `answer -> str`：AI 的生成内容。
    - `answer_tokens -> int`：生成内容消耗的 Token 数。
    - `response_latency -> float`：响应消耗的时间，单位为毫秒。
    - `updated_at -> int`：消息的更新时间。
    - `created_at -> int`：消息的创建时间。

- **请求示例**：

  ```json
  {
      "query": "能详细讲解下LLM是什么吗？"
  }
  ```

- **响应示例**：

  ```json
  {
      "code": "success",
      "data": {
          "id": "1550b71a-1444-47ed-a59d-c2f080fbae94",
          "conversation_id": "2d7d3e3f-95c9-4d9d-ba9c-9daaf09cc8a8",
          "query": "能详细讲解下LLM是什么吗？",
          "answer": "LLM 即 Large Language Model，大语言模型，是一种基于深度学习的自然语言处理模型，具有很高的语言理解和生成能力，能够处理各式各样的自然语言任务，例如文本生成、问答、翻译、摘要等。它通过在大量的文本数据上进行训练，学习到语言的模式、结构和语义知识。",
          "answer_tokens": 1454,
          "response_latency": 8541,
          "updated_at": 1714053834,
          "created_at": 1714053834
      },
      "message": ""
  }
  ```

### 1.6 [todo]获取应用调试历史对话列表

- **接口说明**：用于获取应用调试历史对话列表信息，该接口支持分页，单次最多返回 20 组对话消息，并且分页以时间字段进行降序，接口不会返回软删除对应的数据。

- **接口信息**：`授权`+`GET:/apps/:app_id/messages`

- **接口参数**：

  - 请求参数：
    - `app_id -> str`：路由参数，需要调试的 AI 应用 id，格式为 uuid。
  - 响应参数：
    - `id -> uuid`：响应消息的 id，类型为 uuid。
    - `conversation_id -> uuid`：消息关联会话的 id，类型为 uuid。
    - `query -> str`：人类的输入字符串。
    - `answer -> str`：AI 的生成内容。
    - `answer_tokens -> int`：生成内容消耗的 Token 数。
    - `response_latency -> float`：响应消耗的时间，单位为毫秒。
    - `updated_at -> int`：消息的更新时间。
    - `created_at -> int`：消息的创建时间。

- **响应示例**：

  ```json
  {
      "code": "success",
      "data": {
          "list": [
              {
                  "id": "1550b71a-1444-47ed-a59d-c2f080fbae94",
                  "conversation_id": "2d7d3e3f-95c9-4d9d-ba9c-9daaf09cc8a8",
                  "query": "能详细讲解下LLM是什么吗？",
                  "answer": "LLM 即 Large Language Model，大语言模型，是一种基于深度学习的自然语言处理模型，具有很高的语言理解和生成能力，能够处理各式各样的自然语言任务，例如文本生成、问答、翻译、摘要等。它通过在大量的文本数据上进行训练，学习到语言的模式、结构和语义知识。",
                  "answer_tokens": 1454,
                  "response_latency": 8541,
                  "updated_at": 1714053834,
                  "created_at": 1714053834
              }
          ],
          "paginator": {
              "current_page": 1,
              "page_size": 20,
              "total_page": 1,
              "total_record": 2
          }
      },
      "message": ""
  }
  ```


### 1.7 [todo]删除特定的调试消息

- **接口说明**：用于删除 AI 应用调试对话过程中指定的消息，该删除会在后端执行软删除操作，并且只有当会话 id 和消息 id 都匹配上时，才会删除对应的调试消息。

- **接口信息**：`授权`+`POST:/apps/:app_id/messages/:message_id/delete`

- **接口参数**：

  - 请求参数：
    - `app_id -> uuid`：路由参数，需要删除消息归属的应用 id，格式为 uuid。
    - `message_id -> uuid`：路由参数，需要删除的消息 id，格式为 uuid。

- **请求示例**：

  ```json
  {
      "app_id": "1550b71a-1444-47ed-a59d-c2f080fbae94",
      "message_id": "2d7d3e3f-95c9-4d9d-ba9c-9daaf09cc8a8"
  }
  ```

- **响应示例**：

  ```json
  {
      "code": "success",
      "data": {},
      "message": "删除调试信息成功"
  }
  ```

  
