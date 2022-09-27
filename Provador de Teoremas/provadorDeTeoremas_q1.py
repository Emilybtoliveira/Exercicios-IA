from dataclasses import dataclass


operatorAnd = "^"

# ========== ESTRUTURA DE DADOS E VAR GLOBAIS =============

@dataclass
class Expression:
    var: str
    val: bool

@dataclass
class Sentence:
    expression_antec_list: list[Expression]
    expression_conseq_list: list[Expression]

rules_list = [] # Sentences
facts_list = []  # Expressions only

# ========== Inicio Codigo ===========
def checkIfIsNegation(val):

    if val[0]=="~":
        expressao = Expression(val,False)
    else:
        expressao = Expression(val,True)

    return expressao

def createExpressionFromList(stream):
    
    listExpr = []

    if type(stream)==list:
        for item in stream:
            listExpr.append(checkIfIsNegation(item))
    else:
        listExpr.append(checkIfIsNegation(stream))
    
    return listExpr


def createListsAndAddToRule(conseq,antec):
    listConseq = createExpressionFromList(conseq)
    listAntec = createExpressionFromList(antec)


    sentenca = Sentence(listAntec,listConseq)
    
    rules_list.append(sentenca)

# ======== Tradutor de Texto (SE .. ENTAO) para "A^B->C"

def translateConseq(conseq):
    
    if '~' in conseq:
        return '->~'+conseq[0:conseq.index("=")]
    
    return "->"+conseq[0:conseq.index("=")]

def translateAntec(anteclist):
    
    newAntec = ""
    for index,antec in enumerate(anteclist):
        
        if '~' in antec:
            newAntec+='~'+antec[0:antec.index("=")]
        else:
            newAntec+=antec[0:antec.index("=")]

        if index!=len(anteclist)-1:
            newAntec+='^'
        
    return newAntec


def cleanTranslateLine(line):
    line = line.replace("AND",operatorAnd)
    line = line.replace("ENTAO","->")
    line = line.replace("SE","")

    return line
    
def translate(line):
    line = cleanTranslateLine(line)

    splitAntecConseq = line.split("->")
    
    antec = splitAntecConseq[0].split("^")
    conseq = splitAntecConseq[1]

    line = translateAntec(antec)+translateConseq(conseq)
    
    return line


def cleanLine(line):

    line = line.replace(" ","")
    line = line.replace("(","")
    line = line.replace(")","")
    line = line.replace("&","^")

    return line

# ========== Leitura do Arquivo =============

def readFileAndOutputsToList(fileName,splitter):

    source = open(fileName,'r')
    stream= source.read().split("\n")
    flagTranslated = False
    print("Base de Conhecimento")
    for line in stream:
        line = cleanLine(line)
        if "SE" in line:
            # indica que precisa de traducao
            line = translate(line)
            flagTranslated = True
            
        
        if "->" in line:
            splitConseqAntec = line.split("->")
            print(line)     
    
            conseq = splitConseqAntec[-1] 
            antec = splitConseqAntec[0].split(splitter)
            createListsAndAddToRule(conseq,antec)

        else:
            booleanConst = True

            if flagTranslated:
                
                if '~' in line:
                    line = '~'+line[0:line.index("=")]
                    booleanConst = False
                else:
                    line = line[0:line.index("=")]
                

            expressao = Expression(line,booleanConst)
            facts_list.append(expressao)
            booleanConst = True

    

# =========== RESOLUCAO ===========

def checkIfInFactsList(expression):
    return expression in facts_list

def resolucao(objetivo):
    
    if checkIfInFactsList(objetivo):
        print("Já tens a resposta!")
    else:
        counterRepetitions = 0
        needRecheck = 1
        while(needRecheck!=0):
            addInFact = False
            for sentence in rules_list:

                antecList = sentence.expression_antec_list
                conseqList = sentence.expression_conseq_list

                counter = 0
                qntTrue = 0
                
                while counter!=len(antecList):
                    exprAntec = antecList[counter]
                    if exprAntec not in facts_list:
                        counter = 0
                        qntTrue = 0
                        break
                    else:
                        qntTrue+=1
                        counter+=1
                
                if qntTrue == counter and qntTrue!=0:
                    # se quiser visualizar o caminho só descomentar a linha abaixo
                    # print(f"Var: {sentence.expression_conseq_list[0].var} Valor: {sentence.expression_conseq_list[0].val}")
                    if conseqList[0] == objetivo:
                        print("PROVADO!")
                        needRecheck = 0
                        addInFact = False
                        break
                    else:
                        
                        facts_list.append(conseqList[0])
                        addInFact = True
                        

            if addInFact:
                needRecheck=1
                counterRepetitions+=1
            else:
                needRecheck=0
            
            if counterRepetitions >= len(rules_list)**2:
                print("Nao deu!") 
                counter = 0
                qntTrue = 0   
                needRecheck = 0
                break
            
def main():

    readFileAndOutputsToList("base3_c1_q1.txt",operatorAnd)

    obj = input("QUAL O OBJETIVO? FORMATO: VAR BOOL: ").split(" ")
    varObj = obj[0]
    boolobj = obj[1].lower() == "true"

    if not boolobj:
        varObj = "~"+obj[0]

    exprObj = Expression(varObj,boolobj)
    
    resolucao(exprObj)

main()