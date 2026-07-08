import wikipediaapi
import regex as re  # Note: pip install regex (standard 're' does not support \p{})
import json
from collections import Counter

def get_all_wiki_data(page_titles, languages):
    """
    Fetches Wikipedia text for a list of titles across multiple languages.
    """
    all_data = {}

    # Initialize the Wikipedia API once
    wiki_wiki = wikipediaapi.Wikipedia(
        user_agent='MyWikiScraper/1.0 (contact: your-email@example.com)',
        language='en'  # Default language, we will switch it dynamically
    )

    for lang in languages:
        wiki_wiki.language = lang
        # Wikipedia page titles vary by language (e.g., 'India' in English vs 'भारत' in Hindi)
        title = page_titles.get(lang)

        if not title:
            continue

        page = wiki_wiki.page(title)

        if page.exists():
            all_data[lang] = page.text
            print(f"Successfully fetched {lang} ({title})")
        else:
            all_data[lang] = ""
            print(f"Failed to fetch {lang}")

    return all_data


# --- 1. Fetching Data ---
titles = {
    'en': 'India',
    'hi': 'भारत',
    'te': 'భారతదేశం',
    'es': 'India'
}
languages = ['en', 'hi', 'te', 'es']

corpus_data = get_all_wiki_data(titles, languages)
sentences = "".join(corpus_data.values())

# --- 2. Regex Tokenization ---
pat_str = "|".join([
    r"""[^\r\n\p{L}\p{N}]?[\p{Lu}\p{Lt}\p{Lm}\p{Lo}\p{M}]*[\p{Ll}\p{Lm}\p{Lo}\p{M}]+(?i:'s|'t|'re|'ve|'m|'ll|'d)?""",
    r"""[^\r\n\p{L}\p{N}]?[\p{Lu}\p{Lt}\p{Lm}\p{Lo}\p{M}]+[\p{Ll}\p{Lm}\p{Lo}\p{M}]*(?i:'s|'t|'re|'ve|'m|'ll|'d)?""",
    r"""\p{N}{1,3}""",
    r""" ?[^\s\p{L}\p{N}]+[\r\n/]*""",
    r"""\s*[\r\n]+""",
    r"""\s+(?!\S)""",
    r"""\s+""",
])

sentence_list = re.findall(pat_str, sentences)


# --- 3. BPE Helper Functions ---
def max_sort_counter(corpus):
    top_word = {}
    bigrams = []
    
    for sentence_tokens in corpus:
        for i in zip(sentence_tokens, sentence_tokens[1:]):
            bigrams.append(i)
            
    if len(bigrams) > 0:
        top_word = Counter(bigrams)
        max_word = top_word.most_common(1)[0][0]
        return max_word, dict(top_word)
    else:
        return None, None


merges = {}

def create_vocab_gpt(max_occur, sen_encode, idx):
    print(f"Merging {max_occur} to id: {idx}")
    final_gpt_corpus_new_encoding = []
    
    for sen_list in sen_encode:
        counter = 0
        new_encoding = []
        while counter < len(sen_list):
            if counter < len(sen_list) - 1 and sen_list[counter] == max_occur[0] and sen_list[counter + 1] == max_occur[1]:
                new_encoding.append(idx)
                merges[max_occur] = idx
                counter += 2
            else:
                new_encoding.append(sen_list[counter])
                counter += 1
        final_gpt_corpus_new_encoding.append(new_encoding)
        
    return final_gpt_corpus_new_encoding


# --- 4. Training BPE ---
# Initialize the corpus as a list of byte arrays based on the regex split
gptstyple_corpus = [list(sen.encode('utf-8')) for sen in sentence_list]
idx = 256

for i in range(9750):
    max_occur, _ = max_sort_counter(gptstyple_corpus)
    
    # Break early if there are no more pairs to merge
    if max_occur is None:
        print(f"Stopping early at iteration {i}: No more pairs to merge.")
        break
        
    gptstyple_corpus = create_vocab_gpt(max_occur, gptstyple_corpus, idx)
    idx += 1


# --- 5. Vocab Construction & Decoding ---
vocab = {i: bytes([i]) for i in range(256)}

for (one, two), quantity in merges.items():
    vocab[quantity] = vocab[one] + vocab[two]

def decode(ids):
    decoded_s = b"".join(vocab[i] for i in ids)
    text = decoded_s.decode("utf-8", errors='replace')
    return text


# --- 6. Saving Artifacts ---
with open("vocab_regex_gpt.json", "w", encoding="utf-8") as f:
    # Decode bytes values to strings before dumping to JSON
    serializable_vocab = {k: v.decode('utf-8', errors='replace') if isinstance(v, bytes) else v for k, v in vocab.items()}
    json.dump(serializable_vocab, f, ensure_ascii=False, indent=2)

with open("merges_regex_gpt.txt", "w", encoding="utf-8") as f:
    for (a, b) in merges:
        # Standard format: write the two tokens separated by a space
        f.write(f"{a} {b}\n")


# --- 7. Encoding ---
def encode(text):
    text_list = re.findall(pat_str, text)
    tok = [list(sen.encode('utf-8')) for sen in text_list]
    
    while True:
        t, tr = max_sort_counter(tok)
        
        if tr:
            # Find the pair available in our merges dictionary with the lowest priority index
            pair_to_merge = min(tr.keys(), key=lambda p: merges.get(p, float('inf')))
        else:
            break
            
        if pair_to_merge is None or pair_to_merge not in merges:
            break
            
        merge_idx = merges.get(pair_to_merge)
        tok = create_vocab_gpt(pair_to_merge, tok, merge_idx)
        
    final_encode = [num for sublist in tok for num in sublist]   
    return final_encode
