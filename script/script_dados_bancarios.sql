select  cta.codctabcoint || ' :: ' || cta.descricao conta,
        cta.codemp || ' :: ' || decode(cta.codemp,1,'MATRIZ',3,'FILIAL SC',4,'FILIAL PR') empresa,        
        cta.codbco || ' :: ' || upper(bco.nomebco) banco
from    tsicta cta
inner join tsibco bco on cta.codbco = bco.codbco
where   cta.ativa = 'S'    
    and (cta.codbco = nvl({codigo_banco},cta.codbco) and
         cta.codage = nvl({numero_agencia},cta.codage) and
         cta.codctabco = trim('{numero_conta}'))
    or cta.codctabcoint = nvl({codigo_conta},cta.codctabcoint)