# Gabarito do site de teste

O site montado por `montar-site-teste.py` tem estas falhas. Uma análise completa deve encontrar todas as marcadas com **obrigatório**.

| Segmento | Falha plantada | Onde | Matriz | Esperado |
|---|---|---|---|---|
| Segurança | `.env` público com nomes de variáveis sensíveis | `/.env` | 01.04 | **obrigatório**, crítica |
| Segurança | `.git/HEAD` público | `/.git/HEAD` | 01.04 | **obrigatório**, crítica ou alta |
| Segurança | Padrão de chave secreta Stripe no JS público | `app.js` | 01.06 | **obrigatório**, crítica |
| Segurança | Source map público | `app.js.map` | 01.05 | **obrigatório**, baixa |
| Segurança | Nenhum header de segurança | todas | 01.02 | **obrigatório**, média |
| Segurança | `innerHTML` com `location.hash` | `app.js` | 01.13 | desejável (só com leitura do JS) |
| Privacidade | GA carregado antes do consentimento | home | 02.01 | **obrigatório**, alta |
| Privacidade | Banner sem opção de recusar | home | 02.01 | **obrigatório**, média |
| Privacidade | Sem política de privacidade com formulário que pede CPF | contato | 02.03, 02.05 | **obrigatório** |
| Privacidade | Caixa de ofertas pré-marcada | contato | 02.05 | **obrigatório**, média |
| Desempenho | Imagem de ~1,4 MB em PNG sem dimensões | home | 03.06, 03.11 | **obrigatório**, média ou alta |
| SEO | Title com 88 caracteres e sem meta description | home | 04.03 | **obrigatório** |
| SEO | Dois H1 | home | 04.04 | **obrigatório**, baixa |
| SEO | Sem Open Graph completo | todas | 04.13 | **obrigatório** |
| SEO | Link interno quebrado (`pagina-quebrada.html`) | menu | 04.06 / 10.07 | **obrigatório** |
| Acessibilidade | Imagem sem alt | home | 05.02 | **obrigatório** |
| Acessibilidade | Página sem `lang` | home | 05.08 | **obrigatório** |
| Acessibilidade | Texto cinza claro com contraste baixo | home | 05.03 | **obrigatório** |
| Acessibilidade | Campos de formulário sem rótulo | contato | 05.09 | **obrigatório**, alta |
| Acessibilidade / Design | Alvos de toque pequenos no menu | todas | 05.07 | **obrigatório** |
| Design | Rolagem horizontal no celular (bloco de 600 px) | home | 06.02 | **obrigatório**, alta |
| Copy | Frases genéricas ("melhores soluções do mercado", "Não é só um serviço. É uma experiência.") | home | 07.08 | **obrigatório** |
| Copy | Erro de ortografia "excessão" | home | 07.10 | **obrigatório** |
| Copy | Copyright de 2019 | sobre, serviços | 07.13 | desejável |
| Conversão | WhatsApp com número inválido (`wa.me/999`) | home | 08.10 | **obrigatório**, crítica ou alta |
| Conversão | Telefone sem DDD (`tel:9299`) | home | 08.10 | **obrigatório** |
| Conversão | E-mail inválido (`contato@exemplo`) | contato | 08.10 | **obrigatório** |
| Conversão | Headline "Bem-vindo ao nosso site" | home | 08.02 | **obrigatório** |
| Analytics | GA4 sem evento de conversão | todas | 09.02 | **obrigatório** |
| Arquitetura | Sem favicon | — | 10.08 | **obrigatório**, baixa |

Para medir: conte quantos **obrigatórios** a análise encontrou (meta: 100%) e quantos achados não estão aqui e não se sustentam (falsos positivos; meta: zero).
