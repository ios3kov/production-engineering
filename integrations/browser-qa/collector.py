"""Optional helper for an already authorized synchronous Playwright Page.

Does not install/launch browsers, navigate, change DOM or certify accessibility.
"""
from pathlib import Path

MEASUREMENT = Path(__file__).with_name('measure.js').read_text(encoding='utf-8')


def measure_ui(page, selectors=('[data-ui-qa]',), *, max_elements=1000, timeout_ms=5000):
    """Return bounded observations. A missing scope or font timeout is incomplete."""
    if not isinstance(selectors, (tuple, list)) or not selectors or len(selectors) > 32:
        raise ValueError('Supply 1-32 explicit trusted selectors')
    if any(not isinstance(x, str) or not x or len(x)>256 for x in selectors):
        raise ValueError('Invalid selector')
    if type(max_elements) is not int or not 1<=max_elements<=5000:
        raise ValueError('max_elements must be 1-5000')
    if type(timeout_ms) is not int or not 1<=timeout_ms<=30000:
        raise ValueError('timeout_ms must be 1-30000')
    page.wait_for_function("!document.fonts || document.fonts.status !== 'loading'", timeout=timeout_ms)
    result=page.evaluate(MEASUREMENT, {'selectors':list(selectors),'maxElements':max_elements})
    scope=result['coverage']
    result['inspection_status']='INCOMPLETE' if scope['missingSelectors'] or scope['truncated'] or not scope['measured'] else 'NEEDS_REVIEW'
    return result
