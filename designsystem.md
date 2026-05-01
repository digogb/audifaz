# UI UX Pro Max — Design System

> Extraído visualmente do site metodosid.com.br (UI UX Pro Max)

---

## 1. Cores

### Paleta principal

| Token                    | Hex / valor                  | Uso                            |
|--------------------------|------------------------------|--------------------------------|
| `--bg-base`              | `#0B1527`                    | Fundo principal                |
| `--bg-mid`               | `#112040`                    | Fundo secundário               |
| `--bg-surface`           | `#1A2D50`                    | Cards, containers, nav         |
| `--bg-glass`             | `rgba(255,255,255,0.07)`     | Pills, stat cards              |
| `--color-accent-blue`    | `#2D72D9`                    | Botão primário, links          |
| `--color-text-blue`      | `#5B9EF4`                    | Títulos hero, números de stat  |
| `--color-accent-orange`  | `#D4845A`                    | Destaque "Max", glow bg        |
| `--color-terminal`       | `#E8865A`                    | Prompt `$` no terminal         |
| `--color-text-muted`     | `#A8B5CC`                    | Texto "Pro", subtítulos        |
| `--color-text-primary`   | `#FFFFFF`                    | Headings, texto hero           |
| `--color-text-body`      | `rgba(255,255,255,0.50)`     | Parágrafos, descrições         |
| `--color-text-caption`   | `rgba(255,255,255,0.40)`     | Labels, captions               |
| `--color-border`         | `rgba(255,255,255,0.10)`     | Bordas suaves                  |
| `--bg-terminal`          | `#090F1C`                    | Code block / terminal          |

### Efeitos de fundo (glows radiais)

```css
/* Glow laranja — posicionado à direita */
background: radial-gradient(
  circle,
  rgba(210, 110, 50, 0.35) 0%,
  transparent 70%
);

/* Glow azul — posicionado à esquerda */
background: radial-gradient(
  circle,
  rgba(40, 90, 200, 0.25) 0%,
  transparent 70%
);
```

---

## 2. Tipografia

### Famílias

| Papel        | Família                          | Fallback          |
|--------------|----------------------------------|-------------------|
| Display/Body | `Inter`                          | `system-ui, sans-serif` |
| Mono         | `JetBrains Mono` / `Fira Code`   | `monospace`       |

### Escala

| Nome           | Tamanho | Peso | Line-height | Cor                     | Uso                           |
|----------------|---------|------|-------------|-------------------------|-------------------------------|
| Display Hero   | `72px`  | 800  | 1.05        | `#FFFFFF`               | Subtítulo "Design Intelligence" |
| Display Brand  | `72px`  | 800  | 1.05        | multicolor (ver abaixo) | "UI UX Pro Max"               |
| Logo           | `14px`  | 600  | —           | `#FFFFFF`               | Nome no navbar                |
| Nav Link       | `13px`  | 400  | —           | `rgba(255,255,255,0.6)` | Links de navegação            |
| Body           | `14px`  | 400  | 1.6         | `rgba(255,255,255,0.5)` | Parágrafos descritivos        |
| Stat Number    | `24px`  | 700  | 1.0         | `#5B9EF4`               | Números nos cards de stat     |
| Stat Label     | `11px`  | 400  | —           | `rgba(255,255,255,0.4)` | Labels abaixo dos números     |
| Terminal       | `13px`  | 400  | —           | `#FFFFFF`               | Código no bloco terminal      |
| Badge/Pill     | `12px`  | 500  | —           | `rgba(255,255,255,0.75)`| Chips de ferramentas          |

### Cores do display brand

```css
/* "UI UX " */  color: #5B9EF4;
/* "Pro "   */  color: #A8B5CC;
/* "Max"    */  color: #D4845A;
/* Linha 2  */  color: #FFFFFF;
```

### Gradient em texto (hero)

```css
background: linear-gradient(135deg, #5B9EF4, #2D72D9);
-webkit-background-clip: text;
-webkit-text-fill-color: transparent;
background-clip: text;
```

---

## 3. Espaçamento

Escala base-4:

```
4px  · 6px  · 8px  · 10px · 12px · 14px
16px · 20px · 24px · 32px · 40px · 48px
```

---

## 4. Border Radius

| Token              | Valor   | Uso                        |
|--------------------|---------|----------------------------|
| `--radius-xs`      | `4px`   | Ícones internos, chips     |
| `--radius-btn`     | `8–10px`| Botões                     |
| `--radius-card`    | `10px`  | Stat cards                 |
| `--radius-container`| `12px` | Navbar, containers maiores |
| `--radius-hero`    | `16px`  | Seções hero                |
| `--radius-pill`    | `999px` | Pills / badges             |

---

## 5. Componentes

### Navbar

```css
background: rgba(255, 255, 255, 0.05);
border: 0.5px solid rgba(255, 255, 255, 0.10);
border-radius: 12px;
padding: 12px 20px;
backdrop-filter: blur(8px);
```

### Tool Pill / Badge

```css
display: inline-flex;
align-items: center;
gap: 6px;
padding: 5px 12px;
border-radius: 999px;
background: rgba(255, 255, 255, 0.07);
border: 0.5px solid rgba(255, 255, 255, 0.12);
color: rgba(255, 255, 255, 0.75);
font-size: 12px;
font-weight: 500;
```

### Botão primário

```css
background: #2D72D9;
color: #FFFFFF;
padding: 10px 22px;
border-radius: 10px;
font-size: 13px;
font-weight: 600;
border: none;
```

### Botão secundário

```css
background: rgba(255, 255, 255, 0.08);
color: #FFFFFF;
padding: 10px 22px;
border-radius: 10px;
font-size: 13px;
font-weight: 600;
border: 0.5px solid rgba(255, 255, 255, 0.18);
```

### Stat Card

```css
background: rgba(255, 255, 255, 0.05);
border: 0.5px solid rgba(255, 255, 255, 0.09);
border-radius: 10px;
padding: 14px 10px 12px;
text-align: center;

/* Ícone */
width: 22px;
height: 22px;
opacity: 0.6;
stroke: rgba(91, 158, 244, 0.7); /* stroke dos SVGs */

/* Número */
font-size: 22px;
font-weight: 700;
color: #5B9EF4;

/* Label */
font-size: 10px;
color: rgba(255, 255, 255, 0.4);
margin-top: 4px;
```

### Terminal / Code Block

```css
background: #090F1C;
border: 0.5px solid rgba(255, 255, 255, 0.10);
border-radius: 10px;
padding: 12px 16px;
font-family: 'JetBrains Mono', monospace;
font-size: 13px;
color: #FFFFFF;

/* Prompt $ */
color: #E8865A;

/* Cursor piscante */
display: inline-block;
width: 7px;
height: 14px;
background: #FFFFFF;
animation: blink 1.1s step-end infinite;

@keyframes blink {
  50% { opacity: 0; }
}
```

### Glassmorphism (padrão de surface)

```css
background: rgba(255, 255, 255, 0.05);
border: 0.5px solid rgba(255, 255, 255, 0.10);
backdrop-filter: blur(8px);
-webkit-backdrop-filter: blur(8px);
```

---

## 6. Ícones

- Estilo: **line / stroke**, sem fill
- Stroke width: `1.5px`
- Cor padrão: `rgba(91, 158, 244, 0.7)` (azul suave)
- Tamanho nos stat cards: `22×22px`
- Tamanho no navbar: `14×14px`

---

## 7. Tokens CSS completos

```css
:root {
  /* Backgrounds */
  --bg-base:              #0B1527;
  --bg-mid:               #112040;
  --bg-surface:           #1A2D50;
  --bg-glass:             rgba(255, 255, 255, 0.07);
  --bg-terminal:          #090F1C;

  /* Cores de destaque */
  --color-accent-blue:    #2D72D9;
  --color-text-blue:      #5B9EF4;
  --color-accent-orange:  #D4845A;
  --color-terminal:       #E8865A;

  /* Texto */
  --color-text-primary:   #FFFFFF;
  --color-text-muted:     #A8B5CC;
  --color-text-body:      rgba(255, 255, 255, 0.50);
  --color-text-caption:   rgba(255, 255, 255, 0.40);

  /* Bordas */
  --color-border:         rgba(255, 255, 255, 0.10);
  --color-border-strong:  rgba(255, 255, 255, 0.18);

  /* Tipografia */
  --font-display:         'Inter', system-ui, sans-serif;
  --font-body:            'Inter', system-ui, sans-serif;
  --font-mono:            'JetBrains Mono', 'Fira Code', monospace;

  /* Border radius */
  --radius-xs:            4px;
  --radius-btn:           10px;
  --radius-card:          10px;
  --radius-container:     12px;
  --radius-pill:          999px;

  /* Spacing */
  --space-1:  4px;
  --space-2:  8px;
  --space-3:  12px;
  --space-4:  16px;
  --space-5:  20px;
  --space-6:  24px;
  --space-8:  32px;
  --space-10: 40px;
  --space-12: 48px;
}
```