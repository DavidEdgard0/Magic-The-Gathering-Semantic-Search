import re
import json
from langchain_core.documents import Document
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS
import uuid 
import numpy as np
from numpy.linalg import norm
import ollama
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import ChatOllama
from typing import Sequence, Dict, Literal
from typing_extensions import Annotated, TypedDict
#from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import BaseMessage
from langgraph.graph import START, END, StateGraph, MessagesState
from langgraph.graph.message import add_messages
from langchain.schema import HumanMessage, AIMessage
from IPython.display import Image, display
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from langchain_ollama import ChatOllama, OllamaEmbeddings
from fastapi import FastAPI, UploadFile, Form, File
import os
import requests
import httpx

from langchain_community.vectorstores import FAISS

#Inicializar FastAPI:
app=FastAPI(debug=True)

def card_api(query):
    embeddings = OllamaEmbeddings(
    model="llama3.2",
    )
    db=FAISS.load_local("v_database/",embeddings,allow_dangerous_deserialization=True)
    docs = db.similarity_search(query,k=5)    
    return docs


llm_Ollama = ChatOllama(
    model = "llama3.2",
    temperature = 0.9,
    num_predict = 500
)
llm_Ollama.invoke('mi camisa es azul').content

embeddings = OllamaEmbeddings(
    model="llama3.2",
)

from langchain_community.vectorstores import FAISS
db=FAISS.load_local("C:/Users/card1/Documents/Cursos/Agentes/Proyecto final/v_database/",embeddings,allow_dangerous_deserialization=True)

# Estado del Grafo
class State(TypedDict):
    session_id: str
    messages: Annotated[list, add_messages]
    Cards: Dict[str,str]

#Paso 1
def solicitar_documentos(state: State):
    print(f"DEBUG - Documentos actuales en el estado: {state["Cards"]}")
    if "Exit" not in state["Cards"]:
        ai_msg = f"What kind of card would you want to see?"
    else:
        ai_msg=f"Here you have a description:."
        
    response = [AIMessage(ai_msg)]
    return {"messages":response}

#Paso 2
def conditional(state:State)->Literal["recibir_documentos","procesar_documentos"]:
    
    if "Exit" not in state["Cards"]:
        return "recibir_documentos"
    else:
        return "procesar_documentos"

#Paso 3    
def recibir_documentos (state:State):
    Card_dict=state['Cards']
    human_msg=interrupt("Card description: ")
    #response=[HumanMessage(human_msg)]
    #print("Mensaje humano: ",human_msg, "El tipo de input ingresado es: ",type(human_msg))
    response = [HumanMessage(human_msg)]
    print(f"DEBUG - Documentos actuales en el estado: {state['Cards']}, el usuario dio: {human_msg}, {type(human_msg)}")
    if human_msg != "Exit":
         card_suggestion=card_api(human_msg)
         #i=0
         for suggestion in card_suggestion: 
            #state['Cards'].update({suggestion.id:suggestion.page_content})
            Card_dict.update({suggestion.id:suggestion.page_content})
            #state['Cards'].update({i,suggestion.page_content})
            #i=i+1
         
         print(f"DEBUG - Con la información dada, el estado se actualizó a: {state['Cards']}")    
         
         ai_msg=''' 
            Option 1: \"\"{card_1}\"\"
            Option 2: \"\"{card_2}\"\"
            Option 3: \"\"{card_3}\"\"
            Option 4: \"\"{card_4}\"\"
            Option 5: \"\"{card_5}\"\"
           '''
         ai_msg=ai_msg.format(card_1=card_suggestion[0].page_content,card_2=card_suggestion[1].page_content,card_3=card_suggestion[2].page_content,card_4=card_suggestion[3].page_content,card_5=card_suggestion[4].page_content)
         response=[AIMessage(ai_msg)]

    else:
        response=human_msg
        #state['Cards'].update({"Exit":"Exit"})
        Card_dict.update({"Exit":"Exit"})
    
    return {"messages":response, "Cards": Card_dict}

#Paso 4
def procesar_documentos(state: State):
    summary_list=[]
    for key, value in state['Cards'].items():
        print(f"{key}: {value}")
        summary_list.append(value)
    
    print('los elementos de la lista son:', summary_list)
    
    context_paragraph = " ".join(summary_list)
    print(context_paragraph)

    summary=llm_Ollama.invoke('Create a Summary about the description of the following Magic The Gathering cards:' + context_paragraph).content
    print(summary)

    #ai_msg="Contengo esta información: " 
    ai_msg=summary
    response=[AIMessage(ai_msg)]
    return {"messages":response}

#Paso auxiliar
def Exit_aux(state: State):
    
    ai_msg="See you!"
        
    response = [AIMessage(ai_msg)]
    return {"messages":response}

#Paso 5
graph=StateGraph(State)

#Agregar nodos
graph.add_node("solicitar_documentos", solicitar_documentos)
graph.add_node("recibir_documentos", recibir_documentos)
graph.add_node("procesar_documentos",procesar_documentos)
graph.add_node("Exit_aux",Exit_aux)

#Definir flujo de conexión
graph.add_edge(START,"solicitar_documentos")
graph.add_conditional_edges("solicitar_documentos",conditional)
graph.add_edge("recibir_documentos","solicitar_documentos")
graph.add_edge("procesar_documentos","Exit_aux")
graph.add_edge("Exit_aux",END)

memory=MemorySaver()

app_graph=graph.compile(checkpointer=memory)

#View
#display(Image(app_graph.get_graph().draw_mermaid_png()))

@app.post("/bot/init/")
async def iniciar_proceso(session_id:str=None,messages:str=None):
    if session_id is None:
        print("Esto vale session_id: ",session_id)
        session_id=str(uuid.uuid1())
        inicio=0

    thread_config={"configurable":{"thread_id":session_id}}

    try:
        aux_state=app_graph.get_state(thread_config).metadata['step']
    except:
        aux_state=0

    if aux_state==0:
        state=State(session_id=session_id,Cards={},messages=[])
        response=app_graph.invoke(state,config=thread_config)
        print("Este es el estado 1 del grafo: ",app_graph.get_state(thread_config).metadata["step"])
    else:
        msge_list=messages
        human_command=Command(resume=msge_list)
        print("Este es el input del humano: ",human_command, "el mensaje es de tipo: ", type(msge_list))

        response=app_graph.invoke(human_command,config=thread_config)

    return response
    
    if __name__ == "__main__":
        import uvicorn

    uvicorn.run(app,host="0.0.0.0",port=8000)    