# Padrões de busca para segurança (modo com código)

Apoio para o agente de Segurança. São pontos de partida para `grep`/`rg`: todo resultado precisa ser lido no contexto antes de virar achado. Muitos são falsos positivos (valor vindo do servidor, framework que já escapa).

Base: Prompt 1, Prompt 2, getsentry/security-review, addyosmani/security-and-hardening, trailofbits/insecure-defaults.

## 1. Detectar a stack primeiro

| Sinal | Stack |
|---|---|
| `package.json` com `next` / `nuxt` / `@sveltejs/kit` / `astro` / `express` / `fastify` / `@nestjs` | Node |
| `requirements.txt`, `pyproject.toml` com `django` / `flask` / `fastapi` | Python |
| `go.mod` | Go |
| `composer.json`, `wp-config.php` | PHP / WordPress |
| `supabase/`, `@supabase/supabase-js` | Supabase (isolamento via RLS) |
| `firebase.json`, `firestore.rules` | Firebase (isolamento via rules) |
| `prisma/schema.prisma`, `drizzle`, `typeorm`, `sequelize`, `gorm`, `sqlc` | ORM / query builder |

Antes de procurar IDOR e isolamento, descubra **qual é o mecanismo de isolamento** do projeto (RLS, middleware de tenant, filtro manual por `user_id`/`org_id`) e procure onde ele falta.

## 2. Segredos (bundle do navegador e código)

O script de coleta já varre o JavaScript público com estes padrões. No código, rode também no histórico: `git log -p --all -S '<prefixo>'`.

| Padrão (regex) | O que é | Severidade se real |
|---|---|---|
| `AKIA[0-9A-Z]{16}` | Chave AWS | critica |
| `sk_live_[0-9a-zA-Z]{24,}` | Stripe secreta (produção) | critica |
| `rk_live_[0-9a-zA-Z]{24,}` | Stripe restrita | alta |
| `sk-ant-[A-Za-z0-9_-]{20,}` | Anthropic | critica |
| `sk-(proj-)?[A-Za-z0-9_-]{32,}` | OpenAI | critica |
| `ghp_[A-Za-z0-9]{36}`, `github_pat_` | GitHub | critica |
| `xox[baprs]-[A-Za-z0-9-]{10,}` | Slack | alta |
| `-----BEGIN (RSA \|EC \|OPENSSH )?PRIVATE KEY-----` | Chave privada | critica |
| JWT `eyJ...` cujo payload tem `"role":"service_role"` | Supabase service role | critica |
| `AIza[0-9A-Za-z_-]{35}` | Chave Google | info (chaves de Maps/Firebase são públicas por desenho; vira achado só se a API não tiver restrição de domínio) |
| `pk_live_`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Chaves públicas por desenho | não é achado sozinho; se for Supabase, cheque RLS |

Arquivos para olhar: `.env*` versionados, `docker-compose*.yml`, `.github/workflows/*`, `*.tf`, `values*.yaml`, `config/*`, `README*`.

## 3. Defaults inseguros (trailofbits/insecure-defaults)

| Categoria | Exemplo vulnerável | Quando NÃO é achado |
|---|---|---|
| Segredo com valor padrão | `SECRET = os.getenv("JWT_SECRET", "dev")`, `${JWT_SECRET:-changeme}`, `process.env.KEY \|\| "secret"` | Quando a aplicação falha ao subir sem a variável |
| Credencial padrão | seed com `admin`/`admin123` | Seed usado só em teste e fora do build de produção |
| Fail-open | `REQUIRE_AUTH = getenv("REQUIRE_AUTH", "false")` | Default seguro (`true`) |
| Cripto fraca | `md5(password)`, `sha1(password)`, senha sem hash | Hash de arquivo/cache, não senha |
| Acesso permissivo | `Access-Control-Allow-Origin: *` com credenciais, bucket `public-read`, `chmod 0o777` | CORS `*` em API pública sem cookie |
| Debug ligado | `DEBUG=True`, stack trace na resposta, `app.run(debug=True)` | Só em arquivo de desenvolvimento |

## 4. Autorização (Prompt 2, itens 1 a 3)

Percorra **todos** os handlers de rota, não amostras.

| Stack | Onde estão as rotas |
|---|---|
| Next.js | `app/**/route.ts`, `pages/api/**`, server actions (`"use server"`) |
| Express/Fastify | `router.get/post/put/delete(`, `app.get(` |
| NestJS | `@Get(`, `@Post(` em `*.controller.ts` |
| Django/DRF | `urls.py`, `views.py`, `ViewSet` |
| FastAPI | `@app.get(`, `@router.post(` |
| Go | `http.HandleFunc`, `r.Get(` (chi), `e.GET(` (echo), `gin` |

Para cada handler que recebe um ID (path, query ou body):
1. Ele busca o objeto filtrando pelo usuário/tenant da sessão? (`where: { id, userId: session.user.id }`)
2. Se busca só por ID, há checagem de dono depois?
3. Listagens, buscas, relatórios e exportações filtram pelo tenant?

Permissão só no front: procure `isAdmin`, `role ===`, `canEdit`, `hasPermission` em componentes e confirme que a rota chamada por aquele botão checa o mesmo privilégio no servidor.

Supabase: tabelas sem `enable row level security`, policies com `using (true)`, uso de `service_role` em código que roda no cliente.

## 5. XSS e injeção

| Onde | Padrão |
|---|---|
| React | `dangerouslySetInnerHTML` |
| Vue | `v-html` |
| Angular | `[innerHTML]`, `bypassSecurityTrust` |
| Svelte | `{@html` |
| DOM | `innerHTML =`, `outerHTML =`, `document.write(`, `insertAdjacentHTML(` |
| Geral | `eval(`, `new Function(`, `setTimeout("` com string |
| Links | `href={` com valor do usuário sem validar protocolo (`javascript:`) |
| Markdown | `marked(`, `markdown-it` com `html: true` sem `DOMPurify` |
| SQL | template string ou concatenação em `query(`, `raw(`, `$queryRawUnsafe`, `execute(f"` |
| Comando | `exec(`, `execSync(`, `child_process`, `subprocess` com `shell=True`, `os.system(` |

Confira se o projeto tem biblioteca de sanitização (`dompurify`, `sanitize-html`, `bleach`) e se ela é usada nesses pontos.

## 6. Webhooks e IA

- Webhook (Stripe, Mercado Pago, Asaas, GitHub): procure a verificação de assinatura (`constructEvent`, `x-signature`, HMAC). Sem ela, qualquer um forja pagamento confirmado.
- Endpoints que chamam IA (`openai`, `anthropic`, `generateText`, `chat.completions`): a chave fica só no servidor? Há rate limit por usuário/IP? Há limite de tokens? O system prompt vai para o cliente?

## 7. Checagens passivas em produção (modo URL)

Feitas pelo script de coleta. O agente só interpreta:

- `coleta/http/headers.json`: headers de segurança e cookies.
- `coleta/http/exposicao.json`: `/.env`, `/.git/HEAD`, backups, listagem de diretório, source maps.
- `coleta/http/segredos-bundle.json`: padrões da seção 2 encontrados no JavaScript público.
- `coleta/http/cors.json`: resposta a `Origin` arbitrário.
