#!/usr/bin/env python3
"""
Command-line interface for the Java to Node.js Conversion Agent
"""

import os
import sys
import argparse
import time
from src.agents.orchestrator import create_conversion_workflow, ConversionState, get_execution_status
from src.config.llm_config_manager import LLMConfigManager

def main():
    parser = argparse.ArgumentParser(
        description="Convert Java Spring Boot project to Node.js",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using Gemini (default):
  python run_conversion.py --github-url "https://github.com/owner/repo" \\
    --api-token "YOUR_TOKEN" --model "gemini-2.5-flash"
  
  # Using OpenRouter with DeepSeek (free):
  python run_conversion.py --github-url "https://github.com/owner/repo" \\
    --provider openrouter --api-token "YOUR_OPENROUTER_KEY" \\
    --model "deepseek/deepseek-chat-v3.1:free"
  
  # Using OpenAI GPT-5 Codex:
  python run_conversion.py --github-url "https://github.com/owner/repo" \\
    --provider openai --api-token "YOUR_OPENAI_KEY" --model "gpt-5-codex"
  
  # Using config file profile:
  python run_conversion.py --github-url "https://github.com/owner/repo" \\
    --profile openrouter-deepseek --model "deepseek/deepseek-chat-v3.1:free"
        """
    )
    parser.add_argument("--github-url", required=True, help="GitHub URL of the Java project")
    
    # LLM Provider Configuration
    parser.add_argument("--provider", default="gemini", choices=["gemini", "glm", "openrouter", "openai"],
                        help="LLM provider (default: gemini)")
    parser.add_argument("--api-token", dest="api_key",
                        help="API token for the LLM provider (not required if using --profile)")
    parser.add_argument("--model",
                        help="Model name (format depends on provider, optional if using --profile):\n"
                             "  Gemini: gemini-2.5-flash\n"
                             "  OpenRouter: deepseek/deepseek-chat-v3.1:free, openai/gpt-4-turbo\n"
                             "  OpenAI: gpt-4o, gpt-5-codex\n"
                             "  GLM: glm-4-6\n"
                             "If using --profile, model can override profile's model")
    parser.add_argument("--llm-base-url",
                        help="Custom base URL for GLM/OpenAI (optional)")
    parser.add_argument("--profile",
                        help="Profile name from llm_config.json (alternative to --provider/--api-token)")
    parser.add_argument("--llm-config",
                        help="Path to LLM config file (default: llm_config.json in project root)")
    
    # Conversion Configuration
    parser.add_argument("--framework", default="express", choices=["express", "nestjs"], 
                        help="Target framework (default: express)")
    parser.add_argument("--orm", default="sequelize", choices=["sequelize", "typeorm"], 
                        help="ORM choice (default: sequelize)")
    parser.add_argument("--output", help="Output directory (default: auto-generated)")
    
    args = parser.parse_args()
    
    # Validate arguments and load model from profile if needed
    model_to_use = args.model
    
    if args.profile:
        # Using profile - API token not required, model optional (will use profile's model if not provided)
        if args.api_key:
            print("Warning: --api-token ignored when using --profile")
        
        # Load profile to get model if not provided
        if not model_to_use:
            try:
                manager = LLMConfigManager(args.llm_config)
                profile = manager.get_profile(args.profile)
                if profile:
                    model_to_use = profile.get("model")
                    if model_to_use:
                        print(f"Info: Using model '{model_to_use}' from profile '{args.profile}'")
                    else:
                        parser.error(f"Profile '{args.profile}' does not have a model specified")
                else:
                    parser.error(f"Profile '{args.profile}' not found")
            except Exception as e:
                parser.error(f"Failed to load profile: {e}")
        else:
            print(f"Info: Using model '{model_to_use}' (overriding profile's model)")
    else:
        # Using direct provider - API token and model required
        if not args.api_key:
            parser.error("--api-token is required when not using --profile")
        if not model_to_use:
            parser.error("--model is required when not using --profile")
    
    # Validate model is provided
    if not model_to_use or not model_to_use.strip():
        parser.error("Model is required. Either specify --model or use a profile with a model configured.")
    
    # Create workflow
    workflow = create_conversion_workflow()
    
    # Initial state - support both new and legacy format
    state_data = {
        "github_url": args.github_url,
        "target_framework": args.framework,
        "orm_choice": args.orm,
        "model": model_to_use.strip(),
        "repo_path": None,
        "codebase_text_file": None,
        "file_map": None,
        "metadata": None,
        "converted_components": {},
        "output_path": args.output,
        "validation_result": None,
        "errors": []
    }
    
    # LLM configuration
    if args.profile:
        # Using config file profile
        state_data["llm_profile_name"] = args.profile
        state_data["llm_config_path"] = args.llm_config
        state_data["llm_provider"] = None
        state_data["llm_api_token"] = None
        state_data["gemini_api_token"] = None  # Legacy support
        print(f"Using LLM profile: {args.profile}")
    else:
        # Using direct provider configuration
        state_data["llm_provider"] = args.provider
        state_data["llm_api_token"] = args.api_key
        state_data["llm_base_url"] = args.llm_base_url
        state_data["llm_profile_name"] = None
        state_data["llm_config_path"] = args.llm_config
        # Legacy support for backward compatibility
        if args.provider == "gemini":
            state_data["gemini_api_token"] = args.api_key
        else:
            state_data["gemini_api_token"] = None
        print(f"Using LLM provider: {args.provider}")
    
    initial_state = ConversionState(**state_data)
    
    print(f"Starting conversion of {args.github_url}")
    print(f"Target framework: {args.framework}")
    print(f"ORM: {args.orm}")
    if args.profile:
        print(f"LLM: Profile '{args.profile}' with model '{args.model}'")
    else:
        print(f"LLM: {args.provider} with model '{args.model}'")
    print("-" * 50)
    
    # Execute workflow with status monitoring
    try:
        print("\n" + "=" * 60)
        print("Conversion Status Monitor")
        print("=" * 60)
        
        # Start monitoring thread for status updates
        import threading
        
        def monitor_status():
            while True:
                status = get_execution_status()
                if status["current_phase"]:
                    print(f"\r[{status['progress_percentage']}%] {status['current_phase']}", end="", flush=True)
                    if status["current_file"]:
                        print(f" - {status['current_file']}", end="", flush=True)
                    if status["safety_blocks"]:
                        print(f" [⚠️  {len(status['safety_blocks'])} safety blocks]", end="", flush=True)
                time.sleep(2)
        
        monitor_thread = threading.Thread(target=monitor_status, daemon=True)
        monitor_thread.start()
        
        result = workflow.invoke(initial_state)
        
        # Final status
        final_status = get_execution_status()
        print("\n" + "=" * 60)
        print("Final Status")
        print("=" * 60)
        print(f"Phase: {final_status['current_phase'] or 'Completed'}")
        print(f"Files processed: {final_status['files_processed']}/{final_status['files_total']}")
        
        if final_status["safety_blocks"]:
            print(f"\n⚠️  Safety Blocks ({len(final_status['safety_blocks'])}):")
            for block in final_status["safety_blocks"][:5]:  # Show first 5
                print(f"  - {block['file']} ({block['category']})")
                error_preview = block['error'][:100].replace('\n', ' ')
                print(f"    {error_preview}...")
            if len(final_status["safety_blocks"]) > 5:
                print(f"  ... and {len(final_status['safety_blocks']) - 5} more")
        
        if final_status["errors"]:
            print(f"\n❌ Errors ({len(final_status['errors'])}):")
            for error in final_status["errors"][:5]:
                print(f"  - {error[:100]}...")
        
        if result.get("errors"):
            print("Conversion completed with errors:")
            for error in result["errors"]:
                print(f"  - {error}")
        
        if result.get("validation_result", {}).get("valid"):
            print("\n✅ Conversion completed successfully!")
            print(f"Output directory: {result['output_path']}")
        else:
            print("\n❌ Conversion validation failed")
            if result.get("validation_result", {}).get("errors"):
                for error in result["validation_result"]["errors"]:
                    print(f"  - {error}")
    
    except Exception as e:
        print(f"\n❌ Conversion failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
