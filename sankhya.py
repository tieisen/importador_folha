import os
import re
import requests
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

class Sankhya:

    def __init__(self):
        self.url_login = os.getenv('URL_LOGIN')
        self.url_busca = os.getenv('URL_BUSCA')
        self.url_registro = os.getenv('URL_REGISTRO')
        self.token = os.getenv('TOKEN')
        self.appkey = os.getenv('APPKEY')
        self.username = os.getenv('USERNAME_API')
        self.password = os.getenv('PASSWORD') 
        self.nat_salario = int(os.getenv('NAT_SALARIO'))
        self.nat_ferias = int(os.getenv('NAT_FERIAS'))
        self.tiptit = int(os.getenv('TIPTIT'))
        self.top = int(os.getenv('TOP'))

    async def logar(self) -> dict:
        """Realiza o login na API da Sankhya e retorna o token de autenticação."""

        auth:dict={}

        # Header da requisição
        header:dict = {
            'token': self.token,
            'appkey': self.appkey,
            'username': self.username,
            'password': self.password
        }

        try:
            res = requests.post(
                url=self.url_login,
                headers=header
            )        
            
            if res.status_code != 200:
                msg = f"Código {res.status_code} ao obter token: {res.text}"
                raise Exception(msg)
            
            if not res.json().get('bearerToken'):
                msg = "Token de acesso não encontrado na resposta"
                raise Exception(msg)

            auth = res.json()

        except Exception as e:
            print(f"ERRO AO FAZER LOGIN NA API --> {e}")

        finally:
            pass

        return auth

    async def busca_conta_bancaria(self,token:str,dados_bancarios:dict) -> dict:
        """Busca o código da conta bancária interna e o código da empresa na Sankhya."""

        codctabcoint:int = 0
        codemp:int = 0
        result:dict={}

        def extrair_codctabcoint_codemp(data:dict):
            if not data['responseBody']['rows']:                
                return 0, 0
            return int(data['responseBody']['rows'][0][0]), int(data['responseBody']['rows'][0][1])

        conta = f"{dados_bancarios.get('conta')}{dados_bancarios.get('dv')}" if dados_bancarios.get('dv') else f"{dados_bancarios.get('conta')}"

        query:str = f'''select codctabcoint, codemp
                        from   tsicta
                        where  ativa = 'S'
                           and codbco = {dados_bancarios.get('codigo_banco')}
                           and codage = {dados_bancarios.get('agencia')}
                           and codctabco = '{conta}' '''

        # Header da requisição
        header:dict = {        
            'content-type': 'application/json',
            'Authorization': f"Bearer {token}"
        }

        body:dict = {
            "serviceName": "DbExplorerSP.executeQuery",
            "requestBody": {
                "sql":query
            }
        }

        try:
            res = requests.get(
                url=self.url_busca,
                headers=header,
                json=body)        
            
            if res.status_code != 200:
                msg = f"Código {res.status_code} ao buscar parceiro: {res.text}"
                raise Exception(msg)

            codctabcoint, codemp = extrair_codctabcoint_codemp(res.json())

        except Exception as e:
            print(f"ERRO AO BUSCAR CONTA BANCÁRIA --> {e}")

        finally:
            result['codctabcoint']=codctabcoint
            result['codemp']=codemp

        return result

    async def busca_parceiro(self,token:str,texto:str) -> int:
        """Busca o código Sankhya do parceiro com base no nome fornecido."""

        codparc:int = 0

        def extrair_codparc(data:dict):
            if not data['responseBody']['rows']:                
                return 0
            return int(data['responseBody']['rows'][0][0])

        query:str = f"select codparc from tgfpar where ativo = 'S' and upper(translate(nomeparc,'ÁÀÂÃÄáàâãäÉÈÊËéèêëÍÌÎÏíìîïÓÒÔÕÖóòôõöÚÙÛÜúùûüÇçÑñ','AAAAAaaaaaEEEEeeeeIIIIiiiiOOOOOoooooUUUUuuuuCcNn')) like upper('{texto}%')"

        # Header da requisição
        header:dict = {        
            'content-type': 'application/json',
            'Authorization': f"Bearer {token}"
        }

        body:dict = {
            "serviceName": "DbExplorerSP.executeQuery",
            "requestBody": {
                "sql":query
            }
        }

        try:
            res = requests.get(
                url=self.url_busca,
                headers=header,
                json=body)        
            
            if res.status_code != 200:
                msg = f"Código {res.status_code} ao buscar parceiro: {res.text}"
                raise Exception(msg)
            
            codparc = extrair_codparc(res.json())

        except Exception as e:
            print(f"ERRO AO BUSCAR PARCEIRO --> {e}")            

        finally:
            pass

        return codparc

    def formata_lancamentos_sankhya(self,dados_bancarios:dict,dados_lancamentos:list[dict],tipo_lcto:str) -> list[dict]:        
        """Formata os lançamentos para o padrão exigido pela Sankhya."""

        retorno:list[dict] = []

        for lcto in dados_lancamentos:

            if lcto.get('Natureza') == 'Férias':
                try:
                    observacao:str = f'PGTO FÉRIAS {lcto.get("Nome")} DE {pd.to_datetime(lcto.get("Inicio ferias")).strftime('%d/%m')} ATÉ {pd.to_datetime(lcto.get("Fim ferias")).strftime('%d/%m')}'
                except:
                    observacao:str = f'PGTO FÉRIAS {lcto.get("Nome")}'
            else:
                observacao:str = f'PGTO SALÁRIO {lcto.get("Referencia")}' if tipo_lcto == 'Salário' else f'ADTO SALÁRIO {lcto.get("Referencia")}'

            registro:dict = {
                "values":{
                    '1' : dados_bancarios.get('Codigo empresa'),
                    '2' : self.top,
                    '3' : self.nat_salario if lcto.get('Natureza') == 'Salário' else self.nat_ferias,
                    '4' : 0,
                    '5' : lcto.get('Codigo parceiro'),
                    '6' : re.search(r'^\d+', dados_bancarios.get('Banco')).group(0),
                    '7' : dados_bancarios.get('Codigo conta'),
                    '8' : self.tiptit,
                    '9' : int(lcto.get('Referencia').replace('/','')),
                    '10': '01/'+lcto.get('Referencia'),
                    '11': lcto.get('Data pagamento'),
                    '12': 0,
                    '13': lcto.get('Valor pagamento'),
                    '14': observacao,
                    '15': -1
                }
            }
            retorno.append(registro)
        
        return retorno

    async def registrar_despesas(self,token:str,lancamentos:list[dict]) -> int:
        """Registra os lançamentos de despesas na Sankhya e retorna o número de registros realizados."""
        CAMPOS = [
                    'NUFIN',
                    'CODEMP',
                    'CODTIPOPER',
                    'CODNAT',
                    'CODCENCUS',
                    'CODPARC',
                    'CODBCO',
                    'CODCTABCOINT',
                    'CODTIPTIT',
                    'NUMNOTA',
                    'DTNEG',
                    'DTVENC',
                    'DESDOBRAMENTO',
                    'VLRDESDOB',
                    'HISTORICO',
                    'RECDESP'
                ]

        registros_realizados:int=0

        # Header da requisição
        header:dict = {        
            'content-type': 'application/json',
            'Authorization': f"Bearer {token}"
        }

        body:dict = {
            "serviceName":"DatasetSP.save",
            "requestBody":{
                "entityName":"Financeiro",
                "standAlone":False,
                "fields":CAMPOS,
                "records":lancamentos
            }
        }

        try:
            res = requests.post(
                url=self.url_registro,
                headers=header,
                json=body)        
            
            if res.status_code != 200:
                msg = f"Código {res.status_code} ao lançar despesa: {res.text}"
                raise Exception(msg)

            if res.json()['status'] != '1':
                msg = f"Falha ao lançar despesas.\n{res.json()}"
                raise Exception(msg)            
            
            registros_realizados = int(res.json()['responseBody'].get('total'))

        except Exception as e:
            print(f"ERRO --> {e}")

        finally:
            pass

        return registros_realizados    