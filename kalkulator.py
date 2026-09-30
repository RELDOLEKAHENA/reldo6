
import ast
import operator
import tkinter as tk
from tkinter import messagebox

# ---------- Evaluasi ekspresi aman ----------
_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}


def _eval_node(node):
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        val = _eval_node(node.operand)
        return -val if isinstance(node.op, ast.USub) else val
    raise ValueError("Ekspresi tidak valid")


def hitung(ekspresi: str):
    """Hitung ekspresi matematika sederhana secara aman."""
    ekspresi = ekspresi.replace("×", "*").replace("÷", "/").replace(",", ".")
    return _eval_node(ast.parse(ekspresi, mode="eval"))


def format_angka(x) -> str:
    """Format hasil: hilangkan .0, batasi digit desimal."""
    if isinstance(x, float):
        if x.is_integer() and abs(x) < 1e15:
            return str(int(x))
        return f"{x:.10g}".replace(".", ",")
    return str(x)


# ---------- Aplikasi GUI ----------
class KalkulatorApp(tk.Tk):
    # Warna tema
    BG = "#1e1f26"
    DISPLAY_BG = "#14151a"
    BTN_NUM = "#2d2f3a"
    BTN_NUM_HOVER = "#3a3d4c"
    BTN_OP = "#ff9f43"
    BTN_OP_HOVER = "#ffb56b"
    BTN_FUNC = "#4a4e63"
    BTN_FUNC_HOVER = "#5d6280"
    BTN_EQ = "#1dd1a1"
    BTN_EQ_HOVER = "#48e3bb"
    FG = "#f1f2f6"

    OPERATORS = ("+", "-", "×", "÷")

    def __init__(self):
        super().__init__()
        self.title("Kalkulator Desktop")
        self.configure(bg=self.BG)
        self.resizable(False, False)

        self.ekspresi = ""      # ekspresi yang sedang diketik
        self.sudah_hasil = False  # True jika layar menampilkan hasil "="

        self._buat_display()
        self._buat_tombol()
        self._bind_keyboard()
        self._update_display()

    # ----- Tampilan -----
    def _buat_display(self):
        frame = tk.Frame(self, bg=self.DISPLAY_BG, padx=12, pady=10)
        frame.grid(row=0, column=0, padx=12, pady=(12, 6), sticky="nsew")

        self.lbl_riwayat = tk.Label(
            frame, text="", anchor="e", bg=self.DISPLAY_BG, fg="#8a8fa3",
            font=("Segoe UI", 12), width=22,
        )
        self.lbl_riwayat.pack(fill="x")

        self.lbl_layar = tk.Label(
            frame, text="0", anchor="e", bg=self.DISPLAY_BG, fg=self.FG,
            font=("Segoe UI", 30, "bold"), width=14,
        )
        self.lbl_layar.pack(fill="x")

    def _buat_tombol(self):
        grid = tk.Frame(self, bg=self.BG)
        grid.grid(row=1, column=0, padx=12, pady=(0, 12))

        # (teks, baris, kolom, jenis, perintah)
        layout = [
            ("C", 0, 0, "func", self.clear),
            ("⌫", 0, 1, "func", self.backspace),
            ("%", 0, 2, "func", self.persen),
            ("÷", 0, 3, "op", lambda: self.tekan_operator("÷")),
            ("7", 1, 0, "num", lambda: self.tekan_angka("7")),
            ("8", 1, 1, "num", lambda: self.tekan_angka("8")),
            ("9", 1, 2, "num", lambda: self.tekan_angka("9")),
            ("×", 1, 3, "op", lambda: self.tekan_operator("×")),
            ("4", 2, 0, "num", lambda: self.tekan_angka("4")),
            ("5", 2, 1, "num", lambda: self.tekan_angka("5")),
            ("6", 2, 2, "num", lambda: self.tekan_angka("6")),
            ("-", 2, 3, "op", lambda: self.tekan_operator("-")),
            ("1", 3, 0, "num", lambda: self.tekan_angka("1")),
            ("2", 3, 1, "num", lambda: self.tekan_angka("2")),
            ("3", 3, 2, "num", lambda: self.tekan_angka("3")),
            ("+", 3, 3, "op", lambda: self.tekan_operator("+")),
            ("±", 4, 0, "num", self.ganti_tanda),
            ("0", 4, 1, "num", lambda: self.tekan_angka("0")),
            (",", 4, 2, "num", self.tekan_desimal),
            ("=", 4, 3, "eq", self.sama_dengan),
        ]

        warna = {
            "num": (self.BTN_NUM, self.BTN_NUM_HOVER),
            "op": (self.BTN_OP, self.BTN_OP_HOVER),
            "func": (self.BTN_FUNC, self.BTN_FUNC_HOVER),
            "eq": (self.BTN_EQ, self.BTN_EQ_HOVER),
        }

        for teks, r, c, jenis, cmd in layout:
            normal, hover = warna[jenis]
            btn = tk.Button(
                grid, text=teks, command=cmd, width=5, height=2,
                bg=normal, fg=self.FG if jenis != "eq" else "#0b1d17",
                activebackground=hover, activeforeground=self.FG,
                font=("Segoe UI", 16, "bold"), bd=0, relief="flat", cursor="hand2",
            )
            btn.grid(row=r, column=c, padx=4, pady=4, sticky="nsew")
            btn.bind("<Enter>", lambda e, b=btn, h=hover: b.config(bg=h))
            btn.bind("<Leave>", lambda e, b=btn, n=normal: b.config(bg=n))

    def _bind_keyboard(self):
        self.bind("<Key>", self._on_key)
        self.bind("<Return>", lambda e: self.sama_dengan())
        self.bind("<KP_Enter>", lambda e: self.sama_dengan())
        self.bind("<BackSpace>", lambda e: self.backspace())
        self.bind("<Escape>", lambda e: self.clear())
        self.bind("<Delete>", lambda e: self.clear())

    def _on_key(self, event):
        ch = event.char
        if ch.isdigit():
            self.tekan_angka(ch)
        elif ch in (".", ","):
            self.tekan_desimal()
        elif ch in ("+", "-"):
            self.tekan_operator(ch)
        elif ch == "*":
            self.tekan_operator("×")
        elif ch == "/":
            self.tekan_operator("÷")
        elif ch == "%":
            self.persen()
        elif ch == "=":
            self.sama_dengan()

    # ----- Logika -----
    def _angka_terakhir(self) -> str:
        """Ambil angka terakhir pada ekspresi."""
        i = len(self.ekspresi)
        while i > 0 and (self.ekspresi[i - 1].isdigit() or self.ekspresi[i - 1] == ","):
            i -= 1
        return self.ekspresi[i:]

    def tekan_angka(self, d):
        if self.sudah_hasil:
            self.ekspresi = ""
            self.sudah_hasil = False
        # Cegah angka nol di depan (mis. 007)
        if self._angka_terakhir() == "0" and d == "0":
            return
        if self._angka_terakhir() == "0" and d != "0":
            self.ekspresi = self.ekspresi[:-1]
        self.ekspresi += d
        self._update_display()

    def tekan_desimal(self):
        if self.sudah_hasil:
            self.ekspresi = ""
            self.sudah_hasil = False
        terakhir = self._angka_terakhir()
        if "," in terakhir:
            return
        if terakhir == "":
            self.ekspresi += "0"
        self.ekspresi += ","
        self._update_display()

    def tekan_operator(self, op):
        self.sudah_hasil = False
        if not self.ekspresi:
            if op == "-":            # izinkan angka negatif di awal
                self.ekspresi = "-"
                self._update_display()
            return
        if self.ekspresi == "-":
            return
        if self.ekspresi[-1] in self.OPERATORS:
            self.ekspresi = self.ekspresi[:-1] + op   # ganti operator
        elif self.ekspresi[-1] == ",":
            self.ekspresi = self.ekspresi[:-1] + op
        else:
            self.ekspresi += op
        self._update_display()

    def persen(self):
        angka = self._angka_terakhir()
        if not angka:
            return
        try:
            nilai = float(angka.replace(",", ".")) / 100
        except ValueError:
            return
        self.ekspresi = self.ekspresi[: len(self.ekspresi) - len(angka)] + format_angka(nilai)
        self.sudah_hasil = False
        self._update_display()

    def ganti_tanda(self):
        self.sudah_hasil = False
        angka = self._angka_terakhir()
        if not angka:
            return
        awal = self.ekspresi[: len(self.ekspresi) - len(angka)]
        # Minus unary = "-" di awal ekspresi atau tepat setelah operator lain
        unary = awal.endswith("-") and (len(awal) == 1 or awal[-2] in self.OPERATORS)
        if unary:
            awal = awal[:-1]           # jadikan positif
        else:
            awal += "-"                # jadikan negatif
        self.ekspresi = awal + angka
        self._update_display()

    def backspace(self):
        if self.sudah_hasil:
            self.clear()
            return
        self.ekspresi = self.ekspresi[:-1]
        self._update_display()

    def clear(self):
        self.ekspresi = ""
        self.sudah_hasil = False
        self.lbl_riwayat.config(text="")
        self._update_display()

    def sama_dengan(self):
        if not self.ekspresi or self.sudah_hasil:
            return
        ekspr = self.ekspresi
        while ekspr and (ekspr[-1] in self.OPERATORS or ekspr[-1] == ","):
            ekspr = ekspr[:-1]
        if not ekspr or ekspr == "-":
            return
        try:
            hasil = hitung(ekspr)
            self.lbl_riwayat.config(text=ekspr + " =")
            self.ekspresi = format_angka(hasil)
            self.sudah_hasil = True
        except ZeroDivisionError:
            messagebox.showerror("Kesalahan", "Tidak bisa membagi dengan nol.")
            self.lbl_riwayat.config(text="")
            self.ekspresi = ""
            self.sudah_hasil = False
        except (ValueError, SyntaxError):
            messagebox.showerror("Kesalahan", "Ekspresi tidak valid.")
            self.ekspresi = ""
        self._update_display()

    def _update_display(self):
        teks = self.ekspresi or "0"
        self.lbl_layar.config(text=teks)
        # Perkecil font jika teks panjang
        ukuran = 30 if len(teks) <= 11 else 22 if len(teks) <= 16 else 16
        self.lbl_layar.config(font=("Segoe UI", ukuran, "bold"))


if __name__ == "__main__":
    KalkulatorApp().mainloop()
