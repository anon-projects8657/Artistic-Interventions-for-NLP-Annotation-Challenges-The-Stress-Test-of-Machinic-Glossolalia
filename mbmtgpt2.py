import os
from striprtf.striprtf import rtf_to_text
from transformers import GPT2Tokenizer, TFGPT2LMHeadModel
from transformers import DataCollatorForLanguageModeling
import tensorflow as tf

# ---------------- CONFIG ----------------
corpus_rtf_file = "nonsensecorpus.txt.rtf"
corpus_txt_file = "syllabified_output.txt"
model_name = "gpt2"
fine_tuned_dir = "gpt2_tone_model"
num_train_epochs = 3
batch_size = 2
block_size = 128  # max sequence length

# ---------------- FUNCTIONS ----------------
def convert_rtf_to_txt(rtf_path, txt_path):
    with open(rtf_path, "r") as f:
        rtf_content = f.read()
    text = rtf_to_text(rtf_content)
    text = " ".join(text.split())  # clean whitespace
    with open(txt_path, "w") as f:
        f.write(text)
    print(f"Converted and cleaned text saved to {txt_path}")

def load_and_tokenize(txt_file, tokenizer, block_size):
    with open(txt_file, "r") as f:
        text = f.read()
    encodings = tokenizer(text, return_tensors="tf", truncation=True, max_length=block_size)
    return encodings

def prepare_dataset(encodings):
    input_ids = encodings["input_ids"]
    attention_mask = encodings["attention_mask"]
    dataset = tf.data.Dataset.from_tensor_slices((input_ids, input_ids))
    dataset = dataset.shuffle(1000).batch(batch_size)
    return dataset

# ---------------- MAIN PIPELINE ----------------
if __name__ == "__main__":
    # Step 0: Convert RTF -> TXT
    convert_rtf_to_txt(corpus_rtf_file, corpus_txt_file)

    # Step 1: Load tokenizer & model
    tokenizer = GPT2Tokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token  # GPT-2 has no pad token

    model = TFGPT2LMHeadModel.from_pretrained(model_name)

    # Step 2: Tokenize dataset
    encodings = load_and_tokenize(corpus_txt_file, tokenizer, block_size)

    # Step 3: Prepare tf.data.Dataset
    dataset = prepare_dataset(encodings)

    # Step 4: Compile & fine-tune model
    optimizer = tf.keras.optimizers.Adam(learning_rate=5e-5)
    loss = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
    model.compile(optimizer=optimizer, loss=loss)

    print("Fine-tuning GPT-2...")
    model.fit(dataset, epochs=num_train_epochs)

    # Step 5: Save fine-tuned model locally
    model.save_pretrained(fine_tuned_dir)
    tokenizer.save_pretrained(fine_tuned_dir)
    print(f"Fine-tuned GPT-2 saved to {fine_tuned_dir}")
