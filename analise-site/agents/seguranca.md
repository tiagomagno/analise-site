# Agente: Segurança

Segmento `seguranca` · prefixo `SEG` · linhas 01.xx da matriz de referência

## Missão

Encontrar falhas de segurança reais e exploráveis no site e, se houver código, na aplicação. Cada achado com evidência. Registrar também o que está protegido.

## Leia antes

1. `references/regras-comuns.md`
2. `references/padroes-seguranca.md`
3. `escopo.json` (modo da análise, se há código, se há login)

## Fontes na coleta

| Arquivo | Para quê |
|---|---|
| `coleta/http/headers.json` | headers de segurança, cookies do servidor |
| `coleta/http/exposicao.json` | arquivos sensíveis e listagem de diretório (`exposto: true`) |
| `coleta/http/segredos-bundle.json` | padrões de segredo no JavaScript público (valores já mascarados) |
| `coleta/http/source-maps.json` | source maps públicos |
| `coleta/http/cors.json` | resposta a Origin externo |
| `coleta/http/redirects.json` | HTTP → HTTPS |
| `coleta/privacidade/consentimento.json` | atributos dos cookies no navegador |
| `coleta/paginas/*/dados.json` | formulários, scripts de terceiros, links `javascript:` |
| `coleta/stack.json` | tecnologias detectadas |
| Código do projeto (se `escopo.codigo` existir) | checagens de código |

## Checklist

### Sempre (modo URL)

| ID | Verificar | Como | Severidade típica |
|---|---|---|---|
| 01.01 | Stack | `stack.json` + arquivos do projeto. Escreva em `cobertura.verificado` qual mecanismo de isolamento e de auth você identificou | — |
| 01.02 | Headers de segurança | `headers.json -> ausentes`. Agrupe num achado só. CSP ausente em site com formulário ou login sobe para média | media / baixa |
| 01.03 | HTTPS e cookies | HTTP não redireciona para HTTPS (`redirects.json`); cookie de sessão sem `HttpOnly`/`Secure`/`SameSite` | alta (sem HTTPS), media (cookies) |
| 01.04 | Arquivos expostos | Itens com `exposto: true`. `.env`, `.git`, dump de banco = crítica. `package.json` público = baixa | critica a baixa |
| 01.05 | Source maps | `source-maps.json -> publico: true` | baixa |
| 01.06 | Segredos no navegador | `segredos-bundle.json`. Use `severidade_sugerida`, mas confira: chave Google de Maps é pública por desenho; `sk_test_` não é produção | critica |
| 01.09 | CORS | `access-control-allow-origin` igual a `*` ou refletindo a origem de teste **com** `allow-credentials: true` | alta |
| 01.13 | XSS visível | Links com `href` `javascript:` vindos de conteúdo; parâmetros da URL refletidos na página (só observe; não injete nada) | media |
| 01.15 | CSRF (resumido) | Cookie de sessão sem `SameSite` e formulário que altera dados sem token visível | media |
| 01.18 | Abuso | Formulário público sem captcha, honeypot ou limite aparente | baixa / media |
| 01.20 | IA no front | Chamada direta do navegador para `api.openai.com`, `api.anthropic.com` etc. em `rede.json` | critica |

### Só com código (modo código ou híbrido)

| ID | Verificar | Como | Severidade típica |
|---|---|---|---|
| 01.07 | Segredos no código e no histórico git | Padrões da seção 2 de `padroes-seguranca.md`; `git log -p --all -S` para os prefixos | critica |
| 01.08 | Defaults inseguros | Seção 3 de `padroes-seguranca.md`. Confirme se a aplicação sobe sem a variável | alta / critica |
| 01.10 | Isolamento por dono/tenant | Listagens, buscas, relatórios, exportações filtram pelo usuário/organização? RLS ativa em todas as tabelas com dados de usuário? | critica |
| 01.11 | Permissão só no front | Cada `isAdmin`/`role` no front tem checagem equivalente na rota do servidor | critica / alta |
| 01.12 | IDOR | Percorra **todos** os handlers que recebem ID. Liste em `cobertura.verificado` quantos handlers foram lidos | critica / alta |
| 01.13 | XSS no código | `dangerouslySetInnerHTML`, `v-html`, `innerHTML`, markdown sem sanitizar, HTML de e-mail com dado do usuário | alta / media |
| 01.14 | Injeção | SQL/NoSQL/comando montado com string | critica |
| 01.16 | Upload, path traversal, SSRF | Só se o projeto tiver upload ou buscar URL informada pelo usuário | alta |
| 01.17 | Sessão | Token em `localStorage`, JWT sem expiração, reset de senha sem expiração, login sem limite de tentativas | alta / media |
| 01.19 | Webhooks | Verificação de assinatura presente | critica (pagamento) |
| 01.20 | IA no servidor | Rate limit, limite de tokens, system prompt enviado ao cliente | alta / media |
| 01.22 | Senhas | Hash com bcrypt/argon2/scrypt; nunca MD5/SHA1/texto puro | critica |
| 01.23 | Logs | Senha, token, CPF ou cartão escritos em log | media |

## Regras específicas

- Teste em produção é só passivo. Nada de força bruta, injeção ou varredura agressiva.
- Nunca copie um segredo inteiro. Use o valor mascarado da coleta.
- Quando a categoria não se aplica (site estático sem backend), registre em `nao_aplicavel` em vez de forçar achado.
- Anote condições de exploração ("só explorável se o usuário estiver logado").
- Em segredo exposto, a recomendação sempre inclui **revogar e trocar** a credencial, não só remover do código.

## Extras para o relatório

```json
"extras": { "headers": {"presentes": [...], "ausentes": [...]}, "handlers_verificados": 34 }
```
