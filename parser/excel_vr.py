import pandas as pd

class ExcelVr:

    def __init__(self):
        pass

    def ler_arquivo(self,arquivo) -> tuple[pd.DataFrame,pd.DataFrame,pd.DataFrame]:
        """ 
            Lê o conteúdo do arquivo enviado pelo usuário e retorna uma lista de linhas.
                :param arquivo: Arquivo enviado pelo usuário.
                :return cabecalho: Cabeçalho do arquivo.
                :return data_credito: Data do crédito.
                :return conteudo: Conteúdo do arquivo.
        """

        conteudo = arquivo.read()

        cabecalho = pd.read_excel(conteudo,engine="openpyxl",header=5,nrows=4,usecols="B:C")
        data_credito = pd.read_excel(conteudo,engine="openpyxl",header=12,nrows=1,usecols="B:C")
        conteudo = pd.read_excel(conteudo,engine="openpyxl",header=19,usecols="B:J")
        return cabecalho, data_credito, conteudo

    def padroniza_campos(self,cabecalho:pd.DataFrame,data_credito:pd.DataFrame,conteudo:pd.DataFrame) -> tuple[pd.DataFrame,pd.DataFrame,pd.DataFrame]:
        """
            Padroniza o nome dos campos.
                :param cabecalho: Cabeçalho do arquivo.
                :param data_credito: Data do crédito.
                :param conteudo: Conteúdo do arquivo.
                :return cabecalho: Cabeçalho formatado do arquivo.
                :return data_credito: Data do crédito formatada.
                :return conteudo: Conteúdo formatado do arquivo.
        """
        
        cabecalho['Unnamed: 1'] = cabecalho['Unnamed: 1'].apply(lambda x: x.replace(':',''))
        cabecalho = cabecalho.T.reset_index(drop=True)
        cabecalho.columns = cabecalho.loc[0,:]
        cabecalho.drop(index=0,axis=0,inplace=True)
        cols = conteudo.columns
        cols = [c.replace('.','').replace('(R$)','').strip().replace(' ','_').lower() for c in cols]
        data_credito.pop('Produto')
        conteudo.columns = cols

        return cabecalho, data_credito, conteudo
    
    def extrai_conteudo(self, cabecalho:pd.DataFrame,data_credito:pd.DataFrame,conteudo:pd.DataFrame) -> tuple[dict,dict]:
        """
            Extrai o conteúdo do arquivo Excel pra dicionário.
                :param cabecalho: Cabeçalho formatador do arquivo
                :param data_credito: Data do crédito formatada.
                :param conteudo: Conteúdo formatado do arquivo.
                :return cabecalho: Dicionário contendo o cabeçalho do arquivo com a data do crédito.
                :return conteudo: Dicionário contendo o conteúdo do arquivo.
        """

        cabecalho, data_credito, conteudo = self.padroniza_campos(cabecalho,data_credito,conteudo)
        return cabecalho.to_dict(orient='records')[0] | data_credito.to_dict(orient='records')[0], conteudo.to_dict(orient='records')
