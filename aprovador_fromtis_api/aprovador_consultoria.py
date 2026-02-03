# from mysql import MysqlConnection
# from Dev.code.dates_aux.date_functions import CalendarioBrasileiro

from sqlalchemy.sql import text

from zeep import Client
from zeep.transports import Transport
from zeep import xsd

from requests import Session
from requests.auth import HTTPBasicAuth

from datetime import datetime, timedelta

from pprint import pprint

from pathlib import Path
import requests
import json
import os
import sys

import time

import itertools

import random

import xmltodict
import json


DATE_RANGE_INTERVAL = 8


DICT_CODIGO_SITUCAO = {
    '0'  : 'NÃO DEFINIDO',
    '5'  : 'CADASTRAR MANUALMENTE NOVO CODIGO DE SITUACAO!',
    '1'  : 'AGUARDANDO APROVAÇÃO DA CONSULTORIA',
    '2'  : 'REPROVADO PELA CONSULTORIA',
    '3'  : 'EXPIRADO ENQUANTO AGUARDAVA APROVAÇÃO DA CONSULTORIA',
    '4'  : 'AGUARDANDO APROVAÇÃO DO GESTOR',
    '5'  : 'REPROVADO PELO GESTOR',
    '6'  : 'EXPIRADO ENQUANTO AGUARDAVA APROVAÇÃO DO GESTOR',
    '7'  : 'AGUARDANDO APROVAÇÃO DA CERTIFICADORA',
    '8'  : 'EXPIRADO ENQUANTO AGUARDAVA APROVAÇÃO DA CERTIFICADORA',
    '9'  : 'PENDENTE DE ENVIO PARA CERTIFICADORA',
    '10' : 'EXPIRADO NA APROVAÇÃO PELO ADMINISTRADOR',
    '11' : 'AGUARDANDO APROVAÇÃO DO CUSTÓDIA',
    '12' : 'REPROVADO PELA CUSTÓDIA',
    '13' : 'EXPIRADO ENQUANTO AGUARDAVA APROVAÇÃO DA CUSTÓDIA',
    '14' : 'AGUARDANDO APROVAÇÃO DO GESTOR TED',
    '15' : 'AGUARDANDO PROCESSAMENTO NA C3',
    '16' : 'EXPIRADO ENQUANTO AGUARDAVA APROVAÇÃO DO GESTOR TED',
    '17' : 'REPROVADO PELO GESTOR TED',
    '18' : 'PAGO PELO BANCO COBRADOR',
    '19' : 'TRANSFERÊNCIA ELETRÔNICA DE RECURSOS ENVIADA',
    '20' : 'TRANSFERÊNCIA ELETRÔNICA DE RECURSOS ENVIADA C3',
    '21' : 'EXPIRADO DURANTE ENVIO PARA CERTIFICADORA',
    '22' : 'EXPIRADO NA CONTA INTERNA DO PAULISTA',
    '23' : 'REPROVADO PELA CERTIFICADORA',
    '24' : 'REPROVADO PELO PROCESSAMENTO NA C3',
    '25' : 'TRANSFERÊNCIA ELETRÔNICA DE RECURSOS ENVIADA VIA ARQUIVO',
    '26' : 'APROVADO PELO GESTOR',
    '27' : 'TED LIQUIDADA',
    '28' : 'TED EFETIVADA BANCO LIQUIDANTE',
    '30' : 'SITUACAO NOVA',
    '31' : 'SITUACAO NOVA',
    '32' : 'SITUACAO NOVA',
    '36' : 'SITUACAO NOVA',
    '34' : 'SITUACAO NOVA',
    '37' : 'SITUACAO NOVA',
    '29' : 'SITUACAO NOVA',
    '39' : 'SITUACAO NOVA',
    '38' : 'SITUACAO NOVA',
    '35' : 'SITUACAO NOVA',
    '41' : 'SITUACAO NOVA',
    '33' : 'SITUACAO NOVA',
    '44' : 'CADASTRAR MANUALMENTE NOVO CODIGO DE SITUACAO!',
    '42' : 'CADASTRAR MANUALMENTE NOVO CODIGO DE SITUACAO!',
    '46' : 'CADASTRAR MANUALMENTE NOVO CODIGO DE SITUACAO!',
    '40' : 'CADASTRAR MANUALMENTE NOVO CODIGO DE SITUACAO!',
    '45' : 'CADASTRAR MANUALMENTE NOVO CODIGO DE SITUACAO!',
    '54' : 'CADASTRAR MANUALMENTE NOVO CODIGO DE SITUACAO!',
}

def generate_key_hash(cnpj_fundo, date):
    date_string = date.strftime('%Y-%m-%d')
    return f'{cnpj_fundo}_{date}'

def retrieve_dict_credencial_fundo():
    # print("AQUI")
    # with db.engine.connect() as connection:
    #     result = connection.execute(text("""
    #     SELECT
    #             f.cnpj as cnpj_fundo, c.ws_username, c.ws_password, c.url_fromtis
    #     FROM webservice_fromtis.fundo f
    #     JOIN webservice_fromtis.credencial c on c.id_credencial = f.credencial_id_credencial
    #     WHERE f.id_fundo = 3;""")).mappings().all()[0]
    # print("AQUI2")

    # with db.engine.connect() as connection:
    #     def retrieve_dict_credencial_fundo(db):
    # print("AQUI")
    result = {
        "cnpj_fundo": "32526025000110",
        "ws_username": "usr.carmel",
        "ws_password": "OGM6Vyl4Q",
        "url_fromtis": "https://portalfidc4.singulare.com.br/portal-servicos"
    }
    # return result
    return result

def retrieve_list_operacoes_aprovar(dict_credencial):
    print("=" * 80)
    print("RETRIEVING OPERATIONS TO APPROVE (CONSULTORIA)")
    print("=" * 80)
    print(f"Credentials: {dict_credencial}")

    session = Session()
    # endpoint = f"{dict_credencial['url_fromtis']}/servicos/consulta/operacao"
    # print(endpoint)

    # Always use portalfidc4 endpoint for consistency
    endpoint = "https://portalfidc4.singulare.com.br/portal-servicos/servicos/consulta/operacao"
    # list_endpoints = [
    #     "https://portalfidc.singulare.com.br/portal-servicos/servicos/consulta/operacao",
    #     "https://portalfidc4.singulare.com.br/portal-servicos/servicos/consulta/operacao"
    # ]
    # endpoint  = random.choice(list_endpoints)
    print(f"\nEndpoint selected: {endpoint}")

    session = requests.Session()
    session.auth = (dict_credencial['ws_username'], dict_credencial['ws_password'])
    print(f"Authentication: {dict_credencial['ws_username']} / {'*' * len(dict_credencial['ws_password'])}")

    request_data = {
        'formato': 'xml',
        'data': datetime.now().strftime('%d-%m-%Y'),
    }
    print(f"\nRequest data: {request_data}")

    print(f"\nSending GET request to {endpoint}...")
    response = session.get(endpoint, data=request_data)
    print(f"Response status code: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    print(f"\nResponse text (first 500 chars):\n{response.text[:500]}")

    dict_data = xmltodict.parse(response.text)
    print(f"\nParsed XML data structure: {type(dict_data)}")
    print(f"Top-level keys: {list(dict_data.keys())}")

    if dict_data.get('erro'):
        print(f"\n⚠️  API returned error: {dict_data['erro']}")
        if dict_data['erro']['mensagem'].upper() == 'NENHUMA INFORMACAO ENCONTRADO.':
            print("No operations found. Waiting 10 seconds...")
            time.sleep(10)
            return []

    dict_data = dict_data['operacaoRecebivelDtoes']['operacao']
    print(f"\n✅ Found {len(dict_data) if isinstance(dict_data, list) else 1} operation(s)")
    print("=" * 80)

    return dict_data

def consulta_operacao():

    dict_credencial = retrieve_dict_credencial_fundo()
    list_operacoes_aprovar = retrieve_list_operacoes_aprovar(dict_credencial)

    # Initialize statistics dictionary
    status_stats = {}

    for dict_operacao in reversed(list_operacoes_aprovar):
        print(f"\n📋 Processing operation: {dict_operacao['nomeArquivo']} - Status: {dict_operacao['codigoSituacaoOperacao']} - Fund: {dict_operacao['cnpjFundo']}")

        # Collect statistics
        status_code = dict_operacao['codigoSituacaoOperacao']
        if status_code not in status_stats:
            status_stats[status_code] = 0
        status_stats[status_code] += 1

        if DICT_CODIGO_SITUCAO.get(dict_operacao['codigoSituacaoOperacao']) is None:
            print(f"   ⚠️  Unknown status code: {dict_operacao['codigoSituacaoOperacao']} - Skipping")
            continue

        status_description = DICT_CODIGO_SITUCAO[dict_operacao['codigoSituacaoOperacao']]
        print(f"   Status description: {status_description}")

        if DICT_CODIGO_SITUCAO[dict_operacao['codigoSituacaoOperacao']].upper() == 'AGUARDANDO APROVAÇÃO DA CONSULTORIA' and \
            dict_operacao['cnpjFundo'] == '32526025000110':
            print("\n" + "=" * 80)
            print("🎯 OPERATION MATCHES APPROVAL CRITERIA (CONSULTORIA)!")
            print("=" * 80)
            print(f"Full operation details: {dict_operacao}")


            session = Session()
            wsdl = f"{dict_credencial['url_fromtis']}/servicos/soap/aprovacaoOperacaoConsultoria?wsdl"
            print(f"\n📡 SOAP WSDL URL: {wsdl}")
            session.auth = HTTPBasicAuth(dict_credencial['ws_username'], dict_credencial['ws_password'])

            # Try to create SOAP client with retry logic for 429 errors
            client = None
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    print(f"Creating SOAP client (attempt {attempt + 1}/{max_retries})...")
                    client = Client(wsdl, transport=Transport(session=session))
                    client.transport.session.headers.update(
                        {'username': dict_credencial['ws_username'], 'password': dict_credencial['ws_password']})
                    print("✅ SOAP client created successfully")
                    break
                except Exception as e:
                    print(f"\n❌ Error creating SOAP client: {type(e).__name__}")
                    print(f"Error details: {str(e)}")
                    if '429' in str(e) and attempt < max_retries - 1:
                        wait_time = 30 * (attempt + 1)  # Exponential backoff: 30s, 60s, 90s
                        print(f"⏳ Rate limit hit. Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                    else:
                        print("❌ Failed to create SOAP client. Skipping this operation.")
                        continue  # Skip to next operation

            if client is None:
                print("❌ Could not create SOAP client after all retries. Skipping operation.")
                continue


            request_data = {
                        'cnpjFundo': dict_operacao['cnpjFundo'],
                        'cpfCnpjCedente': dict_operacao['documentoCedente'],
                        'nomeArquivo': dict_operacao['nomeArquivo'],
                        'valorReembolso': dict_operacao['calculoTotalPagamento']
            }
            print("\n🚀 APPROVING OPERATION (CONSULTORIA)")
            print(f"Initial SOAP Request data: {request_data}")

            if dict_operacao['documentoCedente'] in [
                    '36.947.229/0001-85', '36947229000185',
                    # '03.130.170/0001-89', '03130170000189', # Joao pediu para Chow no dia 31/10/24 via whats para zerar
                    '28.080.769/0001-86', '28080769000186',
                    '53.032.513/0001-40', '53032513000140',
                ]:
                print(f"⚠️  Special cedente detected: {dict_operacao['documentoCedente']} - Setting valorReembolso to '0'")
                request_data = {
                            'cnpjFundo': dict_operacao['cnpjFundo'],
                            'cpfCnpjCedente': dict_operacao['documentoCedente'],
                            'nomeArquivo': dict_operacao['nomeArquivo'],
                            'valorReembolso': '0'
                }
                print(f"Modified SOAP Request data: {request_data}")


            # Retry logic for 429 errors
            response = None
            try:
                print("Calling SOAP service aprovarConsultoria...")
                response = client.service.aprovarConsultoria(request_data)
                print(f"\n✅ SOAP Response received: {response}")
            except Exception as e:
                print('\n' + '=' * 80)
                print(f"❌ SOAP Error occurred: {type(e).__name__}")
                print(f"Error details: {str(e)}")
                print('=' * 80)
                if '429' in str(e):
                    print("⏳ Rate limit hit. Waiting 30 seconds before retry...")
                    time.sleep(30)
                    try:
                        print("Retrying SOAP call...")
                        response = client.service.aprovarConsultoria(request_data)
                        print(f"\n✅ SOAP Response (retry): {response}")
                    except Exception as retry_error:
                        print(f"❌ Retry also failed: {type(retry_error).__name__}")
                        print(f"Error details: {str(retry_error)}")
                        print("Skipping this operation.")
                        continue

            if response:
                print(f"\nFinal response: {response}")
                # print(response.__dict__)
                print("=" * 80)

            print("⏳ Waiting 10 seconds before next approval to avoid rate limiting...")
            time.sleep(10)

    # Display summary of operations by status
    print("\n\n")
    print("=" * 80)
    print("📊 SUMMARY - OPERATIONS BY STATUS (CONSULTORIA)")
    print("=" * 80)

    if not status_stats:
        print("No operations found.")
    else:
        # Sort by status code
        for status_code in sorted(status_stats.keys()):
            count = status_stats[status_code]
            status_name = DICT_CODIGO_SITUCAO.get(status_code, "UNKNOWN STATUS")
            print(f"Status {status_code:>2} - {status_name:<50} : {count:>3} operation(s)")

        print("-" * 80)
        print(f"{'TOTAL':<55} : {sum(status_stats.values()):>3} operation(s)")

    print("=" * 80)

def main():
    # Determine the path to mysql.json
    # If running as a PyInstaller bundle, use the directory of the executable
    # Otherwise, use the command line argument
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller bundle
        bundle_dir = os.path.dirname(sys.executable)
        config_path = os.path.join(bundle_dir, 'mysql.json')
        print(f"Running as PyInstaller bundle. Config path: {config_path}")
    else:
        # Running as a normal Python script
        if len(sys.argv) > 1:
            config_path = sys.argv[1]
        else:
            # Default to mysql.json in the same directory as the script
            config_path = os.path.join(os.path.dirname(__file__), 'mysql.json')
        print(f"Running as Python script. Config path: {config_path}")

    dict_config_mysql = json.loads(Path(config_path).read_text())
    # db = MysqlConnection(**dict_config_mysql)

    iteration = 0
    while True:
        iteration += 1
        time.sleep(5)
        print("\n\n")
        print("🔄" * 40)
        print(f"🔄 ITERATION #{iteration} - Checking operations to approve (CONSULTORIA)")
        print(f"🔄 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🔄" * 40)
        # consulta_operacao(db, dict_config, cnpj_to_approve)
        consulta_operacao()
        print(f"\n⏸️  Waiting 5 seconds before next check...")
        time.sleep(5)

if __name__=='__main__':
    main()

