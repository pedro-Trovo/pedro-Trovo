#!/usr/bin/python3

import asyncio
import os
import re

import aiohttp

from coletor_dados import Estatisticas


async def gerar_visao_geral(e: Estatisticas) -> None:
    with open("meus-modelos/modelo-geral.svg", "r") as f:
        saida = f.read()
    saida = re.sub("{{ nome }}", await e.obter_nome(), saida)
    saida = re.sub("{{ estrelas }}", f"{await e.obter_estrelas():,}", saida)
    saida = re.sub("{{ forks }}", f"{await e.obter_forks():,}", saida)
    saida = re.sub("{{ contribuicoes }}", f"{await e.obter_total_contribuicoes():,}", saida)
    alteradas = (await e.obter_linhas_alteradas())[0] + (await e.obter_linhas_alteradas())[1]
    saida = re.sub("{{ linhas_alteradas }}", f"{alteradas:,}", saida)
    saida = re.sub("{{ visualizacoes }}", f"{await e.obter_visualizacoes():,}", saida)
    saida = re.sub("{{ repositorios }}", f"{len(await e.obter_todos_repos()):,}", saida)
    if not os.path.isdir("imagens"):
        os.mkdir("imagens")
    with open("imagens/pedro-stats-geral.svg", "w") as f:
        f.write(saida)


async def gerar_linguagens(e: Estatisticas) -> None:
    with open("meus-modelos/modelo-linguagens.svg", "r") as f:
        saida = f.read()
    progresso = ""
    lista_langs = ""
    langs_ordenadas = sorted((await e.obter_linguagens()).items(), reverse=True,
                              key=lambda t: t[1].get("tamanho"))
    atraso = 150
    for i, (lang, dados) in enumerate(langs_ordenadas[:15]):
        cor = dados.get("cor", "#000000")
        perc = dados.get("percentual", 0)
        if perc > 0:
            progresso += f'<span style="background-color: {cor}; width: {perc}%;" class="progress-item"></span>'
        lista_langs += f"""
<li style="animation-delay: {i * atraso}ms;">
<svg xmlns="http://www.w3.org/2000/svg" class="octicon" style="fill:{cor};" viewBox="0 0 16 16" width="16" height="16"><path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8z"></path></svg>
<span class="lang">{lang}</span>
<span class="percent">{perc:.2f}%</span>
</li>
"""
    saida = re.sub(r"{{ progresso }}", progresso, saida)
    saida = re.sub(r"{{ lista_langs }}", lista_langs, saida)
    if not os.path.isdir("imagens"):
        os.mkdir("imagens")
    with open("imagens/pedro-stats-linguagens.svg", "w") as f:
        f.write(saida)


async def main() -> None:
    token = os.getenv("ACCESS_TOKEN")
    if not token:
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise Exception("Token de acesso necessário!")
    usuario = os.getenv("GITHUB_ACTOR", "pedro-Trovo")
    async with aiohttp.ClientSession() as sessao:
        e = Estatisticas(usuario, token, sessao)
        await asyncio.gather(gerar_linguagens(e), gerar_visao_geral(e))


if __name__ == "__main__":
    asyncio.run(main())
