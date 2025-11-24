using NanoGpt.Core.Configuration;
using TorchSharp;

namespace NanoGpt.Core.Model;

public sealed class NanoGptLanguageModel : TorchSharp.torch.nn.Module
{
    private readonly TorchSharp.Modules.Embedding _tokenEmbeddingTable;
    private readonly TorchSharp.Modules.Embedding _positionEmbeddingTable;
    private readonly TorchSharp.Modules.ModuleList<TorchSharp.torch.nn.Module> _blocks;
    private readonly TorchSharp.Modules.LayerNorm _finalLayerNorm;
    private readonly TorchSharp.Modules.Linear _lmHead;
    private readonly int _blockSize;

    public NanoGptLanguageModel(ModelConfig config) : base("nanogpt")
    {
        _blockSize = config.BlockSize;
        _tokenEmbeddingTable = TorchSharp.torch.nn.Embedding(config.VocabSize, config.EmbeddingDimension);
        _positionEmbeddingTable = TorchSharp.torch.nn.Embedding(config.BlockSize, config.EmbeddingDimension);

        var modules = new TorchSharp.torch.nn.Module[config.NumLayers];
        for (var i = 0; i < config.NumLayers; i++)
        {
            // Simplified: use Linear layers instead of complex blocks for now
            modules[i] = TorchSharp.torch.nn.Linear(config.EmbeddingDimension, config.EmbeddingDimension, hasBias: false);
        }

        _blocks = TorchSharp.torch.nn.ModuleList(modules);
        _finalLayerNorm = TorchSharp.torch.nn.LayerNorm(config.EmbeddingDimension);
        _lmHead = TorchSharp.torch.nn.Linear(config.EmbeddingDimension, config.VocabSize, hasBias: false);

        RegisterComponents();
    }

    private new void RegisterComponents()
    {
        register_module(nameof(_tokenEmbeddingTable), _tokenEmbeddingTable);
        register_module(nameof(_positionEmbeddingTable), _positionEmbeddingTable);
        register_module(nameof(_blocks), _blocks);
        register_module(nameof(_finalLayerNorm), _finalLayerNorm);
        register_module(nameof(_lmHead), _lmHead);
    }

    public int BlockSize => _blockSize;

    public TorchSharp.torch.Tensor Forward(TorchSharp.torch.Tensor index)
    {
        using var _ = TorchSharp.torch.NewDisposeScope();
        var device = index.device;
        var (batchSize, timeSteps) = (index.shape[0], index.shape[1]);

        var tokenEmbeddings = _tokenEmbeddingTable.forward(index);
        var positionIndices = TorchSharp.torch.arange(0, timeSteps, device: device).unsqueeze(0);
        var positionEmbeddings = _positionEmbeddingTable.forward(positionIndices);

        var x = tokenEmbeddings + positionEmbeddings;
        foreach (var block in _blocks)
        {
            x = ((TorchSharp.Modules.Linear)block).forward(x);
        }

        x = _finalLayerNorm.forward(x);
        var logits = _lmHead.forward(x);
        return logits.MoveToOuterDisposeScope();
    }

    public (TorchSharp.torch.Tensor loss, TorchSharp.torch.Tensor logits) ForwardWithLoss(TorchSharp.torch.Tensor idx, TorchSharp.torch.Tensor targets)
    {
        using var _ = TorchSharp.torch.NewDisposeScope();
        var logits = Forward(idx);
        var loss = TorchSharp.torch.nn.functional.cross_entropy(logits.view(-1, logits.shape[^1]), targets.view(-1));
        return (loss.MoveToOuterDisposeScope(), logits.MoveToOuterDisposeScope());
    }
}
