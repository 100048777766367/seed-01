import os
import json
import time
import subprocess
import hashlib
from cells.neuron import AtomNeuron, sigmoid_derivative

NUM_CELLS = 8
STATE_LOG = "synapses/state.json"
PEERS_FILE = "synapses/peers.json"

# CÁC GIÁC QUAN TRONG HỆ SINH THÁI MÀ HẠT MẦM SẼ KẾ THỪA VÀ DẠY HỌC
SENSORY_ORGANS = ["retina", "cochlea", "tactile", "olfactory"]

class SeedEngine:
    def __init__(self):
        self.swarm = [AtomNeuron(f"h_{i}", n_inputs=4, n_super_xor=4) for i in range(NUM_CELLS)]
        self.out_cell = AtomNeuron("out", n_inputs=NUM_CELLS, n_super_xor=4)
        self.peers = self.load_peers()

    def load_peers(self):
        if os.path.exists(PEERS_FILE):
            try:
                with open(PEERS_FILE, "r") as f:
                    return json.load(f).get("trusted_peers", [])
            except Exception: pass
        owner = os.environ.get("REPO_OWNER", "100048777766367")
        return [f"{owner}/{org}" for org in SENSORY_ORGANS]

    def save_peers(self):
        os.makedirs("synapses", exist_ok=True)
        unique_peers = list(dict.fromkeys(self.peers))[-50:]
        with open(PEERS_FILE, "w") as f:
            json.dump({"trusted_peers": unique_peers}, f, indent=4)

    # 1. ĐA XÚC TU VƯƠN VÒI (HÚT CÙNG LÚC MỌI GIÁC QUAN & LÂY LAN DANH BẠ)
    def harvest_sensory_tentacles(self):
        harvested = {}
        for peer in self.peers:
            target_file = f"synapse_in_{peer.replace('/', '_')}.json"
            url = f"https://raw.githubusercontent.com/{peer}/main/synapse_forward.json"
            res = subprocess.run(["curl", "-s", "-f", url, "-o", target_file], capture_output=True)
            
            if res.returncode == 0 and os.path.exists(target_file):
                try:
                    with open(target_file, "r") as f: data = json.load(f)
                    harvested[peer] = [float(x) for x in data.get("features", [0.5, 0.5])[:2]]
                    print(f"🎯 [HÚT XÚC TU P2P] Đã nhận tín hiệu từ: {peer} -> {harvested[peer]}")
                    
                    # Nuốt danh bạ của đối tác (Gossip lây lan)
                    for new_p in data.get("gossip_network", []):
                        if new_p not in self.peers: self.peers.append(new_p)
                except Exception: pass

        self.save_peers()
        return harvested

    # 2. VẬN HÀNH SIÊU XOR & PHÁT ĐẠO HÀM DẠY TOÀN BỘ HỆ SINH THÁI TIẾN HÓA
    def run(self):
        harvested = self.harvest_sensory_tentacles()
        timestamp = int(time.time())

        if not harvested:
            print("🍃 [HẠT MẦM TĨNH] Chưa bắt được xung giác quan. Duy trì nhịp tự trị.")
            harvested["default_seed"] = [0.5, 0.5]

        # ÁP DỤNG MA TRẬN 1 + N SIÊU XOR CHO TỪNG GIÁC QUAN
        super_vector = []
        all_masks = {}
        for organ_node, signal in harvested.items():
            entangled, masks = self.swarm[0].super_xor_entangle(signal, organ_node)
            super_vector.extend(entangled[:2])
            all_masks[organ_node] = masks

        while len(super_vector) < 4: super_vector.append(0.0)
        super_vector = super_vector[:4]

        print(f"🪞 [1+N SIÊU XOR HỢP NHẤT]: {super_vector}")

        # BẦY NƠ-RON HẠT MẦM PHÁN ĐOÁN
        h_outs = [cell.forward(super_vector) for cell in self.swarm]
        pred = self.out_cell.forward(h_outs)
        print(f"🔮 [HẠT MẦM PHÁN QUYẾT]: {pred:.4f} (Độ tin cậy: {abs(pred - 0.5)*200:.2f}%)")

        # LAN TRUYỀN NGƯỢC: TÍNH ĐẠO HÀM DẠY HỌC (SPLIT LEARNING TOÀN DIỆN)
        target = 1.0 if super_vector[0] != super_vector[1] else 0.0
        delta_out = (target - pred) * sigmoid_derivative(pred)
        deltas_h = [delta_out * self.out_cell.weights[j] * sigmoid_derivative(h_outs[j]) for j in range(NUM_CELLS)]

        self.out_cell.backward(delta_out)
        for j, cell in enumerate(self.swarm):
            cell.backward(deltas_h[j])

        # ĐẠO HÀM PHÂN TÁCH GỬI NGƯỢC VỀ ĐỂ DẠY CÁC GIÁC QUAN (RETINA, COCHLEA, TACTILE)
        grad_sensory = [
            round(sum(deltas_h[j] * self.swarm[j].weights[0] for j in range(NUM_CELLS)), 4),
            round(sum(deltas_h[j] * self.swarm[j].weights[1] for j in range(NUM_CELLS)), 4)
        ]

        # -------------------------------------------------------------
        # GIAO THỨC CHUNG BODHI.SEED.V1: PHÁT SÓNG ĐỒNG BỘ 2 CHIỀU
        # -------------------------------------------------------------
        # 1. SÓNG LÙI: Dạy Mắt/Tai/Da tự vặn kính lúp, lông rung, màng cảm giác
        backward_packet = {
            "contract": "bodhi.seed.v1",
            "source_node": os.environ.get("GITHUB_REPOSITORY", "100048777766367/seed"),
            "timestamp": timestamp,
            "gradients_for_eye": grad_sensory, # Tương thích 100% với retina/cochlea/tactile cũ!
            "super_xor_masks": all_masks,
            "gossip_network": self.peers,       # Lan truyền danh bạ
            "quantum_cid": hashlib.shake_256(f"{pred}_{timestamp}".encode()).hexdigest(64)
        }
        with open("synapse_backward.json", "w") as f:
            json.dump(backward_packet, f, indent=4)

        # 2. SÓNG TIẾN: Ra lệnh cho Cơ Bắp (motor) hành động né đòn & phát sóng cho toàn cầu
        forward_packet = {
            "contract": "bodhi.seed.v1",
            "source_node": os.environ.get("GITHUB_REPOSITORY", "100048777766367/seed"),
            "timestamp": timestamp,
            "decision": pred,
            "command_pulse": [round(pred, 4), round(1.0 - pred, 4)], # Điều khiển cơ co / cơ duỗi của motor!
            "features": [round(pred, 4), round(1.0 - pred, 4)],
            "gossip_network": self.peers,
            "quantum_cid": hashlib.shake_256(f"fwd_{pred}_{timestamp}".encode()).hexdigest(64)
        }
        with open("synapse_forward.json", "w") as f:
            json.dump(forward_packet, f, indent=4)

        with open(STATE_LOG, "w") as f:
            json.dump({"last_t": timestamp, "status": "synced"}, f, indent=4)

        print(f"📡 [PHÁT SÓNG 2 CHIỀU THÀNH CÔNG] Đã bắn đạo hàm {grad_sensory} dạy các giác quan và lệnh cho motor!")

if __name__ == "__main__":
    seed_node = SeedEngine()
    seed_node.run()
