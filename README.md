# RentSmart — Orçamento de Locação (R.M Imóveis)

**Autor:** Marcos de França Saldanha · Disciplina: Algorithmic Thinking & Introduction to Object-Oriented Programming

Aplicação em Python, orientada a objetos, que calcula o orçamento de locação de imóveis da R.M Imóveis, mostra o resumo detalhado e gera um arquivo CSV com a projeção dos 12 primeiros meses de contrato.

## Requisitos

- Python 3.8 ou superior
- Nenhuma biblioteca externa (usa apenas `csv` e `datetime`, que já vêm com o Python)

## Como executar

```bash
git clone https://github.com/SEU-USUARIO/rentsmart.git
cd rentsmart
python rentsmart.py
```

No Linux/macOS, pode ser necessário usar `python3 rentsmart.py`.

O programa vai pedir:

1. Nome do cliente
2. Tipo de imóvel: Apartamento, Casa ou Estúdio
3. Para apartamento e casa: quantidade de quartos (1 ou 2) e se deseja vaga de garagem
4. Para apartamento: se o cliente possui crianças
5. Para estúdio: se deseja estacionamento e quantas vagas no total
6. Número de parcelas da taxa contratual (1 a 5)

No final, ele mostra o resumo do orçamento na tela e salva o arquivo `projecao_<cliente>_<data_hora>.csv` na mesma pasta.

## Regras de negócio implementadas

| Item | Valor |
|---|---|
| Aluguel-base: apartamento (1 quarto) | R$ 700,00 |
| Aluguel-base: casa (1 quarto) | R$ 900,00 |
| Aluguel-base: estúdio | R$ 1.200,00 |
| Apartamento com 2 quartos | + R$ 200,00 |
| Casa com 2 quartos | + R$ 250,00 |
| Vaga de garagem (casa ou apartamento) | + R$ 300,00 |
| Estúdio: pacote de 2 vagas | + R$ 250,00 |
| Estúdio: cada vaga adicional | + R$ 60,00 |
| Apartamento sem crianças | 5% de desconto sobre o aluguel com os adicionais |
| Taxa contratual (separada do aluguel) | R$ 2.000,00, em até 5 parcelas |

## Estrutura de classes

| Classe | Responsabilidade |
|---|---|
| `Imovel` | Classe base: aluguel-base, adicionais, descontos e cálculo do aluguel mensal |
| `ImovelResidencial` | Base de casa e apartamento: quartos e vaga de garagem |
| `Apartamento` | Adicional de 2 quartos (R$ 200) e desconto de 5% sem crianças |
| `Casa` | Adicional de 2 quartos (R$ 250) |
| `Estudio` | Pacote de 2 vagas e vagas extras |
| `TaxaContratual` | Valor da taxa, parcelamento e parcela de cada mês |
| `Orcamento` | Junta imóvel e taxa, mostra o resumo, calcula a projeção e gera o CSV |
| `Atendimento` | Perguntas ao usuário com validação das entradas |

## Arquivo CSV

O CSV usa `;` como separador e vírgula como separador decimal, para abrir direto no Excel em português. As colunas são: mês, aluguel, parcela da taxa contratual e total do mês, mais uma linha de total.

```
Mes;Aluguel (R$);Parcela taxa contratual (R$);Total do mes (R$)
1;1140,00;666,67;1806,67
...
Total;13680,00;2000,00;15680,00
```

## Exemplo

Apartamento com 2 quartos, vaga de garagem, sem crianças e taxa em 3x:

- 700 + 200 + 300 = R$ 1.200,00
- Desconto de 5%: − R$ 60,00
- **Aluguel mensal: R$ 1.140,00**
- Taxa contratual: 3x de R$ 666,67, cobrada nos meses 1 a 3
