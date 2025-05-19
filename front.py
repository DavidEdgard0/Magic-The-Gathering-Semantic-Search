import gradio as gr 
import requests
import time
import uuid
import os
import random

BASE_URL="http://127.0.0.1:8000"

#Usuario auxiliar
SESSION_ID=str(uuid.uuid4())

CORPUS_TEXT=''

def add_text(history,text):
    """
    Agrega texto a la historia del chat y actualiza la 
    interfaz
    """
    #history_aux=[]
    #history_aux.append(history)
    print("history: ", history, "es de tipo", type(history))
    print("text: ", [(text,None)], "es de tipo", type([(text,None)]))

    history=history + [(text,None)]
    print("Historia actualizada: ", history)
    return history, gr.update(value="",interactive=False)

def add_file(history,file):

    history=history+[((file.name),None)]
    print("history: ", history)
    return history

def greet(name):
    return name 

def bot (history):
    print("Entré al bot!!!")
    url=f"{BASE_URL}/bot/init"
    input_text=history#[-1][0]
    #print("Este es el input del bot: ", input_text, "y es de tipo: ", type(input_text))
    
    payload={"session_id":SESSION_ID,"messages":input_text}
    #print("Esto es el payload: ", payload)
    
    response_api=requests.post(url,params=payload)

    #print("Esta es la response_api: ",response_api)
    print("Este es el valor de response:", response_api.json()['messages'])

    response=response_api.json()['messages']
    print("#######################################################")
    #print("#######################################################")
    #print("Este es el valor de response:", response)
    for item in response:
        print("##")
        print(item)
        print("##")

    if len(response)==1:
        response_m=response[-1]
    else:
        response_m=response[-2]

    #print("Esto vale  response_m=response['messages'][-2]: ",response_m)

    if "Cards" in response_m:
        print("Entré a Cards")
        response_m=response_m['Cards']
        print("Este es el valor de response['messages'][-1]['Cards']", response_m)
    else: 
        print("Entré a content")
        response_m=response_m['content']
        print("Este es el valor de response['messages'][-1]['content']", response_m)

    try:
        print("Hola estamos aquí: ",response_m)
        print("soy de tipo: ", type(response_m))

    except ValueError:
        print("Error: La respuesta no es un Json válido")

    #Define entradas de texto vacio
    #history[-1][1]=""
    #history=""
    # Genera el efecto de escribir lento con pausa
    #for character in response_m:
    #    history+= character
    #    print(history)
    #    time.sleep(0.05)
    #    yield history
    return response_m

# Crea la aplicación de gradio
#with gr.Blocks() as demo:
#    gr.Markdown("# MTG CARD RECOMMENDER")
#    gr.Markdown("# Your BEST ALLY IN  SEARCH CARDS FOR YOUR STRATEGY")


with gr.Blocks() as demo:
    chatbot = gr.Chatbot(type="messages")
    msg = gr.Textbox()
    clear = gr.ClearButton([msg, chatbot])

    def respond(message, chat_history):
        #bot_message = random.choice(["How are you?", "Today is a great day", "I'm very hungry"])
        #########################################################################################
        print("Entré al bot!!!")
        url=f"{BASE_URL}/bot/init"
        input_text=message#[-1][0]
    #print("Este es el input del bot: ", input_text, "y es de tipo: ", type(input_text))
    
        payload={"session_id":SESSION_ID,"messages":input_text}
    #print("Esto es el payload: ", payload)
    
        response_api=requests.post(url,params=payload)

    #print("Esta es la response_api: ",response_api)
        print("Este es el valor de response:", response_api.json()['messages'])

        response=response_api.json()['messages']
        print("#######################################################")
    #print("#######################################################")
    #print("Este es el valor de response:", response)
        for item in response:
            print("##")
            print(item)
            print("##")

        if len(response)==1:
            response_m=response[-1]
        else:
            response_m=response[-2]

    #print("Esto vale  response_m=response['messages'][-2]: ",response_m)

        if "Cards" in response_m:
            print("Entré a Cards")
            response_m=response_m['Cards']
            print("Este es el valor de response['messages'][-1]['Cards']", response_m)
        else: 
            print("Entré a content")
            response_m=response_m['content']
            print("Este es el valor de response['messages'][-1]['content']", response_m)

        try:
            print("Hola estamos aquí: ",response_m)
            print("soy de tipo: ", type(response_m))

        except ValueError:
            print("Error: La respuesta no es un Json válido")

        #########################################################################################
        
        chat_history.append({"role": "user", "content": message})
        chat_history.append({"role": "assistant", "content": response_m})
        time.sleep(2)
        return "", chat_history

    msg.submit(respond, [msg, chatbot], [msg, chatbot])


demo.queue()
if __name__ == "__main__":
    demo.launch()

