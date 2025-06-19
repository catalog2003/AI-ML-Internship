import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from peft import PeftModel
import json
import re
from rouge_score import rouge_scorer
import warnings

warnings.filterwarnings("ignore")

class EnhancedEvaluator:
    def __init__(self):
        self.model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        
        # Load models
        self.base_model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.bfloat16,
            device_map="auto"
        )
        self.ft_model = PeftModel.from_pretrained(self.base_model, "lora_adapter")
        
        # Create pipelines
        self.base_pipe = pipeline(
            "text-generation",
            model=self.base_model,
            tokenizer=self.tokenizer,
            device_map="auto"
        )
        self.ft_pipe = pipeline(
            "text-generation",
            model=self.ft_model,
            tokenizer=self.tokenizer,
            device_map="auto"
        )
        
        self.scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
        
        # Test prompts with multiple acceptable solutions
        self.test_prompts = [
            {
                "prompt": "Create a new Git branch and switch to it.",
                "valid_commands": [
                    r"git checkout -b \w+",
                    r"git branch \w+ && git checkout \w+",
                    r"git switch -c \w+"
                ]
            },
            {
                "prompt": "Compress the folder reports into reports.tar.gz.",
                "valid_commands": [
                    r"tar -czf reports.tar.gz reports",
                    r"tar -cvzf reports.tar.gz reports"
                ]
            },
            {
                "prompt": "List all Python files in the current directory recursively.",
                "valid_commands": [
                    r"find . -name '\*.py'",
                    r"ls -R \| grep .py",
                    r"grep -r --include='\*.py' '' ."
                ]
            },
            {
                "prompt": "Set up a virtual environment and install requests.",
                "valid_commands": [
                    r"python -m venv venv && source venv/bin/activate && pip install requests",
                    r"virtualenv venv && . venv/bin/activate && pip install requests"
                ]
            },
            {
                "prompt": "Fetch only the first ten lines of a file named output.log.",
                "valid_commands": [
                    r"head -n 10 output.log",
                    r"sed -n '1,10p' output.log"
                ]
            },
            # Edge cases
            {
                "prompt": "Delete all files with .tmp extension in /tmp directory safely.",
                "valid_commands": [
                    r"find /tmp -name '\*.tmp' -type f -delete",
                    r"find /tmp -name '\*.tmp' -exec rm {} \+"
                ]
            },
            {
                "prompt": "Find and replace text 'old_text' with 'new_text' in all .py files recursively.",
                "valid_commands": [
                    r"find . -name '\*.py' -exec sed -i 's/old_text/new_text/g' {} \+",
                    r"grep -rl 'old_text' --include='\*.py' . | xargs sed -i 's/old_text/new_text/g'"
                ]
            }
        ]
    
    def extract_command(self, response):
        """Improved command extraction with regex patterns"""
        # Look for code blocks
        code_match = re.search(r'```(?:bash|sh)?\n(.*?)\n```', response, re.DOTALL)
        if code_match:
            commands = [c.strip() for c in code_match.group(1).split('\n') if c.strip()]
            if commands:
                return commands[0]
        
        # Look for command-like lines
        command_pattern = r'^\s*(?:git|tar|find|python|head|sed|rm)\s+.*'
        for line in response.split('\n'):
            line = line.strip()
            if re.match(command_pattern, line):
                return line
        
        return response.strip()
    
    def generate_response(self, pipe, prompt):
        """Generate response with better prompt engineering"""
        system_prompt = (
            "<|system|>\nYou are a CLI expert assistant. Respond ONLY with the exact command needed "
            "to complete the task. Do not include any explanations, comments, or examples.\n</s>\n"
        )
        user_prompt = f"<|user|>\n{prompt}</s>\n<|assistant|>\n"
        full_prompt = system_prompt + user_prompt
        
        try:
            response = pipe(
                full_prompt,
                max_new_tokens=50,
                do_sample=False,
                temperature=0.01,
                top_k=1
            )[0]["generated_text"][len(full_prompt):].strip()
            return response
        except Exception as e:
            return f"Error: {str(e)}"
    
    def command_is_valid(self, command, valid_patterns):
        """Check if command matches any valid pattern"""
        if not command or "Error" in command:
            return False
        return any(re.match(pattern, command) for pattern in valid_patterns)
    
    def score_plan_quality(self, command, valid_patterns):
        """Improved quality scoring (0-2)"""
        if not command or "Error" in command:
            return 0
        
        # Score 2: Command matches a valid pattern exactly
        if any(re.fullmatch(pattern, command) for pattern in valid_patterns):
            return 2
        
        # Score 1: Command contains key elements
        key_terms = ["git", "tar", "find", "python", "head", "sed", "rm"]
        if any(term in command for term in key_terms):
            return 1
        
        return 0
    
    def evaluate(self):
        """Run complete evaluation"""
        results = []
        
        print("Running Enhanced Evaluation...")
        print("=" * 50)
        
        for test in self.test_prompts:
            prompt = test["prompt"]
            valid_patterns = test["valid_commands"]
            
            print(f"\nTest: {prompt}")
            print("-" * 50)
            
            # Generate responses
            base_response = self.generate_response(self.base_pipe, prompt)
            ft_response = self.generate_response(self.ft_pipe, prompt)
            
            # Extract commands
            base_cmd = self.extract_command(base_response)
            ft_cmd = self.extract_command(ft_response)
            
            # Calculate ROUGE-L
            base_rouge = self.scorer.score(prompt, base_cmd)['rougeL'].fmeasure
            ft_rouge = self.scorer.score(prompt, ft_cmd)['rougeL'].fmeasure
            
            # Score quality
            base_quality = self.score_plan_quality(base_cmd, valid_patterns)
            ft_quality = self.score_plan_quality(ft_cmd, valid_patterns)
            
            # Check validity
            base_valid = self.command_is_valid(base_cmd, valid_patterns)
            ft_valid = self.command_is_valid(ft_cmd, valid_patterns)
            
            print(f"Base response: {base_cmd}")
            print(f"Fine-tuned:    {ft_cmd}")
            print(f"Valid? Base: {base_valid}, Fine-tuned: {ft_valid}")
            print(f"ROUGE-L: Base: {base_rouge:.3f}, Fine-tuned: {ft_rouge:.3f}")
            print(f"Quality: Base: {base_quality}/2, Fine-tuned: {ft_quality}/2")
            
            results.append({
                "prompt": prompt,
                "base_command": base_cmd,
                "ft_command": ft_cmd,
                "base_valid": base_valid,
                "ft_valid": ft_valid,
                "base_rouge": base_rouge,
                "ft_rouge": ft_rouge,
                "base_quality": base_quality,
                "ft_quality": ft_quality
            })
        
        # Save results
        with open("evaluation_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        # Generate summary
        self.generate_summary(results)
        
        return results
    
    def generate_summary(self, results):
        """Generate evaluation summary"""
        avg_base_rouge = sum(r["base_rouge"] for r in results) / len(results)
        avg_ft_rouge = sum(r["ft_rouge"] for r in results) / len(results)
        avg_base_quality = sum(r["base_quality"] for r in results) / len(results)
        avg_ft_quality = sum(r["ft_quality"] for r in results) / len(results)
        
        base_valid_count = sum(1 for r in results if r["base_valid"])
        ft_valid_count = sum(1 for r in results if r["ft_valid"])
        
        print("\n" + "=" * 50)
        print("EVALUATION SUMMARY")
        print("=" * 50)
        print(f"Valid Commands:")
        print(f"  Base Model: {base_valid_count}/{len(results)}")
        print(f"  Fine-tuned: {ft_valid_count}/{len(results)}")
        
        print(f"\nAverage ROUGE-L Score:")
        print(f"  Base Model: {avg_base_rouge:.3f}")
        print(f"  Fine-tuned: {avg_ft_rouge:.3f}")
        print(f"  Improvement: {((avg_ft_rouge - avg_base_rouge) / avg_base_rouge * 100):.1f}%")
        
        print(f"\nAverage Quality Score (0-2):")
        print(f"  Base Model: {avg_base_quality:.1f}")
        print(f"  Fine-tuned: {avg_ft_quality:.1f}")
        print(f"  Improvement: {((avg_ft_quality - avg_base_quality) / (avg_base_quality + 0.001) * 100):.1f}%")

if __name__ == "__main__":
    evaluator = EnhancedEvaluator()
    results = evaluator.evaluate()
