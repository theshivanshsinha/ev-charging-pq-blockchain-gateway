from blockchain.block import Block

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):
        return Block(0, "Genesis Block", "0")

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, data):
        prev_block = self.get_latest_block()
        new_block  = Block(len(self.chain), data, prev_block.hash)
        self.chain.append(new_block)

    def is_valid(self):
        """Verify chain integrity — each block's prev_hash must match the previous block's hash."""
        for i in range(1, len(self.chain)):
            curr = self.chain[i]
            prev = self.chain[i - 1]
            if curr.hash != curr.calculate_hash():
                return False
            if curr.prev_hash != prev.hash:
                return False
        return True

    def print_chain(self):
        print("\n--- BLOCKCHAIN ---")
        for block in self.chain:
            print(f"\nBlock {block.index}")
            print("Timestamp:", block.timestamp)
            print("Data:",      block.data)
            print("Prev Hash:", block.prev_hash)
            print("Hash:",      block.hash)