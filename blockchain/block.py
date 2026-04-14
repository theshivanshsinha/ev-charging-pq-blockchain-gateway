import hashlib
import time
import json


class Block:
    def __init__(self, index, data, prev_hash):
        self.index     = index
        self.timestamp = time.time()
        self.data      = data
        self.prev_hash = prev_hash
        self.hash      = self.calculate_hash()

    def calculate_hash(self):
        # Use json.dumps with sort_keys for deterministic, canonical serialization
        # str(dict) is non-deterministic across Python versions
        block_content = {
            "index":     self.index,
            "timestamp": self.timestamp,
            "data":      self.data,
            "prev_hash": self.prev_hash,
        }
        block_string = json.dumps(block_content, sort_keys=True)
        return hashlib.sha3_256(block_string.encode()).hexdigest()