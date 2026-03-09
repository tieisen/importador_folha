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
        self.nat_vr = int(os.getenv('NAT_VR'))
        self.tiptit_folha = int(os.getenv('TIPTIT_FOLHA'))
        self.tiptit_vr = int(os.getenv('TIPTIT_VR'))
        self.top = int(os.getenv('TOP'))
        self.conta_bancaria_rs = int(os.getenv('CONTA_BANCARIA_RS'))
        self.conta_bancaria_sc = int(os.getenv('CONTA_BANCARIA_SC'))
        self.conta_bancaria_pr = int(os.getenv('CONTA_BANCARIA_PR'))

    async def logar(self) -> dict:
        """
            Realiza o login na API da Sankhya e retorna o token de autenticação.
                :return dict: Dicionário contendo o token de autenticação.
        """

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

    def buscar_script(self) -> str:
        """
        Busca script SQL para buscar dados bancários.
            :return str: script SQL
        """
        script:str=''
        try:
            path:str = os.getenv('PATH_SCRIPT_DADOS_BANCARIOS')
            if not path:
                erro = f"Parâmetro do diretório do script não informado. param: {path}"
                raise ValueError(erro)
        
            try:
                with open(path, "r") as file:
                    script = " ".join(line.strip() for line in file)
            except Exception as e:
                erro = f"Falha ao abrir arquivo do script em {path}. {e}"
                raise FileNotFoundError(erro)
        
            if not script.strip():
                erro = f"Arquivo carregado de {path} sem conteúdo"
                raise ValueError(erro)
        except Exception as e:
            print(f"ERRO AO CARREGAR SCRIPT --> {e}")
        finally:
            pass

        return script        

    async def busca_conta_bancaria(
            self,
            token:str,
            codigo_banco:int=None,
            numero_agencia:int=None,
            numero_conta:str=None,            
            cnpj:str=None,
        ) -> dict:
        """
            Busca o código da conta bancária interna e o código da empresa na Sankhya.
                :param token: Token de autenticação da Sankhya.
                :param dados_bancarios: Dicionário contendo os dados do banco.
                :param cnpj: CNPJ da empresa.
                :return dict: Dicionário contendo dados internos do banco, da conta bancária e da empresa.
        """

        conta:str = ''
        banco:str = ''
        empresa:str = ''
        codigo_conta:int = 0
        result:dict={}

        def extrair(data:dict):
            if not data['responseBody']['rows']:                
                return 0, 0, 0
            return data['responseBody']['rows'][0][0], data['responseBody']['rows'][0][1], data['responseBody']['rows'][0][2]

        if not all([codigo_banco,numero_agencia,numero_conta]) and not cnpj:
            return result

        if cnpj:
            match cnpj:
                case '14.008.597/0001-25': # Matriz
                    codigo_conta = self.conta_bancaria_rs
                case '14.008.597/0004-78': # SC
                    codigo_conta = self.conta_bancaria_sc
                case '14.008.597/0003-97': # PR
                    codigo_conta = self.conta_bancaria_pr
                case _:
                    return result
            
        query:str = self.buscar_script()
        if not query:
            return result

        query = query.format(codigo_banco=codigo_banco or 'NULL',
                             numero_agencia=numero_agencia or 'NULL',
                             numero_conta=numero_conta or '',
                             codigo_conta=codigo_conta) 

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
                msg = f"Código {res.status_code} ao buscar dados bancários: {res.text}"
                raise Exception(msg)

            conta, empresa, banco = extrair(res.json())

        except Exception as e:
            print(f"ERRO AO BUSCAR CONTA BANCÁRIA --> {e}")

        finally:
            result['conta']=conta
            result['empresa']=empresa
            result['banco']=banco

        return result

    async def busca_parceiro(
            self,
            token:str,
            nome:str=None,
            cpf:str=None
        ) -> int:
        """
            Busca o código Sankhya do parceiro com base no nome fornecido.
                :param token: Token de autenticação da Sankhya.
                :param nome: Nome do parceiro.
                :param cpf: CPF do parceiro.
                :return int: Código Sankhya do parceiro.        
        """

        if not any([nome,cpf]):
            return 0
        
        codparc:int = 0

        def extrair_codparc(data:dict):
            if not data['responseBody']['rows']:                
                return 0
            return int(data['responseBody']['rows'][0][0])
        
        def remover_simbolos_cpf(cpf:str) -> str:
            return re.sub(r'[^0-9]', '', cpf)

        if nome:
            query:str = f'''select codparc 
                            from tgfpar
                            where ativo = 'S'
                                and upper(translate(nomeparc,'ÁÀÂÃÄáàâãäÉÈÊËéèêëÍÌÎÏíìîïÓÒÔÕÖóòôõöÚÙÛÜúùûüÇçÑñ','AAAAAaaaaaEEEEeeeeIIIIiiiiOOOOOoooooUUUUuuuuCcNn')) like upper('{nome}%')
                        '''
        if cpf:
            cpf = remover_simbolos_cpf(cpf)
            query:str = f'''select codparc
                            from tgfpar
                            where ativo = 'S'
                                and cgc_cpf = '{cpf}'
                        '''

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
    
    async def busca_parceiro_empresa(
            self,
            token:str,
            nome:str=None,
            cpf:str=None
        ) -> tuple[int,int]:
        """
            Busca o código Sankhya do parceiro com base no nome fornecido.
                :param token: Token de autenticação da Sankhya.
                :param nome: Nome do parceiro.
                :param cpf: CPF do parceiro.
                :return int: Código Sankhya do parceiro.
                :return int: Código Sankhya da empresa preferencial do parceiro.
        """
        
        codparc:int = 0
        codemppref:int = 0

        def extrair_codparc_codemppref(data:dict):
            if not data['responseBody']['rows']:                
                return 0
            return int(data['responseBody']['rows'][0][0]), int(data['responseBody']['rows'][0][1])
        
        def remover_simbolos_cpf(cpf:str) -> str:
            return re.sub(r'[^0-9]', '', cpf)

        if all([nome,cpf]):
            cpf = remover_simbolos_cpf(cpf)
            query:str = f"select max(codparc) as codparc, codemppref from tgfpar where ativo = 'S' and (cgc_cpf = '{cpf}' or upper(translate(nomeparc,'ÁÀÂÃÄáàâãäÉÈÊËéèêëÍÌÎÏíìîïÓÒÔÕÖóòôõöÚÙÛÜúùûüÇçÑñ','AAAAAaaaaaEEEEeeeeIIIIiiiiOOOOOoooooUUUUuuuuCcNn')) like upper('{nome}%')) group by codemppref"
        elif nome:
            query:str = f"select codparc, codemppref from tgfpar where ativo = 'S' and upper(translate(nomeparc,'ÁÀÂÃÄáàâãäÉÈÊËéèêëÍÌÎÏíìîïÓÒÔÕÖóòôõöÚÙÛÜúùûüÇçÑñ','AAAAAaaaaaEEEEeeeeIIIIiiiiOOOOOoooooUUUUuuuuCcNn')) like upper('{nome}%')"
        elif cpf:
            cpf = remover_simbolos_cpf(cpf)
            query:str = f"select codparc, codemppref from tgfpar where ativo = 'S' and cgc_cpf = '{cpf}'"
        else:
            return 0, 0

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
            
            codparc, codemppref = extrair_codparc_codemppref(res.json())

        except Exception as e:
            print(f"ERRO AO BUSCAR PARCEIRO --> {e}")            

        finally:
            pass

        return codparc, codemppref

    def formata_lancamentos_sankhya(
            self,
            dados_bancarios:dict,
            dados_lancamentos:list[dict],
            tipo_lcto:str
        ) -> list[dict]:        
        """
            Formata os lançamentos para o padrão exigido pela Sankhya.
                :param dados_bancarios: Dicionário contendo os dados do banco.
                :param dados_lancamentos: Lista de dicionários contendo os dados dos lançamentos.
                :param tipo_lcto: Tipo de lançamento.
                :return list[dict]: Lista de dicionários contendo os dados dos lançamentos formatados.
        """

        retorno:list[dict] = []

        if tipo_lcto == 'vr':
            for lcto in dados_lancamentos:
                registro:dict = {
                    "values":{
                        '1' : int(re.search(r'^\d+', dados_bancarios.get('Empresa')).group(0)),
                        '2' : self.top,
                        '3' : self.nat_vr,
                        '4' : 0,
                        '5' : lcto.get('Codigo parceiro'),
                        '6' : int(re.search(r'^\d+', dados_bancarios.get('Banco')).group(0)),
                        '7' : int(re.search(r'^\d+', dados_bancarios.get('Conta')).group(0)),
                        '8' : self.tiptit_vr,
                        '9' : int(str(dados_bancarios.get('Pedido'))[-6:]),
                        '10': dados_bancarios.get('Data do crédito'),
                        '11': pd.to_datetime(str(dados_bancarios.get('Pedido'))[:8],format='%Y%m%d').strftime("%d/%m/%Y"),
                        '12': 0,
                        '13': lcto.get('Valor do benefício'),
                        '14': lcto.get('Referencia'),
                        '15': -1
                    }
                }
                retorno.append(registro)

        else:
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
                        '1' : int(re.search(r'^\d+', dados_bancarios.get('Empresa')).group(0)),
                        '2' : self.top,
                        '3' : self.nat_salario if lcto.get('Natureza') == 'Salário' else self.nat_ferias,
                        '4' : 0,
                        '5' : lcto.get('Codigo parceiro'),
                        '6' : int(re.search(r'^\d+', dados_bancarios.get('Banco')).group(0)),
                        '7' : int(re.search(r'^\d+', dados_bancarios.get('Conta')).group(0)),
                        '8' : self.tiptit_folha,
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
        """
            Registra os lançamentos de despesas na Sankhya e retorna o número de registros realizados.
                :param token: Token de autenticação da Sankhya.
                :param lancamentos: Lista de dicionários contendo os dados dos lançamentos.
                :return int: Número de registros realizados.
        """
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