# Translation benchmark

Measured on 2026-11-19 with Python 3.13.5, CTranslate2 4.9.0,
CTranslate2 INT8, one beam, and four CPU inference threads.

Hardware: Intel Core i7-13620H, 31.7 GiB RAM, no discrete GPU.
Each sample was run five times; the first run was excluded from the median.

| Direction | Model load | Warm translation median | Disk | Process RSS |
| --- | ---: | ---: | ---: | ---: |
| Chinese to English | 173.3 ms | 28.9-50.5 ms | 80.3 MB | 136.8 MB |
| English to Chinese | 201.7 ms | 16.7-33.2 ms | 80.3 MB | 137.6 MB |

The RSS is the benchmark process after loading the corresponding model, not
the model's exclusive allocation. These measurements cover text translation
only, not speech recognition, audio capture, or speech synthesis.

The Chinese-English test sentences produced understandable English. The
English-Chinese output is adequate for an initial private prototype but should
be evaluated with real meeting recordings before choosing a final translator.

Both pytest cases pass. A separate test blocked socket connections before model
loading and translation completed successfully without network access.

## Measured environment fixes

- Use `pip --no-cache-dir` when installing dependencies in this Windows
  environment; reads from the existing pip cache stalled repeatedly.
- The CTranslate2 OPUS-MT converter emits the INT8 model but does not copy
  `source.spm` and `target.spm`. The setup scripts copy both tokenizers.
- The local Python HTTPS certificate configuration could not verify the model
  host, so model downloads use the system `curl` with certificate verification.
