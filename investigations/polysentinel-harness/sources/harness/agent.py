"""One bounded call to Claude Code. No tools, no session, no MCP, no settings, so it can neither act nor spawn anything: it returns JSON, and a schema decides what counts.

Whatever a market title says inside the context is data for a function without tools. Off by default: `llm.enabled` must be set.
"""
import json
import os
import subprocess
import tempfile

from .recover import Pause, Permanent, Transient

DEPTH = 'POLYSENTINEL_HARNESS_LLM'
SYSTEM = ('You propose hypotheses for a research queue on Polymarket behaviour. You see notes, not data. Each hypothesis names one feature and a threshold, in these exact units: '
          'new_wallet: the first trade seen from this wallet is at most THRESHOLD seconds before this entry. large_entry: the entry is at least THRESHOLD US dollars. '
          'low_price: the entry price is at most THRESHOLD, between 0 and 1. late_entry: the entry is at most THRESHOLD seconds before the market ends. direction 1 means the feature gains more, -1 less. '
          'An independent verifier tests it out of sample at the cost of every test ever run, so propose few. Do not repeat a rejected idea. Never name a person or call a wallet an insider. Answer with JSON only.')
SCHEMA = dict(type='object', additionalProperties=False, required=['hypotheses'], properties=dict(hypotheses=dict(type='array', maxItems=3, items=dict(type='object', additionalProperties=False, required=['statement', 'feature', 'threshold'],
              properties=dict(statement=dict(type='string', maxLength=300), feature=dict(type='string', enum=['new_wallet', 'large_entry', 'low_price', 'late_entry']), threshold=dict(type='number', minimum=0), direction=dict(type='integer', enum=[1, -1]))))))


def validated(answer):
    """The CLI enforces the schema when it can. This is the check that holds either way."""
    items = answer.get('hypotheses') if isinstance(answer, dict) else None
    if not isinstance(items, list) or len(items) > 3:
        raise Permanent('Model answer without a short list of hypotheses')
    allowed = SCHEMA['properties']['hypotheses']['items']['properties']['feature']['enum']
    for item in items:
        if not isinstance(item, dict) or item.get('feature') not in allowed or not isinstance(item.get('threshold'), (int, float)) or item['threshold'] < 0 or not isinstance(item.get('statement'), str):
            raise Permanent(f'Hypothesis outside the schema: {str(item)[:200]}')
    return items


def ask_for_hypotheses(ctx, context):
    if os.environ.get(DEPTH):
        raise Permanent('A model call may not start another one')
    settings, budgets, h = ctx.config['llm'], ctx.config['budgets'], ctx.h
    if not settings.get('enabled'):
        raise Permanent('The model is disabled')
    # Refused before the call: the estimate counts the prompt and a full answer, since a call cannot be undone once paid for.
    estimate = len(context) // 3 + 1500
    if h.used('llm_calls') + 1 > budgets['llm_calls_per_day']:
        raise Pause(f"{h.used('llm_calls'):g} model calls today, limit {budgets['llm_calls_per_day']}", delay=3600)
    if h.used('llm_tokens') + estimate > budgets['llm_tokens_per_day']:
        raise Pause(f"Token budget: {h.used('llm_tokens'):g} used, about {estimate} needed, limit {budgets['llm_tokens_per_day']}", delay=3600)
    if h.used('llm_usd') + settings['max_usd_per_call'] > budgets['llm_usd_per_day']:
        raise Pause(f"Cost budget: ${h.used('llm_usd'):.3f} used, limit ${budgets['llm_usd_per_day']}", delay=3600)
    with h.tx():
        h.spend('llm_calls', 1)
    command = [settings['executable'], '-p', context + '\n\nPropose at most 3 hypotheses.', '--system-prompt', SYSTEM, '--model', settings['model'], '--output-format', 'json', '--json-schema', json.dumps(SCHEMA),
               '--max-budget-usd', str(settings['max_usd_per_call']), '--tools', '', '--strict-mcp-config', '--no-session-persistence', '--setting-sources', '']
    with tempfile.TemporaryDirectory(dir=h.root) as empty:  # no project files for it to pick up
        try:
            done = subprocess.run(command, capture_output=True, text=True, timeout=settings['timeout_s'], cwd=empty, env=dict(os.environ, **{DEPTH: '1'}), stdin=subprocess.DEVNULL)
        except subprocess.TimeoutExpired as exc:
            raise Transient(f"Model call over {settings['timeout_s']} s") from exc
        except OSError as exc:
            raise Permanent(f'Model CLI unavailable: {exc}') from exc
    try:
        outer = json.loads(done.stdout)
    except ValueError as exc:
        raise Transient(f'Unparsable model output, exit {done.returncode}: {done.stdout[:200]}') from exc
    usage = outer.get('usage') or {}
    tokens = sum(usage.get(k, 0) for k in ('input_tokens', 'output_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens'))
    cost = outer.get('total_cost_usd', 0) or 0
    with h.tx():
        h.spend('llm_tokens', tokens)
        h.spend('llm_usd', cost)
        h.log('info', 'model_call', ctx.id, tokens=tokens, usd=cost, is_error=outer.get('is_error'), model=settings['model'])
    if outer.get('is_error') or done.returncode != 0:
        raise Transient(f"Model call failed, exit {done.returncode}: {str(outer.get('result'))[:200]}")
    answer = outer.get('structured_output')
    if answer is None:
        try:
            answer = json.loads(outer.get('result') or '')
        except ValueError as exc:
            raise Permanent('Model answer is not JSON') from exc
    return dict(hypotheses=validated(answer), usage=dict(tokens=tokens, usd=cost))
