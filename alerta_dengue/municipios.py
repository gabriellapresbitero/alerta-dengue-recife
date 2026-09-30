"""Municípios da Região Metropolitana do Recife e seus códigos IBGE.

O InfoDengue identifica cada cidade pelo geocódigo do IBGE (7 dígitos).
Você pode consultar outros códigos em:
https://www.ibge.gov.br/explica/codigos-dos-municipios.php
"""

MUNICIPIOS = {
    "recife": 2611606,
    "olinda": 2609600,
    "jaboatao": 2607901,
    "paulista": 2610707,
    "camaragibe": 2603454,
}


def resolver_geocodigo(valor: str) -> int:
    """Aceita o nome curto do município ("recife") ou o geocódigo ("2611606")."""
    valor = valor.strip().lower()
    if valor.isdigit():
        if len(valor) != 7:
            raise ValueError("O geocódigo do IBGE tem 7 dígitos.")
        return int(valor)
    if valor not in MUNICIPIOS:
        opcoes = ", ".join(sorted(MUNICIPIOS))
        raise ValueError(f"Município desconhecido: {valor!r}. Opções: {opcoes}")
    return MUNICIPIOS[valor]
