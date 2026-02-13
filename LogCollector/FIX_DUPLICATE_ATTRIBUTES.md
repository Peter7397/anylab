# Fix Duplicate Assembly Attribute Errors

## Problem

You're seeing errors like:
```
CS0579: Duplicate 'System.Reflection.AssemblyVersionAttribute' attribute
```

This happens when assembly attributes are defined in multiple places.

## Solution

### Step 1: Clean Build Output

1. **In Visual Studio:**
   - Go to `Build` → `Clean Solution`
   - Then `Build` → `Rebuild Solution`

2. **Or via Command Line:**
   ```bash
   dotnet clean
   dotnet build
   ```

### Step 2: Delete obj and bin Folders (if Step 1 doesn't work)

1. **Close Visual Studio**
2. **Delete these folders:**
   - `LogCollector\obj\`
   - `LogCollector\bin\`
   - `LogCollector\PingFileGenerator\obj\`
   - `LogCollector\PingFileGenerator\bin\`
3. **Reopen Visual Studio**
4. **Rebuild the solution**

### Step 3: Check Solution Structure

If `PingFileGenerator` is included in the same solution as `Remotecollect`, make sure:
- They are separate projects
- They don't reference each other (unless needed)
- Each has its own `obj` and `bin` folders

## What I Fixed

I've added `<GenerateAssemblyInfo>false</GenerateAssemblyInfo>` to `Remotecollect.csproj` to prevent auto-generation conflicts.

## If Errors Persist

1. **Check for manual AssemblyInfo.cs files:**
   - Look for `Properties\AssemblyInfo.cs` files
   - If found, either delete them or remove duplicate attributes

2. **Verify project references:**
   - Ensure PingFileGenerator is not incorrectly referenced by Remotecollect
   - They should be independent projects

3. **Clean and rebuild:**
   ```bash
   dotnet clean
   dotnet build
   ```
