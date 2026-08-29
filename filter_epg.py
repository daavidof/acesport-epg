import gzip
import urllib.request
from xml.etree import ElementTree as ET

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

    # --- Nieuwe DAZN kanalen ---
    "dazn1.es",
    "dazn2.es",
    "dazn3.es",
    "dazn4.es",
    "daznlaliga.es",
    "daznlaliga2.es",

    # --- Nieuwe Polsat kanalen ---
    "polsatsportpremium1.pl",
    "polsatsportpremium2.pl",

    # --- Nieuwe Sport 4 / 5 (Israël) ---
    "&#x5e1;&#x5e4;&#x5d5;&#x5e8;&#x5d8;4hd.il",
    "5sport4k.il",
}

SOURCES = [
    "https://iptv-epg.org/files/epg-nl.xml.gz",
    "https://iptv-epg.org/files/epg-gb.xml.gz",
    "https://iptv-epg.org/files/epg-de.xml.gz",
    "https://iptv-epg.org/files/epg-es.xml.gz",   # DAZN LaLiga
    "https://iptv-epg.org/files/epg-pl.xml.gz",   # Polsat
    "https://iptv-epg.org/files/epg-il.xml.gz",   # Sport 4 / 5
]

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
            root_out.append(prog)

xml_bytes = ET.tostring(root_out, encoding="utf-8", xml_declaration=True)
with open("epg.xml", "wb") as f:
    f.write(xml_bytes)
with gzip.open("epg.xml.gz", "wb") as f:
    f.write(xml_bytes)

print(f"Done. Channels found: {sorted(seen_channels)}")
print(f"Total programmes: {len(root_out.findall('programme'))}")
