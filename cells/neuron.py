import math
import random
import json
import os
import hashlib

def sigmoid(x):
    return 1.0 / (1.0 + math.exp(-max(min(x, 500), -500)))

def sigmoid_derivative(y):
    return y * (1.0 - y)

class AtomNeuron:
    def __init__(self, neuron_id, n_inputs=4, n_super_xor=4, storage_dir="synapses"):
        self.id = neuron_id
        self.n_in = n_inputs
        self.n_xor = n_super_xor # Số chiều thực tại Siêu XOR (1 + N)
        self.storage_path = os.path.join(storage_dir, f"{self.id}.json")
        self.os_dir = storage_dir
        
        self.weights = []
        self.bias = 0.0
        self.last_inputs = []
        self.last_out = 0.0
        
        self.load_self()

    # TỰ CHỮA LÀNH (SELF-HEALING)
    def load_self(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                if len(data.get("w", [])) == self.n_in:
                    self.weights = data["w"]
                    self.bias = data.get("b", 0.0)
                    return
            except Exception: pass

        self.weights = [random.uniform(-1.0, 1.0) for _ in range(self.n_in)]
        self.bias = random.uniform(-0.5, 0.5)
        self.save_self()

    # ==============================================================
    # MA TRẬN 1 + N SIÊU XOR: KHÚC XẠ THỰC TẠI CHO TỪNG GIÁC QUAN
    # ==============================================================
    def super_xor_entangle(self, stimulus_vector, organ_id):
        masks = []
        for d in range(self.n_xor):
            seed = f"{self.id}_{organ_id}_dim_{d}".encode()
            # Dùng SHAKE-256 tạo mặt nạ lượng tử trực giao
            val = int(hashlib.shake_256(seed).hexdigest(4), 16) / 65535.0
            masks.append(round(val, 4))

        entangled = list(stimulus_vector)
        for i in range(len(entangled)):
            for m in masks:
                entangled[i] = round((entangled[i] + m) % 1.0, 4)
        return entangled, masks

    # LAN TRUYỀN TIẾN: Kháng độc tố đầu vào
    def forward(self, inputs):
        self.last_inputs = [max(-10.0, min(10.0, float(x))) for x in inputs[:self.n_in]]
        while len(self.last_inputs) < self.n_in:
            self.last_inputs.append(0.0)

        tong = sum(self.last_inputs[i] * self.weights[i] for i in range(self.n_in)) + self.bias
        self.last_out = sigmoid(tong)
        return self.last_out

    # LAN TRUYỀN NGƯỢC: Tự tiến hóa trọng số
    def backward(self, delta, lr=0.1):
        safe_delta = max(-5.0, min(5.0, delta))
        for i in range(self.n_in):
            self.weights[i] += lr * safe_delta * self.last_inputs[i]
        self.bias += lr * safe_delta
        self.save_self()

    def save_self(self):
        os.makedirs(self.os_dir, exist_ok=True)
        with open(self.storage_path, "w") as f:
            json.dump({"w": [round(w, 4) for w in self.weights], "b": round(self.bias, 4)}, f, indent=4)
