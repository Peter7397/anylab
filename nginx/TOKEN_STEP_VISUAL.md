# Visual Guide: Cloudflare API Token (Step-by-Step)

## 🎯 Quick Navigation

**Direct Link:** https://dash.cloudflare.com/profile/api-tokens

## 📍 Step-by-Step with Screenshots Description

### Page 1: API Tokens Page
```
┌─────────────────────────────────────────┐
│  Cloudflare Dashboard                   │
│  ─────────────────────────────────────  │
│                                         │
│  [← Profile Icon]  [Settings]  [Help]  │
│                                         │
│  My Profile                             │
│  ─────────────────────────────────────  │
│  [API Tokens] ← Click this tab          │
│  [Authentication]                        │
│  [Notifications]                        │
│                                         │
│  API Tokens                              │
│  ─────────────────────────────────────  │
│                                         │
│  Create Token  [Button]                 │
│                                         │
│  API Token Templates:                   │
│  ┌───────────────────────────────────┐ │
│  │ Edit zone DNS                      │ │
│  │ Use this template to create...     │ │
│  │                    [Use template]  │ │ ← Click this
│  └───────────────────────────────────┘ │
│                                         │
└─────────────────────────────────────────┘
```

### Page 2: Template Configuration
```
┌─────────────────────────────────────────┐
│  Create API Token                       │
│  ─────────────────────────────────────  │
│                                         │
│  Token name:                            │
│  [Edit zone DNS             ]          │ ← Optional: rename
│                                         │
│  Permissions:                           │
│  ✅ Zone → Zone → Read                  │ (Already set)
│  ✅ Zone → DNS → Edit                  │ (Already set)
│                                         │
│  Zone Resources:                         │
│  ┌───────────────────────────────────┐ │
│  │ Include ▼                          │ │ ← Select "Include"
│  │   [All zones]                      │ │
│  │   [Specific zone ▼]                │ │ ← Select this
│  │                                     │ │
│  │   [dpdns.org ▼]                    │ │ ← Select this
│  │     - dpdns.org                    │ │
│  │     - example.com                  │ │
│  │     - other.com                    │ │
│  └───────────────────────────────────┘ │
│                                         │
│  [Continue to summary]                  │ ← Click this
└─────────────────────────────────────────┘
```

### Page 3: Summary Page
```
┌─────────────────────────────────────────┐
│  API Token Summary                      │
│  ─────────────────────────────────────  │
│                                         │
│  Review your token configuration:       │
│                                         │
│  Token name: Edit zone DNS              │
│                                         │
│  Permissions:                           │
│  • Zone → Zone → Read                   │
│  • Zone → DNS → Edit                    │
│                                         │
│  Zone Resources:                         │
│  • Include → dpdns.org                  │
│                                         │
│  [← Back]  [Create Token]               │ ← Click this
└─────────────────────────────────────────┘
```

### Page 4: Token Display (MOST IMPORTANT!)
```
┌─────────────────────────────────────────┐
│  API Token Created!                     │
│  ─────────────────────────────────────  │
│                                         │
│  ⚠️  Make sure to copy your token now. │
│  You won't be able to see it again!      │
│                                         │
│  Your API Token:                        │
│  ┌───────────────────────────────────┐ │
│  │ abc123def456ghi789jkl012mno345... │ │ ← Copy this!
│  └───────────────────────────────────┘ │
│  [Copy]                                 │ ← Click to copy
│                                         │
│  ✅ Token copied to clipboard          │
│                                         │
│  [Continue]                             │
└─────────────────────────────────────────┘
```

## 🔑 Key Points to Remember

1. **Zone Selection:** Select `dpdns.org` (root domain), not `anylab.dpdns.org`
2. **Permissions:** Zone Read + DNS Edit (template sets this automatically)
3. **Copy Token:** Copy it immediately - you won't see it again!
4. **Save Securely:** Store it somewhere safe for the setup script

## ✅ What You Should See

After creating, on the API Tokens page:
```
Your Token:
┌─────────────────────────────────────────┐
│ Edit zone DNS                           │
│ Created: Just now                       │
│ Last used: Never                        │
│ Status: Active                          │
│                                         │
│ Permissions: Zone Read, DNS Edit        │
│ Zone: dpdns.org                         │
│                                         │
│ [Regenerate] [Revoke]                   │
└─────────────────────────────────────────┘
```

## 🚨 Common Mistakes to Avoid

1. ❌ **Selecting wrong zone** - Make sure it's `dpdns.org`, not `anylab.dpdns.org`
2. ❌ **Missing DNS Edit permission** - Must have both Zone Read AND DNS Edit
3. ❌ **Not copying token** - Copy it immediately or you'll need to create a new one
4. ❌ **Using wrong account** - Make sure you're logged into the account that manages `dpdns.org`

## 📝 Quick Reference

**URL:** https://dash.cloudflare.com/profile/api-tokens

**Template:** "Edit zone DNS"

**Zone to Select:** `dpdns.org`

**Permissions Needed:**
- Zone → Zone → Read
- Zone → DNS → Edit

**Token Length:** ~40-50 characters

**Next Step:** Run setup script with your token
