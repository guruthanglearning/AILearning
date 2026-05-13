import torch
from models.simple_transformer import SimpleTransformer

# Load model
model = torch.load("saved_model.pth")
model.eval()

# Generate function
def generate_text(model, prompt, max_length=50):
    input_ids = torch.tensor(list(map(ord, prompt))).unsqueeze(0)

    with torch.no_grad():
        output = model(input_ids)

    predicted_tokens = torch.argmax(output, dim=-1)
    return "".join(map(chr, predicted_tokens[0].cpu().numpy()))

# Test
prompt = "The quick brown fox"
print(generate_text(model, prompt))