# Faster-Whisper-XXL Help Documentation

## Usage
```bash
faster-whisper-xxl.exe [options] audio [audio ...]
```

## Positional Arguments
- `audio`: Audio file(s). You can enter a file wildcard, filelist (txt, m3u, m3u8, lst) or directory to do batch processing. Note: non-media files in list or directory are filtered out by extension.

## Options

### General Options
- `-h, --help`: Show this help message and exit
- `--version`: Show Faster-Whisper's version number

### Model Options
- `--model MODEL, -m MODEL`: Name of the Whisper model to use (default: medium)
- `--model_dir MODEL_DIR`: The path to save model files; uses `C:\Faster-Whisper-XXL\_models` by default (default: None)

### Device Options
- `--device DEVICE, -d DEVICE`: Device to use. Default is 'cuda' if CUDA device is detected, else is 'cpu'. If CUDA GPU is a second device then set 'cuda:1'. (default: cuda)
- `--compute_type {default,auto,int8,int8_float16,int8_float32,int8_bfloat16,int16,float16,float32,bfloat16}, -ct {default,auto,int8,int8_float16,int8_float32,int8_bfloat16,int16,float16,float32,bfloat16}`: Type of quantization to use (see https://opennmt.net/CTranslate2/quantization.html). (default: auto)
- `--threads THREADS`: Number of threads used for CPU inference; By default number of the real cores but no more that 4 (default: 0)

### Output Options
- `--output_dir OUTPUT_DIR, -o OUTPUT_DIR`: Directory to save the outputs. By default the same folder where the executable file is or where media file is if `--batch_recursive=True`. '.' - sets to the current folder. 'source' - sets to where media file is. (default: default)
- `--output_format [{json,lrc,txt,text,vtt,srt,tsv,all} ...], -f [{json,lrc,txt,text,vtt,srt,tsv,all} ...]`: Format(s) of the output file; specify multiple formats separated by spaces. Note: dont add audio after this arg. (default: ['srt'])
- `--verbose VERBOSE, -v VERBOSE`: Whether to print out debug messages (default: False)

### Language Options
- `--language {af,am,ar,as,az,ba,be,bg,bn,bo,br,bs,ca,cs,cy,da,de,el,en,es,et,eu,fa,fi,fo,fr,gl,gu,ha,haw,he,hi,hr,ht,hu,hy,id,is,it,ja,jw,ka,kk,km,kn,ko,la,lb,ln,lo,lt,lv,mg,mi,mk,ml,mn,mr,ms,mt,my,ne,nl,nn,no,oc,pa,pl,ps,pt,ro,ru,sa,sd,si,sk,sl,sn,so,sq,sr,su,sv,sw,ta,te,tg,th,tk,tl,tr,tt,uk,ur,uz,vi,yi,yo,yue,zh,...}, -l {...}`: Language spoken in the audio, specify None to perform language detection (default: None)
- `--language_detection_threshold LANGUAGE_DETECTION_THRESHOLD, -ldt LANGUAGE_DETECTION_THRESHOLD`: If the maximum probability of the language tokens is higher than this value, the language is detected. (default: 0.5)
- `--language_detection_segments LANGUAGE_DETECTION_SEGMENTS, -lds LANGUAGE_DETECTION_SEGMENTS`: Number of segments/chunks to consider for the language detection. (default: 1)

### Task Options
- `--task {transcribe,translate}`: Whether to perform X->X speech recognition ('transcribe') or X->English translation ('translate') (default: transcribe)

### Decoding Options
- `--temperature TEMPERATURE`: Temperature to use for sampling (default: 0)
- `--best_of BEST_OF, -bo BEST_OF`: Number of candidates when sampling with non-zero temperature (default: 5)
- `--beam_size BEAM_SIZE, -bs BEAM_SIZE`: Number of beams in beam search, only applicable when temperature is zero (default: 5)
- `--patience PATIENCE, -p PATIENCE`: Optional patience value to use in beam decoding, as in https://arxiv.org/abs/2204.05424, the default (1.0) is equivalent to conventional beam search (default: 2.0)
- `--length_penalty LENGTH_PENALTY`: Optional token length penalty coefficient (alpha) as in https://arxiv.org/abs/1609.08144, uses simple length normalization by default (default: 1.0)
- `--repetition_penalty REPETITION_PENALTY`: Penalty applied to the score of previously generated tokens (set > 1.0 to penalize). (default: 1.0)
- `--no_repeat_ngram_size NO_REPEAT_NGRAM_SIZE`: Prevent repetitions of ngrams with this size (set 0 to disable). (default: 0)
- `--suppress_blank SUPPRESS_BLANK`: Suppress blank outputs at the beginning of the sampling. (default: True)
- `--suppress_tokens SUPPRESS_TOKENS`: Comma-separated list of token ids to suppress during sampling; '-1' will suppress most special characters except common punctuations. `None` - will pass empty list. (default: -1)
- `--initial_prompt INITIAL_PROMPT, -prompt INITIAL_PROMPT`: Optional text to provide context as a prompt for the first window. Use 'None' to disable it. Note: 'auto' and 'default' are experimental ~universal prompt presets, if task=transcribe then they work only if --language is set. (default: auto)
- `--prefix PREFIX`: Optional text to provide as a prefix for the first window. A partial transcription for the current audio input. (default: None)
- `--condition_on_previous_text CONDITION_ON_PREVIOUS_TEXT, -condition CONDITION_ON_PREVIOUS_TEXT`: If True, provide the previous output of the model as a prompt for the next window; disabling may make the text inconsistent across windows, but the model becomes less prone to getting stuck in a failure loop. If disabled then you may want to disable --reprompt too. (default: True)
- `--prompt_reset_on_temperature PROMPT_RESET_ON_TEMPERATURE`: Resets prompt if temperature is above this value. Arg has effect only if condition_on_previous_text is True. (default: 0.5)
- `--without_timestamps WITHOUT_TIMESTAMPS`: Use <|notimestamps|> to sample text tokens only. For audios shorter than 30s. (default: None)
- `--max_initial_timestamp MAX_INITIAL_TIMESTAMP`: The initial timestamp cannot be later than this. (default: 1.0)
- `--temperature_increment_on_fallback TEMPERATURE_INCREMENT_ON_FALLBACK, -fallback TEMPERATURE_INCREMENT_ON_FALLBACK`: Temperature to increase when falling back when the decoding fails to meet either of the thresholds below. To disable fallback set it to 'None'. (default: 0.2)
- `--compression_ratio_threshold COMPRESSION_RATIO_THRESHOLD`: If the gzip compression ratio is higher than this value, treat the decoding as failed (default: 2.4)
- `--logprob_threshold LOGPROB_THRESHOLD`: If the average log probability is lower than this value, treat the decoding as failed (default: -1.0)
- `--no_speech_threshold NO_SPEECH_THRESHOLD`: If the probability of the <|nospeech|> token is higher than this value AND the decoding has failed due to 'logprob_threshold', consider the segment as silence (default: 0.6)

### Word-Level Options
- `--word_timestamps WORD_TIMESTAMPS, -wt WORD_TIMESTAMPS`: Extract word-level timestamps and refine the results based on them (default: True)
- `--highlight_words HIGHLIGHT_WORDS, -hw HIGHLIGHT_WORDS`: Underline each word as it is spoken AKA karaoke in srt and vtt output formats. Note: it has no effect with --sentence (default: False)
- `--prepend_punctuations PREPEND_PUNCTUATIONS`: If word_timestamps is True, merge these punctuation symbols with the next word (default: "'\"¿([{-)
- `--append_punctuations APPEND_PUNCTUATIONS`: If word_timestamps is True, merge these punctuation symbols with the previous word (default: "'.。,，!！?？:：")]}、)

### Voice Activity Detection (VAD) Options
- `--vad_filter VAD_FILTER, -vad VAD_FILTER`: Enable the voice activity detection (VAD) to filter out parts of the audio without speech. (default: True)
- `--vad_threshold VAD_THRESHOLD`: Probabilities above this value are considered as speech. (default: 0.45)
- `--vad_min_speech_duration_ms VAD_MIN_SPEECH_DURATION_MS`: Final speech chunks shorter min_speech_duration_ms are thrown out. (default: 250)
- `--vad_max_speech_duration_s VAD_MAX_SPEECH_DURATION_S`: Maximum duration of speech chunks in seconds. Longer will be split at the timestamp of the last silence. (default: None)
- `--vad_min_silence_duration_ms VAD_MIN_SILENCE_DURATION_MS`: In the end of each speech chunk time to wait before separating it. (default: 3000)
- `--vad_speech_pad_ms VAD_SPEECH_PAD_MS`: Final speech chunks are padded by speech_pad_ms each side. (default: 900)
- `--vad_window_size_samples VAD_WINDOW_SIZE_SAMPLES`: Size of audio chunks fed to the silero VAD model. Values other than 512, 1024, 1536 may affect model perfomance!!! (default: 1536)
- `--vad_method {silero_v4_fw,silero_v5_fw,silero_v3,silero_v4,silero_v5,pyannote_v3,pyannote_onnx_v3,auditok,webrtc}`: Read there - 'https://github.com/Purfview/whisper-standalone-win/discussions/231'. (default: silero_v4_fw)
- `--vad_dump`: Dumps VAD timings to a subtitle file for inspection. Additionaly dumps various intermediate audio files for debug. (default: False)
- `--vad_dump_aud`: Additional arg for --vad_dump, collected chunks as audio. (default: False)
- `--vad_device VAD_DEVICE`: Device to use for pyannote_v3/pyannote_onnx_v3 VAD. Default is 'cuda' if CUDA device is detected, else is 'cpu'. If CUDA GPU is a second device then set 'cuda:1'. (default: cuda)

### Hallucination Control Options
- `--hallucination_silence_threshold HALLUCINATION_SILENCE_THRESHOLD, -hst HALLUCINATION_SILENCE_THRESHOLD`: (Experimental) When word_timestamps is True, skip silent periods longer than this threshold (in seconds) when a possible hallucination is detected. Optimal value is somewhere between 2 - 8 seconds. Inactive if None. (default: None)
- `--hallucination_silence_th_temp {0.0,0.2,0.5,0.8,1.0}, -hst_temp {0.0,0.2,0.5,0.8,1.0}`: (Experimental) Additional heuristic for '--hallucination_silence_threshold'. If temperature is higher that this threshold then consider segment as possible hallucination ignoring the hst score. Inactive if 1.0. (default: 1.0)

### Audio Processing Options
- `--clip_timestamps CLIP_TIMESTAMPS, -clip CLIP_TIMESTAMPS`: Comma-separated list start,end,start,end,... timestamps (in seconds) of clips to process. The last end timestamp defaults to the end of the file. VAD is auto-disabled. (default: 0)
- `--max_new_tokens MAX_NEW_TOKENS`: Maximum number of new tokens to generate per-chunk. (default: None)
- `--chunk_length CHUNK_LENGTH`: The length of audio segments. If it is not None, it will overwrite the default chunk_length of the FeatureExtractor. (default: None)
- `--hotwords HOTWORDS`: Pass hint words/phrases to the model. Similar as --reprompt except that it unsafely cuts into the new tokens space when reprompt safely cuts into the context tokens space. Has no effect if --prefix is not None. (default: None)

### Batch Processing Options
- `--batched`: Enables batched inference mode - transcribes audio in batched VAD's chunks. Can increase speed ~2x-4x but will decrease transcription quality. Many options doesn't work in this mode. (default: False)
- `--batch_size BATCH_SIZE`: When using batched inference it sets the maximum number of parallel requests to model for decoding. (default: 8)
- `--multilingual MULTILINGUAL`: Perform language detection on every segment. (default: False)
- `--batch_recursive, -br`: Enables recursive batch files processing. Note: If set then it changes defaults of --output_dir. (default: False)

### Audio Enhancement Options
- `--ff_dump`: Dumps pre-processed audio by the filters to the 16000Hz file and prevents deletion of some intermediate audio files. (default: False)
- `--ff_track {1,2,3,4,5,6}`: Audio track selector. 1 - selects the first audio track. (default: 1)
- `--ff_fc`: Selects only front-center channel (FC) to process. (default: False)
- `--ff_mp3`: Audio filter: Conversion to MP3 and back. (default: False)
- `--ff_sync`: Audio filter: Stretch/squeeze samples to the given timestamps, with a maximum of 3600 samples per second compensation. Input file must be container that support storing PTS like mp4, mkv... (default: False)
- `--ff_rnndn_sh`: Audio filter: Suppress non-speech with GregorR's SH model using Recurrent Neural Networks. Notes: It's more aggressive than Xiph, discards singing. (default: False)
- `--ff_rnndn_xiph`: Audio filter: Suppress non-speech with Xiph's original model using Recurrent Neural Networks. (default: False)
- `--ff_fftdn [0 - 97]`: Audio filter: General denoise with Fast Fourier Transform. Notes: 12 - normal strength, 0 - disabled. (default: 0)
- `--ff_tempo [0.5 - 2.0]`: Audio filter: Adjust audio tempo. Values below 1.0 slows down audio, above - speeds up. 1.0 = disabled. (default: 1.0)
- `--ff_gate`: Audio filter: Reduce lower parts of a signal. (default: False)
- `--ff_speechnorm`: Audio filter: Extreme and fast speech amplification. (default: False)
- `--ff_loudnorm`: Audio filter: EBU R128 loudness normalization. (default: False)
- `--ff_silence_suppress noise duration`: Audio filter: Suppress quiet parts of audio. Takes two values. First value - noise tolerance in decibels [-70 - 0] (0=disabled), second value - minimum silence duration in seconds [0.1 - 10]. (default: [0, 3.0])
- `--ff_lowhighpass`: Audio filter: Pass 50Hz - 7800 band. sinc + afir. (default: False)
- `--ff_mdx_kim2`: Audio filter: High quality vocals extraction. MDX-Net 'Kim_Vocal_2' model made by KimberleyJensen. Notes: It's better than 'HT Demucs v4 FT', first in the filters chain, recommended to use on movies and series. (default: False)
- `--mdx_chunk MDX_CHUNK`: Chunk size in seconds for MDX-Net filter. Notes: Smaller is using less memory, but can be slower and produce a bit lower quality. (default: 15)
- `--mdx_device MDX_DEVICE`: Device to use for MDX-Net filter. Default is 'cuda' if CUDA device is detected, else is 'cpu'. If CUDA GPU is a second device then set 'cuda:1'. (default: cuda)

### Speaker Diarization Options
- `--diarize {pyannote_v3.0,pyannote_v3.1,reverb_v1,reverb_v2}`: Notes: It will activate --sentence and all output formats will be affected, exept json. Read more there - 'https://github.com/Purfview/whisper-standalone-win/discussions/322'. (default: None)
- `--diarize_device DIARIZE_DEVICE`: Device to use for '--diarize'. Default is 'cuda' if CUDA device is detected, else is 'cpu'. If CUDA GPU is a second device then set 'cuda:1'. (default: cuda)
- `--diarize_threads DIARIZE_THREADS`: Automatic by default. (default: 0)
- `--diarize_dump`: Dump diarization output to a file. (default: False)
- `--speaker SPEAKER`: Diarization: To replace 'SPEAKER' string with your own word. (default: SPEAKER)
- `--num_speakers NUM_SPEAKERS`: Diarization: Number of speakers, when known. (default: None)
- `--min_speakers MIN_SPEAKERS`: Diarization: Minimum number of speakers. Has no effect when `num_speakers` is provided. (default: None)
- `--max_speakers MAX_SPEAKERS`: Diarization: Maximum number of speakers. Has no effect when `num_speakers` is provided. (default: None)

### Subtitle Formatting Options
- `--beep_off`: Disables the beep sound when operation is finished. (default: False)
- `--skip`: Skips media file if subtitle exists. Works if input is wildcard or directory. Note: Checks for the first format in the list of --output_format. (default: False)
- `--checkcuda, -cc`: Returns CUDA device count. (for Subtitle Edit's internal use)
- `--print_progress, -pp`: Prints progress bar instead of transcription. (default: False)
- `--postfix`: Adds language as a postfix to subtitle's filename. (default: False)
- `--check_files`: Checks input files for errors before passing all them for transcription. Works if input is wildcard or directory. (default: False)
- `--alt_writer_off`: (For dev experiments) Forcefully disables alternative subs writer func. (default: False)
- `--ignore_dupe_prompt IGNORE_DUPE_PROMPT, -idp IGNORE_DUPE_PROMPT`: PR163 aka don't add dupes to prompt. Reduces possibility of the hallucination loops. Sets how deep to look for dupes in the segments. 0 - Disabled. (default: 2)
- `--hallucinations_list_off`: Disables hallucinations_list, allows known hallucinations to be added to prompt. (default: False)
- `--v3_offsets_off`: Disables custom offsets to the defaults of pseudo-vad thresholds when 'large-v3' models are in use. Note: Offsets made to combat 'large-v3' hallucinations. (default: False)
- `--reprompt REPROMPT, --carry_initial_prompt REPROMPT`: Ensures that initial_prompt is present in prompt for all windows/chunks. Has no effect if initial_prompt is None. (default: True)
- `--prompt_reset_on_no_end {0,1,2}`: Resets prompt if there is no end of sentence in window/chunk. 0 - disabled, 1 - looks for period, 2 - looks for period or comma. Note: it's auto-disabled if reprompt is False and if hotwords is None. (default: 2)
- `--rehot`: For Dev experiments. Just to transfer the auto prompt preset to the hotwords routines. (default: False)
- `--unmerged`: Experimental arg for batched inference. Runs unmerged segments instead of merged, very slow. Possible cons: further decrease of batched transcription quality. Possible pros: more accurate timestamps, less hallucinations, not missing sentences, positive effect with --multilingual. (default: False)
- `--japanese {blend,kanji,hiragana,katakana}, -ja {blend,kanji,hiragana,katakana}`: This option may stear Japanese output to have a more prefered writing style. (default: blend)
- `--one_word {0,1,2}`: 0) Disabled. 1) Outputs srt and vtt subtitles with one word per line. 2) As '1', plus removes whitespace and ensures >= 50ms for sub lines. Note: VAD may slightly reduce the accuracy of timestamps on some lines. (default: 0)
- `--sentence`: Enables splitting lines to sentences. Every sentence starts in the new segment. By default meant to output whole sentence per line for better translations, but not limited to, read about '--max_...' parameters. Doesn't work well when --language is not specified. (default: False)
- `--standard`: Quick hardcoded preset to split lines in standard way: --max_line_width=42, --max_line_count=2, --max_comma_cent=70 and --sentence are activated automatically. (default: False)
- `--standard_asia`: Quick hardcoded preset to split lines in standard way for some Asian languages. --max_line_width=16, --max_line_count=2, --max_comma_cent=80 and --sentence are activated automatically. (default: False)
- `--max_comma MAX_COMMA`: (requires --sentence) After this line length a comma is treated as the end of sentence. Note: disabled if it's over or equal to --max_line_width. (default: 250)
- `--max_comma_cent {20,30,40,50,60,70,80,90,100}`: (requires --sentence) Percentage of --max_line_width when it starts breaking the line after comma. Note: 100 = disabled. (default: 100)
- `--max_gap MAX_GAP`: (requires --sentence) Threshold for a gap length in seconds, longer gaps are treated as dots. (default: 3.0)
- `--max_line_width MAX_LINE_WIDTH`: The maximum number of characters in a line before breaking the line. Note: It works with `--sentence` too. (default: 1000)
- `--max_line_count MAX_LINE_COUNT`: The maximum number of lines in one sub segment. Note: It works with `--sentence` too. (default: 1)
- `--min_dist_to_end {0,4,5,6,7,8,9,10,11,12}`: (requires --sentence) If from words like 'the', 'Mr.' and ect. to the end of line distance is less than set then it starts in a new line. Note: 0 = disabled. (default: 0)

## Language Codes
The tool supports extensive language detection with codes like:
- `ja` - Japanese
- `en` - English
- `zh` - Chinese
- `ko` - Korean
- `th` - Thai
- And many more (see full list above)

## Examples

### Basic Usage
```bash
# Transcribe audio file
faster-whisper-xxl.exe audio.wav

# Transcribe with specific language
faster-whisper-xxl.exe --language ja audio.wav

# Transcribe with custom output directory
faster-whisper-xxl.exe --output_dir ./subtitles audio.wav
```

### Advanced Usage
```bash
# High-quality transcription with GPU
faster-whisper-xxl.exe --model large-v2 --device cuda --compute_type float16 --language ja audio.wav

# Batch processing with VAD
faster-whisper-xxl.exe --vad_filter True --batch_recursive *.wav

# Speaker diarization
faster-whisper-xxl.exe --diarize reverb_v2 --num_speakers 2 audio.wav
```

### Audio Enhancement
```bash
# Denoise and transcribe
faster-whisper-xxl.exe --ff_fftdn 12 --ff_rnndn_sh audio.wav

# Extract vocals and transcribe
faster-whisper-xxl.exe --ff_mdx_kim2 audio.wav
```

## Notes
- Many options have interdependencies and may affect each other
- Some options are experimental and may change behavior
- GPU acceleration provides significant speed improvements
- Batch processing can increase throughput but may reduce accuracy
- VAD filtering helps remove silence and improve transcription quality

## Links
- Documentation: https://github.com/Purfview/whisper-standalone-win
- Discussions: https://github.com/Purfview/whisper-standalone-win/discussions
- CTranslate2 Quantization: https://opennmt.net/CTranslate2/quantization.html
