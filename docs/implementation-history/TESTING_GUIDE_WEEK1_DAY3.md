# Testing Guide - Week 1 Day 3: API Integrations + Appearance Sections

**Date:** 2025-01-06  
**URL:** http://127.0.0.1:3000/settings  
**Status:** Servers running, browser opened

---

## 🧪 Testing Checklist

### ✅ Step 1: Verify Application is Running

**Expected:**
- Browser should open to http://127.0.0.1:3000/settings
- Settings page should load without errors
- No console errors in browser DevTools (F12)

**Actions:**
1. Open browser DevTools (F12)
2. Check Console tab for errors
3. Check Network tab for failed requests
4. Verify page loads completely

**Status:** [ ] PASS / [ ] FAIL  
**Notes:**

---

### ✅ Step 2: Test API Integrations Tab

#### 2.1 Initial Load
**Expected:**
- Tab should be visible and clickable
- Empty state alert should appear: "No API integrations configured..."
- "Add Integration" button should be visible
- Security notice should be displayed
- Integration types info should be displayed

**Actions:**
1. Click on "APIS" tab
2. Verify empty state message
3. Verify info alerts are present

**Status:** [ ] PASS / [ ] FAIL  
**Notes:**

#### 2.2 Add New Integration - Economic Calendar
**Expected:**
- Dialog opens with form fields
- Type selector shows: Economic Calendar, News API, Custom
- Base URL auto-populates when type is selected
- API key field has visibility toggle
- Security notice is displayed

**Actions:**
1. Click "Add Integration" button
2. Select "Economic Calendar (Econdb)" from type dropdown
3. Verify base URL auto-populates to "https://www.econdb.com/api"
4. Enter name: "Test Econdb"
5. Enter API key: "test_key_12345678"
6. Click eye icon to toggle API key visibility
7. Click "Add Integration" button

**Expected Result:**
- Success toast appears: "Integration added successfully"
- Dialog closes
- New integration card appears in grid
- API key is masked: "****5678" (last 4 chars)

**Status:** [ ] PASS / [ ] FAIL  
**Notes:**

#### 2.3 Verify Integration Card Display
**Expected:**
- Card shows integration name: "Test Econdb"
- Type icon: Calendar icon
- Type label: "Economic Calendar"
- Status badge: "Inactive" (gray)
- API key masked: "****5678"
- "Test Connection" button visible
- Remove button (trash icon) visible
- Created date displayed

**Actions:**
1. Verify all card elements are present
2. Verify API key is masked correctly

**Status:** [ ] PASS / [ ] FAIL  
**Notes:**

#### 2.4 Test Connection (Expected to Fail)
**Expected:**
- Button shows loading state: "Testing..."
- After timeout, error toast appears
- Status badge may change to "Error" (red)

**Actions:**
1. Click "Test Connection" button
2. Wait for response
3. Verify error toast appears (expected - no real API key)
4. Verify button returns to normal state

**Status:** [ ] PASS / [ ] FAIL  
**Notes:**

#### 2.5 Add Second Integration - News API
**Expected:**
- Can add multiple integrations
- Grid layout shows 2 columns on desktop

**Actions:**
1. Click "Add Integration" button
2. Select "News API" from type dropdown
3. Verify base URL auto-populates to "https://newsapi.org/v2"
4. Enter name: "Test NewsAPI"
5. Enter API key: "test_news_key_abcdef"
6. Click "Add Integration"

**Expected Result:**
- Success toast appears
- Second integration card appears
- Grid shows 2 cards side by side (on desktop)

**Status:** [ ] PASS / [ ] FAIL  
**Notes:**

#### 2.6 Remove Integration
**Expected:**
- Confirmation dialog appears
- Integration is removed after confirmation

**Actions:**
1. Click remove button (trash icon) on first integration
2. Verify confirmation dialog appears: "Are you sure you want to remove integration..."
3. Click "OK" to confirm
4. Verify success toast: "Integration removed"
5. Verify integration card disappears

**Status:** [ ] PASS / [ ] FAIL  
**Notes:**

#### 2.7 Browser Console Check
**Expected:**
- No console errors
- No network errors (except expected API test failures)

**Actions:**
1. Open DevTools Console tab
2. Check for any errors
3. Open Network tab
4. Verify API calls to /api/settings/integrations

**Status:** [ ] PASS / [ ] FAIL  
**Notes:**

---

### ✅ Step 3: Test Appearance Tab

#### 3.1 Initial Load
**Expected:**
- Tab loads without errors
- All settings controls are visible
- Default values are displayed:
  - Density: Normal
  - Theme: Dark
  - Font Size: 14px
  - Accent Color: #3b82f6 (blue)
  - Show Animations: ON

**Actions:**
1. Click on "APPEARANCE" tab
2. Verify all controls are present
3. Verify default values

**Status:** [ ] PASS / [ ] FAIL  
**Notes:**

#### 3.2 Change Density Setting
**Expected:**
- Radio buttons work
- Selection changes visually

**Actions:**
1. Click "Compact" radio button
2. Verify it becomes selected
3. Click "Comfortable" radio button
4. Verify it becomes selected
5. Click "Normal" radio button
6. Verify it becomes selected

**Status:** [ ] PASS / [ ] FAIL  
**Notes:**

#### 3.3 Change Theme Setting
**Expected:**
- Radio buttons work
- Selection changes visually

**Actions:**
1. Click "Light" radio button
2. Verify it becomes selected
3. Click "Dark" radio button
4. Verify it becomes selected

**Status:** [ ] PASS / [ ] FAIL  
**Notes:**

#### 3.4 Adjust Font Size
**Expected:**
- Slider works
- Value display updates in real-time

**Actions:**
1. Drag font size slider to minimum (12px)
2. Verify value display shows "12px"
3. Drag slider to maximum (18px)
4. Verify value display shows "18px"
5. Drag slider to middle (14px)
6. Verify value display shows "14px"

**Status:** [ ] PASS / [ ] FAIL  
**Notes:**

#### 3.5 Change Accent Color
**Expected:**
- Color picker opens
- Hex value updates

**Actions:**
1. Click on color picker
2. Select a different color (e.g., red)
3. Verify hex value changes
4. Verify color swatch updates

**Status:** [ ] PASS / [ ] FAIL  
**Notes:**

#### 3.6 Toggle Show Animations
**Expected:**
- Switch toggles on/off
- Visual state changes

**Actions:**
1. Click "Show Animations" switch to turn OFF
2. Verify switch shows OFF state
3. Click switch to turn ON
4. Verify switch shows ON state

**Status:** [ ] PASS / [ ] FAIL  
**Notes:**

#### 3.7 Save Changes
**Expected:**
- Success toast appears
- Settings are persisted

**Actions:**
1. Change density to "Compact"
2. Change font size to 16px
3. Click "Save Changes" button
4. Verify success toast: "Appearance settings saved successfully"
5. Refresh page (F5)
6. Navigate back to Appearance tab
7. Verify settings are still "Compact" and 16px

**Status:** [ ] PASS / [ ] FAIL  
**Notes:**

#### 3.8 Reset to Defaults
**Expected:**
- Settings reset to defaults
- Success toast appears

**Actions:**
1. Click "Reset to Defaults" button
2. Verify success toast: "Settings reset to defaults"
3. Verify all settings return to defaults:
   - Density: Normal
   - Theme: Dark
   - Font Size: 14px
   - Accent Color: #3b82f6
   - Show Animations: ON

**Status:** [ ] PASS / [ ] FAIL  
**Notes:**

#### 3.9 Browser Console Check
**Expected:**
- No console errors
- No network errors

**Actions:**
1. Open DevTools Console tab
2. Check for any errors
3. Open Network tab
4. Verify API calls to /api/settings/appearance

**Status:** [ ] PASS / [ ] FAIL  
**Notes:**

---

### ✅ Step 4: Test Existing Tabs (Regression Testing)

#### 4.1 Accounts Tab
**Expected:**
- Still works as before
- No regressions

**Actions:**
1. Click on "ACCOUNTS" tab
2. Verify tab loads correctly
3. Verify existing functionality works

**Status:** [ ] PASS / [ ] FAIL  
**Notes:**

#### 4.2 Risk Tab
**Expected:**
- Still works as before
- No regressions

**Actions:**
1. Click on "RISK" tab
2. Verify tab loads correctly
3. Verify existing functionality works

**Status:** [ ] PASS / [ ] FAIL  
**Notes:**

---

### ✅ Step 5: Security Verification

#### 5.1 API Key Masking
**Expected:**
- API keys never shown in full in UI
- Only last 4 characters visible

**Actions:**
1. Go to API Integrations tab
2. Add an integration with API key: "my_secret_api_key_123456"
3. Verify card shows: "****3456"
4. Open DevTools Network tab
5. Check response from GET /api/settings/integrations
6. Verify API key is masked in response

**Status:** [ ] PASS / [ ] FAIL  
**Notes:**

#### 5.2 API Key Visibility Toggle
**Expected:**
- Toggle works in add dialog
- API key hidden by default

**Actions:**
1. Click "Add Integration"
2. Verify API key field is type="password" (dots)
3. Click eye icon
4. Verify API key field shows plaintext
5. Click eye icon again
6. Verify API key field is hidden again

**Status:** [ ] PASS / [ ] FAIL  
**Notes:**

#### 5.3 Confirmation Dialogs
**Expected:**
- Confirmation required before deletion

**Actions:**
1. Try to remove an integration
2. Verify confirmation dialog appears
3. Click "Cancel"
4. Verify integration is NOT removed
5. Try again and click "OK"
6. Verify integration IS removed

**Status:** [ ] PASS / [ ] FAIL  
**Notes:**

---

### ✅ Step 6: Responsive Design

#### 6.1 Desktop Layout
**Expected:**
- 2-column grid for integration cards
- All controls visible and properly sized

**Actions:**
1. Verify layout on full-width browser window
2. Check API Integrations grid (should be 2 columns)

**Status:** [ ] PASS / [ ] FAIL  
**Notes:**

#### 6.2 Mobile Layout (Optional)
**Expected:**
- 1-column grid for integration cards
- All controls still accessible

**Actions:**
1. Resize browser window to mobile width (< 768px)
2. Verify grid becomes 1 column
3. Verify all controls still work

**Status:** [ ] PASS / [ ] FAIL  
**Notes:**

---

## 📊 Overall Test Results

### Summary
- **Total Tests:** 25+
- **Passed:** ___
- **Failed:** ___
- **Skipped:** ___

### Critical Issues Found
1. 
2. 
3. 

### Minor Issues Found
1. 
2. 
3. 

### Recommendations
1. 
2. 
3. 

---

## 🔍 Backend API Testing (Optional)

If you want to test the backend API directly, you can use these curl commands or Postman:

### Get All Integrations
```bash
curl http://127.0.0.1:5001/api/settings/integrations
```

### Create Integration
```bash
curl -X POST http://127.0.0.1:5001/api/settings/integrations \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Integration",
    "type": "news",
    "api_key": "test_key_123456",
    "base_url": "https://newsapi.org/v2"
  }'
```

### Get Appearance Settings
```bash
curl http://127.0.0.1:5001/api/settings/appearance
```

### Update Appearance Settings
```bash
curl -X PUT http://127.0.0.1:5001/api/settings/appearance \
  -H "Content-Type: application/json" \
  -d '{
    "density": "compact",
    "theme": "dark",
    "font_size": 16,
    "accent_color": "#ff0000",
    "show_animations": true
  }'
```

---

## ✅ Next Steps After Testing

### If All Tests Pass:
1. Mark Week 1 Day 3 as COMPLETE ✅
2. Proceed with Week 2 Task 1: Navigation Consolidation
3. Remove duplicate "AI" navigation item
4. Keep only "AI Trading" pointing to `/ai`

### If Issues Found:
1. Document all issues in this file
2. Prioritize issues (critical, major, minor)
3. Fix critical issues before proceeding
4. Create GitHub issues for minor issues to fix later

---

**Testing Started:** ___________  
**Testing Completed:** ___________  
**Tester:** ___________  
**Status:** [ ] PASS / [ ] FAIL / [ ] PARTIAL

---

**Good luck with testing! 🧪**

