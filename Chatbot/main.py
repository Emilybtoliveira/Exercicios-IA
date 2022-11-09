from dataclasses import dataclass
import string
from typing import List
import os
import numpy

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


# ============= FUNÇÕES DE RECONHECIMENTO DA LINGUAGEM E MANIPULAÇÃO DA BASE =========================
def generateDataStructure(base_sentences):
    current_state = "q0"

    current_sentence = Sentence([], [], 1)
    current_expression = Expression("", "")
    
    for index, word in enumerate(base_sentences):
        if word != "":        
            word = word.upper()
            print(word)
            
            if word in transition_table[current_state].keys(): #verifica se é [operador, se, então] e se existe transição
                current_state = transition_table[current_state][word]
                
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
            print(fact.certainty_factor)
            return (fact.certainty_factor,True) if fact.val == var_val_in_sentence else (1,False)

def getVarNegationValueInSentence(val:string):
    return "False" if val == "True" else "False"        

def evaluateASentence(sentence:Sentence): #Modus Ponens #PRECISA SER MOFIFICADO COM O FATOR DE CERTEZA
    fact_CF = sentence.certainty_factor

    for expression in sentence.expression_antec_list:
        cf, ok = getFactVarEvaluation(expression.var, expression.val)
        print(cf)
        if not ok:
            return False
        else:
            fact_CF *= cf #aplicação da regra de multiplação dos fatores de certeza de cada fato


    facts_list.append(FactExpression(sentence.expression_conseq_list[0].var, sentence.expression_conseq_list[0].val, fact_CF))
    print(sentence.expression_conseq_list[0].var, sentence.expression_conseq_list[0].val, fact_CF)
    #print(facts_list)
    return True
    
# ============= ENCADEAMENTO PRA TRÁS =========================
def backwardChaining(goal_var:string):
    print(goal_var)
    if isVariableAFact(goal_var):
        #print(f"{goal_var} é um fato")
        return True
    
    #print(f"{goal_var} não é um fato")

    var_conseq_sentences = getAllVariableConseqSentences(goal_var)
    var_conseq_sentences = [sentence for sentence in var_conseq_sentences if sentence not in visited_sentences] #evita repetição de caminhos
   
    if var_conseq_sentences != []:
        for sentence in var_conseq_sentences:
            visited_sentences.append(sentence)            
            
            sentence_exp_fact_count = len(sentence.expression_antec_list)
            #print(sentence)
            
            for expression in sentence.expression_antec_list:  
                search_result = backwardChaining(expression.var)
                
                if search_result == -1 or facts_list[-1].val != expression.val:
                    break #n da p alcançar por essa sentença
                else:
                    sentence_exp_fact_count -= 1
            
            if sentence_exp_fact_count == 0: #tenho todas variaveis da sentença nos fatos
                result = evaluateASentence(sentence) #chama função para avaliar sentença

                if not result:
                    pass
                elif isVariableAFact(aimed_var):
                    print(f"{aimed_var} é um fato")
                    print(getFactValue(aimed_var))
                    exit()
                else:                
                    return
    else:
        if goal_var != aimed_var and goal_var not in asked_vars:
            print(f"{goal_var} é inalcançável por esse caminho. Perguntando ao usuário...")
            if asksTheUser(goal_var):
                return True
        return -1

    return -1
    
# ============= ENCADEAMENTO PRA FRENTE =========================

def forwardChaining(goal_var:string):
    if isVariableAFact(goal_var):
        print(f"{goal_var} é um fato")
        print(getFactValue(goal_var))
        return True

    print(f"{goal_var} não é um fato")
    
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


# ============= FUNÇÕES GERAIS =========================
def asksTheUser(var_in_question:string):
    asked_vars.append(var_in_question)

    var_value = input(f"Você tem informação sobre a variável {var_in_question}? (True|False|N): ")
    var_value = var_value.upper()

    if var_value == "TRUE" or var_value == "FALSE":
        # print("true ou false")
        var_CF = float(input("Qual o fator de certeza? "))
        facts_list.append(FactExpression(var_in_question, var_value, var_CF))
        print(f"valores recebidos: {var_in_question, var_value, var_CF}")
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

def inferenceEngine():
    global aimed_var
    random_class_vars = numpy.random.choice(class_vars, len(class_vars), False)
    print(random_class_vars)

    for goal_var in random_class_vars: #CHAMA AS VARIAVEIS ALEATORIAMENTE, PRA GARANTIR DINAMICIDADE
        aimed_var = goal_var
        print(f"Tentando pra variável {aimed_var}...")

        if backwardChaining(goal_var) == True:
            print(goal_var)
            return
        else:
            if forwardChaining(goal_var):
                print(goal_var)
                return    
    print("Não consegui adivinhar o animal.")


if __name__ == '__main__':    
    base_sentences = loadBaseSentences()
    #print(base_sentences)
    splited = (base_sentences.replace("\n", " ")).split(" ")
    #print(splited)
    
    generateDataStructure(splited)
    #printBaseSentences()
    getClassVars()
    inferenceEngine()
    #os.system("xdg-open base.txt" or "start base.txt" )