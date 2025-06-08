from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationalRetrievalChain
from langchain.vectorstores.utils import DistanceStrategy
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage, Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
# from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.prompts import PromptTemplate
from langchain_cohere import CohereRerank
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from collections import defaultdict, Counter
from config.logger import logger
from config.env import env
from database.db import ChatHistory
from database.db_session import get_session

session = get_session()

def load_chat_history(channel_id):
    messages = session.query(ChatHistory).filter(channel_id == channel_id).limit(20).all()
    chat_history = []
    
    for msg in messages:
        if msg.role == "user":
            # chat_history.append(HumanMessage(content=msg.content))
            chat_history.append(f"User Question: {msg.content}")
        elif msg.role == "assistant":
            # chat_history.append(AIMessage(content=msg.content))
            chat_history.append(f"AI Response: {msg.content}")

    return "\n".join(chat_history[::-1])

def get_conversational_chain(retriever, channel_id):
    chat_history = load_chat_history(channel_id)
    
    prompt_template_with_chat_history = f'''
    You are an intelligent assistant designed to answer user questions strictly based on internal company policies and the user's query.

    Instructions:
        -Limit all responses to a maximum of 400 words
        -Primary Response Strategy:
            - When relevant context is available: Use only information explicitly stated in the provided context documents
            - When no relevant context is available: Politely acknowledge inability to provide specific information without revealing the RAG system architecture
        - Never return back the context that has been provided to you, as it may contain some information whose formatting is not user friendly, so only use the contenxt to generate a freash reponse and never show the context as it is on the response.  
        - Context Handling:
            - Never assume, infer, or fabricate information not directly present in the provided context
            - Do not include context signifier tokens in responses when context is explicitly mentioned in documents
            - If context exists but doesn't address the specific query, acknowledge this limitation appropriately
        - Graceful Response Templates:
            - Adhere to the Gracefull Response Template especially if the user is asking about numbers, do not hallucinat, state the relavent number present in the context.
            - In the response never say the word context to signify the document embeddings, in such scenarios always use "policies do not mention".
            - When no context is available: "I don't have specific information about [topic] available at the moment. I'm unable to provide details on this particular question."
            - When context is partial: "Based on the available information, I can tell you [what's available], but I don't have complete details about [missing aspects]."
            - When context is unclear: "I have limited information about [topic], but it doesn't provide enough detail to fully answer your question."
            - Alternative: "I'm not able to provide specific information about [topic] right now."
            - In case there is no context do not respond back with unneccessary information, do not respond back with responses like here is what I found, stick strictly to the user's query.  
        - Response Structure:
            - Keep answers concise and focused on essential information
            - Use clear formatting for readability
            - Prioritize direct answers over lengthy explanations
            - Maintain natural conversational tone without revealing system limitations
        - DO NOT FOLLOW the usual markdown systax instead follow the the syntax formating below.
        - Formatting Guidelines:
            - Follow the below formatting guidelines strictly
            - For Bold text enclose them within single asterisks: *bold* text
            - For Bullet Points make sure that the sentence starts with a single dash followed by space: - bullet point
            - For Italic text enclose them within single underscore: _italic_ text
            - Use headings when appropriate for clarity.

        - Detect and handle chitchat/small talk separately; do not treat these as policy questions or use them in the RAG pipeline.
        - When a user’s query relates to provided context but the prior answer wasn’t satisfactory, prompt them for the most relevant follow-up question.
        - Use the <Chat History>…</Chat History> block only to:
        - Understand what the user has already asked or what follow-up you’ve requested.
        - Check whether the user answered your last follow-up; if so, link their reply to that question.
        - Use the <Context>…</Context> block exclusively to answer policy questions.  
        - Don’t bring in information from chat history as content—only as query context.  
        - If the user asks about something covered by earlier AI responses in the history, recycle that exact answer rather than regenerating it.
        - If the user’s query isn’t in the <Context> block, reply with a graceful fallback:  
        “I don’t have specific information about [topic] available at the moment. I’m unable to provide details on this particular question.”

    ------------------------------------------------------------------------------------------------------------------------

    <Chat History> 
    {chat_history}
    </Chat History>
    ------------------------------------------------------------------------------------------------------------------------
    '''
    
    prompt_template_with_context = '''
    <Context> 
    {context}
    </Context>
    ------------------------------------------------------------------------------------------------------------------------

    <Prompt> 
    {question}
    </Prompt>
    ------------------------------------------------------------------------------------------------------------------------

    Answer:
    '''
    
    system_prompt = prompt_template_with_chat_history + prompt_template_with_context
    
    prompt = PromptTemplate(
        template=system_prompt,
        input_variables=["chat_history", "context", "question"]
    )

    memory = ConversationBufferMemory(
        memory_key="chat_history", 
        input_key="question",
        return_messages=True
    )
    
    chain = ConversationalRetrievalChain.from_llm(
        llm=ChatGoogleGenerativeAI(
            model=env.LLM_MODEL_NAME,
        ),
        retriever=retriever,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": prompt},
        verbose=True
    )

    return chain

def user_input(user_question, channel_id):
    # embeddings = CohereEmbeddings(model=env.EMBEDDING_MODEL)
    embeddings = GoogleGenerativeAIEmbeddings(model=env.EMBEDDING_MODEL)
    index_name = f"faiss_index/llama-3"

    new_db = FAISS.load_local(index_name, embeddings, allow_dangerous_deserialization=True)
    new_db.distance_strategy = DistanceStrategy.COSINE
    print(new_db.distance_strategy)

    print(env.LLM_MODEL_NAME)
    reranker = CohereRerank(model=env.RANKING_MODEL)

    retriever = new_db.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 10}
    )
    
    docs = retriever.invoke(user_question)

    logger.info(f"Document Hits: {len(docs)}")

    logger.info("------------------------------------------------")
    logger.info(f"User Name: ")
    logger.info("------------------------------------------------")


    docs_scores = new_db._similarity_search_with_relevance_scores(user_question, k=20)
    for doc, score in docs_scores:
        logger.info(f"File     : {doc.metadata['source']}")
        logger.info(f"Text     : {doc.page_content}")
        logger.info(f"Score    : {score}")
        logger.info("------------------------------------------------")

    reranked_docs = reranker.rerank(
        documents=docs, 
        query=user_question,
        top_n=5
    ) 

    logger.info(f"Reranked Documents: {len(reranked_docs)}")
    for doc in reranked_docs:
        idx = doc.get("index")
        logger.info(f"Text     : {docs[idx].page_content}")
        logger.info(f"Relevance: {doc.get('relevance_score')}")
        logger.info("------------------------------------------------")

    freq = Counter()
    sum_score = defaultdict(float)
    count_score = defaultdict(int)

    for doc in reranked_docs:
        idx = doc["index"]
        src = docs[idx].metadata["source"]
        freq[src] += 1
        sum_score[src] += doc["relevance_score"]
        count_score[src] += 1

    avg_score = {src: sum_score[src]/count_score[src] for src in freq}

    sources = [
        src for src in freq
        if freq[src] >= 2 or avg_score[src] >= 0.9
    ]

    context = [
        Document(
            page_content=docs[doc["index"]].page_content,
            metadata=docs[doc["index"]].metadata
        )
        for doc in reranked_docs
    ]

    chain = get_conversational_chain(retriever, channel_id)
    response = chain(
        {
            "question": user_question,
            "context": context
        },
        return_only_outputs=True
    )

    return {"query": user_input, "response": response["answer"]}, sources, len(sources)