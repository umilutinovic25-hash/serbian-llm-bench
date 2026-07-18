---
title: Serbian LLM Benchmark
emoji: 🇷🇸
colorFrom: blue
colorTo: red
sdk: gradio
sdk_version: 6.20.0
app_file: app.py
pinned: false
license: apache-2.0
tags:
  - leaderboard
  - serbian
  - evaluation
  - benchmark
---

# Serbian LLM Benchmark

Koliko mali open-source modeli zaista znaju srpski? Engleski leaderboardi to ne mere
— model može biti odličan na MMLU i i dalje ne znati u koji padež ide imenica posle
predloga „uprkos".

95 ručno pisanih zadataka, 6 kategorija, jednake uslove za svaki model.

## Rezultati

| # | Model | Ukupno | Gramatika | Padeži | Pravopis | Razumevanje | NER | Prevod |
|---|---|---|---|---|---|---|---|---|
| 1 | mistral:latest (7B) | **71.5** | 65.0 | 50.0 | 66.7 | 73.3 | 95.3 | 96.7 |
| 2 | gemma2:2b | 60.9 | 50.0 | 45.0 | 53.3 | 60.0 | 96.7 | 73.3 |
| 3 | qwen2.5:3b | 56.6 | 65.0 | 30.0 | 53.3 | 46.7 | 96.4 | 53.3 |
| 4 | llama3.2 (3B) | 54.6 | 55.0 | 25.0 | 53.3 | 53.3 | 77.3 | 82.5 |
| 5 | qwen2.5:1.5b | 47.9 | 50.0 | 40.0 | 26.7 | 40.0 | 76.9 | 60.0 |

Nasumično pogađanje daje **33.3%** na pitanjima sa tri ponuđena odgovora.

## Nalazi

**Padeži su zid.** Prosek svih modela je 38%, nijedan ne prelazi 50%, a `llama3.2`
sa 25% i `qwen2.5:3b` sa 30% su **ispod nasumičnog pogađanja** — bolje bi prošli
da su bacali novčić. Sedmopadežni sistem sa rekcijom predloga je ono što ovi modeli
nisu naučili.

**NER je najlakši (88.5% prosek).** Izdvajanje imena, gradova i iznosa je uglavnom
prepisivanje iz teksta — morfologija se ne dira, pa i najslabiji modeli prolaze.

**Broj parametara ne odlučuje.** `gemma2:2b` tuče `qwen2.5:3b` uprkos manjem
modelu, a razlika je najveća baš na padežima (45% naspram 30%). Zastupljenost
srpskog u podacima za treniranje znači više od veličine.

**Gramatika i pravopis stoje na pola.** Modeli znaju uobičajene oblike, ali padaju
na tačkama gde i izvorni govornici greše: „trebam" umesto „treba", komparativ
„strožija" umesto „stroža".

## Kategorije

| Kategorija | Zadataka | Šta meri |
|---|---|---|
| Gramatika | 20 | slaganje subjekta i predikata, glagolski oblici, „trebati" |
| Padeži | 20 | svih sedam padeža, rekcija predloga i glagola |
| Pravopis | 15 | č/ć, dž/đ, spojeno i odvojeno pisanje, jednačenje |
| Razumevanje | 15 | izvlačenje činjenica, poređenje, idiomi, ironija |
| NER | 15 | imena, gradovi, firme, datumi, iznosi, kontakti |
| Prevod | 10 | srpski ↔ engleski, u oba smera |

## Ocenjivanje

- **Pitanja sa izborom** — tačno/netačno. Slovo odgovora se izvlači sa nekoliko
  obrazaca (`B`, `B)`, „odgovor je B"); ako model napiše ceo tekst odgovora umesto
  slova, priznaje se samo ako nije naveo i neku od pogrešnih opcija.
- **NER** — **F1**, ne odziv. Model koji prepiše celu rečenicu ima savršen odziv,
  ali ga preciznost obara na ~0.6 umesto 1.0. Bez ovoga se benchmark trivijalno vara.
- **Prevod** — pokrivenost ključnih pojmova, sa prihvaćenim sinonimima
  (`odložen` / `pomeren` / `odgođen` prolaze isto).
- Poređenje zanemaruje dijakritike i interpunkciju: „Niš" i „Nis" su isto. Meri se
  znanje jezika, ne raspored tastature.

Svi modeli rade na `temperature=0`, sa identičnim promptovima. Za modele koji
generišu razmišljanje, `<think>` blok se odbacuje pre ocenjivanja.

## Pokretanje

```bash
ollama serve

python bench/run.py --model ollama:mistral:latest        # ceo benchmark
python bench/run.py --model ollama:gemma2:2b --categories padezi --verbose
python bench/run.py --model mock                          # provera harnessa

python app.py                                             # leaderboard lokalno
```

Rezultati se upisuju u `results/<model>.json` sa odgovorom i ocenom za svaki
zadatak, pa se greške mogu pregledati pojedinačno.

## Ograničenja

Zadatke je pisao jedan izvorni govornik; standardni srpski, ekavica, latinica.
Skup je mali (95 zadataka), pa razlike ispod nekoliko procentnih poena nisu
značajne. Testirani su samo modeli koji staju na laptop (1.5B–7B) — veliki
komercijalni modeli bi verovatno probili plafon na svim kategorijama osim padeža.

## Struktura

```
data/       zadaci, jedan JSONL po kategoriji
bench/      tasks.py (učitavanje + ocenjivanje), providers.py, run.py
results/    JSON rezultat po modelu
app.py      Gradio leaderboard
```

Doprinosi su dobrodošli — posebno novi zadaci i modeli za testiranje.

Licenca: Apache 2.0
