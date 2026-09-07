import argparse
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


# ============================================================
# USAGE
# ============================================================
# Mostra a video la sintassi dei due modi principali di utilizzo:
#
# 1. EXTRACT
#    Confronta una cartella originale con una cartella modificata
#    e genera una serie di file .xdelta contenenti le differenze.
#
# 2. APPLY
#    Prende i file originali + le patch .xdelta e ricrea i file
#    modificati dentro una cartella di destinazione.
#
def explain_usage():
    print(
        "EXTRACT: Rayquaza.py "
        "--og ORIGINAL_FILES_FOLDER "
        "--mod MODIFIED_FILES_FOLDER "
        "--out OUT_XDELTA_FILES_FOLDER"
    )

    print(
        "APPLY: Rayquaza.py "
        "--og ORIGINAL_FILES_FOLDER "
        "--xdelta XDELTA_FILES_FOLDER "
        "--mod TARGET_FOLDER -a\n"
    )


# ============================================================
# MD5
# ============================================================
# Calcola l'hash MD5 di un file.
#
# Viene usato durante la creazione delle patch per capire se
# il file originale e quello modificato sono realmente diversi.
#
# Se gli hash coincidono, Rayquaza non crea inutilmente una patch.
#
def calculate_md5(file_path):
    hash_md5 = hashlib.md5()

    # Il file viene letto a blocchi da 4096 byte invece che
    # tutto in memoria, così funziona anche con file grandi.
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)

    return hash_md5.hexdigest()


# ============================================================
# EXTRACT PATCH
# ============================================================
# Crea le patch XDelta.
#
# Parametri:
#
#   original_files_folder
#       Cartella contenente i file ORIGINALI.
#
#   modified_files_folder
#       Cartella contenente i file MODIFICATI.
#
#   out_xdelta_files_folder
#       Cartella dove salvare le patch generate.
#
#   use_installer
#       Se True, aggiunge "_patch" al nome della patch.
#
# Esempio:
#
#   original/
#       data/file.bin
#
#   modified/
#       data/file.bin
#
#   output/
#       data/file.bin.xdelta
#
# In modalità installer:
#
#   output/
#       data/file.bin_patch.xdelta
#
def extract_patch(
    original_files_folder,
    modified_files_folder,
    out_xdelta_files_folder,
    use_installer
):
    try:
        # Cerca ricorsivamente tutti i file presenti nella
        # cartella dei file modificati.
        for modified_file in Path(modified_files_folder).rglob("*"):

            # Ignora directory e considera solamente file reali.
            if modified_file.is_file():

                # Ottiene il percorso relativo del file rispetto
                # alla cartella dei modificati.
                #
                # Esempio:
                #
                # modified_files_folder = "modified"
                # modified_file = "modified/data/test.bin"
                #
                # relative_path = "data/test.bin"
                #
                relative_path = modified_file.relative_to(
                    modified_files_folder
                )

                # Ricostruisce il percorso equivalente nella cartella
                # degli originali.
                original_file = (
                    Path(original_files_folder) / relative_path
                )

                # Costruisce il percorso della patch.
                #
                # relative_path.as_posix()
                # mantiene la struttura delle sottocartelle.
                #
                # Se use_installer == False:
                #
                #   data/test.bin.xdelta
                #
                # Se use_installer == True:
                #
                #   data/test.bin_patch.xdelta
                #
                out_xdelta_file = (
                    Path(out_xdelta_files_folder)
                    / (
                        relative_path.as_posix()
                        + ("_patch" if use_installer else "")
                        + ".xdelta"
                    )
                )

                # ----------------------------------------------------
                # Controlla che esista il corrispondente file originale
                # ----------------------------------------------------

                if original_file.exists():

                    # Calcola gli hash per capire se il file è cambiato.
                    original_md5 = calculate_md5(original_file)
                    modified_md5 = calculate_md5(modified_file)

                    print(
                        f"Comparing files: "
                        f"{original_file} and {modified_file}"
                    )

                    print(
                        f"Original MD5: {original_md5}"
                    )

                    print(
                        f"Modified MD5: {modified_md5}"
                    )

                    # ------------------------------------------------
                    # Se gli hash sono diversi, crea la patch.
                    # ------------------------------------------------

                    if original_md5 != modified_md5:

                        # Crea automaticamente la struttura delle
                        # sottocartelle necessarie per la patch.
                        out_xdelta_file.parent.mkdir(
                            parents=True,
                            exist_ok=True
                        )

                        # xdelta3 usa:
                        #
                        #   -s ORIGINAL MODIFIED PATCH
                        #
                        # quindi:
                        #
                        #   ORIGINAL = file di partenza
                        #   MODIFIED = file desiderato
                        #   PATCH    = differenza da salvare
                        #
                        command = (
                            f"xdelta3-3.1.0-x86_64.exe "
                            f"-s \"{original_file}\" "
                            f"\"{modified_file}\" "
                            f"\"{out_xdelta_file}\""
                        )

                        print(
                            f"Executing command: {command}"
                        )

                        # Esegue xdelta tramite la shell.
                        #
                        # capture_output=True
                        # cattura stdout e stderr per mostrarli
                        # nei log.
                        #
                        # text=True
                        # restituisce i log come stringhe.
                        result = subprocess.run(
                            command,
                            shell=True,
                            capture_output=True,
                            text=True
                        )

                        if result.stdout:
                            print(
                                f"Command output: {result.stdout}"
                            )

                        if result.stderr:
                            print(
                                f"Command error: {result.stderr}"
                            )

                    else:
                        # Il file modificato è identico all'originale.
                        # Non serve creare alcuna patch.
                        print(
                            f"No changes detected for file: "
                            f"{relative_path}\n"
                        )

                else:
                    # Nella cartella originale non esiste il file
                    # corrispondente.
                    #
                    # IMPORTANTE:
                    # questa versione di Rayquaza non crea un file
                    # completamente nuovo tramite XDelta.
                    print(
                        f"Original file not found: {original_file}"
                    )

    except Exception as e:
        print(f"Exception: {e}")


# ============================================================
# APPLY PATCH
# ============================================================
# Applica le patch XDelta ai file originali.
#
# Parametri:
#
#   original_files_folder
#       Cartella contenente i file ORIGINALI.
#
#   xdelta_files_folder
#       Cartella contenente i file .xdelta.
#
#   target_folder
#       Cartella finale dove verranno copiati i file ricostruiti.
#
# Il procedimento è:
#
#   ORIGINAL + PATCH
#         ↓
#   FILE RICOSTRUITO
#         ↓
#   CARTELLA TEMPORANEA
#         ↓
#   TARGET
#
def apply_patch(
    original_files_folder,
    xdelta_files_folder,
    target_folder
):
    # Crea una cartella temporanea che viene automaticamente
    # cancellata quando termina il blocco "with".
    with tempfile.TemporaryDirectory() as temp_dir:

        temp_dir_path = Path(temp_dir)

        print(
            f"Temporary directory created at: {temp_dir_path}"
        )

        # Cerca ricorsivamente tutte le patch .xdelta.
        for xdelta_file in Path(
            xdelta_files_folder
        ).rglob("*.xdelta"):

            # Calcola il percorso relativo della patch.
            #
            # Esempio:
            #
            # xdelta/data/test.bin.xdelta
            #
            # diventa:
            #
            # data/test.bin.xdelta
            #
            relative_path = xdelta_file.relative_to(
                xdelta_files_folder
            )

            # Rimuove l'estensione ".xdelta" per ottenere
            # il nome del file originale.
            #
            # data/test.bin.xdelta
            #        ↓
            # data/test.bin
            #
            original_file = (
                Path(original_files_folder)
                / relative_path.with_suffix("")
            )

            # File temporaneo che conterrà il risultato
            # dell'applicazione della patch.
            temp_target_file = (
                temp_dir_path
                / relative_path.with_suffix("")
            )

            print(
                f"Processing xdelta file: {xdelta_file}"
            )

            # --------------------------------------------------------
            # Controlla che esista il file originale.
            # --------------------------------------------------------

            if original_file.exists():

                # Crea le sottocartelle necessarie nella directory
                # temporanea.
                temp_target_file.parent.mkdir(
                    parents=True,
                    exist_ok=True
                )

                # xdelta3 in modalità decode:
                #
                #   -d      = decompression/decode
                #   -f      = forza la sovrascrittura del risultato
                #   -s      = specifica il file sorgente originale
                #
                # Risultato:
                #
                #   ORIGINAL + XDELTA = MODIFIED
                #
                command = (
                    f"xdelta3-3.1.0-x86_64.exe "
                    f"-d -f "
                    f"-s \"{original_file}\" "
                    f"\"{xdelta_file}\" "
                    f"\"{temp_target_file}\""
                )

                print(
                    f"Executing command: {command}"
                )

                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True
                )

                if result.stdout:
                    print(
                        f"Command output: {result.stdout}"
                    )

                if result.stderr:
                    print(
                        f"Command error: {result.stderr}"
                    )

            else:
                print(
                    f"Original file not found: {original_file}"
                )

        # ============================================================
        # COPIA DEI FILE RICOSTRUITI
        # ============================================================
        #
        # Le patch vengono applicate inizialmente nella cartella
        # temporanea.
        #
        # Solo dopo che tutti i file sono stati elaborati, i risultati
        # vengono copiati nella cartella target.
        #
        for temp_file in temp_dir_path.rglob("*"):

            if temp_file.is_file():

                # Percorso relativo rispetto alla directory temporanea.
                relative_path = temp_file.relative_to(
                    temp_dir_path
                )

                # Percorso definitivo nel target.
                final_target_file = (
                    Path(target_folder) / relative_path
                )

                # Crea eventuali sottocartelle.
                final_target_file.parent.mkdir(
                    parents=True,
                    exist_ok=True
                )

                print(
                    f"Copying {temp_file} to {final_target_file}"
                )

                # copy2 mantiene anche i metadati del file quando possibile.
                shutil.copy2(
                    temp_file,
                    final_target_file
                )


# ============================================================
# MAIN
# ============================================================
# Gestisce gli argomenti da riga di comando e decide se Rayquaza
# deve:
#
#   - CREARE patch
# oppure
#   - APPLICARE patch
#
def main():

    # ------------------------------------------------------------
    # ARGUMENT PARSER
    # ------------------------------------------------------------

    parser = argparse.ArgumentParser(
        description="Rayquaza Patch Utility"
    )

    # Cartella contenente i file originali.
    parser.add_argument(
        "--og",
        required=True,
        help="Original files folder"
    )

    # In modalità EXTRACT:
    # cartella contenente i file modificati.
    #
    # In modalità APPLY:
    # cartella di destinazione finale.
    parser.add_argument(
        "--mod",
        help="Modified files folder or target folder"
    )

    # Cartella di destinazione delle patch generate.
    parser.add_argument(
        "--out",
        help="Output xdelta files folder"
    )

    # Cartella contenente le patch .xdelta da applicare.
    parser.add_argument(
        "--xdelta",
        help="Xdelta files folder"
    )

    # Se presente, attiva la modalità APPLY.
    parser.add_argument(
        "--a",
        action="store_true",
        help="Apply patch"
    )

    # Se presente, aggiunge "_patch" al nome delle patch generate.
    #
    # È pensato per il funzionamento con V3UPSManager.
    parser.add_argument(
        "--installer",
        action="store_true",
        help="For V3UPSManager"
    )

    args = parser.parse_args()


    # ------------------------------------------------------------
    # CONTROLLO XDELTA
    # ------------------------------------------------------------
    #
    # Rayquaza si aspetta che l'eseguibile xdelta si trovi
    # nella stessa directory da cui viene eseguito lo script.
    #
    if not Path(
        "xdelta3-3.1.0-x86_64.exe"
    ).exists():

        print(
            "XDelta patcher couldn't be found!"
        )

        return 1


    print(
        f"Arguments received: {args}"
    )


    # ============================================================
    # APPLY MODE
    # ============================================================

    if args.a:

        # Per applicare una patch servono:
        #
        #   --og       = file originali
        #   --xdelta   = patch
        #   --mod     = cartella target
        #
        if not args.og or not args.mod or not args.xdelta:

            print(
                "Not enough args!"
            )

            explain_usage()

            return 1


        apply_patch(
            args.og,
            args.xdelta,
            args.mod
        )


    # ============================================================
    # EXTRACT MODE
    # ============================================================

    else:

        # Per creare patch servono:
        #
        #   --og  = file originali
        #   --mod = file modificati
        #   --out = cartella di output delle patch
        #
        if not args.og or not args.mod or not args.out:

            print(
                "Not enough args!"
            )

            explain_usage()

            return 1


        extract_patch(
            args.og,
            args.mod,
            args.out,
            args.installer
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    # Stampa gli argomenti ricevuti dal sistema prima ancora
    # che argparse li elabori.
    #
    # Utile per capire esattamente cosa è stato passato
    # allo script.
    print(
        f"Arguments before parsing: {sys.argv}"
    )

    main()