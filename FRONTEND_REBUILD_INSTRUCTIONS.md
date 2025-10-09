# Frontend Rebuild Instructions

**Issue:** The Settings page is showing placeholder text instead of the new AccountsSection component.

**Root Cause:** The application serves from a pre-built `dist` folder. The Vite React application needs to be rebuilt to include the new TypeScript/React components.

---

## ✅ SOLUTION: Rebuild Complete

I've successfully rebuilt the Vite frontend application. The build completed in 5.38 seconds with the following output:

```
vite v5.4.19 building for production...
✓ 1732 modules transformed.
dist/index.html                   2.15 kB │ gzip:   0.94 kB
dist/assets/index-C0yxQ2dE.css   61.93 kB │ gzip:  11.09 kB
dist/assets/index-CX_WIu7q.js   470.06 kB │ gzip: 135.32 kB
✓ built in 5.38s
```

---

## 🔄 RESTART THE APPLICATION

To see the new Accounts management UI, please restart the application:

### Option 1: Using start_app.py (Recommended)

```bash
# In the MT5_UI root directory
python start_app.py
```

This will:
- Start the FastAPI backend on http://127.0.0.1:5001
- Serve the rebuilt frontend from the `dist` folder on http://127.0.0.1:3000

### Option 2: Manual Start

If you prefer to start services separately:

**Backend:**
```bash
python -m uvicorn backend.app:app --host 127.0.0.1 --port 5001 --reload
```

**Frontend:**
```bash
python spa_server.py 3000 -d tradecraft-console-main/tradecraft-console-main/dist
```

---

## 🎯 VERIFICATION

Once the application is running, navigate to:

**http://127.0.0.1:3000/settings**

You should now see:

1. **Four tabs:** Accounts, API Integrations, Appearance, Risk Management
2. **Accounts tab** should show:
   - "MT5 Accounts" heading
   - "Add Account" button
   - Empty state alert: "No MT5 accounts configured"
   - Security notice about encryption

---

## 📋 WHAT WAS REBUILT

The Vite build process compiled and bundled:

### New Components:
- `AccountsSection.tsx` - Main accounts management UI
- `AccountCard.tsx` - Individual account display card
- `AddAccountDialog.tsx` - Modal for adding new accounts

### Modified Files:
- `Settings.tsx` - Now imports and renders AccountsSection
- `api.ts` - Added settings API functions

### Build Output:
- `dist/index.html` - Updated HTML entry point
- `dist/assets/index-C0yxQ2dE.css` - Updated CSS bundle (61.93 kB)
- `dist/assets/index-CX_WIu7q.js` - Updated JavaScript bundle (470.06 kB)

---

## 🧪 TESTING THE NEW UI

Once the application is running, test the following:

### 1. Empty State
- Navigate to Settings → Accounts tab
- Verify empty state alert is displayed
- Verify "Add Account" button is visible

### 2. Add Account
- Click "Add Account" button
- Fill in the form:
  - Name: "Demo Account"
  - Login: 107030709
  - Password: (your MT5 password)
  - Server: "MetaQuotes-Demo"
- Click "Add Account"
- Verify success toast appears
- Verify account card is displayed

### 3. Account Card
- Verify account name, login, server are displayed
- Verify status badge shows "Disconnected"
- Verify "Activate" button is visible
- Verify "Test Connection" button is visible
- Verify "Remove" button is visible

### 4. Activate Account
- Click "Activate" button
- Verify success toast appears
- Verify account card now has blue border
- Verify "Active" badge is displayed
- Verify "Activate" button is hidden
- Verify "Remove" button is disabled

### 5. Test Connection
- Click "Test Connection" button
- Verify loading spinner appears
- Verify toast shows connection result with account info

### 6. Remove Account
- Add a second account
- Try to remove the active account (should show error)
- Activate the second account
- Remove the first account
- Verify confirmation dialog appears
- Verify account is removed after confirmation

---

## 🔧 TROUBLESHOOTING

### If you still see placeholder text:

1. **Hard refresh the browser:**
   - Windows/Linux: `Ctrl + Shift + R`
   - Mac: `Cmd + Shift + R`

2. **Clear browser cache:**
   - Open DevTools (F12)
   - Right-click the refresh button
   - Select "Empty Cache and Hard Reload"

3. **Check browser console for errors:**
   - Open DevTools (F12)
   - Go to Console tab
   - Look for any JavaScript errors

4. **Verify the build:**
   ```bash
   # Check that dist folder was updated
   dir tradecraft-console-main\tradecraft-console-main\dist\assets
   
   # You should see files with recent timestamps
   ```

5. **Rebuild again if needed:**
   ```bash
   cd tradecraft-console-main\tradecraft-console-main
   npm run build
   cd ..\..
   python start_app.py
   ```

---

## 📝 FUTURE BUILDS

Whenever you make changes to the frontend code (TypeScript/React files), you need to rebuild:

```bash
cd tradecraft-console-main\tradecraft-console-main
npm run build
```

**Development Mode (Alternative):**

For faster development with hot reload, you can run Vite in dev mode:

```bash
cd tradecraft-console-main\tradecraft-console-main
npm run dev
```

This will start a development server on http://localhost:5173 with hot module replacement (HMR), so changes appear instantly without rebuilding.

However, the `start_app.py` script is configured to serve from the `dist` folder, so you'd need to access the dev server directly at http://localhost:5173 instead of http://127.0.0.1:3000.

---

## ✅ SUMMARY

- ✅ Frontend rebuilt successfully
- ✅ New components included in build
- ✅ Build output: 470 kB JavaScript, 62 kB CSS
- ✅ Ready to restart application

**Next Step:** Restart the application and navigate to http://127.0.0.1:3000/settings to see the new Accounts management UI!

