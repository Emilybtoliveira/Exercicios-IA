from dataclasses import dataclass
import random
import string
from typing import List
import os
import numpy
import datetime
import time
from difflib import *


# ============= ESTRUTURAS DE RECONHECIMENTO DA LINGUAGEM =========================
var_list = []
val_list = ["TRUE", "FALSE"]
class_vars = []

transition_table = {"q0": {"SE": "q1"},
                    "q1": {"var": "q2"},
                    "q2":{"=": "q3"},
                    "q3": {"val": "q4"},
                    "q4":{"ENTAO": "q5", 
                           "&&": "q1"},
                    "q5":{"var": "q6"},
                    "q6":{"=": "q7"},
                    "q7": {"val": "q8"},
                    "q8": {"SE": "q1",
                            "FC": "q9"},
                    "q9":{"=": "q10"},
                    "q10":{"float": "q0"}}

# ============= ESTRUTURAS DE DADOS DA BASE DE CONHECIMENTO =========================
@dataclass
class Expression:
    var: string
    val: string
    

@dataclass
class Sentence:
    expression_antec_list: List[Expression]
    expression_conseq_list: List[Expression]
    certainty_factor: float

@dataclass
class FactExpression:
    var: string
    val: string
    certainty_factor: float

rules_list = []
facts_list = []
visited_sentences = []
asked_vars = []
aimed_var = "" #aqui vai a pergunta!


# ============= ESTRUTURAS DE DADOS DO CHATBOT =========================

derivation_path = []
phrases_per_var = {}

uncertainty_flag = False
user_name = ""
current_conclusion_variable = ""
chatbot_intro = ""

flagChangesInBase = False
selectedKB = ""
flagSelectedKB = False
flagSentencesRegistered = False

# ============= FUNÇÕES DE RECONHECIMENTO DA LINGUAGEM E MANIPULAÇÃO DA BASE =========================
def generateDataStructure(base_sentences):
    global uncertainty_flag

    current_state = "q0"

    current_sentence = Sentence([], [], 1)
    current_expression = Expression("", "")
    
    for index, word in enumerate(base_sentences):
        if word != "":        
            word = word.upper()
            #print(word)
            
            if word in transition_table[current_state].keys(): #verifica se é [operador, se, então] e se existe transição
                current_state = transition_table[current_state][word]
                if word == "FC":
                    uncertainty_flag = True
                if word == "ENTAO" or word == "&&":     
                    current_sentence.expression_antec_list.append(current_expression)       
                    current_expression = Expression("", "")
                     
            elif word in val_list:
                if "val" in transition_table[current_state].keys():
                    current_state = transition_table[current_state]["val"]
                    current_expression.val = word

                    if current_state == "q8": 
                        try:
                            if base_sentences[index+1].upper() == "SE":
                                current_sentence.expression_conseq_list.append(current_expression) 
                                rules_list.append(current_sentence)
                                current_sentence = Sentence([], [], 1) 
                            #se nao for, entao tem que continuar lendo      
                            else:
                                current_sentence.expression_conseq_list.append(current_expression)       
                        except IndexError:
                            current_sentence.expression_conseq_list.append(current_expression) 
                            rules_list.append(current_sentence)
                            current_sentence = Sentence([], [], 1)                    
                        finally:
                            current_expression = Expression("", "")                

                else:
                    print(f"Algo está errado no código inserido em volta de {word}")
                    return False #lança erro pq nao existe transição 
            
            elif "float" in transition_table[current_state].keys():
                try:
                    current_state = transition_table[current_state]["float"]
                    current_sentence.certainty_factor = float(word)
                    rules_list.append(current_sentence)
                    current_sentence = Sentence([], [], 1) 
                except ValueError:
                    print("Algum dos fatores de certeza que você inseriu não são números.")
                    return False

            elif "var" in transition_table[current_state].keys():
                if (word.replace("_", "")).isalnum():
                    current_state = transition_table[current_state]["var"]
                    current_expression.var = word

                    if word not in var_list:
                        var_list.append(word)
            else:
                print(f"Algo está errado no código inserido em volta de {word}")
                return False #erro, nao reconhece        

    return True   
 
def loadBaseSentences():
    with open("KB_Examples/" + selectedKB, "r") as source:
        return source.read()

def printBaseSentences():
    print("REGRAS:")
    for rule in rules_list:
        print(f"antecessor: ", rule.expression_antec_list)
        print(f"consequente: ", rule.expression_conseq_list)
        print(f"fator de certeza: ", rule.certainty_factor)

    print("VARIAVEIS:")
    for var in var_list:
        print(var)

def getSentenceAntecVariables(sentence:Sentence):
    sentence_variables = []

    for expression in sentence.expression_antec_list:
        sentence_variables.append(expression.var)
    
    return sentence_variables

def getSentenceConseqVariables(sentence:Sentence):
    sentence_variables = []

    for expression in sentence.expression_conseq_list:
        sentence_variables.append(expression.var)
    
    return sentence_variables

def getAllVariableAntecSentences(var:string):
    var_sentences = []

    for sentence in rules_list:
        for expression in sentence.expression_antec_list:
            if expression.var == var:
                var_sentences.append(sentence)

    return var_sentences

def getAllVariableConseqSentences(var:string):
    var_sentences = []

    for sentence in rules_list:
        for expression in sentence.expression_conseq_list:
            if expression.var == var:
                var_sentences.append(sentence)

    return var_sentences

def isVariableAFact(var:string):
    for fact in facts_list:
        if fact.var == var:
            return True
    
    return False

def getFactValue(var:string):
    for fact in facts_list:
        if fact.var == var:
            return fact

def getFactVarEvaluation(var:string, var_val_in_sentence:string): #determina se o valor de um fato corresponde ao que se espera na sentença
    for fact in facts_list:
        if fact.var == var:
            #print(fact.certainty_factor)
            return (fact.certainty_factor,True) if fact.val == var_val_in_sentence else (1,False)

def getVarNegationValueInSentence(val:string):
    return "False" if val == "True" else "False"        

def evaluateASentence(sentence:Sentence): #Modus Ponens #PRECISA SER MOFIFICADO COM O FATOR DE CERTEZA
    global derivation_path

    fact_CF = sentence.certainty_factor

    for expression in sentence.expression_antec_list:
        cf, ok = getFactVarEvaluation(expression.var, expression.val)
        if not ok:
            return False
        else:
            fact_CF *= cf #aplicação da regra de multiplação dos fatores de certeza de cada fato


    facts_list.append(FactExpression(sentence.expression_conseq_list[0].var, sentence.expression_conseq_list[0].val, fact_CF))
    derivation_path.append(sentence)
    #print(sentence.expression_conseq_list[0].var, sentence.expression_conseq_list[0].val, fact_CF)
    #print(facts_list)
    return True

def getAimedVarCF():
    for fact in facts_list:
        if fact.var == aimed_var:
            return fact.certainty_factor

# ============= ENCADEAMENTO PRA TRÁS =========================
def backwardChaining(goal_var:string):
    global current_conclusion_variable

    if isVariableAFact(goal_var):
        return True

    var_conseq_sentences = getAllVariableConseqSentences(goal_var)
    var_conseq_sentences = [sentence for sentence in var_conseq_sentences if sentence not in visited_sentences] #evita repetição de caminhos
   
    if var_conseq_sentences != []:
        for sentence in var_conseq_sentences:
            visited_sentences.append(sentence)
            current_conclusion_variable = sentence.expression_conseq_list[0].var          
            
            sentence_exp_fact_count = len(sentence.expression_antec_list)
            #print(sentence)
            
            for expression in sentence.expression_antec_list:  
                search_result = backwardChaining(expression.var)
                current_conclusion_variable = sentence.expression_conseq_list[0].var          
                
                if search_result == -1 or facts_list[-1].val != expression.val:
                    break #n da p alcançar por essa sentença
                else:
                    sentence_exp_fact_count -= 1
            
            if sentence_exp_fact_count == 0: #tenho todas variaveis da sentença nos fatos
                result = evaluateASentence(sentence) #chama função para avaliar sentença

                if not result:
                    pass
                elif isVariableAFact(aimed_var):
                    return True
                else:                
                    return
    else:
        if goal_var != aimed_var and goal_var not in asked_vars:
            #print(f"{goal_var} é inalcançável por esse caminho. Perguntando ao usuário...")
            if asksTheUser(goal_var):
                return True
        return -1

    return -1
    
# ============= ENCADEAMENTO PRA FRENTE =========================

def forwardChaining(goal_var:string):
    if isVariableAFact(goal_var):
        #print(f"{goal_var} é um fato")
        #print(getFactValue(goal_var))
        return True

   # print(f"{goal_var} não é um fato")
    
    loops_with_no_deductions = 0
    deductions = 0
    
    while loops_with_no_deductions != 1:
        deductions = 0
        var_conseq_sentences = [sentence for sentence in rules_list if sentence not in visited_sentences] #evita repetição de caminhos
        
        for sentence in var_conseq_sentences:
            sentence_exp_fact_count = len(sentence.expression_antec_list)
            #print(sentence)
                
            for expression in sentence.expression_antec_list:  
                if isVariableAFact(expression.var):
                    sentence_exp_fact_count -= 1
                else:  
                    break
            
            if sentence_exp_fact_count == 0:
                if evaluateASentence(sentence):  
                    visited_sentences.append(sentence)   
                    deductions +=1

                    if isVariableAFact(aimed_var):
                        """ print(f"{aimed_var} é um fato")
                        print(getFactValue(aimed_var)) """
                        return()
            
        if deductions > 0:
            loops_with_no_deductions = 0
        else:
            loops_with_no_deductions = 1

    #print(f"Não consigo deduzir {goal_var}")
    return False

# ============= FUNÇÕES CHATBOT =========================

def validateUserFC(user_entry):
    try:
        number = int(user_entry)

        return number if number >= 0 and number <= 10 else False
    except:
        return False

def asksTheUser(var_in_question:string):
    global user_name, uncertainty_flag, current_conclusion_variable

    asked_vars.append(var_in_question)

    try:
        var_in_question_phrase = phrases_per_var[var_in_question]
    except:
        var_in_question_phrase = "Você tem alguma informação sobre " + {var_in_question} + "?"

    while(True):
        print(f"[Chatbot]: {var_in_question_phrase}\n\tResponda:\n\t1 - Sim \n\t2 - Não \n\t3 - Não tenho certeza\n\t4 - Por quê?")

        user_aswr = input(f"[Você]: ")
        user_aswr = user_aswr.upper()

        if user_aswr in ["1", "2", "SIM", "NÃO", "NAO"]:
            var_value = "TRUE" if user_aswr in ["1", "SIM"] else "FALSE"
            
            if uncertainty_flag:
                print("[Chatbot]: Em uma escala de 1 a 10, quanta certeza você tem nessa afirmação?")
                user_aswr = input("[Você]: ")

                var_CF = validateUserFC(user_aswr)

                if not var_CF:
                    print("[Chatbot]: Isso não foi um número de 1 a 10. Vamos tentar de novo.")
                else:
                    var_CF = var_CF / 10
                
                    facts_list.append(FactExpression(var_in_question, var_value, var_CF))
                    #print(f"[Chatbot]: valores recebidos: {var_in_question, var_value, var_CF}")
                    return True
            else:
                facts_list.append(FactExpression(var_in_question, var_value, 1))
               # print(f"[Chatbot]: Valores recebidos: {var_in_question, var_value, 1}")
                return True

        elif user_aswr in ["3", "NÃO TENHO CERTEZA", "NAO TENHO CERTEZA"]:
            print(f"[Chatbot]: Sem problemas, {user_name}.")
            return False
        elif user_aswr in ["4", "POR QUÊ?", "POR QUE?", "POR QUE"]:
            try:
                current_conclusion_variable_phrase = (phrases_per_var[current_conclusion_variable].replace('?', '')).lower()
            except:
                current_conclusion_variable_phrase = "posso concluir " + current_conclusion_variable

            print(f"[Chatbot]: Estou te perguntando isso, porque quero descobrir se {current_conclusion_variable_phrase}.")            
        else: 
            print(f"[Chatbot]: Não entendi tua resposta, {user_name}")

def determineGreeting():
    cur_hour = datetime.datetime.now().hour

    if cur_hour < 12:
        return "Bom dia"
    elif cur_hour < 18:
        return "Boa tarde"
    else:
        return "Boa noite"

def getUserName():
    global user_name

    print("[Chatbot]: Qual seu nome?")
    user_name = input("[Você]: ")

def getUserFeedback():
    while(True):
        print("[Chatbot]: Em uma escala de 0 a 10, quão preciso você acha que é esse resultado?")
        user_feedback = input("[Você]: ")
        
        user_feedback = validateUserFC(user_feedback)

        if not user_feedback:
            print("[Chatbot]: Isso não foi um número de 1 a 10. Vamos tentar de novo.")
        else:
            print(f"[Chatbot]: Interessante, {user_name}. Seu feedback é importante para melhorar meus resultados!\n[Chatbot]: Muito obrigado.")
            return

def showChatbotMainMenu():
    os.system("clear")

    print("======= CHATBOT MENU ======= ")
    print("1 - Iniciar o chatbot\n2 - Voltar para o menu de configurações\n3 - Sair da aplicação")

def showDerivationProcess():
    global derivation_path
    conclusion_sentences = ["que foram as respostas que você me deu.", "que foi exatamente o que você me disse.", "que foi o que você respondeu."]
    for sentence in reversed(derivation_path):
        var = ((sentence.expression_conseq_list[0].var).replace('_', ' ')).lower()
        print(f"[Chatbot]: Para concluir {var} eu precisava que: ", end= "")
        
        for expression in sentence.expression_antec_list:
            condition = "verdade" if expression.val == "TRUE" else "falso"
            print(f"{(expression.var.replace('_', ' ')).lower()} fosse {condition}, ", end = "")
    
        print(random.choice(conclusion_sentences))
    
    print("[Chatbot]: Entendeu? ;)")

def showChatbotConclusionMenu():
    global uncertainty_flag

    var = (aimed_var.replace("_", " ")).capitalize()
    
    if uncertainty_flag:
        print(f"[Chatbot]: {user_name}, consegui concluir {var} com {round(getAimedVarCF()*100,2)}% de certeza.\n\t1 - Como?\n\t2 - Continuar")
    else:
        print(f"[Chatbot]: {user_name}, consegui concluir {var}.\n\t1 - Como?\n\t2 - Continuar")

    while(True):
        try:
            user_answr = int(input("[Você]: "))

            if user_answr == 1:
                showDerivationProcess()
                return
            elif user_answr == 2:
                return
            else:
                raise Exception
        except:
            print("[Chatbot]: Isso não é uma opção válida. Tenta novamente.")

def chatbotFlowLoop():
    global user_name, chatbot_intro
    os.system("clear")

    print(f"[Chatbot]: {determineGreeting()}!")
    print(f"[Chatbot]: {chatbot_intro}") if chatbot_intro != "" else print(end="")
    getUserName()

    print(f"[Chatbot]: Vamos começar, {user_name}?")
    
    if inferenceEngine(): 
        showChatbotConclusionMenu()
        getUserFeedback()
    else:
        print(f"[Chatbot]: {user_name}, infelizmente não consegui chegar a uma conclusão.\n[Chatbot]: Estou sempre evoluindo e espero, em breve, conseguir te dar um resultado!")

    pressEnterToContinue()

def mainChatbotLoop():
    while(True):
        try:
            showChatbotMainMenu()

            option = int(input("> "))

            if option == 1:
                chatbotFlowLoop()
            elif option == 2:
                return True
            elif option == 3:
                return False
            else:
                raise Exception
        except:
            print("> Isso não foi uma opção válida. Tente novamente.")
            pressEnterToContinue()

#============== FUNÇÕES DO MENU DE CONFIGURAÇÕES ======================
def changeInfix(model,change): 
    change_clean = change.replace("_", " ") 
    change_clean = change_clean.lower()

    phraseNew = model.replace("substitute",change_clean)
    return f"{change}:{phraseNew}\n"

def generatePhrasesDataStructure():
    phrases_per_var.clear()

    with open("config_files/phrases.txt", "r") as file:
        phrases =  file.read()
    
    phrases = (phrases.replace('\n', ':')).split(':')
    print(phrases)

    index = 0

    while index < len(phrases):
        if not phrases[index] == "":
            var = phrases[index].replace(" ", "")
            
            if var in var_list: #se nao for, dá erro
                phrases_per_var[var] =  phrases[index+1]

                index += 2
            else:
                print(f"Há algo errado com o arquivo de frases. Sugiro que verifique o arquivo utilizando a opção 3 do menu.\nLembre-se que o formato do arquivo deve ser variável:frase.")
                pressEnterToContinue()
                phrases_per_var.clear()

                return
        else:
            index += 1

    """ print(phrases_per_var)
    pressEnterToContinue() """

def editPhrasesFile():
    print("\nVocê poderá editar as frases do chatbot na janela a seguir.\nAo finalizar, salve e feche-a para continuar no fluxo da aplicação.\nMantenha o padrão de formatação do arquivo => variável:frase.")
    time.sleep(4)

    os.system("nano config_files/phrases.txt")
    generatePhrasesDataStructure()

def autoGeneratePhrases():    
    phrase = input("\nDigite uma frase de exemplo (escreva a variável exatamente igual como está na base de conhecimento).\n> ")
    objectivePhrase = input("Qual a variável objetivo da frase?\n> ")

    model = phrase.replace(objectivePhrase,"substitute")
    #time.sleep(10)

    phraseFile = open("config_files/phrases.txt",'w')
    for var in var_list:
        phraseFile.write(changeInfix(model, var))
        
    phraseFile.close()
    generatePhrasesDataStructure()
        
def loadChatbotIntroduction():
    global chatbot_intro

    with open("config_files/chatbot_intro.txt", "r") as file:
        chatbot_intro =  file.read()
        #print(chatbot_intro)        

def createChatbotIntroduction():
    print("\nVocê poderá editar/criar uma introdução para o chatbot na janela a seguir.\nAo finalizar, salve e feche-a para continuar no fluxo da aplicação.")
    time.sleep(4)
    os.system("nano config_files/chatbot_intro.txt")
    
    loadChatbotIntroduction()
    pressEnterToContinue()
 
def getClassVars():    
    global class_vars, flagSentencesRegistered

    var_list_string = ""
    for var in var_list:
        var_list_string += (var + "\n")

    with open("config_files/KB_variables.txt", "w") as file:
        file.write(var_list_string)

    print(f"Você poderá editar as variáveis-objetivo na janela a seguir. Deixe no arquivo apenas as variáveis da base de conhecimento que são de classificação.\nAo finalizar, salve e feche-a para continuar no fluxo da aplicação.")
    
    time.sleep(4)
    os.system("nano config_files/KB_variables.txt")
    
    with open("config_files/KB_variables.txt", "r") as file:
        var_list_string = file.read()
    

    class_vars = var_list_string.split("\n")
    #pressEnterToContinue()

def editBase():
    global flagChangesInBase, selectedKB
    print(f"\nVocê poderá editar a base de conhecimento {selectedKB} na janela a seguir.\nAo finalizar, salve e feche-a para continuar no fluxo da aplicação.")
    #time.sleep(1)

    originalFile = open("KB_Examples/" + selectedKB,'r').read()
    originalFileHash = originalFile.__hash__()
    
    time.sleep(4)
    os.system("nano KB_Examples/"+ selectedKB)
    
    afterFile = open("KB_Examples/" + selectedKB,'r').read()
    afterFileHash = afterFile.__hash__()

    base_sentences = loadBaseSentences()
    #print(base_sentences)
    splited = (base_sentences.replace("\n", " ")).split(" ")
    #print(splited)    
    #printBaseSentences()
    if not generateDataStructure(splited):
       return errorMenu()   

    if originalFileHash != afterFileHash and flagSelectedKB:
        flagChangesInBase = True
        print("\nOcorreram mudanças na base, logo é necessário redefinir as variáveis objetivo.")
        pressEnterToContinue()
        getClassVars()

def checkBeforeChatbot():
    # funcao para checar se ta tudo ok pro chatbot comecar
    # necessario: - base | - frases
    if os.path.getsize('KB_Examples/'+ selectedKB) == 0:
        print("Necessário definir a base antes!")
        return False
    
    if os.path.getsize('config_files/phrases.txt') == 0:
        print("Necessário definir as frases antes. Você pode gerar automaticamente pelo menu!")
        return False

    if os.path.getsize('config_files/KB_variables.txt') == 0:
        print("Necessário definir as variáveis objetivo antes.")
        return False
    
    if len(phrases_per_var) == 0:
        print("Necessário definir as frases antes. Você pode utilizar as opções 2 e 3 do menu.")
        return False

    return True

def selectAKB():
    global selectedKB

    while True:
        print("\nIdentifiquei as seguintes opções de bases de conhecimento: ")
        for _, _, file in os.walk('KB_Examples/'):
            existing_KBs = file
        
        for i,file in enumerate(existing_KBs):
            print(f"\t[{i+1}] {file}")

        try:
            clearFiles()
            selection = int(input(f"Digite a base de conhecimento desejada ou digite {i+2} para criar uma nova base.\n> "))

            if selection >= 1 and selection <= i+1:
                selectedKB = existing_KBs[selection-1]
                return
            elif selection == i+2:
                new_KB = input("Digite o nome da base a ser criada (sem o .txt).\n> ")
                selectedKB = new_KB + ".txt"
                open("KB_Examples/" + selectedKB, "w")
                return
            else:
                print("Opção inválida.")
        except:
            print("Isso não foi um número válido.")

def errorMenu():
    print("\t[1] Editar novamente\n\t[2] Concluir\n")

    try:
        option = int(input("> "))
    except ValueError:
        print("Ops! Você deve que digitar um número!")
        pressEnterToContinue()
    else:
        if option == 1:
            return editBase()
        elif option == 2:
            print("Obrigado por utilizar o Amauteur Sinta!")
            exit()
        else:
            print("Infelizmente essa opção não existe! Tente novamente!\n")

#esse menu só aparece qnd nao existe KB selecionada            
def noSelectedKBMenu():
    global flagSelectedKB

    print("[1] Selecionar uma base de conhecimento\n[2] Concluir\n")

    try:
        option = int(input("> "))
    except ValueError:
        print("Ops! Você deve que digitar um número!")
        pressEnterToContinue()

    else:
        if option == 1:
            selectAKB()
            editBase()
            getClassVars()
            flagSelectedKB = True
        elif option == 2:
            print("Obrigado por utilizar o Amauteur Sinta!")
            exit()
        else:
            print("Infelizmente essa opção não existe! Tente novamente!\n")
            pressEnterToContinue()

#esse menu só aparece qnd existe KB selecionada            
def fullMenu():
    global flagSelectedKB
    
    print("[1] Gerar uma introdução para o Chatbot \n[2] Definir frases-base para o Chatbot \n[3] Editar frases-base \n[4] Selecionar uma base de conhecimento\n[5] Editar Base de Conhecimento \n[6] Editar Variáveis Objetivo\n[7] Iniciar Chatbot\n[8] Concluir\n")
    
    try:
        option = int(input("> "))
    except ValueError:
        print("Ops! Você deve que digitar um número!")
        pressEnterToContinue()

    else:
        # menu aqui
        if option == 1:
            createChatbotIntroduction()
        elif option == 2:
            autoGeneratePhrases()
        elif option == 3:
            editPhrasesFile()
        elif option == 4:
            flagSelectedKB = False
            selectAKB()
            editBase()
            getClassVars()
            flagSelectedKB = True
        elif option == 5:
            editBase()
        elif option == 6:
            getClassVars()                
        elif option == 7:
            testChatbot = checkBeforeChatbot()
            if testChatbot:
                if not mainChatbotLoop():
                    print("Obrigado por utilizar o Amauteur Sinta!")                    
                    exit()
        elif option == 8:
            print("Obrigado por utilizar o Amauteur Sinta!")
            exit()
        else:
            print("Infelizmente essa opção não existe! Tente novamente!\n")
            pressEnterToContinue()

def KBbutNoPhrasesMenu():
    global flagSentencesRegistered, flagSelectedKB
    print("[1] Gerar uma introdução para o Chatbot \n[2] Definir frases-base para o Chatbot \n[3] Selecionar uma base de conhecimento\n[4] Editar Base de Conhecimento \n[5] Editar Variáveis Objetivo\n[6] Concluir\n")

    try:
        option = int(input("> "))
    except ValueError:
        print("Ops! Você deve que digitar um número!")
        pressEnterToContinue()
    else:
        if option == 1:
            createChatbotIntroduction()
        elif option == 2:
            autoGeneratePhrases()
            flagSentencesRegistered = True
        elif option == 3:
            flagSelectedKB = False
            selectAKB()
            editBase()
            getClassVars()
            flagSelectedKB = True
        elif option == 4:
            editBase()
        elif option == 5:
            getClassVars()
        elif option == 6:
            print("Obrigado por utilizar o Amauteur Sinta!")
            exit()
        else:
            print("Infelizmente essa opção não existe! Tente novamente!\n")
            pressEnterToContinue()

def mainConfigLoop():
    while True:
        os.system("clear")

        print("Bem-vindo ao Amateur Sinta!\n")
        # checar se teve mudança?
        print("Escolha uma das opções abaixo digitando o número correspondente!\n")
        
        if flagSelectedKB and flagSentencesRegistered:
            fullMenu()
        elif flagSelectedKB:
            KBbutNoPhrasesMenu()
        else:
            noSelectedKBMenu()

# ============= FUNÇÕES GERAIS =========================
def pressEnterToContinue():
    input("DIGITE ENTER PARA CONTINUAR.")
    os.system("clear")

def clearFiles():
    with open("config_files/phrases.txt", "w") as phrases:
        phrases.write('')
    with open("config_files/KB_variables.txt", "w") as kb_variables:
        kb_variables.write('')
    with open("config_files/chatbot_intro.txt", "w") as intro:
        intro.write('')


def clearDataStructures():
    global facts_list, visited_sentences, asked_vars
    
    facts_list.clear()
    visited_sentences.clear()
    asked_vars.clear()
    derivation_path.clear()

def inferenceEngine():
    global aimed_var, derivation_path
    clearDataStructures()

    random_class_vars = numpy.random.choice(class_vars, len(class_vars), False)
    #print(random_class_vars)

    for goal_var in random_class_vars: #CHAMA AS VARIAVEIS ALEATORIAMENTE, PRA GARANTIR DINAMICIDADE
        aimed_var = goal_var
        derivation_path.clear()
        #print(f"[Chatbot]: Tentando pra variável {aimed_var}...")

        if backwardChaining(goal_var) == True:
            return True
        else:
            if forwardChaining(goal_var):
                return True  
    
    return False

def main():
    mainConfigLoop()

if __name__ == '__main__':    
    main()