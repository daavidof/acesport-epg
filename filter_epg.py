import gzip
import re
import time
import urllib.request
from xml.etree import ElementTree as ET

# Installeer dit in je GitHub Action: pip install deep-translator
try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False
    print("WARNING: pip install deep-translator ontbreekt. Hebreeuwse tekst wordt niet vertaald.")

WANTED = {
    # --- Bestaande kanalen ---
    "espn.nl",
    "espn2.nl",
    "espn4.nl",
    "ziggosport.nl",
    "ziggosport2.nl",
    "ziggosport6.nl",
    "skysportspremierleague.uk",
    "skysportsmainevent.uk",
    "skysportsfootball.uk",
    "tntsports1.uk",
    "tntsports2.uk",
    "tntsports3.uk",
    "tntsports4.uk",
    "premiersports1.uk",
    "premiersports2.uk",
    "sportdigitalfussball.de",

    # --- DAZN (Spaans) ---
    "dazn1.es",
    "dazn2.es",
    "dazn3.es",
    "dazn4.es",
    "daznlaliga.es",
    "daznlaliga2.es",

    # --- Polsat ---
    "polsatsportpremium1.pl",
    "polsatsportpremium2.pl",

    # --- Israël (Hebreeuws) ---
    "ספורט4hd.il",   # Sport 4
    "5sport4k.il",   # Sport 5
}

SOURCES = [
    "https://iptv-epg.org/files/epg-nl.xml.gz",
    "https://iptv-epg.org/files/epg-gb.xml.gz",
    "https://iptv-epg.org/files/epg-de.xml.gz",
    "https://iptv-epg.org/files/epg-es.xml.gz",
    "https://iptv-epg.org/files/epg-pl.xml.gz",
    "https://iptv-epg.org/files/epg-il.xml.gz",
]

# Detecteer Hebreeuwse tekens (Unicode range)
HEBREW_PATTERN = re.compile(r'[\u0590-\u05FF]')
translation_cache = {}


def translate_text(text: str) -> str:
    """Vertaal tekst alleen als deze Hebreeuws bevat."""
    if not text or not TRANSLATOR_AVAILABLE:
        return text
    if not HEBREW_PATTERN.search(text):
        return text
    if text in translation_cache:
        return translation_cache[text]
    try:
        time.sleep(0.3)  # Rate limiting
        translated = GoogleTranslator(source='auto', target='nl').translate(text)
        translation_cache[text] = translated
        print(f"  [NL] {text[:60]}... -> {translated[:60]}...")
        return translated
    except Exception as e:
        print(f"  [TRANSLATE ERROR] {e}")
        return text


def download(url: str) -> bytes:
    print(f"Downloading {url}...")
    req = urllib.request.Request(url, headers={"User-Agent": "acesport-epg/1.0"})
    with urllib.request.urlopen(req, timeout=180) as r:
        data = r.read()
    if url.endswith(".gz"):
        data = gzip.decompress(data)
    return data


root_out = ET.Element("tv")
seen_channels = set()

for url in SOURCES:
    try:
        data = download(url)
        tree = ET.fromstring(data)
    except Exception as e:
        print(f"Failed {url}: {e}")
        continue

    for ch in tree.findall("channel"):
        cid = (ch.get("id") or "").lower()
        if cid in WANTED and cid not in seen_channels:
            root_out.append(ch)
            seen_channels.add(cid)

    for prog in tree.findall("programme"):
        cid = (prog.get("channel") or "").lower()
        if cid in WANTED:
            # Clone het programme element zodat we de tekst kunnen aanpassen
            new_prog = ET.Element("programme", prog.attrib)
            for child in prog:
                new_child = ET.SubElement(new_prog, child.tag)
                new_child.attrib = child.attrib
                if child.text:
                    new_child.text = translate_text(child.text)
                else:
                    new_child.text = child.text
            root_out.append(new_prog)

xml_bytes = ET.tostring(root_out, encoding="utf-8", xml_declaration=True)

with open("epg.xml", "wb") as f:
    f.write(xml_bytes)
with gzip.open("epg.xml.gz", "wb") as f:
    f.write(xml_bytes)

print(f"\nDone. Channels found: {sorted(seen_channels)}")
print(f"Total programmes: {len(root_out.findall('programme'))}")
if translation_cache:
    print(f"Translations made: {len(translation_cache)}")
