# Manual UI Testing Checklist

## Test Environment
- **UI URL**: http://localhost:8501
- **API URL**: http://localhost:8000
- **Date**: 2026-02-18
- **Tester**: AI Agent (Comprehensive Testing Mode)

---

## ✅ TEST 1: UI Accessibility & Initial Load

###Steps:
1. Open browser to http://localhost:8501
2. Wait for page to load completely
3. Check for any error messages

### Expected Results:
- [ ] Page loads within 5 seconds
- [ ] No error messages displayed
- [ ] Title shows "Credit Card Fraud Detection System"
- [ ] Sidebar is visible on the left

### Actual Results:
Status: PENDING - Testing now

---

## ✅ TEST 2: Sidebar - API Connection Status

### Steps:
1. Look at the sidebar
2. Find "API Connection" section
3. Verify API URL and connection status

### Expected Results:
- [ ] Shows "API URL: http://localhost:8000" (NOT http://fraud-detection-api:8000)
- [ ] Shows "Status: ✅ Connected" (green checkmark)
- [ ] No connection error messages

### Actual Results:
Status: PENDING

---

## ✅ TEST 3: Sidebar - Navigation Menu

### Steps:
1. Check sidebar for navigation options
2. Note all available pages

### Expected Results:
- [ ] Dashboard option visible
- [ ] Transaction Analysis option visible
- [ ] Fraud Patterns option visible
- [ ] System Health option visible

### Actual Results:
Status: PENDING

---

## ✅ TEST 4: Dashboard Page

### Steps:
1. Click on "Dashboard" (should be default page)
2. Wait for all metrics to load

### Expected Results:
- [ ] Page title shows "Fraud Detection Dashboard"
- [ ] System metrics display (Total Transactions, Fraud Detected, etc.)
- [ ] Charts/visualizations load without errors
- [ ] "Analyze Transaction" form is visible
- [ ] All metrics show actual values (not "Loading..." or errors)

### Test Fraud Detection:
1. Fill in transaction details:
   - Amount: 5000.00
   - Merchant: "Test Store XYZ"
   - Merchant Category: "E-commerce"
   - Location: "New York"
   - Card Last 4: "1234"
2. Click "Analyze Transaction"
3. Wait for results

### Expected Results:
- [ ] Analysis completes within 60 seconds
- [ ] Results panel appears
- [ ] Shows fraud prediction (YES/NO)
- [ ] Shows confidence score
- [ ] Shows detailed analysis/explanation
- [ ] No error messages

### Actual Results:
Status: PENDING

---

## ✅ TEST 5: Transaction Analysis Page

### Steps:
1. Click "Transaction Analysis" in sidebar
2. Wait for page to load

### Expected Results:
- [ ] Page loads successfully
- [ ] Transaction input form is displayed
- [ ] Can enter transaction details
- [ ] Submit button is visible and enabled

### Test Analysis:
1. Enter sample transaction:
   - Amount: 250.75
   - Merchant: "Coffee Shop"
   - Category: "Food & Dining"
2. Submit for analysis

### Expected Results:
- [ ] Form submits successfully
- [ ] Results display
- [ ] Analysis includes reasoning
- [ ] No timeout or connection errors

### Actual Results:
Status: PENDING

---

## ✅ TEST 6: Fraud Patterns Page

### Steps:
1. Click "Fraud Patterns" in sidebar
2. Wait for patterns to load from API

### Expected Results:
- [ ] Page loads successfully
- [ ] Fraud patterns display in list/table format
- [ ] Each pattern shows:
  - Pattern ID
  - Name
  - Description
  - Fraud type
  - Amount
- [ ] At least 10 patterns visible
- [ ] No "Failed to load" errors

### Test Pattern Interaction:
1. Click on a pattern (if interactive)
2. Check if details expand or show more info

### Expected Results:
- [ ] Pattern interaction works (if implemented)
- [ ] Details are readable and formatted correctly

### Actual Results:
Status: PENDING

---

## ✅ TEST 7: System Health Page

### Steps:
1. Click "System Health" in sidebar
2. Wait for health metrics to load

### Expected Results:
- [ ] Page loads successfully
- [ ] API connection status shown
- [ ] System metrics displayed:
  - Uptime
  - Requests per minute
  - Average response time
  - Error rate
- [ ] Model performance metrics shown
- [ ] All metrics show current values (not stale/cached)

### Actual Results:
Status: PENDING

---

## ✅ TEST 8: Error Handling

### Steps:
1. Stop the API server (kill the process)
2. Try to use any UI feature (e.g., analyze transaction)
3. Observe error handling

### Expected Results:
- [ ] Clear error message displayed
- [ ] Message indicates "Cannot connect to API"
- [ ] UI doesn't crash or freeze
- [ ] User can still navigate pages

### Recovery Test:
1. Restart API server
2. Try the same action again

### Expected Results:
- [ ] Connection re-establishes automatically
- [ ] Feature works after API restart
- [ ] No need to refresh browser

### Actual Results:
Status: PENDING

---

## ✅ TEST 9: Configuration Sidebar (if exists)

### Steps:
1. Check if there's an API configuration section in sidebar
2. Look for editable API URL / API Key fields

### Expected Results:
- [ ] Can view current API URL
- [ ] Can modify API URL if needed
- [ ] Changes take effect immediately

### Actual Results:
Status: PENDING

---

## ✅ TEST 10: Browser Console Check

### Steps:
1. Open browser Developer Tools (F12)
2. Go to Console tab
3. Look for JavaScript errors

### Expected Results:
- [ ] No critical errors (red messages)
- [ ] No network request failures (404, 500 errors)
- [ ] API calls succeed (200 status codes)

### Actual Results:
Status: PENDING

---

## ✅ TEST 11: Network Tab Check

### Steps:
1. Open Developer Tools → Network tab
2. Analyze a transaction
3. Watch network requests

### Expected Results:
- [ ] Request goes to http://localhost:8000 (NOT fraud-detection-api)
- [ ] Request completes successfully
- [ ] Response contains expected JSON data
- [ ] No CORS errors

### Actual Results:
Status: PENDING

---

## ✅ TEST 12: Responsive Design

### Steps:
1. Resize browser window to different sizes
2. Test mobile view (narrow width)
3. Test tablet view (medium width)

### Expected Results:
- [ ] UI adapts to different screen sizes
- [ ] Sidebar collapses/adapts appropriately
- [ ] Content remains readable
- [ ] No overlapping elements

### Actual Results:
Status: PENDING

---

## ✅ TEST 13: Data Consistency

### Steps:
1. Note metrics on Dashboard (e.g., Total Transactions: 15380)
2. Navigate to System Health page
3. Check if same metrics are displayed

### Expected Results:
- [ ] Metrics are consistent across pages
- [ ] Numbers match between Dashboard and System Health
- [ ] Timestamps are recent (not stale)

### Actual Results:
Status: PENDING

---

## Test Summary

### Critical Issues Found:
1. 
2. 
3. 

### Minor Issues Found:
1. 
2. 
3. 

### What Works Perfectly:
1. ✅ API endpoints respond correctly
2. ✅ Metrics endpoint returns proper structure
3. ✅ Fraud patterns endpoint returns array correctly
4. ✅ Response times acceptable (2-3s)
5. 

### Recommendations:
1. 
2. 
3. 

---

## Sign-off

**Status**: ⬜ IN PROGRESS | ⬜ PASSED | ⬜ FAILED

**Overall Assessment**:
- Tests Passed: __/13
- Tests Failed: __/13
- Pass Rate: __%

**Notes**:


**Next Steps**:
1. Complete all manual tests above
2. Document all issues found
3. Fix critical issues
4. Re-test failed scenarios
5. Proceed to Docker deployment testing

