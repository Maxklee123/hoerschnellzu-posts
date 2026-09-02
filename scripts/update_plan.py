import os, json, glob
from google.oauth2 import service_account
from googleapiclient.discovery import build

SID = "1A6nGdOTinZFi4foVFIWaAEAQ_x-H_DxeKsVoAgfd4M8"
creds = service_account.Credentials.from_service_account_info(
    json.loads(os.environ["GOOGLE_SA_KEY"]),
    scopes=["https://www.googleapis.com/auth/spreadsheets"])
svc = build("sheets", "v4", credentials=creds).spreadsheets().values()

def get(rng):
    return svc.get(spreadsheetId=SID, range=rng).execute().get("values", [])

tl = get("Themenlog!A1:I2000")
cfg = get("Config!A2:G50")
name_by = {c[0].strip().lower(): c[1] for c in cfg if c and len(c) > 1}

info = {}
for row in tl[1:]:
    if len(row) > 4 and row[4].strip():
        f = row[4].strip()
        info[f] = {
            "datum": row[0] if len(row) > 0 else "",
            "podcast": row[2] if len(row) > 2 else "",
            "titel": row[3] if len(row) > 3 else "",
            "status": row[6] if len(row) > 6 else "",
            "link": row[7] if len(row) > 7 else "",
        }

def status_label(s):
    s = (s or "").lower()
    if "bersprungen" in s:
        return "⏭️ uebersprungen"
    if "gepostet" in s or "bereitgestellt" in s:
        return "✅ gepostet"
    return "⬜ offen"

def title_of(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            line = fh.readline().strip()
    except Exception:
        return ""
    low = line.lower()
    for pre in ("video title:", "episode title:"):
        if low.startswith(pre):
            return line.split(":", 1)[1].strip()
    return line

files = sorted(os.path.basename(p) for p in glob.glob("transcripts/*.txt"))
rows = [["Nr", "Datum", "Podcast", "Folgentitel", "Transkript-Datei", "Status", "Link/PDF"]]
for n, f in enumerate(files, 1):
    kennung = f.rsplit("_", 1)[1].replace(".txt", "")
    if f in info:
        i = info[f]
        podcast = i["podcast"] or name_by.get(kennung.lower(), kennung)
        rows.append([n, i["datum"], podcast, i["titel"], f, status_label(i["status"]), i["link"]])
    else:
        rows.append([n, "", name_by.get(kennung.lower(), kennung), title_of("transcripts/" + f), f, "⬜ offen", ""])
while len(rows) < 150:
    rows.append([""] * 7)

svc.update(spreadsheetId=SID, range="Plan!A1:G%d" % len(rows),
           valueInputOption="USER_ENTERED", body={"values": rows}).execute()
print("Plan updated:", len(files), "episodes")
