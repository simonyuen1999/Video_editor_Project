# Simon's Working Note — Media Archive Audit & Repair Plan

**Status date:** 2026-11-01
**Scope:** 2025 Hong Kong / China trip archive (Mar 17 – May 25, 2025)
**Status:** Audit complete. No repair has been performed yet. This document is the pre-change baseline.

> Everything marked **[verified]** was measured by reading the files or querying the DB on 2026-11-01.
> Everything marked **[assumed]** comes from Simon's recollection and has not been independently proven.

---

## 1. Purpose

This note records:

1. What actually lives in each of the four media directories.
2. Simon's copy / collect / delete assumptions, and whether the evidence supports them.
3. The current state of every file as of 2026-11-01 — what is trustworthy and what is damaged.
4. The Phase 0–5 repair plan.

---

## 2. The four directories

All four sit on `/Volumes/SSD_HD` (exFAT, 3.6 TB, ~1.9 TB free).

| ID | Path | Role | Real files | Size (du) | Structure |
|----|------|------|-----------:|----------:|-----------|
| **C** | `/Volumes/SSD_HD/Keep_Media_files/2025HKTrip_Organized_from_Original` | Pristine curated master | 3,235 | 290 GB | 23 hand-named folders, flat, **files renamed** |
| **B** | `/Volumes/SSD_HD/Keep_Media_files/Videos_Original_Inc_Simon_iPhone` | Raw archive (C + other people's media + LRF) | 4,410 | 378 GB | 31 folders, original names |
| **A** | `/Volumes/SSD_HD/Keep_Media_files/testing_media_dir_2025-Nov-18` | Processed / scanned / de-duplicated working copy | 3,403 | 293 GB | same 31 folders as B |
| **D** | `/Volumes/SSD_HD/media` | **Duplicate of A** (no `*.db`) — configured `base_directory` in the DB | 3,401 | 293 GB | same as A |

### 2.1 File inventory [verified]

| Extension | A | B | C |
|-----------|---:|---:|---:|
| HEIC | 2,068 | 2,220 | 2,055 |
| MP4 | 945 | 945 | 896 |
| JPG | 192 | 123 | 102 |
| MOV | 108 | 109 | 91 |
| PNG | 88 | 115 | 91 |
| LRF (DJI proxies) | 0 | 897 | 0 |
| INI / DB | 2 (`.db`) | 1 | 0 |
| **Total real files** | **3,403** | **4,410** | **3,235** |
| AppleDouble `._*` junk | **1,689** | 174 | 0 |

Logical byte totals: A = 310.9 GB, B = 403.2 GB (incl. 91.9 GB LRF), C = 309.8 GB.

### 2.2 What each tree really is [verified]

**C — pristine master.** Files were **renamed** to Chinese descriptive names (`香港_1.HEIC`, `台灣_1.MP4`, `長洲太平清醮_3.HEIC`, `東莞家族晚餐_Menu3.HEIC`). No Zulu `UserComment` was written. 97 files carry Apple's own `UserComment` ("Screenshot"). 1,612 of 3,235 have GPS. Folder set is a hand-curated regrouping, so **path and filename do not align with A or B** — matching must be by content.

> Note: C is *not* perfectly untouched. 21 of its 3,235 files are not byte-identical to anything in B; at least one (`00_2025_iPhone/IMG_8262.HEIC`) has different rotation metadata. Treat C as "best available original", not "certified untouched".

**B — raw archive.** A superset of C: 3,214 of C's 3,235 files match a B file exactly on size + mtime (3,212 also match mtime within 2 s). B adds 1,097 items: 897 LRF sidecars, 152 HEIC, 27 PNG, 19 JPG, 1 MOV, `desktop.ini`. Contains the DJI `.LRF` proxies that C and A do not.

**A — processed working copy.** Produced by `PreImport_exif_file_processor.py` + the scan pipeline, then manually pruned. Same 31 folders as B, extensions upper-cased, 88 `.HEIC`→`.JPG` corrections, `UserComment` stamped on every file, GPS written into 1,604 files, all mtimes rewritten to Nov 2025, 1,689 AppleDouble files created, and the two `*.db` files copied into the root.

**D — `/Volumes/SSD_HD/media`.** Same 3,401 media files as A with identical relative paths and identical sizes; the only difference is A additionally holds `media_organizer.db` and `media_library.db`. Different inodes → a real second copy, not a symlink. **This is ~293 GB of duplication** and is the path recorded in `config.base_directory`.

---

## 3. Simon's assumption vs. the evidence

### What Simon said [assumed]

> C holds my own original media. I duplicated C to B, then collected other people's media into B. I copied B to A. I ran the scan programs against A, then manually removed LRF files and removed duplicate/useless files from A. A should therefore hold the minimal set. Their creation time and Geo may not be correct.

### What the evidence says [verified]

| Assumption | Verdict | Evidence |
|---|---|---|
| C is Simon's own original set | ✅ supported | C ⊂ B on content; all C names are Simon-style Chinese descriptive names |
| B = C + other people's media | ✅ supported | 3,214/3,235 C files found in B; B adds 165 HEIC / 27 PNG / 19 JPG / 1 MOV beyond C |
| A = copy of B | ✅ supported | 3,354 shared folder+stem items; A holds nothing B lacks except the 2 DB files |
| Scan programs modified A | ✅ confirmed | `UserComment` on 3,401/3,401; GPS added to 1,604 files; all mtimes → Nov 2025 |
| LRF files removed from A | ✅ confirmed | 897 LRF in B (91.9 GB), 0 in A |
| Duplicates / useless files removed from A | ⚠️ **only partly true** | 111 media files (328.9 MB) were removed, but **none of them is a content duplicate of anything left in A**. They were unique files. |
| A is the minimal set | ❌ not quite | A keeps 3,401 media items; C's curated set is 3,235. Also A is duplicated in full at `/Volumes/SSD_HD/media`. |
| A's creation times / Geo may be wrong | ✅ **confirmed, and quantified below** | 1,597 of 3,401 stamped timestamps are provably wrong |

### 3.1 What was actually deleted from A

111 media files, 328.9 MB: **64 HEIC, 27 PNG, 19 JPG, 1 MOV**.

| Folder | Count | Nature |
|---|---:|---|
| `Orders` | 52 | receipts, screenshots, document photos |
| `Captures` | 17 | iOS screenshots |
| `HK_Bank` | 8 | screenshots |
| `01_2025Mar香港` | 7 | travel photos |
| `Miu_iPhone/202505` | 6 | photos |
| `05_2025Apr深圳` | 5 | mixed |
| `iPhone` | 4 | incl. a 135 MB screen recording |
| others (12 folders) | 12 | mixed |

- 96 of the 111 are still preserved in **C**.
- **15 exist nowhere but B** (41.0 MB) — see §7.

---

## 4. Method

1. Full inventory of all four trees (path, size, mtime) → `/tmp/inv.json`.
2. Set comparison by folder + stem (case- and extension-normalised), then by content.
3. **Content verification of every shared item:**
   - Video → MD5 of the `mdat` payload / `ffmpeg -c copy -f md5` (ignores container metadata).
   - Image → MD5 of decoded RGB pixels (ignores EXIF).
   - Result file: `/tmp/content_verify.jsonl` (3,354 records).
4. Metadata survey with `exiftool -j -G1` over all 3,401 files → `/tmp/rich_A.json`.
5. Cross-checks against independent in-file sources (`GPSDateTime`, `Keys:CreationDate`, filename clock).
6. DB introspection with `sqlite3`.

> The scratch artifacts under `/tmp` (`inv.json`, `rich_A.json`, `content_verify.jsonl`) are regenerable and may not survive a reboot; Phase 1 rebuilds an equivalent, permanent ledger inside the project.

**Known false positive, corrected:** an initial pass flagged 11 Shenzhen MP4s as content-different. Cause was pairing a Live Photo's `.MP4` against its sibling `.HEIC`. After pairing by extension: **48/48 MP4 payloads and 97/97 images identical**.

---

## 5. Current status as of 2026-11-01

### 5.1 Content integrity — CLEAN

**All 3,354 media items shared between A and B have identical content.** No re-encoding, no resizing, no quality loss anywhere. A is a pure metadata rewrite of B.

### 5.2 The critical reassurance

**No original capture timestamp was ever modified.** `QuickTime:CreateDate` is byte-for-byte unchanged in **3,313 / 3,313** shared files. Only a new `UserComment` field was added. Every file still contains its own ground truth.

### 5.3 Metadata written into A

| Change | Scope |
|---|---|
| `UserComment` = UTC Zulu (`YYYY-MM-DDTHH:MM:SSZ`) | 3,401 / 3,401 |
| GPS coordinates written into the file (XMP for video, EXIF for stills) | **+1,604** files (3,223 with GPS vs 1,619 in B; 0 lost) |
| Extension case normalised to upper case | all |
| Real-type correction `.HEIC` → `.JPG` (iOS had mislabelled JPEG data) | 88 (`Shenzhen_2025`) |
| `FileModifyDate` overwritten | 3,401 / 3,401 → all `2025-11-17/18` |
| AppleDouble `._*` junk created | 1,689 |
| DB files copied into root | `media_organizer.db`, `media_library.db` |

### 5.4 Timestamp damage — 1,597 provably wrong

Each stamped `UserComment` compared against the file's own authoritative source:

| Type | Files | Stamped correct | **Provably wrong** | Unverifiable | Error pattern |
|---|---:|---:|---:|---:|---|
| HEIC | 2,068 | 1,530 | **538** | 0 | **+12 h** (all `Miu_iPhone` + 94 in `Shenzhen_2025`) |
| JPG | 192 | 28 | **95** | 69 | **+12 h** (every one exactly 43,200 s) |
| MOV | 108 | 88 | **20** | 0 | **+4 h ×19** (all in `Shenzhen_2025`), +51 days ×1 (`63.MOV`), −16 min ×1 (screen recording) |
| MP4 | 945 | 1 | **944** | 0 | **end-of-clip, not start**: median +51 s, p90 330 s, max 14,400 s |
| PNG | 88 | 0 | 0 | 88 | no timezone in file — cannot validate |
| **Total** | **3,401** | **1,647** | **1,597** | **157** | |

### 5.5 GPS damage — mild

| Metric | Count |
|---|---:|
| Files with GPS before (B) | 1,619 |
| Files with GPS after (A) | 3,223 |
| GPS added | **+1,604** |
| Original GPS preserved untouched | **1,602 / 1,619** |
| Original GPS **modified** (needs review) | **17** (e.g. `IMG_8925`: 30°14'54.16"N → 30°14'54.75"N, ≈18 m) |
| GPS lost | 0 |

### 5.6 Device and file-type inventory [verified]

| Source | Files | Reliable time field | Reliable GPS field |
|---|---:|---|---|
| iPhone 15 Plus (Simon) | **1,619** (1,528 HEIC + 88 MOV + 3 JPG) | `DateTimeOriginal`+`OffsetTimeOriginal`; `Keys:CreationDate` | EXIF GPS; `Keys:GPSCoordinates` |
| iPhone 13 (wife, `Miu_iPhone`) | **587** (538 HEIC + 49 JPG) | `DateTimeOriginal`+`OffsetTimeOriginal` (all `+08:00`) | EXIF GPS |
| iPhone 15 | **54** (40 JPG + 14 MOV) | as above | as above |
| iPhone 8 Plus | **2** HEIC | as above | as above |
| Samsung Galaxy A54 5G | **6** JPG | EXIF | EXIF |
| DJI Pocket 3 (`PP-101`) | **949** (945 MP4 + 4 JPG) | `QuickTime:CreateDate` = **UTC** | **none** |
| No model (screenshots / exports) | **184** (90 JPG + 88 PNG + 6 MOV) | none reliable | rarely |
| **Total** | **3,401** | | |

Timezone offsets found: **+08:00 on 2,189 files**, **−04:00 on 2 files only** (`Captures/IMG_0217.HEIC`, `Captures/IMG_0218.HEIC`, 2025-05-25 — after returning to Toronto). 2,191 files carry an EXIF offset in total; the other 1,210 do not (945 MP4 + 108 MOV + 88 PNG + 69 JPG — MP4/MOV carry their time in the container instead).

### 5.7 Independent verification of the good data

| Check | Sample | Result |
|---|---|---|
| HEIC `DateTimeOriginal`+offset vs **GPS satellite time** (`GPSDateTime`) | 1,515 | median **1.0 s**, p99 18 s, 1,505 within 30 s, 4 outliers > 60 s |
| Own phone vs wife's phone, same day, median latitude | 47 shared days | **40 days within 0.05°** (≈5 km); remainder = different parts of the same city |
| MOV `QuickTime:CreateDate` vs `Keys:CreationDate` | 103 | **97 exact**; 6 inconsistent |
| DJI filename clock vs `QuickTime:CreateDate` | 8 samples, Mar 16 – May 20 | **constant +4:00** → filename = Toronto local, CreateDate = UTC |

**Conclusion:** the iPhone's own EXIF time and GPS are trustworthy — on **both** phones. Only the data our program stamped over them is wrong.

### 5.8 Known outliers requiring manual review

| File | Problem |
|---|---|
| `IMG_8186.HEIC` | EXIF time is 84 min later than GPS satellite time |
| `IMG_8450.HEIC`, `IMG_8451.HEIC`, `IMG_9209.HEIC` | 62–95 s later than GPS satellite time |
| `05_2025Apr深圳/63.MOV` | `QuickTime:CreateDate` and `Keys:CreationDate` differ by **51 days** |
| `IMG_8291.MOV`, `IMG_8460.MOV`, `IMG_8888.MOV`, `IMG_8889.MOV`, `IMG_8943.MOV` | internal timestamps differ by 5–100 min |
| All 19 `Shenzhen_2025/*.MOV` | stamped 4 hours late (double-applied −04:00 offset); originals are correct in `Keys:CreationDate` |
| `ScreenRecording_04-10-2025 13-41-35_1.MOV` | stamped −944 s vs authority |

### 5.9 Database contents

**`/Users/syuen/Video_editor_Project/Vacaction_Media_Org/media_organizer.db`** (the one the web app uses — see `media_library_web/src/main.py`, which points at the repo root):

| Table | Rows | Rebuildable? |
|---|---:|---|
| `journal` | 74 (65 with text) | ❌ **irreplaceable — Simon's diary** |
| `geo_data` | 4,823 | ✅ exact 1:1 copy of `geo_chinese.list` (verified: 0 rows differ either way) |
| `config` | 4 | ✅ trivial |
| `media_files` | 3,401 | ✅ rebuild from a ledger |

`config` values: `OffsetTime = +08:00`, `TimeZone = Asia/Hong_Kong`, `base_directory = /Volumes/SSD_HD/media`, `thumb_directory = /Volumes/SSD_HD/media_thumb`.

`media_files` path column is **relative** (e.g. `01_2025Mar香港/DJI_….MP4`), resolved against `base_directory`.

GPS provenance recorded in `media_files`:

| Media | `hasGPS` | `shareGPS` | Count | Meaning |
|---|---:|---:|---:|---|
| Image | 1 | 0 | 1,499 | native EXIF GPS |
| Image | 0 | 1 | 696 | inherited from a neighbour |
| Image | 0 | 0 | 135 | no location |
| Image | 1 | 1 | 18 | both flags set (anomaly) |
| Video | 0 | 1 | 955 | inherited |
| Video | 1 | 0 | 96 | set manually via FixInfo |
| Video | 1 | 1 | 2 | both flags set (anomaly) |

**`media_library.db`** is a near-empty legacy database (`journal` 2 rows, `media` 2 rows). Safe to ignore.

> ⚠️ Chinese city names in `geo_chinese.list` are machine transliterations with errors, e.g. `Wanning → 减弱` (should be 万宁), `Wuzhen → 武恩` (should be 烏鎮), `Lanyang → 兰南`. Cosmetic, but worth a separate cleanup.

### 5.10 Root causes (code)

| Symptom | Cause | Location |
|---|---|---|
| 633 stills +12 h wrong | Uses the **file's** `FileInodeChangeDate` offset as if it were the capture timezone. Files copied in Toronto (−04:00) had that offset applied to Asia (`+08:00`) wall-clock times. | `calculate_creation_time()`, `PreImport_exif_file_processor.py:468` |
| MOV +4 h | Same bug applied to `QuickTime:CreateDate`, which is already UTC | same |
| MP4 end-of-clip | Falls back to file mtime (written when the clip closes) instead of `QuickTime:CreateDate` | same |
| PNG unverifiable | No timezone exists in PNG; whatever offset is applied is invented | same |
| Videos `+duration` in DB | `metadata_extractor.py` prioritises `UserComment`, which is already wrong | `metadata_extractor.py:865` |
| One global display offset | `+08:00` applied to every row regardless of where it was shot | `media_library_web/src/routes/media.py:179` |

**The correct authority per file type — always prefer these over mtime:**

| Type | UTC from |
|---|---|
| HEIC / JPG | `EXIF:DateTimeOriginal` + `EXIF:OffsetTimeOriginal` |
| MOV | `Keys:CreationDate` (has offset) → `QuickTime:CreateDate` (UTC) |
| MP4 | `QuickTime:CreateDate` (UTC) |
| PNG / unknown | **none** — mark as unknown, never guess |

---

## 6. Answers to the four questions

1. **Can iPhone HEIC time and GPS be trusted?** Yes, on both phones. 100% of 2,068 HEICs carry `DateTimeOriginal` + `OffsetTimeOriginal`; GPS exists on 2,059. Cross-checked against GPS satellite time: median error 1 second. The wife's phone is equally reliable — its original EXIF is intact; only our stamp is wrong.
2. **Can JPG / MOV be trusted?** MOV yes (97/103 internally consistent, 108 with UTC container time, 98 with GPS); 6 files need triage. JPG partly — 123 of 192 carry a timezone, 152 carry GPS; the other ~65 are screenshots or exports with no usable time.
3. **The MP4 modifications need rework?** Yes — 944 of 945 stamps are end-of-clip rather than start. But the fix is safe: the untouched `QuickTime:CreateDate` still holds the true start time in every file.
4. **Is the DB at risk?** No. `geo_data` is a byte-equivalent copy of `geo_chinese.list`; only the 74-row `journal` is irreplaceable and needs an export before any rebuild.

---

## 7. Files that exist only in B (at risk)

15 files, 41.0 MB. Present in B; absent from A and from C.

```
01_2025Mar香港/IMG_8183.HEIC        3,005,197
01_2025Mar香港/IMG_8189.HEIC        3,196,541
01_2025Mar香港/IMG_8190.HEIC        2,325,927
01_2025Mar香港/IMG_8191.HEIC        2,354,540
01_2025Mar香港/IMG_8235.HEIC        2,601,412
01_2025Mar香港/IMG_8320.HEIC        2,613,098
05_2025Apr深圳/IMG_8294.PNG           629,590
05_2025Apr深圳/IMG_8295.HEIC        2,504,065
10_2025Apr東莞/IMG_8566.HEIC        2,999,075
40_2025Apr_/IMG_9062.PNG            4,225,508
Miu_iPhone/202505/IBHS3955.JPG      2,165,124
Miu_iPhone/202505/IMG_1836.HEIC     2,334,021
Miu_iPhone/202505/IMG_1903.HEIC     2,909,484
Miu_iPhone/202505/IMG_1907.HEIC     1,783,300
iPhone/IMG_9748.HEIC                5,319,456
```

**B must not be deleted until these 15 are restored to C or A.**

---

## 8. Repair plan

### Guiding principles

1. **B and C are read-only.** No process may write to them.
2. **Never re-run PreImport against A.** A's mtimes are destroyed, so any recomputation is guaranteed wrong.
3. **The files already hold the truth.** Repair means *reading* the authoritative field and *replacing derived data*, not inventing values.
4. **Derived data belongs in the DB, not in the media files.** Inheritance and manual corrections should live in SQLite; files should stay as the camera wrote them.
5. **Every derived value carries provenance and confidence.**

---

### Phase 0 — Freeze and back up

- [ ] Make `/Volumes/SSD_HD/Keep_Media_files/Videos_Original_Inc_Simon_iPhone` (B) and `…/2025HKTrip_Organized_from_Original` (C) read-only; never write to them.
- [ ] `sqlite3 media_organizer.db ".backup media_organizer.db.2026-11-01.bak"`
- [ ] Export the journal: `sqlite3 media_organizer.db ".mode insert journal" "SELECT * FROM journal;" > journal_export_2026-11-01.sql`
- [ ] Snapshot `geo_chinese.list` checksum (it is the true source of `geo_data`).
- [ ] Stop running `PreImport_exif_file_processor.py` and `Main_scan_media.py` against A or D.
- [ ] Decide the fate of D (`/Volumes/SSD_HD/media`, 293 GB duplicate of A).

**Exit criteria:** backups exist and verify; B and C untouched; no pipeline runs scheduled.

---

### Phase 1 — Build the ledger (read-only, changes nothing)

Create `build_media_ledger.py` producing `media_ledger` (SQLite table + CSV export), one row per media file in A:

| Column | Rule |
|---|---|
| `relpath`, `ext`, `size`, `device` | from the filesystem + EXIF `Make`/`Model` |
| `capture_utc` | HEIC/JPG: `DateTimeOriginal` + `OffsetTimeOriginal` · MOV: `Keys:CreationDate` → `QuickTime:CreateDate` · MP4: `QuickTime:CreateDate` · PNG: `NULL` |
| `time_source` | `exif_offset` / `keys` / `quicktime` / `filename` / `unknown` |
| `time_confidence` | `high` / `medium` / `unknown` |
| `lat`, `lon` | EXIF GPS → `Keys:GPSCoordinates` → `NULL` |
| `geo_source` | `exif` / `keys` / `inherited:<file>` / `manual` / `none` |
| `old_usercomment` | the current (often wrong) stamp, kept for audit |
| `stamp_error_s` | `old_usercomment − capture_utc` in seconds |

Expected outcome: **3,244 files with authoritative UTC** (2,068 HEIC + 123 JPG + 108 MOV + 945 MP4) and **157 unknown** (88 PNG + 69 JPG). For GPS: **1,619 native** coordinates survive from the originals; the remaining ~1,650 currently hold inherited or hand-entered values that must be re-derived (see Phase 3) rather than trusted. Note the DB and the files are slightly out of sync — files show 3,223 with GPS, the DB's own flags imply 1,615 native + 1,651 inherited + 135 none — which is one more reason to rebuild from a single ledger.

**Exit criteria:** Simon reviews the CSV and agrees with the counts. Nothing on disk has changed.

---

### Phase 2 — Restore files that should never have changed

**2a. 6 internally inconsistent MOVs** — copy back from B:

```
05_2025Apr深圳/63.MOV
05_2025Apr深圳/IMG_8291.MOV
05_2025Apr深圳/IMG_8460.MOV
25_2025Apr上海/IMG_8888.MOV
25_2025Apr上海/IMG_8889.MOV
40_2025Apr_/IMG_8943.MOV
```

**2b. 17 photos whose original EXIF GPS was overwritten** — copy back from B (their original coordinates are intact there):

| File | Original (B) | Currently in A |
|---|---|---|
| `IMG_8240.HEIC` | 22°17'23.96"N | 22°17'21.28"N |
| `IMG_8241.HEIC` | 22°17'23.96"N | 22°17'21.28"N |
| `IMG_8297.HEIC` | 22°17'04.10"N | 22°16'39.79"N (≈750 m) |
| `IMG_8446.HEIC` | 22°32'37.79"N | 22°32'38.73"N |
| `IMG_8447.HEIC` | 22°32'35.89"N | 22°32'38.73"N |
| `IMG_8793.HEIC` | 31°14'16.03"N | 31°06'26.94"N (**≈14 km**) |
| `IMG_8925.HEIC` | 30°14'54.16"N | 30°14'54.75"N |
| `IMG_8926.HEIC` | 30°14'53.50"N | 30°14'54.75"N |
| `IMG_8952.HEIC` | 31°54'55.59"N | 31°54'56.10"N |
| `IMG_8953.HEIC` | 31°54'55.46"N | 31°54'56.10"N |
| `IMG_8954.HEIC` | 31°54'55.46"N | 31°54'56.10"N |
| `IMG_8955.HEIC` | 31°54'55.46"N | 31°54'56.10"N |
| `IMG_9135.HEIC` | 30°41'12.19"N | 30°41'11.61"N |
| `IMG_9136.HEIC` | 30°41'11.97"N | 30°41'11.61"N |
| `IMG_9149.HEIC` | 30°41'17.03"N | 30°41'11.61"N |
| `IMG_9233.HEIC` | 31°14'16.49"N | 31°14'16.59"N |
| `IMG_9234.HEIC` | 31°14'16.47"N | 31°14'16.59"N |

Most are tens of metres — consistent with "snap to saved location" bulk edits. `IMG_8793` (14 km) and `IMG_8297` (750 m) look like genuine mistakes and must be reverted. **Confirm with Simon before reverting the small ones**, which may be deliberate corrections.

**2c. 15 files that currently exist only in B** (§7) — restore into C first, then into A.

**Exit criteria:** A's GPS values match B's for every file that had GPS in B (or a documented, deliberate override is recorded); the 15 orphans are preserved in at least two locations.

---

### Phase 3 — Fix the derived metadata

**Decision required from Simon — choose one:**

- **Option 1 (recommended): files stay as the camera wrote them.** Strip the program-written `UserComment` and the program-added GPS. All derived values live in the DB only. Cleanest for archival integrity.
- **Option 2 (PhotoPrism-friendly): rewrite `UserComment` with the *correct* UTC** from the ledger, and keep GPS in files only where the source is `exif` or `manual` (not `inherited`).

For the 945 DJI clips, re-run GPS inheritance properly:

- [ ] Match on **clip start UTC**, not end.
- [ ] Hard window 20 min; widen to 45 min only if no candidate exists.
- [ ] Require a geo-tagged photo **before and after** the clip that agree within 1 km; otherwise mark `confidence = low`.
- [ ] Reject any match implying travel > 300 km/h versus the previous confirmed anchor.
- [ ] Fall back to the day's location cluster (majority vote) rather than a single nearest photo.
- [ ] Manually review the 96 clips with `hasGPS=1` (manual entries) and the 142 clips whose coordinates match no photo.

**Exit criteria:** 0 timestamp stamps provably disagree with `capture_utc`; every inherited coordinate carries a confidence label.

---

### Phase 4 — Rebuild the DB

- [ ] Preserve `journal` (74 rows) and `config` (4 rows).
- [ ] Verify `geo_data` still equals `geo_chinese.list`; then reload it to be safe.
- [ ] Recreate `media_files` from `media_ledger`, adding: `capture_utc`, `time_source`, `time_confidence`, `geo_source`, `geo_confidence`.
- [ ] Keep `creation_time` as the UTC string the web app expects, so **no front-end change is needed**.
- [ ] Fix the display logic: convert each row using its **own** `timezone` (from `geo_data`), falling back to `config.OffsetTime` only when the row has none.

**Exit criteria:** the web pages render identically to today for Asia-shot media, and Toronto-shot media now display in Toronto time instead of being shifted to +08:00.

---

### Phase 5 — Prove the repair

Re-run these checks and require:

| Check | Acceptance |
|---|---|
| HEIC `DateTimeOriginal`+offset vs `GPSDateTime` | median < 2 s; report any file > 60 s |
| MOV `QuickTime:CreateDate` vs `Keys:CreationDate` | 0 mismatches (or all documented) |
| MP4 filename clock + 4:00 vs `QuickTime:CreateDate` | 0 mismatches |
| `UserComment` (if retained) vs `capture_utc` | 0 mismatches |
| Content hash A vs B | still 3,354/3,354 identical |
| Row count | `media_files` = `media_ledger` = actual file count |
| Journal | 74 rows, byte-identical text to the Phase 0 export |
| Web UI spot-check | 10 known dates display the expected local times and locations |

---

## 9. Open decisions

| # | Decision | Options |
|---|---|---|
| 1 | What to do with `/Volumes/SSD_HD/media` (D, 293 GB duplicate) | keep as scan target · delete · make it the only working copy |
| 2 | Phase 3 option | leave files untouched (Option 1) vs write corrected UTC+GPS for PhotoPrism (Option 2) |
| 3 | Keep or drop the 88 PNG screenshots and ~65 JPGs with no usable date | drop · keep in a separate `Screenshots/` folder |
| 4 | Rename strategy for A | keep original camera names · adopt C's Chinese descriptive names |
| 5 | Whether to clean the machine-translated Chinese city names in `geo_chinese.list` | now · later · never |

---

## 10. Reference — commands used

```bash
# inventory (path, size, mtime)
find "$DIR" -type f ! -name ".*" -exec stat -f '%N|%z|%m' {} +

# authoritative time, per file type
exiftool -j -G1 -FileName -Make -Model \
  -EXIF:DateTimeOriginal -EXIF:OffsetTimeOriginal \
  -QuickTime:CreateDate -Keys:CreationDate \
  -EXIF:GPSLatitude -EXIF:GPSLongitude -Keys:GPSCoordinates \
  "$FILE"

# video content check (ignores container metadata)
ffmpeg -v error -i "$FILE" -map 0 -c copy -f md5 -

# DJI reality check: filename clock is Toronto local, CreateDate is UTC
exiftool -s3 -CreateDate "$DJI_MP4"      # 2025:03:20 08:39:32
# filename DJI_20250320043931 → 04:39:31 local (UTC-4) → 08:39:31Z  (+4:00)

# DB integrity
sqlite3 media_organizer.db "SELECT media_type,hasGPS,shareGPS,COUNT(*) FROM media_files GROUP BY 1,2,3;"
sqlite3 media_organizer.db ".backup media_organizer.db.bak"
```

---

*End of note. Next action: Simon reviews Phase 1's expected counts and answers the Open Decisions, then implementation begins.*
