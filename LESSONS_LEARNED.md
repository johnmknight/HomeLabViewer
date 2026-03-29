# Critical Lessons Learned - HomeLabViewer Icon Upgrade
**Date:** 2026-03-29

## 1. Docker Deployment Architecture Matters

**Problem:** Changed file on server, container didn't update.

**Why:** Container had NO volume mounts - files baked into image at build time.

**Fix:** Must rebuild Docker image: `docker build -t homelabviewer:latest .`

**Always Check:** `docker inspect <container> | grep Mounts` before assuming file copy works.

**Prevention:**
- Development: Use volume mounts `-v /host/path:/container/path`
- Production: Baked images are fine, but document rebuild requirement

## 2. Multi-Layer Caching is Real

**Two independent cache layers:**
1. **Server-side:** Docker image cache (old files baked in)
2. **Client-side:** Browser cache (old HTML/CSS/JS cached)

**Both must be cleared:**
1. Server: Rebuild Docker image
2. Browser: Hard refresh (Ctrl+Shift+R)

**Debugging Tip:** Changes deployed but not visible = check BOTH layers.

## 3. edit_block > write_file for Large Files

**Problem:** write_file in "rewrite" mode truncated 843-line file.

**Why:** Easy to make mistakes with large content strings.

**Better:** Use `edit_block` for surgical edits:
- Safer (only changes what you specify)
- Clear diff on mismatch
- Git protects from disasters

**Rule of Thumb:**
- New files < 100 lines → write_file okay
- Existing files > 100 lines → use edit_block
- Critical production files → ALWAYS edit_block

## 4. SVG Icon Types Affect Conversion

**Stroke vs Fill:**
- Old icons: `fill="currentColor"`
- New icons: `stroke="currentColor"`

**Conversion function must match:**
```javascript
// WRONG (for stroke-based icons)
svg.replace(/fill="currentColor"/g, `fill="${color}"`)

// RIGHT (for stroke-based icons)  
svg.replace(/stroke="currentColor"/g, `stroke="${color}"`)
```

**Lesson:** Know your icon library's SVG structure before converting.

## 5. Deployment Verification is Multi-Step

**Don't just deploy and assume it worked.**

**Proper workflow:**
1. ✅ Local file correct: `git diff`
2. ✅ File on server: `ssh grep "unique string"`
3. ✅ File timestamp: `ssh ls -lh`
4. ✅ Container state: `docker ps`
5. ✅ Volume mounts: `docker inspect | grep Mounts`
6. ✅ Rebuild if needed: `docker build && run`
7. ✅ Browser test: Hard refresh (Ctrl+Shift+R)

**Each layer can fail independently!**

## 6. Industry Standards > Custom Everything

**Before:** 6 custom icons, purple/blue filled shapes  
**After:** 17 Tabler Icons, professional stroke-based

**Benefits:**
- Recognizable across applications
- MIT licensed (commercial use okay)
- Maintained by community
- Consistent design language
- Accessible & SVG-native

**Lesson:** Don't reinvent the wheel. Use established icon libraries.

---

**Bottom Line:**
- Verify deployment architecture before deploying
- Clear all cache layers when testing
- Use surgical edits on production code
- Know your dependencies (SVG structure matters)
- Follow verification checklists religiously
- Prefer industry standards over custom solutions
