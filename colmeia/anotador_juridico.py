# anotador_juridico_regex.py
# ---------------------------------------------------------
# Anotador REGEX discreto de textos jurídicos
# Objetivo: prefixar trechos relevantes para
# posterior análise por LLM (sem extração)
# ---------------------------------------------------------

import re
from typing import List, Tuple


class AnotadorJuridicoRegex:
    """
    Anotador leve, discreto e tolerante.
    Prefixa trechos relevantes com _TAG:
    """

    TAGS: List[Tuple[str, str]] = [

        # =========================
        # IDENTIFICAÇÃO
        # =========================
        ("TRIBUNAL", r"\b(TJ[A-Z]{2}|Tribunal de Justiça[^,\n]*)\b"),
        ("ORGAO", r"\b(\d+[ªº°]?\s+(Câmara|Turma)[^\n,.]*)\b"),
        ("CL_PROCESSUAL", r"\b(Apelação Cível|Recurso Inominado|Agravo de Instrumento|Embargos de Declaração|REsp|AREsp)\b"),

        # =========================
        # PROCESSOS
        # =========================
        ("PROCESSO", r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}"),

        # =========================
        # ESTRUTURA DO JULGADO
        # =========================
        ("EMENTA", r"\bEMENTA\b"),
        ("RELATORIO", r"\bRELATÓRIO\b"),
        ("VOTO", r"\bVOTO\b"),
        ("DISPOSITIVO", r"\b(ACORDAM|DECIDO|ISTO POSTO|ANTE O EXPOSTO)\b"),

        # =========================
        # FUNDAMENTAÇÃO / VOTO
        # =========================
        ("ADMIS", r"\b(conheço|não conheço|admissibilidade|pressupostos de admissibilidade)\b"),
        ("CONCLUSAO", r"\b(diante do exposto|ante o exposto|assim, concluo)\b"),

        # =========================
        # DISPOSITIVOS LEGAIS
        # =========================
        ("ARTIGO", r"\b(art\.?\s*\d+)\b"),
        ("LEI", r"\bLei\s+n?[ºo]?\s*\d+[./]\d+\b"),
        ("CODIGO", r"\b(CPC|CDC|CC|CF|CLT|CP|CPP)\b"),

        # =========================
        # JURISPRUDÊNCIA
        # =========================
        ("JURIS", r"\b(REsp|AREsp|AgInt|AgRg|Súmula|Tema)\b"),

        # =========================
        # RESULTADO
        # =========================
        ("RESULTADO", r"\b(nego provimento|dou provimento|parcial provimento|recurso provido|recurso improvido)\b"),
    ]

    def __init__(self):
        self.compiled_tags = [
            (tag, re.compile(pattern, re.IGNORECASE))
            for tag, pattern in self.TAGS
        ]

    def anotar(self, texto: str) -> str:
        """
        Aplica marcações discretas no texto.
        """

        if not texto or not isinstance(texto, str):
            return texto

        texto_anotado = texto

        for tag, pattern in self.compiled_tags:
            texto_anotado = pattern.sub(
                lambda m: f"_{tag}: {m.group(0)}",
                texto_anotado
            )

        return texto_anotado


# =========================================================
# FUNÇÃO DE CONVENIÊNCIA
# =========================================================

_anotador_singleton = AnotadorJuridicoRegex()


def anotar_texto_juridico(texto: str) -> str:
    """
    Função simples para uso direto em workers / pipelines.
    """
    return _anotador_singleton.anotar(texto)


# =========================================================
# TESTE RÁPIDO
# =========================================================
if __name__ == "__main__":
    exemplo = """
    TJPR - 2ª Câmara Cível
    Agravo de Instrumento nº 0001234-56.2024.8.16.0001

    EMENTA
    Recurso improvido nos termos do art. 14 do CDC.

    RELATÓRIO
    Trata-se de Agravo de Instrumento interposto...

    VOTO
    Conheço do recurso. Diante do exposto, nego provimento.

    ACORDAM os Desembargadores...
    """

    print(anotar_texto_juridico(exemplo))