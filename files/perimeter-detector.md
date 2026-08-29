## ⚙️ Como usar

> **Ambiente:** Google Colab

1. Abra o notebook no [Google Colab](https://colab.research.google.com/).
2. Numere seus desenhos `.dxf` com um **prefixo fixo**, por exemplo:

```
   p001.dxf
   p002.dxf
   p003.dxf
```

3. Envie todos os arquivos para a aba **Arquivos** (ícone de pasta 📁 na barra lateral do Colab).
4. Execute o código normalmente — o script identifica automaticamente os arquivos pelo prefixo definido em `MEU_PREFIXO`, e gera o relatório com o nome definido em `NOME_ARQUIVO_TXT`.

> 💡 **Dica:** o prefixo (`p`, `n`, `x`...) pode ser alterado no topo do código, na variável `MEU_PREFIXO`.

---

```python

# ==========================================
# 1. IMPORTAÇÕES E CONFIGURAÇÃO DA VARIÁVEL
# ==========================================
try:
    import ezdxf
except ImportError:
    !pip install ezdxf
    import ezdxf

from ezdxf import path
import math
import os
from collections import defaultdict
import re

# Defina o prefixo aqui no topo (ex: 'n', 'p', 'x', etc.)
MEU_PREFIXO = 'n'

# Nome do arquivo de texto que será gerado para download
NOME_ARQUIVO_TXT = "relatorio_perimetros.txt"


# ==========================================
# 2. FUNÇÕES DE PROCESSAMENTO GEOMÉTRICO
# ==========================================
def comprimento_via_path(entidade, tolerancia=0.01):
    """Converte a entidade num Path e mede o comprimento por achatamento."""
    try:
        p = path.make_path(entidade)
    except Exception:
        return 0.0
    pontos = list(p.flattening(tolerancia))
    if len(pontos) < 2:
        return 0.0
    return sum(
        math.dist((pontos[i].x, pontos[i].y), (pontos[i + 1].x, pontos[i + 1].y))
        for i in range(len(pontos) - 1)
    )

def processar_entidades(entidades, nome_peca, dados_layer, dados_peca, profundidade=0):
    total_peca = 0.0
    for e in entidades:
        tipo = e.dxftype()
        if tipo == "INSERT":
            sub_nome = nome_peca if profundidade > 0 else e.dxf.name
            try:
                filhos = e.virtual_entities()
                total_peca += processar_entidades(filhos, sub_nome, dados_layer, dados_peca, profundidade + 1)
            except Exception:
                pass
        else:
            comp = comprimento_via_path(e)
            if comp > 0.0:
                camada = getattr(e.dxf, 'layer', '0')
                dados_layer[camada] += comp
                dados_peca[nome_peca] += comp
                total_peca += comp
    return total_peca


# ==========================================
# 3. FUNÇÃO PRINCIPAL E GERAÇÃO DO TXT
# ==========================================
def executar_processamento_com_txt(diretorio='.', prefixo_desejado=MEU_PREFIXO, arquivo_txt=NOME_ARQUIVO_TXT):
    if not os.path.exists(diretorio):
        print(f"O diretório '{diretorio}' não foi encontrado.")
        return

    padrao_nome = re.compile(rf'^{prefixo_desejado}\d+\.dxf$', re.IGNORECASE)
    arquivos = sorted([f for f in os.listdir(diretorio) if padrao_nome.match(f)])

    if not arquivos:
        print(f"Nenhum arquivo correspondente ao prefixo '{prefixo_desejado}' foi encontrado.")
        return

    print(f"Processando {len(arquivos)} arquivos (Prefixo: '{prefixo_desejado.upper()}')...\n")

    with open(arquivo_txt, 'w', encoding='utf-8') as f_txt:
        for arq in arquivos:
            caminho_arquivo = os.path.join(diretorio, arq)
            dados_layer = defaultdict(float)
            dados_peca = defaultdict(float)
            perimetro_total = 0.0

            try:
                doc = ezdxf.readfile(caminho_arquivo)
                msp = doc.modelspace()

                nome_base = os.path.splitext(arq)[0]
                perimetro_total = processar_entidades(msp, nome_base, dados_layer, dados_peca)

                # Montagem com os espaçamentos idênticos ao modelo solicitado
                bloco_relatorio = []
                bloco_relatorio.append(f"Arquivo: {arq}")
                bloco_relatorio.append(f"\tPerímetro Total: {perimetro_total:.2f} unidades")
                bloco_relatorio.append(f"\tDetalhamento por Layer:")
                for layer, comp in dados_layer.items():
                    bloco_relatorio.append(f"\t\t- Layer {layer}: {comp:.2f}")

                bloco_relatorio.append(f"\tDetalhamento por Peça (Bloco):")
                for peca, comp in dados_peca.items():
                    nome_bloco_exibicao = "Bloco raiz" if peca == nome_base else peca
                    bloco_relatorio.append(f"\t\t- {nome_bloco_exibicao}: {comp:.2f}")

                bloco_relatorio.append("-" * 55)

                texto_final_arquivo = "\n".join(bloco_relatorio) + "\n"

                print(texto_final_arquivo)
                f_txt.write(texto_final_arquivo)

            except Exception as e:
                erro_msg = f"Arquivo: {arq} | Erro ao processar: {e}\n" + "-" * 55 + "\n"
                print(erro_msg)
                f_txt.write(erro_msg)

    print(f"\n[Sucesso!] Relatório gerado e salvo no arquivo: '{arquivo_txt}' para download.")


# ==========================================
# 4. EXECUÇÃO
# ==========================================
if __name__ == "__main__":
    executar_processamento_com_txt(diretorio='.', prefixo_desejado=MEU_PREFIXO, arquivo_txt=NOME_ARQUIVO_TXT)

```
