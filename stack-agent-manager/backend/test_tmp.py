#!/usr/bin/env python3
"""
Simple test script to verify OCI LLM models are working.
Usage: uv run python tmp_test.py
"""

import os
from dotenv import load_dotenv
from langchain_oci import OCIGenAI

# Load environment variables
load_dotenv()


def test_model(model_name: str, model_id: str):
    """Test a single OCI model"""
    print(f"\n{'='*60}")
    print(f"Testing {model_name} model")
    print(f"{'='*60}\n")

    compartment_id = os.getenv("COMPARTMENT_OCID")
    if not compartment_id:
        print("ERROR: COMPARTMENT_OCID not found in environment variables")
        return False

    service_endpoint = os.getenv(
        "OCI_SERVICE_ENDPOINT",
        "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com",
    )

    try:
        # Initialize the model
        print(f"Initializing {model_name} model...")
        llm = OCIGenAI(
            model_id=model_id,
            service_endpoint=service_endpoint,
            compartment_id=compartment_id,
            model_kwargs={"temperature": 0.7, "max_tokens": 200},
        )
        print(f"✓ Model initialized successfully\n")

        # Get user input
        prompt = input("Enter your prompt (or press Enter for default): ").strip()
        if not prompt:
            prompt = "Say hello and introduce yourself in one sentence."

        print(f"\nPrompt: {prompt}")
        print(f"\nGenerating response...\n")
        print("-" * 60)

        # Generate response
        response = llm.invoke(prompt)

        print(response)
        print("-" * 60)
        print(f"\n✓ Success! {model_name} model is working correctly.\n")
        return True

    except Exception as e:
        print(f"\n✗ Error testing {model_name} model:")
        print(f"  {str(e)}\n")
        return False


def main():
    """Main function to test models"""
    print("OCI LLM Model Test Script")
    print("=" * 60)

    # Get available models from environment
    models_to_test = []

    # cohere_id = os.getenv("OCI_COHERE_MODEL_ID")
    # if cohere_id:
    #     models_to_test.append(("Cohere", cohere_id))

    # gemini_id = os.getenv("OCI_GEMINI_MODEL_ID")
    # if gemini_id:
    #     models_to_test.append(("Gemini", gemini_id))

    grok_id = "xai.grok-3"
    if grok_id:
        models_to_test.append(("Grok", grok_id))

    # llama_id = os.getenv("OCI_LLAMA_MODEL_ID")
    # if llama_id:
    #     models_to_test.append(("Llama", llama_id))

    if not models_to_test:
        print("\nERROR: No model IDs found in environment variables.")
        print("Please set at least one of:")
        print("  - OCI_COHERE_MODEL_ID")
        print("  - OCI_GEMINI_MODEL_ID")
        print("  - OCI_GROK_MODEL_ID")
        print("  - OCI_LLAMA_MODEL_ID")
        return

    # Test each model
    for model_name, model_id in models_to_test:
        test_model(model_name, model_id)

        # Ask if user wants to test another model
        if len(models_to_test) > 1:
            continue_test = input("\nTest another model? (y/n): ").strip().lower()
            if continue_test != "y":
                break

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()