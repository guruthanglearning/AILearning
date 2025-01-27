import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from torch.optim import AdamW

# Load the pre-trained GPT-2 tokenizer and model
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
model = GPT2LMHeadModel.from_pretrained("gpt2")

# Load training data
with open("resource\data.txt", "r") as file:
    dataset = file.read()

# Tokenize the data
inputs = tokenizer(dataset, return_tensors="pt", max_length=512, truncation=True)

print

# Define optimizer
optimizer = AdamW(model.parameters(), lr=5e-5)

# Training loop (1 epoch for simplicity)
model.train()
for epoch in range(1):
    outputs = model(**inputs, labels=inputs["input_ids"])
    loss = outputs.loss
    loss.backward()
    optimizer.step()
    optimizer.zero_grad()
    print(f"Epoch {epoch+1}, Loss: {loss.item()}")

model.save_pretrained("./gen_ai_model")
tokenizer.save_pretrained("./gen_ai_model")
print("Model saved successfully!")