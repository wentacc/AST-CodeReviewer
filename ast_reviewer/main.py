import argparse
import sys
from ast_reviewer.pipeline.reviewer import ReviewPipeline

def main():
    parser = argparse.ArgumentParser(description="AST-Reviewer: Structure-Aware Code Reviewer")
    parser.add_argument("file", help="Path to the file to review")
    args = parser.parse_args()

    print(f"Reviewing {args.file}...")
    
    reviewer = ReviewPipeline()
    report = reviewer.review_file(args.file)
    
    print("\n" + report)

if __name__ == "__main__":
    main()
