# app.py
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import json
from pathlib import Path
import psutil # <--- IMPORTANTE: Biblioteca para ler status do sistema

app = FastAPI()

# ATUALIZE O CAMINHO: O worker agora salva em 'trabalho/stats.json'
# Se o seu app.py e o worker.py rodam a partir do mesmo diretório,
# este caminho deve estar correto.
STATS_FILE = Path("./trabalho/stats.json")

@app.get("/", response_class=HTMLResponse)
def root():
    stats = {}
    if STATS_FILE.exists():
        try:
            stats = json.loads(STATS_FILE.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, FileNotFoundError):
            stats = {}
    
    # --- Coleta de Dados ---
    # Extrai totais GLOBAIS
    total_paginas = stats.get("total_global_paginas", 0)
    total_processos = stats.get("total_global_processos", 0)
    
    # Extrai ritmo da SESSÃO
    ritmo = stats.get("ritmo_sessao", {})
    default_rate = {"novas_paginas": 0, "novos_processos": 0, "media_pag_min": 0.0, "media_proc_min": 0.0}
    r5 = ritmo.get("5min", default_rate)
    r30 = ritmo.get("30min", default_rate)
    r180 = ritmo.get("180min", default_rate)
    
    last_update = stats.get("timestamp_atualizacao", "Aguardando worker...")

    # NOVO: Coleta de Status do Sistema
    cpu_usage = psutil.cpu_percent()
    mem_info = psutil.virtual_memory()
    disk_info = psutil.disk_usage('/')

    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <title>Monitor de Extração TJPR</title>
        <meta http-equiv="refresh" content="10">
        <meta charset="UTF-8">
        <style>
            /* --- NOVA FONTE E ANIMAÇÕES --- */
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

            @keyframes buzz {{
                0%, 100% {{ transform: translateY(0) rotate(-2deg); }}
                50% {{ transform: translateY(-4px) rotate(2deg); }}
            }}
            
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(10px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}

            body {{
                font-family: 'Poppins', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                margin: 0; padding: 25px; background: #f0f2f5; color: #333;
            }}
            .container {{
                max-width: 850px; margin: 0 auto; background: white; border-radius: 12px;
                box-shadow: 0 6px 20px rgba(0,0,0,0.07);
                animation: fadeIn 0.5s ease-out;
            }}
            .header {{
                background: linear-gradient(135deg, #4a69bd, #34495e);
                color: white; padding: 25px; text-align: center; border-radius: 12px 12px 0 0;
            }}
            .header h1 {{
                margin: 0; font-size: 1.8rem; font-weight: 600;
                display: flex; align-items: center; justify-content: center; gap: 15px;
            }}
            .bee {{
                display: inline-block;
                animation: buzz 1.2s infinite ease-in-out;
                font-size: 2.2rem;
            }}
            
            .kpi-grid {{ display: flex; text-align: center; border-bottom: 1px solid #e8e8e8; }}
            .kpi-box {{ 
                flex: 1; padding: 30px 15px; border-right: 1px solid #e8e8e8;
                transition: background-color 0.2s ease, transform 0.2s ease;
            }}
            .kpi-box:hover {{ background-color: #fafcff; transform: scale(1.03); }}
            .kpi-box:last-child {{ border-right: none; }}
            .kpi-val {{ font-size: 2.3rem; font-weight: 700; color: #4a69bd; }}
            .kpi-label {{ font-size: 0.85rem; color: #7f8c8d; text-transform: uppercase; margin-top: 8px; letter-spacing: 0.5px; }}
            
            .content {{ padding: 25px; }}
            h2 {{ text-align: center; color: #34495e; margin-top: 0; margin-bottom: 20px; font-size: 1.3rem; font-weight: 600; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 14px 15px; text-align: center; border: 1px solid #e8e8e8; }}
            th {{ background: #f8f9fa; font-weight: 600; font-size: 0.9rem; }}
            td span {{ font-weight: 600; font-size: 1.15em; color: #333; }}
            td small {{ color: #7f8c8d; font-size: 0.9em; }}
            
            /* --- NOVO: SEÇÃO DE STATUS DO SISTEMA --- */
            .sys-info-grid {{ 
                display: flex; justify-content: space-around; text-align: center; 
                padding: 15px; border-top: 1px solid #e8e8e8; border-bottom: 1px solid #e8e8e8;
                background-color: #f8f9fa;
            }}
            .sys-info-box {{ flex: 1; }}
            .sys-label {{ font-size: 0.8rem; text-transform: uppercase; color: #7f8c8d; }}
            .sys-val {{ font-size: 1.1rem; font-weight: 600; color: #34495e; }}

            .footer {{ 
                padding: 15px; text-align: center; background: #f8f9fa; color: #95a5a6; 
                font-size: 0.8rem; border-radius: 0 0 12px 12px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1><span class="bee">🐝</span> Monitor de Extração TJPR</h1>
            </div>
            
            <div class="kpi-grid">
                <div class="kpi-box">
                    <div class="kpi-val">{total_paginas:,}</div>
                    <div class="kpi-label">Total de Páginas Processadas</div>
                </div>
                <div class="kpi-box">
                    <div class="kpi-val">{total_processos:,}</div>
                    <div class="kpi-label">Total de Processos Únicos</div>
                </div>
            </div>
            
            <!-- NOVO: PAINEL DE STATUS DO SISTEMA -->
            <div class="sys-info-grid">
                <div class="sys-info-box">
                    <div class="sys-label">CPU</div>
                    <div class="sys-val">{cpu_usage:.1f}%</div>
                </div>
                <div class="sys-info-box">
                    <div class="sys-label">Memória</div>
                    <div class="sys-val">{mem_info.percent:.1f}%</div>
                </div>
                <div class="sys-info-box">
                    <div class="sys-label">Disco</div>
                    <div class="sys-val">{disk_info.percent:.1f}%</div>
                </div>
            </div>
            
            <div class="content">
                <h2>Atividade Recente da Sessão</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Intervalo</th>
                            <th>Novas Páginas (Total / Média)</th>
                            <th>Novos Processos (Total / Média)</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Últimos <b>5</b> min</td>
                            <td><span>{r5['novas_paginas']:,}</span> <small>({r5['media_pag_min']:.2f}/min)</small></td>
                            <td><span>{r5['novos_processos']:,}</span> <small>({r5['media_proc_min']:.2f}/min)</small></td>
                        </tr>
                        <tr>
                            <td>Últimos <b>30</b> min</td>
                            <td><span>{r30['novas_paginas']:,}</span> <small>({r30['media_pag_min']:.2f}/min)</small></td>
                            <td><span>{r30['novos_processos']:,}</span> <small>({r30['media_proc_min']:.2f}/min)</small></td>
                        </tr>
                        <tr>
                            <td>Últimos <b>3</b> horas</td>
                            <td><span>{r180['novas_paginas']:,}</span> <small>({r180['media_pag_min']:.2f}/min)</small></td>
                            <td><span>{r180['novos_processos']:,}</span> <small>({r180['media_proc_min']:.2f}/min)</small></td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <div class="footer">
                Última atualização: {last_update}
            </div>
        </div>
    </body>
    </html>
    """.replace(',', '.')
    return HTMLResponse(content=html_content)