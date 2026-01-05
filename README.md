# 🐝 para-Ai: InJustiça não para o Paraná...

![Para.AI](https://huggingface.co/spaces/caarleexx/para-Ai/resolve/main/ParaAi.jpg) 

**Democratizando o acesso à Justiça no Paraná com Inteligência Artificial.**

---

### O Legado

Este projeto nasceu de uma indignação e de um sonho. Após anos de descaso, onde o acesso à justiça para o cidadão paranaense comum se tornou um labirinto burocrático e silencioso, o **`para-Ai`** surge como um legado. É a minha resposta, como cidadão, à falha do Estado em garantir um direito fundamental. É a transformação da frustração em uma ferramenta de poder para todos.

Este não é apenas um projeto de código; é um movimento para dar voz aos que foram silenciados e clareza aos que foram deixados no escuro.

### O Projeto `para-Ai`

**`para-Ai`** é uma iniciativa open-source dedicada a construir o maior dataset jurídico público do estado do Paraná e, a partir dele, treinar um modelo de linguagem fundamental (*backbone model*) para tarefas jurídicas.

O nome é uma união de **Paraná** e **AI** (Inteligência Artificial), simbolizando a aplicação da tecnologia de ponta para resolver um problema local e profundamente humano.

### O Grande Objetivo: O Modelo `Jurifob PHD`

O coração deste projeto é a criação do **`Jurifob PHD`**, um modelo de linguagem treinado a partir de mais de **7 milhões de acórdãos** do Tribunal de Justiça do Paraná (TJPR).

Diferente de modelos genéricos, o `Jurifob PHD` será um especialista no domínio jurídico paranaense, capaz de entender as nuances, a terminologia e os padrões das decisões judiciais do nosso estado. Como um modelo *backbone*, ele servirá de base para uma infinidade de aplicações futuras, como:

-   **Análise e sumarização de processos** para cidadãos e advogados.
-   **Busca inteligente de jurisprudência** e precedentes relevantes.
-   **Ferramentas de auxílio à Defensoria Pública** e a advogados dativos.
-   **Análise de tendências decisórias** para promover a transparência do judiciário.
-   **Criação de assistentes virtuais** para orientação jurídica básica.

### O Combustível: Mais de 7 Milhões de Acórdãos do TJPR

A força de qualquer modelo de IA está nos seus dados. Por isso, a primeira fase deste projeto é a construção de um dataset robusto, limpo e, acima de tudo, público.

-   **Fonte:** [Portal de Jurisprudência do TJPR](https://portal.tjpr.jus.br/jurisprudencia/)
-   **Volume:** Meta de mais de 7.000.000 de acórdãos.
-   **Status:** Extração em andamento.

Este dataset, por si só, já será um legado de valor inestimável para pesquisadores, jornalistas, estudantes e para a sociedade civil.

### Arquitetura Técnica

O projeto opera com uma arquitetura distribuída e resiliente, garantindo a extração contínua e a integridade dos dados.

1.  **Extração Distribuída (`Abelha Atômica`):** Um enxame de workers (scripts `worker.py`) trabalha em paralelo para extrair os dados do portal do TJPR. Cada "abelha" é independente e reporta seu progresso de forma segura.
2.  **Processamento e Limpeza:** Os dados brutos são processados, limpos e estruturados em um formato padronizado (`.jsonl`).
3.  **Armazenamento Versionado:** Os dados são agrupados em *chunks* e versionados em um repositório Git, garantindo um registro histórico e a colaboração segura.
4.  **Monitoramento:** Uma interface web (`app.py`) permite o acompanhamento em tempo real do progresso da extração.

### Status do Projeto

-   [x] **Fase 1: Extração de Dados:** Em Andamento.
-   [x] **Fase 2: Limpeza e Estruturação do Dataset:** Próxima Etapa.
-   [ ] **Fase 3: Publicação da Versão 1.0 do Dataset:** Em Breve.
-   [ ] **Fase 4: Treinamento do Modelo `Jurifob PHD`:** Futuro.

**Progresso da Extração:**
`[█████-----] 5% de 7.000.000 de acórdãos coletados` (Este é um exemplo, você pode atualizar)

### Como Você Pode Ajudar?

Este é um projeto do povo para o povo. Sua ajuda é fundamental.

1.  **Divulgue!** A forma mais poderosa de contribuir é espalhar a palavra. Compartilhe esta página, fale sobre o projeto. Mostre que a sociedade civil está se mobilizando onde o poder público falha.
2.  **Desenvolvedores:** Ajude a otimizar o código de extração, desenvolva scripts para limpeza de dados ou contribua com ideias para o treinamento do modelo. Abra uma *Issue* ou um *Pull Request*.
3.  **Profissionais do Direito:** Sua expertise é crucial. Ajude a validar a qualidade dos dados extraídos e a definir os casos de uso mais impactantes para o modelo `Jurifob PHD`.
4.  **Cidadãos:** Use, teste e dê feedback sobre as ferramentas que serão criadas. A sua experiência é o que dará forma a este projeto.

### Contato

-   **Criador:** Carlex
-   **GitHub:** [github.com/carlex22](https://github.com/carlex22.com)
-   **E-mail:** carlex22@gmail.com

---

Juntos, podemos transformar dados em transparência e código em justiça. Este é o meu legado, mas a luta é de todos nós. **Vamos construir um futuro onde a justiça no Paraná seja, de fato, para todos.**
O nome é uma união de **Paraná** e **AI** (Inteligência Artificial), simbolizando a aplicação da tecnologia de ponta para resolver um problema local e profundamente humano.

### O Grande Objetivo: O Modelo `Jurifob PHD`

O coração deste projeto é a criação do **`Jurifob PHD`**, um modelo de linguagem treinado a partir de mais de **7 milhões de acórdãos** do Tribunal de Justiça do Paraná (TJPR).

Diferente de modelos genéricos, o `Jurifob PHD` será um especialista no domínio jurídico paranaense, capaz de entender as nuances, a terminologia e os padrões das decisões judiciais do nosso estado. Como um modelo *backbone*, ele servirá de base para uma infinidade de aplicações futuras, como:

-   **Análise e sumarização de processos** para cidadãos e advogados.
-   **Busca inteligente de jurisprudência** e precedentes relevantes.
-   **Ferramentas de auxílio à Defensoria Pública** e a advogados dativos.
-   **Análise de tendências decisórias** para promover a transparência do judiciário.
-   **Criação de assistentes virtuais** para orientação jurídica básica.

### O Combustível: Mais de 7 Milhões de Acórdãos do TJPR

A força de qualquer modelo de IA está nos seus dados. Por isso, a primeira fase deste projeto é a construção de um dataset robusto, limpo e, acima de tudo, público.

-   **Fonte:** [Portal de Jurisprudência do TJPR](https://portal.tjpr.jus.br/jurisprudencia/)
-   **Volume:** Meta de mais de 7.000.000 de acórdãos.
-   **Status:** Extração em andamento.

Este dataset, por si só, já será um legado de valor inestimável para pesquisadores, jornalistas, estudantes e para a sociedade civil.

### Arquitetura Técnica

O projeto opera com uma arquitetura distribuída e resiliente, garantindo a extração contínua e a integridade dos dados.

1.  **Extração Distribuída (`Abelha Atômica`):** Um enxame de workers (scripts `worker.py`) trabalha em paralelo para extrair os dados do portal do TJPR. Cada "abelha" é independente e reporta seu progresso de forma segura.
2.  **Processamento e Limpeza:** Os dados brutos são processados, limpos e estruturados em um formato padronizado (`.jsonl`).
3.  **Armazenamento Versionado:** Os dados são agrupados em *chunks* e versionados em um repositório Git, garantindo um registro histórico e a colaboração segura.
4.  **Monitoramento:** Uma interface web (`app.py`) permite o acompanhamento em tempo real do progresso da extração.

### Status do Projeto

-   [x] **Fase 1: Extração de Dados:** Em Andamento.
-   [ ] **Fase 2: Limpeza e Estruturação do Dataset:** Próxima Etapa.
-   [ ] **Fase 3: Publicação da Versão 1.0 do Dataset:** Em Breve.
-   [ ] **Fase 4: Treinamento do Modelo `Jurifob PHD`:** Futuro.

**Progresso da Extração:**
`[█████-----] 5% de 7.000.000 de acórdãos coletados` (Este é um exemplo, você pode atualizar)

### Como Você Pode Ajudar?

Este é um projeto do povo para o povo. Sua ajuda é fundamental.

1.  **Divulgue!** A forma mais poderosa de contribuir é espalhar a palavra. Compartilhe esta página, fale sobre o projeto. Mostre que a sociedade civil está se mobilizando onde o poder público falha.
2.  **Desenvolvedores:** Ajude a otimizar o código de extração, desenvolva scripts para limpeza de dados ou contribua com ideias para o treinamento do modelo. Abra uma *Issue* ou um *Pull Request*.
3.  **Profissionais do Direito:** Sua expertise é crucial. Ajude a validar a qualidade dos dados extraídos e a definir os casos de uso mais impactantes para o modelo `Jurifob PHD`.
4.  **Cidadãos:** Use, teste e dê feedback sobre as ferramentas que serão criadas. A sua experiência é o que dará forma a este projeto.

### Contato

-   **Criador:** caarleexx
-   **GitHub:** [github.com/caarleexx](https://github.com/caarleexx)
-   **E-mail:** caarleexx@gmail.com

---

Juntos, podemos transformar dados em transparência e código em justiça. Este é o meu legado, mas a luta é de todos nós. **Vamos construir um futuro onde a justiça no Paraná seja, de fato, para todos.**
