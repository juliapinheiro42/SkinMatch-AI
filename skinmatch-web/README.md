# SkinMatch AI Web

Frontend MVP da Fase 6 do SkinMatch AI. A aplicacao permite preencher o perfil de pele, colar uma formula INCI ou enviar foto do rotulo, salvar historico, registrar feedback pos-uso, visualizar insights pessoais, navegar por produtos similares, buscar alternativas mais compativeis e gerar uma rotina manha/noite.

## Requisitos

- Node.js 20+
- Backend `skinmatch-api` rodando em `http://localhost:8000`

## Instalar dependencias

```bash
npm install
```

## Configurar ambiente

Crie um arquivo `.env.local` com:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

O arquivo `.env.example` ja contem o valor esperado para desenvolvimento local.

## Rodar localmente

```bash
npm run dev
```

Acesse:

```text
http://localhost:3000
```

Rotas disponiveis:

```text
/           Nova analise
/history    Historico de analises salvas
/history/id Detalhe da analise e formulario de feedback
/insights   Insights pessoais baseados em feedbacks
/agent      Chat com agente SkinMatch
/catalog    Dashboard simples do catalogo de produtos
/products/id/similar Produtos com formulas similares
```

## Exemplo de uso

1. Inicie o backend da Fase 1:

```bash
cd ../skinmatch-api
docker compose up --build
```

2. Inicie o frontend:

```bash
cd ../skinmatch-web
npm install
npm run dev
```

3. Preencha o perfil de pele, cole uma formula como:

```text
Aqua, Glycerin, Niacinamide, Salicylic Acid, Alcohol Denat., Parfum
```

4. Envie para visualizar score, riscos, beneficios, pontos positivos, alertas e ingredientes nao reconhecidos.
5. Ou envie uma foto do rotulo para preencher a formula via OCR.
6. Acesse `/history` para ver a analise salva.
7. Abra o detalhe, registre feedback pos-uso e salve.
8. Acesse `/insights` para conferir gatilhos possiveis, ingredientes bem tolerados e padroes detectados.
9. No resultado, use "Ver produtos similares" para abrir `/products/[id]/similar`.
10. No card de recomendacoes, clique em "Ver alternativas melhores" para chamar `/recommendations` usando o mesmo perfil e objetivo da analise.
11. Clique em "Gerar rotina completa" para chamar `/routines/generate`.
12. Acesse `/agent` para conversar com o agente e passar contexto opcional de produto.
13. Acesse `/catalog` para ver produtos cadastrados e filtrar por categoria, etapa, tag, preco ou tratamento ativo.

## Recomendacoes

O componente `Recommendations` aparece apos uma analise bem-sucedida e envia:

```ts
{
  skin_profile,
  main_goal,
  exclude_ingredients: skin_profile.known_triggers,
  limit: 5
}
```

Ele mostra nome, marca, score, motivo deterministico, ingredientes-chave e o botao "Analisar este produto".

## Rotina

O componente `RoutineView` aparece depois de gerar a rotina e separa:

```text
Manha
Noite
Cuidados importantes
```

Cada passo mostra numero, tipo, produto, instrucao e motivo. A interface reforca "Comece devagar" e exibe warnings retornados pelo backend.

## Agente

A rota `/agent` exibe:

```text
Chat simples
Contexto opcional de produto
Sugestoes rapidas
Ferramentas usadas
Confianca da resposta
Dados faltantes
Follow-up sugerido
Resumo de score quando houver analise
```

O frontend chama `POST /agent/chat` com:

```ts
{
  user_id,
  message,
  context: {
    product_name,
    brand,
    raw_ingredient_list,
    skin_profile,
    main_goal
  }
}
```

O prompt interno nao e exposto no frontend. A resposta mostra o texto do agente, confianca, dados faltantes, tools usadas, follow-up sugerido e cards estruturados quando `structured_result` contem `compatibility_score` ou rotina.

## Catalogo

A rota `/catalog` chama `GET /catalog/products` e mostra:

```text
nome
marca
categoria
etapa de rotina
periodos de uso
faixa de preco
tags
status
```

Filtros disponiveis:

- categoria
- etapa da rotina
- tag
- faixa de preco
- tratamento ativo

## Testar feedback e insights

Fluxo manual recomendado:

1. Crie uma analise com `Parfum` ou `Fragrance` na formula.
2. Em `/history`, abra o detalhe da analise.
3. Registre feedback com `irritation_level` 3 ou maior.
4. Abra `/insights` e verifique se fragrance aparece como possivel gatilho.
5. Rode uma nova analise com fragrance e confira se a regra `RULE_008` aparece nos sinais considerados.

## Observacao

Esta interface nao implementa autenticacao, pagamento ou banco no frontend. O agente usa LLM apenas no backend quando `OPENAI_API_KEY` esta configurada; sem chave, usa fallback deterministico. A analise exibida e uma estimativa educacional e depende do backend estar rodando.
