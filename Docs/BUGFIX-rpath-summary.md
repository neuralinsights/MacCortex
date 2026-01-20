# Bug Fix Summary: Sparkle.framework @rpath Issue (Both Versions)

**Bug ID**: #20260120-RPATH
**Fix Date**: 2026-01-20
**Affected Projects**: MacCortex (中文版) + MacCortex-en (English)
**Status**: ✅ Both Fixed

---

## Executive Summary

Both Chinese and English versions of MacCortex experienced the same critical bug where the application crashed immediately on launch due to dyld being unable to locate Sparkle.framework. The issue was caused by missing `@rpath` configuration during SPM (Swift Package Manager) build.

**Impact**: 🔴 Critical - Application unable to launch (100% failure rate)

**Fix Applied**: Modified build scripts to add linker flags setting `@loader_path/../Frameworks` as `@rpath`, ensuring dyld can correctly locate Sparkle.framework.

---

## Version 1: MacCortex (中文版)

### Repository
`/Users/jamesg/projects/MacCortex`

### Fix Details

**Modified Files**:
- `Scripts/build-app.sh` (Line 45-55, 84-94)

**Changes**:
1. Added linker flags: `-Xlinker -rpath -Xlinker @loader_path/../Frameworks`
2. Added post-build @rpath verification
3. Automatic fix mechanism

**Verification**:
- ✅ @rpath configured: `@loader_path/../Frameworks`
- ✅ Application launch: PID 47768
- ✅ Gatekeeper: accepted

**Notarization**:
- Submission ID: `8b695834-10e6-40b8-a102-8dbe605f2989`
- Status: Accepted
- Processing Time: ~2 minutes

**Git Commit**: `bbfb85e`

---

## Version 2: MacCortex-en (English)

### Repository
`/Users/jamesg/projects/MacCortex-en`

### Fix Details

**Modified Files**:
- `Scripts/build-app.sh` (Line 45-55, 84-94)

**Changes**:
1. Added linker flags: `-Xlinker -rpath -Xlinker @loader_path/../Frameworks`
2. Added post-build @rpath verification
3. Automatic fix mechanism

**Verification**:
- ✅ @rpath configured: `@loader_path/../Frameworks`
- ✅ Application launch: PID 48759
- ✅ Gatekeeper: accepted

**Notarization**:
- Submission ID: `2375a8ab-7c9d-4978-8da7-9d801b03881e`
- Status: Accepted
- Processing Time: ~2 minutes

**Git Commit**: `7aa4c8e`

---

## Technical Details

### Root Cause

SPM builds did not include `@loader_path/../Frameworks` in the executable's `@rpath`, causing dyld to fail when trying to load Sparkle.framework at runtime.

**Before Fix**:
```
@rpath includes:
- /usr/lib/swift
- @loader_path (points to MacOS/ directory)
- Xcode toolchain path

dyld searches:
❌ /usr/lib/swift/Sparkle.framework/... (not found)
❌ MacOS/Sparkle.framework/... (not found)
❌ Xcode toolchain/Sparkle.framework/... (not found)
→ Crash with "Library not loaded" error
```

**After Fix**:
```
@rpath includes:
- /usr/lib/swift
- @loader_path
- Xcode toolchain path
- @loader_path/../Frameworks (newly added)

dyld searches:
✅ @loader_path/../Frameworks/Sparkle.framework/... (found!)
→ Application launches successfully
```

---

## Fix Implementation

### Modified Code (Both Versions)

**Addition 1: Linker Flags**
```bash
# Add linker flags to set correct @rpath
LINKER_FLAGS="-Xlinker -rpath -Xlinker @loader_path/../Frameworks"

if [ "$BUILD_CONFIG" = "release" ]; then
    swift build --configuration release $LINKER_FLAGS
    echo "  ✓ Release build complete (@rpath configured)"
else
    swift build --configuration debug $LINKER_FLAGS
    echo "  ✓ Debug build complete (@rpath configured)"
fi
```

**Addition 2: Verification Step**
```bash
# Step 6.5: Verify @rpath configuration
echo ""
echo -e "${YELLOW}[Verify]${NC} Checking @rpath configuration..."
if otool -l "$APP_BUNDLE/Contents/MacOS/$APP_NAME" | grep -q "@loader_path/../Frameworks"; then
    echo "  ✓ @rpath configured correctly"
else
    echo -e "  ${RED}✗ @rpath configuration missing!${NC}"
    echo "  Adding @rpath..."
    install_name_tool -add_rpath "@loader_path/../Frameworks" "$APP_BUNDLE/Contents/MacOS/$APP_NAME"
    echo "  ✓ @rpath fixed"
fi
```

---

## Verification Commands

### Check @rpath
```bash
# Chinese version
otool -l /Users/jamesg/projects/MacCortex/build/MacCortex.app/Contents/MacOS/MacCortex | grep "@loader_path/../Frameworks"

# English version
otool -l /Users/jamesg/projects/MacCortex-en/build/MacCortex.app/Contents/MacOS/MacCortex | grep "@loader_path/../Frameworks"
```

### Test Launch
```bash
# Chinese version
open /Users/jamesg/projects/MacCortex/build/MacCortex.app

# English version
open /Users/jamesg/projects/MacCortex-en/build/MacCortex.app
```

### Verify Gatekeeper
```bash
# Chinese version
spctl --assess --type execute /Users/jamesg/projects/MacCortex/build/MacCortex.app

# English version
spctl --assess --type execute /Users/jamesg/projects/MacCortex-en/build/MacCortex.app
```

---

## Notarization Records

| Version | Submission ID | Status | Processing Time | Commit |
|---------|---------------|--------|-----------------|--------|
| MacCortex (中文) | 8b695834-10e6-40b8-a102-8dbe605f2989 | Accepted | ~2 min | bbfb85e |
| MacCortex-en | 2375a8ab-7c9d-4978-8da7-9d801b03881e | Accepted | ~2 min | 7aa4c8e |

**Total Notarizations**: 2
**Success Rate**: 100%

---

## Impact Assessment

### Severity
🔴 **Critical** - Application unable to launch

### Affected Users
- All users building MacCortex Phase 0.5
- All users who integrated Sparkle.framework (Day 10)
- Impact: 100% (application crash on launch)

### Resolution Time
- **Discovery**: 2026-01-20 20:49:11 +1300 (user reported)
- **Root Cause Identified**: 2026-01-20 20:52:00 +1300 (~3 min)
- **Fix Implemented (中文)**: 2026-01-20 20:55:00 +1300 (~6 min)
- **Fix Implemented (English)**: 2026-01-20 21:03:00 +1300 (~8 min)
- **Total Time**: ~14 minutes for both versions

---

## Lessons Learned

### What Went Wrong

1. **Build Script Incomplete**: Did not configure `@rpath` during SPM build
2. **Insufficient Testing**: Did not test application launch after Sparkle integration (Day 10)
3. **Missing Verification**: No automated check for dyld dependencies

### What Went Right

1. **Quick Diagnosis**: Root cause identified in ~3 minutes using `otool`
2. **Systematic Fix**: Applied to both versions consistently
3. **Automated Verification**: Added verification step to prevent future occurrences
4. **Documentation**: Comprehensive bug reports created for both versions

---

## Preventive Measures

### Immediate (✅ Implemented)

1. **Build Script Enhancement**
   - ✅ Add linker flags in SPM build command
   - ✅ Add post-build @rpath verification
   - ✅ Automatic fix with `install_name_tool` if missing

2. **Documentation**
   - ✅ Created BUGFIX-rpath.md for both versions
   - ✅ Created this summary document

### Future Recommendations

1. **Automated Testing**
   - Add launch test to CI/CD pipeline
   - Verify all dyld dependencies after build
   - Test on clean macOS installation

2. **Acceptance Criteria Update**
   - P0-5 should include: "Application launches successfully"
   - Add test command: `open build/MacCortex.app && sleep 3 && ps aux | grep MacCortex`

3. **Build Script Template**
   - Create reusable template for SPM-based macOS apps
   - Include @rpath configuration by default
   - Add comprehensive verification steps

---

## Files Modified

### MacCortex (中文版)
```
/Users/jamesg/projects/MacCortex/
├── Scripts/build-app.sh (modified)
├── Docs/BUGFIX-rpath.md (new)
└── Docs/BUGFIX-rpath-summary.md (new, this file)
```

### MacCortex-en (English)
```
/Users/jamesg/projects/MacCortex-en/
├── Scripts/build-app.sh (modified)
└── Docs/BUGFIX-rpath.md (new)
```

---

## Git Commits

### MacCortex (中文版)
```
Commit: bbfb85e
Title: [BUGFIX] 修复 Sparkle.framework 动态链接错误 (#20260120-RPATH)
Files: Scripts/build-app.sh, Docs/BUGFIX-rpath.md
```

### MacCortex-en (English)
```
Commit: 7aa4c8e
Title: [BUGFIX] Fix Sparkle.framework Dynamic Library Loading Error (#20260120-RPATH)
Files: Scripts/build-app.sh, Docs/BUGFIX-rpath.md
```

---

## Status

| Version | Build | Sign | Notarize | Launch | Status |
|---------|-------|------|----------|--------|--------|
| MacCortex (中文) | ✅ | ✅ | ✅ Accepted | ✅ PID 47768 | ✅ **Fixed** |
| MacCortex-en | ✅ | ✅ | ✅ Accepted | ✅ PID 48759 | ✅ **Fixed** |

**Overall Status**: ✅ **Both Versions Fixed and Verified**

---

## References

### Internal Documentation
- [MacCortex BUGFIX-rpath.md](../MacCortex/Docs/BUGFIX-rpath.md)
- [MacCortex-en BUGFIX-rpath.md](../MacCortex-en/Docs/BUGFIX-rpath.md)

### External Resources
- [Apple: Runtime Search Paths](https://developer.apple.com/library/archive/documentation/DeveloperTools/Conceptual/DynamicLibraries/100-Articles/RunpathDependentLibraries.html)
- [otool man page](https://www.manpagez.com/man/1/otool/)
- [install_name_tool man page](https://www.manpagez.com/man/1/install_name_tool/)

---

**Summary Created**: 2026-01-20 21:05:00 +1300
**Created By**: Claude Code (Sonnet 4.5)
**Purpose**: Cross-version bug fix documentation
**Status**: ✅ **Complete**
