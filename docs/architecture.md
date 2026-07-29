# Arquitetura do Leme Norte

## Visão Geral

O Leme Norte é um SaaS construído sobre uma arquitetura em camadas, utilizando Next.js, React e TypeScript.

O objetivo desta arquitetura é manter o código organizado, reutilizável e escalável.

---

# Estrutura

```
apps/
└── web/
    ├── app/
    ├── public/
    ├── src/
    │
    ├── components/
    │   ├── ui/
    │   ├── dashboard/
    │   ├── charts/
    │   └── forms/
    │
    ├── features/
    │   ├── diario-de-bordo/
    │   ├── dashboard/
    │   ├── indice-saude/
    │   └── bussola/
    │
    ├── services/
    ├── repositories/
    ├── hooks/
    ├── lib/
    ├── styles/
    ├── types/
    └── utils/
```

---

# Fluxo da Aplicação

```
Usuário

↓

Página (app)

↓

Feature

↓

Service

↓

Repository

↓

Banco de Dados
```

---

# Responsabilidades

## app

Responsável apenas pelas rotas, layouts e páginas.

Não deve conter regra de negócio.

---

## features

Contém a lógica funcional de cada módulo do sistema.

---

## services

Coordena operações e regras de negócio.

---

## repositories

Realiza acesso ao banco de dados.

---

## components

Contém componentes reutilizáveis.

---

## hooks

Hooks customizados.

---

## utils

Funções utilitárias puras.

---

## lib

Configurações compartilhadas.

---

## styles

Arquivos globais de estilo.

---

## types

Interfaces e tipos TypeScript.