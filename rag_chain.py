from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
import os
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from uuid import uuid4
from templates.prompt import QA_PROMPT
from dotenv import load_dotenv
load_dotenv()


AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_DEPLOYMENT_ID = os.getenv('AZURE_OPENAI_DEPLOYMENT_ID')
AZURE_OPENAI_KEY = os.getenv('AZURE_OPENAI_KEY')
AZURE_API_VERSION = os.getenv('AZURE_API_VERSION')
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
pc = Pinecone(api_key=PINECONE_API_KEY)


index_name = "ocbc-hr-gpt"  # change if desired
index = pc.Index(index_name)

llm = AzureChatOpenAI(
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            azure_deployment=AZURE_OPENAI_DEPLOYMENT_ID,
            api_version=AZURE_API_VERSION,
            api_key=AZURE_OPENAI_KEY,
            temperature=0.0,
            verbose=True,
        )

embedding_llm = AzureOpenAIEmbeddings(
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            azure_deployment='embedding-ada-crayon',
            api_key=AZURE_OPENAI_KEY,
            api_version=AZURE_API_VERSION,
        )

vector_store = PineconeVectorStore(index=index, embedding=embedding_llm)
retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={'k': 6})

prompt = PromptTemplate.from_template(QA_PROMPT)


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

def caller(message):
    response = rag_chain.invoke(message)
    return response