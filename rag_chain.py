from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import PromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings, ChatOpenAI, OpenAIEmbeddings
import os
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from uuid import uuid4
from templates.prompt import QA_PROMPT, CV_sumerrizer, QUESTION_PROMPT
from dotenv import load_dotenv
from operator import itemgetter
load_dotenv()


AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_DEPLOYMENT_ID = os.getenv('AZURE_OPENAI_DEPLOYMENT_ID')
AZURE_OPENAI_KEY = os.getenv('AZURE_OPENAI_KEY')
AZURE_API_VERSION = os.getenv('AZURE_API_VERSION')
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
pc = Pinecone(api_key=PINECONE_API_KEY)


index_name = "ocbc-cv-gpt-3-small"  # change if desired
index = pc.Index(index_name)

### AZURE
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
            azure_deployment='embedding-3-small',
            api_key=AZURE_OPENAI_KEY,
            api_version=AZURE_API_VERSION,
        )

### OPENAI
# llm = ChatOpenAI(
#             temperature=0.0,
#             verbose=True,
#             model="gpt-4o-mini",
#         )

# embedding_llm = OpenAIEmbeddings(model="text-embedding-3-small")


vector_store = PineconeVectorStore(index=index, embedding=embedding_llm)
retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={'k': 4})

prompt = PromptTemplate.from_template(QA_PROMPT)




cv_summarizer_prompt = PromptTemplate.from_template(CV_sumerrizer)
cv_summarizer_chain = (
    RunnablePassthrough() | 
    {"cv": itemgetter("cv")}
    | cv_summarizer_prompt
    | llm
    | StrOutputParser()
)

# QA chain
qa_prompt = PromptTemplate.from_template(QA_PROMPT)

# Merged chain
# merged_rag_chain = (
#     {"cv": RunnablePassthrough(), "job_listing": RunnablePassthrough()}
#     | cv_summarizer_chain
#     | (lambda x: {"job_listing": retriever.invoke(x), "cv": x}) #bikin job listing summarizer
#     | qa_prompt
#     | llm
#     | StrOutputParser()
# )

merged_rag_chain = (
    {"cv": RunnablePassthrough(), "job_listing": RunnablePassthrough()} | RunnablePassthrough()
    |  {"job_listing": itemgetter("cv") | cv_summarizer_chain | retriever, "cv": itemgetter("cv")} #bikin job listing summarizer
    | qa_prompt
    | llm
    | StrOutputParser()
)

question_prompt = PromptTemplate.from_template(QUESTION_PROMPT)
question_chain = (
    {"cv": itemgetter("cv"),
     "user_question": itemgetter("user_question"),
     "retriever_docs": itemgetter("user_question") | retriever} 
    | RunnablePassthrough()
    | {"summary": cv_summarizer_chain, "user_question": itemgetter("user_question"), "retriever_docs": itemgetter("retriever_docs")}
    | RunnablePassthrough()
    | question_prompt
    | llm
    | StrOutputParser()
)

cv = ""

def caller_cv(message):
    global cv
    response = merged_rag_chain.invoke({"cv": message})
    cv = message
    return response

def caller_question(message):
    global cv
    response = question_chain.invoke({"cv": cv, "user_question": message})
    return response



