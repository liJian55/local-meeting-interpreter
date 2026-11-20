# Speech recognition benchmark

Measured on 2026-11-19 using faster-whisper 1.2.1, faster-whisper-small INT8,
four CPU threads, one beam, and the built-in VAD filter.

| Sample | Duration | Processing | Real-time factor | Process RSS |
| --- | ---: | ---: | ---: | ---: |
| English synthetic meeting speech | 12.96 s | 2.83 s | 0.218 | 412.1 MB |
| Chinese synthetic meeting speech | 15.56 s | 2.89 s | 0.185 | 414.4 MB |

The English test correctly recognized passenger name, flight number, arrival
time, and the release-plan sentence. The Chinese test was recognized correctly
with traditional characters. Both language detections had probabilities above
0.99. The offline `interpret` command then translated the three segments in
each sample.

These tests use Windows synthetic speech, not a real meeting. They establish
CPU throughput and pipeline correctness only. Real meeting latency must also
account for waiting for a phrase to finish before recognition begins.
