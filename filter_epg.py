import gzip
import re
import time
import urllib.error
import urllib.request
from xml.etree import ElementTree as ET

# --- Vertaling (optioneel, faalt netjes als Google blokkeert) ---
TRANSLATOR_AVAILABLE = False
try:
    from deep_translator import GoogleTranslator
    translator = GoogleTranslator(source='auto', target='nl')
    TRANSLATOR_AVAILABLE = True
    print("Vertaler geladen.")
except ImportError:
    print("WARNING: pip install deep-translator ontbreekt.")

HEBREW_PATTERN = re.compile(r'[\u0590-\u05FF]')
translation_cache = {}

def translate_text(text: str) -> str:
    """Vertaal Hebreeuws naar NL. Bij elk falen: originele tekst behouden."""
    if not text or not TRANSLATOR_AVAILABLE:
        return text
    if not HEBREW_PATTERN.search(text):
        return text  # Geen Hebreeuws, niks doen
    
    key = text.strip()
    if key in translation_cache:
        return translation_cache[key]
    
    try:
        time.sleep(0.25)
        result = translator.translate(key)
        translation_cache[key] = result
        print(f"  [NL] {key[:45]}... -> {result[:45]}...")
        return result
    except Exception as e:
        print(f"  [VERTALING MISLUKT] {key[:45]}... | Fout: {e}")
        translation_cache[key] = key  # Cache fallback, voorkom herhaalde pogingen
        return key

def translate_recursive(elem):
    """Doorloop XML element en vertaal alle Hebreeuwse tekst."""
    if elem.text:
        elem.text = translate_text(elem.text)
    for child in elem:
        translate_recursive(child)
        if child.tail:
            child.tail = translate_text(child.tail)

# --- Configuratie ---
WANTED = {
    "espn.nl", "espn2.nl", "espn4.nl",
    "ziggosport.nl", "ziggosport2.nl", "ziggosport6.nl",
    "skysportspremierleague.uk", "skysportsmainevent.uk", "skysportsfootball.uk",
    "tntsports1.uk", "tntsports2.uk", "tntsports3.uk", "tntsports4.uk",
    "premiersports1.uk", "premiersports2.uk",
    "sportdigitalfussball.de",
    "dazn1.es", "dazn2.es", "dazn3.es", "dazn4.es",
    "daznlaliga.es", "daznlaliga2.es",
    "polsatsportpremium1.pl", "polsatsportpremium2.pl",
    "ספורט4hd.il", "5sport4k.il",
}

SOURCES = [
    "https://iptv-epg.org/files/epg-nl.xml.gz",
    "https://iptv-epg.org/files/epg-gb.xml.gz",
    "https://iptv-epg.org/files/epg-de.xml.gz",
    "https://iptv-epg.org/files/epg-es.xml.gz",
    "https://iptv-epg.org/files/epg-pl.xml.gz",
    "https://iptv-epg.org/files/epg-il.xml.gz",
]

# --- Main ---
root_out = ET.Element("tv")
seen_channels = set()

for url in SOURCES:
    print(f"\nDownloading {url}...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "acesport-epg/1.0"})
        with urllib.request.urlopen(req, timeout=180) as r:
            data = r.read()
        if url.endswith(".gz"):
            data = gzip.decompress(data)
        tree = ET.fromstring(data)
    except urllib.error.HTTPError as e:
        print(f"  -> HTTP {e.code} ({e.reason}) — bron overgeslagen.")
        continue
    except Exception as e:
        print(f"  -> FAILED: {e}")
        continue

    for ch in tree.findall("channel"):
        cid = (ch.get("id") or "").lower()
        if cid in WANTED and cid not in seen_channels:
            root_out.append(ch)
            seen_channels.add(cid)

    for prog in tree.findall("programme"):
        cid = (prog.get("channel") or "").lower()
        if cid in WANTED:
            translate_recursive(prog)
            root_out.append(prog)

xml_bytes = ET.tostring(root_out, encoding="utf-8", xml_declaration=True)
with open("epg.xml", "wb") as f:
    f.write(xml_bytes)
with gzip.open("epg.xml.gz", "wb") as f:
    f.write(xml_bytes)

print(f"\n{'='*50}")
print(f"Klaar! Channels: {len(seen_channels)} | Programma's: {len(root_out.findall('programme'))}")
if TRANSLATOR_AVAILABLE:
    failed = sum(1 for k, v in translation_cache.items() if k == v)
    success = len(translation_cache) - failed
    print(f"Vertalingen gelukt: {success} | mislukt: {failed}")
