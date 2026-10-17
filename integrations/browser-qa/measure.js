// Original measurement helper; no network, mutation, taste score or motion quota.
({ selectors, maxElements }) => {
  const chosen = new Set();
  const missing = [];
  for (const selector of selectors) {
    const nodes = document.querySelectorAll(selector);
    if (!nodes.length) missing.push(selector);
    for (const node of nodes) chosen.add(node);
  }
  const nodes = [...chosen];
  const elements = [];
  const candidates = [];
  const rectOf = r => ({ x:r.x, y:r.y, width:r.width, height:r.height });
  for (const [index, element] of nodes.slice(0, maxElements).entries()) {
    const r = element.getBoundingClientRect();
    let visible = r.width > 0 && r.height > 0;
    for (let p = element; p; p = p.parentElement) {
      const s = getComputedStyle(p);
      if (s.display === 'none' || s.visibility === 'hidden' || s.visibility === 'collapse' || Number(s.opacity) === 0) visible = false;
    }
    const style = getComputedStyle(element);
    const row = { index, tag:element.tagName.toLowerCase(), visible, rect:rectOf(r),
      declaredFont:style.fontFamily, fontSize:style.fontSize, lineHeight:style.lineHeight,
      clientWidth:element.clientWidth, scrollWidth:element.scrollWidth,
      clientHeight:element.clientHeight, scrollHeight:element.scrollHeight };
    if (visible) {
      const range = document.createRange(); range.selectNodeContents(element);
      const lineTops = new Set([...range.getClientRects()].filter(b => b.width && b.height).map(b => Math.round(b.top)));
      row.textRectRows = lineTops.size;
      const clippedX = element.clientWidth > 0 && element.scrollWidth > element.clientWidth + 1 && ['hidden','clip'].includes(style.overflowX);
      const clippedY = element.clientHeight > 0 && element.scrollHeight > element.clientHeight + 1 && ['hidden','clip'].includes(style.overflowY);
      if (clippedX || clippedY) candidates.push({ kind:'clipped-content', index, horizontal:clippedX, vertical:clippedY });
      const points = [0.25,0.5,0.75].map(f => [r.left+r.width*f, r.top+r.height*0.5])
        .filter(([x,y]) => x>=0 && x<innerWidth && y>=0 && y<innerHeight);
      const covered = points.filter(([x,y]) => {
        const hit = document.elementFromPoint(x,y);
        return hit && hit!==element && !element.contains(hit) && !hit.contains(element);
      }).length;
      row.hitTest = { sampled:points.length, covered };
      if (covered) candidates.push({ kind:'hit-test-obstruction', index, sampled:points.length, covered });
      if (element instanceof HTMLImageElement && element.complete && element.naturalWidth===0 && element.getAttribute('src')) candidates.push({kind:'broken-image',index});
    }
    elements.push(row);
  }
  const pageWidth = Math.max(document.documentElement.scrollWidth, document.body?.scrollWidth || 0);
  if (pageWidth > document.documentElement.clientWidth + 1) candidates.push({kind:'horizontal-overflow',pixels:pageWidth-document.documentElement.clientWidth});
  const fonts = document.fonts ? [...document.fonts].map(f => ({family:f.family,status:f.status})) : null;
  for (const font of fonts || []) if(font.status==='error') candidates.push({kind:'font-load-error',family:font.family});
  return { schema_version:1, producer:'pe-ui-measurements', release_readiness:'not_assessed',
    viewport:{width:innerWidth,height:innerHeight,dpr:devicePixelRatio}, fonts,
    coverage:{selected:nodes.length, measured:elements.length, missingSelectors:missing,
      truncated:nodes.length>maxElements, scope:'Selected elements in this document and current viewport; no shadow DOM or iframe traversal'},
    elements, candidates,
    limitations:['Candidates need rendered review; intentional cropping may be valid.',
      'Hit tests sample pointer geometry, not painted-pixel occlusion or accessibility.',
      'Declared font families and loaded faces do not identify actual glyph fallback.',
      'No text content, source URLs, motion minimum or aesthetic score is collected.'] };
}
