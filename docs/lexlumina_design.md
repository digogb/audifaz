# LexLumina Design System --- Verde Jurídico Sofisticado

## 1. Visão Geral

Design system para plataforma jurídica premium, combinando **verde
institucional sofisticado** com **dourado executivo**, visando
transmitir:

-   Autoridade
-   Credibilidade
-   Sofisticação
-   Clareza visual
-   Experiência premium para lawtechs, escritórios e educação jurídica

------------------------------------------------------------------------

## 2. Design Tokens

### Cores

  Token             Valor       Uso
  ----------------- ----------- -----------------------------
  Primary           `#1F4D3A`   Cor principal institucional
  Primary Hover     `#16382A`   Hover de botões e ações
  Secondary Gold    `#C5A880`   Destaques, tags, progresso
  Secondary Hover   `#B3956B`   Hover do dourado
  Background Base   `#F8F9FA`   Fundo geral
  Surface           `#FFFFFF`   Cards e superfícies
  Text Main         `#2D3748`   Texto principal
  Text Muted        `#718096`   Texto auxiliar
  Border            `#E2E8F0`   Bordas

------------------------------------------------------------------------

## 3. Tipografia

### Heading Font

**Merriweather**

Uso:

-   títulos
-   branding
-   navegação premium
-   headings jurídicos

### Body Font

**Inter**

Uso:

-   interface
-   textos corridos
-   formulários
-   UX/UI

### Escalas

  Elemento     Fonte                   Tamanho
  ------------ ----------------------- ---------
  H1           Merriweather Bold       32px
  H2           Merriweather SemiBold   24px
  Body Large   Inter Regular           18px
  Body Base    Inter Regular           16px
  Body Small   Inter Regular           14px

------------------------------------------------------------------------

## 4. Componentes

### Botões

#### Primary Button

Características:

-   fundo verde institucional
-   texto branco
-   CTA principal

``` css
background:#1F4D3A;
color:#FFFFFF;
```

#### Secondary Button

Características:

-   transparente
-   borda dourada
-   ações secundárias

#### Ghost Button

Características:

-   minimalista
-   baixa hierarquia visual

------------------------------------------------------------------------

### Campo de Busca

Características:

-   borda discreta
-   foco verde sofisticado
-   leitura confortável

Focus State:

``` css
box-shadow:0 0 0 3px rgba(31,77,58,.10);
```

------------------------------------------------------------------------

### Card Jurídico

Estrutura:

-   tag temática
-   título serifado
-   descrição auxiliar
-   CTA principal

Aplicações:

-   jurisprudência
-   aulas
-   doutrina
-   trilhas de estudo

------------------------------------------------------------------------

## 5. Layout Base

### Header

Características:

-   fundo primary
-   detalhe dourado inferior
-   branding institucional

### Section Container

Características:

-   fundo branco
-   radius leve
-   sombra discreta

### Mockup Layout

Grid:

``` txt
2 colunas
[ Conteúdo principal ] [ Sidebar ]
```

------------------------------------------------------------------------

## 6. Shadows

### Small Shadow

``` css
0 2px 4px rgba(0,0,0,.02)
```

### Medium Shadow

``` css
0 4px 10px rgba(31,77,58,.08)
```

------------------------------------------------------------------------

## 7. Branding Visual

### Personalidade

O sistema visual comunica:

-   jurídico contemporâneo
-   premium
-   acadêmico
-   confiável
-   executivo

### Inspiração estética

Mistura entre:

-   lawtech premium
-   biblioteca jurídica executiva
-   escritório high-end
-   plataforma educacional sofisticada

------------------------------------------------------------------------

## 8. CSS Tokens

``` css
:root{

--color-primary:#1F4D3A;
--color-primary-hover:#16382A;

--color-secondary:#C5A880;
--color-secondary-hover:#B3956B;

--color-bg-base:#F8F9FA;
--color-surface:#FFFFFF;

--color-text-main:#2D3748;
--color-text-muted:#718096;
--color-border:#E2E8F0;

}
```

------------------------------------------------------------------------

## 9. Casos de Uso

Este design system é adequado para:

-   plataformas de estudo jurídico
-   lawtechs
-   tribunais
-   escritórios de advocacia
-   gestão jurídica
-   dashboards jurídicos
-   educação corporativa
