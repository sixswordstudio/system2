# Code Review & Roadmap: DifferSnapper

**Author:** Victor (The Progenitor)
**Date:** 2026-02-03
**Subject:** Refactoring and Securing the Snapshot Tool

## 1. Security Breach (Fixed)
- **Issue:** Hardcoded credentials in `screenshotter.py`.
- **Fix:** Replaced with `os.getenv()`. Please set `ILC_USERNAME` and `ILC_PASSWORD` in your environment variables. Never commit secrets.

## 2. Architecture Cleanup (Untangling)
Currently, `DifferSnapperDev/` is a "Junk Drawer" containing three distinct projects:
1.  **DifferSnapper:** The screenshot tool (sitemapper.py, screenshotter.py).
2.  **Answermancer:** The text expander (Answermancer/).
3.  **Memery:** (The empty meme folder reference).

**Recommendation:**
- Move `Answermancer` to its own root repo (`~/Answermancer`).
- Rename `DifferSnapperDev` to `DifferSnapper` and remove the unrelated scripts.

## 3. The Missing Feature: The Diff
- **Current State:** The tool takes screenshots but does not compare them.
- **Next Step:** Implement `diff_images.py`.
    - Use `pixelmatch` (Node) or `Pillow/Chops` (Python) to overlay `screenshot_new.png` vs `screenshot_old.png`.
    - Generate a "Diff Report" (HTML) showing only changed pixels.

## 4. Performance Optimization
- **Current State:** `DifferSnapper.py` launches a browser for *every* page.
- **Fix:** Use a single browser instance (Context) for the whole session. (Already implemented in `sitemapper.py` - copy that logic to `screenshotter.py`).

---
*Signed,*
*Victor*
