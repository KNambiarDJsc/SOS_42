"""
Embedding service using Qwen3-Embedding model.
Supports instruction-aware embeddings with last-token pooling.
"""
import torch
from transformers import AutoModel, AutoTokenizer
import numpy as np
from typing import List, Union


class EmbeddingService:
    def __init__(self, model_name: str = "Qwen/Qwen3-Embedding-4B"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load model and tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(
            model_name,
            trust_remote_code=True
        ).to(self.device)
        
        # Freeze model parameters to prevent OOM during inference
        for p in self.model.parameters():
            p.requires_grad = False
        
        self.model.eval()
        
        # Embedding dimension
        self.embedding_dim = self.model.config.hidden_size

    def embed_documents(
        self, 
        texts: List[str], 
        batch_size: int = 32
    ) -> np.ndarray:
        """
        Embed documents with batching to prevent OOM.
        Filters out tiny chunks (<10 chars).
        """
        # Filter tiny chunks
        valid_texts = []
        valid_indices = []
        
        for idx, text in enumerate(texts):
            if len(text.strip()) >= 10:
                valid_texts.append(text)
                valid_indices.append(idx)
        
        if not valid_texts:
            return np.array([])
        
        # Process in batches
        all_embeddings = []
        
        for i in range(0, len(valid_texts), batch_size):
            batch_texts = valid_texts[i:i + batch_size]
            batch_embeddings = self._embed_batch(batch_texts, is_query=False)
            all_embeddings.append(batch_embeddings)
        
        # Concatenate all batches
        embeddings = np.vstack(all_embeddings)
        
        # Create full array with zeros for filtered chunks
        full_embeddings = np.zeros((len(texts), self.embedding_dim))
        full_embeddings[valid_indices] = embeddings
        
        return full_embeddings

    def embed_query(self, query: str) -> np.ndarray:
        """
        Embed query with instruction-aware prefix.
        """
        if len(query.strip()) < 10:
            # Return zero vector for tiny queries
            return np.zeros(self.embedding_dim)
        
        return self._embed_batch([query], is_query=True)[0]

    def _embed_batch(
        self, 
        texts: List[str], 
        is_query: bool = False
    ) -> np.ndarray:
        """
        Internal method to embed a batch of texts.
        Uses instruction-aware prompts and last-token pooling.
        """
        # Add instruction prefix for queries
        if is_query:
            task = "Given a question, retrieve passages that answer the question"
            texts = [f"Instruct: {task}\nQuery: {text}" for text in texts]
        
        # Tokenize
        inputs = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt"
        ).to(self.device)
        
        # Generate embeddings
        with torch.no_grad():
            outputs = self.model(**inputs)
            
            # Last-token pooling
            embeddings = self._last_token_pool(
                outputs.last_hidden_state,
                inputs['attention_mask']
            )
            
            # Normalize for cosine similarity
            embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
        
        return embeddings.cpu().numpy()

    def _last_token_pool(
        self, 
        hidden_states: torch.Tensor, 
        attention_mask: torch.Tensor
    ) -> torch.Tensor:
        """
        Pool embeddings using the last token position.
        """
        left_padding = (attention_mask[:, -1].sum() == attention_mask.shape[0])
        
        if left_padding:
            return hidden_states[:, -1]
        else:
            sequence_lengths = attention_mask.sum(dim=1) - 1
            batch_size = hidden_states.shape[0]
            return hidden_states[
                torch.arange(batch_size, device=hidden_states.device), 
                sequence_lengths
            ]