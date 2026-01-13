# C: Drive Space Analysis and Cleanup Report

## Executive Summary

Analysis of the WizTree scan reveals **WSL (Windows Subsystem for Linux) is consuming 156.5 GB** - accounting for **64.5% of the scanned space** under AppData\Local. The remaining ~86 GB is distributed across developer tools, AI models, temp files, and application caches. This report provides actionable cleanup strategies prioritized by potential space recovery.

## Table Summary

| Category | Size (GB) | % of Total | Recovery Priority | Effort |
|----------|-----------|------------|-------------------|--------|
| WSL Virtual Disk | 156.5 | 64.5% | HIGH | Medium |
| Microsoft (Teams, Office, etc.) | 20.6 | 8.5% | LOW | Low |
| Packages (Windows Store) | 14.8 | 6.1% | LOW | Low |
| Programs | 12.5 | 5.2% | LOW | Low |
| nomic.ai (AI models) | 10.5 | 4.3% | MEDIUM | Low |
| Temp Files | 6.2 | 2.5% | HIGH | Low |
| uv cache (Python) | 5.3 | 2.2% | MEDIUM | Low |
| pip cache | 3.3 | 1.4% | MEDIUM | Low |
| Google Chrome | 2.9 | 1.2% | LOW | Low |
| SquirrelTemp | 2.1 | 0.9% | HIGH | Low |
| Ollama (local LLMs) | 1.2 | 0.5% | MEDIUM | Low |
| Other | ~7 | 2.7% | LOW | - |
| **TOTAL SCANNED** | **242.6** | **100%** | - | - |

## Relevant Files

- `app/tests/assets/samples/WizTree_20251223105843.csv` - WizTree disk scan export showing space consumption under `C:\Users\johnw\AppData\Local\`

## WSL: The Primary Culprit (156.5 GB)

WSL2 uses a VHDX (virtual hard disk) file that **grows automatically but never shrinks** when you delete files inside Linux. Your WSL disk is located at:
```
C:\Users\johnw\AppData\Local\wsl\
```

### Why WSL Takes So Much Space

1. **VHDX files only grow, never auto-shrink** - Deleted files inside WSL don't release space back to Windows
2. **Docker images** - If running Docker in WSL, images accumulate in the VHDX
3. **npm/pip packages** - Development dependencies installed inside WSL
4. **Git repositories** - Cloned repos with full history

### How to Reclaim WSL Space (Step-by-Step)

**Step 1: Clean up inside WSL first** (run inside your Linux terminal)
```bash
# Remove unused apt packages
sudo apt autoremove -y
sudo apt clean

# Clear pip cache
pip cache purge

# Clear npm cache (if using npm)
npm cache clean --force

# If using Docker
docker system prune -a

# CRITICAL: Run fstrim to mark deleted blocks as free
sudo fstrim /
```

**Step 2: Shut down WSL** (run in PowerShell as Admin)
```powershell
wsl --shutdown
```

**Step 3: Compact the VHDX** (run in Admin PowerShell)

Option A - Using Optimize-VHD (requires Hyper-V):
```powershell
Optimize-VHD -Path "C:\Users\johnw\AppData\Local\wsl\docker-desktop-data\ext4.vhdx" -Mode Full
```

Option B - Using DiskPart (works on Windows Home):
```cmd
diskpart
select vdisk file="C:\Users\johnw\AppData\Local\wsl\docker-desktop-data\ext4.vhdx"
attach vdisk readonly
compact vdisk
detach vdisk
exit
```

**Expected Recovery: 20-80 GB** depending on how much unused space is in the VHDX.

### Alternative: Move WSL to Another Drive

If you have a D: drive with more space, you can export and import WSL to a different location:
```powershell
wsl --export Ubuntu ubuntu-backup.tar
wsl --unregister Ubuntu
wsl --import Ubuntu D:\WSL\Ubuntu ubuntu-backup.tar
```

## Quick Wins: Immediate Space Recovery

### 1. Clear Temp Files (6.2 GB)

**Windows GUI Method:**
- Open Settings > System > Storage > Temporary files
- Select all safe categories and click "Remove files"

**PowerShell Method:**
```powershell
Remove-Item -Path "$env:TEMP\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "C:\Windows\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue
```

### 2. Clear SquirrelTemp (2.1 GB)

This folder contains Electron app update packages (Discord, Slack, etc.):
```
C:\Users\johnw\AppData\Local\SquirrelTemp\
```
Safe to delete contents manually.

### 3. Clear Python Caches (8.6 GB combined)

**uv cache (5.3 GB):**
```powershell
uv cache clean
```

**pip cache (3.3 GB):**
```powershell
pip cache purge
```

### 4. npm cache (22 MB)

```powershell
npm cache clean --force
```

## AI/ML Model Storage (11.7 GB)

### nomic.ai (10.5 GB)
Contains local embeddings models for GPT4All. If not actively using:
- Delete `C:\Users\johnw\AppData\Local\nomic.ai\`

### Ollama (1.2 GB)
Local LLM storage. Clean unused models:
```powershell
ollama list
ollama rm <model-name>
```

## Windows Built-in Cleanup Tools

### Storage Sense (Recommended)
Enable automatic cleanup:
1. Settings > System > Storage
2. Turn on "Storage Sense"
3. Configure to run weekly or monthly
4. Enable cleanup of temporary files

### Disk Cleanup (Deep Clean)
```
cleanmgr /d C:
```
Select "Clean up system files" for additional options like:
- Windows Update Cleanup
- Previous Windows installations
- Delivery Optimization Files

## Recovery Summary by Category

| Action | Potential Recovery | Difficulty |
|--------|-------------------|------------|
| Compact WSL VHDX | 20-80 GB | Medium |
| Clear Temp files | 6.2 GB | Easy |
| Clear Python caches (uv + pip) | 8.6 GB | Easy |
| Clear SquirrelTemp | 2.1 GB | Easy |
| Delete nomic.ai (if unused) | 10.5 GB | Easy |
| Clear Ollama models | 1.2 GB | Easy |
| Windows Disk Cleanup | 5-15 GB | Easy |
| **TOTAL POTENTIAL** | **53-123 GB** | - |

## 2025 Best Practices

1. **Enable sparse VHD for WSL** - Add to `%USERPROFILE%\.wslconfig`:
   ```ini
   [experimental]
   sparseVhd=true
   ```
   This helps WSL auto-reclaim some space (not perfect but helps)

2. **Use wslcompact tool** - Automates VHDX compaction: https://github.com/okibcn/wslcompact

3. **Schedule monthly cleanup** - Set Storage Sense to run monthly

4. **Monitor with WizTree** - Run periodic scans to catch growth early

5. **Keep C: drive under 70% full** - Prevents performance degradation

## Simple List Summary

- **WSL is using 156.5 GB (64.5%)** - compact the VHDX after running `fstrim` inside WSL to recover 20-80 GB
- **Temp files (6.2 GB)** - clear via Settings > System > Storage > Temporary files
- **Python caches (8.6 GB)** - run `uv cache clean` and `pip cache purge`
- **SquirrelTemp (2.1 GB)** - safe to delete app update packages
- **AI models (11.7 GB)** - remove unused nomic.ai/Ollama models if not needed
- **Enable Storage Sense** - automate monthly cleanup
- **Total potential recovery: 53-123 GB**

## Sources

- [How to manage WSL disk space | Microsoft Learn](https://learn.microsoft.com/en-us/windows/wsl/disk-space)
- [Shrink your WSL2 Virtual Disks - Scott Hanselman](https://www.hanselman.com/blog/shrink-your-wsl2-virtual-disks-and-docker-images-and-reclaim-disk-space)
- [How to Shrink a WSL2 Virtual Disk - Stephen Rees-Carter](https://stephenreescarter.net/how-to-shrink-a-wsl2-virtual-disk/)
- [The Friendly Guide: Why WSL is Eating My C: Drive - DEV Community](https://dev.to/rasulmmdv/the-friendly-guide-why-wsl-is-eating-my-c-drive-and-how-to-get-it-back-15p8)
- [Free up drive space in Windows - Microsoft Support](https://support.microsoft.com/en-us/windows/free-up-drive-space-in-windows-85529ccb-c365-490d-b548-831022bc9b32)
- [12 best tips to free up hard drive space on Windows 11 - Windows Central](https://www.windowscentral.com/how-free-space-windows-11)
