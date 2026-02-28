
import sys
import os
import asyncio
from typing import Dict, Any, List
from pydantic import BaseModel, Field

# Add project root to path
sys.path.append(os.getcwd())

from models.report import CoachRead, FlashCard, InsightObject
from transforms.insight_generator import InsightSynthesizerAgent, FlashCardAgent

class MockResult:
    def __init__(self, data=None, output=None, parts=None):
        self.data = data
        self.output = output
        self.parts = parts

class MockPart:
    def __init__(self, text=None, content=None):
        self.text = text
        self.content = content

async def test_coach_read_parsing():
    print("Testing CoachRead parsing with various result types...")
    agent = InsightSynthesizerAgent()
    
    json_content = '{"insights": [{"title": "Test", "recommendation": "Do something", "reason": "Because", "evidence": ["Fact 1"], "scope": "general"}]}'
    
    # 1. Test with result.data (pydantic-ai 1.x style if it returns data directly)
    print("- Testing with result.data (dict)")
    mock_result = MockResult(data={"insights": [{"title": "Test", "recommendation": "Do something", "reason": "Because", "evidence": ["Fact 1"], "scope": "general"}]})
    # We need to mock agent.run
    original_run = agent.agent.run
    agent.agent.run = lambda prompt: asyncio.Future()
    agent.agent.run = asyncio.iscoroutinefunction(original_run) # This is getting complicated
    
    # Let's just test the parsing logic by extracting it if possible or mocking the whole call
    
    print("Manual parsing test:")
    content = mock_result.data
    try:
        if isinstance(content, dict):
            CoachRead.model_validate(content)
            print("  ✅ Parsed dict successfully")
    except Exception as e:
        print(f"  ❌ Failed to parse dict: {e}")

    # 2. Test with result.parts (Google AI style)
    print("- Testing with result.parts")
    mock_result = MockResult(parts=[MockPart(text='```json\n' + json_content + '\n```')])
    
    # Simulate the extraction logic in synthesize_coach_read
    parts_text = []
    for part in mock_result.parts:
        if hasattr(part, 'text'):
            parts_text.append(part.text)
    content = "".join(parts_text)
    
    import re
    match = re.search(r'\{.*\}', content, re.DOTALL)
    if match:
        try:
            CoachRead.model_validate_json(match.group())
            print("  ✅ Parsed parts text successfully")
        except Exception as e:
            print(f"  ❌ Failed to parse parts text: {e}")

async def test_flash_card_parsing():
    print("\nTesting FlashCard parsing...")
    # This one failed with "missing field" because it was wrapped in 'flash_card'
    json_wrapped = '{"flash_card": {"game_plan": ["A", "B", "C"], "veto_recommendation": "Ban X", "punish_patterns": [], "risk_flags": []}}'
    
    try:
        # This is what currently happens
        FlashCard.model_validate_json(json_wrapped)
        print("  ✅ Parsed wrapped JSON successfully (Wait, it should fail if schema doesn't have flash_card key at top)")
    except Exception as e:
        print(f"  ❌ Failed to parse wrapped JSON as expected: {e}")
        
    # Test our proposed fix: try to unwrap if validation fails
    import json
    data = json.loads(json_wrapped)
    if "flash_card" in data and len(data) == 1:
        try:
            FlashCard.model_validate(data["flash_card"])
            print("  ✅ Parsed unwrapped data successfully")
        except Exception as e:
            print(f"  ❌ Failed to parse unwrapped data: {e}")

if __name__ == "__main__":
    asyncio.run(test_coach_read_parsing())
    asyncio.run(test_flash_card_parsing())
