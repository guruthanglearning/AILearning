import torch
import torch.nn as nn
from models.positional_encoding import PositionalEncoding
from models.transformer_block import TransformerBlock

class SimpleTransformer(nn.Module):
    def __init__(self, vocab_size, embed_size, num_layers, heads, device, forward_expansion, dropout, max_length):
        super().__init__()
        self.device = device
        self.word_embedding = nn.Embedding(vocab_size, embed_size)
        self.position_embedding = PositionalEncoding(embed_size, max_length)

        self.layers = nn.ModuleList(
            [TransformerBlock(embed_size, heads, dropout, forward_expansion) for _ in range(num_layers)]
        )

        self.fc_out = nn.Linear(embed_size, vocab_size)
        self.dropout = nn.Dropout(dropout)
        
    def forward(self, x):
        x = self.word_embedding(x)
        x = self.position_embedding(x)
        
        for layer in self.layers:
            x = layer(x)

        return self.fc_out(x)