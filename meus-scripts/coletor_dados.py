import asyncio
import os
from typing import Dict, List, Optional, Set, Tuple
import aiohttp
import requests

class ConsultasGitHub:
    def __init__(self, username: str, access_token: str,
                 session: aiohttp.ClientSession, max_connections: int = 10):
        self.username = username
        self.access_token = access_token
        self.session = session
        self.semaphore = asyncio.Semaphore(max_connections)

    async def consultar_graphql(self, query: str) -> Dict:
        headers = {"Authorization": f"Bearer {self.access_token}"}
        try:
            async with self.semaphore:
                r = await self.session.post("https://api.github.com/graphql",
                                            headers=headers,
                                            json={"query": query})
            return await r.json()
        except:
            async with self.semaphore:
                r = requests.post("https://api.github.com/graphql",
                                  headers=headers,
                                  json={"query": query})
                return r.json()

    async def consultar_rest(self, path: str, params: Optional[Dict] = None) -> Dict:
        for _ in range(60):
            headers = {"Authorization": f"token {self.access_token}"}
            if params is None:
                params = {}
            if path.startswith("/"):
                path = path[1:]
            try:
                async with self.semaphore:
                    r = await self.session.get(f"https://api.github.com/{path}",
                                               headers=headers,
                                               params=tuple(params.items()))
                if r.status == 202:
                    await asyncio.sleep(2)
                    continue
                return await r.json()
            except:
                async with self.semaphore:
                    r = requests.get(f"https://api.github.com/{path}",
                                     headers=headers,
                                     params=tuple(params.items()))
                    if r.status_code == 202:
                        await asyncio.sleep(2)
                        continue
                    elif r.status_code == 200:
                        return r.json()
        return {}

    @staticmethod
    def visao_geral(cursor_proprio: Optional[str] = None,
                    cursor_contrib: Optional[str] = None) -> str:
        return f"""{{
  viewer {{
    login,
    name,
    repositories(
        first: 20,
        orderBy: {{
            field: UPDATED_AT,
            direction: DESC
        }},
        isFork: false,
        after: {"null" if cursor_proprio is None else '"'+ cursor_proprio +'"'}
    ) {{
      pageInfo {{
        hasNextPage
        endCursor
      }}
      nodes {{
        nameWithOwner
        stargazers {{
          totalCount
        }}
        forkCount
        languages(first: 10, orderBy: {{field: SIZE, direction: DESC}}) {{
          edges {{
            size
            node {{
              name
              color
            }}
          }}
        }}
      }}
    }}
    repositoriesContributedTo(
        first: 100,
        includeUserRepositories: false,
        orderBy: {{
            field: UPDATED_AT,
            direction: DESC
        }},
        contributionTypes: [
            COMMIT,
            PULL_REQUEST,
            REPOSITORY,
            PULL_REQUEST_REVIEW
        ]
        after: {"null" if cursor_contrib is None else '"'+ cursor_contrib +'"'}
    ) {{
      pageInfo {{
        hasNextPage
        endCursor
      }}
      nodes {{
        nameWithOwner
        stargazers {{
          totalCount
        }}
        forkCount
        languages(first: 10, orderBy: {{field: SIZE, direction: DESC}}) {{
          edges {{
            size
            node {{
              name
              color
            }}
          }}
        }}
      }}
    }}
  }}
}}
"""

    @staticmethod
    def anos_contribuicao() -> str:
        return """
query {
  viewer {
    contributionsCollection {
      contributionYears
    }
  }
}
"""

    @staticmethod
    def contribs_por_ano(ano: str) -> str:
        return f"""
    ano{ano}: contributionsCollection(
        from: "{ano}-01-01T00:00:00Z",
        to: "{int(ano) + 1}-01-01T00:00:00Z"
    ) {{
      contributionCalendar {{
        totalContributions
      }}
    }}
"""

    @classmethod
    def todas_contribs(cls, anos: List[str]) -> str:
        por_ano = "\n".join(map(cls.contribs_por_ano, anos))
        return f"""
query {{
  viewer {{
    {por_ano}
  }}
}}
"""


class Estatisticas:
    def __init__(self, username: str, access_token: str,
                 session: aiohttp.ClientSession,
                 repos_ignorar: Optional[Set] = None,
                 langs_ignorar: Optional[Set] = None,
                 considerar_forks: bool = False):
        self.username = username
        self.repos_ignorar = set() if repos_ignorar is None else repos_ignorar
        self.langs_ignorar = set() if langs_ignorar is None else langs_ignorar
        self.considerar_forks = considerar_forks
        self.consultas = ConsultasGitHub(username, access_token, session)
        self.nome = None
        self.total_estrelas = None
        self.total_forks = None
        self.total_contribs = None
        self.linguagens = None
        self.repos_lista = None
        self.linhas_alteradas = None
        self.visualizacoes = None
        self.repos_ignorados = None

    async def carregar_dados(self) -> None:
        self.total_estrelas = 0
        self.total_forks = 0
        self.linguagens = {}
        self.repos_lista = set()
        self.repos_ignorados = set()
        
        prox_proprio = None
        prox_contrib = None
        
        while True:
            resultados = await self.consultas.consultar_graphql(
                ConsultasGitHub.visao_geral(cursor_proprio=prox_proprio,
                                           cursor_contrib=prox_contrib)
            )
            resultados = resultados if resultados is not None else {}

            self.nome = (resultados
                         .get("data", {})
                         .get("viewer", {})
                         .get("name", None))
            if self.nome is None:
                self.nome = (resultados
                             .get("data", {})
                             .get("viewer", {})
                             .get("login", "Sem Nome"))

            repos_contrib = (resultados
                             .get("data", {})
                             .get("viewer", {})
                             .get("repositoriesContributedTo", {}))
            repos_proprios = (resultados
                              .get("data", {})
                              .get("viewer", {})
                              .get("repositories", {}))
            
            repos = repos_proprios.get("nodes", [])
            if self.considerar_forks:
                repos += repos_contrib.get("nodes", [])
            else:
                for repo in repos_contrib.get("nodes", []):
                    nome = repo.get("nameWithOwner")
                    if nome in self.repos_ignorados or nome in self.repos_ignorar:
                        continue
                    self.repos_ignorados.add(nome)

            for repo in repos:
                nome = repo.get("nameWithOwner")
                if nome in self.repos_lista or nome in self.repos_ignorar:
                    continue
                self.repos_lista.add(nome)
                self.total_estrelas += repo.get("stargazers").get("totalCount", 0)
                self.total_forks += repo.get("forkCount", 0)

                for lang in repo.get("languages", {}).get("edges", []):
                    nome_lang = lang.get("node", {}).get("name", "Outras")
                    if nome_lang in self.langs_ignorar:
                        continue
                    if nome_lang in self.linguagens:
                        self.linguagens[nome_lang]["tamanho"] += lang.get("size", 0)
                        self.linguagens[nome_lang]["ocorrencias"] += 1
                    else:
                        self.linguagens[nome_lang] = {
                            "tamanho": lang.get("size", 0),
                            "ocorrencias": 1,
                            "cor": lang.get("node", {}).get("color")
                        }

            if repos_proprios.get("pageInfo", {}).get("hasNextPage", False) or \
                    repos_contrib.get("pageInfo", {}).get("hasNextPage", False):
                prox_proprio = (repos_proprios
                                .get("pageInfo", {})
                                .get("endCursor", prox_proprio))
                prox_contrib = (repos_contrib
                                .get("pageInfo", {})
                                .get("endCursor", prox_contrib))
            else:
                break

        total_bytes = sum([v.get("tamanho", 0) for v in self.linguagens.values()])
        for k, v in self.linguagens.items():
            v["percentual"] = 100 * (v.get("tamanho", 0) / total_bytes) if total_bytes > 0 else 0

    async def obter_nome(self) -> str:
        if self.nome is not None:
            return self.nome
        await self.carregar_dados()
        return self.nome

    async def obter_estrelas(self) -> int:
        if self.total_estrelas is not None:
            return self.total_estrelas
        await self.carregar_dados()
        return self.total_estrelas

    async def obter_forks(self) -> int:
        if self.total_forks is not None:
            return self.total_forks
        await self.carregar_dados()
        return self.total_forks

    async def obter_linguagens(self) -> Dict:
        if self.linguagens is not None:
            return self.linguagens
        await self.carregar_dados()
        return self.linguagens

    async def obter_linguagens_percentual(self) -> Dict:
        if self.linguagens is None:
            await self.carregar_dados()
        return {k: v.get("percentual", 0) for (k, v) in self.linguagens.items()}

    async def obter_repos(self) -> List[str]:
        if self.repos_lista is not None:
            return self.repos_lista
        await self.carregar_dados()
        return self.repos_lista
    
    async def obter_todos_repos(self) -> List[str]:
        if self.repos_lista is not None and self.repos_ignorados is not None:
            return self.repos_lista | self.repos_ignorados
        await self.carregar_dados()
        return self.repos_lista | self.repos_ignorados

    async def obter_total_contribuicoes(self) -> int:
        if self.total_contribs is not None:
            return self.total_contribs
        self.total_contribs = 0
        anos = (await self.consultas.consultar_graphql(ConsultasGitHub.anos_contribuicao())) \
            .get("data", {}) \
            .get("viewer", {}) \
            .get("contributionsCollection", {}) \
            .get("contributionYears", [])
        por_ano = (await self.consultas.consultar_graphql(ConsultasGitHub.todas_contribs(anos))) \
            .get("data", {}) \
            .get("viewer", {}).values()
        for ano in por_ano:
            self.total_contribs += ano \
                .get("contributionCalendar", {}) \
                .get("totalContributions", 0)
        return self.total_contribs

    async def obter_linhas_alteradas(self) -> Tuple[int, int]:
        if self.linhas_alteradas is not None:
            return self.linhas_alteradas
        adicoes = 0
        delecoes = 0
        for repo in await self.obter_todos_repos():
            r = await self.consultas.consultar_rest(f"/repos/{repo}/stats/contributors")
            for autor_obj in r:
                if not isinstance(autor_obj, dict) or not isinstance(autor_obj.get("author", {}), dict):
                    continue
                autor = autor_obj.get("author", {}).get("login", "")
                if autor != self.username:
                    continue
                for semana in autor_obj.get("weeks", []):
                    adicoes += semana.get("a", 0)
                    delecoes += semana.get("d", 0)
        self.linhas_alteradas = (adicoes, delecoes)
        return self.linhas_alteradas

    async def obter_visualizacoes(self) -> int:
        if self.visualizacoes is not None:
            return self.visualizacoes
        total = 0
        for repo in await self.obter_repos():
            r = await self.consultas.consultar_rest(f"/repos/{repo}/traffic/views")
            for view in r.get("views", []):
                total += view.get("count", 0)
        self.visualizacoes = total
        return self.visualizacoes
