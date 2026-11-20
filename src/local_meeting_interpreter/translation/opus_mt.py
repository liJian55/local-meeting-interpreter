from pathlib import Path

import ctranslate2
import sentencepiece as spm


class OpusTranslator:
    def __init__(
        self,
        model_dir: str | Path,
        *,
        device: str = "cpu",
        inter_threads: int = 1,
        intra_threads: int = 4,
    ) -> None:
        self.model_dir = Path(model_dir)
        self.translator = ctranslate2.Translator(
            str(self.model_dir),
            device=device,
            inter_threads=inter_threads,
            intra_threads=intra_threads,
        )
        self.source_tokenizer = spm.SentencePieceProcessor(
            model_file=str(self.model_dir / "source.spm")
        )
        self.target_tokenizer = spm.SentencePieceProcessor(
            model_file=str(self.model_dir / "target.spm")
        )

    def translate(self, text: str, *, beam_size: int = 1) -> str:
        if not text.strip():
            return ""
        source_tokens = self.source_tokenizer.encode(text.strip(), out_type=str)
        result = self.translator.translate_batch(
            [source_tokens],
            beam_size=beam_size,
            max_decoding_length=256,
        )[0]
        return self.target_tokenizer.decode(result.hypotheses[0])

