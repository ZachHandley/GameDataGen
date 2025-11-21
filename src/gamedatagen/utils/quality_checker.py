"""
Image Quality Checker with GPT-4o-mini vision

Lightweight quality control for generated images.
"""

import json
from typing import List, Optional

from openai import AsyncOpenAI
from pydantic import BaseModel


class QualityIssue(BaseModel):
    """Quality issue found in image"""

    type: str  # "anatomy", "proportions", "artifacts", "text", "blur", "distortion"
    severity: str  # "minor", "moderate", "severe"
    description: str


class QualityCheckResult(BaseModel):
    """Quality check result"""

    passed: bool
    score: int  # 0-100
    issues: List[QualityIssue]
    recommendation: str  # "approve", "regenerate", "manual_review"
    explanation: str


class QualityChecker:
    """Image quality checker using GPT-4o-mini vision"""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"

    async def check_image(
        self,
        image_url: str,
        entity_type: str,
        expected_content: str,
        strict_mode: bool = False,
        check_for_text: bool = True,
    ) -> QualityCheckResult:
        """
        Check image quality

        Args:
            image_url: URL of image to check
            entity_type: Type of entity (for context)
            expected_content: What should be in the image
            strict_mode: Use stricter quality standards
            check_for_text: Check for unwanted text artifacts

        Returns:
            Quality check result
        """
        # Build quality check prompt
        prompt = self._build_check_prompt(
            entity_type=entity_type,
            expected_content=expected_content,
            strict_mode=strict_mode,
            check_for_text=check_for_text,
        )

        # Call GPT-4o-mini with vision
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an image quality checker for game art. Analyze images and return quality assessment as JSON.",
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.3,  # Lower temperature for consistent checking
        )

        # Parse response
        content = response.choices[0].message.content
        if not content:
            raise ValueError("No response from quality checker")

        data = json.loads(content)

        # Build result
        issues = [QualityIssue(**issue) for issue in data.get("issues", [])]

        result = QualityCheckResult(
            passed=data.get("passed", False),
            score=data.get("score", 0),
            issues=issues,
            recommendation=data.get("recommendation", "manual_review"),
            explanation=data.get("explanation", ""),
        )

        return result

    def _build_check_prompt(
        self,
        entity_type: str,
        expected_content: str,
        strict_mode: bool,
        check_for_text: bool,
    ) -> str:
        """Build quality check prompt"""

        prompt = f"""Analyze this {entity_type} image for quality issues.

Expected Content: {expected_content}

Check for the following issues:
1. **AI Artifacts**: Weird patterns, duplicate features, morphing textures
2. **Anatomy Issues**: Incorrect proportions, extra/missing limbs (for characters)
3. **Proportions**: Objects that look wrong size-wise
4. **Blur/Distortion**: Blurry areas, distorted features
"""

        if check_for_text:
            prompt += "5. **Unwanted Text**: Any text or writing in the image\n"

        if strict_mode:
            prompt += "\nUse STRICT quality standards. Minor issues should be flagged.\n"
        else:
            prompt += "\nUse NORMAL quality standards. Only flag moderate to severe issues.\n"

        prompt += """
Return a JSON object with this structure:
{
  "passed": boolean,  // true if image is acceptable
  "score": number,    // 0-100 quality score
  "issues": [
    {
      "type": "anatomy|proportions|artifacts|text|blur|distortion",
      "severity": "minor|moderate|severe",
      "description": "Brief description of the issue"
    }
  ],
  "recommendation": "approve|regenerate|manual_review",
  "explanation": "Brief explanation of the assessment"
}

Scoring guide:
- 90-100: Excellent, no issues
- 75-89: Good, minor issues only
- 50-74: Acceptable, some issues
- Below 50: Poor, regenerate recommended
"""

        return prompt

    def format_result(self, result: QualityCheckResult) -> str:
        """Format quality check result for display"""

        lines = []

        # Header
        status_emoji = "✓" if result.passed else "✗"
        lines.append(f"{status_emoji} Quality Score: {result.score}/100")

        # Recommendation
        rec_map = {
            "approve": "✅ APPROVE",
            "regenerate": "🔄 REGENERATE",
            "manual_review": "👁️  MANUAL REVIEW",
        }
        lines.append(f"Recommendation: {rec_map.get(result.recommendation, result.recommendation)}")

        # Issues
        if result.issues:
            lines.append(f"\nIssues found ({len(result.issues)}):")
            for issue in result.issues:
                severity_emoji = {
                    "minor": "⚠️",
                    "moderate": "⚠️",
                    "severe": "❌",
                }.get(issue.severity, "⚠️")
                lines.append(f"  {severity_emoji} [{issue.severity.upper()}] {issue.type}: {issue.description}")
        else:
            lines.append("\n✓ No issues found")

        # Explanation
        if result.explanation:
            lines.append(f"\n{result.explanation}")

        return "\n".join(lines)
