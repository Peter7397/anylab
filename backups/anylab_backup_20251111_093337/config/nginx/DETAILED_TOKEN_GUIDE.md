# Detailed Guide: Getting Cloudflare API Token (Step 2)

## What You Need
- A Cloudflare account with access to `dpdns.org` zone
- Admin access to the domain

## Step-by-Step Instructions

### Method 1: Using Template (Recommended - Easiest)

#### Step 1: Open Cloudflare Dashboard
1. Go to: **https://dash.cloudflare.com**
2. Log in to your Cloudflare account

#### Step 2: Navigate to API Tokens
You have two ways to get there:

**Option A:**
1. Click on your **profile icon** (top right corner)
2. Click **"My Profile"**
3. Click **"API Tokens"** tab (on the left sidebar)

**Option B:**
1. Go directly to: **https://dash.cloudflare.com/profile/api-tokens**

#### Step 3: Find the Template
1. Scroll down to the section called **"API Tokens"**
2. Look for **"Edit zone DNS"** template
3. You'll see it says:
   ```
   Edit zone DNS
   Use this template to create a token that can edit DNS records for a specific zone.
   ```
4. Click the **"Use template"** button (usually on the right side)

#### Step 4: Configure Token Permissions
After clicking "Use template", you'll see a configuration page:

**1. Token Name (Optional but recommended)**
   - You can leave it as "Edit zone DNS" or rename it
   - Example: "AnyLab SSL Certificate Token"
   - This helps you identify it later

**2. Permissions (Already set by template)**
   - Should show:
     - **Zone** → **Zone** → **Read** ✅
     - **Zone** → **DNS** → **Edit** ✅
   - These are already correct, don't change them

**3. Zone Resources (IMPORTANT!)**
   This is where you select which domain/zone:
   
   a. Find **"Zone Resources"** section
   
   b. You'll see options:
      - Include - All zones
      - Include - Specific zone
      - Exclude - All zones
   
   c. Select: **"Include"** → **"Specific zone"**
   
   d. A dropdown will appear
   
   e. Click the dropdown and select: **`dpdns.org`**
      - Note: Even though your site is `anylab.dpdns.org`, you select `dpdns.org`
      - This is the root domain/zone
      - It will work for all subdomains including `anylab.dpdns.org`
   
   f. Verify it shows: **"Include"** → **"dpdns.org"**

**4. Client IP Address Filtering (Optional)**
   - You can leave this empty (default)
   - Only needed if you want to restrict token to specific IP addresses

**5. TTL (Time to Live)**
   - You can leave this as default
   - This is how long the token is valid

#### Step 5: Review and Create
1. Scroll down to see the summary
2. Review what you've set:
   - Permissions: Zone Read, DNS Edit ✅
   - Zone Resources: Include → dpdns.org ✅
3. Click **"Continue to summary"** button (usually at bottom)

#### Step 6: Create Token
1. You'll see a summary page
2. Review everything one more time
3. Click **"Create Token"** button (blue button at bottom)

#### Step 7: COPY THE TOKEN IMMEDIATELY! ⚠️
**IMPORTANT:** This is the only time you'll see the token!

1. A screen will show your token (long string of letters and numbers)
2. It looks like: `abc123def456ghi789jkl012mno345pqr678stu901vwx234yz`
3. **COPY IT IMMEDIATELY** - Click the copy button or select all and copy
4. Save it somewhere safe:
   - Text file (not in the project folder)
   - Password manager
   - Notes app
   - You'll need it in Step 3

**⚠️ WARNING:** If you close this page without copying, you'll need to create a new token!

#### Step 8: Verify Token (Optional)
1. You can test the token works by going back to API Tokens page
2. You'll see your new token listed
3. You can see when it was created, last used, etc.
4. You can regenerate or revoke it if needed

---

### Method 2: Create Custom Token (If Template Not Available)

If you don't see the "Edit zone DNS" template, create a custom token:

#### Step 1: Navigate to API Tokens
1. Go to: **https://dash.cloudflare.com/profile/api-tokens**
2. Click **"Create Token"** button (top right)

#### Step 2: Create Custom Token
1. Click **"Create custom token"** button
2. You'll see a form with multiple sections

#### Step 3: Set Token Name
1. In **"Token name"** field, enter:
   - Example: "AnyLab SSL Certificate Token"
   - This helps you identify it later

#### Step 4: Set Permissions
You need to add two permissions:

**Permission 1: Zone Read**
1. Click **"Add"** or **"+"** button next to "Permissions"
2. In the dropdown, select:
   - **Zone** (first dropdown)
   - **Zone** (second dropdown)  
   - **Read** (third dropdown)
3. Click to confirm

**Permission 2: DNS Edit**
1. Click **"Add"** or **"+"** button again
2. Select:
   - **Zone** (first dropdown)
   - **DNS** (second dropdown)
   - **Edit** (third dropdown)
3. Click to confirm

You should now see:
- Zone → Zone → Read ✅
- Zone → DNS → Edit ✅

#### Step 5: Set Zone Resources
1. Find **"Zone Resources"** section
2. Click **"Add"** or **"+"** button
3. Select:
   - **Include** (from first dropdown)
4. Then select:
   - **Specific zone** (from second dropdown)
5. A third dropdown will appear
6. Select: **`dpdns.org`** from the dropdown
7. Verify it shows: **Include → dpdns.org**

#### Step 6: Continue to Summary
1. Scroll down to review
2. Click **"Continue to summary"** button

#### Step 7: Create Token
1. Review the summary
2. Click **"Create Token"** button

#### Step 8: Copy Token
1. **COPY THE TOKEN IMMEDIATELY** (same as Method 1)
2. Save it securely
3. You'll need it for the setup script

---

## What Your Token Should Look Like

- **Length:** About 40-50 characters
- **Format:** Mix of letters and numbers
- **Example:** `3a8b2c9d4e1f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5`
- **Important:** It's unique to your account

## Verify Token Has Correct Permissions

After creating, you can verify:

1. Go back to API Tokens page
2. Find your token in the list
3. Click on it to see details
4. Verify:
   - ✅ Permissions: Zone (Read), DNS (Edit)
   - ✅ Zone Resources: Include → dpdns.org

## Troubleshooting

### Issue: "Token not found" or "No zones available"
**Solution:**
- Make sure you're logged into the correct Cloudflare account
- Verify you have access to `dpdns.org` zone
- Check that `dpdns.org` appears in your zones list

### Issue: "Insufficient permissions"
**Solution:**
- Make sure token has both permissions:
  - Zone → Zone → Read
  - Zone → DNS → Edit
- Verify zone resources includes `dpdns.org`

### Issue: "Can't find dpdns.org in dropdown"
**Solution:**
- Make sure `dpdns.org` is in your Cloudflare account
- Check you're using the correct account
- Verify the domain is active in Cloudflare

### Issue: "Lost my token"
**Solution:**
- Create a new token (old one won't work anymore)
- You can revoke old tokens from the API Tokens page

## Security Best Practices

1. **Store Securely**
   - Don't commit to git
   - Don't share publicly
   - Use password manager or secure notes

2. **Limit Scope**
   - Only give permissions needed (Zone Read, DNS Edit)
   - Only for specific zone (dpdns.org)

3. **Monitor Usage**
   - Check API Tokens page periodically
   - Revoke if compromised

4. **Regenerate If Needed**
   - You can create new token anytime
   - Revoke old one after creating new

## Next Steps

Once you have the token:
1. Save it securely
2. Continue to Step 3: Run the setup script
3. The script will ask for your token
4. Paste it when prompted

## Quick Checklist

- [ ] Logged into Cloudflare Dashboard
- [ ] Navigated to API Tokens page
- [ ] Used "Edit zone DNS" template OR created custom token
- [ ] Set permissions: Zone Read + DNS Edit
- [ ] Selected zone: `dpdns.org`
- [ ] Created token
- [ ] **COPIED THE TOKEN** (most important!)
- [ ] Saved token securely
- [ ] Ready for Step 3

## Ready for Step 3?

Once you have your token, run:
```bash
cd /Volumes/Orico/Anylab103
sudo ./nginx/setup-cloudflare-ssl.sh
```

The script will ask for your token. Paste it when prompted!

