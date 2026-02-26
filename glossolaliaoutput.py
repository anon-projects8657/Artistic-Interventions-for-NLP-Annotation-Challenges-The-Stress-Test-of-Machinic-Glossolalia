import os
import serial
import time
import re
import pyttsx3
import random
import datetime
from transformers import GPT2Tokenizer, TFGPT2LMHeadModel, pipeline

# CONFIGURATION
ARDUINO_PORT = '/dev/cu.usbmodem1201'
BAUD_RATE = 9600

model_dir = "gpt2_glossolalia"
audio_folder = "nonsense_audio"
os.makedirs(audio_folder, exist_ok=True)

MAX_DISTANCE_CM = 200.0

PROMPT_POOL = [
    "jolifanto","bambla","o","falli","großiga","m'pfa","habla","horem",
    "egiga","goramen","higo","bloiko","russula","huju","hollaka",
    "hollala","anlogo","bung","blago","bosso","fataka","ü","üü",
    "schampa","wulla","wussa","olobo","hej","tatta","gorem",
    "eschige","zunbada","wulubu","ssubudu","uluwu","–umf","kusa",
    "gauma","ba–umf"
]

BASE_PROMPTS = [
    "jolifanto bambla o falli bambla",
    "großiga m'pfa habla horem",
    "egiga goramen",
    "higo bloiko russula huju",
    "hollaka hollala",
    "anlogo bung",
    "blago bung blago bung",
    "bosso fataka",
    "ü üü ü",
    "schampa wulla wussa olobo",
    "hej tatta gorem",
    "eschige zunbada",
    "wulubu ssubudu uluwu ssubudu",
    "–umf",
    "kusa gauma",
    "ba–umf",
]

# LOAD MODEL
tokenizer = GPT2Tokenizer.from_pretrained(model_dir)
tokenizer.pad_token = tokenizer.eos_token
model = TFGPT2LMHeadModel.from_pretrained(model_dir)
generator = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    framework="tf"
)

# INIT TTS
engine = pyttsx3.init()
engine.setProperty("rate", 150)
engine.setProperty("volume", 1.0)

# HELPERS
def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()

def map_range(x, in_min, in_max, out_min, out_max):
    if in_max - in_min == 0:
        return out_min
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def parse_arduino_line(line):
    try:
        line_str = line.decode("utf-8").strip()
        parts = line_str.split(",")
        if len(parts) == 6:
            return {
                "HUMIDITY": float(parts[0]),
                "TEMPERATURE": float(parts[1]),
                "PRESSURE": float(parts[2]),
                "GAS": float(parts[3]),
                "DISTANCE_CM": float(parts[4]),
                "LIGHT_STATE": int(parts[5]),
            }
    except:
        return None
    return None

def generate_dynamic_prompt(score):
    num_words = int(map_range(score, 0.0, 1.0, 2, 5))
    num_words = max(2, min(5, num_words))
    if score < 0.2:
        return random.choice(BASE_PROMPTS).capitalize()
    else:
        return " ".join(random.sample(PROMPT_POOL, k=num_words)).capitalize()

# MAIN LOOP
def main():
    try:
        ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=0.1)
        time.sleep(2)
        ser.flushInput()

        last_distance = MAX_DISTANCE_CM

        while True:
            line = ser.readline()
            sensor_data = parse_arduino_line(line) if line else None

            if sensor_data:
                h = sensor_data["HUMIDITY"]
                t = sensor_data["TEMPERATURE"]
                p = sensor_data["PRESSURE"]
                g = sensor_data["GAS"]
                dist = sensor_data["DISTANCE_CM"]
                light = sensor_data["LIGHT_STATE"]

                # COMPOSITE NONSENSE SCORE
                proximity = 1.0 - max(0.0, min(1.0, dist / MAX_DISTANCE_CM)) * 0.3
                gas = max(0.0, min(1.0, map_range(g, 50, 500, 1.0, 0.0))) * 0.2
                hum_dev = abs(h - 50.0) / 50.0
                temp_dev = abs(t - 22.0) / 10.0
                pres_dev = abs(p - 1013.0) / 20.0
                env = max(0.0, min(1.0, (hum_dev + temp_dev + pres_dev)/3.0)) * 0.3
                light_w = 0.2 if light == 0 else 0.0
                total_nonsense = max(0.0, min(1.0, proximity + gas + env + light_w))

                target_temp = max(0.7, min(4.0, map_range(total_nonsense, 0.0, 1.0, 0.7, 4.0)))
                seed = generate_dynamic_prompt(total_nonsense)
                last_distance = dist

                # GENERATE
                outputs = generator(
                    seed,
                    max_new_tokens=30,
                    temperature=target_temp,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id,
                    repetition_penalty=1.2,
                )

                spoken_text = clean_text(outputs[0]["generated_text"])
                
                # PRINT ONLY WHAT IS BEING SPOKEN
                if spoken_text:
                    print(spoken_text)

                    # TTS
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = os.path.join(audio_folder, f"nonsense_{timestamp}.wav")
                    engine.save_to_file(spoken_text, filename)
                    engine.say(spoken_text)
                    engine.runAndWait()

    except serial.SerialException:
        print(f"Could not open port {ARDUINO_PORT}.")
    except KeyboardInterrupt:
        if 'ser' in locals() and ser.is_open:
            ser.close()

if __name__ == "__main__":
    main()