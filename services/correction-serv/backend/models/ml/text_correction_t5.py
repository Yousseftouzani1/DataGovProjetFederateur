"""
T5-based Text Correction Model
================================
Data Quality V2 - Section 8.6

Intelligent correction using T5 (Text-to-Text Transfer Transformer)
for format, semantic, and text-based inconsistencies.

As per specification:
- Input format: "correct: <incorrect_value> context: <field_name>"
- Output: Corrected value
- Confidence threshold: 0.9 for auto-apply
"""

from typing import Tuple, List, Dict, Any, Optional
import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer
import warnings
warnings.filterwarnings('ignore')


class TextCorrectionT5:
    """
    T5-based intelligent text correction
    
    Features:
    - Pre-trained T5 model with optional fine-tuning
    - Confidence scoring based on model probabilities
    - Batch processing for efficiency
    - Context-aware correction suggestions
    """
    
    DEFAULT_CONFIDENCE = 0.85
    MIN_CONFIDENCE = 0.6
    
    def __init__(self, model_name: str = "t5-small", device: str = "cpu"):
        """
        Initialize T5 corrector
        
        Args:
            model_name: HuggingFace model name (t5-small for faster, t5-base for better quality)
            device: 'cpu' or 'cuda' for GPU acceleration
        """
        self.device = device
        self.model_name = model_name
        
        try:
            print(f"📥 Loading T5 model: {model_name}...")
            self.tokenizer = T5Tokenizer.from_pretrained(model_name)
            self.model = T5ForConditionalGeneration.from_pretrained(model_name)
            self.model.to(device)
            self.model.eval()  # Set to evaluation mode
            print(f"✅ T5 Corrector loaded successfully")
        except Exception as e:
            print(f"⚠️ Failed to load T5 model: {e}")
            print(f"💡 Using fallback mode (rule-based only)")
            self.model = None
            self.tokenizer = None
    
    def correct(
        self, 
        value: str, 
        context: str, 
        row_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, float]:
        """
        Suggest correction for incorrect value
        
        Args:
            value: The incorrect value to correct
            context: Field name or context (e.g., "date_naissance", "email")
            row_data: Optional full row context for better suggestions
            
        Returns:
            (corrected_value, confidence_score)
        """
        if self.model is None or self.tokenizer is None:
            # Fallback: return original with low confidence
            return value, 0.0
        
        # Format input as per specification (Section 8.6)
        input_text = f"correct: {value} context: {context}"
        
        # Add row context if available (improves accuracy)
        if row_data:
            row_str = " ".join([f"{k}={v}" for k, v in list(row_data.items())[:3]])
            input_text += f" row: {row_str}"
        
        try:
            # Tokenize input
            inputs = self.tokenizer(
                input_text,
                return_tensors="pt",
                max_length=128,
                truncation=True,
                padding=True
            ).to(self.device)
            
            # Generate correction with confidence tracking
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_length=50,
                    num_beams=5,
                    early_stopping=True,
                    temperature=0.7,
                    return_dict_in_generate=True,
                    output_scores=True
                )
            
            # Decode correction
            corrected = self.tokenizer.decode(
                outputs.sequences[0], 
                skip_special_tokens=True
            )
            
            # Calculate confidence score
            confidence = self._calculate_confidence(value, corrected, outputs)
            
            return corrected, confidence
            
        except Exception as e:
            print(f"⚠️ T5 correction error: {e}")
            return value, 0.0
    
    def batch_correct(
        self, 
        corrections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Correct multiple values in batch for efficiency
        
        Args:
            corrections: List of dicts with 'value', 'context', 'row_data'
            
        Returns:
            List of dicts with 'value', 'context', 'suggested_value', 'confidence'
        """
        if self.model is None:
            return [
                {**c, 'suggested_value': c['value'], 'confidence': 0.0} 
                for c in corrections
            ]
        
        results = []
        
        # Process in batches of 8 for memory efficiency
        batch_size = 8
        for i in range(0, len(corrections), batch_size):
            batch = corrections[i:i+batch_size]
            
            # Prepare batch inputs
            input_texts = [
                f"correct: {c['value']} context: {c['context']}"
                for c in batch
            ]
            
            try:
                # Tokenize batch
                inputs = self.tokenizer(
                    input_texts,
                    return_tensors="pt",
                    max_length=128,
                    truncation=True,
                    padding=True
                ).to(self.device)
                
                # Generate corrections
                with torch.no_grad():
                    outputs = self.model.generate(
                        inputs.input_ids,
                        max_length=50,
                        num_beams=3,
                        early_stopping=True
                    )
                
                # Decode results
                for j, output in enumerate(outputs):
                    corrected = self.tokenizer.decode(output, skip_special_tokens=True)
                    confidence = self._calculate_confidence(
                        batch[j]['value'], 
                        corrected, 
                        None
                    )
                    
                    results.append({
                        **batch[j],
                        'suggested_value': corrected,
                        'confidence': confidence
                    })
                    
            except Exception as e:
                print(f"⚠️ Batch correction error: {e}")
                # Fallback for failed batch
                for c in batch:
                    results.append({
                        **c,
                        'suggested_value': c['value'],
                        'confidence': 0.0
                    })
        
        return results
    
    def _calculate_confidence(
        self, 
        original: str, 
        corrected: str, 
        outputs: Any
    ) -> float:
        """
        Calculate confidence score for correction
        
        Factors:
        - Model output probabilities (if available)
        - Similarity to original (high similarity = low confidence correction)
        - Validation checks (format, type)
        """
        # No correction made = low confidence
        if original == corrected:
            return 0.0
        
        # Use model scores if available
        if outputs and hasattr(outputs, 'sequences_scores'):
            try:
                # Convert log probability to confidence
                score = torch.exp(outputs.sequences_scores[0]).item()
                confidence = min(score, 0.95)  # Cap at 0.95
            except Exception:
                confidence = self.DEFAULT_CONFIDENCE
        else:
            confidence = self.DEFAULT_CONFIDENCE
        
        # Adjust based on correction quality
        if self._is_valid_correction(corrected):
            confidence = min(confidence + 0.05, 0.95)
        else:
            confidence = max(confidence - 0.1, self.MIN_CONFIDENCE)
        
        return round(confidence, 2)
    
    def _is_valid_correction(self, value: str) -> bool:
        """
        Verify the corrected value is valid
        
        Basic checks for common formats
        """
        import re
        
        if not value or value.strip() == "":
            return False
        
        # Email validation
        if "@" in value:
            email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
            return bool(re.match(email_pattern, value))
        
        # Phone validation (Morocco format)
        if value.startswith('+212') or value.startswith('0'):
            phone_pattern = r'^(\+212|0)[5-7]\d{8}$'
            return bool(re.match(phone_pattern, value.replace(' ', '').replace('-', '')))
        
        # Date validation (basic)
        if '/' in value or '-' in value:
            try:
                from datetime import datetime
                # Try common formats
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d']:
                    try:
                        datetime.strptime(value, fmt)
                        return True
                    except ValueError:
                        continue
            except Exception:
                pass
        
        # Default: assume valid if it's a reasonable string
        return len(value) > 0 and len(value) < 200
    
    def train(
        self, 
        training_data: List[Dict[str, str]], 
        output_dir: str = "./models/t5_corrector_finetuned",
        num_epochs: int = 3
    ) -> None:
        """
        Fine-tune T5 on correction examples
        
        Args:
            training_data: List of {'input': str, 'output': str} examples
            output_dir: Directory to save fine-tuned model
            num_epochs: Training epochs
            
        Example training_data:
        [
            {
                "input": "correct: 32/13/2024 context: date_naissance",
                "output": "31/12/2024"
            },
            ...
        ]
        """
        if self.model is None or self.tokenizer is None:
            print("⚠️ Cannot train: Model not loaded")
            return
        
        if len(training_data) < 50:
            print(f"⚠️ Insufficient training data: {len(training_data)} examples (minimum 50)")
            return
        
        try:
            from transformers import Trainer, TrainingArguments
            from torch.utils.data import Dataset
            
            # Prepare dataset
            class CorrectionDataset(Dataset):
                def __init__(self, data, tokenizer):
                    self.data = data
                    self.tokenizer = tokenizer
                
                def __len__(self):
                    return len(self.data)
                
                def __getitem__(self, idx):
                    item = self.data[idx]
                    inputs = self.tokenizer(
                        item['input'],
                        max_length=128,
                        truncation=True,
                        padding='max_length',
                        return_tensors='pt'
                    )
                    targets = self.tokenizer(
                        item['output'],
                        max_length=50,
                        truncation=True,
                        padding='max_length',
                        return_tensors='pt'
                    )
                    return {
                        'input_ids': inputs.input_ids.squeeze(),
                        'attention_mask': inputs.attention_mask.squeeze(),
                        'labels': targets.input_ids.squeeze()
                    }
            
            dataset = CorrectionDataset(training_data, self.tokenizer)
            
            # Training configuration
            training_args = TrainingArguments(
                output_dir=output_dir,
                num_train_epochs=num_epochs,
                per_device_train_batch_size=8,
                save_steps=100,
                save_total_limit=2,
                logging_steps=50,
                learning_rate=5e-5,
                weight_decay=0.01,
                warmup_steps=100,
            )
            
            # Train
            trainer = Trainer(
                model=self.model,
                args=training_args,
                train_dataset=dataset,
            )
            
            print(f"🚀 Starting fine-tuning on {len(training_data)} examples...")
            trainer.train()
            
            # Save fine-tuned model
            self.model.save_pretrained(output_dir)
            self.tokenizer.save_pretrained(output_dir)
            
            print(f"✅ Model fine-tuned and saved to {output_dir}")
            
        except Exception as e:
            print(f"❌ Training failed: {e}")
