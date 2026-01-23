import sys
import os

# Ensure backend can be imported
sys.path.append(os.getcwd())

from main import engine

print("Testing engine.analyze with ['string']...")
try:
    detections = engine.analyze(
        text="Mon CIN est AB123456",
        language="fr",
        entities=["string"],
        score_threshold=0.3
    )
    print("Success:", detections)
except Exception as e:
    print("Caught exception:")
    import traceback
    traceback.print_exc()
