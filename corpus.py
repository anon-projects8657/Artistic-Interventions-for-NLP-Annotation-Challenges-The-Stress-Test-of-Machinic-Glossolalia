import re
import os

input_file = 'nonsensecorpus.txt.rtf'
output_file = 'syllabified_output.txt'

def strip_rtf(text):
    text = re.sub(r"{\\.*?}", "", text)
    text = re.sub(r"\\[a-zA-Z]+\d*", "", text)
    text = re.sub(r"\\'[0-9a-fA-F]{2}", "", text)
    text = text.replace("{", "").replace("}", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def tokenize_word_by_syllable(word):
    syllables = re.findall(r'[bcdfghjklmnpqrstvwxyz]*[aeiouáàâäãéèêëẽíìîïĩóòôöõúùûüũ]+', word, flags=re.IGNORECASE)
    if not syllables:
        return [word]
    return syllables

def create_corpus(input_file, output_file):
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"{input_file} not found.")

    with open(input_file, "r", encoding="utf-8") as f_in:
        raw_rtf = f_in.read()
        clean_text = strip_rtf(raw_rtf)

    with open(output_file, "w", encoding="utf-8") as f_out:
        lines = clean_text.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            words = re.findall(r"\S+", line)
            syllabified_words = [" ".join(tokenize_word_by_syllable(word)) for word in words]
            f_out.write(" ".join(syllabified_words) + "\n")

    print(f"Corpus created: {output_file}")

if __name__ == "__main__":
    create_corpus(input_file, output_file)