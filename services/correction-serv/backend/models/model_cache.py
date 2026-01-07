"""
ML Model Cache & Optimization Module
=====================================

Reduces latency for AI/ML models through:
- Lazy loading
- In-memory caching
- Connection pooling
- Async operations
- Batch processing
"""

import asyncio
from typing import Optional, Dict, Any, List
from functools import lru_cache
import time


class ModelCache:
    """
    Singleton cache for ML models
    
    Reduces latency by:
    - Loading models only once
    - Caching predictions for identical inputs  
    - Batching requests
    - Async prediction queue
    """
    
    _instance = None
    _t5_model = None
    _prediction_cache: Dict[str, tuple] = {}
    _cache_hits = 0
    _cache_misses = 0
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_t5_model(cls):
        """Get cached T5 model (lazy load)"""
        if cls._t5_model is None:
            from backend.models.ml.text_correction_t5 import TextCorrectionT5
            print("🔄 Loading T5 model (first time only)...")
            start = time.time()
            cls._t5_model = TextCorrectionT5(model_name="t5-small")
            elapsed = time.time() - start
            print(f"✅ T5 model loaded in {elapsed:.2f}s")
        return cls._t5_model
    
    @classmethod
    @lru_cache(maxsize=1000)
    def get_cached_correction(cls, value: str, context: str) -> Optional[tuple]:
        """
        Get cached correction prediction
        
        Args:
            value: Value to correct
            context: Field context
            
        Returns:
            (corrected_value, confidence) or None if not cached
        """
        cache_key = f"{value}::{context}"
        
        if cache_key in cls._prediction_cache:
            cls._cache_hits += 1
            return cls._prediction_cache[cache_key]
        
        cls._cache_misses += 1
        return None
    
    @classmethod
    def cache_correction(cls, value: str, context: str, corrected: str, confidence: float):
        """Cache a correction prediction"""
        cache_key = f"{value}::{context}"
        cls._prediction_cache[cache_key] = (corrected, confidence)
        
        # Limit cache size
        if len(cls._prediction_cache) > 10000:
            # Remove oldest 20%
            items = list(cls._prediction_cache.items())
            cls._prediction_cache = dict(items[2000:])
    
    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """Get cache statistics"""
        total = cls._cache_hits + cls._cache_misses
        hit_rate = cls._cache_hits / total if total > 0 else 0
        
        return {
            "cache_hits": cls._cache_hits,
            "cache_misses": cls._cache_misses,
            "hit_rate": round(hit_rate, 3),
            "cached_items": len(cls._prediction_cache),
            "model_loaded": cls._t5_model is not None
        }
    
    @classmethod
    def clear_cache(cls):
        """Clear prediction cache"""
        cls._prediction_cache.clear()
        cls._cache_hits = 0
        cls._cache_misses = 0


class BatchProcessor:
    """
    Batch processor for ML predictions
    
    Reduces latency by batching multiple requests together
    """
    
    def __init__(self, batch_size: int = 8, wait_time: float = 0.1):
        self.batch_size = batch_size
        self.wait_time = wait_time
        self.queue: List[Dict[str, Any]] = []
        self.lock = asyncio.Lock()
    
    async def add_to_batch(self, value: str, context: str) -> tuple:
        """
        Add correction request to batch
        
        Waits for batch to fill or timeout, then processes
        """
        async with self.lock:
            # Check cache first
            cached = ModelCache.get_cached_correction(value, context)
            if cached:
                return cached
            
            # Add to batch
            future = asyncio.Future()
            self.queue.append({
                "value": value,
                "context": context,
                "future": future
            })
            
            # Process if batch is full
            if len(self.queue) >= self.batch_size:
                await self._process_batch()
        
        # Wait for result
        return await future
    
    async def _process_batch(self):
        """Process current batch"""
        if not self.queue:
            return
        
        # Get T5 model
        t5 = ModelCache.get_t5_model()
        
        # Prepare batch
        batch_items = self.queue[: self.batch_size]
        self.queue = self.queue[self.batch_size:]
        
        # Batch correct
        corrections = t5.batch_correct([
            {"value": item["value"], "context": item["context"]}
            for item in batch_items
        ])
        
        # Resolve futures and cache results
        for item, corr in zip(batch_items, corrections):
            result = (corr["suggested_value"], corr["confidence"])
            item["future"].set_result(result)
            
            # Cache for future requests
            ModelCache.cache_correction(
                item["value"],
                item["context"],
                corr["suggested_value"],
                corr["confidence"]
            )


class AsyncConnectionPool:
    """
    Async connection pool for database
    
    Reduces latency through connection reuse
    """
    
    _pool = None
    _pool_size = 10
    
    @classmethod
    async def get_connection(cls):
        """Get connection from pool"""
        if cls._pool is None:
            from backend.database.mongodb import db
            cls._pool = db
        return cls._pool


# Global batch processor
_batch_processor = None

def get_batch_processor() -> BatchProcessor:
    """Get global batch processor"""
    global _batch_processor
    if _batch_processor is None:
        _batch_processor = BatchProcessor(batch_size=8, wait_time=0.1)
    return _batch_processor
