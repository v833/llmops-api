from langchain_community.document_loaders import UnstructuredFileLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain.storage import LocalFileStore
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import QianfanEmbeddingsEndpoint
from langchain.retrievers import MultiVectorRetriever

import uuid
import os


llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL"), api_key=os.getenv("OPENAI_API_KEY"))

file_path = os.path.join(os.path.dirname(__file__), "test.txt")

loader = UnstructuredFileLoader(file_path)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
)

docs = loader.load_and_split(text_splitter)

summary_chain = (
    {"doc": lambda x: x.page_content}
    | ChatPromptTemplate.from_template(
        "请总结以下文档的内容,字数不超过100字：\n\n{doc}"
    )
    | llm
    | StrOutputParser()
)

summaries = summary_chain.batch(
    docs,
    {
        "max_concurrency": 5,
    },
)

doc_ids = [str(uuid.uuid4()) for _ in enumerate(docs)]

summary_docs = [
    Document(
        page_content=summary,
        metadata={"doc_id": doc_ids[idx]},
    )
    for idx, summary in enumerate(summaries)
]

byte_store = LocalFileStore("./multi-vector")

db = FAISS.from_documents(
    summary_docs,
    embedding=QianfanEmbeddingsEndpoint(
        qianfan_ak="uexDJXSAF3qDg7tR3vkQZLOS",
        qianfan_sk="ovpeF9z5CcZleDczaFuc49AVhOjxGezS",
        model="embedding-v1",
    ),
)

retriever = MultiVectorRetriever(
    vectorstore=db,
    byte_store=byte_store,
    id_key="doc_id",
)

retriever.docstore.mset(list(zip(doc_ids, docs)))

search_docs = retriever.invoke("推荐一些潮州特产?")
print(search_docs)
print(len(search_docs))
