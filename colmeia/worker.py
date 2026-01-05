#!/usr/bin/env python3
"""
TJ-PR - Extrator por Contagem de Registros (v8.7 - Push Inteligente)
Worker com inicialização otimizada e lógica de push "anti-buraco" que
aguarda os workers lentos para garantir a integridade dos chunks.
"""

import re
import json
import requests
import csv
import shutil
import hashlib
import unicodedata
from pathlib import Path
import logging
import random
import uuid
import html
import os
import time
import tarfile
import io
from typing import Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from threading import Thread, Lock, current_thread
from queue import Queue, Empty
# Certifique-se de ter o GitPython instalado: pip install GitPython
from git import Repo, GitCommandError
from anotador_juridico import anotar_texto_juridico

# -----------------------------
# Configuração
# -----------------------------
GIT_TOKEN = os.getenv("GIT_TOKEN")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")

github_repo_env = os.getenv("GITHUB_REPO")
if github_repo_env:
    GITHUB_REPO = github_repo_env.replace("https://github.com/", "").replace(".git", "")
else:
    GITHUB_REPO = None

# Constantes de Controle
MAX_PAGINA = int(os.getenv("MAX_PAGINA", "1000000"))
MIN_PAGINA = int(os.getenv("MIN_PAGINA", "1"))
NUM_WORKERS_EXTRACAO = int(os.getenv("NUM_WORKERS_EXTRACAO", "10"))
TAMANHO_CHUNK_REGISTROS = 1000
MAX_TENTATIVAS_EXTRACAO = int(os.getenv("MAX_TENTATIVAS_EXTRACAO", "5"))

# Pasta onde o script executa e salva os arquivos de trabalho.
WORK_DIR = Path("./trabalho")
WORK_DIR.mkdir(exist_ok=True)

# Pasta que contém a clonagem do repositório Git para sincronização.
REPO_DIR = Path("./repo_git_temp")

# Caminhos para os arquivos na pasta de trabalho
PATH_PAGINAS_CSV = WORK_DIR / "paginas_status.csv"
PATH_PROCESSOS_CSV = WORK_DIR / "processos_vistos.csv"
PATH_OUTPUT_DIR = WORK_DIR / "chunks_dados"
PATH_STATS = WORK_DIR / "stats.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

# ===================================================================================
# CLASSE DE GERENCIAMENTO DO GIT (v2 - Lógica mais Segura)
# ===================================================================================
class GerenciadorGit:
    """
    Encapsula toda a lógica de interação com o repositório Git.
    Gerencia a autenticação, clonagem, sincronização (pull) e publicação (push).
    """
    def __init__(self, token: str, repo_slug: str, branch: str, local_path: Path):
        if not all([token, repo_slug, branch, local_path]):
            raise ValueError("Token, repo_slug, branch e local_path são obrigatórios para o GerenciadorGit.")
        
        self.remote_url = f"https://oauth2:{token}@github.com/{repo_slug}.git"
        self.local_path = local_path
        self.branch = branch
        self.repo = self._setup_repo()

    def _setup_repo(self) -> Repo:
        """Clona o repositório se não existir, ou abre o existente."""
        try:
            if not self.local_path.exists():
                logger.info(f"Clonando repositório de {GITHUB_REPO} para {self.local_path}...")
                repo = Repo.clone_from(self.remote_url, self.local_path, branch=self.branch)
            else:
                logger.info(f"Repositório local encontrado em {self.local_path}. Abrindo...")
                repo = Repo(self.local_path)
                repo.remotes.origin.set_url(self.remote_url)
            
            with repo.config_writer() as config:
                config.set_value("pull", "rebase", "true")
                config.set_value("user", "email", "worker-v8@bot.com")
                config.set_value("user", "name", "Abelha Atomica v8")
            
            return repo
        except GitCommandError as e:
            logger.critical(f"Falha crítica na configuração do repositório Git: {e}", exc_info=True)
            raise

    def sincronizar_com_remoto(self):
        """Prepara o repositório para receber novos arquivos, limpando-o e atualizando-o."""
        try:
            logger.info("Limpando o repositório local para garantir um estado inicial limpo...")
            self.repo.git.reset("--hard", "HEAD")
            self.repo.git.clean("-fd")
            logger.info(f"Executando 'pull' para sincronizar com a origem...")
            self.repo.remotes.origin.pull()
            logger.info("Repositório local sincronizado com a origem.")
        except GitCommandError as e:
            logger.error(f"⚠️ Falha ao sincronizar o repositório: {e}", exc_info=True)
            raise

    def publicar_alteracoes(self, arquivos_para_add: list, commit_message: str) -> bool:
        """Adiciona, commita e envia as alterações. Assume que o repo já foi sincronizado e os arquivos copiados."""
        try:
            logger.info(f"Adicionando arquivos ao stage: {arquivos_para_add}")
            self.repo.git.add(arquivos_para_add)
            if not self.repo.is_dirty(untracked_files=True):
                logger.warning("Nenhuma alteração detectada para o commit. Push ignorado.")
                return True
            logger.info(f"Realizando commit: \"{commit_message}\"")
            self.repo.index.commit(commit_message)
            logger.info("Realizando push para a origem...")
            self.repo.remotes.origin.push()
            logger.info("✅ Push concluído com sucesso!")
            return True
        except GitCommandError as e:
            logger.error(f"⚠️ Falha durante o commit/push no Git: {e}", exc_info=True)
            return False

# ===================================================================================
# CLASSE DE EXTRAÇÃO WEB
# ===================================================================================
class ExtratorUltraSimples:
    def __init__(self): self.base_url = "https://portal.tjpr.jus.br"
    
    def extrair_chave_valor_da_linha(self, tr_html: str) -> tuple:
        """Extrai chave normalizada e valor limpo de linha HTML de tabela."""
        
        # Extrai chave
        match_chave = re.search(r"<b>(.*?)</b>", tr_html, re.DOTALL | re.I)
        if not match_chave: return None, None
        
        # Normaliza chave
        chave = re.sub(r"<[^>]+>", "", match_chave.group(1))
        chave = unicodedata.normalize('NFKD', chave.replace(":", "")) \
            .encode('ascii', 'ignore').decode('utf-8')
        chave = re.sub(r"[^\w]+", "_", chave).strip("_").lower()
        
        # Extrai valor
        match_valor = re.search(r"</b>\s*(.*?)</td>", tr_html, re.DOTALL | re.I)
        if not match_valor: return chave, None
        
        # Limpa valor
        valor = match_valor.group(1)
        valor = re.sub(r"<div[^>]*>", "_DIV: ", valor, flags=re.I)
        
        valor = re.sub(r"</div>", "", valor, flags=re.I)
        valor = re.sub(r"<br\s*/?>", " --- ", valor, flags=re.I)
        valor = re.sub(r"<[^>]+>", "", valor)
        valor = re.sub(r"\(([^)]+)\)", r"_CITACAO:[\1]", valor)
        valor = re.sub(r' "([^"]+)"', r'_CITACAO:[\1]', valor)

        valor = re.sub(r' DISPOSITIVO ', r' ### _DISPOSITIVO: ', valor)
        valor = re.sub(r' ACORDAM ', r' ### _ACORDAM: ', valor)
        valor = re.sub(r' voto por ', r' ### _CITACAO: ', valor)
        valor = re.sub(r' RELATÓRIO ', r' ### _CITACAO: ', valor)
        valor = re.sub(r' ACORDAM ', r' ### _ACORDAM: ', valor)
        
        valor = html.unescape(valor)
        valor = re.sub(r"\s+", " ", valor).strip()
        valor = anotar_texto_juridico(valor)
        valor = re.sub(r' - ', ' ### ', valor)
        valor = re.sub(r' --- --- ', ' --- ', valor)
        valor = re.sub(r' --- --- ', ' --- ', valor)
    
        valor = self.remover_anotacoes_vazias(valor)
        valor = re.sub(r'  +', ' ', valor)
        valor = re.sub(r'\)', '', valor)
        valor = re.sub(r'"', '', valor)
        valor = re.sub(r'Ocultar Acórdão Atenção: O texto abaixo representa a transcrição de Acórdão. Eventuais imagens serão suprimidas.Recomenda-se acessar o PDF assinado.', '', valor)
        valor = re.sub(r' ---\s*([A-Za-z0-9IVXLCDM]{1,3})\s*­+', r' \n\n#### \1 - ', valor)
        valor = re.sub(r' ­ ', ' *** ', valor)
        return chave, valor
    
    def extrair_url_documento(self, tr_html: str) -> str: match = re.search(r"visualizacao\.do\?tjpr\.url\.crypto=([a-f0-9]+)", tr_html); return f"{self.base_url}/jurisprudencia/publico/visualizacao.do?tjpr.url.crypto={match.group(1)}" if match else None
    def extrair_tabelas(self, html: str) -> list: return re.findall(r'<table[^>]*class=["\']?[^"\']*resultTable[^"\']*["\']?[^>]*>(.*?)</table>', html, re.DOTALL | re.IGNORECASE)
    def extrair_linhas_tr(self, tabela_html: str) -> list: return re.findall(r"<tr[^>]*>(.*?)</tr>", tabela_html, re.DOTALL | re.IGNORECASE)
    def extrair_acordao(self, tabela_html: str) -> dict:
        acordao = {}
        for linha_html in self.extrair_linhas_tr(tabela_html):
            if url := self.extrair_url_documento(linha_html): acordao["url_documento"] = url
            if (chave := self.extrair_chave_valor_da_linha(linha_html)[0]) and (valor := self.extrair_chave_valor_da_linha(linha_html)[1]): acordao[chave] = valor
        return acordao
    def extrair_todos_acordaos(self, html: str) -> list: return [acordao for tabela in self.extrair_tabelas(html) if (acordao := self.extrair_acordao(tabela))]

    def remover_anotacoes_vazias(self, texto: str) -> str:
        #return re.sub(r'  +', ' ', re.sub(r'_\([^)]+\):_|_([^:]+):_', '', texto))
        return re.sub(r'  +', ' ', re.sub(r'_\([^)]+\):_|_([^:]+):\s+', '', texto))

# ===================================================================================
# CLASSE PRINCIPAL DO WORKER (v8.7 - Push Inteligente)
# ===================================================================================
class AbelhaAtomica:
    def __init__(self):
        if not GIT_TOKEN or not GITHUB_REPO:
            raise ValueError("As variáveis de ambiente GIT_TOKEN e GITHUB_REPO são obrigatórias.")
        
        self.worker_id = f"abelha-{uuid.uuid4().hex[:6]}"
        self.extrator_html = ExtratorUltraSimples()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": f"Mozilla/5.0 ({self.worker_id})"})
        self.fila_de_paginas = Queue()
        self.fila_de_resultados = Queue()
        self.lock_git = Lock()
        self.lock_estado = Lock()
        self.lock_pagina = Lock()
        self.thread_de_push = None
        self.paginas_em_processamento = {} # NOVO: Rastreia a página atual de cada worker
        self.paginas_status = {}
        self.processos_vistos = set()
        self.registros_para_chunk = []
        self.novos_status_processos = []
        self.novos_status_paginas = []
        self.html_bruto_acumulado = {}
        self.proximo_id_registro = 1
        self.proximo_chunk_id = 1
        self.proxima_pagina_a_verificar = MIN_PAGINA

        logger.info(f"Inicializando Abelha {self.worker_id} (v8.7 - Push Inteligente)...")
        
        self.git = GerenciadorGit(
            token=GIT_TOKEN, repo_slug=GITHUB_REPO, branch=GITHUB_BRANCH, local_path=REPO_DIR
        )
        self._inicializar_ambiente()
        
        logger.info(f"Abelha pronta. Estado: {len(self.paginas_status)} págs, {len(self.processos_vistos)} procs. Próximo Chunk ID: {self.proximo_chunk_id}")

    def _inicializar_ambiente(self):
        """
        Prepara o ambiente de trabalho de forma segura e otimizada.
        Deriva todo o estado a partir dos arquivos CSV.
        """
        with self.lock_git:
            logger.info("Iniciando preparação do ambiente de trabalho (lógica otimizada)...")
            self.git.sincronizar_com_remoto()

            logger.info(f"Verificando a pasta de trabalho em: {WORK_DIR}")
            arquivos_base = [PATH_PAGINAS_CSV.name, PATH_PROCESSOS_CSV.name]
            for nome_arquivo in arquivos_base:
                origem, destino = REPO_DIR / nome_arquivo, WORK_DIR / nome_arquivo
                if not destino.exists() and origem.exists():
                    logger.info(f"Arquivo de estado '{nome_arquivo}' não encontrado. Copiando do repositório...")
                    shutil.copy2(origem, destino)
            PATH_OUTPUT_DIR.mkdir(exist_ok=True)
            
            logger.info("Carregando estado a partir dos arquivos da pasta de trabalho...")
            if not PATH_PAGINAS_CSV.exists():
                with open(PATH_PAGINAS_CSV, 'w', newline='', encoding='utf-8') as f: csv.writer(f).writerow(['pagina', 'num_registros_ok', 'id_chunk', 'timestamp'])
            
            max_chunk_id = 0
            with open(PATH_PAGINAS_CSV, 'r', encoding='utf-8') as f:
                reader = csv.reader(f); next(reader, None)
                for row in reader:
                    try:
                        if row and row[0].isdigit(): self.paginas_status[int(row[0])] = {"status": "ok"}
                        if len(row) > 2 and row[2].isdigit(): max_chunk_id = max(max_chunk_id, int(row[2]))
                    except (ValueError, IndexError): continue
            
            if self.paginas_status: self.proxima_pagina_a_verificar = max(self.paginas_status.keys()) + 1
            self.proximo_chunk_id = max_chunk_id + 1

            if not PATH_PROCESSOS_CSV.exists():
                with open(PATH_PROCESSOS_CSV, 'w', newline='', encoding='utf-8') as f: csv.writer(f).writerow(['Id_processo', 'processo_25', 'pagina_extraida', 'chunk_inserida', 'timestamp', 'status'])
            with open(PATH_PROCESSOS_CSV, 'r', encoding='utf-8') as f:
                reader = csv.reader(f); next(reader, None)
                ids = [int(row[0]) for row in reader if row and len(row) > 1 and row[0].isdigit() and self.processos_vistos.add(row[1]) is None]
                if ids: self.proximo_id_registro = max(ids) + 1
            
            logger.info("Ambiente de trabalho pronto e estado carregado.")

    def _criar_chunk_e_fazer_push(self, registros_chunk, status_processos, status_paginas, html_a_salvar):
        """Processo de push seguro seguindo a lógica: 1º PULL, 2º COPY, 3º PUSH."""
        chunk_id = self.proximo_chunk_id
        try:
            # ETAPA 1: Gerar arquivos localmente em WORK_DIR.
            logger.info(f"📤 Gerando arquivos para o Chunk ID: {chunk_id} em {WORK_DIR}...")
            jurisprudencias_jsonl, timestamp = [], datetime.now().isoformat()
            for item in registros_chunk:
                reg_id = self.proximo_id_registro
                status_processos.append([reg_id, item['processo_25'], item['pagina'], chunk_id, timestamp, 'ok'])
                acordao = item['dados']; acordao['Id'] = reg_id
                jurisprudencias_jsonl.append(acordao)
                self.proximo_id_registro += 1
            for i in range(len(status_paginas)):
                if status_paginas[i][1] > 0: status_paginas[i][2] = chunk_id
            
            archive_path = PATH_OUTPUT_DIR / f"chunk_dados_{chunk_id:06d}.tar.gz"
            jsonl_content = "\n".join(json.dumps(rec, ensure_ascii=False) for rec in jurisprudencias_jsonl)
            with tarfile.open(archive_path, "w:gz") as tar:
                data = jsonl_content.encode('utf-8')
                tarinfo = tarfile.TarInfo(name="jurisprudencias.jsonl"); tarinfo.size = len(data)
                tar.addfile(tarinfo, io.BytesIO(data))

            with open(PATH_PAGINAS_CSV, 'a', newline='', encoding='utf-8') as f: csv.writer(f).writerows(status_paginas)
            with open(PATH_PROCESSOS_CSV, 'a', newline='', encoding='utf-8') as f: csv.writer(f).writerows(status_processos)

            with self.lock_git:
                logger.info(f"--- INÍCIO DO PROCESSO DE PUSH (CHUNK {chunk_id}) ---")
                
                # ETAPA 2: PRIMEIRO O PULL
                logger.info("PASSO 1/3: Sincronizando repositório local com o remoto...")
                self.git.sincronizar_com_remoto()

                # ETAPA 3: DEPOIS A CÓPIA
                logger.info("PASSO 2/3: Copiando novos dados da pasta de trabalho para o repositório...")
                shutil.copy2(PATH_PAGINAS_CSV, REPO_DIR / PATH_PAGINAS_CSV.name)
                shutil.copy2(PATH_PROCESSOS_CSV, REPO_DIR / PATH_PROCESSOS_CSV.name)
                repo_chunks_dir = REPO_DIR / PATH_OUTPUT_DIR.name
                repo_chunks_dir.mkdir(exist_ok=True)
                shutil.copy2(archive_path, repo_chunks_dir / archive_path.name)
                
                # ETAPA 4: POR FIM O PUSH
                logger.info("PASSO 3/3: Publicando alterações no repositório remoto...")
                paths_to_add = [PATH_PAGINAS_CSV.name, PATH_PROCESSOS_CSV.name, f"{PATH_OUTPUT_DIR.name}/{archive_path.name}"]
                commit_message = f"DATA: Adiciona chunk de dados {chunk_id}"
                
                if self.git.publicar_alteracoes(paths_to_add, commit_message):
                    self.proximo_chunk_id += 1
                    self._atualizar_estatisticas()
                    if PATH_STATS.exists():
                        shutil.copy2(PATH_STATS, REPO_DIR / PATH_STATS.name)
                        self.git.publicar_alteracoes([PATH_STATS.name], f"STATS: Atualiza com chunk {chunk_id}")
                else:
                    raise Exception("A publicação no Git falhou. Veja os logs de erro.")

        except Exception as e:
            logger.critical(f"❌ FALHA CRÍTICA no push do Chunk {chunk_id}: {e}", exc_info=True)
            logger.warning(f"Devolvendo {len(registros_chunk)} registros para a fila principal.")
            with self.lock_estado:
                self.registros_para_chunk = registros_chunk + self.registros_para_chunk
        finally:
            self.thread_de_push = None
            
    # --- O RESTANTE DAS FUNÇÕES DE LÓGICA DO WORKER ---

    def _encontrar_proxima_pagina_livre(self):
        with self.lock_pagina:
            while self.proxima_pagina_a_verificar <= MAX_PAGINA:
                pagina = self.proxima_pagina_a_verificar
                self.proxima_pagina_a_verificar += 1
                if pagina not in self.paginas_status:
                    self.paginas_status[pagina] = {"status": "processando"}; return pagina
            return None

    def _produtor_de_paginas(self):
        while True:
            if self.fila_de_paginas.qsize() < NUM_WORKERS_EXTRACAO * 2:
                if pagina := self._encontrar_proxima_pagina_livre(): self.fila_de_paginas.put(pagina)
                else: logger.info("Produtor: Nenhuma página nova encontrada. Aguardando..."); time.sleep(10)
            else: time.sleep(1)

    def _worker_de_extracao(self):
        thread_name = current_thread().name
        while True:
            pagina = -1 # Para logs de erro
            try:
                pagina = self.fila_de_paginas.get(timeout=30)
                with self.lock_estado: self.paginas_em_processamento[thread_name] = pagina
                self._processar_pagina(pagina)
                self.fila_de_paginas.task_done()
            except Empty:
                logger.info(f"Worker de extração {thread_name} ocioso, encerrando."); break
            except Exception as e:
                logger.error(f"Erro fatal no worker {thread_name} (Pág {pagina}): {e}", exc_info=True); self.fila_de_paginas.task_done()
            finally:
                with self.lock_estado: self.paginas_em_processamento.pop(thread_name, None)

    def _atualizar_estatisticas(self):
        logger.info(f"Iniciando atualização de estatísticas para o arquivo: {PATH_STATS}")
        try:
            total_paginas_com_resultados, total_processos_unicos = 0, 0
            if PATH_PAGINAS_CSV.exists():
                with open(PATH_PAGINAS_CSV, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f); next(reader, None)
                    for row in reader:
                        try:
                            num_registros = int(row[1])
                            if num_registros > 0:
                                total_paginas_com_resultados += 1
                                total_processos_unicos += num_registros
                        except (ValueError, IndexError):
                            continue
            
            agora = datetime.now()
            intervalos = {
                "5min": {"delta": timedelta(minutes=5), "paginas": 0, "processos": 0},
                "30min": {"delta": timedelta(minutes=30), "paginas": 0, "processos": 0},
                "180min": {"delta": timedelta(minutes=180), "paginas": 0, "processos": 0}
            }
            if PATH_PAGINAS_CSV.exists():
                with open(PATH_PAGINAS_CSV, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f); next(reader, None)
                    for row in reader:
                        try:
                            ts = datetime.fromisoformat(row[3])
                            num_registros = int(row[1])
                            for nome, dados in intervalos.items():
                                if agora - ts <= dados["delta"]:
                                    dados["paginas"] += 1
                                    if num_registros > 0:
                                        dados["processos"] += num_registros
                        except (ValueError, IndexError):
                            continue
            
            stats = {
                "total_global_paginas": total_paginas_com_resultados,
                "total_global_processos": total_processos_unicos,
                "ritmo_sessao": {},
                "timestamp_atualizacao": agora.isoformat()
            }
            
            # --- CORREÇÃO APLICADA AQUI ---
            # A lógica foi simplificada para dividir o total pelo número de minutos
            # do intervalo (5, 30, 180), como sugerido, para maior clareza e precisão.
            for nome, dados in intervalos.items():
                # Extrai o número de minutos diretamente do nome do intervalo (ex: "5min" -> 5)
                minutos_do_intervalo = int(re.search(r'\d+', nome).group())
                
                stats["ritmo_sessao"][nome] = {
                    "novas_paginas": dados["paginas"],
                    "media_pag_min": round(dados["paginas"] / minutos_do_intervalo, 2),
                    "novos_processos": dados["processos"],
                    "media_proc_min": round(dados["processos"] / minutos_do_intervalo, 2)
                }
            # --- FIM DA CORREÇÃO ---
    
            logger.info(f"Estatísticas geradas -> Totais(Páginas: {total_paginas_com_resultados}, Processos: {total_processos_unicos}) | Ritmo 5min(Páginas: {stats['ritmo_sessao']['5min']['novas_paginas']}, Processos: {stats['ritmo_sessao']['5min']['novos_processos']})")
            with open(PATH_STATS, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            logger.info("Arquivo stats.json atualizado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao atualizar estatísticas: {e}", exc_info=True)
            
    def extrair_processo_25(self, processo_str: Optional[str]) -> Optional[str]:
        """
        Extrai o número do processo (padrão CNJ novo ou antigo) usando uma única
        expressão regular e de forma segura. Retorna o número ou None.
        """
        if not isinstance(processo_str, str):
            return None
        padrao_combinado = r'\b(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}|\d{6,7}-\d)\b'
        match = re.search(padrao_combinado, processo_str)
        return match.group(1) if match else None        

    def _processar_pagina(self, pagina: int):
        logger.info(f"🐝 Processando página {pagina}...")
        num_registros_encontrados, num_registros_validos, html_content = 0, 0, ""
        try:
            html_content = self._requisitar_pagina(pagina)
            acordaos_brutos = self.extrator_html.extrair_todos_acordaos(html_content)
            num_registros_encontrados = len(acordaos_brutos)
            for acordao in acordaos_brutos:
                timestamp = datetime.now().isoformat()
                processo_25 = self.extrair_processo_25(acordao.get("processo"))
                tem_conteudo = any([acordao.get("url_documento"), acordao.get("ementa"), acordao.get("integra_do_acordao")])
                if not processo_25 or not tem_conteudo:
                    resultado = {"tipo": "status_processo", "dados": [0, processo_25 or "N/A", pagina, 0, timestamp, "ignorado"]}
                elif processo_25 in self.processos_vistos:
                    resultado = {"tipo": "status_processo", "dados": [0, processo_25, pagina, 0, timestamp, "duplicado"]}
                else:
                    num_registros_validos += 1; resultado = {"tipo": "registro_valido", "dados": acordao, "pagina": pagina, "processo_25": processo_25}
                self.fila_de_resultados.put(resultado)
            logger.info(f"✅ Página {pagina} finalizada. Encontrados: {num_registros_encontrados}, Válidos: {num_registros_validos}.")
        except Exception as e: logger.error(f"❌ Falha ao processar página {pagina}: {e}")
        self.fila_de_resultados.put({"tipo": "status_pagina", "dados": [pagina, num_registros_validos, 0, datetime.now().isoformat()], "html": html_content})
    
    def _requisitar_pagina(self, pagina: int) -> str:
        form_data = {"actionType": "pesquisar", "criterioPesquisa": "", "idLocalPesquisa": "99", "pageSize": "50", "pageNumber": str(pagina), "sortColumn": "processos.dataJulgamento", "sortOrder": "asc", "segredoJustica": "pesquisar sem", "mostrarCompleto": "true", "dataJulgamentoInicio": "01/01/2014", "dataJulgamentoFim": "11/12/2014"}
        for _ in range(MAX_TENTATIVAS_EXTRACAO):
            try:
                response = self.session.post("https://portal.tjpr.jus.br/jurisprudencia/publico/pesquisa.do", data=form_data, timeout=45)
                response.raise_for_status(); return response.text
            except requests.RequestException: time.sleep(5)
        raise ConnectionError(f"Excedido o número de tentativas para a página {pagina}.")

    def _consumidor_de_resultados(self):
        while True:
            try:
                item = self.fila_de_resultados.get()
                with self.lock_estado:
                    if item['tipo'] == 'registro_valido':
                        self.processos_vistos.add(item['processo_25']); self.registros_para_chunk.append(item)
                    elif item['tipo'] == 'status_processo':
                        if item['dados'][5] != 'duplicado': self.processos_vistos.add(item['dados'][1])
                        self.novos_status_processos.append(item['dados'])
                    elif item['tipo'] == 'status_pagina':
                        self.novos_status_paginas.append(item['dados'])
                        if item.get('html'): self.html_bruto_acumulado[item['dados'][0]] = item['html']

                    # LÓGICA DE GATILHO DE PUSH REFEITA
                    if len(self.registros_para_chunk) >= TAMANHO_CHUNK_REGISTROS and not self.thread_de_push:
                        registros_a_enviar = self.registros_para_chunk[:TAMANHO_CHUNK_REGISTROS]
                        max_pagina_no_chunk = max((reg['pagina'] for reg in registros_a_enviar if 'pagina' in reg), default=0)
                        min_pagina_ativa = min(self.paginas_em_processamento.values()) if self.paginas_em_processamento else float('inf')

                        if min_pagina_ativa > max_pagina_no_chunk:
                            logger.info(f"PUSH AUTORIZADO. Chunk com págs até ~{max_pagina_no_chunk}. Worker mais lento está em pág ~{min_pagina_ativa}.")
                            self.registros_para_chunk = self.registros_para_chunk[TAMANHO_CHUNK_REGISTROS:]
                            self.thread_de_push = Thread(target=self._criar_chunk_e_fazer_push, args=(registros_a_enviar, list(self.novos_status_processos), list(self.novos_status_paginas), dict(self.html_bruto_acumulado)), name="PushThread")
                            self.thread_de_push.start()
                            self.novos_status_processos.clear(); self.novos_status_paginas.clear(); self.html_bruto_acumulado.clear()
                        else:
                            logger.info(f"Push adiado. Chunk pronto (págs até ~{max_pagina_no_chunk}), mas worker está em pág {min_pagina_ativa}. Aguardando workers avançarem.")

            except Exception as e: logger.critical(f"Erro no consumidor de resultados: {e}", exc_info=True)

    def iniciar(self):
        Thread(target=self._produtor_de_paginas, name="PageProducer", daemon=True).start()
        Thread(target=self._consumidor_de_resultados, name="ResultConsumer", daemon=True).start()
        with ThreadPoolExecutor(max_workers=NUM_WORKERS_EXTRACAO, thread_name_prefix='ExtractionWorker') as executor:
            for _ in range(NUM_WORKERS_EXTRACAO):
                executor.submit(self._worker_de_extracao)
        logger.info("Todos os workers de extração terminaram.")

def main():
    try: 
        AbelhaAtomica().iniciar()
        while True: time.sleep(60)
    except Exception as e:
        logger.critical(f"Falha fatal na inicialização: {e}", exc_info=True); exit(1)

if __name__ == "__main__":
    main()