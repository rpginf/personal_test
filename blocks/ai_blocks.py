from __future__ import annotations
import json
from typing import Any, Dict
from .base import Block, Param
from .registry import register


@register
class AITextBlock(Block):
    CATEGORY = 'AI'
    NAME = 'AI Text Generation'
    DESCRIPTION = 'Sends a prompt to an OpenAI model and stores the response. Supports {variable} substitution.'
    ICON = '🤖'
    COLOR = '#f1fa8c'
    PARAMS = [
        Param('prompt', 'Prompt', 'multiline', required=True,
              placeholder='Summarise the following text:\n{extracted_text}'),
        Param('api_key', 'OpenAI API Key', 'password', default=''),
        Param('model', 'Model', 'choice', default='gpt-4o-mini',
              options=['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo']),
        Param('output_variable', 'Store response in variable', 'text', default='ai_response'),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        try:
            import openai
        except ImportError:
            raise ImportError("openai not installed. Run: pip install openai")
        api_key = (self.params.get('api_key') or '').strip()
        if not api_key:
            raise ValueError("OpenAI API key is required")
        prompt = self.params.get('prompt') or ''
        for key, val in context.items():
            prompt = prompt.replace(f'{{{key}}}', str(val))
        client = openai.OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=self.params.get('model', 'gpt-4o-mini'),
            messages=[{'role': 'user', 'content': prompt}]
        )
        result = resp.choices[0].message.content
        var = self.params.get('output_variable') or 'ai_response'
        context[var] = result
        self.output = result[:200]


@register
class AIDataExtractionBlock(Block):
    CATEGORY = 'AI'
    NAME = 'AI Data Extraction'
    DESCRIPTION = 'Uses AI to extract structured JSON data from a context variable containing text'
    ICON = '🔬'
    COLOR = '#f1fa8c'
    PARAMS = [
        Param('data_variable', 'Input data variable', 'text', default='web_content',
              placeholder='Variable containing text to analyse'),
        Param('instructions', 'What to extract', 'multiline', required=True,
              placeholder='Extract: company name, date, total amount as JSON'),
        Param('api_key', 'OpenAI API Key', 'password', default=''),
        Param('output_variable', 'Store result in variable', 'text', default='extracted_data'),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        try:
            import openai
        except ImportError:
            raise ImportError("openai not installed. Run: pip install openai")
        api_key = (self.params.get('api_key') or '').strip()
        if not api_key:
            raise ValueError("OpenAI API key is required")
        var = self.params.get('data_variable') or 'web_content'
        data = context.get(var)
        if data is None:
            raise ValueError(f"No data in variable '{var}'")
        instructions = self.params.get('instructions') or ''
        prompt = (
            f"Given the following data, {instructions}\n\n"
            f"Data:\n{str(data)[:4000]}\n\n"
            "Respond with a valid JSON object only."
        )
        client = openai.OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{'role': 'user', 'content': prompt}],
            response_format={'type': 'json_object'}
        )
        result = json.loads(resp.choices[0].message.content)
        var_out = self.params.get('output_variable') or 'extracted_data'
        context[var_out] = result
        self.output = str(result)[:200]


@register
class AIDecisionBlock(Block):
    CATEGORY = 'AI'
    NAME = 'AI Decision'
    DESCRIPTION = 'Uses AI to make a yes/no decision; stores "yes" or "no" in a variable'
    ICON = '🧠'
    COLOR = '#f1fa8c'
    PARAMS = [
        Param('question', 'Decision question', 'multiline', required=True,
              placeholder='Should I proceed? Context: {my_var}'),
        Param('api_key', 'OpenAI API Key', 'password', default=''),
        Param('output_variable', 'Store result in variable', 'text', default='ai_decision'),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        try:
            import openai
        except ImportError:
            raise ImportError("openai not installed. Run: pip install openai")
        api_key = (self.params.get('api_key') or '').strip()
        if not api_key:
            raise ValueError("OpenAI API key is required")
        question = self.params.get('question') or ''
        for key, val in context.items():
            question = question.replace(f'{{{key}}}', str(val))
        prompt = f"{question}\n\nAnswer with exactly 'yes' or 'no'."
        client = openai.OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{'role': 'user', 'content': prompt}]
        )
        decision = resp.choices[0].message.content.strip().lower()
        if 'yes' in decision:
            decision = 'yes'
        else:
            decision = 'no'
        var = self.params.get('output_variable') or 'ai_decision'
        context[var] = decision
        self.output = f"Decision: {decision}"
