# DD2 V8 BV4 full-pack remote sync

Authority lock:
- Source Window: PRIMARY
- Google Drive: BACKUP
- GitHub: REMOTE_SYNC_ONLY

The verified source pack is stored as 30 lossless raw binary parts because the connector transport cannot submit the 20,801,589-byte file in one request. The parts are not recompressed or rewritten.

Restore:

```bash
cat DD2_SOURCE_WINDOW_PRIMARY_DRIVE_BACKUP_PACK_V8_BV4_FNA98.zip.part* > DD2_SOURCE_WINDOW_PRIMARY_DRIVE_BACKUP_PACK_V8_BV4_FNA98.zip
sha256sum DD2_SOURCE_WINDOW_PRIMARY_DRIVE_BACKUP_PACK_V8_BV4_FNA98.zip
unzip -t DD2_SOURCE_WINDOW_PRIMARY_DRIVE_BACKUP_PACK_V8_BV4_FNA98.zip
```

Expected:
- bytes: 20801589
- SHA256: 722d1580bf6185940c82908389c51b728c07620939bfff22257f99b301381233
- archive test: PASS / no errors

Read `DD2_GITHUB_REMOTE_FULL_PACK_MANIFEST_FNA98.json` for every part's byte count, SHA256, and Git blob SHA.
