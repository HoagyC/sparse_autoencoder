"""Tied Bias Tests."""
from jaxtyping import Float
import torch
from torch import Tensor

from sparse_autoencoder.autoencoder.components.tied_bias import TiedBias, TiedBiasPosition
from sparse_autoencoder.tensor_types import Axis


def test_pre_encoder_subtracts_bias() -> None:
    """Check that the pre-encoder bias subtracts the bias."""
    encoder_input: Float[Tensor, Axis.names(Axis.BATCH, Axis.INPUT_OUTPUT_FEATURE)] = torch.tensor(
        [[5.0, 3.0, 1.0]]
    )
    bias = torch.tensor([2.0, 4.0, 6.0])
    expected = encoder_input - bias

    pre_encoder = TiedBias(bias, TiedBiasPosition.PRE_ENCODER)
    output = pre_encoder(encoder_input)

    assert torch.allclose(output, expected)


def test_post_encoder_adds_bias() -> None:
    """Check that the post-encoder bias adds the bias."""
    decoder_output: Float[Tensor, Axis.names(Axis.BATCH, Axis.INPUT_OUTPUT_FEATURE)] = torch.tensor(
        [[5.0, 3.0, 1.0]]
    )
    bias = torch.tensor([2.0, 4.0, 6.0])
    expected = decoder_output + bias

    post_decoder = TiedBias(bias, TiedBiasPosition.POST_DECODER)
    output = post_decoder(decoder_output)

    assert torch.allclose(output, expected)
