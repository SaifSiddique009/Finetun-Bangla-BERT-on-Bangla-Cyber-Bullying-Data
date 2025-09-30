"""
Generic Transformer-based Multi-Label Classifier
Supports any transformer model (BERT, RoBERTa, XLM-RoBERTa, etc.) through AutoModel
"""

import torch.nn as nn
from transformers import AutoModel, AutoConfig


class TransformerMultiLabelClassifier(nn.Module):
    """
    Generic transformer-based multi-label classifier.
    Works with any transformer model from HuggingFace (BERT, RoBERTa, XLM-RoBERTa, etc.)
    """
    
    def __init__(self, model_name, num_labels, dropout=0.1):
        """
        Initialize the multi-label classifier.
        
        Args:
            model_name (str): Name or path of pre-trained transformer model
            num_labels (int): Number of labels for multi-label classification
            dropout (float): Dropout rate for regularization
        """
        super(TransformerMultiLabelClassifier, self).__init__()
        
        # Auto-detect and load any transformer model
        self.encoder = AutoModel.from_pretrained(model_name)
        
        # Get the hidden size from the model's config
        config = AutoConfig.from_pretrained(model_name)
        hidden_size = config.hidden_size
        
        # Classification head with intermediate layer for better feature extraction
        self.classifier = nn.Sequential(
            nn.Linear(hidden_size, 256),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(256, num_labels)
        )
    
    def forward(self, input_ids, attention_mask=None, labels=None):
        """
        Forward pass of the model.
        
        Args:
            input_ids: Token IDs from tokenizer
            attention_mask: Attention mask for padding
            labels: Ground truth labels (optional, for loss calculation)
            
        Returns:
            dict: Dictionary containing loss (if labels provided) and logits
        """
        # Get encoder outputs (works for BERT, RoBERTa, XLM-RoBERTa, etc.)
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        
        # Extract CLS token representation (first token)
        # This pattern works for most transformer models
        cls_output = outputs.last_hidden_state[:, 0, :]
        
        # Pass through classification head
        logits = self.classifier(cls_output)
        
        # Calculate loss if labels are provided
        loss = None
        if labels is not None:
            loss_fct = nn.BCEWithLogitsLoss()
            loss = loss_fct(logits, labels)
        
        return {'loss': loss, 'logits': logits}
    
    def freeze_base_layers(self):
        """
        Freeze encoder parameters for feature extraction.
        This prevents updating the pre-trained weights during training.
        
        Note: This is now an instance method (bug fix from original code)
        """
        for param in self.encoder.parameters():
            param.requires_grad = False
        
        # Count frozen parameters for logging
        frozen_params = sum(p.numel() for p in self.encoder.parameters())
        total_params = sum(p.numel() for p in self.parameters())
        print(f"Frozen {frozen_params:,} parameters out of {total_params:,} total parameters")
        print(f"Trainable parameters: {total_params - frozen_params:,}")
    
    def unfreeze_base_layers(self):
        """
        Unfreeze encoder parameters (useful for fine-tuning after feature extraction).
        """
        for param in self.encoder.parameters():
            param.requires_grad = True
        
        trainable_params = sum(p.numel() for p in self.parameters() if p.requires_grad)
        print(f"All parameters unfrozen. Trainable parameters: {trainable_params:,}")