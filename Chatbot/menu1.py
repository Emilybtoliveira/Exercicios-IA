import os
import time
from difflib import *
import sys
flagChangesInBase = False
objList = []

def changeInfix(model,change):
    
    phraseNew = model.replace("substitute",change)
    return f"{change} : {phraseNew}\n"

def editPhrasesFile():
    print("Na janela a seguir você poderá editar as frases!")
    time.sleep(1)

    os.system("gedit frases.txt")
    

def autoGeneratePhrases():
    phraseList = ['dor de cabeca','dor de barriga','fome']
    
    phrase = input("Digite uma frase de exemplo: ")
    objectivePhrase = input("Qual o objetivo da frase acima? ")

    model = phrase.replace(objectivePhrase,"substitute")

    phraseFile = open("frases.txt",'w')
    for newPhrase in phraseList:
        phraseFile.write(changeInfix(model,newPhrase))
        
    phraseFile.close()

    return
        

def createHelp():
    print("Na janela a seguir você poderá editar o help!")
    time.sleep(1)

    os.system("gedit help.txt")
    

def createObjVariables():
    objList = []
    inputObjList = ""
    while True:
        # TODO fazer o check de se tiver agum erro aqui, se nao tiver dentro de nenhuma frase, por ex
        inputObjList = input("Digite as variaveis objetivos. Quando tiver finalizado, digite 99!")
        if inputObjList=="99":
            break

        objList.append(inputObjList)
        
    return objList

def editBase():
    global flagChangesInBase, objList
    print("Na janela a seguir você poderá editar a base de regras!")
    time.sleep(1)

    originalFile = open("base.txt",'r').read()
    originalFileHash = originalFile.__hash__()
    os.system("gedit base.txt")

    afterFile = open("base.txt",'r').read()
    afterFileHash = afterFile.__hash__()

    if originalFileHash != afterFileHash:
        flagChangesInBase = True
        print("Ocorreram mudanças na base, logo é necessário redefinir os objetivos!")
        objList = createObjVariables()

def checkBeforeChatbot():
    # funcao para checar se ta tudo ok pro chatbot comecar
    # necessario: - base | - frases
    if os.path.getsize('base.txt') == 0:
        print("Necessário definir a base antes!")
        return False
    
    if os.path.getsize('frases.txt') == 0:
        print("Necessário definir as frases antes. Você pode gerar automaticamente pelo menu!")
        return False

    return True



def firstMenu():
    global objList
    # aqui eh onde ficara o fluxo com o loop e etc
    while True:
        print("Bem-vindo ao Amateur Sinta!\n")
        # checar se teve mudança?
        print("Escolha uma das opções abaixo digitando o número correspondente!\n")
        print("[1] Gerar Help para o Chatbot \n[2] Gerar Frases Automaticamente \n[3] Editar Frases \n[4] Editar Base \n[5] Chatbot\n[6] Gerar Variáveis Objetivos\n[99] Concluir\n")
        try:
            option = int(input("Digite a opção: "))
        except ValueError:
            print("Ops! Você deve que digitar um número!")
        else:
            # menu aqui
            if option == 1:
                createHelp()
            elif option == 2:
                autoGeneratePhrases()
            elif option == 3:
                editPhrasesFile()
            elif option == 4:
                editBase()
            elif option == 5:
                testChatbot = checkBeforeChatbot()
                if testChatbot:
                    pass # add chatbot here
            elif option==6:
                objList = createObjVariables()
            elif option == 99:
                print("Obrigado por utilizar o Amauteur Sinta!")
                break
            else:
                print("Infelizmente essa opção não existe! Tente novamente!\n")
    

# lista = modelPhrase()
# print(lista)
#print(changeInfix(lista))

firstMenu()


# TODO cadastrar base
"""
cadastrar e editar a base
checar para quando nao houver alteracao nao ter que refazer tudo
se houver alteracao, tem que refazer todos os proximos passos

tem que pedir os objetivos 
logo, se tiver mudança, tem que pedir
    - pedir apenas do que mudou? se ocneguir ver o que apenas mudou stonks 
    - pedir de tudo dnv?
"""
# TODO carcaça de frase
"""
precisa ver a forma de lidar com o `?`
porque, por exemplo, se tiver voce tem sentido dor?
nao da pra fazer split por espaco porque vai puxar o ? junto com dor
entao tem que ver um jeito de lidar
e nem sempre vai ter a posicao certa, mas eh algo que podemos validar
- tentar ver algo como regex eh uma opcao

ex

a condicao a seguir esta sendo sentida? dor
voce sente dor?
dores sao sentidas??? - acho que essa eh uma opcao extrema ne?

---

se for algo que nao vai rolar, posso adicionar um seguinte split em de cada um
para que sejam gerados eles separados dos demais
"""