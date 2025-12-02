import os
import json
from pathlib import Path

# ===== 修改这两项 =====
ORIGIN_ROOT = "origin_dataset"
TARGET_ROOT = "sft_dataset"
SUBFOLDER = "Python-22k/Python-22k"
INPUT_FILE = "train.json"
# =====================

# 构造输入输出路径
input_path = os.path.join(ORIGIN_ROOT, SUBFOLDER, INPUT_FILE)

# 输出文件夹：保持原有目录结构
output_folder = os.path.join(TARGET_ROOT, SUBFOLDER)
os.makedirs(output_folder, exist_ok=True)

output_path = os.path.join(output_folder, "train.jsonl")

print(f"Loading {input_path}")

# 读取原始 JSON
with open(input_path, "r") as f:
    data = json.load(f)

print(f"Loaded {len(data)} samples.")

# 创建 JSONL 输出
with open(output_path, "w") as fout:
    for item in data:
        # Kaggle 格式字段
        old_comment = item.get("old_comment_raw", "")
        new_comment = item.get("new_comment_raw", "")
        old_code = item.get("old_code_raw", "")
        
        # 构造指令
        instruction = (
            "Here is a code snippet and its original comment.\n\n"
            f"[Original comment]:\n{old_comment}\n\n"
            f"[Code]:\n{old_code}\n\n"
            "Improve the comment to make it clearer, more accurate, and more informative."
        )

        # 构造输出
        output = new_comment

        fout.write(
            json.dumps(
                {
                    "instruction": instruction,
                    "output": output
                },
                ensure_ascii=False
            ) + "\n"
        )

print(f"Saved processed SFT data → {output_path}")
