"""Training Pipeline."""
import torch
from torch.optim import Optimizer
from torch.utils.data import DataLoader
from tqdm import tqdm

import wandb
from sparse_autoencoder.autoencoder.loss import (
    l1_loss,
    reconstruction_loss,
    sae_training_loss,
)
from sparse_autoencoder.autoencoder.model import SparseAutoencoder
from sparse_autoencoder.train.sweep_config import SweepParametersRuntime


def train_autoencoder(
    activations_dataloader: DataLoader,
    autoencoder: SparseAutoencoder,
    optimizer: Optimizer,
    sweep_parameters: SweepParametersRuntime,
    log_interval: int = 10,
    device: torch.device | None = None,
):
    """Sparse Autoencoder Training Loop.

    Args:
        activations_dataloader: DataLoader containing activations.
        autoencoder: Sparse autoencoder model.
        optimizer: The optimizer to use.
        sweep_parameters: The sweep parameters to use.
        log_interval: How often to log progress.
    """
    torch.autograd.set_detect_anomaly(True)

    with torch.set_grad_enabled(True):
        for step, batch in tqdm(
            enumerate(activations_dataloader),
            desc="Train Autoencoder",
            leave=False,
            total=len(activations_dataloader.dataset) // activations_dataloader.batch_size,  # type: ignore,
            unit_scale=activations_dataloader.batch_size,
        ):
            # Zero the gradients
            optimizer.zero_grad()

            # Move the batch to the device (in place)
            batch = batch.to(device)

            # Forward pass
            learned_activations, reconstructed_activations = autoencoder(batch)

            # Get metrics
            reconstruction_loss_mse = reconstruction_loss(
                batch, reconstructed_activations
            )
            l1_loss_learned_activations = l1_loss(learned_activations)
            total_loss = sae_training_loss(
                reconstruction_loss_mse,
                l1_loss_learned_activations,
                sweep_parameters.l1_coefficient,
            )
            # TODO: Log dead neurons metric (get_frequencies in Neel's code)

            # Backwards pass
            total_loss.backward()

            # TODO: Make decoder weights and grad unit norm

            optimizer.step()

            # TODO: Enable neuron resampling

            # Log
            if step % log_interval == 0 and wandb.run is not None:
                wandb.log(
                    {
                        "reconstruction_loss": reconstruction_loss_mse,
                        "l1_loss": l1_loss_learned_activations,
                        "loss": total_loss,
                    }
                )
