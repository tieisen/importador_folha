from pydantic import BaseModel, Field, field_validator
from typing import Literal
import unicodedata, re
from datetime import datetime, timedelta, timezone


def normalizarString(texto: str, picture: int) -> str:        
    if not isinstance(texto,str):
        texto = str(texto)  
    texto = unicodedata.normalize('NFKD', texto)
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r'[^a-zA-Z0-9\s_]', '', texto)        
    return texto.upper()[:picture].ljust(picture)

def normalizarDate(data: str, picture: int) -> str:
    _data:datetime=None        
    if not isinstance(data,str):
        data = str(data)        
    try:
        _data = datetime.strptime(data,'%d/%m/%Y')
    except:
        try:
            _data = datetime.strptime(data,'%Y-%m-%d')
        except:
            pass
    finally:
        if not _data:
            raise ValueError("Data inválida")            
    return _data.strftime("%d%m%Y").ljust(picture)

def normalizarInteger(numero: int, picture: int) -> str:        
    if not isinstance(numero,int):
        try:
            numero = int(numero)
        except:
            raise ValueError(f"Número inválido: {numero}")            
    return str(numero).zfill(picture)

def normalizarFloat(numero: float, picture: int) -> str:        
    if not isinstance(numero,float):
        try:
            numero = float(numero)
        except:
            raise ValueError(f"Número inválido: {numero}")
    FORMATO = f"{{:.2f}}"
    _numero = FORMATO.format(numero)
    _numero = str(re.sub(r'[.,]', '', _numero)).strip()
    return _numero.zfill(picture)

def dataHoraGeracao(tipo:Literal['d','h','dh']):
    br_tz = timezone(timedelta(hours=-3))        
    agora:datetime = datetime.now(tz=br_tz)
    data:str = agora.strftime('%d%m%Y')
    hora:str = agora.strftime('%H%M%S')
    data_completa:str = agora.strftime('%d%m%Y%H%M%S')        
    match tipo:
        case 'd':
            return data
        case 'h':
            return hora
        case 'dh':
            return data_completa
        case _:
            raise ValueError("Tipo inválido")  

def corrigirBarcode(barcode: str) -> str:
    
    def modulo10_barra(codigo_sem_dv: str) -> int:
        soma = 0
        peso = 2
        for digito in reversed(codigo_sem_dv):
            mult = int(digito) * peso
            soma += sum(map(int, str(mult)))
            peso = 1 if peso == 2 else 2
        resto = soma % 10
        return 0 if resto == 0 else 10 - resto

    def modulo11_barra(codigo_sem_dv: str) -> int:
        pesos = list(range(2, 10))
        soma = 0
        peso_idx = 0
        for digito in reversed(codigo_sem_dv):
            soma += int(digito) * pesos[peso_idx]
            peso_idx = (peso_idx + 1) % len(pesos)
        resto = soma % 11
        dv = 11 - resto
        # regra FEBRABAN
        if dv in [0, 1, 10, 11]:
            return 1
        return dv

    def calcular_dv_geral(codigo_sem_dv: str) -> int:
        """
        Detecta automaticamente qual módulo usar
        com base no 3º dígito do código de barras.
        """
        tipo = codigo_sem_dv[2]
        if tipo in ['6', '7']:
            return modulo10_barra(codigo_sem_dv)
        elif tipo in ['8', '9']:
            return modulo11_barra(codigo_sem_dv)
        else:
            raise ValueError(f"Tipo de valor inválido: {tipo}")

    linha = ''.join(filter(str.isdigit, barcode))
    if len(linha) != 48:
        raise ValueError("Linha digitável deve ter 48 dígitos")
    campo1 = linha[0:11]
    campo2 = linha[12:23]
    campo3 = linha[24:35]
    campo4 = linha[36:47]
    codigo = campo1 + campo2 + campo3 + campo4
    codigo_sem_dv = codigo[:3] + codigo[4:]
    dv_geral = calcular_dv_geral(codigo_sem_dv)
    codigo_final = codigo[:3] + str(dv_geral) + codigo[4:]
    return codigo_final

def validar_segmento_o(linha_digitavel: str, valor_informado: float | None = None) -> dict:
    
    def modulo10(numero: str) -> int:
        soma = 0
        peso = 2

        for n in reversed(numero):
            calc = int(n) * peso
            if calc >= 10:
                calc = (calc // 10) + (calc % 10)
            soma += calc
            peso = 1 if peso == 2 else 2

        resto = soma % 10
        return (10 - resto) if resto != 0 else 0

    def corrigir_linha_digitavel(linha: str) -> dict:
        resultado = {
            "valida": True,
            "corrigida": linha,
            "alteracoes": []
        }

        if len(linha) != 48 or not linha.isdigit():
            raise ValueError("Linha digitável inválida (formato)")

        campos = [linha[i:i+12] for i in range(0, 48, 12)]
        campos_corrigidos = []

        for idx, campo in enumerate(campos, start=1):
            dados = campo[:-1]
            dv_informado = int(campo[-1])
            dv_calculado = modulo10(dados)

            if dv_informado != dv_calculado:
                resultado["valida"] = False
                resultado["alteracoes"].append({
                    "campo": idx,
                    "dv_original": dv_informado,
                    "dv_corrigido": dv_calculado
                })
                campo_corrigido = dados + str(dv_calculado)
            else:
                campo_corrigido = campo

            campos_corrigidos.append(campo_corrigido)

        linha_corrigida = "".join(campos_corrigidos)
        resultado["corrigida"] = linha_corrigida

        return resultado

    def linha_digitavel_to_barcode(linha: str) -> str:
        res = corrigir_linha_digitavel(linha)

        linha_corrigida = res["corrigida"]

        campos = [linha_corrigida[i:i+12] for i in range(0, 48, 12)]
        codigo_barras = "".join(c[:-1] for c in campos)

        if len(codigo_barras) != 44:
            raise ValueError("Erro na conversão para código de barras")

        return codigo_barras

    def extrair_valor_codigo_barras(codigo: str) -> float:
        tipo_valor = codigo[2]

        valor_str = codigo[4:15]

        if tipo_valor in ["6", "8"]:
            # valor em reais (2 casas decimais)
            return int(valor_str) / 100

        elif tipo_valor in ["7", "9"]:
            # sem valor definido
            return 0.0

        else:
            raise ValueError(f"Tipo de valor inválido: {tipo_valor}")    
    
    resultado = {
        "valido": True,
        "erros": [],
        "barcode": None,
        "valor_codigo": None
    }

    try:
        barcode = linha_digitavel_to_barcode(linha_digitavel)
        resultado["barcode"] = barcode

        if len(barcode) != 44:
            raise ValueError("Código de barras inválido (tamanho)")

        if not barcode.isdigit():
            raise ValueError("Código de barras contém caracteres inválidos")

        if barcode[0] != "8":
            raise ValueError("Não é arrecadação (deve iniciar com 8)")

        valor_codigo = extrair_valor_codigo_barras(barcode)
        resultado["valor_codigo"] = valor_codigo

        if valor_informado is not None:
            if round(valor_codigo, 2) != round(valor_informado, 2):
                raise ValueError(
                    f"Valor divergente: código={valor_codigo} informado={valor_informado}"
                )

    except Exception as e:
        resultado["valido"] = False
        resultado["erros"].append(str(e))

    return resultado

class HeaderArquivo(BaseModel):
    
    codigoBanco:int
    nomeBanco:str    
    agencia:int
    conta:int
    dac:int
    cnpjEmpresa:str
    nomeEmpresa:str
    codigoLote:str = Field(min_length=4, max_length=4, default=''.zfill(4))
    tipoRegistro:str = Field(min_length=1, max_length=1, default=str(0))
    layoutArquivo:str = Field(min_length=3, max_length=3, default='080')
    inscricaoEmpresa:str = Field(min_length=1, max_length=1, default=str(2))
    arquivoCodigo:str = Field(min_length=3, max_length=3, default=str(1))
    dataGeracao:str = Field(min_length=8, max_length=8, default=dataHoraGeracao('d'))
    horaGeracao:str = Field(min_length=6, max_length=6, default=dataHoraGeracao('h'))
    unidadeDensidade:str = ''.zfill(5)
    zeros:str = ''.zfill(9)
    brancos:str = ''
    
    @field_validator("codigoBanco")
    def valida_codigoBanco(cls, v):
        if len(str(v).strip()) != 3:
            raise ValueError("Código do banco inválido")
        return str(v)
    
    @field_validator("nomeBanco")
    def valida_nomeBanco(cls, v):
        if len(v) < 3:
            raise ValueError("Nome do banco inválido")
        return normalizarString(v,30)

    @field_validator("agencia")
    def valida_agencia(cls, v):
        if len(str(v).strip()) not in range(1,5):
            raise ValueError("Código da agência inválido")
        return normalizarInteger(v,5)

    @field_validator("conta")
    def valida_conta(cls, v):
        if len(str(v).strip()) not in range(1,12):
            raise ValueError("Código da conta inválido")
        return normalizarInteger(v,12)

    @field_validator("dac")
    def valida_dac(cls, v):
        if len(str(v).strip()) != 1:
            raise ValueError("Dígito verificador da conta bancária inválido")
        return normalizarInteger(v,1)

    @field_validator("cnpjEmpresa")
    def valida_cnpjEmpresa(cls, v):
        from re import sub
        regex = r'[^0-9]'
        cnpj_tratado = sub(regex, '', v)
        if len(cnpj_tratado) != 14:
            raise ValueError("CNPJ inválido")
        v = cnpj_tratado
        return v.ljust(14)
        
    @field_validator("nomeEmpresa")
    def valida_nomeEmpresa(cls, v):
        if len(v) < 3:
            raise ValueError("Nome da empresa inválido")
        return normalizarString(v,30)

class TrailerArquivo(BaseModel):
    
    codigoBanco:int
    totalQtdeLotes:int
    totalQtdeRegistros:int
    codigoLote:str = Field(min_length=4, max_length=4, default='9999')
    tipoRegistro:str = Field(min_length=1, max_length=1, default=str(9))    
    brancos:str = ''

    @field_validator("codigoBanco")
    def valida_codigoBanco(cls, v):
        if len(str(v).strip()) != 3:
            raise ValueError("Código do banco inválido")
        return normalizarInteger(v,3)
    
    @field_validator("totalQtdeLotes")
    def valida_totalQtdeLotes(cls, v):
        if not v or v < 1:
            raise ValueError("Quantidade de lotes inválida")
        return normalizarInteger(v,6)
    
    @field_validator("totalQtdeRegistros")
    def valida_totalQtdeRegistros(cls, v):
        if not v or v < 1:
            raise ValueError("Quantidade de registros inválida")
        return normalizarInteger(v,6)

class HeaderLoteO(BaseModel):

    codigoBanco:int
    agencia:int
    conta:int
    dac:int
    cnpjEmpresa:str
    nomeEmpresa:str
    enderecoEmpresa:str
    numeroEndereco:str
    complementoEndereco:str #= Field(default=''.rjust(15))
    cidadeEmpresa:str
    cepEmpresa:str
    ufEmpresa:str    
    codigoLote:str = Field(min_length=4, max_length=4, default='1'.zfill(4))
    tipoRegistro:str = Field(min_length=1, max_length=1, default=str(1))
    tipoOperacao:str = Field(min_length=1, max_length=1, default='C')
    tipoPagamento:str = Field(min_length=2, max_length=2, default='22')
    formaPagamento:str = Field(min_length=2, max_length=2, default='91')
    layoutLote:str = Field(min_length=3, max_length=3, default='030')
    inscricaoEmpresa:str = Field(min_length=1, max_length=1, default=str(2))
    finalidadeLote:str = Field(min_length=30, max_length=30, default=''.rjust(30))
    historicoCC:str = Field(min_length=10, max_length=10, default=''.rjust(10))        
    brancos:str = ''

    @field_validator("codigoBanco")
    def valida_codigoBanco(cls, v):
        if len(str(v).strip()) != 3:
            raise ValueError("Código do banco inválido")
        return normalizarInteger(v,3)

    @field_validator("agencia")
    def valida_agencia(cls, v):
        if len(str(v).strip()) not in range(1,5):
            raise ValueError("Código da agência inválido")
        return normalizarInteger(v,5)

    @field_validator("conta")
    def valida_conta(cls, v):
        if len(str(v).strip()) not in range(1,12):
            raise ValueError("Código da conta inválido")
        return normalizarInteger(v,12)

    @field_validator("dac")
    def valida_dac(cls, v):
        if len(str(v).strip()) != 1:
            raise ValueError("Dígito verificador da conta bancária inválido")
        return normalizarInteger(v,1)

    @field_validator("cnpjEmpresa")
    def valida_cnpjEmpresa(cls, v):
        from re import sub
        regex = r'[^0-9]'
        cnpj_tratado = sub(regex, '', v)
        if len(cnpj_tratado) != 14:
            raise ValueError("CNPJ inválido")
        v = cnpj_tratado
        return v.ljust(14)
        
    @field_validator("nomeEmpresa")
    def valida_nomeEmpresa(cls, v):
        if len(str(v).strip()) < 3:
            raise ValueError("Nome da empresa inválido")
        return normalizarString(v,30)
    
    @field_validator("numeroEndereco")
    def valida_numeroEndereco(cls, v):
        if not v:
            return str(v).rjust(5)
        return str(v).upper().rjust(5,"0")
    
    @field_validator("enderecoEmpresa")
    def valida_enderecoEmpresa(cls, v):
        if len(str(v).strip()) < 3:
            raise ValueError("Endereço da empresa inválido")
        return normalizarString(v,30)
    
    @field_validator("complementoEndereco")
    def valida_complementoEndereco(cls, v):
        return normalizarString(v,15)
    
    @field_validator("cepEmpresa")
    def valida_cepEmpresa(cls, v):
        from re import sub
        regex = r'[^0-9]'
        cep_tratado = sub(regex, '', v)        
        if len(str(cep_tratado).strip()) != 8:
            raise ValueError("CEP da empresa inválido")
        v = cep_tratado
        return v
    
    @field_validator("cidadeEmpresa")
    def valida_cidadeEmpresa(cls, v):
        if len(str(v).strip()) < 3:
            raise ValueError("Endereço da empresa inválido")
        return normalizarString(v,20)
    
    @field_validator("ufEmpresa")
    def valida_ufEmpresa(cls, v):
        if len(str(v).strip()) != 2:
            raise ValueError("UF da empresa inválido. Informe somente a sigla.")
        return normalizarString(v,2)

class TrailerLoteO(BaseModel):
    
    codigoBanco:int
    totalQtdeRegistros:int
    totalValorPgtos:float = Field(default=''.zfill(18))
    totalQtdeMoeda:float = Field(default=''.zfill(15))
    codigoLote:str = Field(min_length=4, max_length=4, default='1'.zfill(4))
    tipoRegistro:str = Field(min_length=1, max_length=1, default=str(5))
    brancos:str = ''

    @field_validator("codigoBanco")
    def valida_codigoBanco(cls, v):
        if len(str(v).strip()) != 3:
            raise ValueError("Código do banco inválido")
        return normalizarInteger(v,3)
    
    @field_validator("totalQtdeRegistros")
    def valida_totalQtdeRegistros(cls, v):
        return normalizarInteger(v,6)
    
    @field_validator("totalValorPgtos")
    def valida_totalValorPgtos(cls, v):
        return normalizarFloat(v,18)
    
    @field_validator("totalQtdeMoeda")
    def valida_totalQtdeMoeda(cls, v):
        return normalizarFloat(v,15)

class DetalheO(BaseModel):

    codigoBanco:int
    numeroRegistro:int
    codigoBarras:str
    nome:str
    dataVcto:str
    valorPagar:float
    dataPgto:str
    seuNumero:int    
    codigoLote:str = Field(min_length=4, max_length=4, default='1'.zfill(4))
    tipoRegistro:str = Field(min_length=1, max_length=1, default=str(3))    
    segmento:str = Field(min_length=1, max_length=1, default='O')
    tipoMovimento:str = Field(min_length=3, max_length=3, default=''.zfill(3))    
    moeda:str = Field(min_length=3, max_length=3, default='REA')
    quantMoeda:float = Field(default=''.zfill(15))
    valorPago:str = Field(min_length=15, max_length=15, default=''.zfill(15))
    notaFiscal:int = Field(min_length=1, max_length=9, default=''.ljust(9))
    nossoNumero:int = Field(min_length=1, max_length=15, default=''.ljust(15))
    brancos:str = ''

    @field_validator("codigoBanco")
    def valida_codigoBanco(cls, v):
        if len(str(v).strip()) != 3:
            raise ValueError("Código do banco inválido")
        return normalizarInteger(v,3)

    @field_validator("numeroRegistro")
    def valida_numeroRegistro(cls, v):
        return normalizarInteger(v,5)
        
    @field_validator("codigoBarras")
    def valida_codigoBarras(cls, v):
        # if len(str(v).strip()) < 3:
        #     raise ValueError("Código de barras inválido")
        # v = corrigirBarcode(v)
        aux = validar_segmento_o(v)
        if not aux['valido']:
            raise ValueError("Código de barras inválido")
        v = aux['barcode']
        # if not v:
        #     raise ValueError("Código de barras inválido")
        return normalizarString(v,48)
        
    @field_validator("nome")
    def valida_nome(cls, v):
        if len(str(v).strip()) < 3:
            raise ValueError("Nome da empresa inválido")
        return normalizarString(v,30)
        
    @field_validator("dataVcto")
    def valida_dataVcto(cls, v):
        if len(str(v).strip()) < 8:
            raise ValueError("Data inválida")
        return normalizarDate(v,8)
        
    @field_validator("quantMoeda")
    def valida_quantMoeda(cls, v):
        return normalizarFloat(v,15)
        
    @field_validator("valorPagar")
    def valida_valorPagar(cls, v):
        return normalizarFloat(v,15)

    @field_validator("dataPgto")
    def valida_dataPgto(cls, v):
        if len(str(v).strip()) < 8:
            raise ValueError("Data inválida")
        return normalizarDate(v,8)

    @field_validator("seuNumero")
    def valida_seuNumero(cls, v):
        return normalizarInteger(v,20)    