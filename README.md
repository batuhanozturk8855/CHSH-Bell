# Q# ile Bell Testi (CHSH)

Staj onboarding programı için yaptığım proje. İki qubit'i entangle edip farklı
açılardan ölçüyorum ve CHSH değeri `S`'i hesaplıyorum. Klasik bir sistemde
`S` en fazla 2 olabiliyor, entangle qubit'lerle teoride 2√2 ≈ 2.83'e çıkıyor.
Amacım bunu Q# ile kendim ölçmekti.

Devre Q#'ta (`src/CHSH.qs`), analiz ve grafikler Python'da (`experiment.py`).

## Çalıştırma

VS Code + Azure Quantum Development Kit extension ile local simulator'da
çalıştırdım.

```bash
python -m pip install -r requirements.txt
python experiment.py
```

Yaklaşık 1 dakika sürüyor. Tablolar, grafikler ve kısa bir özet
(`SONUCLAR.md`) `results/` klasörüne yazılıyor.

## Sonuçlar

Correlator başına 100.000 shot ile:

| Durum | S |
|---|---:|
| Bell state (entangled) | **2.83** ± 0.005 |
| Product state (entangle değil) | 1.42 ± 0.006 |

- Entangle qubit'lerle `S` klasik sınır olan 2'yi geçiyor.
- Entangle olmayan kontrol 2'nin altında kalıyor, yani farkı yaratan
  entanglement.

Ayrıca açı taraması, gürültü eşiği ve shot sayısına göre yakınsama
grafikleri de `results/` içinde.

## Takıldığım yerler

- Q# sadece Z ekseninde ölçüyor, başka açıda ölçmek için önce `Ry` ile
  döndürmek gerektiğini anlamam biraz sürdü.
- İlk denemede `S` formülündeki eksi işaretini yanlış terime koydum, `S = 0`
  çıktı.
- Entangle olmayan durumun 0 vermesini bekliyordum, 1.41 çıktı. Sonra
  sınırı aşan kısmın entanglement'tan geldiğini anladım.

## Neler öğrendim

- Q#'ta Bell state hazırlama ve farklı açılarda ölçüm
- Olasılıksal bir sonucu çok sayıda shot ve hata payıyla ölçmek
- Gürültü arttıkça quantum avantajının nasıl kaybolduğu

Sadece ideal simulator kullandım, gerçek donanımda denemedim.
