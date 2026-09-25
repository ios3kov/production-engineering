"""Added structural checks for static HTML; framework templates remain heuristic."""
from html.parser import HTMLParser

class Markup(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.images=[]; self.controls=[]; self.labels=[]; self.open_labels=[]; self.ids=set()
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if a.get('id'):self.ids.add(a['id'])
        if tag=='label':
            label={'for':a.get('for'),'text':''}
            self.labels.append(label);self.open_labels.append(label)
        if tag=='img' and 'alt' not in a:self.images.append(self.getpos()[0])
        if tag in {'input','select','textarea'}:
            self.controls.append((tag,a,self.getpos()[0],list(self.open_labels)))
    def handle_startendtag(self,tag,attrs):
        self.handle_starttag(tag,attrs)
        self.handle_endtag(tag)
    def handle_endtag(self,tag):
        if tag=='label' and self.open_labels:self.open_labels.pop()
    def handle_data(self,data):
        for label in self.open_labels:label['text']+=data
    def missing_labels(self):
        for tag,a,line,wrappers in self.controls:
            kind=(a.get('type') or 'text').lower()
            if tag=='input' and kind in {'hidden','submit','reset'}:continue
            if tag=='input' and kind=='image' and (a.get('alt') or '').strip():continue
            if tag=='input' and kind=='button' and (a.get('value') or '').strip():continue
            if (a.get('aria-label') or '').strip() or (a.get('title') or '').strip():continue
            refs=(a.get('aria-labelledby') or '').split()
            if refs and all(ref in self.ids for ref in refs):continue
            if any(l['text'].strip() for l in wrappers):continue
            if a.get('id') and any(l['for']==a['id'] and l['text'].strip() for l in self.labels):continue
            yield line
