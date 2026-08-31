# Sonuclar

Bu dosya `experiment.py` calistirildiginda otomatik uretilir. Simulator sabit bir seed kullanmadigi icin her calistirmada rakamlar birkac binde oynayabilir.

## Ana olcum

| Durum | S degeri | Hata payi | Ihlal var mi |
|---|---:|---:|:--:|
| Bell state (entangled) | **2.8315** | 0.0045 | evet |
| Product state (entangle degil) | 1.4190 | 0.0055 | hayir |

- Klasik sinir: **2.0000**
- Tsirelson bound (quantum tavan): **2.8284**
- Olculen deger klasik sinirin **185 sigma** ustunde

Yorum: Bell state ile klasik olarak imkansiz bir deger olculuyor. Entangle olmayan product state ise 1.41 civarinda kaliyor, yani sinirin altinda. Demek ki S'i 2'nin ustune tasiyan sey olcum duzeni degil, entanglement.

## Devre dogrulamasi

| delta | Teori | Olculen | Hata payi | Sonuc |
|---|---:|---:|---:|:--:|
| 0 | +1.0000 | +1.0000 | 0.0000 | gecti |
| pi/4 | +0.7071 | +0.7019 | 0.0050 | gecti |
| pi/2 | +0.0000 | -0.0002 | 0.0071 | gecti |
| 3pi/4 | -0.7071 | -0.7006 | 0.0050 | gecti |
| pi | -1.0000 | -1.0000 | 0.0000 | gecti |

Olcmeye baslamadan once devrenin dogru calistigini kontrol ettim: E(a,b) degeri her acida cos(a-b) ile ayni cikiyor.

## Shot sayisinin etkisi

| Shot | S | Hata payi | Sinirin kac sigma ustunde |
|---:|---:|---:|---:|
| 100 | 3.1200 | 0.1256 | 8.9 |
| 300 | 2.9333 | 0.0786 | 11.9 |
| 1,000 | 2.7320 | 0.0462 | 15.8 |
| 3,000 | 2.8073 | 0.0260 | 31.0 |
| 10,000 | 2.8400 | 0.0141 | 59.6 |
| 30,000 | 2.8365 | 0.0081 | 102.7 |
| 100,000 | 2.8333 | 0.0045 | 186.6 |

100 shot bile klasik siniri asmaya yetiyor. Fazla shot sonucu degistirmiyor, sadece hata payini kucultuyor.

## Gurultu esigi

Olcumlerin p kadarlik kismini rastgele sonucla degistirince S degeri (1-p) ile carpiliyor. Ihlal ancak visibility **%70.7** ustunde oldugunda hayatta kaliyor (p = 0.2929).

## Grafikler

- `angle_sweep.png` - olcum acisina gore S
- `correlation_curve.png` - entangled ve separable karsilastirmasi
- `noise_sweep.png` - gurultu esigi
- `convergence.png` - shot sayisina gore yakinsama
