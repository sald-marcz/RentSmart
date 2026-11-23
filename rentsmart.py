"""
RentSmart - Sistema de Orçamento de Locação da R.M Imóveis.

Recebe as características da locação, aplica as regras comerciais da
imobiliária, mostra o orçamento detalhado e gera um arquivo CSV com a
projeção dos 12 primeiros meses de contrato.
"""

import csv
from datetime import datetime


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------

def formatar_moeda(valor):
    """Formata um número no padrão brasileiro: R$ 1.234,56."""
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


# ---------------------------------------------------------------------------
# Imóveis
# ---------------------------------------------------------------------------

class Imovel:
    """Classe base com o que todo imóvel tem em comum.

    Cada tipo de imóvel (Apartamento, Casa, Estudio) herda desta classe e
    define apenas as suas próprias regras de adicionais e descontos.
    """

    nome = "Imóvel"
    aluguel_base = 0.0

    def calcular_adicionais(self):
        """Retorna uma lista de tuplas (descrição, valor) com os adicionais."""
        return []

    def calcular_descontos(self, subtotal):
        """Retorna uma lista de tuplas (descrição, valor) com os descontos."""
        return []

    def total_adicionais(self):
        return sum(valor for _, valor in self.calcular_adicionais())

    def subtotal(self):
        """Aluguel-base somado aos adicionais (antes dos descontos)."""
        return self.aluguel_base + self.total_adicionais()

    def total_descontos(self):
        return sum(valor for _, valor in self.calcular_descontos(self.subtotal()))

    def aluguel_mensal(self):
        """Valor final do aluguel mensal."""
        return round(self.subtotal() - self.total_descontos(), 2)

    def descricao(self):
        return self.nome


class ImovelResidencial(Imovel):
    """Base para casas e apartamentos, que têm quartos e vaga de garagem."""

    ADICIONAL_GARAGEM = 300.00
    adicional_dois_quartos = 0.0

    def __init__(self, quartos, tem_garagem):
        if quartos not in (1, 2):
            raise ValueError("O número de quartos deve ser 1 ou 2.")
        self.quartos = quartos
        self.tem_garagem = tem_garagem

    def calcular_adicionais(self):
        adicionais = []
        if self.quartos == 2:
            adicionais.append(("Adicional 2º quarto", self.adicional_dois_quartos))
        if self.tem_garagem:
            adicionais.append(("Vaga de garagem", self.ADICIONAL_GARAGEM))
        return adicionais

    def descricao(self):
        texto = f"{self.nome} com {self.quartos} quarto(s)"
        if self.tem_garagem:
            texto += " e vaga de garagem"
        return texto


class Apartamento(ImovelResidencial):
    nome = "Apartamento"
    aluguel_base = 700.00
    adicional_dois_quartos = 200.00
    PERCENTUAL_DESCONTO_SEM_CRIANCAS = 0.05

    def __init__(self, quartos, tem_garagem, possui_criancas):
        super().__init__(quartos, tem_garagem)
        self.possui_criancas = possui_criancas

    def calcular_descontos(self, subtotal):
        # O desconto é aplicado depois dos adicionais, sobre o subtotal.
        if not self.possui_criancas:
            desconto = round(subtotal * self.PERCENTUAL_DESCONTO_SEM_CRIANCAS, 2)
            return [("Desconto 5% (sem crianças)", desconto)]
        return []


class Casa(ImovelResidencial):
    nome = "Casa"
    aluguel_base = 900.00
    adicional_dois_quartos = 250.00


class Estudio(Imovel):
    nome = "Estúdio"
    aluguel_base = 1200.00
    VALOR_PACOTE_VAGAS = 250.00   # pacote inicial com 2 vagas
    VAGAS_NO_PACOTE = 2
    VALOR_VAGA_EXTRA = 60.00

    def __init__(self, vagas):
        # Estacionamento do estúdio: nenhuma vaga ou, no mínimo, o pacote de 2.
        if vagas != 0 and vagas < self.VAGAS_NO_PACOTE:
            raise ValueError("Informe 0 vagas ou no mínimo 2 (pacote inicial).")
        self.vagas = vagas

    def vagas_extras(self):
        return max(0, self.vagas - self.VAGAS_NO_PACOTE)

    def calcular_adicionais(self):
        if self.vagas == 0:
            return []
        adicionais = [("Pacote de 2 vagas", self.VALOR_PACOTE_VAGAS)]
        extras = self.vagas_extras()
        if extras > 0:
            adicionais.append(
                (f"{extras} vaga(s) extra(s) x {formatar_moeda(self.VALOR_VAGA_EXTRA)}",
                 extras * self.VALOR_VAGA_EXTRA)
            )
        return adicionais

    def descricao(self):
        if self.vagas == 0:
            return f"{self.nome} sem estacionamento"
        return f"{self.nome} com {self.vagas} vaga(s) de estacionamento"


# ---------------------------------------------------------------------------
# Taxa contratual
# ---------------------------------------------------------------------------

class TaxaContratual:
    """Taxa de contrato, cobrada separadamente do aluguel."""

    VALOR_TOTAL = 2000.00
    MAX_PARCELAS = 5

    def __init__(self, parcelas):
        if not 1 <= parcelas <= self.MAX_PARCELAS:
            raise ValueError(f"A taxa pode ser parcelada de 1 a {self.MAX_PARCELAS} vezes.")
        self.parcelas = parcelas

    def valor_parcela(self):
        return round(self.VALOR_TOTAL / self.parcelas, 2)

    def parcela_do_mes(self, mes):
        """Valor da taxa cobrado em um mês (1 a 12). Zero depois de quitada."""
        if mes > self.parcelas:
            return 0.0
        if mes == self.parcelas:
            # Última parcela ajusta os centavos do arredondamento.
            return round(self.VALOR_TOTAL - self.valor_parcela() * (self.parcelas - 1), 2)
        return self.valor_parcela()


# ---------------------------------------------------------------------------
# Orçamento
# ---------------------------------------------------------------------------

class Orcamento:
    """Junta o imóvel e a taxa contratual e gera o resumo e a projeção."""

    MESES_PROJECAO = 12

    def __init__(self, cliente, imovel, taxa):
        self.cliente = cliente
        self.imovel = imovel
        self.taxa = taxa

    def projecao(self):
        """Lista de dicionários com os valores de cada um dos 12 meses."""
        linhas = []
        aluguel = self.imovel.aluguel_mensal()
        for mes in range(1, self.MESES_PROJECAO + 1):
            parcela = self.taxa.parcela_do_mes(mes)
            linhas.append({
                "mes": mes,
                "aluguel": aluguel,
                "parcela_taxa": parcela,
                "total": round(aluguel + parcela, 2),
            })
        return linhas

    def total_12_meses(self):
        return round(sum(linha["total"] for linha in self.projecao()), 2)

    def exibir_resumo(self):
        imovel = self.imovel
        largura = 52
        print("\n" + "=" * largura)
        print("RESUMO DO ORÇAMENTO - R.M IMÓVEIS".center(largura))
        print("=" * largura)
        print(f"Cliente: {self.cliente}")
        print(f"Imóvel:  {imovel.descricao()}")

        print("\n--- ALUGUEL MENSAL ---")
        print(f"{'Aluguel-base (' + imovel.nome + ')':<36}{formatar_moeda(imovel.aluguel_base):>16}")
        for descricao, valor in imovel.calcular_adicionais():
            print(f"{'+ ' + descricao:<36}{formatar_moeda(valor):>16}")
        for descricao, valor in imovel.calcular_descontos(imovel.subtotal()):
            print(f"{'- ' + descricao:<36}{formatar_moeda(valor):>16}")
        print("-" * largura)
        print(f"{'ALUGUEL MENSAL':<36}{formatar_moeda(imovel.aluguel_mensal()):>16}")

        print("\n--- TAXA CONTRATUAL (cobrada à parte) ---")
        print(f"{'Valor total da taxa':<36}{formatar_moeda(self.taxa.VALOR_TOTAL):>16}")
        print(f"{'Parcelamento':<36}{str(self.taxa.parcelas) + 'x de ' + formatar_moeda(self.taxa.valor_parcela()):>16}")

        print("\n--- PROJEÇÃO DOS 12 MESES ---")
        print(f"{'Mês':<6}{'Aluguel':>14}{'Taxa':>14}{'Total':>16}")
        for linha in self.projecao():
            print(f"{linha['mes']:<6}{formatar_moeda(linha['aluguel']):>14}"
                  f"{formatar_moeda(linha['parcela_taxa']):>14}{formatar_moeda(linha['total']):>16}")
        print("-" * largura)
        print(f"{'TOTAL NO PRIMEIRO ANO':<36}{formatar_moeda(self.total_12_meses()):>16}")
        print("=" * largura)

    def gerar_csv(self, nome_arquivo=None):
        """Grava a projeção em CSV (separador ';', abre direto no Excel)."""
        if nome_arquivo is None:
            data = datetime.now().strftime("%Y%m%d_%H%M%S")
            cliente = "".join(c if c.isalnum() else "_" for c in self.cliente)
            nome_arquivo = f"projecao_{cliente}_{data}.csv"

        def numero(valor):
            return f"{valor:.2f}".replace(".", ",")

        with open(nome_arquivo, "w", newline="", encoding="utf-8-sig") as arquivo:
            escritor = csv.writer(arquivo, delimiter=";")
            escritor.writerow(["Mes", "Aluguel (R$)", "Parcela taxa contratual (R$)", "Total do mes (R$)"])
            for linha in self.projecao():
                escritor.writerow([linha["mes"], numero(linha["aluguel"]),
                                   numero(linha["parcela_taxa"]), numero(linha["total"])])
            escritor.writerow(["Total", numero(self.imovel.aluguel_mensal() * self.MESES_PROJECAO),
                               numero(self.taxa.VALOR_TOTAL), numero(self.total_12_meses())])
        return nome_arquivo


# ---------------------------------------------------------------------------
# Entrada de dados (com validação)
# ---------------------------------------------------------------------------

class Atendimento:
    """Conversa com o usuário: pergunta, valida e monta o orçamento."""

    TIPOS = {"1": "Apartamento", "2": "Casa", "3": "Estúdio"}

    @staticmethod
    def perguntar_texto(mensagem):
        while True:
            resposta = input(mensagem).strip()
            if resposta:
                return resposta
            print("  Campo obrigatório. Tente novamente.")

    @staticmethod
    def perguntar_opcao(mensagem, opcoes):
        while True:
            resposta = input(mensagem).strip()
            if resposta in opcoes:
                return resposta
            print(f"  Opção inválida. Digite uma destas: {', '.join(opcoes)}.")

    @staticmethod
    def perguntar_sim_nao(mensagem):
        while True:
            resposta = input(mensagem + " (S/N): ").strip().upper()
            if resposta in ("S", "SIM"):
                return True
            if resposta in ("N", "NAO", "NÃO"):
                return False
            print("  Responda com S ou N.")

    @staticmethod
    def perguntar_inteiro(mensagem, minimo, maximo):
        while True:
            resposta = input(mensagem).strip()
            if resposta.isdigit() and minimo <= int(resposta) <= maximo:
                return int(resposta)
            print(f"  Digite um número inteiro entre {minimo} e {maximo}.")

    def escolher_imovel(self):
        print("\nTipos de imóvel:")
        print("  1 - Apartamento (a partir de R$ 700,00)")
        print("  2 - Casa        (a partir de R$ 900,00)")
        print("  3 - Estúdio     (a partir de R$ 1.200,00)")
        tipo = self.perguntar_opcao("Escolha o tipo [1-3]: ", list(self.TIPOS))

        if tipo == "3":
            if self.perguntar_sim_nao("Deseja estacionamento? Pacote de 2 vagas por R$ 250,00"):
                vagas = self.perguntar_inteiro(
                    "Quantas vagas no total? (mínimo 2, R$ 60,00 por vaga extra) [2-10]: ", 2, 10)
            else:
                vagas = 0
            return Estudio(vagas)

        quartos = self.perguntar_inteiro("Quantidade de quartos [1-2]: ", 1, 2)
        garagem = self.perguntar_sim_nao("Deseja vaga de garagem? (+ R$ 300,00)")

        if tipo == "1":
            criancas = self.perguntar_sim_nao("O cliente possui crianças?")
            return Apartamento(quartos, garagem, criancas)
        return Casa(quartos, garagem)

    def escolher_taxa(self):
        print(f"\nTaxa contratual: {formatar_moeda(TaxaContratual.VALOR_TOTAL)}")
        parcelas = self.perguntar_inteiro(
            f"Em quantas parcelas? [1-{TaxaContratual.MAX_PARCELAS}]: ", 1, TaxaContratual.MAX_PARCELAS)
        return TaxaContratual(parcelas)

    def novo_orcamento(self):
        cliente = self.perguntar_texto("\nNome do cliente: ")
        imovel = self.escolher_imovel()
        taxa = self.escolher_taxa()
        return Orcamento(cliente, imovel, taxa)


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------

def main():
    print("=" * 52)
    print("RentSmart - Orçamento de Locação | R.M Imóveis".center(52))
    print("=" * 52)

    atendimento = Atendimento()
    while True:
        orcamento = atendimento.novo_orcamento()
        orcamento.exibir_resumo()
        arquivo = orcamento.gerar_csv()
        print(f"\nProjeção de 12 meses salva em: {arquivo}")

        if not Atendimento.perguntar_sim_nao("\nDeseja fazer outro orçamento?"):
            print("Obrigado por usar o RentSmart!")
            break


if __name__ == "__main__":
    main()
