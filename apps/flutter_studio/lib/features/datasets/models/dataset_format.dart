class DatasetFormat {
  const DatasetFormat._();

  static const sftJsonl = 'sft_jsonl';
  static const alpacaJsonl = 'alpaca_jsonl';
  static const chatmlJsonl = 'chatml_jsonl';
  static const preferenceJsonl = 'preference_jsonl';

  static const values = [sftJsonl, alpacaJsonl, chatmlJsonl, preferenceJsonl];
}
