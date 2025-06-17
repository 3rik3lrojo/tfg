import sys
from pathlib import Path

def format_cell(val1, val2):
    """Devuelve el contenido de la celda en formato hexadecimal, con color si hay diferencia."""
    if val1 == val2:
        return f"\\textbf{{{val2:02X}}}"
    else:
        return f"\\cellcolor{{diffcolor}}\\textbf{{{val2:02X}}}"

def generate_latex_table_block(data1, data2, offset, sector, block, file1, file2):
    row1 = " & " + " & ".join(f"{b:02X}" for b in data1) + " \\\\"
    row2 = " & " + " & ".join(format_cell(data1[i], data2[i]) for i in range(16)) + " \\\\"

    header = f"""
\\begin{{table}}[H]
\\centering
\\renewcommand{{\\arraystretch}}{{1.4}}
\\setlength{{\\tabcolsep}}{{4pt}}

% --- Cabecera de columnas ---
\\begin{{tabular}}{{|c|c|*{{16}}{{c}}|}}
\\hline
\\shortstack{{\\textbf{{Sector}} \\\\ \\textbf{{Bloque}}}} & \\shortstack{{\\textbf{{Archivo 1}} \\\\ \\textbf{{Archivo 2}}}} & \\multicolumn{{16}}{{c|}}{{\\textbf{{Bytes (offset relativo)}}}} \\\\
\\hline
& & """ + " & ".join(f"\\textbf{{{i:X}}}" for i in range(16)) + " \\\\\n\\hline\n"

    rows = f"\\multirow{{2}}{{*}}{{\\shortstack{{\\textbf{{Sector {sector}}} \\\\ \\textbf{{Bloque {block}}}}}}} & \\shortstack{{ \\\\ \\texttt{{{file1}}}}} {row1}\n"
    rows += f"& \\shortstack{{\\texttt{{{file2}}}}} {row2}\n\\hline\n"

    footer = f"""\\end{{tabular}}
\\caption{{Diferencias en el sector {sector}, bloque {block} }}
\\end{{table}}
"""
    return header + rows + footer

def generate_full_latex_document(tables_latex, file1, file2):
    return f"""\\documentclass{{article}}
\\usepackage[table]{{xcolor}}
\\usepackage{{geometry}}
\\usepackage{{array}}
\\usepackage{{caption}}
\\usepackage{{multirow}}
\\geometry{{margin=1in}}
\\definecolor{{diffcolor}}{{RGB}}{{255,220,220}}

\\begin{{document}}

\\section*{{Comparación sectorial: \\texttt{{{file1}}} (izq.) vs \\texttt{{{file2}}} (der.)}}

{tables_latex}
\\end{{document}}
"""

def generate_diff_tables(data1, data2, file1, file2):
    output = ""
    for i in range(0, len(data1), 16):
        chunk1 = data1[i:i+16]
        chunk2 = data2[i:i+16]
        if chunk1 != chunk2:
            sector = i // 64
            block = (i % 64) // 16
            output += generate_latex_table_block(chunk1, chunk2, i, sector, block, file1, file2)
    return output

def main(file1_path, file2_path):
    data1 = Path(file1_path).read_bytes()
    data2 = Path(file2_path).read_bytes()
    if len(data1) != len(data2):
        raise ValueError("Los archivos deben tener la misma longitud")

    file1 = Path(file1_path).name
    file2 = Path(file2_path).name

    latex_tables = generate_diff_tables(data1, data2, file1, file2)
    full_doc = generate_full_latex_document(latex_tables, file1, file2)
    Path("diff_output.tex").write_text(full_doc, encoding="utf-8")
    print("✅ Archivo LaTeX generado: diff_output.tex")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python generate_diff_tex.py archivo1.bin archivo2.bin")
    else:
        main(sys.argv[1], sys.argv[2])
