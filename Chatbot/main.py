from dataclasses import dataclass
import random
import string
from typing import List
import os
import numpy
import datetime

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

uncertainty_flag = False
user_name = ""
current_conclusion_variable = ""
derivation_path = []

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
                    print("algo está errado no código inserido")
                    exit() #lança erro pq nao existe transição 
            
            elif "float" in transition_table[current_state].keys():
                try:
                    current_state = transition_table[current_state]["float"]
                    current_sentence.certainty_factor = float(word)
                    rules_list.append(current_sentence)
                    current_sentence = Sentence([], [], 1) 
                except ValueError:
                    print("Algum dos fatores de certeza que você inseriu não são números.")
                    exit()

            elif "var" in transition_table[current_state].keys():
                if (word.replace("_", "")).isalnum():
                    current_state = transition_table[current_state]["var"]
                    current_expression.var = word

                    if word not in var_list:
                        var_list.append(word)
            else:
                print("algo está errado no código inserido")
                exit() #erro, nao reconhece            
 
def loadBaseSentences(path="base.txt"):
    with open(path, "r") as source:
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
        print(getFactValue(goal_var))
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
                        print(f"{aimed_var} é um fato")
                        print(getFactValue(aimed_var))
                        return()
            
        if deductions > 0:
            loops_with_no_deductions = 0
        else:
            loops_with_no_deductions = 1

    print(f"Não consigo deduzir {goal_var}")
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

    while(True):
        print(f"[Chatbot]: {var_in_question}?\n\tResponda:\n\t1 - Sim \n\t2 - Não \n\t3 - Não tenho certeza\n\t4 - Por quê?")

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
            print(f"[Chatbot]: Sem problemas, {user_name}")
            return False
        elif user_aswr in ["4", "POR QUÊ?", "POR QUE?", "POR QUE"]:
           print(f"[Chatbot]: Estou te perguntando isso, porque quero descobrir {current_conclusion_variable}.")            
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
        print(f"[Chatbot]: Para concluir {sentence.expression_conseq_list[0].var} eu precisava que: ", end= "")
        
        for expression in sentence.expression_antec_list:
            print(f"{expression.var} fosse {expression.val}, ", end = "")
    
        print(random.choice(conclusion_sentences))
    
    print("[Chatbot]: Entendeu? ;)")

def showChatbotConclusionMenu():
    global uncertainty_flag
    
    if uncertainty_flag:
        print(f"[Chatbot]: {user_name}, consegui concluir {aimed_var} com {round(getAimedVarCF()*100,2)}% de certeza.\n\t1 - Como?\n\t2 - Continuar")
    else:
        print(f"[Chatbot]: {user_name}, consegui concluir {aimed_var}.\n\t1 - Como?\n\t2 - Continuar")

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

def chatbotFlowLoop(chatbot_intro = ""):
    global user_name
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

    input("PRESS ENTER TO CONTINUE.")

# ============= FUNÇÕES GERAIS =========================
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
        print(f"[Chatbot]: Tentando pra variável {aimed_var}...")

        if backwardChaining(goal_var) == True:
            return True
        else:
            if forwardChaining(goal_var):
                return True  
    
    return False

def getClassVars():
    for var in var_list:
        print(var)

    class_var = input("Dentre as variáveis identificadas na base de conhecimento listadas acima, quais são as variáveis objetivo? (Liste as variáveis separadas por quebra de linha).\n")
    
    while class_var != "":
        if (class_var.upper() in var_list)and (class_var.upper() not in class_vars):
            class_vars.append(class_var.upper())

            class_var = input()
        else:
            print("Essa variável não existe na base de conhecimento ou já foi adicionada por você. Digite novamente.")
            class_var = input()

    print(f"Variáveis objetivo: {class_vars}")

def mainLoop():
    while(True):
        try:
            showChatbotMainMenu()

            option = int(input("> "))

            if option == 1:
                chatbotFlowLoop("Sou um chatbot para diagnóstico médico.")
            elif option == 2:
                pass
            elif option == 3:
                return
            else:
                raise Exception
        except:
            print("> Isso não foi uma opção válida. Tente novamente.")
            input("PRESS ENTER TO CONTINUE.")

if __name__ == '__main__':    
    base_sentences = loadBaseSentences()
    #print(base_sentences)
    splited = (base_sentences.replace("\n", " ")).split(" ")
    #print(splited)
    
    generateDataStructure(splited)
    #printBaseSentences()
    getClassVars()
    #inferenceEngine()
    mainLoop()
    #os.system("xdg-open base.txt" or "start base.txt" )