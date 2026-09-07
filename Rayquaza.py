import argparse
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


# ============================================================
# PATHS / TOOLS
# ============================================================

# Directory dove si trova Rayquaza.py.
SCRIPT_DIR = Path(__file__).resolve().parent

# Eseguibili richiesti dai due formati.
XDELTA_EXE = SCRIPT_DIR / "xdelta3-3.1.0-x86_64.exe"
UPS_EXE = SCRIPT_DIR / "ups.exe"


# ============================================================
# USAGE
# ============================================================

def explain_usage():
    print(
        "EXTRACT:"
    )

    print(
        "  Rayquaza.py "
        "--og ORIGINAL_FILES_FOLDER "
        "--mod MODIFIED_FILES_FOLDER "
        "--out OUT_PATCH_FILES_FOLDER"
    )

    print(
        "  opzionale: --format xdelta"
    )

    print(
        "  opzionale: --format ups"
    )

    print()

    print(
        "APPLY:"
    )

    print(
        "  Rayquaza.py "
        "--og ORIGINAL_FILES_FOLDER "
        "--xdelta PATCH_FILES_FOLDER "
        "--mod TARGET_FOLDER "
        "-a"
    )

    print(
        "  oppure:"
    )

    print(
        "  Rayquaza.py "
        "--og ORIGINAL_FILES_FOLDER "
        "--xdelta PATCH_FILES_FOLDER "
        "--mod TARGET_FOLDER "
        "-a --format xdelta"
    )

    print(
        "  oppure:"
    )

    print(
        "  Rayquaza.py "
        "--og ORIGINAL_FILES_FOLDER "
        "--xdelta PATCH_FILES_FOLDER "
        "--mod TARGET_FOLDER "
        "-a --format ups"
    )

    print()


# ============================================================
# PATCH FORMAT SELECTION
# ============================================================

def choose_patch_format(requested_format=None):
    """
    Determina il formato patch da utilizzare.

    Se --format è stato specificato, viene usato direttamente.

    Altrimenti viene mostrato un menu interattivo:

        1 = XDelta
        2 = UPS
    """

    if requested_format:
        patch_format = requested_format.strip().lower()

        if patch_format not in {"xdelta", "ups"}:
            raise ValueError(
                f"Unsupported patch format: {requested_format}"
            )

        return patch_format

    print()
    print(
        "============================================================"
    )
    print(
        "RAYQUAZA PATCH FORMAT"
    )
    print(
        "============================================================"
    )
    print(
        "[1] XDelta"
    )
    print(
        "[2] UPS"
    )
    print()

    while True:
        choice = input(
            "Choose patch format [1/2]: "
        ).strip()

        if choice == "1":
            return "xdelta"

        if choice == "2":
            return "ups"

        print(
            "Invalid choice. Enter 1 for XDelta or 2 for UPS."
        )


# ============================================================
# TOOL PATH
# ============================================================

def get_patch_tool(patch_format):
    """
    Restituisce il percorso dell'eseguibile associato al formato.
    """

    if patch_format == "xdelta":
        return XDELTA_EXE

    if patch_format == "ups":
        return UPS_EXE

    raise ValueError(
        f"Unsupported patch format: {patch_format}"
    )


def check_patch_tool(patch_format):
    """
    Verifica che l'eseguibile necessario sia presente nella
    stessa cartella di Rayquaza.py.
    """

    tool = get_patch_tool(
        patch_format
    )

    if not tool.is_file():
        raise FileNotFoundError(
            f"{patch_format.upper()} patcher not found:\n"
            f"{tool}"
        )

    print(
        f"[RAYQUAZA] {patch_format.upper()} tool: {tool}"
    )

    return tool


# ============================================================
# MD5
# ============================================================

def calculate_md5(file_path):
    """
    Calcola l'MD5 di un file leggendo il contenuto a blocchi.
    """

    hash_md5 = hashlib.md5()

    with open(
        file_path,
        "rb"
    ) as f:

        for chunk in iter(
            lambda: f.read(4096),
            b""
        ):
            hash_md5.update(
                chunk
            )

    return hash_md5.hexdigest()


# ============================================================
# EXTRACT PATCH
# ============================================================

def extract_patch(
    original_files_folder,
    modified_files_folder,
    out_patch_files_folder,
    use_installer,
    patch_format
):
    """
    Confronta ORIGINAL con MODIFIED e crea una patch per ogni
    file modificato.

    Formato XDelta:

        file.bin.xdelta

    Formato UPS:

        file.bin.ups

    Con --installer:

        file.bin_patch.xdelta
        file.bin_patch.ups

    Viene inoltre creato:

        report.txt
    """

    # --------------------------------------------------------
    # REPORT DATA
    # --------------------------------------------------------

    patched_files = []
    ignored_files = []
    missing_original_files = []
    failed_files = []

    try:
        # ----------------------------------------------------
        # OUTPUT ROOT
        # ----------------------------------------------------

        output_root = Path(
            out_patch_files_folder
        )

        output_root.mkdir(
            parents=True,
            exist_ok=True
        )

        # ----------------------------------------------------
        # TOOL
        # ----------------------------------------------------

        patch_tool = check_patch_tool(
            patch_format
        )

        print()
        print(
            f"[RAYQUAZA] Creating {patch_format.upper()} patches..."
        )

        # ----------------------------------------------------
        # SCAN MODIFIED FILES
        # ----------------------------------------------------

        for modified_file in Path(
            modified_files_folder
        ).rglob("*"):

            if not modified_file.is_file():
                continue

            # ------------------------------------------------
            # RELATIVE PATH
            # ------------------------------------------------

            relative_path = modified_file.relative_to(
                modified_files_folder
            )

            # ------------------------------------------------
            # ORIGINAL
            # ------------------------------------------------

            original_file = (
                Path(original_files_folder)
                / relative_path
            )

            # ------------------------------------------------
            # PATCH NAME
            # ------------------------------------------------

            patch_extension = (
                ".xdelta"
                if patch_format == "xdelta"
                else ".ups"
            )

            patch_suffix = (
                "_patch"
                if use_installer
                else ""
            )

            patch_name = (
                relative_path.as_posix()
                + patch_suffix
                + patch_extension
            )

            out_patch_file = (
                output_root
                / patch_name
            )

            # =================================================
            # MISSING ORIGINAL
            # =================================================

            if not original_file.exists():

                print(
                    f"Original file not found: "
                    f"{original_file}"
                )

                missing_original_files.append(
                    str(relative_path)
                )

                continue

            # =================================================
            # MD5
            # =================================================

            try:
                original_md5 = calculate_md5(
                    original_file
                )

                modified_md5 = calculate_md5(
                    modified_file
                )

            except Exception as e:

                print(
                    f"ERROR calculating MD5 for "
                    f"{relative_path}: {e}"
                )

                failed_files.append({
                    "path": str(relative_path),
                    "reason": f"MD5 error: {e}"
                })

                continue

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

            # =================================================
            # IDENTICAL
            # =================================================

            if original_md5 == modified_md5:

                print(
                    f"No changes detected for file: "
                    f"{relative_path}"
                )

                ignored_files.append({
                    "path": str(relative_path),
                    "md5": original_md5
                })

                continue

            # =================================================
            # PREPARE OUTPUT
            # =================================================

            out_patch_file.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            # =================================================
            # CREATE PATCH
            # =================================================

            if patch_format == "xdelta":

                # ---------------------------------------------
                # XDELTA
                # ---------------------------------------------
                #
                # xdelta3:
                #
                #   -s BASE MODIFIED PATCH
                #

                command = [
                    str(patch_tool),
                    "-s",
                    str(original_file),
                    str(modified_file),
                    str(out_patch_file)
                ]

            else:

                # ---------------------------------------------
                # UPS
                # ---------------------------------------------
                #
                # ups:
                #
                #   diff
                #       --base
                #       --modified
                #       --output
                #

                command = [
                    str(patch_tool),
                    "diff",
                    "--base",
                    str(original_file),
                    "--modified",
                    str(modified_file),
                    "--output",
                    str(out_patch_file)
                ]

            print(
                "[RAYQUAZA] Executing:"
            )

            print(
                "  "
                + subprocess.list2cmdline(
                    command
                )
            )

            # =================================================
            # EXECUTE PATCHER
            # =================================================

            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True
                )

            except Exception as e:

                print(
                    f"ERROR executing {patch_format.upper()} "
                    f"for {relative_path}: {e}"
                )

                failed_files.append({
                    "path": str(relative_path),
                    "reason": (
                        f"{patch_format.upper()} "
                        f"execution error: {e}"
                    )
                })

                continue

            # -------------------------------------------------
            # STDOUT
            # -------------------------------------------------

            if result.stdout:
                print(
                    f"Command output: "
                    f"{result.stdout}"
                )

            # -------------------------------------------------
            # STDERR
            # -------------------------------------------------

            if result.stderr:
                print(
                    f"Command error: "
                    f"{result.stderr}"
                )

            # =================================================
            # CHECK RESULT
            # =================================================

            if (
                result.returncode == 0
                and out_patch_file.exists()
            ):

                patch_relative = (
                    out_patch_file.relative_to(
                        output_root
                    )
                )

                print(
                    f"Patch created successfully: "
                    f"{out_patch_file}"
                )

                patched_files.append({
                    "path": str(relative_path),
                    "original_md5": original_md5,
                    "modified_md5": modified_md5,
                    "patch": str(
                        patch_relative
                    )
                })

            else:

                reason = (
                    f"{patch_format.upper()} "
                    f"exit code: "
                    f"{result.returncode}"
                )

                print(
                    f"FAILED creating patch for "
                    f"{relative_path}: {reason}"
                )

                failed_files.append({
                    "path": str(relative_path),
                    "reason": reason
                })

    except Exception as e:

        print(
            f"Exception during extract: {e}"
        )

        failed_files.append({
            "path": "<GLOBAL>",
            "reason": str(e)
        })

    # ========================================================
    # GENERATE REPORT
    # ========================================================

    report_path = (
        Path(out_patch_files_folder)
        / "report.txt"
    )

    try:
        with open(
            report_path,
            "w",
            encoding="utf-8"
        ) as report:

            report.write(
                "============================================================\n"
            )

            report.write(
                "RAYQUAZA PATCH REPORT\n"
            )

            report.write(
                "============================================================\n\n"
            )

            # ------------------------------------------------
            # CONFIGURATION
            # ------------------------------------------------

            report.write(
                f"Patch format: {patch_format.upper()}\n"
            )

            report.write(
                f"Installer mode: "
                f"{'YES' if use_installer else 'NO'}\n"
            )

            report.write("\n")

            # ------------------------------------------------
            # SUMMARY
            # ------------------------------------------------

            report.write(
                "SUMMARY\n"
            )

            report.write(
                "------------------------------------------------------------\n"
            )

            report.write(
                f"Patched files:           "
                f"{len(patched_files)}\n"
            )

            report.write(
                f"Ignored identical files: "
                f"{len(ignored_files)}\n"
            )

            report.write(
                f"Missing original files:  "
                f"{len(missing_original_files)}\n"
            )

            report.write(
                f"Failed files:            "
                f"{len(failed_files)}\n"
            )

            report.write("\n")

            # ------------------------------------------------
            # PATCHED
            # ------------------------------------------------

            report.write(
                "PATCHED FILES\n"
            )

            report.write(
                "------------------------------------------------------------\n"
            )

            if patched_files:

                for item in patched_files:

                    report.write(
                        f"{item['path']}\n"
                    )

                    report.write(
                        f"  Original MD5: "
                        f"{item['original_md5']}\n"
                    )

                    report.write(
                        f"  Modified MD5: "
                        f"{item['modified_md5']}\n"
                    )

                    report.write(
                        f"  Patch:        "
                        f"{item['patch']}\n"
                    )

                    report.write("\n")

            else:

                report.write(
                    "None\n\n"
                )

            # ------------------------------------------------
            # IGNORED
            # ------------------------------------------------

            report.write(
                "IGNORED - IDENTICAL MD5\n"
            )

            report.write(
                "------------------------------------------------------------\n"
            )

            if ignored_files:

                for item in ignored_files:

                    report.write(
                        f"{item['path']}\n"
                    )

                    report.write(
                        f"  MD5: {item['md5']}\n"
                    )

                    report.write("\n")

            else:

                report.write(
                    "None\n\n"
                )

            # ------------------------------------------------
            # MISSING ORIGINAL
            # ------------------------------------------------

            report.write(
                "MISSING ORIGINAL FILES\n"
            )

            report.write(
                "------------------------------------------------------------\n"
            )

            if missing_original_files:

                for path in missing_original_files:

                    report.write(
                        f"{path}\n"
                    )

            else:

                report.write(
                    "None\n"
                )

            report.write("\n")

            # ------------------------------------------------
            # FAILED
            # ------------------------------------------------

            report.write(
                "FAILED FILES\n"
            )

            report.write(
                "------------------------------------------------------------\n"
            )

            if failed_files:

                for item in failed_files:

                    report.write(
                        f"{item['path']}\n"
                    )

                    report.write(
                        f"  Reason: "
                        f"{item['reason']}\n"
                    )

                    report.write("\n")

            else:

                report.write(
                    "None\n"
                )

            report.write("\n")

            report.write(
                "============================================================\n"
            )

        print(
            f"[RAYQUAZA] Report saved to: {report_path}"
        )

    except Exception as e:

        print(
            f"[RAYQUAZA] ERROR writing report: {e}"
        )


# ============================================================
# APPLY PATCH
# ============================================================

def apply_patch(
    original_files_folder,
    patch_files_folder,
    target_folder,
    patch_format
):
    """
    Applica le patch del formato selezionato.

    XDelta:

        xdelta3 -d -f
            -s ORIGINAL
            PATCH
            OUTPUT

    UPS:

        ups.exe apply
            --base ORIGINAL
            --patch PATCH
            --output OUTPUT
    """

    with tempfile.TemporaryDirectory() as temp_dir:

        temp_dir_path = Path(
            temp_dir
        )

        print(
            f"Temporary directory created at: "
            f"{temp_dir_path}"
        )

        # ----------------------------------------------------
        # TOOL
        # ----------------------------------------------------

        patch_tool = check_patch_tool(
            patch_format
        )

        # ----------------------------------------------------
        # PATCH EXTENSION
        # ----------------------------------------------------

        patch_extension = (
            "*.xdelta"
            if patch_format == "xdelta"
            else "*.ups"
        )

        # ----------------------------------------------------
        # PROCESS PATCHES
        # ----------------------------------------------------

        for patch_file in Path(
            patch_files_folder
        ).rglob(
            patch_extension
        ):

            relative_path = (
                patch_file.relative_to(
                    patch_files_folder
                )
            )

            # ------------------------------------------------
            # REMOVE PATCH EXTENSION
            # ------------------------------------------------
            #
            # Esempio:
            #
            # file.bin.xdelta
            #     ↓
            # file.bin
            #
            # file.bin.ups
            #     ↓
            # file.bin
            #
            #

            original_relative_path = (
                relative_path.with_suffix("")
            )

            # ------------------------------------------------
            # REMOVE _patch FOR INSTALLER PATCHES
            # ------------------------------------------------
            #
            # Esempio:
            #
            # file.bin_patch.ups
            #
            # deve diventare:
            #
            # file.bin
            #
            #

            filename = original_relative_path.name

            if filename.endswith("_patch"):
                filename = filename[:-6]

                original_relative_path = (
                    original_relative_path.with_name(
                        filename
                    )
                )

            # ------------------------------------------------
            # ORIGINAL
            # ------------------------------------------------

            original_file = (
                Path(original_files_folder)
                / original_relative_path
            )

            # ------------------------------------------------
            # TEMP TARGET
            # ------------------------------------------------

            temp_target_file = (
                temp_dir_path
                / original_relative_path
            )

            print(
                f"Processing patch: {patch_file}"
            )

            print(
                f"Original file: {original_file}"
            )

            # =================================================
            # MISSING ORIGINAL
            # =================================================

            if not original_file.exists():

                print(
                    f"Original file not found: "
                    f"{original_file}"
                )

                continue

            # ------------------------------------------------
            # OUTPUT DIRECTORY
            # ------------------------------------------------

            temp_target_file.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            # =================================================
            # APPLY PATCH
            # =================================================

            if patch_format == "xdelta":

                # ---------------------------------------------
                # XDELTA
                # ---------------------------------------------

                command = [
                    str(patch_tool),
                    "-d",
                    "-f",
                    "-s",
                    str(original_file),
                    str(patch_file),
                    str(temp_target_file)
                ]

            else:

                # ---------------------------------------------
                # UPS
                # ---------------------------------------------

                command = [
                    str(patch_tool),
                    "apply",
                    "--base",
                    str(original_file),
                    "--patch",
                    str(patch_file),
                    "--output",
                    str(temp_target_file)
                ]

            print(
                "[RAYQUAZA] Executing:"
            )

            print(
                "  "
                + subprocess.list2cmdline(
                    command
                )
            )

            result = subprocess.run(
                command,
                capture_output=True,
                text=True
            )

            if result.stdout:
                print(
                    f"Command output: "
                    f"{result.stdout}"
                )

            if result.stderr:
                print(
                    f"Command error: "
                    f"{result.stderr}"
                )

            # ------------------------------------------------
            # CHECK RESULT
            # ------------------------------------------------

            if (
                result.returncode != 0
                or not temp_target_file.exists()
            ):

                print(
                    f"[RAYQUAZA] FAILED applying patch: "
                    f"{patch_file}"
                )

                continue

            print(
                f"[RAYQUAZA] Patch applied successfully: "
                f"{patch_file}"
            )

        # ====================================================
        # COPY GENERATED FILES TO TARGET
        # ====================================================

        print(
            "[RAYQUAZA] Copying generated files to target..."
        )

        for temp_file in temp_dir_path.rglob("*"):

            if not temp_file.is_file():
                continue

            relative_path = (
                temp_file.relative_to(
                    temp_dir_path
                )
            )

            final_target_file = (
                Path(target_folder)
                / relative_path
            )

            final_target_file.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            print(
                f"Copying {temp_file} "
                f"to {final_target_file}"
            )

            shutil.copy2(
                temp_file,
                final_target_file
            )


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # ARGUMENT PARSER
    # --------------------------------------------------------

    parser = argparse.ArgumentParser(
        description="Rayquaza Patch Utility"
    )

    parser.add_argument(
        "--og",
        required=True,
        help="Original files folder"
    )

    parser.add_argument(
        "--mod",
        help="Modified files folder or target folder"
    )

    parser.add_argument(
        "--out",
        help="Output patch files folder"
    )

    parser.add_argument(
        "--xdelta",
        help="Patch files folder"
    )

    parser.add_argument(
        "-a",
        "--apply",
        action="store_true",
        help="Apply patch"
    )

    parser.add_argument(
        "--installer",
        action="store_true",
        help="For V3UPSManager"
    )

    parser.add_argument(
        "--format",
        choices=[
            "xdelta",
            "ups"
        ],
        help=(
            "Patch format. "
            "If omitted, Rayquaza asks interactively."
        )
    )

    args = parser.parse_args()

    # --------------------------------------------------------
    # SELECT FORMAT
    # --------------------------------------------------------

    try:
        patch_format = choose_patch_format(
            args.format
        )
    except ValueError as e:
        print(
            f"ERROR: {e}"
        )

        return 1

    print(
        f"[RAYQUAZA] Selected format: "
        f"{patch_format.upper()}"
    )

    # --------------------------------------------------------
    # CHECK TOOL
    # --------------------------------------------------------

    try:
        check_patch_tool(
            patch_format
        )
    except FileNotFoundError as e:
        print(
            f"ERROR: {e}"
        )

        return 1

    print(
        f"Arguments received: {args}"
    )

    # ========================================================
    # APPLY
    # ========================================================

    if args.apply:

        if (
            not args.og
            or not args.mod
            or not args.xdelta
        ):
            print(
                "Not enough args!"
            )

            explain_usage()

            return 1

        try:
            apply_patch(
                args.og,
                args.xdelta,
                args.mod,
                patch_format
            )
        except Exception as e:
            print(
                f"ERROR during patch application: {e}"
            )

            return 1

    # ========================================================
    # EXTRACT
    # ========================================================

    else:

        if (
            not args.og
            or not args.mod
            or not args.out
        ):
            print(
                "Not enough args!"
            )

            explain_usage()

            return 1

        try:
            extract_patch(
                args.og,
                args.mod,
                args.out,
                args.installer,
                patch_format
            )
        except Exception as e:
            print(
                f"ERROR during patch extraction: {e}"
            )

            return 1

    return 0


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    print(
        f"Arguments before parsing: "
        f"{sys.argv}"
    )

    sys.exit(
        main()
    )