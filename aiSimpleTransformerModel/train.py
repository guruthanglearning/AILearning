import sys
sys.path.append("D:\Study\AILearning\shared_env\Lib\site-packages")

import torch
import torch.nn as nn
import torch.optim as optim
from datasets import load_dataset
import sys
sys.path.append("./")  # Ensure project root is in Python's path
from models.simple_transformer import SimpleTransformer

# Set device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load dataset
dataset = load_dataset("wikitext", "wikitext-2-raw-v1", split="train").map(
    lambda x: {"input_ids": torch.tensor(list(map(ord, x["text"][:128]))), "labels": torch.tensor(list(map(ord, x["text"][:128])))}
)

# Define model hyperparameters
vocab_size = 50000
embed_size = 256
num_layers = 4
heads = 4
dropout = 0.1
forward_expansion = 4
max_length = 512

# Initialize model
model = SimpleTransformer(vocab_size, embed_size, num_layers, heads, device, forward_expansion, dropout, max_length).to(device)

# Define optimizer & loss function
optimizer = optim.Adam(model.parameters(), lr=3e-4)
criterion = nn.CrossEntropyLoss()

# Training loop
def train_model(model, dataset, optimizer, criterion, epochs=3):
    model.train()
    for epoch in range(epochs):
        for batch in dataset:
            inputs, targets = batch["input_ids"], batch["labels"]
            inputs, targets = inputs.to(device), targets.to(device)

            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs.view(-1, outputs.size(-1)), targets.view(-1))
            loss.backward()
            optimizer.step()
        
        print(f"Epoch {epoch+1}, Loss: {loss.item()}")

# Train the model
train_model(model, dataset, optimizer, criterion)