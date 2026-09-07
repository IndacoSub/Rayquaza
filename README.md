### `README.md`

# Rayquaza

Rayquaza è un piccolo tool per creare e applicare patch **XDelta** tra una versione originale e una versione modificata dei file.

Il programma ha **due modalità completamente separate**:

1. **Creazione delle patch**
2. **Applicazione delle patch**

Le due operazioni non devono necessariamente essere eseguite sulla stessa macchina o nello stesso momento.

---

## Come funziona

Il concetto fondamentale è:

```text
FILE ORIGINALE
      +
FILE MODIFICATO
      ↓
    XDELTA
      ↓
     PATCH
```

Successivamente, in un'altra occasione:

```text
FILE ORIGINALE
      +
     PATCH
      ↓
FILE MODIFICATO
```

Rayquaza usa `xdelta3-3.1.0-x86_64.exe` per generare e applicare le patch.

---

# Struttura consigliata

Per esempio:

```text
Rayquaza/
│
├── Rayquaza.py
├── xdelta3-3.1.0-x86_64.exe
│
├── original/
│   ├── data/
│   │   ├── file1.bin
│   │   └── file2.bin
│   └── config/
│       └── settings.dat
│
├── modified/
│   ├── data/
│   │   ├── file1.bin
│   │   └── file2.bin
│   └── config/
│       └── settings.dat
│
└── patches/
```

La cosa importante è che `original/` e `modified/` abbiano la **stessa struttura relativa**.

Per esempio:

```text
original/data/test.bin
modified/data/test.bin
```

Rayquaza confronterà automaticamente quei due file.

---

# 1. Creare le patch

La creazione delle patch si fa senza `-a`.

Sintassi:

```bash
python Rayquaza.py --og ORIGINAL --mod MODIFIED --out PATCHES
```

Esempio:

```bash
python Rayquaza.py --og original --mod modified --out patches
```

Rayquaza farà questo:

```text
original/data/file1.bin
        +
modified/data/file1.bin
        ↓
patches/data/file1.bin.xdelta
```

---

## Come decide quali file patchare

Per ogni file presente nella cartella `modified`, Rayquaza cerca il corrispondente file nella cartella `original`.

Poi calcola:

```text
MD5 originale
MD5 modificato
```

Se i due MD5 sono uguali:

```text
Original MD5: abc123...
Modified MD5: abc123...

No changes detected
```

non viene creata alcuna patch.

Se invece sono diversi:

```text
Original MD5: abc123...
Modified MD5: 789xyz...
```

Rayquaza crea una patch XDelta.

Questo evita di generare patch inutili per file che non sono stati modificati.

---

# 2. Applicare le patch

L'applicazione è una fase separata dalla creazione.

Servono:

* la cartella originale
* la cartella contenente le patch `.xdelta`
* una cartella di destinazione

Sintassi:

```bash
python Rayquaza.py --og ORIGINAL --xdelta PATCHES --mod TARGET -a
```

Esempio:

```bash
python Rayquaza.py --og original --xdelta patches --mod output -a
```

Il risultato sarà:

```text
original/data/file1.bin
        +
patches/data/file1.bin.xdelta
        ↓
output/data/file1.bin
```

Quindi puoi conservare e distribuire solamente:

```text
patches/
```

insieme alle istruzioni necessarie per applicarle alla versione originale.

---

# Differenza tra `--mod` nelle due modalità

L'argomento `--mod` ha un significato diverso a seconda della modalità.

## Creazione

```bash
--mod modified
```

significa:

> "Questa è la cartella che contiene i file modificati da cui devo creare le patch."

Esempio:

```bash
python Rayquaza.py --og original --mod modified --out patches
```

## Applicazione

```bash
--mod output
```

significa:

> "Questa è la cartella dove devo mettere i file ricostruiti."

Esempio:

```bash
python Rayquaza.py --og original --xdelta patches --mod output -a
```

Per questo motivo sarebbe possibile, in futuro, rinominare `--mod` in qualcosa di più esplicito, ma attualmente il comportamento è questo.

---

# Modalità Installer

È possibile passare:

```bash
--installer
```

durante la creazione delle patch.

Esempio:

```bash
python Rayquaza.py --og original --mod modified --out patches --installer
```

Normalmente una patch viene chiamata:

```text
file.bin.xdelta
```

Con `--installer` diventa:

```text
file.bin_patch.xdelta
```

Questa modalità è specificamente prevista per l'utilizzo con **V3UPSManager**.

---

# File nuovi

Rayquaza attualmente lavora sulla logica:

```text
ORIGINAL FILE
      +
MODIFIED FILE
      ↓
PATCH
```

Se trova un file nella cartella `modified` che **non esiste nella cartella `original`**, non genera una patch.

Esempio:

```text
original/
    file1.bin

modified/
    file1.bin
    newfile.bin
```

Rayquaza segnalerà:

```text
Original file not found: original/newfile.bin
```

`newfile.bin` non viene quindi incluso nella patch.

---

# File eliminati

La situazione opposta è simile.

Se un file esiste in `original` ma non esiste in `modified`, Rayquaza non lo percorre perché analizza i file presenti nella cartella `modified`.

Di conseguenza **l'attuale implementazione non genera informazioni per cancellare file dalla versione originale**.

In pratica Rayquaza gestisce principalmente:

```text
file originale
      ↓
file modificato
      ↓
patch
```

e non un sistema completo di aggiunta/rimozione file.

---

# Requisiti

Rayquaza richiede:

```text
Python 3
xdelta3-3.1.0-x86_64.exe
```

`xdelta3-3.1.0-x86_64.exe` deve essere raggiungibile dalla directory di esecuzione dello script.

La struttura più semplice è:

```text
Rayquaza/
├── Rayquaza.py
└── xdelta3-3.1.0-x86_64.exe
```

---

# Esempio completo: creazione

Supponiamo di avere:

```text
original/
└── game/
    ├── data.bin
    └── text.bin

modified/
└── game/
    ├── data.bin
    └── text.bin
```

Eseguire:

```bash
python Rayquaza.py --og original --mod modified --out patches
```

Se solo `data.bin` è cambiato, il risultato sarà:

```text
patches/
└── game/
    └── data.bin.xdelta
```

Non verrà creata una patch per `text.bin`.

---

# Esempio completo: applicazione

Partendo da:

```text
original/
└── game/
    ├── data.bin
    └── text.bin

patches/
└── game/
    └── data.bin.xdelta
```

eseguire:

```bash
python Rayquaza.py --og original --xdelta patches --mod output -a
```

Risultato:

```text
output/
└── game/
    └── data.bin
```

`data.bin` sarà il risultato dell'applicazione della patch all'originale.

---

# Flusso consigliato

## Fase 1 — Sviluppo / creazione patch

Hai:

```text
ORIGINAL
MODIFICATO
```

Esegui:

```bash
python Rayquaza.py --og original --mod modified --out patches
```

Ottieni:

```text
PATCHES
```

Queste sono quelle che distribuirai.

---

## Fase 2 — Installazione / applicazione

In un momento successivo hai:

```text
ORIGINAL
PATCHES
```

Esegui:

```bash
python Rayquaza.py --og original --xdelta patches --mod output -a
```

Ottieni:

```text
OUTPUT
```

contenente i file risultanti.

---

# Errori comuni

## XDelta non trovato

```text
XDelta patcher couldn't be found!
```

Controlla che:

```text
xdelta3-3.1.0-x86_64.exe
```

sia presente nella directory da cui viene eseguito Rayquaza.

---

## Parametri insufficienti

Rayquaza stampa automaticamente l'utilizzo corretto.

Creazione:

```bash
python Rayquaza.py --og original --mod modified --out patches
```

Applicazione:

```bash
python Rayquaza.py --og original --xdelta patches --mod output -a
```

---

## File originale mancante

Durante la creazione:

```text
Original file not found: ...
```

significa che esiste il file modificato, ma non esiste il corrispondente file nella cartella originale.

Durante l'applicazione significa invece che una patch richiede un file originale che non è presente.

---

# Riassunto dei parametri

| Parametro     | Significato                                                             |
| ------------- | ----------------------------------------------------------------------- |
| `--og`        | Cartella dei file originali                                             |
| `--mod`       | Cartella dei modificati durante EXTRACT / cartella target durante APPLY |
| `--out`       | Cartella dove creare le patch                                           |
| `--xdelta`    | Cartella contenente le patch da applicare                               |
| `-a`          | Attiva la modalità APPLY                                                |
| `--installer` | Aggiunge `_patch` ai nomi delle patch generate                          |

---

# Comandi principali

### Creare patch

```bash
python Rayquaza.py --og original --mod modified --out patches
```

### Creare patch per V3UPSManager

```bash
python Rayquaza.py --og original --mod modified --out patches --installer
```

### Applicare patch

```bash
python Rayquaza.py --og original --xdelta patches --mod output -a
```

---

# Nota importante

Rayquaza confronta i file usando MD5 **solo per stabilire se il file è cambiato**.

L'MD5 non viene usato come controllo di validità della patch durante l'applicazione.

Inoltre, la versione attuale non gestisce automaticamente:

* aggiunta di file completamente nuovi
* rimozione di file
* verifica finale MD5 dei file ricostruiti

Queste funzioni possono essere aggiunte in futuro se Rayquaza deve diventare un sistema di patch completo.