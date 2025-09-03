# Security Testing and Audit Tools

This directory contains comprehensive security testing and audit tools for the Django Admin project.

## Files Overview

### Security Audit Tools
- **`simple_security_audit.py`** - Automated security audit scanner
- **`apply_security_fixes.py`** - Automated security decorator application
- **`security_summary.py`** - Security status summary and reporting

### Test Suites
- **`test_security_corrected.py`** - Comprehensive role-based access control tests
- **`test_security_comprehensive.py`** - Original comprehensive security tests

## Quick Start

### 1. Run Security Audit
```bash
python3 tests/simple_security_audit.py
```
This will:
- Scan all view functions for security decorators
- Generate a protection rate report
- Identify unprotected views
- Save results to `security_audit_report.json`

### 2. Apply Security Fixes
```bash
python3 tests/apply_security_fixes.py
```
This will:
- Automatically apply appropriate security decorators
- Create backups of all modified files
- Generate a fixes report
- Save results to `security_fixes_report.json`

### 3. Run Security Tests
```bash
python3 manage.py test tests.test_security_corrected
```
This will:
- Test admin user access
- Test restricted user blocking
- Test manager-level permissions
- Verify security middleware functionality

### 4. View Security Summary
```bash
python3 tests/security_summary.py
```
This will:
- Display comprehensive security metrics
- Show applied fixes breakdown
- List unprotected views
- Provide recommendations

## Security Levels

### Admin Only (`@admin_only`)
- User management
- Role management
- Permission management

### Manager or Above (`@manager_or_above`)
- Financial reports
- Expense management
- Purchase management
- Supplier management

### Login Required (`@login_required`)
- Inventory management
- Sales operations
- Customer management
- Profile settings

### Public (No protection)
- Homepage
- FAQ pages
- Login/Logout functionality

## Backup and Restore

### Create Backups
Backups are automatically created when applying security fixes.

### Restore from Backups
```bash
python3 tests/apply_security_fixes.py --restore
```

## CI/CD Integration

### Add to CI Pipeline
```yaml
- name: Run Security Audit
  run: python3 tests/simple_security_audit.py

- name: Run Security Tests
  run: python3 manage.py test tests.test_security_corrected
```

## Monitoring

### Monthly Security Audit
Set up a monthly cron job:
```bash
0 0 1 * * cd /path/to/admin && python3 tests/simple_security_audit.py
```

### Security Alerts
Monitor the protection rate and alert if it drops below 80%:
```bash
python3 tests/simple_security_audit.py && python3 -c "
import json
with open('security_audit_report.json') as f:
    data = json.load(f)
    if data['protection_rate'] < 80:
        print('ALERT: Protection rate below 80%')
"
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **Permission Errors**: Check file permissions for backup creation
3. **Template Errors**: Some tests may fail due to missing templates (expected)

### Debug Mode
Run with verbose output:
```bash
python3 tests/simple_security_audit.py --verbose
```

## Security Best Practices

1. **Regular Audits**: Run security audits monthly
2. **Test Coverage**: Include security tests in CI/CD
3. **Code Review**: Review new views for appropriate protection
4. **Documentation**: Document security decisions
5. **Monitoring**: Monitor security metrics over time

## Report Files

- **`security_audit_report.json`** - Detailed audit results
- **`security_fixes_report.json`** - Applied fixes documentation
- **`SECURITY_AUDIT_REPORT.md`** - Comprehensive security report

## Support

For issues or questions about the security tools:
1. Check the logs in the terminal output
2. Review the generated JSON reports
3. Examine the backup files if restoration is needed
4. Run the security summary for current status