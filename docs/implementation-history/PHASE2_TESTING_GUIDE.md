# Phase 2: Frontend Integration - Testing Guide

## 🎯 Overview

This guide provides step-by-step instructions for testing the Phase 2 AI Trading frontend integration with your demo MT5 account.

**Prerequisites:**
- Phase 1 backend is running (`python start_app.py`)
- Phase 2 frontend is running (`npm run dev` in tradecraft-console-main/)
- Demo MT5 terminal is running and connected
- At least one strategy file exists (e.g., `config/ai/strategies/EURUSD_H1.json`)

---

## 🚀 Quick Start

### 1. Start Backend Server
```bash
# From project root
python start_app.py
```

**Expected Output:**
```
INFO:     Started server process
INFO:     Uvicorn running on http://127.0.0.1:5001
```

### 2. Start Frontend Development Server
```bash
# From tradecraft-console-main/tradecraft-console-main/
npm run dev
```

**Expected Output:**
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:3000/
➜  Network: use --host to expose
```

### 3. Open Browser
Navigate to: `http://localhost:3000/`

---

## 📋 Test Checklist

### Test 1: AI Status Indicator in Sidebar

**Location:** Trading Dashboard (/) → Left Sidebar

**Steps:**
1. ✅ Open `http://localhost:3000/`
2. ✅ Look at left sidebar below navigation buttons
3. ✅ Verify "AI Trading" section appears
4. ✅ Check status indicator shows "OFF" badge (if AI not enabled)
5. ✅ Verify "0 symbols" text appears
6. ✅ Click on AI Trading section
7. ✅ Verify navigation to `/ai` page

**Expected Results:**
- AI Trading section visible in sidebar
- Brain icon displayed
- Status shows "OFF" with red badge (initially)
- Symbol count shows "0 symbols"
- Clicking navigates to AI page

**Screenshot Location:** Left sidebar between navigation and priority symbols

---

### Test 2: AI Control Panel

**Location:** AI Page (/) → Overview Tab → Left Column

**Steps:**
1. ✅ Navigate to `http://localhost:3000/ai`
2. ✅ Verify "AI Control Panel" appears in left column
3. ✅ Check "Engine Status" shows "DISABLED" (red indicator)
4. ✅ Verify "Mode" shows "SEMI-AUTO"
5. ✅ Check "Active Trade Ideas" shows "0"
6. ✅ Verify "Autonomy Loop" shows "Stopped"
7. ✅ Check "Enabled Symbols" shows "No symbols enabled"
8. ✅ Verify warning message appears (yellow box)
9. ✅ Click "KILL SWITCH" button (should be disabled)
10. ✅ Click refresh button (circular arrow icon)

**Expected Results:**
- Control panel displays all status fields
- Status indicators show correct colors
- Kill switch button is disabled when AI is off
- Refresh button updates status
- Warning message explains AI is disabled

---

### Test 3: Manual Evaluation

**Location:** AI Page (/) → Overview Tab → Left Column → Manual Evaluation Panel

**Steps:**
1. ✅ Verify "Manual Evaluation" panel appears below control panel
2. ✅ Check symbol dropdown is populated with symbols
3. ✅ Select "EURUSD" from dropdown
4. ✅ Click "Evaluate Now" button
5. ✅ Wait for evaluation to complete
6. ✅ Check for toast notification
7. ✅ Verify trade idea appears in right column (if conditions met)

**Expected Results:**
- Symbol dropdown shows available symbols
- Evaluate button triggers API call
- Loading state shows "Evaluating..."
- Toast notification shows result
- Trade idea card appears if evaluation successful
- Error toast if strategy file missing

**Possible Outcomes:**
- ✅ **Success:** Trade idea generated → Card appears in right column
- ⚠️ **No Trade:** Conditions not met → Toast shows "No Trade Idea"
- ❌ **Error:** Strategy missing → Toast shows error message

---

### Test 4: Trade Idea Card

**Location:** AI Page (/) → Overview Tab → Right Column

**Prerequisites:** Generate a trade idea via manual evaluation

**Steps:**
1. ✅ Verify trade idea card appears after evaluation
2. ✅ Check symbol and timeframe display (e.g., "EURUSD H1")
3. ✅ Verify confidence score shows (0-100)
4. ✅ Check confidence color coding:
   - Red (0-20): Very Low
   - Orange (20-40): Low
   - Yellow (40-60): Medium
   - Green (60-80): High
   - Emerald (80-100): Very High
5. ✅ Verify direction shows (LONG or SHORT)
6. ✅ Check action label (Observe/Pending Only/Wait for RR/Execute)
7. ✅ Verify price levels display:
   - Entry price
   - Stop Loss (red)
   - Take Profit (green)
8. ✅ Check trade details:
   - Volume
   - RR Ratio (color-coded: green if ≥2, yellow if <2)
   - Risk %
   - Status badge
9. ✅ Verify EMNR flags section:
   - Entry (green if true, gray if false)
   - Strong (blue if true, gray if false)
   - Weak (orange if true, gray if false)
   - Exit (red if true, gray if false)
10. ✅ Check indicators section:
    - EMA Fast/Slow
    - RSI
    - MACD
    - ATR/ATR Median
11. ✅ Verify action buttons appear (if status is "pending_approval"):
    - "Approve & Execute" (green)
    - "Reject" (red)
12. ✅ Click "Reject" button
13. ✅ Verify trade idea disappears
14. ✅ Check toast notification confirms rejection

**Expected Results:**
- All trade idea details display correctly
- Colors match direction and confidence
- EMNR flags show correct states
- Indicators show accurate values
- Buttons work and provide feedback
- Card has colored left border (green for long, red for short)

---

### Test 5: Strategy Editor

**Location:** AI Page (/) → Strategies Tab

**Prerequisites:** Strategy file exists (e.g., `config/ai/strategies/EURUSD_H1.json`)

**Steps:**
1. ✅ Click "Strategies" tab
2. ✅ Verify symbol list appears in left column
3. ✅ Click "EURUSD" in symbol list
4. ✅ Verify strategy editor loads in right column
5. ✅ Check strategy details display:
   - Symbol (disabled input)
   - Timeframe (disabled input)
6. ✅ Verify indicator parameters section:
   - EMA Fast/Slow periods
   - RSI Period/Overbought/Oversold
   - ATR Period/Multiplier
7. ✅ Verify strategy settings section:
   - Direction dropdown (Long Only/Short Only/Both)
   - Min RR Ratio input
8. ✅ Change EMA Fast period from 20 to 25
9. ✅ Click "Save" button
10. ✅ Verify toast notification confirms save
11. ✅ Click refresh button
12. ✅ Verify changes persist

**Expected Results:**
- Symbol list shows all available symbols
- Strategy loads when symbol selected
- All parameters display correctly
- Inputs are editable
- Save button persists changes
- Refresh button reloads from backend
- Info note explains advanced editing

**Error Case:**
- If no strategy file exists:
  - Shows "No strategy found" message
  - Displays file path hint
  - No editable fields

---

### Test 6: Decision History

**Location:** AI Page (/) → Decision History Tab

**Prerequisites:** At least one evaluation has been performed

**Steps:**
1. ✅ Click "Decision History" tab
2. ✅ Verify decision table appears
3. ✅ Check table columns:
   - Timestamp
   - Symbol
   - TF (Timeframe)
   - Confidence
   - Action
   - Direction
   - Entry
   - SL
   - TP
   - RR
   - EMNR (E/S/W/X flags)
4. ✅ Verify at least one row appears (from previous evaluation)
5. ✅ Check confidence color coding (green ≥75, yellow ≥60, gray <60)
6. ✅ Verify direction color coding (green for long, red for short)
7. ✅ Check EMNR flags display as compact letters
8. ✅ Verify table is scrollable if many records

**Expected Results:**
- Table displays all AI decisions
- Columns show correct data
- Colors match confidence and direction
- EMNR flags show as E/S/W/X with colors
- Timestamps are formatted correctly
- Table scrolls horizontally if needed

**Empty State:**
- If no decisions yet:
  - Shows "No decision history" message
  - Displays helpful hint

---

### Test 7: AI Status Updates

**Location:** Trading Dashboard (/) → Left Sidebar

**Prerequisites:** Enable AI for a symbol (via backend API or future UI)

**Steps:**
1. ✅ Enable AI for EURUSD via backend:
   ```bash
   curl -X POST http://127.0.0.1:5001/api/ai/enable/EURUSD \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your-key-here" \
     -d '{"timeframe": "H1", "auto_execute": false}'
   ```
2. ✅ Wait 10 seconds (auto-refresh interval)
3. ✅ Verify sidebar AI status updates:
   - "OFF" badge disappears
   - "1 symbol" appears
   - Green pulse indicator shows
4. ✅ Navigate to `/ai` page
5. ✅ Verify control panel shows:
   - "ACTIVE" status (green)
   - "EURUSD" in enabled symbols list
6. ✅ Trigger kill switch:
   - Click "KILL SWITCH" button
   - Confirm dialog
7. ✅ Verify status updates to "DISABLED"
8. ✅ Check sidebar updates to "OFF" badge

**Expected Results:**
- Sidebar updates automatically every 10 seconds
- Control panel updates every 5 seconds
- Status changes reflect immediately after actions
- Kill switch disables all AI
- Confirmation dialog prevents accidental clicks

---

### Test 8: Error Handling

**Location:** Various

**Test 8.1: Backend Offline**
1. ✅ Stop backend server
2. ✅ Refresh AI page
3. ✅ Verify error toast appears
4. ✅ Check control panel shows loading state
5. ✅ Restart backend
6. ✅ Verify status recovers

**Test 8.2: Missing Strategy**
1. ✅ Navigate to Strategies tab
2. ✅ Select symbol without strategy file
3. ✅ Verify "No strategy found" message
4. ✅ Check file path hint displays

**Test 8.3: Evaluation Error**
1. ✅ Trigger evaluation for symbol without MT5 data
2. ✅ Verify error toast appears
3. ✅ Check error message is descriptive

**Expected Results:**
- All errors show toast notifications
- Error messages are user-friendly
- UI remains functional after errors
- Loading states prevent duplicate requests

---

## 🎨 Visual Verification

### Color Coding
- ✅ **Green:** Long positions, positive values, success states
- ✅ **Red:** Short positions, negative values, error states
- ✅ **Yellow:** Warnings, medium confidence
- ✅ **Blue:** Information, strong signals
- ✅ **Gray:** Disabled, neutral, inactive

### Animations
- ✅ **Pulse:** Active status indicators
- ✅ **Spin:** Loading/refreshing states
- ✅ **Fade:** Toast notifications
- ✅ **Hover:** Interactive elements

### Dark Theme
- ✅ Background: Dark gray (#0a0a0a)
- ✅ Panels: Slightly lighter (#1a1a1a)
- ✅ Borders: Subtle gray (#2a2a2a)
- ✅ Text: White/gray hierarchy

---

## 🐛 Common Issues & Solutions

### Issue 1: "Failed to load AI status"
**Cause:** Backend not running or wrong API_BASE  
**Solution:**
1. Check backend is running on port 5001
2. Verify `window.CONFIG.API_BASE` in browser console
3. Check CORS settings in backend

### Issue 2: "No strategy found"
**Cause:** Strategy file doesn't exist  
**Solution:**
1. Create strategy file: `config/ai/strategies/EURUSD_H1.json`
2. Copy from example in `AI_INTEGRATION_TECHNICAL_SPECS.md`
3. Restart backend to load new file

### Issue 3: Evaluation returns "No Trade Idea"
**Cause:** EMNR conditions not met  
**Solution:**
1. This is normal - not all evaluations generate ideas
2. Check decision history to see why
3. Adjust strategy conditions if needed

### Issue 4: Sidebar AI status not updating
**Cause:** Auto-refresh not working  
**Solution:**
1. Check browser console for errors
2. Verify backend is responding
3. Manually refresh page

### Issue 5: Trade idea card not appearing
**Cause:** Evaluation didn't generate idea  
**Solution:**
1. Check toast notification for message
2. Review decision history for details
3. Verify strategy file is valid

---

## ✅ Success Criteria

Phase 2 testing is successful if:

- [ ] AI status indicator appears in sidebar
- [ ] AI page loads with 3 tabs
- [ ] Control panel shows correct status
- [ ] Manual evaluation triggers successfully
- [ ] Trade idea card displays all details
- [ ] Strategy editor loads and saves
- [ ] Decision history table populates
- [ ] All colors and animations work
- [ ] Error handling shows appropriate messages
- [ ] No console errors in browser
- [ ] All accessibility features work (keyboard nav, ARIA labels)

---

## 📸 Screenshots to Capture

For documentation/review:

1. **Trading Dashboard with AI Status**
   - Full dashboard view
   - Sidebar with AI indicator visible

2. **AI Page - Overview Tab**
   - Control panel on left
   - Trade idea card on right

3. **AI Page - Strategies Tab**
   - Symbol list on left
   - Strategy editor on right

4. **AI Page - Decision History Tab**
   - Full table with multiple decisions

5. **Trade Idea Card - Detailed View**
   - All sections visible
   - EMNR flags and indicators

---

## 🚀 Next Steps After Testing

1. **Report Issues:** Document any bugs or unexpected behavior
2. **Provide Feedback:** Suggest UI/UX improvements
3. **Test Edge Cases:** Try unusual scenarios
4. **Performance Check:** Monitor for slow loading or lag
5. **Accessibility Test:** Try keyboard-only navigation

---

**Happy Testing! 🎉**

If you encounter any issues, check the browser console for errors and review the backend logs for API errors.

