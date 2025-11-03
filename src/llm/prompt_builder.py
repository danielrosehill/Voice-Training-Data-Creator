"""Prompt building for text generation."""
from typing import Optional, List
import random


class PromptBuilder:
    """Builds prompts for LLM text generation."""

    STYLE_DESCRIPTIONS = {
        "General Purpose": "varied, neutral content suitable for general voice training",
        "Colloquial": "casual, everyday conversational speech with natural patterns",
        "Voice Note": "natural dictation style with thinking patterns and pauses, as if speaking into a voice recorder",
        "Technical": "professional and technical language with industry terminology",
        "Prose": "literary, narrative style with descriptive and flowing language"
    }

    # Expanded topic list for maximum variability
    RANDOM_TOPICS = [
        # Technology & Innovation
        "artificial intelligence and machine learning",
        "software development and programming",
        "cybersecurity and data privacy",
        "emerging technologies and future trends",
        "digital transformation",
        "robotics and automation",
        "virtual reality and augmented reality",
        "blockchain and cryptocurrency",
        "quantum computing",
        "Internet of Things and smart devices",

        # Science & Nature
        "climate change and environmental conservation",
        "space exploration and astronomy",
        "biology and human health",
        "oceanography and marine life",
        "renewable energy and sustainability",
        "wildlife and ecosystems",
        "geology and natural phenomena",
        "physics and the universe",
        "chemistry in everyday life",
        "genetics and biotechnology",

        # Society & Culture
        "history and historical events",
        "art and artistic movements",
        "music and musical traditions",
        "literature and storytelling",
        "philosophy and ethics",
        "languages and linguistics",
        "architecture and urban design",
        "fashion and design trends",
        "cultural traditions and customs",
        "social movements and change",

        # Daily Life & Personal
        "personal productivity and organization",
        "mindfulness and mental wellness",
        "fitness and physical health",
        "nutrition and cooking",
        "home improvement and DIY projects",
        "gardening and plant care",
        "pets and animal companionship",
        "parenting and family life",
        "relationships and communication",
        "hobbies and creative pursuits",

        # Professional & Business
        "entrepreneurship and startups",
        "leadership and management",
        "marketing and branding",
        "finance and investing",
        "career development and skills",
        "remote work and digital nomad lifestyle",
        "business strategy and innovation",
        "project management",
        "sales and customer service",
        "human resources and workplace culture",

        # Travel & Geography
        "international travel destinations",
        "local tourism and hidden gems",
        "cultural immersion experiences",
        "adventure travel and outdoor activities",
        "food tourism and culinary exploration",
        "sustainable and eco-tourism",
        "historical landmarks and monuments",
        "urban exploration",
        "road trips and scenic routes",
        "travel planning and logistics",

        # Entertainment & Media
        "film and cinema",
        "television and streaming content",
        "gaming and esports",
        "podcasts and audio content",
        "social media and digital culture",
        "theater and performing arts",
        "photography and visual arts",
        "comedy and humor",
        "sports and athletics",
        "books and reading",

        # Education & Learning
        "online education and e-learning",
        "study techniques and memory",
        "scientific research methods",
        "critical thinking and problem solving",
        "teaching and pedagogy",
        "childhood development and learning",
        "vocational training and skills",
        "language learning",
        "educational technology",
        "lifelong learning and personal growth",

        # Miscellaneous
        "urban legends and folklore",
        "mysteries and unexplained phenomena",
        "psychology and human behavior",
        "economics and global markets",
        "politics and governance",
        "law and legal systems",
        "transportation and mobility",
        "community building and volunteering",
        "meditation and spirituality",
        "disaster preparedness and survival skills"
    ]

    def __init__(self):
        """Initialize prompt builder."""
        pass

    def build_generation_prompt(
        self,
        duration_minutes: float,
        wpm: int,
        style: str,
        dictionary: Optional[List[str]] = None
    ) -> str:
        """Build a prompt for text generation.

        Args:
            duration_minutes: Target duration in minutes.
            wpm: Words per minute.
            style: Style of text to generate.
            dictionary: Optional list of words to include.

        Returns:
            Complete prompt string.
        """
        # Calculate target word count
        word_count = int(duration_minutes * wpm)

        # Get style description
        style_desc = self.STYLE_DESCRIPTIONS.get(
            style,
            self.STYLE_DESCRIPTIONS["General Purpose"]
        )

        # Select a random topic for variety
        random_topic = random.choice(self.RANDOM_TOPICS)

        # Build base prompt
        prompt_parts = [
            f"Generate approximately {word_count} words ({duration_minutes} minutes at {wpm} WPM) of {style_desc}.",
            "",
            f"Topic focus: {random_topic}",
            "",
            "Requirements:",
            f"- Write in a {style.lower()} style",
            f"- Focus the content around the topic: {random_topic}",
            "- Generate ONLY the text content without any meta-commentary, introduction, or explanation",
            "- Make the text natural and suitable for voice recording",
            "- Avoid special formatting, markdown, or unusual characters",
        ]

        # Add dictionary requirements if provided
        if dictionary and len(dictionary) > 0:
            prompt_parts.extend([
                "",
                "Vocabulary requirements:",
                f"- Naturally incorporate these words throughout the text: {', '.join(dictionary)}",
                "- Use the words in appropriate context",
                "- Don't force the words if they don't fit naturally"
            ])

        # Add style-specific guidance
        if style == "Voice Note":
            prompt_parts.extend([
                "",
                "Voice note style guidance:",
                "- Include natural speech patterns like 'um', 'you know', 'I think'",
                "- Add brief pauses and thinking patterns",
                "- Make it sound like someone talking through their thoughts"
            ])
        elif style == "Colloquial":
            prompt_parts.extend([
                "",
                "Colloquial style guidance:",
                "- Use everyday language and common expressions",
                "- Include contractions (don't, won't, can't)",
                "- Make it sound conversational and natural"
            ])
        elif style == "Technical":
            prompt_parts.extend([
                "",
                "Technical style guidance:",
                "- Use professional terminology appropriately",
                "- Maintain formal but clear language",
                "- Focus on explanatory or instructional content"
            ])
        elif style == "Prose":
            prompt_parts.extend([
                "",
                "Prose style guidance:",
                "- Use descriptive and flowing language",
                "- Create narrative or literary content",
                "- Employ varied sentence structures"
            ])

        prompt_parts.append("")
        prompt_parts.append("Begin the text now:")

        return "\n".join(prompt_parts)

    def clean_generated_text(self, text: str) -> str:
        """Clean up generated text by removing meta-commentary.

        Args:
            text: Generated text to clean.

        Returns:
            Cleaned text.
        """
        # Remove common meta-commentary phrases
        meta_phrases = [
            "Here's your text:",
            "Here is the text:",
            "Here's the generated text:",
            "Here is your text:",
            "As requested,",
            "Certainly!",
            "Sure!",
            "Of course!",
            "I'll generate",
            "I've generated",
        ]

        cleaned = text.strip()

        # Remove meta-commentary from the beginning
        for phrase in meta_phrases:
            if cleaned.lower().startswith(phrase.lower()):
                cleaned = cleaned[len(phrase):].strip()

        # Remove leading/trailing quotes if present
        if cleaned.startswith('"') and cleaned.endswith('"'):
            cleaned = cleaned[1:-1]
        elif cleaned.startswith("'") and cleaned.endswith("'"):
            cleaned = cleaned[1:-1]

        return cleaned.strip()

    def validate_dictionary(self, words: List[str]) -> tuple[bool, Optional[str]]:
        """Validate dictionary words.

        Args:
            words: List of words to validate.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if not words:
            return True, None

        if len(words) > 50:
            return False, "Dictionary contains more than 50 words. Consider reducing for better results."

        # Check for very long words (likely not actual words)
        for word in words:
            if len(word) > 30:
                return False, f"Word '{word}' is unusually long. Please check your dictionary."

        return True, None
