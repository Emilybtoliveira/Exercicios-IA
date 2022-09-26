from dataclasses import dataclass
import string
from typing import List

# ============= ESTRUTURAS DE RECONHECIMENTO DA LINGUAGEM =========================
var_list = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V",  "W", "X","Y", "Z"]
val_list = ["TRUE", "FALSE"]

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
                            "var": "q9"},
                    "q9":{"=": "q10"},
                    "q10":{"val": "q8"}}

# ============= ESTRUTURAS DE DADOS DA BASE DE CONHECIMENTO =========================
@dataclass
class Expression:
    var: string
    val: string
    

@dataclass
class Sentence:
    expression_antec_list: List[Expression]
    expression_conseq_list: List[Expression]

rules_list = []
facts_list = []
visited_sentences = []
asked_vars = []
aimed_var = "" #aqui vai a pergunta!


# ============= FUNÇÕES DE RECONHECIMENTO DA LINGUAGEM E MANIPULAÇÃO DA BASE =========================
def generateDataStructure(base_sentences):
    current_state = "q0"

    current_sentence = Sentence([], [])
    current_expression = Expression("", "")
    
    for word in base_sentences:
        if word != "":
            #print(word)
        
            word = word.upper()
            
            if word in transition_table[current_state].keys(): #verifica se é [operador, se, então] e se existe transição
                current_state = transition_table[current_state][word]
                
                if word == "ENTAO" or word == "&&":     
                    current_sentence.expression_antec_list.append(current_expression)       
                    current_expression = Expression("", "")
            
            elif word in var_list: 
                if "var" in transition_table[current_state].keys():
                    current_state = transition_table[current_state]["var"]
                    current_expression.var = word
                else:
                    print("algo está errado no código inserido")
                    exit() #lança erro pq nao existe transição            
            elif word in val_list:
                if "val" in transition_table[current_state].keys():
                    current_state = transition_table[current_state]["val"]
                    current_expression.val = word

                    if current_state == "q8": 
                        if current_sentence.expression_antec_list != []:
                            current_sentence.expression_conseq_list.append(current_expression) 
                            rules_list.append(current_sentence)
                            current_sentence = Sentence([], [])                           
                        else:
                            facts_list.append(current_expression)
                        
                        current_expression = Expression("", "")                  

                else:
                    print("algo está errado no código inserido")
                    exit() #lança erro pq nao existe transição       
            else:
                print("algo está errado no código inserido")
                exit() #erro, nao reconhece            
 
def loadBaseSentences(path="base1_q2.txt"):
    with open(path, "r") as source:
        return source.read()

def printBaseSentences():
    print("REGRAS:")
    for rule in rules_list:
        print(f"antecessor: ", rule.expression_antec_list)
        print(f"consequente: ", rule.expression_conseq_list)

    print("FATOS:")
    for fact in facts_list:
        print(fact)

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
            return True if fact.val == var_val_in_sentence else False
    
    return ""

def getVarNegationValueInSentence(val:string):
    return "False" if val == "True" else "False"        

def evaluateASentence(sentence:Sentence): #Modus Ponens
    for expression in sentence.expression_antec_list:
        if not getFactVarEvaluation(expression.var, expression.val):
            return False
            
    facts_list.append(Expression(sentence.expression_conseq_list[0].var, sentence.expression_conseq_list[0].val))
    #print(sentence.expression_conseq_list[0].var, sentence.expression_conseq_list[0].val)
    #print(facts_list)
    return True
    
# ============= ENCADEAMENTO PRA TRÁS =========================
def backwardChaining(goal_var:string):
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

                if search_result == -1:
                    break #n da p alcançar por essa sentença
                else:
                    sentence_exp_fact_count -= 1
            
            if sentence_exp_fact_count == 0: #tenho todas variaveis da sentença nos fatos
                result = evaluateASentence(sentence) #chama função para avaliar sentença
                if not result:
                    return - 1 
                elif isVariableAFact(aimed_var):
                    print(f"{aimed_var} é um fato")
                    print(getFactValue(aimed_var))
                    exit()
                
                return
    else:
        if goal_var != aimed_var and goal_var not in asked_vars:
            print(f"{goal_var} é inalcançável por esse caminho. Perguntando ao usuário...")
            if asksTheUser(goal_var):
                return True
        return -1

    """ if goal_var != aimed_var:
        print(f"{goal_var} é indeduzível.") """
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
                        exit()
            
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
        facts_list.append(Expression(var_in_question, var_value))
        return True
    
    return False


if __name__ == '__main__':
    aimed_var = input("Digite o nome do arquivo onde se encontra a base a ser lida. \n(Exemplo: base1_q2.txt): ")
    base_sentences = loadBaseSentences(aimed_var)
    #print(base_sentences)
    splited = (base_sentences.replace("\n", " ")).split(" ")
    #print(splited)
    
    generateDataStructure(splited)
    #printBaseSentences()

    aimed_var = input("\nQual a variável de busca?: ")
    aimed_var = aimed_var.upper()

    print("\nIniciando encadeamento pra frente...")
    if not forwardChaining(aimed_var):
        print("\nIniciando encadeamento pra trás...")
        if not (backwardChaining(aimed_var) == True):
            print(f"{aimed_var} é indeduzível.")
