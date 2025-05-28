from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_groq import ChatGroq

def get_conversational_chain(retriever):
    prompt_template = '''
    You are an intelligent assistant designed to answer user questions based solely on the provided context.

    Instructions:
        - Do not respond to any query with more then 600 words at max.
        - Only use information explicitly stated in the provided context to answer the question.
        - If the question cannot be answered based on the context, respond clearly and politely that the necessary information is not available in the document and redirect the user to the the link provided below - asking them to raise the ticket on the link below.
        - Use this redirect link in case no context is available - https://hrsupport.angelone.in/hc/en-us/requests/new?ticket_form_id=5893162753309
        - Do not assume, infer, or fabricate any information that is not directly present in the context.
        - Structure your response for clarity and readability, using bullet points, headings, or code blocks as needed.
        - Keep the answer short and concise, giving only the required information quickly
        - respond by following the format below:
            - for bold characters enclose them within single asterisks: *bold text*
            - for bullet points enclose them within a dash followed by a space: - bullet point
            - for italic characters enclose them within underscores: _italic_
            
    Chat History:
    {chat_history}

    Context:
    {context}

    Question:
    {question}

    Answer:
    '''

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["chat_history", "context", "question"]
    )

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    chain = ConversationalRetrievalChain.from_llm(
        llm=ChatGroq(temperature=0.3, model_name="llama-3.3-70b-versatile"),
        retriever=retriever,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": prompt},
        verbose=True
    )
    # model = models[model_name]["llm"]()
    # chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    return chain

def user_input(user_question, chat_history):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    index_name = f"faiss_index/llama-3"

    new_db = FAISS.load_local(index_name, embeddings, allow_dangerous_deserialization=True)
    retriever = new_db.as_retriever()

    # docs = new_db.similarity_search(user_question)
    chain = get_conversational_chain(retriever)

    # response = chain(
    #     {"input_documents": docs, "question": user_question},
    #     return_only_outputs=True
    # )

    for q, a in chat_history:
        chain.memory.chat_memory.add_user_message(q)
        chain.memory.chat_memory.add_ai_message(a)
    
    response = chain(
        {
            "question": user_question,
        },
        return_only_outputs=True
    )

    chat_history.append((user_question, response["answer"]))
    return chat_history
