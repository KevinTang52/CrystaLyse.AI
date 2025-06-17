# CrystaLyse.AI Python CLI Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the CrystaLyse.AI Python CLI.

## 📋 Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Installation Issues](#installation-issues)
3. [API Configuration Issues](#api-configuration-issues)
4. [Interactive Shell Issues](#interactive-shell-issues)
5. [Analysis Issues](#analysis-issues)
6. [Visualization Issues](#visualization-issues)
7. [Performance Issues](#performance-issues)
8. [Error Messages](#common-error-messages)
9. [Getting Help](#getting-help)

## 🔍 Quick Diagnostics

### Step 1: Check System Status
```bash
crystalyse status
```

This command will show you:
- ✅/❌ API key configuration
- Default model settings
- Rate limits and capabilities
- System requirements

### Step 2: Verify Installation
```bash
# Check if crystalyse is installed
which crystalyse

# Check Python version (must be 3.10+)
python --version

# Check installed packages
pip list | grep crystalyse
```

### Step 3: Test Basic Functionality
```bash
# Test help command
crystalyse --help

# Test examples
crystalyse examples

# Test one-time analysis (requires API key)
crystalyse analyze "test query" --temperature 0.1
```

## 🛠 Installation Issues

### Issue: `crystalyse: command not found`

**Symptoms:**
```bash
$ crystalyse
bash: crystalyse: command not found
```

**Solutions:**

1. **Verify Installation:**
   ```bash
   cd /path/to/CrystaLyse.AI
   pip install -e .
   ```

2. **Check Python Path:**
   ```bash
   which python
   python -m pip list | grep crystalyse
   ```

3. **Use Python Module Directly:**
   ```bash
   python -m crystalyse.cli
   ```

4. **Fix PATH Issues:**
   ```bash
   # Add to ~/.bashrc or ~/.zshrc
   export PATH="$HOME/.local/bin:$PATH"
   source ~/.bashrc
   ```

### Issue: `ModuleNotFoundError: No module named 'crystalyse'`

**Symptoms:**
```bash
ModuleNotFoundError: No module named 'crystalyse'
```

**Solutions:**

1. **Install in Development Mode:**
   ```bash
   cd /path/to/CrystaLyse.AI
   pip install -e .
   ```

2. **Check Virtual Environment:**
   ```bash
   # Activate the correct virtual environment
   source venv/bin/activate  # or your venv path
   pip install -e .
   ```

3. **Install Dependencies:**
   ```bash
   pip install -e ".[all]"  # Install with all optional dependencies
   ```

### Issue: `ImportError: No module named 'prompt_toolkit'`

**Symptoms:**
```bash
ImportError: No module named 'prompt_toolkit'
```

**Solutions:**

1. **Install Missing Dependencies:**
   ```bash
   pip install prompt-toolkit>=3.0.0
   ```

2. **Reinstall with Dependencies:**
   ```bash
   pip install -e ".[all]"
   ```

3. **Use Requirements File:**
   ```bash
   pip install -r requirements.txt  # if available
   ```

## 🔑 API Configuration Issues

### Issue: `❌ Error: OpenAI API key not found!`

**Symptoms:**
```bash
❌ Error: OpenAI API key not found!
Set OPENAI_MDG_API_KEY or OPENAI_API_KEY environment variable.
```

**Solutions:**

1. **Set API Key:**
   ```bash
   export OPENAI_MDG_API_KEY="your_api_key_here"
   
   # Or for regular OpenAI API
   export OPENAI_API_KEY="your_api_key_here"
   ```

2. **Make Permanent:**
   ```bash
   # Add to ~/.bashrc or ~/.zshrc
   echo 'export OPENAI_MDG_API_KEY="your_api_key_here"' >> ~/.bashrc
   source ~/.bashrc
   ```

3. **Verify Configuration:**
   ```bash
   crystalyse status
   # Should show ✅ Configured
   ```

### Issue: `401 Unauthorized` or `Invalid API Key`

**Symptoms:**
```bash
401 Unauthorized: Invalid API key
```

**Solutions:**

1. **Verify API Key:**
   ```bash
   echo $OPENAI_MDG_API_KEY
   # Should display your API key (be careful not to share this!)
   ```

2. **Test API Key:**
   ```bash
   curl -H "Authorization: Bearer $OPENAI_MDG_API_KEY" \
        https://api.openai.com/v1/models
   ```

3. **Check Key Format:**
   - Should start with `sk-`
   - Should be exactly the key from OpenAI dashboard
   - No extra spaces or characters

### Issue: Rate Limit Exceeded

**Symptoms:**
```bash
Rate limit exceeded. Please wait and try again.
```

**Solutions:**

1. **Wait and Retry:**
   ```bash
   # Wait a few minutes and try again
   crystalyse analyze "your query"
   ```

2. **Use Creative Mode:**
   ```bash
   crystalyse shell
   /mode creative
   # Creative mode uses fewer tokens
   ```

3. **Check Rate Limits:**
   ```bash
   crystalyse status
   # Shows your rate limits and usage
   ```

## 🖥 Interactive Shell Issues

### Issue: Shell Freezes or Becomes Unresponsive

**Symptoms:**
- Shell stops responding to input
- No prompt appears
- Ctrl+C doesn't work

**Solutions:**

1. **Force Quit and Restart:**
   ```bash
   # Force quit with Ctrl+Z, then kill
   kill %1
   
   # Or force quit the process
   pkill -f crystalyse
   ```

2. **Check Terminal Compatibility:**
   ```bash
   # Test with different terminal
   # Some terminals have prompt_toolkit issues
   ```

3. **Reset Terminal:**
   ```bash
   reset
   crystalyse shell
   ```

### Issue: Command History Not Working

**Symptoms:**
- Up/down arrows don't show previous commands
- No auto-suggestions

**Solutions:**

1. **Check History File:**
   ```bash
   ls -la ~/.crystalyse_history
   # Should exist and be readable
   ```

2. **Fix Permissions:**
   ```bash
   chmod 644 ~/.crystalyse_history
   ```

3. **Clear and Restart:**
   ```bash
   rm ~/.crystalyse_history
   crystalyse shell
   ```

### Issue: Tab Completion Not Working

**Symptoms:**
- Tab key doesn't complete commands
- No suggestions appear

**Solutions:**

1. **Check Prompt Toolkit Version:**
   ```bash
   pip show prompt-toolkit
   # Should be >= 3.0.0
   ```

2. **Reinstall Prompt Toolkit:**
   ```bash
   pip uninstall prompt-toolkit
   pip install prompt-toolkit>=3.0.0
   ```

## 🔬 Analysis Issues

### Issue: Analysis Takes Too Long

**Symptoms:**
- Analysis runs for many minutes
- No progress indicators
- Eventually times out

**Solutions:**

1. **Use Creative Mode:**
   ```bash
   crystalyse shell
   /mode creative
   # Much faster analysis
   ```

2. **Simplify Query:**
   ```bash
   # Instead of: "Design complex multi-component material with specific properties..."
   # Try: "Design a simple battery material"
   ```

3. **Check Internet Connection:**
   ```bash
   ping api.openai.com
   # Should have stable, fast connection
   ```

4. **Use Streaming:**
   ```bash
   crystalyse analyze "your query" --stream
   # Shows progress in real-time
   ```

### Issue: Analysis Returns Empty Results

**Symptoms:**
```bash
⚠️ No results returned
```

**Solutions:**

1. **Rephrase Query:**
   ```bash
   # Be more specific
   # Instead of: "find materials"
   # Try: "design cathode materials for lithium batteries"
   ```

2. **Check Agent Initialization:**
   ```bash
   crystalyse shell
   # Should show "✅ CrystaLyse.AI ready!"
   ```

3. **Switch Modes:**
   ```bash
   # If rigorous mode fails, try creative
   /mode creative
   your query here
   ```

### Issue: "Agent Not Initialized" Error

**Symptoms:**
```bash
❌ Agent not initialized
```

**Solutions:**

1. **Check API Key:**
   ```bash
   crystalyse status
   # Must show ✅ Configured
   ```

2. **Restart Shell:**
   ```bash
   # Exit and restart
   /exit
   crystalyse shell
   ```

3. **Check Network:**
   ```bash
   curl -I https://api.openai.com
   # Should return 200 OK
   ```

## 🎨 Visualization Issues

### Issue: `/view` Command Does Nothing

**Symptoms:**
- `/view` command runs but no browser opens
- No error messages

**Solutions:**

1. **Check for Structure:**
   ```bash
   # Run analysis first to generate structure
   design a simple crystal structure
   /view
   ```

2. **Check Browser:**
   ```bash
   # Test if browser opens
   python -c "import webbrowser; webbrowser.open('https://google.com')"
   ```

3. **Check Visualization Dependencies:**
   ```bash
   pip install "crystalyse[visualization]"
   ```

### Issue: Browser Opens but Shows Blank Page

**Symptoms:**
- Browser opens successfully
- Page is blank or shows error

**Solutions:**

1. **Check JavaScript:**
   - Open browser developer tools (F12)
   - Look for JavaScript errors in console

2. **Try Different Browser:**
   ```bash
   # Set default browser
   export BROWSER="firefox"  # or "chrome", "safari"
   ```

3. **Check File Path:**
   - Look at the URL in browser
   - Verify the temp file exists

### Issue: 3D Viewer Not Loading

**Symptoms:**
- Page loads but 3D viewer is empty
- "3DMol.js failed to load" error

**Solutions:**

1. **Check Internet Connection:**
   - 3DMol.js loads from CDN
   - Requires internet access

2. **Wait for Loading:**
   - Large structures take time to render
   - Check browser loading indicator

3. **Try Simpler Structure:**
   ```bash
   # Request simpler crystal structure
   design a simple cubic crystal
   /view
   ```

## ⚡ Performance Issues

### Issue: CLI Starts Slowly

**Symptoms:**
- Long delay before shell appears
- "Initializing..." takes minutes

**Solutions:**

1. **Check Dependencies:**
   ```bash
   # Some packages are slow to import
   time python -c "import crystalyse"
   ```

2. **Update Packages:**
   ```bash
   pip install --upgrade openai openai-agents
   ```

3. **Clear Cache:**
   ```bash
   rm -rf ~/.cache/pip
   pip install -e . --force-reinstall
   ```

### Issue: High Memory Usage

**Symptoms:**
- System becomes slow
- High RAM usage during analysis

**Solutions:**

1. **Limit Session History:**
   ```bash
   # Export and clear session regularly
   /export
   /exit
   crystalyse shell  # Start fresh
   ```

2. **Use Creative Mode:**
   ```bash
   /mode creative
   # Uses less memory than rigorous mode
   ```

3. **Monitor Usage:**
   ```bash
   top -p $(pgrep -f crystalyse)
   ```

## 🚨 Common Error Messages

### `ConnectionError: Unable to connect to OpenAI API`

**Cause:** Network connectivity issues

**Solutions:**
1. Check internet connection
2. Try again later (API might be down)
3. Check if behind corporate firewall
4. Verify DNS resolution: `nslookup api.openai.com`

### `TimeoutError: Request timed out`

**Cause:** Request took too long

**Solutions:**
1. Use creative mode for faster analysis
2. Simplify your query
3. Check network stability
4. Increase timeout in configuration

### `KeyboardInterrupt: Analysis interrupted`

**Cause:** User pressed Ctrl+C

**Solutions:**
1. This is normal - analysis was cancelled
2. Restart analysis if needed
3. Use `/exit` to quit properly

### `ValueError: Invalid mode 'xyz'`

**Cause:** Tried to set invalid analysis mode

**Solutions:**
1. Use only 'creative' or 'rigorous'
2. Check spelling: `/mode rigorous`

### `FileNotFoundError: No such file or directory`

**Cause:** Missing files or incorrect paths

**Solutions:**
1. Check working directory
2. Verify installation completeness
3. Reinstall: `pip install -e . --force-reinstall`

## 🆘 Getting Help

### Built-in Help
```bash
# General help
crystalyse --help

# Shell help
crystalyse shell
/help

# Examples
crystalyse examples
```

### Debug Mode
```bash
# Enable verbose output
export CRYSTALYSE_DEBUG=true
export CRYSTALYSE_VERBOSE=true
crystalyse shell
```

### Log Files
```bash
# Check for log files
ls ~/.crystalyse/
cat ~/.crystalyse/debug.log  # if exists
```

### System Information
```bash
# Gather system info for bug reports
python --version
pip list | grep -E "(crystalyse|openai|rich|prompt)"
crystalyse status
```

### Reporting Issues

When reporting issues, include:

1. **Error Message:** Full error text
2. **Command Used:** Exact command that failed
3. **System Info:** OS, Python version
4. **Configuration:** Output of `crystalyse status`
5. **Steps to Reproduce:** What you did before the error

### Contact Information

- **Documentation:** Check this troubleshooting guide first
- **Issues:** Create GitHub issue with system information
- **Questions:** Use discussion forums or community channels

## 🔧 Advanced Troubleshooting

### Debugging Network Issues
```bash
# Test API connectivity
curl -H "Authorization: Bearer $OPENAI_MDG_API_KEY" \
     https://api.openai.com/v1/models

# Test with verbose output
crystalyse analyze "test" --stream 2>&1 | tee debug.log
```

### Python Environment Issues
```bash
# Check Python environment
python -c "import sys; print(sys.path)"
python -c "import crystalyse; print(crystalyse.__file__)"

# Virtual environment check
which python
which pip
echo $VIRTUAL_ENV
```

### File Permission Issues
```bash
# Fix common permission issues
chmod +x ~/.local/bin/crystalyse
chmod 644 ~/.crystalyse_history
chmod -R 755 ~/.crystalyse/
```

### Clean Reinstall
```bash
# Complete clean reinstall
pip uninstall crystalyse
rm -rf ~/.crystalyse/
rm ~/.crystalyse_history
cd /path/to/CrystaLyse.AI
pip install -e . --force-reinstall
```

Remember: Most issues are resolved by checking API key configuration and ensuring all dependencies are properly installed. When in doubt, start with `crystalyse status` to verify your setup!