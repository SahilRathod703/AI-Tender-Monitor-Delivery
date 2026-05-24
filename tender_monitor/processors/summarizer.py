"""
processors/summarizer.py — AI-powered tender summarization via Claude API.
Generates concise, structured summaries for each relevant tender.
"""

import asyncio
import logging
from typing import Optional

import anthropic

from scrapers.base_scraper import RawTender

logger = logging.getLogger(__name__)

SUMMARY_SYSTEM_PROMPT = """You are an expert government procurement analyst for India. 
Your task is to summarize government tenders in a clear, structured way for technology companies 
looking for business opportunities.

For each tender, provide a summary in this exact JSON format:
{
  "summary": "2-3 sentence description of what is needed and who the buyer is",
  "tech_stack": "Key technologies/skills required (comma-separated)",
  "opportunity_type": "one of: AI/ML, Software Dev, IT Services, Electronics, Cybersecurity, Cloud, Data Science, Automation, Digital Infrastructure, Other",
  "urgency": "one of: High (< 7 days), Medium (7-30 days), Low (> 30 days)",
  "scope": "one of: Small (< 10L), Medium (10L-1Cr), Large (> 1Cr), Unknown"
}

Be factual, concise, and focus on actionable information for a technology company."""


class TenderSummarizer:
    """Uses Claude API to generate structured summaries of tenders."""

    def __init__(self, api_key: str):
        if not api_key:
            logger.warning("No Anthropic API key — summaries will be skipped")
            self.client = None
        else:
            self.client = anthropic.AsyncAnthropic(api_key=api_key)

    async def summarize_batch(
        self, tenders: list[RawTender], concurrency: int = 5
    ) -> list[RawTender]:
        """Summarize multiple tenders with controlled concurrency."""
        if not self.client:
            logger.warning("Skipping AI summaries (no API key)")
            for t in tenders:
                t.ai_summary = t.raw_description or t.title
            return tenders

        semaphore = asyncio.Semaphore(concurrency)
        tasks = [self._summarize_one(t, semaphore) for t in tenders]
        return await asyncio.gather(*tasks)

    async def _summarize_one(
        self, tender: RawTender, semaphore: asyncio.Semaphore
    ) -> RawTender:
        """Summarize a single tender."""
        async with semaphore:
            try:
                summary_data = await self._call_claude(tender)
                tender.ai_summary = self._format_summary(summary_data)
            except Exception as e:
                logger.error(f"Summarizer error for '{tender.title[:50]}': {e}")
                tender.ai_summary = tender.raw_description or tender.title
        return tender

    async def _call_claude(self, tender: RawTender) -> Optional[dict]:
        """Call Claude API to summarize a tender."""
        import json

        prompt = f"""Summarize this Indian government tender:

Title: {tender.title}
Organization: {tender.organization}
Portal: {tender.portal_source}
Category: {tender.category or 'N/A'}
Matched Keywords: {', '.join(tender.matched_keywords[:5])}
Description: {tender.raw_description or 'N/A'}
Publish Date: {tender.publish_date or 'N/A'}
Deadline: {tender.deadline or 'N/A'}
Tender Value: {tender.tender_value or 'Not specified'}

Return ONLY the JSON object, no other text."""

        response = await self.client.messages.create(
            model="claude-haiku-4-5-20251001",   # Fast + cheap for batch summarization
            max_tokens=400,
            system=SUMMARY_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()

        # Parse JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON from text
            import re
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                return json.loads(m.group())
            return {"summary": text, "tech_stack": "", "opportunity_type": "Other",
                    "urgency": "Unknown", "scope": "Unknown"}

    def _format_summary(self, data: dict) -> str:
        """Format the AI summary dict into a readable string."""
        if not data:
            return "Summary unavailable"

        parts = [
            f"📋 {data.get('summary', 'N/A')}",
            f"🔧 Tech: {data.get('tech_stack', 'N/A')}",
            f"📂 Type: {data.get('opportunity_type', 'N/A')}",
            f"⏰ Urgency: {data.get('urgency', 'N/A')}",
            f"💰 Scope: {data.get('scope', 'N/A')}",
        ]
        return "\n".join(parts)
