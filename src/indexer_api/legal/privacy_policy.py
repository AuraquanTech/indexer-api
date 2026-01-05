"""
Privacy Policy for IndexerAPI
Compliant with GDPR, CCPA, and international data protection regulations
Last Updated: January 2026
"""

PRIVACY_POLICY = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Privacy Policy - IndexerAPI</title>
    <style>
        :root { --primary: #00f3ff; --bg: #0a0a0f; --card: #111118; --text: #e0e0e0; --muted: #888; }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: var(--bg); color: var(--text); line-height: 1.7; padding: 40px 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: var(--primary); font-size: 2.5rem; margin-bottom: 10px; }
        h2 { color: var(--primary); font-size: 1.5rem; margin: 40px 0 20px; border-bottom: 1px solid #333; padding-bottom: 10px; }
        h3 { color: #fff; font-size: 1.2rem; margin: 25px 0 15px; }
        p, li { margin-bottom: 15px; color: var(--text); }
        ul, ol { padding-left: 25px; }
        .effective-date { color: var(--muted); margin-bottom: 30px; }
        .highlight { background: #1a1a2e; border-left: 3px solid var(--primary); padding: 15px 20px; margin: 20px 0; border-radius: 0 8px 8px 0; }
        a { color: var(--primary); }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { border: 1px solid #333; padding: 12px; text-align: left; }
        th { background: #1a1a2e; color: var(--primary); }
        .footer { margin-top: 60px; padding-top: 30px; border-top: 1px solid #333; color: var(--muted); font-size: 0.9rem; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Privacy Policy</h1>
        <p class="effective-date">Effective Date: January 5, 2026 | Last Updated: January 5, 2026</p>

        <div class="highlight">
            <strong>Summary:</strong> We collect only what's necessary to provide our service, we don't sell your data, and you have full control over your information. This policy explains our practices in detail.
        </div>

        <h2>1. Introduction</h2>
        <p>Ayrto Engineering ("Company," "we," "us," or "our") operates IndexerAPI, an enterprise file indexing and code analysis API service. This Privacy Policy describes how we collect, use, disclose, and protect your personal information when you use our services at indexer-api.com and related applications (collectively, the "Service").</p>
        <p>By accessing or using our Service, you acknowledge that you have read, understood, and agree to be bound by this Privacy Policy. If you do not agree with our policies and practices, please do not use our Service.</p>

        <h2>2. Information We Collect</h2>

        <h3>2.1 Information You Provide Directly</h3>
        <ul>
            <li><strong>Account Information:</strong> When you create an account, we collect your email address, organization name, and password (stored in hashed format).</li>
            <li><strong>Payment Information:</strong> When you make a purchase, payment details are processed directly by Stripe, Inc. We receive only a token reference, transaction ID, and the last four digits of your card. We never store full credit card numbers.</li>
            <li><strong>Communication Data:</strong> When you contact us for support, we collect the content of your messages, your email address, and any attachments you provide.</li>
            <li><strong>API Usage Data:</strong> File paths, metadata, and content you choose to index through our API.</li>
        </ul>

        <h3>2.2 Information Collected Automatically</h3>
        <ul>
            <li><strong>Log Data:</strong> IP address, browser type, operating system, referring URLs, pages visited, and timestamps.</li>
            <li><strong>Device Information:</strong> Device type, unique device identifiers, and mobile network information.</li>
            <li><strong>Usage Analytics:</strong> API call frequency, endpoints accessed, response times, and error rates.</li>
            <li><strong>Cookies and Tracking:</strong> We use essential cookies for authentication and optional analytics cookies (see Section 8).</li>
        </ul>

        <h3>2.3 Information from Third Parties</h3>
        <ul>
            <li><strong>Payment Processor:</strong> Stripe provides transaction confirmations and fraud prevention signals.</li>
            <li><strong>Authentication Providers:</strong> If you use SSO, we receive your email and name from the identity provider.</li>
        </ul>

        <h2>3. How We Use Your Information</h2>
        <table>
            <tr>
                <th>Purpose</th>
                <th>Legal Basis (GDPR)</th>
            </tr>
            <tr>
                <td>Provide and maintain the Service</td>
                <td>Contract performance</td>
            </tr>
            <tr>
                <td>Process payments and send receipts</td>
                <td>Contract performance</td>
            </tr>
            <tr>
                <td>Send service notifications and updates</td>
                <td>Legitimate interest</td>
            </tr>
            <tr>
                <td>Respond to support requests</td>
                <td>Contract performance</td>
            </tr>
            <tr>
                <td>Prevent fraud and abuse</td>
                <td>Legitimate interest</td>
            </tr>
            <tr>
                <td>Improve and optimize the Service</td>
                <td>Legitimate interest</td>
            </tr>
            <tr>
                <td>Comply with legal obligations</td>
                <td>Legal obligation</td>
            </tr>
            <tr>
                <td>Send marketing communications (with consent)</td>
                <td>Consent</td>
            </tr>
        </table>

        <h2>4. Data Sharing and Disclosure</h2>
        <p><strong>We do not sell, rent, or trade your personal information.</strong> We may share your information only in these circumstances:</p>

        <h3>4.1 Service Providers</h3>
        <ul>
            <li><strong>Stripe, Inc.</strong> - Payment processing (PCI-DSS compliant)</li>
            <li><strong>Railway</strong> - Cloud infrastructure hosting</li>
            <li><strong>Resend</strong> - Transactional email delivery</li>
        </ul>
        <p>All service providers are contractually bound to protect your data and use it only for the services they provide to us.</p>

        <h3>4.2 Legal Requirements</h3>
        <p>We may disclose your information if required by law, subpoena, court order, or government request, or to protect our rights, property, or safety.</p>

        <h3>4.3 Business Transfers</h3>
        <p>In the event of a merger, acquisition, or sale of assets, your information may be transferred. We will provide notice before your information becomes subject to a different privacy policy.</p>

        <h2>5. Data Retention</h2>
        <ul>
            <li><strong>Account Data:</strong> Retained while your account is active, plus 30 days after deletion request.</li>
            <li><strong>Indexed Content:</strong> Deleted immediately upon your request or account termination.</li>
            <li><strong>Payment Records:</strong> Retained for 7 years for tax and legal compliance.</li>
            <li><strong>Log Data:</strong> Retained for 90 days for security and debugging purposes.</li>
            <li><strong>Support Communications:</strong> Retained for 3 years to provide consistent support.</li>
        </ul>

        <h2>6. Your Rights and Choices</h2>

        <h3>6.1 Rights Under GDPR (European Users)</h3>
        <ul>
            <li><strong>Access:</strong> Request a copy of your personal data.</li>
            <li><strong>Rectification:</strong> Correct inaccurate or incomplete data.</li>
            <li><strong>Erasure:</strong> Request deletion of your data ("right to be forgotten").</li>
            <li><strong>Portability:</strong> Receive your data in a machine-readable format.</li>
            <li><strong>Restriction:</strong> Limit how we process your data.</li>
            <li><strong>Objection:</strong> Object to processing based on legitimate interest.</li>
            <li><strong>Withdraw Consent:</strong> Withdraw consent at any time for consent-based processing.</li>
        </ul>

        <h3>6.2 Rights Under CCPA (California Residents)</h3>
        <ul>
            <li><strong>Know:</strong> Request disclosure of data collected about you.</li>
            <li><strong>Delete:</strong> Request deletion of your personal information.</li>
            <li><strong>Opt-Out:</strong> Opt out of sale of personal information (we do not sell data).</li>
            <li><strong>Non-Discrimination:</strong> We will not discriminate against you for exercising your rights.</li>
        </ul>

        <h3>6.3 Exercising Your Rights</h3>
        <p>To exercise any of these rights, contact us at <a href="mailto:privacy@ayrto.dev">privacy@ayrto.dev</a> or use the account settings in your dashboard. We will respond within 30 days (or 45 days for complex requests).</p>

        <h2>7. Data Security</h2>
        <p>We implement industry-standard security measures including:</p>
        <ul>
            <li>TLS 1.3 encryption for all data in transit</li>
            <li>AES-256 encryption for sensitive data at rest</li>
            <li>Secure password hashing using bcrypt</li>
            <li>Regular security audits and penetration testing</li>
            <li>Access controls and authentication for all systems</li>
            <li>Automated threat detection and monitoring</li>
        </ul>
        <p>While we strive to protect your data, no method of transmission over the Internet is 100% secure. We cannot guarantee absolute security.</p>

        <h2>8. Cookies and Tracking Technologies</h2>

        <h3>8.1 Types of Cookies We Use</h3>
        <table>
            <tr>
                <th>Type</th>
                <th>Purpose</th>
                <th>Duration</th>
            </tr>
            <tr>
                <td>Essential</td>
                <td>Authentication, security, basic functionality</td>
                <td>Session / 30 days</td>
            </tr>
            <tr>
                <td>Functional</td>
                <td>Remember preferences and settings</td>
                <td>1 year</td>
            </tr>
            <tr>
                <td>Analytics</td>
                <td>Understand usage patterns (with consent)</td>
                <td>2 years</td>
            </tr>
        </table>

        <h3>8.2 Managing Cookies</h3>
        <p>You can control cookies through your browser settings. Disabling essential cookies may affect Service functionality. You can opt out of analytics cookies via our cookie banner or account settings.</p>

        <h2>9. International Data Transfers</h2>
        <p>Our servers are located in the United States. If you access our Service from outside the US, your information will be transferred to and processed in the US. We ensure appropriate safeguards through:</p>
        <ul>
            <li>Standard Contractual Clauses (SCCs) approved by the European Commission</li>
            <li>Data Processing Agreements with all sub-processors</li>
            <li>Privacy Shield-certified service providers where applicable</li>
        </ul>

        <h2>10. Children's Privacy</h2>
        <p>Our Service is not directed to children under 16 years of age. We do not knowingly collect personal information from children under 16. If we discover we have collected such information, we will delete it immediately. If you believe a child has provided us with personal information, please contact us.</p>

        <h2>11. Third-Party Links</h2>
        <p>Our Service may contain links to third-party websites or services. We are not responsible for their privacy practices. We encourage you to review the privacy policies of any third-party sites you visit.</p>

        <h2>12. Changes to This Policy</h2>
        <p>We may update this Privacy Policy periodically. We will notify you of material changes by:</p>
        <ul>
            <li>Posting the new policy on this page with an updated "Last Updated" date</li>
            <li>Sending an email notification for significant changes</li>
            <li>Displaying a prominent notice in our Service</li>
        </ul>
        <p>Your continued use of the Service after changes become effective constitutes acceptance of the revised policy.</p>

        <h2>13. Data Protection Officer</h2>
        <p>For GDPR-related inquiries, you may contact our Data Protection Officer:</p>
        <div class="highlight">
            <strong>Data Protection Officer</strong><br>
            Ayrto Engineering<br>
            Email: <a href="mailto:dpo@ayrto.dev">dpo@ayrto.dev</a>
        </div>

        <h2>14. Contact Us</h2>
        <p>If you have questions or concerns about this Privacy Policy or our data practices, please contact us:</p>
        <div class="highlight">
            <strong>Ayrto Engineering</strong><br>
            Email: <a href="mailto:privacy@ayrto.dev">privacy@ayrto.dev</a><br>
            Support: <a href="mailto:support@ayrto.dev">support@ayrto.dev</a>
        </div>

        <h2>15. Supervisory Authority</h2>
        <p>If you are located in the European Economic Area and believe we have not adequately addressed your concerns, you have the right to lodge a complaint with your local data protection supervisory authority.</p>

        <div class="footer">
            <p>&copy; 2026 Ayrto Engineering. All rights reserved.</p>
            <p>IndexerAPI is a trademark of Ayrto Engineering.</p>
        </div>
    </div>
</body>
</html>
"""

def get_privacy_policy() -> str:
    """Return the Privacy Policy HTML content."""
    return PRIVACY_POLICY
