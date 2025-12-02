import json
from dataclasses import dataclass, field
import torch
from torch.utils.data import Dataset
import transformers
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    Trainer,
    TrainingArguments,
)
from peft import LoraConfig, get_peft_model


###############################################
# 1. Dataset for Gemma-IT SFT LoRA
###############################################

USER_START = "<start_of_turn>user\n"
USER_END = "<end_of_turn>\n"
MODEL_START = "<start_of_turn>model\n"
MODEL_END = "<end_of_turn>"

class TextSFTDataset(Dataset):
    def __init__(self, jsonl_path, tokenizer, max_len=2048):
        super().__init__()
        self.data = [json.loads(l) for l in open(jsonl_path)]
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]

        text = (
            USER_START + item["instruction"] + USER_END +
            MODEL_START + item["output"] + MODEL_END
        )

        enc = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_len,
            return_tensors="pt"
        )

        input_ids = enc.input_ids[0]
        labels = input_ids.clone()

        # mask user part
        user_text = USER_START + item["instruction"] + USER_END
        user_ids = self.tokenizer(user_text, add_special_tokens=False)["input_ids"]
        labels[:len(user_ids)] = -100

        return {
            "input_ids": input_ids,
            "attention_mask": enc.attention_mask[0],
            "labels": labels,
        }


###############################################
# 2. Custom arguments (no output_dir here!)
###############################################

@dataclass
class MyArguments:
    model_id: str = field(default="google/gemma-3-4b-it")
    train_file: str = field(default="sft_dataset/Python-22k/Python-22k/train.jsonl")
    max_len: int = field(default=2048)
    lora_rank: int = field(default=64)
    lora_alpha: int = field(default=16)
    lora_dropout: float = field(default=0.05)


###############################################
# 3. Main training function
###############################################

def main():
    # parse both dataclasses
    parser = transformers.HfArgumentParser((MyArguments, TrainingArguments))
    model_args, training_args = parser.parse_args_into_dataclasses()

    print("Loading tokenizer & model...")
    tokenizer = AutoTokenizer.from_pretrained(model_args.model_id, use_fast=False)
    model = AutoModelForCausalLM.from_pretrained(
        model_args.model_id,
        torch_dtype=torch.float16,
        device_map="auto"
    )

    model.gradient_checkpointing_enable()
    model.config.use_cache = False
    
    # LoRA config
    target_modules = [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"
    ]

    peft_config = LoraConfig(
        r=model_args.lora_rank,
        lora_alpha=model_args.lora_alpha,
        lora_dropout=model_args.lora_dropout,
        target_modules=target_modules,
        bias="none",
        task_type="CAUSAL_LM"
    )

    print("Applying LoRA...")
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    # load dataset
    print("Loading dataset...")
    train_dataset = TextSFTDataset(
        model_args.train_file,
        tokenizer,
        max_len=model_args.max_len
    )

    print("Starting Trainer...")
    trainer = Trainer(
        model=model,
        train_dataset=train_dataset,
        args=training_args,
        tokenizer=tokenizer,
    )

    trainer.train()
    trainer.save_model(training_args.output_dir)
    print("Done!")


if __name__ == "__main__":
    main()
