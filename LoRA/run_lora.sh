#!/bin/bash

export CUDA_VISIBLE_DEVICES=0

python3 train_lora.py \
  --model_id "google/gemma-3-4b-it" \
  --train_file "sft_dataset/Python-22k/Python-22k/train.jsonl" \
  --output_dir "gemma4b-lora-output" \
  --num_train_epochs 2 \
  --per_device_train_batch_size 1 \
  --gradient_accumulation_steps 8 \
  --learning_rate 1e-4 \
  --bf16 True \
  --gradient_checkpointing True \
  --logging_steps 20 \
  --save_steps 1000 \
  --report_to none

sudo shutdown now