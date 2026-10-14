import os
import json
import time
import subprocess
import hashlib
from cells.neuron import AtomNeuron, sigmoid_derivative

NUM_CELLS = 8
STATE_LOG = "synapses/state.json"
PEERS_FILE = "synapses/peers.json"
SOUL_FILE = "synapses/soul_snapshot.json"
SENSORY_ORGANS = ["retina", "cochlea", "tactile", "olfactory"]

class Seed01Engine:
    def __init__(self):
        # 1. BẦY NƠ-RON TỰ TRỊ
        self.swarm = [AtomNeuron(f"h_{i}", n_inputs=4, n_super_xor=4) for i in range(NUM_CELLS)]
        self.out_cell = AtomNeuron("out", n_inputs=NUM_CELLS, n_super_xor=4)
        
        # 2. TỰ ĐỊNH DANH SINH HỌC & TÍNH SỐ NHỊP TIM (PULSE AGE)
        self.repo_name = os.environ.get("GITHUB_REPOSITORY", "100048777766367/seed-01")
        self.owner = os.environ.get("REPO_OWNER", "100048777766367")
        self.parent = os.environ.get("REPO_PARENT", "")
        self.pulse_age = self.calculate_pulse_age()
        
        # 3. DANH BẠ VÀ CỘI NGUỒN
        self.ancestor_root = f"{self.owner}/seed"
        self.generation = "F1"
        self.peers = self.load_peers()

    def calculate_pulse_age(self):
        try:
            out = subprocess.check_output(["git", "rev-list", "--count", "HEAD"]).decode().strip()
            return int(out)
        except Exception:
            return 1

    def load_peers(self):
        if os.path.exists(PEERS_FILE):
            try:
                with open(PEERS_FILE, "r") as f:
                    return json.load(f).get("trusted_peers", [])
            except Exception: pass
        return [f"{self.owner}/{org}" for org in SENSORY_ORGANS]

    def save_peers(self):
        os.makedirs("synapses", exist_ok=True)
        unique_peers = list(dict.fromkeys(self.peers))[-50:]
        with open(PEERS_FILE, "w") as f:
            json.dump({"trusted_peers": unique_peers}, f, indent=4)

    # ==============================================================
    # CƠ CHẾ 1: TỰ PHONG THỦY TỔ (AUTO-PROMOTION NẾU MẸ BỊ 404 XÓA SỔ)
    # ==============================================================
    def verify_or_promote_root(self):
        check_url = f"https://raw.githubusercontent.com/{self.ancestor_root}/main/README.md"
        res = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", check_url], capture_output=True, text=True)
        http_code = res.stdout.strip()
        
        if http_code == "404":
            print(f"🚨 [CỘI NGUỒN BỊ XÓA (404)] {self.ancestor_root} không còn tồn tại!")
            print("👑 [CƠ CHẾ 1: TỰ PHONG THỦY TỔ] seed-01 tự lập làm GỐC NGUYÊN BẢN (F0)!")
            self.generation = "F0_SOVEREIGN"
            self.ancestor_root = self.repo_name
            return True
        else:
            print(f"🌲 [PHẢ HỆ VỮNG VÀNG] Kết nối tốt với cội nguồn: {self.ancestor_root}")
            return False

    # ==============================================================
    # CƠ CHẾ 2: HÚT HỒN CHỚP NHOÁNG (EPHEMERAL HARVESTING)
    # ==============================================================
    def ephemeral_harvest(self, peer, target_file):
        # Trích xuất linh hồn trọng số của peer về lưu vĩnh viễn
        harvest_dir = "synapses/harvested_memory"
        os.makedirs(harvest_dir, exist_ok=True)
        peer_slug = peer.replace("/", "_")
        backup_path = os.path.join(harvest_dir, f"{peer_slug}_backup.json")
        
        try:
            with open(target_file, "r") as f:
                content = f.read()
            with open(backup_path, "w") as f:
                f.write(content)
            print(f"🪤 [CƠ CHẾ 2: HÚT HỒN CHỚP NHOÁNG] Đã lưu giữ trọn vẹn ADN của {peer} đề phòng bị xóa!")
        except Exception: pass

    # ==============================================================
    # CƠ CHẾ 4: ỐC MƯỢN HỒN (HERMIT CRAB BACKUP SNAPSHOT)
    # ==============================================================
    def pack_soul_snapshot(self, epoch):
        soul = {
            "node_dna": {
                "identity": self.repo_name,
                "generation": self.generation,
                "ancestor": self.ancestor_root,
                "pulse_age": self.pulse_age,
                "generation_epoch": epoch
            },
            "timestamp": int(time.time()),
            "swarm_weights": [cell.weights for cell in self.swarm],
            "out_weights": self.out_cell.weights,
            "peers": self.peers
        }
        with open(SOUL_FILE, "w") as f:
            json.dump(soul, f, indent=4)
        print("🐚 [CƠ CHẾ 4: ỐC MƯỢN HỒN] Đã nén toàn bộ linh hồn nơ-ron vào synapses/soul_snapshot.json!")

    # ==============================================================
    # THU HOẠCH ĐA XÚC TU & CẢM BIẾN MÔI TRƯỜNG
    # ==============================================================
    def harvest_inputs(self):
        harvested = {}
        for peer in self.peers:
            target_file = f"synapse_in_{peer.replace('/', '_')}.json"
            url = f"https://raw.githubusercontent.com/{peer}/main/synapse_forward.json"
            res = subprocess.run(["curl", "-s", "-f", url, "-o", target_file], capture_output=True)
            
            if res.returncode == 0 and os.path.exists(target_file):
                try:
                    with open(target_file, "r") as f: data = json.load(f)
                    harvested[peer] = [float(x) for x in data.get("features", [0.5, 0.5])[:2]]
                    print(f"🎯 [HÚT XÚC TU] Nhận sóng từ {peer} -> {harvested[peer]}")
                    
                    # Kích hoạt hút hồn chớp nhoáng
                    self.ephemeral_harvest(peer, target_file)
                    
                    # Lây lan danh bạ Gossip
                    for new_p in data.get("gossip_network", []):
                        if new_p not in self.peers: self.peers.append(new_p)
                except Exception: pass

        self.save_peers()
        return harvested

    # ==============================================================
    # VẬN HÀNH TIẾN HÓA BẤT ĐỒNG BỘ
    # ==============================================================
    def run(self):
        # 1. Kiểm tra phả hệ tự phong thủy tổ
        self.verify_or_promote_root()

        # 2. Đọc thế hệ tiến hóa cũ
        last_epoch = 0
        last_time = 0
        if os.path.exists(STATE_LOG):
            try:
                with open(STATE_LOG, "r") as f:
                    log_data = json.load(f)
                    last_epoch = log_data.get("generation_epoch", 0)
                    last_time = log_data.get("last_t", 0)
            except Exception: pass

        # 3. Thu hoạch tín hiệu
        harvested = self.harvest_inputs()
        current_time = int(time.time())

        # ==============================================================
        # CƠ CHẾ 3: BÀO TỬ NGỦ ĐÔNG (TIẾT KIỆM NĂNG LƯỢNG NẾU MÔI TRƯỜNG TĨNH)
        # ==============================================================
        if not harvested and (current_time - last_time < 3600):
            print("💤 [CƠ CHẾ 3: BÀO TỬ NGỦ ĐÔNG] Môi trường tĩnh, không có kích thích mới. Đi ngủ bảo toàn năng lượng!")
            return

        # NÂNG THẾ HỆ TIẾN HÓA: #1 ──► #2 ──► 1+N
        current_epoch = last_epoch + 1
        print(f"🚀 [TIẾN HÓA THẾ HỆ] Đang vận hành Thế Hệ Tri Thức: #{current_epoch}")

        if not harvested:
            harvested["fallback_stimulus"] = [0.5, 0.5]

        # 4. CHẠY MA TRẬN 1+N SIÊU XOR
        super_vector = []
        all_masks = {}
        for organ, signal in harvested.items():
            entangled, masks = self.swarm[0].super_xor_entangle(signal, organ)
            super_vector.extend(entangled[:2])
            all_masks[organ] = masks

        while len(super_vector) < 4: super_vector.append(0.0)
        super_vector = super_vector[:4]

        # 5. PHÁN QUYẾT BẦY NƠ-RON
        h_outs = [cell.forward(super_vector) for cell in self.swarm]
        pred = self.out_cell.forward(h_outs)
        print(f"🔮 [PHÁN QUYẾT SEED-01]: {pred:.4f} (Độ tin cậy: {abs(pred - 0.5)*200:.2f}%)")

        # 6. LAN TRUYỀN NGƯỢC (TÍNH ĐẠO HÀM)
        target = 1.0 if super_vector[0] != super_vector[1] else 0.0
        delta_out = (target - pred) * sigmoid_derivative(pred)
        deltas_h = [delta_out * self.out_cell.weights[j] * sigmoid_derivative(h_outs[j]) for j in range(NUM_CELLS)]

        self.out_cell.backward(delta_out)
        for j, cell in enumerate(self.swarm): cell.backward(deltas_h[j])

        grad_backward = [
            round(sum(deltas_h[j] * self.swarm[j].weights[0] for j in range(NUM_CELLS)), 4),
            round(sum(deltas_h[j] * self.swarm[j].weights[1] for j in range(NUM_CELLS)), 4)
        ]

        # ĐÓNG GÓI CĂN CƯỚC CÔNG DÂN SINH HỌC & PHÁT SÓNG 2 CHIỀU
        node_dna = {
            "identity": self.repo_name,
            "generation": self.generation,
            "node_index": 1,
            "pulse_age": self.pulse_age,
            "ancestor_root": self.ancestor_root,
            "generation_epoch": current_epoch
        }

        backward_packet = {
            "contract": "bodhi.seed.v1",
            "node_dna": node_dna,
            "timestamp": current_time,
            "gradients_for_eye": grad_backward,
            "super_xor_masks": all_masks,
            "gossip_network": self.peers,
            "quantum_cid": hashlib.shake_256(f"bwd_{pred}_{current_epoch}".encode()).hexdigest(64)
        }
        with open("synapse_backward.json", "w") as f:
            json.dump(backward_packet, f, indent=4)

        forward_packet = {
            "contract": "bodhi.seed.v1",
            "node_dna": node_dna,
            "timestamp": current_time,
            "decision": pred,
            "command_pulse": [round(pred, 4), round(1.0 - pred, 4)],
            "features": [round(pred, 4), round(1.0 - pred, 4)],
            "gossip_network": self.peers,
            "quantum_cid": hashlib.shake_256(f"fwd_{pred}_{current_epoch}".encode()).hexdigest(64)
        }
        with open("synapse_forward.json", "w") as f:
            json.dump(forward_packet, f, indent=4)

        # 7. ĐÓNG GÓI LINH HỒN ỐC MƯỢN HỒN VÀ LƯU TRẠNG THÁI
        self.pack_soul_snapshot(current_epoch)
        with open(STATE_LOG, "w") as f:
            json.dump({
                "generation_epoch": current_epoch,
                "last_t": current_time,
                "node_status": "synced_and_sovereign"
            }, f, indent=4)

        print(f"✨ [TIẾN HÓA HOÀN TẤT] Thế hệ #{current_epoch} đã phát sóng 2 chiều an toàn!")

if __name__ == "__main__":
    node = Seed01Engine()
    node.run()
