# SkinMatch AI API

Backend MVP deterministico para analisar formulas INCI de skincare e estimar compatibilidade com um perfil de pele. Esta versao nao usa LLM, nao possui frontend e nao implementa autenticacao.

## Stack

- Python 3.11
- FastAPI
- Pydantic
- SQLAlchemy ORM classico
- PostgreSQL
- Alembic
- pgvector
- Tesseract OCR
- Docker
- Pytest

## Como rodar

```bash
docker-compose up --build
```

A API ficara disponivel em:

```text
http://localhost:8000
```

Health check:

```bash
curl http://localhost:8000/health
```

## Como testar

Com dependencias instaladas localmente e PostgreSQL disponivel:

```bash
pytest
```

Para rodar a API localmente com o banco do Docker:

```bash
docker-compose up db
python -m uvicorn app.main:app --reload
```

O banco do projeto fica exposto em `localhost:5433` para evitar conflito com PostgreSQL local na porta `5432`.

O `docker-compose.yml` usa a imagem `pgvector/pgvector:pg16`, que ja permite habilitar a extensao `vector`.
O Dockerfile instala `tesseract-ocr` para o endpoint de OCR.

Tambem e possivel testar dentro do container:

```bash
docker-compose run --rm api pytest
```

## Migrations

O MVP ainda chama `Base.metadata.create_all` ao subir a API para facilitar desenvolvimento local. A Fase 3 tambem inclui Alembic para versionar as tabelas novas:

```bash
alembic upgrade head
```

Migration criada:

```text
alembic/versions/20260503_0001_phase3_history_feedback.py
alembic/versions/20260503_0002_phase4_products_ocr_vectors.py
```

Para pgvector:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

A migration da Fase 4 executa esse comando automaticamente.

## Exemplo de request

```bash
curl -X POST http://localhost:8000/analysis \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Serum Antiacne X",
    "brand": "Marca Y",
    "main_goal": "acne",
    "raw_ingredient_list": "Aqua, Glycerin, Niacinamide, Parfum, BHA, Ceramide",
    "skin_profile": {
      "skin_type": "oily",
      "sensitive_skin": true,
      "acne_prone": true,
      "barrier_compromised": false,
      "known_triggers": ["fragrance"],
      "tolerated_ingredients": ["salicylic acid"]
    }
  }'
```

Resposta esperada:

```json
{
  "analysis_id": "11111111-1111-1111-1111-111111111111",
  "compatibility_score": 68,
  "verdict": "caution",
  "irritation_risk": 0.8,
  "acne_risk": 0.02,
  "benefit_score": 1.0,
  "barrier_support": 1.0,
  "applied_rules": ["RULE_001", "RULE_003", "RULE_005", "RULE_006", "RULE_007"],
  "positive_ingredients": ["ceramide", "glycerin", "niacinamide", "salicylic acid"],
  "warning_ingredients": ["fragrance"],
  "unknown_ingredients": ["aqua"],
  "parsed_ingredients": [],
  "recommendation": "Formula has useful ingredients but also some cautions. Patch testing is recommended.",
  "disclaimer": "This deterministic analysis is informational and does not replace medical advice."
}
```

## Historico

Toda chamada para `POST /analysis` salva automaticamente um registro para o usuario temporario:

```text
00000000-0000-0000-0000-000000000001
```

Listar historico:

```bash
curl "http://localhost:8000/analysis/history?limit=20&offset=0"
```

Filtros opcionais:

```bash
curl "http://localhost:8000/analysis/history?verdict=caution&main_goal=acne"
```

Detalhe:

```bash
curl http://localhost:8000/analysis/{analysis_id}
```

## Feedback pos-uso

Criar ou atualizar feedback de uma analise:

```bash
curl -X POST http://localhost:8000/analysis/{analysis_id}/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "used_product": true,
    "usage_days": 14,
    "usage_frequency": "3x_per_week",
    "irritation_level": 3,
    "acne_level": 1,
    "dryness_level": 2,
    "satisfaction_level": 4,
    "noticed_benefits": ["less_oiliness", "less_acne"],
    "would_buy_again": true,
    "comments": "Funcionou, mas ardeu um pouco nos primeiros dias."
  }'
```

Uma analise possui apenas um feedback no MVP. Se o endpoint for chamado novamente, o feedback existente sera atualizado.

## Insights pessoais

```bash
curl http://localhost:8000/insights/personal
```

O resumo usa feedbacks salvos:

- `irritation_level >= 3` conta ingredientes da formula como possiveis gatilhos.
- `satisfaction_level >= 4` e `irritation_level <= 1` conta ingredientes como bem tolerados.
- `RULE_008` aumenta risco de irritacao para gatilhos pessoais.
- `RULE_009` reduz risco de irritacao e aumenta beneficio para ingredientes bem tolerados.

## Produtos e cache de formulas

Na Fase 4, toda analise:

1. normaliza a formula
2. gera `formula_hash`
3. busca ou cria um registro em `products`
4. salva o snapshot em `product_formulas`
5. busca ou cria cache em `formula_analysis_cache`
6. salva `product_id` em `analysis_records`

Formulas identicas reutilizam o mesmo produto e o mesmo cache base.

## OCR de rotulo

Endpoint:

```bash
curl -X POST http://localhost:8000/formulas/ocr \
  -F "image=@rotulo.jpg"
```

Resposta:

```json
{
  "extracted_text": "INGREDIENTS: Aqua, Glycerin, Niacinamide",
  "cleaned_ingredient_list": "Aqua, Glycerin, Niacinamide"
}
```

Se o OCR nao encontrar uma secao clara de ingredientes, o backend retorna o texto bruto como fallback.

## Similaridade de produtos

Endpoint:

```bash
curl http://localhost:8000/products/{product_id}/similar
```

Resposta:

```json
[
  {
    "product_id": "22222222-2222-2222-2222-222222222222",
    "name": "Serum Antiacne X",
    "brand": "Marca Y",
    "similarity": 0.87
  }
]
```

Embeddings:

- Usa `OPENAI_API_KEY` quando disponivel.
- Modelo padrao: `text-embedding-3-small`.
- Sem chave, usa embedding deterministico local para manter o fluxo testavel.
- A documentacao oficial da OpenAI descreve `text-embedding-3-small` com vetor padrao de 1536 dimensoes e recomenda cosine similarity para busca vetorial.

## Recomendacoes

Endpoint:

```bash
curl -X POST http://localhost:8000/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "skin_profile": {
      "skin_type": "oily",
      "sensitive_skin": true,
      "acne_prone": true,
      "barrier_compromised": true,
      "known_triggers": ["fragrance"],
      "tolerated_ingredients": ["niacinamide"]
    },
    "main_goal": "acne",
    "exclude_ingredients": ["fragrance"],
    "limit": 5
  }'
```

Resposta:

```json
[
  {
    "product_id": "22222222-2222-2222-2222-222222222222",
    "name": "Gel Antiacne X",
    "brand": "Marca Y",
    "compatibility_score": 82,
    "irritation_risk": 20,
    "acne_risk": 15,
    "benefit_score": 78,
    "reason": "Alta compatibilidade com seu perfil e baixo risco de irritacao",
    "key_ingredients": ["salicylic acid", "niacinamide"]
  }
]
```

Regras:

- Trabalha apenas com produtos ja existentes no banco.
- Remove produtos com ingredientes em `exclude_ingredients`.
- Remove produtos com ingredientes em `known_triggers`.
- Remove produtos com `irritation_risk > 85`.
- Analisa no maximo 100 produtos por chamada e retorna o top `limit`.
- Nao usa LLM nem APIs externas de catalogo.

## Rotinas

Endpoint:

```bash
curl -X POST http://localhost:8000/routines/generate \
  -H "Content-Type: application/json" \
  -d '{
    "skin_profile": {
      "skin_type": "oily",
      "sensitive_skin": true,
      "acne_prone": true,
      "barrier_compromised": true,
      "known_triggers": ["fragrance"],
      "tolerated_ingredients": ["niacinamide"]
    },
    "main_goal": "acne",
    "constraints": {
      "avoid_ingredients": ["fragrance"],
      "max_steps": 5
    }
  }'
```

Resposta:

```json
{
  "morning_routine": [
    {
      "step": 1,
      "type": "cleanser",
      "product": {
        "id": "22222222-2222-2222-2222-222222222222",
        "name": "Gel de Limpeza",
        "brand": "Marca Y"
      },
      "instructions": "Use uma pequena quantidade e enxague com agua morna.",
      "reason": "Ajuda a remover oleosidade e residuos sem adicionar muitos ativos."
    }
  ],
  "night_routine": [],
  "warnings": [
    "Introduza novos produtos gradualmente.",
    "Faca teste de contato antes de usar uma rotina nova no rosto todo."
  ]
}
```

Logica:

- Usa produtos ja recomendaveis pela Fase 5.
- Classifica produto por funcao inferida da formula/nome.
- Respeita `constraints.max_steps`.
- Manha segue ordem: limpeza, hidratante, protetor solar.
- Noite segue ordem: limpeza, tratamento, hidratante.
- Evita retinol junto com AHA/BHA na mesma rotina.
- Para pele sensivel, reduz agressividade e prioriza menor risco.
- Nao usa LLM e nao substitui orientacao medica.

## Agente conversacional

Configure a chave da OpenAI se quiser respostas geradas por LLM:

```env
OPENAI_API_KEY=sk-...
AGENT_MODEL=gpt-4o-mini
```

Sem `OPENAI_API_KEY`, o agente usa classificacao de intencao por regras e respostas deterministicas. As ferramentas internas continuam funcionando.

Endpoint:

```bash
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "00000000-0000-0000-0000-000000000001",
    "message": "Esse produto pode dar acne em mim?",
    "context": {
      "product_name": "Serum Antiacne X",
      "brand": "Marca Y",
      "raw_ingredient_list": "Aqua, Glycerin, Niacinamide, Salicylic Acid, Alcohol Denat., Parfum",
      "main_goal": "acne",
      "skin_profile": {
        "skin_type": "oily",
        "sensitive_skin": true,
        "acne_prone": true,
        "barrier_compromised": false,
        "known_triggers": ["fragrance"],
        "tolerated_ingredients": ["niacinamide"]
      }
    }
  }'
```

Resposta:

```json
{
  "answer": "Com base na ferramenta de analise...",
  "intent": "analyze_product",
  "tools_used": ["analyze_product"],
  "structured_result": {
    "compatibility_score": 58,
    "verdict": "caution"
  },
  "safety_disclaimer": "Esta resposta e uma estimativa educacional e nao substitui orientacao medica ou dermatologica."
}
```

Arquitetura:

- `agent/service.py` detecta intencao, aplica guardrails, chama tools e gera a resposta.
- `agent/tools.py` encapsula analise, recomendacoes, rotina, insights e historico.
- `agent/context_builder.py` monta contexto com perfil, insights, ultimas analises, feedbacks, reacoes recentes e resumo da conversa.
- `agent/planner.py` decide intencao, confianca, dados faltantes, tools necessarias e pergunta de esclarecimento.
- `agent/response_templates.py` renderiza respostas orientadas a acao por tipo de intencao.
- `agent/quality.py` valida disclaimer, ausencia de diagnostico, uso correto de tools e proximo passo pratico.
- `agent/memory.py` salva mensagens em `agent_messages`.
- A LLM nunca calcula score sozinha; ela apenas explica resultados estruturados das tools.
- Se faltar formula para pergunta sobre produto, o agente pede a lista INCI ou imagem do rotulo.

Migration:

```bash
alembic upgrade head
```

A migration `20260503_0003_phase7_agent_messages.py` cria a tabela `agent_messages`.
A migration `20260503_0005_agent_context_planning.py` adiciona `confidence` e `user_context_snapshot` na memoria do agente.

Seguranca:

- Mensagens com sinais como `rosto inchado`, `queimadura`, `falta de ar`, `ferida aberta` ou `dor intensa` acionam resposta segura imediata.
- O agente nao diagnostica doencas e nao substitui dermatologista.

## Catalogo de produtos

A Fase 8 expande `products` com metadados usados por recomendacoes e rotinas:

```text
category, routine_step, usage_periods, price_range, tags,
is_active_treatment, is_sunscreen, is_moisturizer, is_cleanser,
source, source_url, catalog_status
```

Migration:

```bash
alembic upgrade head
```

A migration `20260503_0004_phase8_catalog_fields.py` adiciona os campos ao banco. No ambiente de desenvolvimento, o startup tambem garante as colunas com `ALTER TABLE IF NOT EXISTS`.

Importar CSV:

```bash
curl -X POST http://localhost:8000/catalog/import-csv \
  -H "Content-Type: text/csv" \
  --data-binary @catalog.csv
```

Colunas aceitas:

```text
name, brand, category, routine_step, usage_periods, price_range, raw_ingredient_list, tags, source
```

Exemplo:

```csv
name,brand,category,routine_step,usage_periods,price_range,raw_ingredient_list,tags,source
Gel Limpeza Suave,Marca X,cleanser,cleanser,morning;night,mid,"Aqua, Glycerin, Decyl Glucoside",cleanser;gentle,manual
```

Listar produtos:

```bash
curl "http://localhost:8000/catalog/products?category=sunscreen"
```

Filtros:

- `category`
- `routine_step`
- `tag`
- `price_range`
- `is_active_treatment`

Seed inicial:

- 10 cleansers
- 10 moisturizers
- 10 sunscreens
- 10 tratamentos de acne
- 10 produtos de reparo de barreira

As rotinas agora priorizam `routine_step` e flags de catalogo antes de inferir tipo pela formula. Uma rotina completa de manha precisa conter `cleanser`, `moisturizer` e `sunscreen`; tratamento entra conforme objetivo e disponibilidade.
