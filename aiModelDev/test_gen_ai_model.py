import math
from transformers import GPT2LMHeadModel, GPT2Tokenizer

# Load the fine-tuned model and tokenizer
tokenizer = GPT2Tokenizer.from_pretrained("./gen_ai_model")
tokenizer.pad_token = tokenizer.eos_token
model = GPT2LMHeadModel.from_pretrained("./gen_ai_model")

#prompt = "The stars"
prompt = "bbbbb"
inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True)
outputs = model.generate(
    inputs["input_ids"],
    attention_mask=inputs["attention_mask"], 
    max_length=50,
    num_return_sequences=1,
    temperature=0.7,
    top_p=0.9,
    do_sample=True    
)

for i, output in enumerate(outputs):
    print(f"Generated Text {i+1}:\n{tokenizer.decode(output, skip_special_tokens=True)}")


def calculate_perplexity(text):
    tokenizer = GPT2Tokenizer.from_pretrained("./gen_ai_model")
    model = GPT2LMHeadModel.from_pretrained("./gen_ai_model")
    inputs = tokenizer(text, return_tensors="pt")
    outputs = model(**inputs, labels=inputs["input_ids"])
    loss = outputs.loss.item()
    perplexity = math.exp(loss)
    return perplexity

#text = "The stars twinkle in the midnight sky."
text = "blah blah"
print(f"Perplexity: {calculate_perplexity(text):.2f}")