import re, unicodedata, json, os
import pandas as pd
from datetime import datetime
from typing import Literal
from schema.Itau240 import HeaderArquivo, TrailerArquivo, HeaderLoteO, TrailerLoteO, DetalheO

DIR_REMESSAS = "remessas"

class Arquivo:
    def __init__(self):
        self.data:pd.DataFrame = None
        self.dados_bancarios:dict = None

    def normalizarColunas(self,texto: str) -> str:
        if not texto:
            return texto
        
        texto = unicodedata.normalize('NFKD', texto)
        texto = ''.join(c for c in texto if not unicodedata.combining(c))
        texto = texto.replace(" ","_").replace("/","_")
        texto = re.sub(r'[^a-zA-Z0-9\s_]', '', texto)
        texto = re.sub(r'\s+', ' ', texto).strip()    
        return texto.lower()

    def carregarArquivo(self,filePath:str,fileType:str=None) -> pd.DataFrame:

        REGEX_FILE_EXTENSION = r'\w+$'
        match:re.Match = None
        df:pd.DataFrame = None
        data:pd.DataFrame = None
        cols:list = None

        # with open(filePath,"rb") as f:    
        # match = re.search(REGEX_FILE_EXTENSION, f.name)
        if not fileType:
            match = re.search(REGEX_FILE_EXTENSION, filePath)
            if not match:
                raise ValueError(f"Não foi possível extrair a extensão do arquivo: {f.name}")
            fileType = match.group(0)
            
        if fileType not in ["csv","xls", "xlsx","text/csv"]:
            raise ValueError(f"Extensão de arquivo não suportada: {fileType}")
        
        if fileType in ["xls"]:
            df = pd.read_excel(filePath,engine='xlrd')
        
        if fileType in ["xlsx"]:
            df = pd.read_excel(filePath,engine='openpyxl')
        
        if fileType in ["csv","text/csv"]:
            df = pd.read_csv(filePath,encoding="utf-8")

        cols = [self.normalizarColunas(c) for c in df.columns]
        df.columns = cols

        data = df[['fornecedor','chave_pix_codigo_boleto','numero_documento','data_vencimento','valor_documento','historico']].copy()
        if data['valor_documento'].dtype == "object":
            data['valor_documento'] = data['valor_documento'].apply(lambda x: x.replace(",","."))
            data['valor_documento'] = data['valor_documento'].astype(float)
        
        self.data = data
        return data

    def validaDadosBancariosEmpresa(self, empresa:Literal['storya', 'outbeauty','compre']) -> dict:
        
        if empresa not in ['storya', 'outbeauty','compre']:
            raise ValueError("Empresa inválida. Escolha entre 'storya', 'outbeauty' ou 'compre'.")
        
        dados_bancarios:list[dict] = []
        with open("json/.dados_empresas.json","r") as f:
            dados_bancarios = json.load(f)
        
        if not dados_bancarios:
            raise ValueError("Arquivo de dados bancários não encontrado.")
        
        for d in dados_bancarios:
            if d.get('empresa') == empresa:
                self.dados_bancarios = d.get('dados')
                return d.get('dados')
        raise ValueError(f"Dados bancários para a empresa {empresa} não encontrados.")    
    
class Layout(Arquivo):
    
    def __init__(self):
        super().__init__()
        self.headerArquivo:str = None
        self.trailerArquivo:str = None
        self.headerLote:str = None
        self.trailerLote:str = None
        self.detalhes:list[str] = []
        self.conteudo:str = None
        self.nomeArquivo:str = None
        self.caminhoArquivo:str = None
        
    def __str__(self) -> str:
        return self.conteudo if self.conteudo else ""

    def comporHeaderArquivo(self,headerArquivo:HeaderArquivo) -> bool:

        linha:str="%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s" % (
            headerArquivo.codigoBanco,
            headerArquivo.codigoLote,
            headerArquivo.tipoRegistro,
            headerArquivo.brancos.ljust(6),
            headerArquivo.layoutArquivo,
            headerArquivo.inscricaoEmpresa,
            headerArquivo.cnpjEmpresa,
            headerArquivo.brancos.ljust(20),
            headerArquivo.agencia,
            headerArquivo.brancos.ljust(1),
            headerArquivo.conta,
            headerArquivo.brancos.ljust(1),
            headerArquivo.dac,
            headerArquivo.nomeEmpresa,
            headerArquivo.nomeBanco,
            headerArquivo.brancos.ljust(10),
            headerArquivo.arquivoCodigo,
            headerArquivo.dataGeracao,
            headerArquivo.horaGeracao,
            headerArquivo.zeros,
            headerArquivo.unidadeDensidade,
            headerArquivo.brancos.ljust(69)
        )    
        
        self.headerArquivo = linha
        return True

    def comporTrailerArquivo(self,trailerArquivo:TrailerArquivo) -> bool:

        linha:str="%s%s%s%s%s%s%s" % (
            trailerArquivo.codigoBanco,
            trailerArquivo.codigoLote,
            trailerArquivo.tipoRegistro,
            trailerArquivo.brancos.ljust(9),
            trailerArquivo.totalQtdeLotes,
            trailerArquivo.totalQtdeRegistros,
            trailerArquivo.brancos.ljust(211)
        )    
        
        self.trailerArquivo = linha
        return True

    def comporHeaderLote(self,headerLote:HeaderLoteO) -> bool:

        linha:str="%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s" % (
            headerLote.codigoBanco,
            headerLote.codigoLote,
            headerLote.tipoRegistro,
            headerLote.tipoOperacao,
            headerLote.tipoPagamento,
            headerLote.formaPagamento,
            headerLote.layoutLote,
            headerLote.brancos.ljust(1),
            headerLote.inscricaoEmpresa,
            headerLote.cnpjEmpresa,
            headerLote.brancos.ljust(20),
            headerLote.agencia,
            headerLote.brancos.ljust(1),
            headerLote.conta,
            headerLote.brancos.ljust(1),
            headerLote.dac,
            headerLote.nomeEmpresa,
            headerLote.finalidadeLote,
            headerLote.historicoCC,
            headerLote.enderecoEmpresa,
            headerLote.numeroEndereco,
            headerLote.complementoEndereco,
            headerLote.cidadeEmpresa,
            headerLote.cepEmpresa,
            headerLote.ufEmpresa,        
            headerLote.brancos.ljust(8),
            headerLote.brancos.ljust(10)
        )    
        
        self.headerLote = linha
        return True

    def comporTrailerLote(self,trailerLote:TrailerLoteO) -> bool:

        linha:str="%s%s%s%s%s%s%s%s%s" % (
            trailerLote.codigoBanco,
            trailerLote.codigoLote,
            trailerLote.tipoRegistro,
            trailerLote.brancos.ljust(9),
            trailerLote.totalQtdeRegistros,
            trailerLote.totalValorPgtos,
            trailerLote.totalQtdeMoeda,
            trailerLote.brancos.ljust(174),
            trailerLote.brancos.ljust(10)
        )    
        
        self.trailerLote = linha
        return True

    def comporDetalhe(self,detalhe:DetalheO) -> bool:

        linha:str="%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s" % (
            detalhe.codigoBanco,
            detalhe.codigoLote,
            detalhe.tipoRegistro,
            detalhe.numeroRegistro,
            detalhe.segmento,
            detalhe.tipoMovimento,
            detalhe.codigoBarras,
            detalhe.nome,
            detalhe.dataVcto,
            detalhe.moeda,
            detalhe.quantMoeda,
            detalhe.valorPagar,
            detalhe.dataPgto,
            detalhe.valorPago,
            detalhe.brancos.ljust(3),
            detalhe.notaFiscal,
            detalhe.brancos.ljust(3),
            detalhe.seuNumero,
            detalhe.brancos.ljust(21),
            detalhe.nossoNumero,
            detalhe.brancos.ljust(10)
        )    
        
        self.detalhes.append(linha)
        return True

    def montarArquivo(self) -> bool:
        
        linhas = []
        linhas.append(self.headerArquivo)
        linhas.append(self.headerLote)
        for detalhe in self.detalhes:
            linhas.append(detalhe)
        linhas.append(self.trailerLote)
        linhas.append(self.trailerArquivo)

        self.conteudo = '\r\n'.join(linhas) + '\r\n'
        return True

    def salvarArquivo(self, nomeArquivo:str=None) -> bool:
        
        if not self.conteudo:
            raise ValueError("Nenhum conteúdo para salvar")
        nomeArquivo = nomeArquivo if nomeArquivo else "REM"+datetime.now().strftime("%d%m")
        self.nomeArquivo = nomeArquivo+self.headerArquivo[72:73]+".REM"
        os.makedirs(DIR_REMESSAS,exist_ok=True)
        self.caminhoArquivo = os.path.join(DIR_REMESSAS,self.nomeArquivo)
        with open(self.caminhoArquivo,"w",newline='') as f:
            f.write(self.conteudo)
        self.limparDados()
        return True
    
    def limparDados(self) -> bool:
        self.headerArquivo = None
        self.trailerArquivo = None
        self.headerLote = None
        self.trailerLote = None
        self.detalhes = []
        self.conteudo = None
        self.data = None
        self.dados_bancarios = None
        return True