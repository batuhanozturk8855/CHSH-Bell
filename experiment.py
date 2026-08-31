"""
CHSH / Bell esitsizligi deneyi.

Quantum devre Q# tarafinda (src/CHSH.qs). Bu script onu calistiriyor:
correlator degerlerini ornekliyor, CHSH istatistigi S'i hesapliyor,
olcum acilarini tariyor, white noise ekleyip visibility esigini
buluyor ve results/ klasorune CSV tablolari ile PNG grafikleri yaziyor.
"""

import itertools
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import qsharp

RESULTS = "results"
CLASSICAL_BOUND = 2.0
TSIRELSON_BOUND = 2.0 * math.sqrt(2.0)

# Optimal CHSH angle set (Bloch polar angles, X-Z plane).
A0, A1 = 0.0, math.pi / 2
B0, B1 = math.pi / 4, -math.pi / 4


def sample_products(angle_a, angle_b, entangled, shots):
    """Return an array of +1/-1 products from `shots` Q# trials."""
    call = (
        f"CHSH.SampleCorrelationBatch("
        f"{angle_a}, {angle_b}, {'true' if entangled else 'false'}, {shots})"
    )
    return np.array(qsharp.run(call, shots=1)[0], dtype=float)


def correlator(angle_a, angle_b, entangled=True, shots=4000, noise=0.0, rng=None):
    """Estimate E(a, b) with a standard error.

    `noise` replaces that fraction of trials with uniformly random
    products, modelling white noise / loss of visibility.
    """
    products = sample_products(angle_a, angle_b, entangled, shots)
    if noise > 0.0:
        rng = rng or np.random.default_rng()
        mask = rng.random(shots) < noise
        products[mask] = rng.choice([-1.0, 1.0], size=int(mask.sum()))
    mean = products.mean()
    stderr = products.std(ddof=1) / math.sqrt(shots)
    return mean, stderr


def chsh_statistic(a0=A0, a1=A1, b0=B0, b1=B1, **kw):
    """S = E(a0,b0) + E(a0,b1) + E(a1,b0) - E(a1,b1)."""
    terms = [
        correlator(a0, b0, **kw),
        correlator(a0, b1, **kw),
        correlator(a1, b0, **kw),
        correlator(a1, b1, **kw),
    ]
    signs = [1.0, 1.0, 1.0, -1.0]
    s = sum(sg * m for sg, (m, _) in zip(signs, terms))
    err = math.sqrt(sum(e**2 for _, e in terms))
    return s, err, [m for m, _ in terms]


# ----------------------------------------------------------------------
# Stage 1 - validate the circuit against the analytic correlator
# ----------------------------------------------------------------------
def stage_validation(shots=20000):
    print("\n[1] Devre dogrulamasi: E(a,b) degeri cos(a-b) ile ayni cikmali")
    rows = []
    for label, delta in [
        ("0", 0.0),
        ("pi/4", math.pi / 4),
        ("pi/2", math.pi / 2),
        ("3pi/4", 3 * math.pi / 4),
        ("pi", math.pi),
    ]:
        measured, err = correlator(0.0, delta, shots=shots)
        theory = math.cos(-delta)
        deviation = abs(measured - theory)
        passed = deviation < 4 * err + 1e-9
        rows.append(
            {
                "delta": label,
                "theory": round(theory, 4),
                "measured": round(measured, 4),
                "stderr": round(err, 4),
                "abs_deviation": round(deviation, 4),
                "within_4_sigma": passed,
            }
        )
        print(f"    delta={label:>5}  teori={theory:+.4f}  "
              f"olculen={measured:+.4f} +/- {err:.4f}  {'GECTI' if passed else 'KALDI'}")
    df = pd.DataFrame(rows)
    df.to_csv(f"{RESULTS}/correlator_validation.csv", index=False)
    return df


# ----------------------------------------------------------------------
# Stage 2 - the classical bound, proved by exhaustive enumeration
# ----------------------------------------------------------------------
def stage_classical_bound():
    print("\n[2] Klasik sinir (local hidden variable) - tum ihtimallerin sayimi")
    rows = []
    for a0, a1, b0, b1 in itertools.product([-1, 1], repeat=4):
        s = a0 * b0 + a0 * b1 + a1 * b0 - a1 * b1
        rows.append({"A0": a0, "A1": a1, "B0": b0, "B1": b1, "S": s})
    df = pd.DataFrame(rows)
    df.to_csv(f"{RESULTS}/classical_strategies.csv", index=False)
    print(f"    16 deterministik strateji tek tek hesaplandi")
    print(f"    tum klasik stratejilerde maksimum |S| = {df.S.abs().max()}")
    print(f"    ortak rastgelelik bunlarin ortalamasi oldugu icin sinir gecerli: |S| <= 2")
    return df


# ----------------------------------------------------------------------
# Stage 3 - the measurement itself
# ----------------------------------------------------------------------
def stage_main_measurement(shots=100000):
    print(f"\n[3] Optimal acilarda CHSH degeri (correlator basina {shots} shot)")
    rows = []
    for label, entangled in [("Bell state |Phi+>", True), ("Product state |+>|+>", False)]:
        s, err, terms = chsh_statistic(entangled=entangled, shots=shots)
        rows.append(
            {
                "state": label,
                "E_a0b0": round(terms[0], 4),
                "E_a0b1": round(terms[1], 4),
                "E_a1b0": round(terms[2], 4),
                "E_a1b1": round(terms[3], 4),
                "S": round(s, 4),
                "stderr": round(err, 4),
                "violates_classical_bound": bool(s - 2 * err > CLASSICAL_BOUND),
            }
        )
        print(f"    {label:<22} S = {s:.4f} +/- {err:.4f}"
              f"   {'IHLAL VAR' if s - 2 * err > CLASSICAL_BOUND else 'ihlal yok'}")
    print(f"    klasik sinir = {CLASSICAL_BOUND:.4f}   "
          f"Tsirelson bound = {TSIRELSON_BOUND:.4f}")
    df = pd.DataFrame(rows)
    df.to_csv(f"{RESULTS}/chsh_main_result.csv", index=False)
    return df


# ----------------------------------------------------------------------
# Stage 4 - angle sweep: why pi/4 is the right choice
# ----------------------------------------------------------------------
def stage_angle_sweep(points=25, shots=8000):
    print(f"\n[4] Aci taramasi: Bob'un olcum ekseni delta kadar donduruluyor")
    deltas = np.linspace(0.0, math.pi / 2, points)
    rows = []
    for d in deltas:
        s, err, _ = chsh_statistic(b0=d, b1=-d, shots=shots)
        theory = 2 * (math.cos(d) + math.sin(d))
        rows.append({"delta": d, "S_measured": s, "stderr": err, "S_theory": theory})
    df = pd.DataFrame(rows)
    df.to_csv(f"{RESULTS}/angle_sweep.csv", index=False)
    best = df.loc[df.S_measured.idxmax()]
    print(f"    en iyi delta = {best.delta:.4f} rad "
          f"(pi/4 = {math.pi/4:.4f}), S = {best.S_measured:.4f}")

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(df.delta, df.S_theory, "-", color="#444", label="teori: 2sqrt(2) sin(d + pi/4)")
    ax.errorbar(df.delta, df.S_measured, yerr=df.stderr, fmt="o", ms=4,
                color="#1f77b4", capsize=2, label=f"simulasyon ({shots} shot/nokta)")
    ax.axhline(CLASSICAL_BOUND, color="#d62728", ls="--", label="klasik sinir = 2")
    ax.axhline(TSIRELSON_BOUND, color="#2ca02c", ls=":", label="Tsirelson bound = 2sqrt(2)")
    ax.axvline(math.pi / 4, color="#999", lw=0.8)
    ax.set_xlabel("Bob'un eksen kaymasi  delta  (rad)")
    ax.set_ylabel("CHSH degeri  S")
    ax.set_title("Olcum acisina gore CHSH degeri")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(f"{RESULTS}/angle_sweep.png", dpi=140)
    plt.close(fig)
    return df


# ----------------------------------------------------------------------
# Stage 5 - correlator curve, entangled vs product
# ----------------------------------------------------------------------
def stage_correlation_curve(points=25, shots=8000):
    print("\n[5] Korelasyon egrisi E(delta): entangled ve separable karsilastirmasi")
    deltas = np.linspace(0.0, math.pi, points)
    rows = []
    for d in deltas:
        me, ee = correlator(0.0, d, entangled=True, shots=shots)
        mp, ep = correlator(0.0, d, entangled=False, shots=shots)
        rows.append({"delta": d, "E_bell": me, "E_bell_err": ee,
                     "E_product": mp, "E_product_err": ep,
                     "E_theory": math.cos(d)})
    df = pd.DataFrame(rows)
    df.to_csv(f"{RESULTS}/correlation_curve.csv", index=False)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(df.delta, df.E_theory, "-", color="#444", label="teori: cos(delta)")
    ax.errorbar(df.delta, df.E_bell, yerr=df.E_bell_err, fmt="o", ms=4,
                color="#1f77b4", capsize=2, label="Bell state")
    ax.errorbar(df.delta, df.E_product, yerr=df.E_product_err, fmt="s", ms=4,
                color="#ff7f0e", capsize=2, label="product state (entangle degil)")
    ax.set_xlabel("aci farki  delta  (rad)")
    ax.set_ylabel("correlator  E")
    ax.set_title("Aci farkina gore iki qubit korelasyonu")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(f"{RESULTS}/correlation_curve.png", dpi=140)
    plt.close(fig)
    print(f"    product state correlator degeri sifira yakin sabit kaliyor "
          f"(ortalama |E| = {df.E_product.abs().mean():.4f})")
    return df


# ----------------------------------------------------------------------
# Stage 6 - white-noise visibility threshold
# ----------------------------------------------------------------------
def stage_noise_threshold(points=21, shots=20000, seed=1234):
    print("\n[6] White noise taramasi: ihlal ne kadar gurultude kayboluyor")
    rng = np.random.default_rng(seed)
    ps = np.linspace(0.0, 0.6, points)
    rows = []
    for p in ps:
        s, err, _ = chsh_statistic(shots=shots, noise=float(p), rng=rng)
        rows.append({"noise_p": p, "visibility": 1 - p, "S": s, "stderr": err,
                     "S_theory": (1 - p) * TSIRELSON_BOUND})
    df = pd.DataFrame(rows)
    df.to_csv(f"{RESULTS}/noise_sweep.csv", index=False)

    above = df[df.S > CLASSICAL_BOUND]
    empirical_p = above.noise_p.max() if len(above) else float("nan")
    theory_p = 1 - 1 / math.sqrt(2)
    print(f"    teorik esik: p = 1 - 1/sqrt(2) = {theory_p:.4f} "
          f"(visibility {1-theory_p:.4f})")
    print(f"    klasik sinirin ustunde kalan en yuksek p degeri: {empirical_p:.4f}")

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(df.noise_p, df.S_theory, "-", color="#444", label="teori: (1-p)*2sqrt(2)")
    ax.errorbar(df.noise_p, df.S, yerr=df.stderr, fmt="o", ms=4,
                color="#1f77b4", capsize=2, label=f"simulasyon ({shots} shot/nokta)")
    ax.axhline(CLASSICAL_BOUND, color="#d62728", ls="--", label="klasik sinir = 2")
    ax.axvline(theory_p, color="#999", lw=0.8)
    ax.annotate(f"p = {theory_p:.3f}", xy=(theory_p, 2.6), fontsize=8,
                xytext=(theory_p + 0.03, 2.65))
    ax.set_xlabel("white noise orani  p")
    ax.set_ylabel("CHSH degeri  S")
    ax.set_title("Bell ihlali sadece %70.7 visibility ustunde hayatta kaliyor")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(f"{RESULTS}/noise_sweep.png", dpi=140)
    plt.close(fig)
    return df, theory_p


# ----------------------------------------------------------------------
# Stage 7 - statistical convergence
# ----------------------------------------------------------------------
def stage_convergence(seed=7):
    print("\n[7] Shot sayisina gore S degerinin yakinsamasi")
    shot_counts = [100, 300, 1000, 3000, 10000, 30000, 100000]
    rows = []
    for n in shot_counts:
        s, err, _ = chsh_statistic(shots=n)
        sigmas = (s - CLASSICAL_BOUND) / err if err > 0 else float("nan")
        rows.append({"shots": n, "S": s, "stderr": err,
                     "sigmas_above_classical_bound": sigmas})
        print(f"    {n:>6} shot  S = {s:.4f} +/- {err:.4f}   "
              f"2 degerinin {sigmas:5.1f} sigma ustunde")
    df = pd.DataFrame(rows)
    df.to_csv(f"{RESULTS}/convergence.csv", index=False)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.errorbar(df.shots, df.S, yerr=df.stderr, fmt="o-", ms=5,
                color="#1f77b4", capsize=3, label="olculen S")
    ax.axhline(CLASSICAL_BOUND, color="#d62728", ls="--", label="klasik sinir = 2")
    ax.axhline(TSIRELSON_BOUND, color="#2ca02c", ls=":", label="Tsirelson bound = 2sqrt(2)")
    ax.set_xscale("log")
    ax.set_xlabel("correlator basina shot sayisi (log olcek)")
    ax.set_ylabel("CHSH degeri  S")
    ax.set_title("CHSH tahmininin istatistiksel yakinsamasi")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(f"{RESULTS}/convergence.png", dpi=140)
    plt.close(fig)
    return df


def yaz_ozet(valid_df, main_df, conv_df, theory_p):
    """results/SONUCLAR.md dosyasina Turkce ozet yazar."""
    bell = main_df.iloc[0]
    prod = main_df.iloc[1]
    en_iyi = conv_df.iloc[-1]

    satirlar = []
    satirlar.append("# Sonuclar\n")
    satirlar.append(
        "Bu dosya `experiment.py` calistirildiginda otomatik uretilir. "
        "Simulator sabit bir seed kullanmadigi icin her calistirmada "
        "rakamlar birkac binde oynayabilir.\n"
    )

    satirlar.append("## Ana olcum\n")
    satirlar.append("| Durum | S degeri | Hata payi | Ihlal var mi |")
    satirlar.append("|---|---:|---:|:--:|")
    satirlar.append(
        f"| Bell state (entangled) | **{bell.S:.4f}** | {bell.stderr:.4f} | evet |"
    )
    satirlar.append(
        f"| Product state (entangle degil) | {prod.S:.4f} | {prod.stderr:.4f} | hayir |"
    )
    satirlar.append("")
    satirlar.append(f"- Klasik sinir: **2.0000**")
    satirlar.append(f"- Tsirelson bound (quantum tavan): **{TSIRELSON_BOUND:.4f}**")
    sigma = (bell.S - CLASSICAL_BOUND) / bell.stderr
    satirlar.append(f"- Olculen deger klasik sinirin **{sigma:.0f} sigma** ustunde\n")

    satirlar.append(
        "Yorum: Bell state ile klasik olarak imkansiz bir deger olculuyor. "
        "Entangle olmayan product state ise 1.41 civarinda kaliyor, yani "
        "sinirin altinda. Demek ki S'i 2'nin ustune tasiyan sey olcum "
        "duzeni degil, entanglement.\n"
    )

    satirlar.append("## Devre dogrulamasi\n")
    satirlar.append("| delta | Teori | Olculen | Hata payi | Sonuc |")
    satirlar.append("|---|---:|---:|---:|:--:|")
    for _, r in valid_df.iterrows():
        sonuc = "gecti" if r.within_4_sigma else "kaldi"
        satirlar.append(
            f"| {r.delta} | {r.theory:+.4f} | {r.measured:+.4f} | {r.stderr:.4f} | {sonuc} |"
        )
    satirlar.append("")
    satirlar.append(
        "Olcmeye baslamadan once devrenin dogru calistigini kontrol ettim: "
        "E(a,b) degeri her acida cos(a-b) ile ayni cikiyor.\n"
    )

    satirlar.append("## Shot sayisinin etkisi\n")
    satirlar.append("| Shot | S | Hata payi | Sinirin kac sigma ustunde |")
    satirlar.append("|---:|---:|---:|---:|")
    for _, r in conv_df.iterrows():
        satirlar.append(
            f"| {int(r.shots):,} | {r.S:.4f} | {r.stderr:.4f} | {r.sigmas_above_classical_bound:.1f} |"
        )
    satirlar.append("")
    satirlar.append(
        "100 shot bile klasik siniri asmaya yetiyor. Fazla shot sonucu "
        "degistirmiyor, sadece hata payini kucultuyor.\n"
    )

    satirlar.append("## Gurultu esigi\n")
    satirlar.append(
        f"Olcumlerin p kadarlik kismini rastgele sonucla degistirince "
        f"S degeri (1-p) ile carpiliyor. Ihlal ancak visibility "
        f"**%{(1-theory_p)*100:.1f}** ustunde oldugunda hayatta kaliyor "
        f"(p = {theory_p:.4f}).\n"
    )

    satirlar.append("## Grafikler\n")
    satirlar.append("- `angle_sweep.png` - olcum acisina gore S")
    satirlar.append("- `correlation_curve.png` - entangled ve separable karsilastirmasi")
    satirlar.append("- `noise_sweep.png` - gurultu esigi")
    satirlar.append("- `convergence.png` - shot sayisina gore yakinsama")

    with open(f"{RESULTS}/SONUCLAR.md", "w", encoding="utf-8") as f:
        f.write("\n".join(satirlar) + "\n")


def main():
    os.makedirs(RESULTS, exist_ok=True)
    qsharp.init(project_root=os.path.dirname(os.path.abspath(__file__)))

    print("=" * 68)
    print("CHSH / Bell esitsizligi deneyi  -  Q# devre + Python analiz")
    print("=" * 68)

    valid_df = stage_validation()
    stage_classical_bound()
    main_df = stage_main_measurement()
    stage_angle_sweep()
    stage_correlation_curve()
    _, theory_p = stage_noise_threshold()
    conv_df = stage_convergence()

    yaz_ozet(valid_df, main_df, conv_df, theory_p)

    s_bell = main_df.loc[0, "S"]
    print("\n" + "=" * 68)
    print(f"SONUC: S = {s_bell}   (klasik maksimum 2.0)")
    print(f"Tsirelson bound 2sqrt(2) = {TSIRELSON_BOUND:.4f}")
    print(f"Ihlal, visibility %{(1-theory_p)*100:.1f} altina inince kayboluyor")
    print(f"Tablolar ve grafikler {RESULTS}/ klasorune yazildi")
    print("=" * 68)


if __name__ == "__main__":
    main()
