import sys
import os

# Ensure backend can be imported
sys.path.append(os.getcwd())

from main import engine

print("Testing anonymize logic...")

operators_input = {
    "CIN_MAROC": {
      "type": "replace",
      "new_value": "<IDENTITÉ_MASQUÉE>"
    },
    "PHONE_MA": {
      "type": "mask",
      "masking_char": "*",
      "chars_to_mask": 4,
      "from_end": True
    }
}

text_input = "Le dossier de AB123456 est validé. Appelez le 0661998877."

try:
    print("Running engine.anonymize...")
    result = engine.anonymize(
        text=text_input,
        language="fr",
        operators=operators_input
    )
    print("Success!")
    print(result)
except Exception as e:
    print("Caught exception:")
    import traceback
    traceback.print_exc()
