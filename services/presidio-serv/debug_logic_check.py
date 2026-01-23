import sys
import os

# Ensure backend can be imported
sys.path.append(os.getcwd())

from main import engine

print("Testing filtering logic...")

entities_input = ["string"]
supported = engine.get_supported_entities()
valid_entities = [e for e in entities_input if e in supported]

print(f"Supported count: {len(supported)}")
print(f"Input: {entities_input}")
print(f"Valid: {valid_entities}")

if not valid_entities:
    final_entities = None
    print("Fallback to None (ALL)")
else:
    final_entities = valid_entities

print(f"Final entities passed to analyze: {final_entities}")

print("Running analyze...")
try:
    detections = engine.analyze(
        text="Mon CIN est AB123456",
        language="fr",
        entities=final_entities,
        score_threshold=0.3
    )
    print("Success:", len(detections), "detections")
except Exception as e:
    print("Caught exception:")
    import traceback
    traceback.print_exc()
