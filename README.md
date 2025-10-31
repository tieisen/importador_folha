# 💰 Importador de Folha de Pagamento para Sankhya

Este projeto é uma aplicação web desenvolvida com Streamlit para automatizar a importação de arquivos de folha de pagamento no formato CNAB240 para o ERP Sankhya. A ferramenta extrai os dados de pagamento do arquivo, enriquece-os com informações do Sankhya e os lança como despesas financeiras.

## ✨ Funcionalidades

- **Interface Web Intuitiva**: Interface amigável construída com Streamlit para facilitar o upload e processamento dos arquivos.
- **Parsing de CNAB240**: Suporte para arquivos de retorno de pagamento no formato CNAB240 dos bancos Bradesco (237) and Itaú (341).
- **Integração com Sankhya**:
  - Autenticação segura na API do Sankhya.
  - Busca e validação automática da conta bancária da empresa.
  - Busca automática do código de parceiro (funcionário) no Sankhya a partir do nome.
- **Revisão de Dados**: Permite que o usuário revise e edite os dados antes de enviá-los, podendo ajustar a natureza do lançamento (Salário, Férias), referência e datas.
- **Lançamento de Despesas**: Formata e envia os pagamentos para serem registrados como lançamentos financeiros no Sankhya.

## 🚀 Começando

Siga estas instruções para configurar e executar o projeto em seu ambiente local.

### Pré-requisitos

- Python 3.8+
- Acesso à uma instância do Sankhya com API habilitada.

### Instalação

1.  Clone o repositório para sua máquina local:
    ```bash
    git clone <URL_DO_SEU_REPOSITORIO>
    cd importador-folha
    ```

2.  É altamente recomendado usar um ambiente virtual:
    ```bash
    python -m venv venv
    source venv/bin/activate  # No Windows, use `venv\Scripts\activate`
    ```

3.  Instale as dependências do projeto:
    ```bash
    pip install -r requirements.txt
    ```

### Configuração

A aplicação utiliza variáveis de ambiente para se conectar à API do Sankhya. Crie um arquivo chamado `.env` na raiz do projeto e preencha-o com as informações necessárias.
Use o arquivo `.env.example` como modelo.

### Executando a Aplicação

Com o ambiente configurado e as dependências instaladas, execute o seguinte comando no terminal:

```bash
streamlit run app.py
```

A aplicação será aberta em seu navegador padrão. Agora você pode fazer o upload do seu arquivo CNAB240 e iniciar o processo de importação.