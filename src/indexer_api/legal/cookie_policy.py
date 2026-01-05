"""
Cookie Policy for IndexerAPI
GDPR and ePrivacy Directive compliant cookie disclosure
Last Updated: January 2026
"""

COOKIE_POLICY = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cookie Policy - IndexerAPI</title>
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
        .cookie-type { display: inline-block; padding: 4px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: 600; margin-right: 8px; }
        .essential { background: #00ff8833; color: #00ff88; }
        .functional { background: #00f3ff33; color: #00f3ff; }
        .analytics { background: #ffaa0033; color: #ffaa00; }
        .marketing { background: #ff444433; color: #ff4444; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Cookie Policy</h1>
        <p class="effective-date">Effective Date: January 5, 2026 | Last Updated: January 5, 2026</p>

        <div class="highlight">
            <strong>Quick Summary:</strong> We use essential cookies to make our service work and optional analytics cookies to improve it. You can control non-essential cookies through our cookie banner or your browser settings.
        </div>

        <h2>1. What Are Cookies?</h2>
        <p>Cookies are small text files that are stored on your device (computer, tablet, or mobile) when you visit a website. They are widely used to make websites work more efficiently, provide information to website owners, and enable certain features.</p>
        <p>Similar technologies include:</p>
        <ul>
            <li><strong>Local Storage:</strong> Data stored in your browser that persists until explicitly deleted</li>
            <li><strong>Session Storage:</strong> Data stored temporarily for a single browser session</li>
            <li><strong>Pixels/Web Beacons:</strong> Small images that track page views and email opens</li>
        </ul>

        <h2>2. How We Use Cookies</h2>
        <p>We use cookies and similar technologies to:</p>
        <ul>
            <li>Keep you signed in to your account</li>
            <li>Remember your preferences and settings</li>
            <li>Understand how you use our Service</li>
            <li>Improve our Service based on usage patterns</li>
            <li>Protect against fraud and unauthorized access</li>
        </ul>

        <h2>3. Types of Cookies We Use</h2>

        <h3>3.1 <span class="cookie-type essential">Essential</span> Strictly Necessary Cookies</h3>
        <p>These cookies are required for the Service to function. Without them, you cannot use core features like logging in. <strong>You cannot opt out of these cookies.</strong></p>
        <table>
            <tr>
                <th>Cookie Name</th>
                <th>Purpose</th>
                <th>Duration</th>
            </tr>
            <tr>
                <td>session_id</td>
                <td>Maintains your login session</td>
                <td>Session</td>
            </tr>
            <tr>
                <td>csrf_token</td>
                <td>Prevents cross-site request forgery attacks</td>
                <td>Session</td>
            </tr>
            <tr>
                <td>auth_token</td>
                <td>Authenticates API requests</td>
                <td>30 days</td>
            </tr>
            <tr>
                <td>refresh_token</td>
                <td>Refreshes expired authentication tokens</td>
                <td>7 days</td>
            </tr>
        </table>

        <h3>3.2 <span class="cookie-type functional">Functional</span> Preference Cookies</h3>
        <p>These cookies remember your preferences to provide enhanced features. Disabling them may affect your experience.</p>
        <table>
            <tr>
                <th>Cookie Name</th>
                <th>Purpose</th>
                <th>Duration</th>
            </tr>
            <tr>
                <td>theme</td>
                <td>Remembers your dark/light mode preference</td>
                <td>1 year</td>
            </tr>
            <tr>
                <td>language</td>
                <td>Stores your language preference</td>
                <td>1 year</td>
            </tr>
            <tr>
                <td>sidebar_state</td>
                <td>Remembers if sidebar is collapsed/expanded</td>
                <td>1 year</td>
            </tr>
            <tr>
                <td>cookie_consent</td>
                <td>Records your cookie consent choices</td>
                <td>1 year</td>
            </tr>
        </table>

        <h3>3.3 <span class="cookie-type analytics">Analytics</span> Performance Cookies</h3>
        <p>These cookies help us understand how visitors use our Service. All data is aggregated and anonymous. <strong>You can opt out of these cookies.</strong></p>
        <table>
            <tr>
                <th>Cookie Name</th>
                <th>Purpose</th>
                <th>Duration</th>
            </tr>
            <tr>
                <td>_analytics_id</td>
                <td>Identifies unique visitors (anonymized)</td>
                <td>2 years</td>
            </tr>
            <tr>
                <td>_analytics_session</td>
                <td>Groups page views into sessions</td>
                <td>30 minutes</td>
            </tr>
            <tr>
                <td>_page_views</td>
                <td>Counts pages viewed in session</td>
                <td>Session</td>
            </tr>
        </table>

        <h3>3.4 <span class="cookie-type marketing">Marketing</span> Advertising Cookies</h3>
        <p><strong>We do not currently use marketing or advertising cookies.</strong> If this changes, we will update this policy and request your consent.</p>

        <h2>4. Third-Party Cookies</h2>
        <p>Some cookies are placed by third-party services that appear on our pages:</p>

        <h3>4.1 Stripe (Payment Processing)</h3>
        <table>
            <tr>
                <th>Cookie Name</th>
                <th>Purpose</th>
                <th>Duration</th>
            </tr>
            <tr>
                <td>__stripe_mid</td>
                <td>Fraud prevention</td>
                <td>1 year</td>
            </tr>
            <tr>
                <td>__stripe_sid</td>
                <td>Session identifier for payments</td>
                <td>30 minutes</td>
            </tr>
        </table>
        <p>For more information, see <a href="https://stripe.com/privacy" target="_blank" rel="noopener">Stripe's Privacy Policy</a>.</p>

        <h2>5. Managing Cookies</h2>

        <h3>5.1 Cookie Consent Banner</h3>
        <p>When you first visit our Service, you will see a cookie consent banner that allows you to:</p>
        <ul>
            <li>Accept all cookies</li>
            <li>Accept only essential cookies</li>
            <li>Customize your preferences by category</li>
        </ul>
        <p>You can change your preferences at any time in your account settings.</p>

        <h3>5.2 Browser Settings</h3>
        <p>Most browsers allow you to control cookies through their settings. Here's how to manage cookies in popular browsers:</p>
        <ul>
            <li><strong>Chrome:</strong> Settings → Privacy and Security → Cookies</li>
            <li><strong>Firefox:</strong> Settings → Privacy & Security → Cookies</li>
            <li><strong>Safari:</strong> Preferences → Privacy → Cookies</li>
            <li><strong>Edge:</strong> Settings → Privacy, Search, and Services → Cookies</li>
        </ul>

        <h3>5.3 Opt-Out Links</h3>
        <p>For third-party analytics services, you can opt out directly:</p>
        <ul>
            <li><a href="https://tools.google.com/dlpage/gaoptout" target="_blank" rel="noopener">Google Analytics Opt-out</a></li>
        </ul>

        <h2>6. Do Not Track</h2>
        <p>Some browsers have a "Do Not Track" feature that signals websites not to track you. Currently, there is no universal standard for how websites should respond to this signal. We currently do not respond to DNT signals, but we honor the cookie preferences you set through our consent banner.</p>

        <h2>7. Cookie Duration</h2>
        <p>Cookies have different lifespans:</p>
        <ul>
            <li><strong>Session Cookies:</strong> Deleted when you close your browser</li>
            <li><strong>Persistent Cookies:</strong> Remain until they expire or you delete them</li>
        </ul>

        <h2>8. Impact of Blocking Cookies</h2>
        <p>If you choose to block or delete cookies:</p>
        <table>
            <tr>
                <th>Cookie Type Blocked</th>
                <th>Impact</th>
            </tr>
            <tr>
                <td>Essential</td>
                <td>Service may not function; cannot log in</td>
            </tr>
            <tr>
                <td>Functional</td>
                <td>Preferences not saved; default settings used</td>
            </tr>
            <tr>
                <td>Analytics</td>
                <td>No impact on your experience</td>
            </tr>
        </table>

        <h2>9. Updates to This Policy</h2>
        <p>We may update this Cookie Policy to reflect changes in our practices or for legal reasons. We will:</p>
        <ul>
            <li>Update the "Last Updated" date at the top</li>
            <li>Notify you of significant changes via email or notice on our Service</li>
            <li>Request new consent if required for new types of cookies</li>
        </ul>

        <h2>10. Legal Basis</h2>
        <p>Our use of cookies is based on:</p>
        <ul>
            <li><strong>Essential cookies:</strong> Legitimate interest (necessary for service operation)</li>
            <li><strong>Functional cookies:</strong> Consent or legitimate interest</li>
            <li><strong>Analytics cookies:</strong> Consent</li>
        </ul>
        <p>This policy complies with the EU ePrivacy Directive, GDPR, and CCPA requirements.</p>

        <h2>11. Contact Us</h2>
        <p>If you have questions about our use of cookies:</p>
        <div class="highlight">
            <strong>Ayrto Engineering</strong><br>
            Email: <a href="mailto:privacy@ayrto.dev">privacy@ayrto.dev</a><br>
            For data protection inquiries: <a href="mailto:dpo@ayrto.dev">dpo@ayrto.dev</a>
        </div>

        <div class="footer">
            <p>&copy; 2026 Ayrto Engineering. All rights reserved.</p>
            <p>IndexerAPI is a trademark of Ayrto Engineering.</p>
        </div>
    </div>
</body>
</html>
"""

def get_cookie_policy() -> str:
    """Return the Cookie Policy HTML content."""
    return COOKIE_POLICY
