async def gerar_linguagens(e: Estatisticas) -> None:
    print("="*50)
    print("GERANDO LINGUAGENS")
    print("="*50)
    
    # CARREGA OS DADOS PRIMEIRO
    linguagens = await e.obter_linguagens()
    
    print(f"Linguagens encontradas: {linguagens}")
    print(f"Tipo: {type(linguagens)}")
    print(f"Tamanho: {len(linguagens) if linguagens else 0}")
    
    with open("meus-modelos/modelo-linguagens.svg", "r") as f:
        saida = f.read()
    
    progresso = ""
    lista_langs = ""
    
    if linguagens:
        langs_ordenadas = sorted(linguagens.items(), reverse=True,
                                  key=lambda t: t[1].get("tamanho", 0))
        print(f"Langs ordenadas: {[lang for lang, _ in langs_ordenadas[:5]]}")
        
        atraso = 150
        
        for i, (lang, dados) in enumerate(langs_ordenadas[:15]):
            cor = dados.get("cor", "#000000")
            tamanho = dados.get("tamanho", 0)
            perc = dados.get("percentual", 0)
            
            print(f"  - {lang}: {perc:.2f}% ({tamanho} bytes) cor: {cor}")
            
            if perc > 0:
                progresso += f'<span style="background-color: {cor}; width: {perc}%;" class="progress-item"></span>'
            
            lista_langs += f"""
<li style="animation-delay: {i * atraso}ms;">
<svg xmlns="http://www.w3.org/2000/svg" class="octicon" style="fill:{cor};" viewBox="0 0 16 16" width="16" height="16"><path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8z"></path></svg>
<span class="lang">{lang}</span>
<span class="percent">{perc:.2f}%</span>
</li>
"""
    else:
        print("❌ NENHUMA LINGUAGEM ENCONTRADA!")
        # Dados de exemplo para teste
        progresso = '<span style="background-color: #f1e05a; width: 100%;" class="progress-item"></span>'
        lista_langs = """
<li style="animation-delay: 0ms;">
<svg xmlns="http://www.w3.org/2000/svg" class="octicon" style="fill:#f1e05a;" viewBox="0 0 16 16" width="16" height="16"><path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8z"></path></svg>
<span class="lang">Sem linguagens detectadas</span>
<span class="percent">0.00%</span>
</li>
"""
    
    saida = re.sub(r"{{ progress }}", progresso, saida)
    saida = re.sub(r"{{ lang_list }}", lista_langs, saida)
    
    if not os.path.isdir("imagens"):
        os.mkdir("imagens")
    with open("imagens/pedro-stats-linguagens.svg", "w") as f:
        f.write(saida)
    
    print("✅ SVG de linguagens salvo!")
    print("="*50)


async def gerar_visao_geral(e: Estatisticas) -> None:
    print("="*50)
    print("GERANDO VISÃO GERAL")
    print("="*50)
    
    nome = await e.obter_nome()
    estrelas = await e.obter_estrelas()
    forks = await e.obter_forks()
    contribs = await e.obter_total_contribuicoes()
    linhas = await e.obter_linhas_alteradas()
    views = await e.obter_visualizacoes()
    repos = await e.obter_todos_repos()
    
    print(f"Nome: {nome}")
    print(f"Estrelas: {estrelas}")
    print(f"Forks: {forks}")
    print(f"Contribuições: {contribs}")
    print(f"Linhas alteradas: {linhas[0]+linhas[1]}")
    print(f"Views: {views}")
    print(f"Repositórios: {len(repos)}")
    
    with open("meus-modelos/modelo-geral.svg", "r") as f:
        saida = f.read()
    
    saida = re.sub(r"{{ name }}", nome, saida)
    saida = re.sub(r"{{ stars }}", f"{estrelas:,}", saida)
    saida = re.sub(r"{{ forks }}", f"{forks:,}", saida)
    saida = re.sub(r"{{ contributions }}", f"{contribs:,}", saida)
    
    alteradas = linhas[0] + linhas[1]
    saida = re.sub(r"{{ lines_changed }}", f"{alteradas:,}", saida)
    
    saida = re.sub(r"{{ views }}", f"{views:,}", saida)
    saida = re.sub(r"{{ repos }}", f"{len(repos):,}", saida)
    
    if not os.path.isdir("imagens"):
        os.mkdir("imagens")
    with open("imagens/pedro-stats-geral.svg", "w") as f:
        f.write(saida)
    
    print("✅ SVG geral salvo!")
    print("="*50)
