# ADR-001 — Arquitetura Base do Projeto

## Status

Aceito

---

## Contexto

O Projeto Leme Norte é um SaaS que deverá crescer de forma incremental, incorporando novos módulos, dashboards, integrações e serviços.

Era necessário definir uma arquitetura que favorecesse organização, escalabilidade e facilidade de manutenção.

---

## Decisão

Adotar uma arquitetura em camadas composta por:

- app
- features
- services
- repositories
- components
- hooks
- lib
- utils
- types
- styles

A aplicação será organizada em um monorepo, mantendo a aplicação web em:

apps/web

---

## Consequências

### Positivas

- Organização clara.
- Baixo acoplamento.
- Alta reutilização de componentes.
- Facilidade para testes.
- Facilidade para crescimento do projeto.

### Negativas

- Curva de aprendizado inicial um pouco maior.
- Maior disciplina na organização dos arquivos.

---

## Data

29/07/2026

---

## Responsáveis

Equipe de Engenharia do Projeto Leme Norte