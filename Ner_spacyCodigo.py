import re
import os
import pdfplumber
import spacy
import pandas as pd

# Carregar o modelo de NER
nlp = spacy.load("en_ner_bc5cdr_md")

# Função para extrair texto de um PDF
def extrair_texto_pdf(caminho_pdf):
    with pdfplumber.open(caminho_pdf) as pdf:
        texto = ""
        for pagina in pdf.pages:
            texto += pagina.extract_text()
    return texto

def extrair_informacoes_basicas(texto):
    nome = re.search(r"Nome:\s*([^\n]+)", texto)
    nome = nome.group(1).split("Id")[0].strip()
    
    sexo = re.search(r"Sexo:\s*(M|F)", texto)
    sexo = sexo.group(1)
    
    nascimento = re.search(r"Data de Nascimento:\s*([\d-]+)", texto)
    nascimento = nascimento.group(1)
    
    return nome, sexo, nascimento

def extrair_procedimentos_vacinas(texto):
    # Extrair Procedimentos
    procedimentos = re.search(r"Procedimentos:\s*(.+?)\n", texto, re.DOTALL)
    procedimentos = procedimentos.group(1).split(", ") if procedimentos else []
    
    # Extrair Vacinas
    vacinas = re.search(r"Vacinas:\s*(.+)", texto, re.DOTALL)
    vacinas = vacinas.group(1).split(", ") if vacinas else []
    
    return procedimentos, vacinas


# Função para aplicar o NER no texto e agrupar resultados
def aplicar_ner(texto):
    doc = nlp(texto)
    doencas = []
    medicamentos = []
    
    # Palavras irrelevantes a serem ignoradas
    palavras_irrelevantes = {"mg", "ml", "actuat", "oral", "tablet", "solution", "preservative", "free"}

    # Filtrar e agrupar entidades
    for entidade in doc.ents:
        if entidade.label_ == 'DISEASE' and entidade.text.lower() not in ["doenças prévias"]:
            doencas.append(entidade.text)
        elif entidade.label_ == 'CHEMICAL':
            # Verificar se a entidade contém apenas palavras irrelevantes
            if not all(palavra.lower() in palavras_irrelevantes for palavra in entidade.text.split()):
                medicamentos.append(entidade.text)
    
    # Remover duplicatas e manter a ordem
    doencas = list(dict.fromkeys(doencas))
    medicamentos = list(dict.fromkeys(medicamentos))
    
    return doencas, medicamentos

# Processar múltiplos PDFs e organizar os dados em tabelas
def processar_pdfs_em_tabelas(pasta_pdfs):
    pacientes = []
    condicoes = []
    tratamentos = []
    procedimentos_vacinas = []

    for arquivo in os.listdir(pasta_pdfs):
        if arquivo.endswith(".pdf"):
            caminho_pdf = os.path.join(pasta_pdfs, arquivo)
            print(f"Processando: {arquivo}")
            
            # Extrair texto do PDF
            texto = extrair_texto_pdf(caminho_pdf)
            
            # Extrair informações básicas
            nome, sexo, nascimento = extrair_informacoes_basicas(texto)
            
            # Aplicar NER ao texto
            doencas, medicamentos = aplicar_ner(texto)
            
            # Extrair Procedimentos e Vacinas
            procedimentos, vacinas = extrair_procedimentos_vacinas(texto)
            
            # Adicionar informações do paciente
            pacientes.append({"Nome": nome, "Sexo": sexo, "Data de Nascimento": nascimento})
            
            # Adicionar condições médicas
            for doenca in doencas:
                condicoes.append({"Nome do Paciente": nome, "Condição Médica": doenca})
            
            # Adicionar medicamentos
            for medicamento in medicamentos:
                tratamentos.append({"Nome do Paciente": nome, "Medicamento": medicamento})
            
            # Adicionar procedimentos
            for procedimento in procedimentos:
                procedimentos_vacinas.append({"Nome do Paciente": nome, "Procedimento/Vacina": procedimento})
            
            # Adicionar vacinas
            for vacina in vacinas:
                procedimentos_vacinas.append({"Nome do Paciente": nome, "Procedimento/Vacina": vacina})

    # Criar DataFrames
    df_pacientes = pd.DataFrame(pacientes)
    df_condicoes = pd.DataFrame(condicoes)
    df_tratamentos = pd.DataFrame(tratamentos)
    df_procedimentos_vacinas = pd.DataFrame(procedimentos_vacinas)
    
    return df_pacientes, df_condicoes, df_tratamentos, df_procedimentos_vacinas

# Caminho para a pasta com PDFs
pasta_pdfs = "C:\\Users\\Usuario\\Desktop\\TCCPLN\\pdf_output"

# Processar os PDFs
df_pacientes, df_condicoes, df_tratamentos, df_procedimentos_vacinas = processar_pdfs_em_tabelas(pasta_pdfs)

# Salvar os DataFrames em arquivos CSV
df_pacientes.to_csv("pacientes.csv", index=False)
df_condicoes.to_csv("condicoes.csv", index=False)
df_tratamentos.to_csv("tratamentos.csv", index=False)
df_procedimentos_vacinas.to_csv("procedimentos_vacinas.csv", index=False)

# Exibir os DataFrames
print("Pacientes:")
print(df_pacientes.head())
print("\nCondições:")
print(df_condicoes.head())
print("\nTratamentos:")
print(df_tratamentos.head())
print("\nProcedimentos/Vacinas:")
print(df_procedimentos_vacinas.head())
