import math
import re
import tkinter as tk
from tkinter import messagebox


# ---------- Evaluasi ekspresi aman (parser rekursif) ----------
class KesalahanHitung(ValueError):
    """Kesalahan perhitungan dengan pesan yang bisa ditampilkan ke pengguna."""


class Parser:
    FUNGSI = {"sin", "cos", "tan", "asin", "acos", "atan", "lg", "ln", "sqrt"}
    KONSTANTA = {"pi": math.pi, "e": math.e}

    def __init__(self, tokens, derajat=True):
        self.tokens = tokens
        self.pos = 0
        self.derajat = derajat

    # -- util token --
    def _lihat(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _ambil(self):
        t = self._lihat()
        self.pos += 1
        return t

    def _harap(self, simbol):
        if self._ambil() != simbol:
            raise KesalahanHitung("Ekspresi tidak valid.")

    # -- tata bahasa --
    def parse(self):
        nilai = self._ekspresi()
        if self.pos != len(self.tokens):
            raise KesalahanHitung("Ekspresi tidak valid.")
        return nilai

    def _ekspresi(self):
        v = self._suku()
        while self._lihat() in ("+", "-"):
            op = self._ambil()
            r = self._suku()
            v = v + r if op == "+" else v - r
        return v

    def _suku(self):
        v = self._unary()
        while True:
            t = self._lihat()
            if t in ("*", "/"):
                self._ambil()
                r = self._unary()
                if t == "/":
                    if r == 0:
                        raise ZeroDivisionError
                    v = v / r
                else:
                    v = v * r
            elif t is not None and (t == "(" or t[0].isdigit() or t[0].isalpha()):
                v = v * self._unary()        # perkalian implisit: 2π, 3(4+1), 2sin(30)
            else:
                return v

    def _unary(self):
        t = self._lihat()
        if t == "-":
            self._ambil()
            return -self._unary()
        if t == "+":
            self._ambil()
            return self._unary()
        return self._pangkat()

    def _pangkat(self):
        a = self._postfix()
        if self._lihat() == "^":
            self._ambil()
            b = self._unary()                # asosiatif kanan
            return self._hitung_pangkat(a, b)
        return a

    def _postfix(self):
        v = self._primer()
        while self._lihat() == "!":
            self._ambil()
            v = self._faktorial(v)
        return v

    def _primer(self):
        t = self._ambil()
        if t is None:
            raise KesalahanHitung("Ekspresi tidak valid.")
        if t[0].isdigit():
            return float(t) if "." in t else int(t)
        if t == "(":
            v = self._ekspresi()
            self._harap(")")
            return v
        if t in self.KONSTANTA:
            return self.KONSTANTA[t]
        if t in self.FUNGSI:
            self._harap("(")
            v = self._ekspresi()
            self._harap(")")
            return self._panggil(t, v)
        raise KesalahanHitung("Ekspresi tidak valid.")

    # -- operasi --
    @staticmethod
    def _hitung_pangkat(a, b):
        if isinstance(a, int) and isinstance(b, int) and 0 <= b <= 1000:
            return a ** b
        r = float(a) ** float(b)
        if isinstance(r, complex):
            raise KesalahanHitung("Hasil pangkat bukan bilangan real.")
        return r

    @staticmethod
    def _faktorial(x):
        if x < 0 or x != int(x):
            raise KesalahanHitung("Faktorial hanya untuk bilangan bulat ≥ 0.")
        if x > 170:
            raise KesalahanHitung("Angka terlalu besar untuk faktorial.")
        return math.factorial(int(x))

    def _panggil(self, nama, x):
        if nama in ("sin", "cos", "tan"):
            rad = math.radians(x) if self.derajat else x
            if nama == "tan":
                if abs(math.cos(rad)) < 1e-12:
                    raise KesalahanHitung("Tangen tidak terdefinisi.")
                r = math.tan(rad)
            else:
                r = getattr(math, nama)(rad)
            return 0.0 if abs(r) < 1e-12 else r
        if nama in ("asin", "acos"):
            if not -1 <= x <= 1:
                raise KesalahanHitung("Masukan harus di antara -1 dan 1.")
            r = getattr(math, nama)(x)
            return math.degrees(r) if self.derajat else r
        if nama == "atan":
            r = math.atan(x)
            return math.degrees(r) if self.derajat else r
        if nama in ("lg", "ln"):
            if x <= 0:
                raise KesalahanHitung("Logaritma hanya untuk bilangan positif.")
            return math.log10(x) if nama == "lg" else math.log(x)
        if nama == "sqrt":
            if x < 0:
                raise KesalahanHitung("Akar bilangan negatif tidak didukung.")
            return math.sqrt(x)
        raise KesalahanHitung("Ekspresi tidak valid.")


def _tokenisasi(ekspresi: str):
    s = (ekspresi.replace("×", "*").replace("÷", "/").replace(",", ".")
         .replace("sin⁻¹", "asin").replace("cos⁻¹", "acos").replace("tan⁻¹", "atan")
         .replace("√", "sqrt").replace("π", "pi").replace(" ", ""))
    tokens = re.findall(r"\d+(?:\.\d+)?|[a-z]+|[-+*/^()!]", s)
    if "".join(tokens) != s:
        raise KesalahanHitung("Ekspresi tidak valid.")
    return tokens


def hitung(ekspresi: str, derajat: bool = True):
    """Hitung ekspresi matematika ilmiah secara aman."""
    hasil = Parser(_tokenisasi(ekspresi), derajat).parse()
    if isinstance(hasil, float) and not math.isfinite(hasil):
        raise KesalahanHitung("Hasil tidak terdefinisi.")
    return hasil


def format_angka(x) -> str:
    """Format hasil: hilangkan .0, batasi digit, notasi ilmiah untuk angka ekstrem."""
    if isinstance(x, float) and x.is_integer() and abs(x) < 1e15:
        x = int(x)
    if isinstance(x, int):
        if abs(x) < 10 ** 15:
            return str(x)
        x = float(x)
    teks = f"{x:.10g}"
    if "e" in teks:
        mantisa, eksp = teks.split("e")
        return mantisa.replace(".", ",") + f"×10^({int(eksp)})"
    return teks.replace(".", ",")


# ---------- Aplikasi GUI ----------
class KalkulatorApp(tk.Tk):
    BG = "#1e1f26"
    DISPLAY_BG = "#14151a"
    FG = "#f1f2f6"

    # jenis: (warna normal, warna hover, warna teks)
    WARNA = {
        "num":  ("#2d2f3a", "#3a3d4c", "#f1f2f6"),
        "sci":  ("#262833", "#34374a", "#c9ccd8"),
        "op":   ("#ff9f43", "#ffb56b", "#f1f2f6"),
        "func": ("#4a4e63", "#5d6280", "#f1f2f6"),
        "eq":   ("#1dd1a1", "#48e3bb", "#0b1d17"),
    }

    OPERATORS = ("+", "-", "×", "÷", "^")
    FUNC_TOKENS = ("sin⁻¹(", "cos⁻¹(", "tan⁻¹(", "sin(", "cos(", "tan(",
                   "lg(", "ln(", "√(")

    def __init__(self):
        super().__init__()
        self.title("Kalkulator Ilmiah")
        self.configure(bg=self.BG)
        self.resizable(False, False)

        self.ekspresi = ""
        self.sudah_hasil = False
        self.derajat = True       # True = deg, False = rad
        self.mode_2nd = False

        self._warna = {}          # tombol -> [normal, hover]
        self._dual = {}           # tombol -> (teks1, cmd1, teks2, cmd2)

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
            font=("Segoe UI", 12), width=1,
        )
        self.lbl_riwayat.pack(fill="x")

        self.lbl_layar = tk.Label(
            frame, text="0", anchor="e", bg=self.DISPLAY_BG, fg=self.FG,
            font=("Segoe UI", 30, "bold"), width=1,
        )
        self.lbl_layar.pack(fill="x")

    def _buat_tombol(self):
        grid = tk.Frame(self, bg=self.BG)
        grid.grid(row=1, column=0, padx=12, pady=(0, 12))

        ang, op, fn = self.tekan_angka, self.tekan_operator, self.sisip_fungsi
        k = self.tekan_konstanta

        # (baris, kolom, jenis, teks, perintah, teks_2nd, perintah_2nd, [span])
        layout = [
            (0, 0, "func", "2nd", self.toggle_2nd),
            (0, 1, "func", "deg", self.toggle_sudut),
            (0, 2, "sci", "sin⁻¹", lambda: fn("sin⁻¹("), "sin", lambda: fn("sin(")),
            (0, 3, "sci", "cos⁻¹", lambda: fn("cos⁻¹("), "cos", lambda: fn("cos(")),
            (0, 4, "sci", "tan⁻¹", lambda: fn("tan⁻¹("), "tan", lambda: fn("tan(")),

            (1, 0, "sci", "xʸ", lambda: self.tambah_akhiran("^")),
            (1, 1, "sci", "lg", lambda: fn("lg("), "10ˣ", lambda: fn("10^(")),
            (1, 2, "sci", "ln", lambda: fn("ln("), "eˣ", lambda: fn("e^(")),
            (1, 3, "sci", "(", self.kurung_buka),
            (1, 4, "sci", ")", self.kurung_tutup),

            (2, 0, "sci", "√x", lambda: fn("√("), "x²", lambda: self.tambah_akhiran("^2")),
            (2, 1, "op_text", "AC", self.clear),
            (2, 2, "op_text", "⌫", self.backspace),
            (2, 3, "op_text", "%", self.persen),
            (2, 4, "op_text", "÷", lambda: op("÷")),

            (3, 0, "sci", "x!", lambda: self.tambah_akhiran("!")),
            (3, 1, "num", "7", lambda: ang("7")),
            (3, 2, "num", "8", lambda: ang("8")),
            (3, 3, "num", "9", lambda: ang("9")),
            (3, 4, "op_text", "×", lambda: op("×")),

            (4, 0, "sci", "1/x", self.kebalikan),
            (4, 1, "num", "4", lambda: ang("4")),
            (4, 2, "num", "5", lambda: ang("5")),
            (4, 3, "num", "6", lambda: ang("6")),
            (4, 4, "op_text", "−", lambda: op("-")),

            (5, 0, "sci", "π", lambda: k("π"), "e", lambda: k("e")),
            (5, 1, "num", "1", lambda: ang("1")),
            (5, 2, "num", "2", lambda: ang("2")),
            (5, 3, "num", "3", lambda: ang("3")),
            (5, 4, "op_text", "+", lambda: op("+")),

            (6, 0, "num", "±", self.ganti_tanda),
            (6, 1, "num", "0", lambda: ang("0")),
            (6, 2, "num", ",", self.tekan_desimal),
            (6, 3, "eq", "=", self.sama_dengan, None, None, 2),
        ]

        for baris, kolom, jenis, t1, c1, *sisa in layout:
            t2, c2, span = (sisa + [None, None, 1][len(sisa):])[:3] if sisa else (None, None, 1)
            # "op_text": tombol gelap dengan teks oranye (seperti di foto)
            if jenis == "op_text":
                normal, hover, fg = "#2d2f3a", "#3a3d4c", self.WARNA["op"][0]
            else:
                normal, hover, fg = self.WARNA[jenis]

            btn = tk.Button(
                grid, text=t1, command=c1, width=5, height=2,
                bg=normal, fg=fg, activebackground=hover, activeforeground=fg,
                font=("Segoe UI", 14, "bold"), bd=0, relief="flat", cursor="hand2",
            )
            btn.grid(row=baris, column=kolom, columnspan=span, padx=4, pady=4, sticky="nsew")
            self._warna[btn] = [normal, hover]
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self._warna[b][1]))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self._warna[b][0]))

            if t2 is not None:
                self._dual[btn] = (t1, c1, t2, c2)
            if t1 == "2nd":
                self.btn_2nd = btn
            elif t1 == "deg":
                self.btn_sudut = btn

    def _bind_keyboard(self):
        self.bind("<Key>", self._on_key)
        self.bind("<Return>", lambda e: self.sama_dengan())
        self.bind("<KP_Enter>", lambda e: self.sama_dengan())
        self.bind("<BackSpace>", lambda e: self.backspace())
        self.bind("<Escape>", lambda e: self.clear())
        self.bind("<Delete>", lambda e: self.clear())

    def _on_key(self, event):
        ch = event.char
        if not ch:
            return
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
        elif ch == "^":
            self.tambah_akhiran("^")
        elif ch == "!":
            self.tambah_akhiran("!")
        elif ch == "(":
            self.kurung_buka()
        elif ch == ")":
            self.kurung_tutup()
        elif ch in ("p", "P"):
            self.tekan_konstanta("π")
        elif ch == "%":
            self.persen()
        elif ch == "=":
            self.sama_dengan()

    # ----- Toggle mode -----
    def toggle_2nd(self):
        self.mode_2nd = not self.mode_2nd
        for btn, (t1, c1, t2, c2) in self._dual.items():
            btn.config(text=t2 if self.mode_2nd else t1,
                       command=c2 if self.mode_2nd else c1)
        normal, hover, _ = self.WARNA["op" if self.mode_2nd else "func"]
        self._warna[self.btn_2nd] = [normal, hover]
        self.btn_2nd.config(bg=normal)

    def toggle_sudut(self):
        self.derajat = not self.derajat
        self.btn_sudut.config(text="deg" if self.derajat else "rad")

    # ----- Logika -----
    def _angka_terakhir(self) -> str:
        i = len(self.ekspresi)
        while i > 0 and (self.ekspresi[i - 1].isdigit() or self.ekspresi[i - 1] == ","):
            i -= 1
        return self.ekspresi[i:]

    def _bersihkan_koma(self):
        if self.ekspresi.endswith(","):
            self.ekspresi = self.ekspresi[:-1]

    def tekan_angka(self, d):
        if self.sudah_hasil:
            self.ekspresi = ""
            self.sudah_hasil = False
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
        if not self.ekspresi or self.ekspresi[-1] == "(":
            if op == "-":            # izinkan angka negatif di awal / setelah kurung
                self.ekspresi += "-"
                self._update_display()
            return
        if self.ekspresi[-1] == "-" and (len(self.ekspresi) == 1 or self.ekspresi[-2] == "("):
            return
        if self.ekspresi[-1] in self.OPERATORS:
            self.ekspresi = self.ekspresi[:-1] + op
        elif self.ekspresi[-1] == ",":
            self.ekspresi = self.ekspresi[:-1] + op
        else:
            self.ekspresi += op
        self._update_display()

    def tambah_akhiran(self, teks):
        """Tambah ^, !, atau ^2 jika ekspresi berakhir pada operand."""
        self._bersihkan_koma()
        if not self.ekspresi or self.ekspresi[-1] not in "0123456789)πe!":
            return
        self.ekspresi += teks
        self.sudah_hasil = False
        self._update_display()

    def sisip_fungsi(self, token):
        """Sisipkan fungsi seperti sin( atau √(. Jika ada hasil, hasil jadi argumen."""
        self._bersihkan_koma()
        if self.sudah_hasil:
            self.ekspresi = token + self.ekspresi
            self.sudah_hasil = False
        else:
            self.ekspresi += token
        self._update_display()

    def tekan_konstanta(self, simbol):
        if self.sudah_hasil:
            self.ekspresi = ""
            self.sudah_hasil = False
        self._bersihkan_koma()
        self.ekspresi += simbol
        self._update_display()

    def kurung_buka(self):
        if self.sudah_hasil:
            self.ekspresi = ""
            self.sudah_hasil = False
        self._bersihkan_koma()
        self.ekspresi += "("
        self._update_display()

    def kurung_tutup(self):
        if self.sudah_hasil:
            return
        self._bersihkan_koma()
        if self.ekspresi.count("(") <= self.ekspresi.count(")"):
            return
        if not self.ekspresi or self.ekspresi[-1] in self.OPERATORS + ("(",):
            return
        self.ekspresi += ")"
        self._update_display()

    def kebalikan(self):
        """1/x untuk angka terakhir."""
        self._bersihkan_koma()
        angka = self._angka_terakhir()
        if not angka:
            return
        awal = self.ekspresi[: len(self.ekspresi) - len(angka)]
        self.ekspresi = awal + "(1÷" + angka + ")"
        self.sudah_hasil = False
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
        unary = awal.endswith("-") and (
            len(awal) == 1 or awal[-2] in self.OPERATORS + ("(",)
        )
        if unary:
            awal = awal[:-1]
        else:
            awal += "-"
        self.ekspresi = awal + angka
        self._update_display()

    def backspace(self):
        if self.sudah_hasil:
            self.clear()
            return
        for tok in self.FUNC_TOKENS:          # hapus nama fungsi sekaligus
            if self.ekspresi.endswith(tok):
                self.ekspresi = self.ekspresi[: -len(tok)]
                break
        else:
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
        ekspr += ")" * (ekspr.count("(") - ekspr.count(")"))   # tutup kurung otomatis
        try:
            hasil = hitung(ekspr, self.derajat)
            self.lbl_riwayat.config(text=ekspr + " =")
            self.ekspresi = format_angka(hasil)
            self.sudah_hasil = True
        except ZeroDivisionError:
            messagebox.showerror("Kesalahan", "Tidak bisa membagi dengan nol.")
            self.lbl_riwayat.config(text="")
            self.ekspresi = ""
            self.sudah_hasil = False
        except KesalahanHitung as e:
            messagebox.showerror("Kesalahan", str(e))
            self.ekspresi = ""
        except OverflowError:
            messagebox.showerror("Kesalahan", "Hasil terlalu besar.")
            self.ekspresi = ""
        except (ValueError, SyntaxError):
            messagebox.showerror("Kesalahan", "Ekspresi tidak valid.")
            self.ekspresi = ""
        self._update_display()

    def _update_display(self):
        teks = self.ekspresi or "0"
        tampil = teks if len(teks) <= 40 else "…" + teks[-39:]
        ukuran = 30 if len(teks) <= 10 else 24 if len(teks) <= 14 else 18 if len(teks) <= 20 else 14
        self.lbl_layar.config(text=tampil, font=("Segoe UI", ukuran, "bold"))


if __name__ == "__main__":
    KalkulatorApp().mainloop()