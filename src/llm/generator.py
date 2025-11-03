"""LLM text generation."""
from openai import OpenAI, OpenAIError
from typing import Optional, Tuple
from .prompt_builder import PromptBuilder


class TextGenerator:
    """Generates synthetic text using OpenAI API."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """Initialize text generator.

        Args:
            api_key: OpenAI API key.
            model: Model to use for generation.
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.prompt_builder = PromptBuilder()

    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test API connection and credentials.

        Returns:
            Tuple of (success, error_message).
        """
        try:
            # Make a minimal API call to test connectivity
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": "Test"}
                ],
                max_tokens=5
            )
            return True, None
        except OpenAIError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def generate_text(
        self,
        duration_minutes: float,
        wpm: int,
        style: str,
        dictionary: Optional[list] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """Generate text based on parameters.

        Args:
            duration_minutes: Target duration in minutes.
            wpm: Words per minute.
            style: Style of text to generate.
            dictionary: Optional list of words to include.

        Returns:
            Tuple of (generated_text, error_message).
        """
        try:
            # Build prompt
            prompt = self.prompt_builder.build_generation_prompt(
                duration_minutes=duration_minutes,
                wpm=wpm,
                style=style,
                dictionary=dictionary
            )

            # Call API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that generates high-quality text for voice training purposes. Generate only the requested text without any meta-commentary or explanations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.8
            )

            # Extract and clean text
            generated_text = response.choices[0].message.content
            if generated_text:
                generated_text = self.prompt_builder.clean_generated_text(generated_text)
                return generated_text, None
            else:
                return None, "No text generated"

        except OpenAIError as e:
            error_msg = str(e)
            if "insufficient_quota" in error_msg.lower():
                return None, "Insufficient API credits. Please check your OpenAI account."
            elif "invalid_api_key" in error_msg.lower():
                return None, "Invalid API key. Please check your API key in settings."
            elif "rate_limit" in error_msg.lower():
                return None, "Rate limit exceeded. Please wait a moment and try again."
            else:
                return None, f"API error: {error_msg}"
        except Exception as e:
            return None, f"Unexpected error: {str(e)}"

    def estimate_cost(self, duration_minutes: float, wpm: int) -> float:
        """Estimate API cost for generating text.

        Args:
            duration_minutes: Target duration in minutes.
            wpm: Words per minute.

        Returns:
            Estimated cost in USD (approximate).
        """
        # Rough estimation based on token usage
        # 1 word ≈ 1.3 tokens (average)
        word_count = int(duration_minutes * wpm)
        estimated_tokens = int(word_count * 1.3)

        # GPT-4o-mini pricing (as of 2024): ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
        # Conservative estimate assuming all tokens are output
        if "gpt-4" in self.model.lower() and "mini" in self.model.lower():
            cost_per_token = 0.60 / 1_000_000
        else:
            # Default conservative estimate
            cost_per_token = 1.0 / 1_000_000

        return estimated_tokens * cost_per_token
