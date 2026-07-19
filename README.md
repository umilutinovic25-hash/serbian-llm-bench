# Serbian LLM Benchmark

[**Rezultati uživo**](https://umilutinovic25-hash.github.io/serbian-llm-bench/) ·
[Hugging Face Space](https://huggingface.co/spaces/uros69/serbian-llm-bench)

Koliko mali open-source modeli zaista znaju srpski? Engleski leaderboardi to ne mere
— model može biti odličan na MMLU i i dalje ne znati u koji padež ide imenica posle
predloga „uprkos".

95 ručno pisanih zadataka, 6 kategorija, 8 modela, jednake uslove za svaki.

## Rezultati

| # | Model | Ukupno | Gramatika | Padeži | Pravopis | Razumevanje | NER | Prevod |
|---|---|---|---|---|---|---|---|---|
| 1 | gemma3 (4B) | **79.5** | 70.0 | 55.0 | 86.7 | 86.7 | 100.0 | 95.0 |
| 2 | mistral (7B) | 71.5 | 65.0 | 50.0 | 66.7 | 73.3 | 95.3 | 96.7 |
| 3 | gemma2:2b | 60.9 | 50.0 | 45.0 | 53.3 | 60.0 | 96.7 | 73.3 |
| 4 | qwen2.5:3b | 56.6 | 65.0 | 30.0 | 53.3 | 46.7 | 96.4 | 53.3 |
| 5 | llama3.2 (3B) | 54.6 | 55.0 | 25.0 | 53.3 | 53.3 | 77.3 | 82.5 |
| 6 | qwen2.5:1.5b | 47.9 | 50.0 | 40.0 | 26.7 | 40.0 | 76.9 | 60.0 |
| 7 | phi3:mini (3.8B) | 45.9 | 35.0 | 40.0 | 46.7 | 53.3 | 61.5 | 44.2 |
| 8 | llama3.2:1b | 38.3 | 35.0 | 30.0 | 33.3 | 20.0 | 78.4 | 35.8 |

Nasumično pogađanje daje **33.3%** na pitanjima sa tri ponuđena odgovora.

## Nalazi

**Padeži su zid.** Prosek svih modela je 39%, nijedan ne prelazi 55%, a
`llama3.2:latest` (25%), `qwen2.5:3b` i `llama3.2:1b` (po 30%) su **ispod
nasumičnog pogađanja** — bolje bi prošli da su bacali novčić. Sedmopadežni sistem sa rekcijom predloga je ono što ovi modeli
nisu naučili.

**NER je najlakši (83.2% prosek).** Izdvajanje imena, gradova i iznosa je uglavnom
prepisivanje iz teksta — morfologija se ne dira, pa i najslabiji modeli prolaze.

**Broj parametara ne odlučuje.** `gemma3:4b` tuče `mistral` sa 7B, a `gemma2:2b`
pretiče tri veća modela (`qwen2.5:3b`, `llama3.2`, `phi3:mini`). Zastupljenost srpskog u
podacima za treniranje znači više od veličine.

**Ispod ~2B model prestaje da prati zadatak.** `llama3.2:1b` na razumevanju ima
20% — daleko ispod nasumičnog pogađanja, jer često uopšte ne odgovori slovom nego
napiše nepovezan tekst („Napomena: Ova pitanja nema odgovora"). `phi3:mini` sklizne
u ćirilicu i piše rečenice koje nisu srpski („Визимото је пропуштано"), pa mu prevod
pada na 44% uprkos 3.8B parametara.

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
- Poređenje zanemaruje dijakritike i **transliterira ćirilicu**: „Niš", „Nis" i
  „Ниш" su isto. Srpski je dvoazbučan, pa bi kažnjavanje ćiriličnog odgovora merilo
  pismo umesto znanja jezika.

Svi modeli rade na `temperature=0`, sa identičnim promptovima. Za modele koji
generišu razmišljanje, `<think>` blok se odbacuje pre ocenjivanja.

Ocenjivanje pokriva `bench/test_scoring.py` (`python bench/test_scoring.py`).
Testovi postoje jer su dva buga u ocenjivanju već obarala rezultate: izvlačenje
slova je bez razlikovanja velikih i malih slova hvatalo „a" unutar reči „Dva" i
čitalo ga kao odgovor A, a normalizacija je brisala ćirilicu u prazan string, pa
bi ispravan ćirilični odgovor dobio nulu.

## Pokretanje

```bash
ollama serve

python bench/run.py --model ollama:mistral:latest        # ceo benchmark
python bench/run.py --model ollama:gemma2:2b --categories padezi --verbose
python bench/run.py --model mock                          # provera harnessa
python bench/test_scoring.py                              # testovi ocenjivanja

python app.py                                             # Gradio leaderboard lokalno
```

### Dodavanje modela

```bash
ollama pull gemma3:4b
./update.sh gemma3:4b        # izmeri, regeneriši stranicu, objavi
./update.sh                  # isto, ali za sve instalirane modele
./update.sh --no-push        # bez objavljivanja
```

`update.sh` prvo pušta testove ocenjivanja i staje ako padnu — brojevi se ne
objavljuju dok se grader ne proveri. Stranica u `docs/` je **generisana** iz
`results/*.json` (`bench/build_page.py`), pa ne može da se raziđe sa merenjima.

Za objavljivanje na Hugging Face treba `export HF_TOKEN=...` (besplatan write
token); bez njega se objavljuje samo na GitHub.

Rezultati se upisuju u `results/<model>.json` sa odgovorom i ocenom za svaki
zadatak, pa se greške mogu pregledati pojedinačno.

## Ograničenja

Zadatke je pisao jedan izvorni govornik; standardni srpski, ekavica, latinica.
Skup je mali (95 zadataka), pa razlike ispod nekoliko procentnih poena nisu
značajne. Testirani su samo modeli koji staju na laptop (1B–7B) — veliki
komercijalni modeli bi verovatno probili plafon na svim kategorijama osim padeža.

## Struktura

```
data/                 zadaci, jedan JSONL po kategoriji
bench/tasks.py        učitavanje zadataka + ocenjivanje
bench/providers.py    ollama i mock backend
bench/run.py          pokretanje benchmarka
bench/test_scoring.py testovi ocenjivanja
bench/build_page.py   generisanje docs/index.html iz rezultata
results/              JSON rezultat po modelu, sa odgovorom za svaki zadatak
docs/index.html       objavljena stranica (generisana, ne uređivati ručno)
app.py                Gradio leaderboard za lokalno pokretanje
update.sh             izmeri sve, regeneriši stranicu, objavi
```

Napomena: Gradio Space na Hugging Face free tieru traži PRO pretplatu, pa je
objavljena statična verzija. `app.py` radi lokalno i spreman je za deploy ako
PRO ikad postane opcija.

Doprinosi su dobrodošli — posebno novi zadaci i modeli za testiranje.

Licenca: Apache 2.0
