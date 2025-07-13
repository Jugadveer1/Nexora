# MetaMask Popup Not Appearing - Debug Guide

## 🔍 **Immediate Testing Steps**

### Step 1: Test Direct MetaMask API
1. Open your website: http://127.0.0.1:8000
2. Click on any "Invest" button to open the modal
3. Click the **"Direct Test"** button (orange button)
4. Check browser console (F12) for any errors
5. **Expected Result**: MetaMask popup should appear asking to connect

### Step 2: Test Web3 Integration
1. After Direct Test works, click **"Test MetaMask"** button (blue button)
2. Check console for detailed logs
3. **Expected Result**: Should show account connection success

### Step 3: Test Full Investment Flow
1. Enter a small amount (e.g., 0.001)
2. Click "Confirm Investment"
3. Check console logs for transaction flow
4. **Expected Result**: MetaMask popup for transaction confirmation

## 🚨 **Common Issues & Solutions**

### Issue 1: MetaMask Not Detected
**Symptoms**: "MetaMask not found" error
**Solutions**:
- Install MetaMask browser extension
- Refresh the page after installation
- Check if MetaMask is enabled for the site

### Issue 2: No Popup Appears
**Symptoms**: Functions run but no MetaMask popup
**Possible Causes**:
- MetaMask popup blocker is active
- Browser popup blocker is blocking MetaMask
- MetaMask is locked
- Site not connected to MetaMask

**Solutions**:
1. **Check MetaMask Settings**:
   - Open MetaMask extension
   - Go to Settings → Advanced
   - Ensure "Use Phishing Detection" is not blocking the site

2. **Check Browser Popup Settings**:
   - Allow popups for localhost/127.0.0.1
   - Disable popup blockers temporarily

3. **Reset MetaMask Connection**:
   - Open MetaMask
   - Go to Settings → Connected Sites
   - Remove your site if listed, then reconnect

### Issue 3: JavaScript Errors
**Symptoms**: Console shows errors
**Common Errors & Fixes**:

```javascript
// Error: "ethereum is undefined"
// Fix: MetaMask not installed or not injected yet
if (typeof window.ethereum === 'undefined') {
  console.log('Install MetaMask');
}

// Error: "User rejected the request"
// Fix: User clicked "Cancel" in MetaMask
// Code: 4001

// Error: "Already processing eth_requestAccounts"
// Fix: Multiple requests sent simultaneously
// Wait for first request to complete
```

## 🛠 **Advanced Debugging**

### Check MetaMask Injection
Open browser console and run:
```javascript
console.log('MetaMask available:', typeof window.ethereum !== 'undefined');
console.log('Ethereum object:', window.ethereum);
console.log('Is MetaMask:', window.ethereum?.isMetaMask);
```

### Manual MetaMask Test
Run this in browser console:
```javascript
window.ethereum.request({ method: 'eth_requestAccounts' })
  .then(accounts => console.log('Success:', accounts))
  .catch(error => console.error('Error:', error));
```

### Check Network
```javascript
window.ethereum.request({ method: 'eth_chainId' })
  .then(chainId => console.log('Chain ID:', chainId))
  .catch(error => console.error('Network error:', error));
```

## 📋 **Troubleshooting Checklist**

- [ ] MetaMask extension installed and enabled
- [ ] MetaMask is unlocked (not showing lock screen)
- [ ] Browser allows popups for localhost
- [ ] No JavaScript errors in console
- [ ] MetaMask is connected to the correct network
- [ ] Site has permission to connect to MetaMask
- [ ] No other dApps are currently requesting MetaMask access
- [ ] Browser is up to date
- [ ] MetaMask extension is up to date

## 🔧 **Quick Fixes**

1. **Refresh Everything**:
   - Close all browser tabs
   - Restart browser
   - Unlock MetaMask
   - Try again

2. **Reset MetaMask**:
   - MetaMask → Settings → Advanced → Reset Account
   - (This clears transaction history but keeps wallet)

3. **Clear Browser Data**:
   - Clear cache and cookies for localhost
   - Restart browser

4. **Try Different Browser**:
   - Test in Chrome, Firefox, or Edge
   - Some browsers have different MetaMask behavior

## 📞 **If Still Not Working**

1. **Check Browser Console**: Look for specific error messages
2. **Check MetaMask Console**: Open MetaMask → Settings → Advanced → Developer Mode
3. **Try Standalone Test**: Open `metamask_test.html` directly in browser
4. **Network Issues**: Try switching MetaMask to different network (Mainnet, Sepolia)
5. **Extension Conflicts**: Disable other browser extensions temporarily

## 🎯 **Expected Behavior**

When working correctly:
1. **Direct Test**: Immediate MetaMask popup asking to connect
2. **Test MetaMask**: Shows connected account info
3. **Investment**: MetaMask popup asking to confirm transaction
4. **Console Logs**: Clear step-by-step progress messages

The key is that `window.ethereum.request({ method: 'eth_requestAccounts' })` should ALWAYS trigger a MetaMask popup if MetaMask is properly installed and unlocked.
