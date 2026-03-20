#!/usr/bin/env python3
"""
Combined Aprovador - Handles both Gestor and Consultoria approvals
"""

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
    '15' : 'REPROVADO PELO GESTOR TED',
    '16' : 'EXPIRADO ENQUANTO AGUARDAVA APROVAÇÃO DO GESTOR TED',
    '17' : 'AGUARDANDO APROVAÇÃO DO ADMINISTRADOR',
    '18' : 'REPROVADO PELO ADMINISTRADOR',
    '19' : 'TRANSFERÊNCIA ELETRÔNICA DE RECURSOS ENVIADA',
    '20' : 'TRANSFERÊNCIA ELETRÔNICA DE RECURSOS CONFIRMADA',
    '21' : 'TRANSFERÊNCIA ELETRÔNICA DE RECURSOS REJEITADA',
    '22' : 'TRANSFERÊNCIA ELETRÔNICA DE RECURSOS DEVOLVIDA',
    '23' : 'TRANSFERÊNCIA ELETRÔNICA DE RECURSOS CANCELADA',
}

# Special cedentes that require valorReembolso = '0' for consultoria approvals
SPECIAL_CEDENTES = [
    '36.947.229/0001-85', '36947229000185',
    '28.080.769/0001-86', '28080769000186',
    '53.032.513/0001-40', '53032513000140',
]


def get_config_path():
    """Get the path to mysql.json config file"""
    if getattr(sys, 'frozen', False):
        # Running as compiled binary
        return os.path.join(os.path.dirname(sys.executable), 'mysql.json')
    else:
        # Running as script
        return os.path.join(os.path.dirname(__file__), 'mysql.json')


def retrieve_dict_credencial_fundo():
    """Retrieve credentials for the fund"""
    config_path = get_config_path()
    print(f"📁 Loading config from: {config_path}")
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    dict_credencial = {
        'url_fromtis': 'https://portalfidc4.singulare.com.br/portal-servicos',
        'ws_username': 'usr.carmel',
        'ws_password': 'OGM6Vyl4Q'
    }
    
    print(f"✅ Credentials loaded: {dict_credencial['ws_username']}")
    return dict_credencial


def retrieve_list_operacoes_aprovar(dict_credencial):
    """Retrieve list of operations to approve"""
    url = f"{dict_credencial['url_fromtis']}/servicos/consulta/operacao"
    
    data_hoje = datetime.now()
    data_hoje_str = data_hoje.strftime('%d-%m-%Y')
    
    params = {
        'formato': 'xml',
        'data': data_hoje_str
    }
    
    print(f"\n🌐 Fetching operations from API...")
    print(f"URL: {url}")
    print(f"Params: {params}")
    print(f"Auth: {dict_credencial['ws_username']}")
    
    response = requests.get(
        url,
        params=params,
        auth=(dict_credencial['ws_username'], dict_credencial['ws_password'])
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response length: {len(response.text)} bytes")
    
    if response.status_code != 200:
        print(f"❌ Error: HTTP {response.status_code}")
        print(f"Response: {response.text[:500]}")
        return []
    
    dict_response = xmltodict.parse(response.text)

    # Check for error response
    if 'erro' in dict_response:
        mensagem = dict_response['erro'].get('mensagem', '')
        print(f"⚠️  API returned error: {mensagem}")
        if 'NENHUMA INFORMACAO ENCONTRADO' in mensagem.upper():
            print("ℹ️  No operations found for today")
            return []
        return []

    # Correct XML structure: operacaoRecebivelDtoes -> operacao
    list_operacoes = dict_response.get('operacaoRecebivelDtoes', {}).get('operacao', [])

    if not isinstance(list_operacoes, list):
        list_operacoes = [list_operacoes]

    print(f"✅ Found {len(list_operacoes)} operations")
    return list_operacoes


def approve_operation(dict_operacao, dict_credencial, approval_type):
    """
    Approve an operation

    Args:
        dict_operacao: Operation details
        dict_credencial: Credentials
        approval_type: 'gestor' or 'consultoria'

    Returns:
        True if successful, False otherwise
    """
    session = Session()

    # Determine SOAP endpoint and method based on approval type
    if approval_type == 'gestor':
        wsdl = f"{dict_credencial['url_fromtis']}/servicos/soap/aprovacaoOperacaoGestor?wsdl"
        soap_method_name = 'aprovarGestor'
    else:  # consultoria
        wsdl = f"{dict_credencial['url_fromtis']}/servicos/soap/aprovacaoOperacaoConsultoria?wsdl"
        soap_method_name = 'aprovarConsultoria'

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
                wait_time = 5  # Wait 5 seconds on rate limit
                print(f"⏳ Rate limit hit. Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                print("❌ Failed to create SOAP client. Skipping this operation.")
                return False

    if client is None:
        print("❌ Could not create SOAP client after all retries. Skipping operation.")
        return False

    # Prepare request data
    request_data = {
        'cnpjFundo': dict_operacao['cnpjFundo'],
        'cpfCnpjCedente': dict_operacao['documentoCedente'],
        'nomeArquivo': dict_operacao['nomeArquivo'],
    }

    # Add valorReembolso for consultoria approvals
    if approval_type == 'consultoria':
        request_data['valorReembolso'] = dict_operacao['calculoTotalPagamento']

        # Check for special cedentes
        if dict_operacao['documentoCedente'] in SPECIAL_CEDENTES:
            print(f"⚠️  Special cedente detected: {dict_operacao['documentoCedente']} - Setting valorReembolso to '0'")
            request_data['valorReembolso'] = '0'

    print(f"\n🚀 APPROVING OPERATION ({approval_type.upper()})")
    print(f"SOAP Request data: {request_data}")

    # Get the SOAP method
    soap_method = getattr(client.service, soap_method_name)

    # Retry logic for 429 errors
    response = None
    try:
        print(f"Calling SOAP service {soap_method_name}...")
        response = soap_method(request_data)
        print(f"\n✅ SOAP Response received: {response}")
    except Exception as e:
        print('\n' + '=' * 80)
        print(f"❌ SOAP Error occurred: {type(e).__name__}")
        print(f"Error details: {str(e)}")
        print('=' * 80)
        if '429' in str(e):
            print("⏳ Rate limit hit. Waiting 5 seconds before retry...")
            time.sleep(5)
            try:
                print("Retrying SOAP call...")
                response = soap_method(request_data)
                print(f"\n✅ SOAP Response (retry): {response}")
            except Exception as retry_error:
                print(f"❌ Retry also failed: {type(retry_error).__name__}")
                print(f"Error details: {str(retry_error)}")
                print("Skipping this operation.")
                return False

    if response:
        print(f"\nFinal response: {response}")
        print("=" * 80)
        return True

    return False


def consulta_operacao():
    """Main function to query and approve operations"""
    dict_credencial = retrieve_dict_credencial_fundo()
    list_operacoes_aprovar = retrieve_list_operacoes_aprovar(dict_credencial)

    # Initialize statistics dictionaries
    status_stats = {}
    approval_stats = {'gestor': 0, 'consultoria': 0, 'skipped': 0}

    for dict_operacao in reversed(list_operacoes_aprovar):
        print(f"\n📋 Processing operation: {dict_operacao['nomeArquivo']} - Status: {dict_operacao['codigoSituacaoOperacao']} - Fund: {dict_operacao['cnpjFundo']}")

        # Collect statistics
        status_code = dict_operacao['codigoSituacaoOperacao']
        if status_code not in status_stats:
            status_stats[status_code] = 0
        status_stats[status_code] += 1

        if DICT_CODIGO_SITUCAO.get(dict_operacao['codigoSituacaoOperacao']) is None:
            print(f"   ⚠️  Unknown status code: {dict_operacao['codigoSituacaoOperacao']} - Skipping")
            approval_stats['skipped'] += 1
            continue

        status_description = DICT_CODIGO_SITUCAO[dict_operacao['codigoSituacaoOperacao']]
        print(f"   Status description: {status_description}")

        # Check if operation matches approval criteria
        approval_type = None

        if (DICT_CODIGO_SITUCAO[dict_operacao['codigoSituacaoOperacao']].upper() == 'AGUARDANDO APROVAÇÃO DO GESTOR' and
            dict_operacao['cnpjFundo'] == '32526025000110'):
            approval_type = 'gestor'
        elif (DICT_CODIGO_SITUCAO[dict_operacao['codigoSituacaoOperacao']].upper() == 'AGUARDANDO APROVAÇÃO DA CONSULTORIA' and
              dict_operacao['cnpjFundo'] == '32526025000110'):
            approval_type = 'consultoria'

        if approval_type:
            print("\n" + "=" * 80)
            print(f"🎯 OPERATION MATCHES APPROVAL CRITERIA ({approval_type.upper()})!")
            print("=" * 80)
            print(f"Full operation details: {dict_operacao}")

            # Approve the operation
            success = approve_operation(dict_operacao, dict_credencial, approval_type)

            if success:
                approval_stats[approval_type] += 1
            else:
                approval_stats['skipped'] += 1

            print("⏳ Waiting 1 second before next approval...")
            time.sleep(1)
        else:
            approval_stats['skipped'] += 1

    # Display summary of operations by status
    print("\n\n")
    print("=" * 80)
    print("📊 SUMMARY - OPERATIONS BY STATUS")
    print("=" * 80)

    if status_stats:
        for status_code in sorted(status_stats.keys()):
            status_name = DICT_CODIGO_SITUCAO.get(status_code, 'UNKNOWN')
            count = status_stats[status_code]
            print(f"Status {status_code} ({status_name}): {count} operations")
    else:
        print("No operations found")

    print("\n" + "=" * 80)
    print("📊 SUMMARY - APPROVALS")
    print("=" * 80)
    print(f"✅ Gestor approvals: {approval_stats['gestor']}")
    print(f"✅ Consultoria approvals: {approval_stats['consultoria']}")
    print(f"⏭️  Skipped: {approval_stats['skipped']}")
    print(f"📊 Total processed: {len(list_operacoes_aprovar)}")
    print("=" * 80)


def main():
    """Main loop"""
    print("=" * 80)
    print("🚀 APROVADOR FROMTIS - COMBINED (GESTOR + CONSULTORIA)")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    while True:
        try:
            consulta_operacao()
        except Exception as e:
            print(f"\n❌ Error in main loop: {type(e).__name__}")
            print(f"Error details: {str(e)}")
            import traceback
            traceback.print_exc()

        print(f"\n⏳ Waiting 5 seconds before next query...")
        time.sleep(5)


if __name__ == '__main__':
    main()

