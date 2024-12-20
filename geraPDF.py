import pandas as pd
from fpdf import FPDF
import re
import os

# Carregar os dados gerados pelo Synthea
patients = pd.read_csv('synthea_sample_data_csv_apr2020/csv/patients.csv')
conditions = pd.read_csv('synthea_sample_data_csv_apr2020/csv/conditions.csv')
observations = pd.read_csv('synthea_sample_data_csv_apr2020/csv/observations.csv')
medications = pd.read_csv('synthea_sample_data_csv_apr2020/csv/medications.csv')
immunizations = pd.read_csv('synthea_sample_data_csv_apr2020/csv/immunizations.csv')
careplans = pd.read_csv('synthea_sample_data_csv_apr2020/csv/careplans.csv')
procedures = pd.read_csv('synthea_sample_data_csv_apr2020/csv/procedures.csv')

# Função para remover números do nome
def limpar_nome(nome):
    return re.sub(r'\d+', '', nome).strip()

# Função para remover duplicatas de listas
def remover_duplicatas(lista):
    return list(dict.fromkeys(lista))


# Função para formatar e gerar PDF para um paciente
def gerar_prontuario(patient_data, patient_id):
    pdf = FPDF()
    pdf.add_page()

    # Identificação do paciente
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Prontuário Eletrônico", ln=True, align='C')

    pdf.ln(10)  # linha em branco

    # Limpar números do nome e gerar o CPF (usando os números para o CPF)
    nome_primeiro = limpar_nome(patient_data['FIRST'])
    nome_ultimo = limpar_nome(patient_data['LAST'])
    id = ''.join(filter(str.isdigit, patient_data['FIRST'] + patient_data['LAST']))  # ID com números do nome


    nome_arquivo = f"{nome_primeiro}_{nome_ultimo}".replace(" ", "_")  # Nome do arquivo com nome do paciente


    # Exibir o nome limpo e o CPF
    pdf.cell(200, 10, txt=f"Nome: {nome_primeiro} {nome_ultimo}", ln=True)
    pdf.cell(200, 10, txt=f"Id: {id}", ln=True)

    pdf.cell(200, 10, txt=f"Sexo: {patient_data['GENDER']}", ln=True)
    pdf.cell(200, 10, txt=f"Data de Nascimento: {patient_data['BIRTHDATE']}", ln=True)

    # Anamnese
    pdf.ln(10)
    pdf.cell(200, 10, txt="Anamnese:", ln=True)

    # Doenças e Alergias
    condition_data = conditions[conditions['PATIENT'] == patient_id]
    if not condition_data.empty:
        # Doenças prévias
        pdf.cell(200, 10, txt="Doenças prévias:", ln=True)
        for index, row in condition_data.iterrows():
            pdf.multi_cell(0, 10, txt=f"- {row['DESCRIPTION']} (Início: {row['START']})")
    
    # Se houver alergias, exiba-as (condições contendo "allergy" no nome)
    allergy_data = condition_data[condition_data['DESCRIPTION'].str.contains("allergy", case=False, na=False)]
    if not allergy_data.empty:
        pdf.ln(5)
        pdf.cell(200, 10, txt="Alergias:", ln=True)
        for index, row in allergy_data.iterrows():
            pdf.multi_cell(0, 10, txt=f"- {row['DESCRIPTION']}")

    # Exame Físico
    pdf.ln(10)
    pdf.cell(200, 10, txt="Exame Físico:", ln=True)

    # Pressão arterial
    systolic_bp = observations[(observations['PATIENT'] == patient_id) & (observations['DESCRIPTION'] == 'Systolic Blood Pressure')]
    if not systolic_bp.empty:
        pdf.cell(200, 10, txt=f"Pressão arterial: {systolic_bp['VALUE'].values[0]} mmHg", ln=True)

    # Frequência cardíaca
    heart_rate = observations[(observations['PATIENT'] == patient_id) & (observations['DESCRIPTION'] == 'Heart rate')]
    if not heart_rate.empty:
        pdf.cell(200, 10, txt=f"Frequência cardíaca: {heart_rate['VALUE'].values[0]} bpm", ln=True)

    #altura e peso???

    # Hipóteses Diagnósticas
    pdf.ln(10)
    pdf.cell(200, 10, txt="Hipóteses Diagnósticas:", ln=True)
    diagnostic_hypothesis = conditions[(conditions['PATIENT'] == patient_id) & (conditions['STOP'].isna())]  # Sem data de término
    if not diagnostic_hypothesis.empty:
        for index, row in diagnostic_hypothesis.iterrows():
            pdf.multi_cell(0, 10, txt=f"Condição: {row['DESCRIPTION']} (Início: {row['START']})")

    # Diagnósticos Definitivos
    pdf.ln(10)
    pdf.cell(200, 10, txt="Diagnósticos Definitivos:", ln=True)
    definitive_diagnosis = conditions[(conditions['PATIENT'] == patient_id) & (conditions['STOP'].notna())]  # Com data de término
    if not definitive_diagnosis.empty:
        for index, row in definitive_diagnosis.iterrows():
            pdf.multi_cell(0, 10, txt=f"Condição: {row['DESCRIPTION']} (Início: {row['START']}, Fim: {row['STOP']})")

    # Tratamentos Efetuados
    pdf.ln(10)
    pdf.cell(200, 10, txt="Tratamentos Efetuados:", ln=True)
    medication_data = medications[medications['PATIENT'] == patient_id]
    procedure_data = procedures[procedures['PATIENT'] == patient_id]
    careplan_data = careplans[careplans['PATIENT'] == patient_id]

    if not medication_data.empty:
        pdf.multi_cell(0, 10, txt=f"Medicações: {', '.join(remover_duplicatas(medication_data['DESCRIPTION'].values))}")
    if not procedure_data.empty:
        pdf.multi_cell(0, 10, txt=f"Procedimentos: {', '.join(remover_duplicatas(procedure_data['DESCRIPTION'].values))}")
    if not careplan_data.empty:
        pdf.multi_cell(0, 10, txt=f"Planos de cuidado: {', '.join(remover_duplicatas(careplan_data['DESCRIPTION'].values))}")
    
    # Imunizações
    pdf.ln(10)
    pdf.cell(200, 10, txt="Imunizações:", ln=True)
    immunization_data = immunizations[immunizations['PATIENT'] == patient_id]
    if not immunization_data.empty:
        pdf.multi_cell(0, 10, txt=f"Vacinas: {', '.join(remover_duplicatas(immunization_data['DESCRIPTION'].values))}")

    # Criar diretório de saída se não existir
    if not os.path.exists("pdf_output"):
        os.makedirs("pdf_output")

    # Salvar o PDF
    pdf.output(f"pdf_output/prontuario_{nome_arquivo}.pdf")


def main():
    # Gerar o prontuário para todos os pacientes
    for _, patient in patients.iterrows():
        gerar_prontuario(patient, patient['Id'])

if __name__ == "__main__":
    main()