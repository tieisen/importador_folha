class Cnab240:

    def __init__(self):
        pass

    def ler_arquivo(self, arquivo) -> list[str]:
        """
            Lê o conteúdo do arquivo enviado pelo usuário e retorna uma lista de linhas.
                :param arquivo: Arquivo enviado pelo usuário.
                :return: Lista de linhas do arquivo.
        """

        conteudo = arquivo.read().decode("utf-8")
        return conteudo.split('\n')

    def padroniza_campos(self,conteudo:dict) -> dict:
        """
            Padroniza o nome dos campos de CNAB240 de bancos diferentes.
                :param conteudo: Conteúdo do arquivo.
                :return dict: Dicionário contendo headers, detalhes e trailers do arquivo CNAB.
        """

        header_arquivo:dict = conteudo.get('header_arquivo', {})
        header_lote:dict = conteudo.get('header_lote', [{}])[0]
        detalhes:list = conteudo.get('detalhes', [])
        trailer_lote:dict = conteudo.get('trailer_lote', [{}])[0]
        trailer_arquivo:dict = conteudo.get('trailer_arquivo', {})

        header_arquivo_padronizado:dict = {}
        header_lote_padronizado:list[dict] = []
        detalhes_padronizado:list[dict] = []
        trailer_lote_padronizado:list[dict] = []
        trailer_arquivo_padronizado:dict = {}
        retorno:dict = {}

        try:
            header_arquivo_padronizado = {
                'codigo_banco': int(header_arquivo.get('codigo_banco', 0)),
                'codigo_lote':  int(header_arquivo.get('codigo_lote', 0)),
                'tipo_registro': int(header_arquivo.get('tipo_registro', 0)),
                'tipo_inscricao': int(header_arquivo.get('tipo_inscricao', header_arquivo.get('codigo_inscricao', 0))),
                'numero_inscricao': int(header_arquivo.get('numero_inscricao', 0)),
                'convenio': None if header_arquivo.get('convenio') == '' else int(header_arquivo.get('convenio')),
                'agencia': int(header_arquivo.get('agencia', 0)),
                'conta': int(header_arquivo.get('conta', 0)),
                'dv': None if header_arquivo.get('dv', header_arquivo.get('dac', '')) == '' else int(header_arquivo.get('dac', 0)),
                'nome': header_arquivo.get('nome', ''),
                'banco': header_arquivo.get('banco', ''),
                'codigo': int(header_arquivo.get('codigo', 0)),
                'data_geracao': header_arquivo.get('data_geracao', ''),
                'hora_geracao': header_arquivo.get('hora_geracao', ''),
                'sequencia': int(header_arquivo.get('sequencia', 0)),
                'layout': int(header_arquivo.get('layout', 0)),
                'densidade': int(header_arquivo.get('densidade', header_arquivo.get('unidade_densidade', 0))),
                'reservado_banco': header_arquivo.get('reservado_banco', ''),
                'reservado_empresa': header_arquivo.get('reservado_empresa', '')
            }
        except Exception as e:
            print(f"Erro na padronização do header do arquivo: {e}")
        finally:
            pass

        try:
            header_lote_padronizado = [{
                'codigo_banco': int(header_lote.get('codigo_banco', 0)),
                'codigo_lote':  int(header_lote.get('codigo_lote', 0)),
                'tipo_registro': int(header_lote.get('tipo_registro', 0)),
                'tipo_operacao': header_lote.get('tipo_operacao', ''),
                'tipo_servico': int(header_lote.get('tipo_servico', header_lote.get('servico', 0))),
                'forma_lancamento': int(header_lote.get('forma_lancamento', 0)),
                'layout': int(header_lote.get('layout', 0)),
                'numero_inscricao': int(header_lote.get('numero_inscricao', 0)),
                'convenio': None if header_lote.get('convenio') == '' else int(header_lote.get('convenio')),
                'agencia': int(header_lote.get('agencia', 0)),
                'conta': int(header_lote.get('conta', 0)),
                'dv': None if header_lote.get('dv', header_lote.get('dac', '')) == '' else int(header_lote.get('dac', 0)),
                'nome_empresa': header_lote.get('nome_empresa', ''),
                'endereco': header_lote.get('endereco', ''),
                'numero': int(header_lote.get('numero', 0)),
                'complemento': header_lote.get('complemento', ''),
                'cidade': header_lote.get('cidade', ''),
                'cep': int(header_lote.get('cep', 0)),
                'estado': header_lote.get('estado', ''),
                'ocorrencias': header_lote.get('ocorrencias', '')
            }]
        except Exception as e:
            print(f"Erro na padronização do header do lote: {e}")
        finally:
            pass

        try:
            aux:dict = {}
            for d in detalhes:
                if not d:
                    continue
                aux = {
                    'codigo_banco': int(d.get('codigo_banco', 0)),
                    'codigo_lote':  int(d.get('codigo_lote', 0)),
                    'tipo_registro': int(d.get('tipo_registro', 0)),
                    'numero_registro': int(d.get('numero_registro', 0)),
                    'segmento': d.get('segmento', ''),
                    'tipo_movimento': None if d.get('tipo_movimento','') == '' else int(d.get('tipo_movimento')),
                    'codigo_movimento': None if d.get('codigo_movimento','') == '' else int(d.get('codigo_movimento')),
                    'codigo_camara': None if d.get('codigo_camara','') == '' else int(d.get('codigo_camara')),
                    'codigo_instrucao': None if d.get('codigo_instrucao','') == '' else int(d.get('codigo_instrucao')),
                    'compensacao': None if d.get('compensacao','') == '' else int(d.get('compensacao')),
                    'banco': int(d.get('banco', 0)),
                    'agencia': int(d.get('agencia', 0)),
                    'conta': int(d.get('conta', 0)),
                    'dv': None if d.get('dv', d.get('dac', '')) == '' else int(d.get('dac', 0)),
                    'nome': d.get('nome', ''),
                    'seu_numero': d.get('seu_numero', ''),
                    'data_pagamento': d.get('data_pagamento', d.get('data_agendada', '')),
                    'tipo_moeda': d.get('tipo_moeda', ''),
                    'quantidade_moeda': int(d.get('quantidade_moeda', 0)),
                    'valor_pagamento': float(d.get('valor_pagamento', d.get('valor_agendado', 0))),
                    'nosso_numero': d.get('nosso_numero', ''),
                    'data_real': d.get('data_real', d.get('data_cobrada', '')),
                    'valor_real': float(d.get('valor_real', d.get('valor_cobrado', 0))),
                    'tipo_mora': d.get('tipo_mora', ''),
                    'valor_mora': float(d.get('valor_mora', 0)),
                    'codigo_finalidade_doc': None if d.get('codigo_finalidade_doc','') == '' else int(d.get('codigo_finalidade_doc')),
                    'codigo_finalidade_ted': None if d.get('codigo_finalidade_ted','') == '' else int(d.get('codigo_finalidade_ted')),
                    'aviso': None if d.get('aviso','') == '' else int(d.get('aviso')),
                    'complemento': d.get('complemento', ''),
                    'inscricao_debitado': d.get('inscricao_debitado', ''),
                    'ocorrencias': d.get('ocorrencias', '')
                }
                detalhes_padronizado.append(aux)
        except Exception as e:
            print(f"Erro na padronização dos detalhes: {e}")
            print(d)
        finally:
            pass

        try:
            trailer_lote_padronizado = [{
                'codigo_banco': int(trailer_lote.get('codigo_banco', 0)),
                'codigo_lote':  int(trailer_lote.get('codigo_lote', 0)),
                'tipo_registro': int(trailer_lote.get('tipo_registro', 0)),
                'qtde_registros': int(trailer_lote.get('qtde_registros',0)),
                'valor_total': float(trailer_lote.get('valor_total', trailer_lote.get('valor_total_debitos', 0))),
                'qtde_moedas': int(trailer_lote.get('qtde_moedas', 0)),
                'numero_aviso_debito': int(trailer_lote.get('numero_aviso_debito', 0)),
                'ocorrencias': trailer_lote.get('ocorrencias', '')
            }]
        except Exception as e:
            print(f"Erro na padronização do trailer do lote: {e}")
        finally:
            pass

        try:
            trailer_arquivo_padronizado = {
                'codigo_banco': int(trailer_arquivo.get('codigo_banco', 0)),
                'codigo_lote':  int(trailer_arquivo.get('codigo_lote', 0)),
                'tipo_registro': int(trailer_arquivo.get('tipo_registro', 0)),
                'qtde_lotes': int(trailer_arquivo.get('qtde_lotes', 0)),
                'qtde_registros': int(trailer_arquivo.get('qtde_registros', 0)),
                'qtd_contas_conciliar': None if trailer_arquivo.get('qtd_contas_conciliar', '') == '' else int(trailer_arquivo.get('qtd_contas_conciliar'))
            }
        except Exception as e:
            print(f"Erro na padronização do trailer do arquivo: {e}")
        finally:
            pass

        retorno['header_arquivo'] = header_arquivo_padronizado
        retorno['header_lote'] = header_lote_padronizado
        retorno['detalhes'] = detalhes_padronizado
        retorno['trailer_lote'] = trailer_lote_padronizado
        retorno['trailer_arquivo'] = trailer_arquivo_padronizado

        return retorno

    def extrai_conteudo(self, conteudo:list[str]) -> dict:
        """
            Extrai o conteúdo do arquivo CNAB240 utilizando o parser adequado conforme o banco identificado.
                :param conteudo: Lista com o conteúdo do arquivo.
                :return dict: Dicionário com o conteúdo do arquivo padronizado.
        """

        extracao:dict={}

        if conteudo[0][0:3] == '237':
            extracao = self.bradesco(conteudo=conteudo)
        elif conteudo[0][0:3] == '341':
            extracao = self.itau(conteudo=conteudo)
        else:
            extracao = {}

        extracao = self.padroniza_campos(extracao)

        return extracao

    def itau(self,caminho_arquivo:str=None,conteudo:list=None) -> dict:
        """
            Lê um arquivo CNAB240 Itaú e retorna dicionário com todos os registros.
                :param caminho_arquivo: Caminho do arquivo CNAB240.
                :param conteudo: Conteúdo do arquivo CNAB240.
                :return dict: Dicionário com todos os registros.
        """

        if not any([caminho_arquivo,conteudo]):
            return {}

        registros = {
            'header_arquivo': None,
            'header_lote': [],
            'detalhes': [],
            'trailer_lote': [],
            'trailer_arquivo': None
        }

        def header_arquivo(linha:str):
            from datetime import datetime
            formatado:dict={}
            try:
                formatado['codigo_banco'] = linha[0:3]
                formatado['codigo_lote']  = linha[3:7]
                formatado['tipo_registro'] = linha[7:8]
                formatado['codigo_inscricao'] = linha[17:18]
                formatado['numero_inscricao'] = linha[18:32]
                formatado['convenio'] = linha[32:45]
                formatado['agencia'] = linha[53:57]
                formatado['conta'] = linha[65:70]
                formatado['dac'] = linha[71:72]
                formatado['nome'] = linha[72:102]
                formatado['banco'] = linha[102:132]
                formatado['codigo'] = linha[142:143]
                try:
                    formatado['data_geracao'] = datetime.strptime(linha[143:151], '%d%m%Y').strftime('%d/%m/%Y')
                except:
                    formatado['data_geracao'] = ''        
                try:
                    formatado['hora_geracao'] = datetime.strptime(linha[151:157], '%H%M%S').strftime('%H:%M:%S')
                except:
                    formatado['hora_geracao'] = ''        
                formatado['sequencia'] = linha[157:163]
                formatado['layout'] = linha[163:166]
                formatado['unidade_densidade'] = linha[166:171]
                formatado['reservado_banco'] = linha[171:191]
                for key, value in formatado.items():
                    formatado[key] = str.strip(value)            
            except Exception as e:
                print(f"Erro HEADER ARQUIVO: {e}")
            finally:
                pass
            return formatado

        def header_lote(linha:str):
            formatado = {}
            try:
                formatado['codigo_banco'] = linha[0:3]
                formatado['codigo_lote'] = linha[3:7]
                formatado['tipo_registro'] = linha[7:8]
                formatado['tipo_operacao'] = linha[8:9]
                formatado['servico'] = linha[9:11]
                formatado['forma_lancamento'] = linha[11:13]
                formatado['layout'] = linha[13:16]
                formatado['tipo_inscricao'] = linha[17:18]
                formatado['numero_inscricao'] = linha[18:32]
                formatado['convenio'] = linha[32:45]
                formatado['agencia'] = linha[53:57]
                formatado['conta'] = linha[65:70]
                formatado['dac'] = linha[71:72]
                formatado['nome_empresa'] = linha[72:102]
                formatado['endereco'] = linha[142:172]
                formatado['numero'] = linha[172:177]
                formatado['complemento'] = linha[177:192]
                formatado['cidade'] = linha[192:212]
                formatado['cep'] = linha[212:220]
                formatado['estado'] = linha[220:222]
                formatado['ocorrencias'] = linha[230:240]
                for k, v in formatado.items():
                    formatado[k] = v.strip()
            except Exception as e:
                print(f"Erro HEADER LOTE: {e}")
            finally:
                pass        
            return formatado

        def detalhe(linha:str):
            from datetime import datetime
            formatado = {}
            try:
                formatado['codigo_banco'] = linha[0:3]
                formatado['codigo_lote'] = linha[3:7]
                formatado['tipo_registro'] = linha[7:8]
                formatado['numero_registro'] = linha[8:13]
                formatado['segmento'] = linha[13:14]
                formatado['codigo_instrucao'] = linha[14:17]
                formatado['compensacao'] = linha[17:20]
                formatado['banco'] = linha[20:23]
                formatado['agencia'] = linha[24:28]
                formatado['conta'] = linha[36:41]
                formatado['dac'] = linha[42:43]
                formatado['nome'] = linha[43:73]
                formatado['seu_numero'] = linha[73:88]
                try:
                    formatado['data_agendada'] = datetime.strptime(linha[93:101], '%d%m%Y').strftime('%d/%m/%Y')
                except:
                    formatado['data_agendada'] = ''
                formatado['tipo_moeda'] = linha[101:104]
                formatado['quantidade_moeda'] = linha[104:119]
                formatado['valor_agendado'] = float(int(linha[119:134]) / 100)
                formatado['nosso_numero'] = linha[134:154]
                try:
                    formatado['data_cobrada'] = datetime.strptime(linha[154:162], '%d%m%Y').strftime('%d/%m/%Y')
                except:
                    formatado['data_cobrada'] = ''
                formatado['valor_cobrado'] = float(int(linha[162:177]) / 100)
                formatado['tipo_mora'] = linha[177:179]
                formatado['valor_mora'] = linha[179:196]
                formatado['complemento'] = linha[196:212]
                formatado['inscricao_debitado'] = linha[216:230]
                formatado['ocorrencias'] = linha[230:240]
                for k, v in formatado.items():
                    if isinstance(v,float) or isinstance(v,int):
                        continue
                    formatado[k] = v.strip()
            except Exception as e:
                print(f"Erro DETALHE: {e}")
            finally:
                pass        
            return formatado

        def trailer_lote(linha:str):
            formatado = {}
            try:
                formatado['codigo_banco'] = linha[0:3]
                formatado['codigo_lote'] = linha[3:7]
                formatado['tipo_registro'] = linha[7:8]
                formatado['qtde_registros'] = int(linha[17:23])
                formatado['valor_total_debitos'] = float(int(linha[23:41]) / 100)
                formatado['qtde_moedas'] = linha[41:59]
                formatado['ocorrencias'] = linha[230:240]
                for k, v in formatado.items():
                    if isinstance(v,float) or isinstance(v,int):
                        continue            
                    formatado[k] = v.strip()
            except Exception as e:
                print(f"Erro TRAILER LOTE: {e}")
            finally:
                pass        
            return formatado

        def trailer_arquivo(linha:str):
            formatado = {}
            try:
                formatado['codigo_banco'] = linha[0:3]
                formatado['codigo_lote'] = linha[3:7]
                formatado['tipo_registro'] = linha[7:8]
                formatado['qtde_lotes'] = int(linha[17:23])
                formatado['qtde_registros'] = int(linha[23:29])
                for k, v in formatado.items():
                    if isinstance(v,float) or isinstance(v,int):
                        continue
                    formatado[k] = v.strip()
            except Exception as e:
                print(f"Erro TRAILER ARQUIVO: {e}")
            finally:
                pass        
            return formatado

        if caminho_arquivo:
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                for linha in f:
                    if linha == '':
                        continue                    
                    tipo = linha[7]
                    if tipo == '0':
                        registros['header_arquivo'] = header_arquivo(linha)
                    elif tipo == '1':
                        registros['header_lote'].append(header_lote(linha))
                    elif tipo == '3':
                        registros['detalhes'].append(detalhe(linha))
                    elif tipo == '5':
                        registros['trailer_lote'].append(trailer_lote(linha))
                    elif tipo == '9':
                        registros['trailer_arquivo'] = trailer_arquivo(linha)

        if conteudo:
            for linha in conteudo:
                if linha == '':
                    continue
                tipo = linha[7]
                if tipo == '0':
                    registros['header_arquivo'] = header_arquivo(linha)
                elif tipo == '1':
                    registros['header_lote'].append(header_lote(linha))
                elif tipo == '3':
                    registros['detalhes'].append(detalhe(linha))
                elif tipo == '5':
                    registros['trailer_lote'].append(trailer_lote(linha))
                elif tipo == '9':
                    registros['trailer_arquivo'] = trailer_arquivo(linha)

        return registros

    def bradesco(self,caminho_arquivo:str=None,conteudo:list=None) -> dict:
        """
            Lê um arquivo CNAB240 Bradesco e retorna dicionário com todos os registros.
                :param caminho_arquivo: Caminho do arquivo CNAB240.
                :param conteudo: Conteúdo do arquivo CNAB240.
                :return dict: Dicionário com todos os registros.
        """

        if not any([caminho_arquivo,conteudo]):
            return {}

        registros = {
            'header_arquivo': None,
            'header_lote': [],
            'detalhes': [],
            'trailer_lote': [],
            'trailer_arquivo': None
        }

        def header_arquivo(linha:str):
            from datetime import datetime    
            formatado:dict={}
            try:
                formatado['codigo_banco'] = linha[0:3]
                formatado['codigo_lote']  = linha[3:7]
                formatado['tipo_registro'] = linha[7:8]
                formatado['tipo_inscricao'] = linha[17:18]
                formatado['numero_inscricao'] = linha[18:32]
                formatado['convenio'] = linha[32:52]                
                formatado['agencia'] = linha[53:58]
                formatado['conta'] = linha[58:71]
                formatado['dv'] = linha[71:72]
                formatado['nome'] = linha[72:102]
                formatado['banco'] = linha[102:132]
                formatado['codigo'] = linha[142:143]
                try:
                    formatado['data_geracao'] = datetime.strptime(linha[143:151], '%d%m%Y').strftime('%d/%m/%Y')
                except:
                    formatado['data_geracao'] = ''        
                try:
                    formatado['hora_geracao'] = datetime.strptime(linha[151:157], '%H%M%S').strftime('%H:%M:%S')
                except:
                    formatado['hora_geracao'] = ''        
                formatado['sequencia'] = linha[157:163]
                formatado['layout'] = linha[163:166]
                formatado['densidade'] = linha[166:171]
                formatado['reservado_banco'] = linha[171:191]
                formatado['reservado_empresa'] = linha[191:211]
                for key, value in formatado.items():
                    formatado[key] = str.strip(value)            
            except Exception as e:
                print(f"Erro HEADER ARQUIVO: {e}")
            finally:
                pass
            return formatado

        def header_lote(linha:str):
            formatado = {}
            try:
                formatado['codigo_banco'] = linha[0:3]
                formatado['codigo_lote'] = linha[3:7]
                formatado['tipo_registro'] = linha[7:8]
                formatado['tipo_operacao'] = linha[8:9]
                formatado['tipo_servico'] = linha[9:11]
                formatado['forma_lancamento'] = linha[11:13]
                formatado['layout'] = linha[13:16]
                formatado['tipo_inscricao'] = linha[17:18]
                formatado['numero_inscricao'] = linha[18:32]
                formatado['convenio'] = linha[32:52]
                formatado['agencia'] = linha[52:58]
                formatado['conta'] = linha[58:71]
                formatado['dv'] = linha[71:72]
                formatado['nome_empresa'] = linha[72:102]
                formatado['informacao'] = linha[102:142]
                formatado['endereco'] = linha[142:172]
                formatado['numero'] = linha[172:177]
                formatado['complemento'] = linha[177:192]
                formatado['cidade'] = linha[192:212]
                formatado['cep'] = linha[212:220]
                formatado['estado'] = linha[220:222]
                formatado['ocorrencias'] = linha[230:240]
                for k, v in formatado.items():
                    formatado[k] = v.strip()
            except Exception as e:
                print(f"Erro HEADER LOTE: {e}")
            finally:
                pass        
            return formatado

        def detalhe(linha:str):
            from datetime import datetime
            formatado = {}
            try:
                formatado['codigo_banco'] = linha[0:3]
                formatado['codigo_lote'] = linha[3:7]
                formatado['tipo_registro'] = linha[7:8]
                formatado['numero_registro'] = linha[8:13]
                formatado['segmento'] = linha[13:14]
                formatado['tipo_movimento'] = linha[14:15]
                formatado['codigo_movimento'] = linha[15:17]
                formatado['codigo_camara'] = linha[17:20]
                formatado['banco'] = linha[20:23]
                formatado['agencia'] = linha[23:29]
                formatado['conta'] = linha[29:42]
                formatado['dv'] = linha[42:43]
                formatado['nome'] = linha[43:73]
                formatado['seu_numero'] = linha[73:93]
                try:
                    formatado['data_pagamento'] = datetime.strptime(linha[93:101], '%d%m%Y').strftime('%d/%m/%Y')
                except:
                    formatado['data_pagamento'] = ''
                formatado['tipo_moeda'] = linha[101:104]
                formatado['quantidade_moeda'] = linha[104:119]
                formatado['valor_pagamento'] = float(int(linha[119:134]) / 100)
                formatado['nosso_numero'] = linha[134:154]
                try:
                    formatado['data_real'] = datetime.strptime(linha[154:162], '%d%m%Y').strftime('%d/%m/%Y')
                except:
                    formatado['data_real'] = ''
                formatado['valor_real'] = float(int(linha[162:177]) / 100)
                formatado['informacao'] = linha[177:217]
                formatado['codigo_finalidade_doc'] = linha[217:219]
                formatado['codigo_finalidade_ted'] = linha[219:224]
                formatado['cnab'] = linha[224:229]
                formatado['aviso'] = linha[229:230]            
                formatado['ocorrencias'] = linha[230:240]
                for k, v in formatado.items():
                    if isinstance(v,float) or isinstance(v,int):
                        continue
                    formatado[k] = v.strip()
            except Exception as e:
                print(f"Erro DETALHE: {e}")
            finally:
                pass        
            return formatado

        def trailer_lote(linha:str):
            formatado = {}
            try:
                formatado['codigo_banco'] = linha[0:3]
                formatado['codigo_lote'] = linha[3:7]
                formatado['tipo_registro'] = linha[7:8]
                formatado['qtde_registros'] = int(linha[17:23])
                formatado['valor_total'] = float(int(linha[23:41]) / 100)
                formatado['qtde_moedas'] = linha[41:59]
                formatado['numero_aviso_debito'] = linha[59:65]
                formatado['ocorrencias'] = linha[230:240]
                for k, v in formatado.items():
                    if isinstance(v,float) or isinstance(v,int):
                        continue            
                    formatado[k] = v.strip()
            except Exception as e:
                print(f"Erro TRAILER LOTE: {e}")
            finally:
                pass        
            return formatado

        def trailer_arquivo(linha:str):
            formatado = {}
            try:
                formatado['codigo_banco'] = linha[0:3]
                formatado['codigo_lote'] = linha[3:7]
                formatado['tipo_registro'] = linha[7:8]
                formatado['qtde_lotes'] = int(linha[17:23])
                formatado['qtde_registros'] = int(linha[23:29])
                formatado['qtd_contas_conciliar'] = linha[29:35]
                for k, v in formatado.items():
                    if isinstance(v,float) or isinstance(v,int):
                        continue
                    formatado[k] = v.strip()
            except Exception as e:
                print(f"Erro TRAILER ARQUIVO: {e}")
            finally:
                pass        
            return formatado

        if caminho_arquivo:
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                for linha in f:
                    if linha == '':
                        continue                    
                    tipo = linha[7]
                    if tipo == '0':
                        registros['header_arquivo'] = header_arquivo(linha)
                    elif tipo == '1':
                        registros['header_lote'].append(header_lote(linha))
                    elif tipo == '3':
                        if linha[13:14] != 'A':
                            continue
                        registros['detalhes'].append(detalhe(linha))
                    elif tipo == '5':
                        registros['trailer_lote'].append(trailer_lote(linha))
                    elif tipo == '9':
                        registros['trailer_arquivo'] = trailer_arquivo(linha) 

        if conteudo:
            for linha in conteudo:
                if linha == '':
                    continue
                tipo = linha[7]
                if tipo == '0':
                    registros['header_arquivo'] = header_arquivo(linha)
                elif tipo == '1':
                    registros['header_lote'].append(header_lote(linha))
                elif tipo == '3':
                    if linha[13:14] != 'A':
                        continue
                    registros['detalhes'].append(detalhe(linha))
                elif tipo == '5':
                    registros['trailer_lote'].append(trailer_lote(linha))
                elif tipo == '9':
                    registros['trailer_arquivo'] = trailer_arquivo(linha)                 

        return registros
