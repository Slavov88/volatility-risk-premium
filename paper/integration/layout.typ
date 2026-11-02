$definitions.typst()$

#let diff = $$ ∂ $$
#let ink = rgb("183c4c")
#set page(paper: "a4", margin: (top: 22mm, bottom: 21mm, x: 24mm),
  header: context { if counter(page).get().first() > 1 { text(size: 8pt, fill: ink)[VOLATILITY RISK PREMIUM #h(1fr) RESEARCH DRAFT] } },
  footer: context align(center, text(size: 9pt, counter(page).display())))
#set text(font: "Libertinus Serif", size: 10.5pt, lang: "en")
#set par(justify: true, leading: 0.58em)
#set heading(numbering: none)
#show heading.where(level: 1): it => block(above: 1.6em, below: 0.7em, text(size: 15pt, weight: "bold", fill: ink, it.body))
#show heading.where(level: 2): it => block(above: 1.2em, below: 0.5em, text(size: 12pt, weight: "bold", fill: ink, it.body))
#show link: set text(fill: ink)
#show raw: set text(size: 8pt)
#show figure.caption: set text(size: 9pt)
#show table: it => block(breakable: false, it)
#text(size: 9pt, weight: "bold", fill: ink)[EMPIRICAL FINANCE #h(1fr) 2 NOVEMBER 2026]
#v(0.6cm)
#block[
#set par(justify: false)
#set text(hyphenate: false)
#text(size: 21pt, weight: "bold", fill: ink)[$title$]
]
#v(0.25cm)
#text(size: 9.5pt)[Coauthor review draft | Provisional evidence]
#v(0.2cm)
#line(length: 100%, stroke: 0.5pt + ink)
#v(0.1cm)
$body$
