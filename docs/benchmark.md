# Benchmark de inferência

Medido em 04/10/2026 | Windows 11 | processador: Intel Core i5-10500H (x86-64, 12 threads) + GTX 1650 | 100 quadros 1280×720 do vídeo da esteira (entrada do modelo: 640 px) | tempo total do `predict` (pré + inferência + pós).

| Modelo | Onde | Mediana (ms) | P95 (ms) | FPS (mediana) |
| --- | --- | --- | --- | --- |
| PyTorch (best.pt) | CPU | 53.5 | 79.4 | 18.7 |
| NCNN (best_ncnn_model) | CPU | 86.8 | 104.2 | 11.5 |
| PyTorch (best.pt) | GPU NVIDIA GeForce GTX 1650 | 26.3 | 36.0 | 38.1 |
