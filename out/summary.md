# Summary numbers

## Data
- Lichess games sampled: 39,536,010 over 165 months
- TWIC games with 20 plies and both ratings >= 2000: 2,498,827
- of which OTB classical 2600+: 36,196
- online / fast games excluded from the OTB series: 1,097,176 / 184,599

## Era change, collision entropy, 2022-25 vs 2014-17 (95% cluster bootstrap)
- twic classical 2600+ @4: -0.53 bits [-0.63, -0.43]; 3.83 -> 3.30 bits, 14.3 -> 9.9 effective lines
- twic classical 2600+ @8: -0.31 bits [-0.48, -0.13]
- twic classical 2600+ @12: +0.24 bits [+0.03, +0.46]
- twic classical 2600+ @16: +0.25 bits [-0.10, +0.54]
- twic classical 2400-2599 @4: -0.54 bits [-0.58, -0.50]; 4.64 -> 4.10 bits, 25.0 -> 17.2 effective lines
- twic classical 2400-2599 @8: -0.64 bits [-0.73, -0.55]
- twic classical 2400-2599 @12: -0.19 bits [-0.29, -0.08]
- twic classical 2400-2599 @16: +0.26 bits [+0.08, +0.41]
- twic classical 2200-2399 @4: -0.52 bits [-0.56, -0.49]; 5.09 -> 4.56 bits, 34.0 -> 23.7 effective lines
- twic classical 2200-2399 @8: -0.62 bits [-0.69, -0.55]
- twic classical 2200-2399 @12: -0.28 bits [-0.36, -0.20]
- twic classical 2200-2399 @16: +0.00 bits [-0.12, +0.11]
- twic classical 2000-2199 @4: -0.46 bits [-0.50, -0.42]; 5.31 -> 4.85 bits, 39.8 -> 28.9 effective lines
- twic classical 2000-2199 @8: -0.52 bits [-0.60, -0.43]
- twic classical 2000-2199 @12: -0.34 bits [-0.42, -0.26]
- twic classical 2000-2199 @16: -0.26 bits [-0.39, -0.14]
- lichess blitz 2400+ @4: -0.02 bits [-0.11, +0.09]; 5.95 -> 5.93 bits, 61.8 -> 61.2 effective lines
- lichess blitz 2400+ @8: +0.02 bits [-0.17, +0.27]
- lichess blitz 2400+ @12: +0.09 bits [-0.12, +0.52]
- lichess blitz 2400+ @16: -0.09 bits [-0.42, +0.64]
- lichess blitz 2100-2399 @4: +0.21 bits [+0.16, +0.25]; 6.12 -> 6.33 bits, 69.7 -> 80.6 effective lines
- lichess blitz 2100-2399 @8: +0.68 bits [+0.56, +0.79]
- lichess blitz 2100-2399 @12: +0.93 bits [+0.81, +1.07]
- lichess blitz 2100-2399 @16: +1.18 bits [+0.99, +1.38]
- lichess blitz 1800-2099 @4: +0.17 bits [+0.14, +0.21]; 6.19 -> 6.36 bits, 72.8 -> 82.1 effective lines
- lichess blitz 1800-2099 @8: +1.04 bits [+0.97, +1.11]
- lichess blitz 1800-2099 @12: +1.48 bits [+1.36, +1.61]
- lichess blitz 1800-2099 @16: +2.02 bits [+1.82, +2.24]
- lichess blitz 1500-1799 @4: -0.11 bits [-0.17, -0.06]; 6.10 -> 5.99 bits, 68.5 -> 63.4 effective lines
- lichess blitz 1500-1799 @8: +0.35 bits [+0.27, +0.42]
- lichess blitz 1500-1799 @12: +0.41 bits [+0.28, +0.54]
- lichess blitz 1500-1799 @16: +0.50 bits [+0.29, +0.74]
- lichess blitz 1200-1499 @4: -0.32 bits [-0.41, -0.22]; 5.79 -> 5.47 bits, 55.4 -> 44.4 effective lines
- lichess blitz 1200-1499 @8: -0.35 bits [-0.45, -0.24]
- lichess blitz 1200-1499 @12: -0.36 bits [-0.52, -0.19]
- lichess blitz 1200-1499 @16: -0.39 bits [-0.68, -0.11]
- lichess blitz <1200 @4: -0.77 bits [-0.90, -0.65]; 6.31 -> 5.54 bits, 79.6 -> 46.7 effective lines
- lichess blitz <1200 @8: -0.91 bits [-1.13, -0.74]
- lichess blitz <1200 @12: -1.29 bits [-1.52, -1.05]
- lichess blitz <1200 @16: -1.81 bits [-2.41, -1.25]
- lichess rapid 1800-2099 @4: -0.02 bits [-0.06, +0.02]; 5.64 -> 5.62 bits, 49.7 -> 49.1 effective lines
- lichess rapid 1800-2099 @8: +0.43 bits [+0.31, +0.55]
- lichess rapid 1800-2099 @12: +0.48 bits [+0.32, +0.64]
- lichess rapid 1800-2099 @16: +0.69 bits [+0.45, +0.96]
- lichess bullet 1800-2099 @4: -0.60 bits [-0.64, -0.56]; 8.03 -> 7.43 bits, 261.7 -> 172.4 effective lines
- lichess bullet 1800-2099 @8: -0.50 bits [-0.57, -0.41]
- lichess bullet 1800-2099 @12: -0.05 bits [-0.15, +0.14]
- lichess bullet 1800-2099 @16: +0.45 bits [+0.25, +0.91]

## Gap (Lichess blitz band change minus elite change)
- 2400+ @4: +0.51 bits [+0.38, +0.66]
- 2400+ @8: +0.34 bits [+0.10, +0.61]
- 2400+ @12: -0.14 bits [-0.39, +0.34]
- 2100-2399 @4: +0.74 bits [+0.62, +0.86]
- 2100-2399 @8: +0.99 bits [+0.79, +1.21]
- 2100-2399 @12: +0.70 bits [+0.45, +0.97]
- 1800-2099 @4: +0.70 bits [+0.60, +0.80]
- 1800-2099 @8: +1.35 bits [+1.17, +1.52]
- 1800-2099 @12: +1.25 bits [+0.99, +1.50]
- 1500-1799 @4: +0.42 bits [+0.28, +0.54]
- 1500-1799 @8: +0.66 bits [+0.47, +0.85]
- 1500-1799 @12: +0.18 bits [-0.09, +0.43]
- 1200-1499 @4: +0.21 bits [+0.06, +0.35]
- 1200-1499 @8: -0.03 bits [-0.24, +0.18]
- 1200-1499 @12: -0.60 bits [-0.85, -0.29]
- <1200 @4: -0.24 bits [-0.39, -0.11]
- <1200 @8: -0.60 bits [-0.86, -0.38]
- <1200 @12: -1.53 bits [-1.85, -1.19]

## Fixed recurring events (550 event names)
- 2600+ @2: -0.33 bits [-0.41, -0.26] (n 6,760 -> 4,844)
- 2600+ @4: -0.57 bits [-0.71, -0.44] (n 6,760 -> 4,844)
- 2600+ @8: -0.38 bits [-0.57, -0.21] (n 6,760 -> 4,844)
- 2600+ @12: +0.12 bits [-0.16, +0.40] (n 6,760 -> 4,844)
- 2600+ @16: +0.12 bits [-0.30, +0.60] (n 6,760 -> 4,844)
- 2200-2399 @2: -0.20 bits [-0.23, -0.17] (n 80,672 -> 76,933)
- 2200-2399 @4: -0.52 bits [-0.58, -0.47] (n 80,672 -> 76,933)
- 2200-2399 @8: -0.61 bits [-0.72, -0.51] (n 80,672 -> 76,933)
- 2200-2399 @12: -0.29 bits [-0.40, -0.17] (n 80,672 -> 76,933)
- 2200-2399 @16: -0.00 bits [-0.17, +0.16] (n 80,672 -> 76,933)

## Breakpoints, elite 2600+ (quarterly H2, HAC SE)
- @4 AlphaZero paper: jump +0.02 (p 0.864), trend -0.028 -> -0.068 bits/yr (p 0.132)
- @4 Leela wins TCEC: jump -0.28 (p 0.002), trend -0.007 -> -0.039 bits/yr (p 0.200)
- @4 Stockfish 12 NNUE: jump -0.32 (p 0.011), trend -0.029 -> -0.010 bits/yr (p 0.511)
- @8 AlphaZero paper: jump -0.09 (p 0.379), trend -0.031 -> -0.015 bits/yr (p 0.640)
- @8 Leela wins TCEC: jump -0.27 (p 0.000), trend -0.016 -> +0.014 bits/yr (p 0.251)
- @8 Stockfish 12 NNUE: jump -0.27 (p 0.005), trend -0.032 -> +0.044 bits/yr (p 0.002)
- @12 AlphaZero paper: jump -0.09 (p 0.627), trend -0.022 -> +0.073 bits/yr (p 0.022)
- @12 Leela wins TCEC: jump -0.41 (p 0.007), trend +0.021 -> +0.127 bits/yr (p 0.004)
- @12 Stockfish 12 NNUE: jump -0.36 (p 0.034), trend +0.005 -> +0.173 bits/yr (p 0.000)
- supF 2600+ @4: break at 2022.12, F 10.9, bootstrap p 0.017
- supF 1200-1499 minus elite @4: break at 2017.12, F 53.0, bootstrap p 0.003
- supF 1800-2099 minus elite @4: break at 2023.88, F 6.1, bootstrap p 0.203
- supF 2600+ @8: break at 2021.88, F 4.6, bootstrap p 0.060
- supF 1200-1499 minus elite @8: break at 2019.38, F 25.1, bootstrap p 0.003
- supF 1800-2099 minus elite @8: break at 2019.88, F 8.2, bootstrap p 0.043
- supF 2600+ @12: break at 2021.88, F 8.5, bootstrap p 0.027
- supF 1200-1499 minus elite @12: break at 2021.88, F 11.7, bootstrap p 0.027
- supF 1800-2099 minus elite @12: break at 2021.88, F 12.3, bootstrap p 0.050
- placebo scan 2600+ @4: largest |jump t| at 2022.12 (t -4.8)
- placebo scan 1800-2099 minus elite @4: largest |jump t| at 2016.38 (t -4.9)

## Shannon check (plug-in at N=200, yearly cells, mean 2022-25 minus mean 2014-17)
- twic 2600+ @2: 3.34 -> 2.94 (-0.39)
- twic 2600+ @4: 4.72 -> 4.24 (-0.48)
- twic 2600+ @6: 6.03 -> 5.67 (-0.35)
- twic 2200-2399 @2: 3.81 -> 3.50 (-0.31)
- twic 2200-2399 @4: 5.60 -> 5.20 (-0.40)
- twic 2200-2399 @6: 6.75 -> 6.47 (-0.27)
- lichess 1800-2099 @2: 4.24 -> 4.23 (-0.01)
- lichess 1800-2099 @4: 6.45 -> 6.54 (+0.10)
- lichess 1800-2099 @6: 7.27 -> 7.33 (+0.07)
- lichess 1200-1499 @2: 3.86 -> 3.83 (-0.03)
- lichess 1200-1499 @4: 6.48 -> 6.35 (-0.13)
- lichess 1200-1499 @6: 7.46 -> 7.38 (-0.08)

## Players (elite 2600+, White repertoires)
- @4 yearly mean, same player: 12.3% -> 14.2%; different players: 7.0% -> 10.2%
- @8 yearly mean, same player: 2.6% -> 2.4%; different players: 1.0% -> 1.2%
- panel (112 players) @2: self-repeat 23.1% -> 25.9% (+2.7 pts [+0.5, +4.9]), 60% rose
- panel (112 players) @4: self-repeat 11.9% -> 14.5% (+2.6 pts [+1.2, +4.0]), 63% rose
- panel (112 players) @6: self-repeat 4.2% -> 5.6% (+1.4 pts [+0.7, +2.2]), 61% rose
- panel (112 players) @8: self-repeat 2.2% -> 2.7% (+0.5 pts [+0.0, +1.0]), 61% rose
- panel (112 players) @12: self-repeat 0.6% -> 0.7% (+0.0 pts [-0.2, +0.2]), 44% rose
- panel between-player match @4: 7.3% -> 9.9%
- panel between-player match @8: 1.0% -> 1.3%

## Elite 4-ply line shares (% of OTB classical 2600+ games)
| p4            |   2014-17 |   2018-21 |   2022-25 |
|:--------------|----------:|----------:|----------:|
| e4 e5 Nf3 Nc6 |      17.5 |      20   |      24.2 |
| d4 Nf6 c4 e6  |      15   |      14.4 |      17.1 |
| e4 c5 Nf3 d6  |       6.4 |       7.1 |       6.8 |
| d4 Nf6 c4 g6  |       6.5 |       5.4 |       3.4 |
| d4 d5 c4 c6   |       5.4 |       3.3 |       3.1 |
| d4 d5 c4 e6   |       2.2 |       2.2 |       3.7 |
| e4 e5 Nf3 Nf6 |       1.6 |       3.4 |       3.6 |
| e4 e6 d4 d5   |       3.4 |       2.7 |       2.8 |
