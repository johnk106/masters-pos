#!/usr/bin/env python
"""
Comprehensive Security Audit and Test Runner
Runs security audit, applies fixes, and generates comprehensive reports.
"""

import os
import sys
import django
import json
from datetime import datetime
from pathlib import Path

# Add the parent directory to the path so we can import from admin
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin.settings')
django.setup()

from .security_audit import run_security_audit
from .security_fixer import apply_security_fixes
from .test_role_based_access import run_security_tests


class SecurityAuditRunner:
    """Main class to run comprehensive security audit and testing"""
    
    def __init__(self):
        self.results = {
            'audit_report': None,
            'fixes_applied': None,
            'test_results': None,
            'timestamp': datetime.now().isoformat(),
            'summary': {}
        }
    
    def run_complete_audit(self):
        """Run complete security audit process"""
        print("=" * 60)
        print("COMPREHENSIVE SECURITY AUDIT")
        print("=" * 60)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Step 1: Run security audit
        print("STEP 1: Running Security Audit...")
        print("-" * 30)
        audit_report, recommended_fixes = run_security_audit()
        self.results['audit_report'] = audit_report
        self.results['recommended_fixes'] = recommended_fixes
        
        # Step 2: Apply security fixes (with user confirmation)
        print("\nSTEP 2: Applying Security Fixes...")
        print("-" * 30)
        
        if recommended_fixes:
            print(f"Found {len(recommended_fixes)} views that need security fixes.")
            
            # In production, you might want to ask for confirmation
            # For automated testing, we'll apply fixes automatically
            apply_fixes = True
            
            if apply_fixes:
                fixer = apply_security_fixes()
                self.results['fixes_applied'] = {
                    'total_fixes': len(fixer.fixes_applied),
                    'files_modified': len(set(fix['file'] for fix in fixer.fixes_applied)),
                    'fixes_detail': fixer.fixes_applied
                }
            else:
                print("Skipping fix application.")
                self.results['fixes_applied'] = None
        else:
            print("No security fixes needed!")
            self.results['fixes_applied'] = None
        
        # Step 3: Run security tests
        print("\nSTEP 3: Running Security Tests...")
        print("-" * 30)
        test_results = run_security_tests()
        self.results['test_results'] = test_results
        
        # Step 4: Generate summary
        self.generate_summary()
        
        # Step 5: Generate reports
        self.generate_reports()
        
        print("\n" + "=" * 60)
        print("SECURITY AUDIT COMPLETE")
        print("=" * 60)
    
    def generate_summary(self):
        """Generate overall security summary"""
        audit = self.results['audit_report']
        fixes = self.results['fixes_applied']
        tests = self.results['test_results']
        
        summary = {
            'overall_security_score': self.calculate_overall_score(),
            'total_views_audited': audit['total_views'] if audit else 0,
            'unprotected_views_found': audit['unprotected_views'] if audit else 0,
            'fixes_applied': fixes['total_fixes'] if fixes else 0,
            'test_success_rate': tests['success_rate'] if tests else 0,
            'recommendations': self.generate_recommendations()
        }
        
        self.results['summary'] = summary
    
    def calculate_overall_score(self):
        """Calculate overall security score"""
        audit = self.results['audit_report']
        tests = self.results['test_results']
        
        if not audit or not tests:
            return 0
        
        # Weight: 60% audit score, 40% test success rate
        audit_score = audit.get('security_score', 0)
        test_score = tests.get('success_rate', 0)
        
        overall_score = (audit_score * 0.6) + (test_score * 0.4)
        return round(overall_score, 1)
    
    def generate_recommendations(self):
        """Generate security recommendations"""
        recommendations = []
        
        audit = self.results['audit_report']
        tests = self.results['test_results']
        
        if audit and audit['unprotected_views'] > 0:
            recommendations.append(
                f"Apply security decorators to {audit['unprotected_views']} unprotected views"
            )
        
        if tests and tests['failures'] > 0:
            recommendations.append(
                f"Fix {tests['failures']} failing security tests"
            )
        
        if not recommendations:
            recommendations.append("Security posture is good! Continue monitoring.")
        
        return recommendations
    
    def generate_reports(self):
        """Generate comprehensive reports"""
        # Generate JSON report
        self.generate_json_report()
        
        # Generate HTML report
        self.generate_html_report()
        
        # Generate markdown report
        self.generate_markdown_report()
    
    def generate_json_report(self):
        """Generate JSON report"""
        report_path = Path(__file__).parent / 'security_audit_report.json'
        
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"JSON report generated: {report_path}")
    
    def generate_html_report(self):
        """Generate HTML report"""
        report_path = Path(__file__).parent / 'security_audit_report.html'
        
        html_content = self.create_html_report()
        
        with open(report_path, 'w') as f:
            f.write(html_content)
        
        print(f"HTML report generated: {report_path}")
    
    def create_html_report(self):
        """Create HTML report content"""
        summary = self.results['summary']
        audit = self.results['audit_report']
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Security Audit Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; }}
        .score {{ font-size: 24px; font-weight: bold; color: #28a745; }}
        .score.warning {{ color: #ffc107; }}
        .score.danger {{ color: #dc3545; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .table {{ width: 100%; border-collapse: collapse; }}
        .table th, .table td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
        .table th {{ background-color: #f8f9fa; }}
        .alert {{ padding: 10px; margin: 10px 0; border-radius: 4px; }}
        .alert-success {{ background-color: #d4edda; color: #155724; }}
        .alert-warning {{ background-color: #fff3cd; color: #856404; }}
        .alert-danger {{ background-color: #f8d7da; color: #721c24; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Security Audit Report</h1>
        <p>Generated: {self.results['timestamp']}</p>
        <div class="score {'danger' if summary['overall_security_score'] < 70 else 'warning' if summary['overall_security_score'] < 90 else ''}">
            Overall Security Score: {summary['overall_security_score']}%
        </div>
    </div>

    <div class="section">
        <h2>Summary</h2>
        <table class="table">
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Total Views Audited</td><td>{summary['total_views_audited']}</td></tr>
            <tr><td>Unprotected Views Found</td><td>{summary['unprotected_views_found']}</td></tr>
            <tr><td>Fixes Applied</td><td>{summary['fixes_applied']}</td></tr>
            <tr><td>Test Success Rate</td><td>{summary['test_success_rate']:.1f}%</td></tr>
        </table>
    </div>

    <div class="section">
        <h2>Recommendations</h2>
        <ul>
        """
        
        for rec in summary['recommendations']:
            html += f"<li>{rec}</li>"
        
        html += """
        </ul>
    </div>
        """
        
        if audit and audit['unprotected_views'] > 0:
            html += """
    <div class="section">
        <h2>Unprotected Views</h2>
        <div class="alert alert-warning">
            The following views were found to be unprotected and may need security decorators:
        </div>
        <table class="table">
            <tr><th>View</th><th>Namespace</th><th>Pattern</th></tr>
            """
            
            for view in audit['unprotected_details']:
                if view['should_protect']:
                    html += f"""
            <tr>
                <td>{view['view_name']}</td>
                <td>{view['namespace']}</td>
                <td>{view['pattern']}</td>
            </tr>
                    """
            
            html += """
        </table>
    </div>
            """
        
        html += """
</body>
</html>
        """
        
        return html
    
    def generate_markdown_report(self):
        """Generate Markdown report"""
        report_path = Path(__file__).parent / 'SECURITY_AUDIT_REPORT.md'
        
        summary = self.results['summary']
        audit = self.results['audit_report']
        tests = self.results['test_results']
        
        markdown = f"""# Security Audit Report

**Generated:** {self.results['timestamp']}
**Overall Security Score:** {summary['overall_security_score']}%

## Executive Summary

This report provides a comprehensive security audit of the Django admin project, including:
- Route protection analysis
- Role-based access control testing
- Automated security fix application
- Comprehensive test results

## Key Metrics

| Metric | Value |
|--------|-------|
| Total Views Audited | {summary['total_views_audited']} |
| Unprotected Views Found | {summary['unprotected_views_found']} |
| Fixes Applied | {summary['fixes_applied']} |
| Test Success Rate | {summary['test_success_rate']:.1f}% |

## Security Score Breakdown

- **Audit Score:** {audit['security_score']:.1f}% (Route Protection Coverage)
- **Test Score:** {tests['success_rate']:.1f}% (Role-Based Access Tests)
- **Overall Score:** {summary['overall_security_score']}%

## Recommendations

"""
        
        for rec in summary['recommendations']:
            markdown += f"- {rec}\n"
        
        if audit and audit['unprotected_views'] > 0:
            markdown += f"""
## Unprotected Views ({audit['unprotected_views']} found)

The following views were identified as needing security protection:

| View | Namespace | Pattern | Reason |
|------|-----------|---------|---------|
"""
            
            for view in audit['unprotected_details']:
                if view['should_protect']:
                    markdown += f"| {view['view_name']} | {view['namespace']} | {view['pattern']} | Sensitive endpoint |\n"
        
        if self.results['fixes_applied']:
            fixes = self.results['fixes_applied']
            markdown += f"""
## Security Fixes Applied ({fixes['total_fixes']} fixes)

The following security decorators were automatically applied:

| View | Decorator | File |
|------|-----------|------|
"""
            
            for fix in fixes['fixes_detail']:
                markdown += f"| {fix['view']} | {fix['decorator']} | {fix['file']} |\n"
        
        if tests and (tests['failures'] > 0 or tests['errors'] > 0):
            markdown += f"""
## Test Issues

### Failures ({tests['failures']} found)
"""
            
            for failure in tests.get('failure_details', []):
                markdown += f"- **{failure[0]}:** {failure[1]}\n"
            
            if tests['errors'] > 0:
                markdown += f"""
### Errors ({tests['errors']} found)
"""
                
                for error in tests.get('error_details', []):
                    markdown += f"- **{error[0]}:** {error[1]}\n"
        
        markdown += """
## Next Steps

1. Review and verify all applied security fixes
2. Address any failing tests
3. Implement additional role-based restrictions as needed
4. Schedule regular security audits
5. Monitor for new unprotected endpoints

## Security Best Practices

- Always use appropriate role-based decorators on sensitive views
- Regularly audit URL patterns for missing protection
- Test access control with different user roles
- Keep security middleware updated
- Monitor for unauthorized access attempts

---
*Report generated by Django Security Audit Tool*
"""
        
        with open(report_path, 'w') as f:
            f.write(markdown)
        
        print(f"Markdown report generated: {report_path}")
    
    def print_final_summary(self):
        """Print final summary to console"""
        summary = self.results['summary']
        
        print("\n" + "=" * 60)
        print("FINAL SECURITY AUDIT SUMMARY")
        print("=" * 60)
        print(f"Overall Security Score: {summary['overall_security_score']}%")
        print(f"Views Audited: {summary['total_views_audited']}")
        print(f"Unprotected Views: {summary['unprotected_views_found']}")
        print(f"Fixes Applied: {summary['fixes_applied']}")
        print(f"Test Success Rate: {summary['test_success_rate']:.1f}%")
        
        print("\nRecommendations:")
        for rec in summary['recommendations']:
            print(f"- {rec}")
        
        print("\nReports generated in admin/tests/:")
        print("- security_audit_report.json")
        print("- security_audit_report.html")
        print("- SECURITY_AUDIT_REPORT.md")


def main():
    """Main function to run the complete security audit"""
    runner = SecurityAuditRunner()
    runner.run_complete_audit()
    runner.print_final_summary()
    
    return runner.results


if __name__ == "__main__":
    main()