"""
Refund and Cancellation Policy for IndexerAPI
Clear guidelines for refunds, cancellations, and subscription management
Last Updated: January 2026
"""

REFUND_POLICY = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Refund Policy - IndexerAPI</title>
    <style>
        :root { --primary: #00f3ff; --bg: #0a0a0f; --card: #111118; --text: #e0e0e0; --muted: #888; --success: #00ff88; }
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
        .success { background: #1a2e1a; border-left: 3px solid var(--success); padding: 15px 20px; margin: 20px 0; border-radius: 0 8px 8px 0; }
        .warning { background: #2e1a1a; border-left: 3px solid #ff4444; padding: 15px 20px; margin: 20px 0; border-radius: 0 8px 8px 0; }
        a { color: var(--primary); }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { border: 1px solid #333; padding: 12px; text-align: left; }
        th { background: #1a1a2e; color: var(--primary); }
        .footer { margin-top: 60px; padding-top: 30px; border-top: 1px solid #333; color: var(--muted); font-size: 0.9rem; }
        .badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: 600; }
        .badge-green { background: #00ff8833; color: var(--success); }
        .badge-yellow { background: #ffaa0033; color: #ffaa00; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Refund & Cancellation Policy</h1>
        <p class="effective-date">Effective Date: January 5, 2026 | Last Updated: January 5, 2026</p>

        <div class="success">
            <strong>Our Commitment:</strong> We want you to be completely satisfied with IndexerAPI. If you're not happy, we offer a straightforward refund process with a 14-day money-back guarantee for new subscribers.
        </div>

        <h2>1. Money-Back Guarantee</h2>

        <h3>1.1 First-Time Subscribers</h3>
        <p>If you are a <strong>first-time subscriber</strong> to IndexerAPI, you are eligible for a full refund within <strong>14 days</strong> of your initial purchase, no questions asked.</p>

        <div class="highlight">
            <strong>14-Day Guarantee Conditions:</strong>
            <ul>
                <li>Applies only to your first subscription purchase</li>
                <li>Request must be made within 14 calendar days of payment</li>
                <li>Full refund of the subscription amount</li>
                <li>Your account and data will be deleted upon refund</li>
            </ul>
        </div>

        <h3>1.2 EU/EEA Customers - Right of Withdrawal</h3>
        <p>Under the EU Consumer Rights Directive, customers in the European Union and European Economic Area have the right to withdraw from a contract within 14 days without giving any reason.</p>
        <p>However, by using the Service immediately after purchase, you acknowledge that:</p>
        <ul>
            <li>You request immediate access to the Service</li>
            <li>You acknowledge that you lose your right of withdrawal once the Service is fully performed</li>
            <li>For subscription services, you may still cancel future renewals at any time</li>
        </ul>

        <h2>2. Subscription Cancellation</h2>

        <h3>2.1 How to Cancel</h3>
        <p>You may cancel your subscription at any time through:</p>
        <ol>
            <li><strong>Account Dashboard:</strong> Navigate to Settings → Billing → Cancel Subscription</li>
            <li><strong>Email:</strong> Send a cancellation request to <a href="mailto:billing@ayrto.dev">billing@ayrto.dev</a></li>
            <li><strong>Support:</strong> Contact our support team for assistance</li>
        </ol>

        <h3>2.2 Effect of Cancellation</h3>
        <table>
            <tr>
                <th>What Happens</th>
                <th>Timeline</th>
            </tr>
            <tr>
                <td>Cancellation confirmed</td>
                <td>Immediate</td>
            </tr>
            <tr>
                <td>Service access continues</td>
                <td>Until end of current billing period</td>
            </tr>
            <tr>
                <td>No further charges</td>
                <td>After current period ends</td>
            </tr>
            <tr>
                <td>Account downgraded to free tier (if available)</td>
                <td>After current period ends</td>
            </tr>
            <tr>
                <td>Data retention</td>
                <td>30 days after subscription ends</td>
            </tr>
            <tr>
                <td>Data deletion</td>
                <td>31+ days after subscription ends</td>
            </tr>
        </table>

        <div class="warning">
            <strong>Important:</strong> Cancellation does not automatically generate a refund. Refunds are processed separately according to the policies below.
        </div>

        <h2>3. Refund Eligibility</h2>

        <h3>3.1 Eligible for Refund <span class="badge badge-green">Approved</span></h3>
        <ul>
            <li>First-time subscription within 14-day guarantee period</li>
            <li>Service unavailability exceeding 24 consecutive hours (pro-rata)</li>
            <li>Billing errors or duplicate charges</li>
            <li>Unauthorized charges (with verification)</li>
            <li>Significant service degradation affecting your use</li>
            <li>Features advertised at purchase not delivered</li>
        </ul>

        <h3>3.2 Not Eligible for Refund <span class="badge badge-yellow">Case-by-Case</span></h3>
        <ul>
            <li>Change of mind after 14-day guarantee period</li>
            <li>Unused subscription time (partial month)</li>
            <li>Failure to cancel before renewal date</li>
            <li>Violation of Terms of Service resulting in termination</li>
            <li>Temporary service disruptions under 24 hours</li>
            <li>Third-party integration issues outside our control</li>
            <li>Custom enterprise agreements (separate terms apply)</li>
        </ul>

        <h2>4. Refund Process</h2>

        <h3>4.1 How to Request a Refund</h3>
        <ol>
            <li>Email <a href="mailto:billing@ayrto.dev">billing@ayrto.dev</a> with subject "Refund Request"</li>
            <li>Include your account email and order/invoice number</li>
            <li>Briefly explain the reason for your request</li>
            <li>We will respond within 2 business days</li>
        </ol>

        <h3>4.2 Refund Timeline</h3>
        <table>
            <tr>
                <th>Stage</th>
                <th>Timeframe</th>
            </tr>
            <tr>
                <td>Request acknowledgment</td>
                <td>Within 24 hours</td>
            </tr>
            <tr>
                <td>Review and decision</td>
                <td>1-2 business days</td>
            </tr>
            <tr>
                <td>Refund processed</td>
                <td>1-3 business days after approval</td>
            </tr>
            <tr>
                <td>Funds appear in account</td>
                <td>5-10 business days (depends on bank)</td>
            </tr>
        </table>

        <h3>4.3 Refund Method</h3>
        <p>Refunds are issued to the original payment method:</p>
        <ul>
            <li><strong>Credit/Debit Card:</strong> Refunded to the same card</li>
            <li><strong>PayPal:</strong> Refunded to PayPal account</li>
            <li><strong>Bank Transfer:</strong> Refunded to originating account</li>
        </ul>
        <p>If the original payment method is no longer available, we will work with you to find an alternative solution.</p>

        <h2>5. Pro-Rata Refunds</h2>

        <h3>5.1 Service Credits</h3>
        <p>For service disruptions or issues that don't warrant a full refund, we may offer:</p>
        <ul>
            <li>Pro-rata credit for downtime exceeding SLA commitments</li>
            <li>Extension of subscription period</li>
            <li>Upgrade to higher tier for remaining period</li>
        </ul>

        <h3>5.2 Annual Subscription Refunds</h3>
        <p>Annual subscriptions receive a discount for upfront payment. If you cancel an annual subscription:</p>
        <ul>
            <li><strong>Within 14 days:</strong> Full refund available</li>
            <li><strong>After 14 days:</strong> Pro-rata refund minus the discount received (calculated at monthly rate)</li>
        </ul>

        <h2>6. Automatic Renewal</h2>

        <h3>6.1 Renewal Notice</h3>
        <p>We will send you a reminder email <strong>7 days before</strong> your subscription renews. This email will include:</p>
        <ul>
            <li>Renewal date and amount</li>
            <li>How to cancel if you don't wish to continue</li>
            <li>Any price changes (with 30 days' notice for increases)</li>
        </ul>

        <h3>6.2 Failed Renewal Payments</h3>
        <p>If your renewal payment fails:</p>
        <ol>
            <li>We will notify you immediately</li>
            <li>Retry the payment after 3 days</li>
            <li>Send a final notice after 7 days</li>
            <li>Suspend service after 14 days of non-payment</li>
            <li>You can reactivate by updating payment information</li>
        </ol>

        <h2>7. Chargebacks</h2>
        <p>Before initiating a chargeback with your bank, please contact us first. Chargebacks:</p>
        <ul>
            <li>Incur additional fees that may be passed to you if found unjustified</li>
            <li>May result in account suspension pending resolution</li>
            <li>Take longer to resolve than direct refund requests</li>
        </ul>
        <p>We commit to resolving legitimate billing issues faster than the chargeback process.</p>

        <h2>8. Free Trials</h2>
        <p>If we offer free trials:</p>
        <ul>
            <li>No payment is charged during the trial period</li>
            <li>You will be notified before the trial ends</li>
            <li>Subscription begins automatically unless canceled</li>
            <li>First charge occurs at end of trial</li>
        </ul>

        <h2>9. Price Changes</h2>
        <p>If we increase prices:</p>
        <ul>
            <li>Existing subscribers receive 30 days' notice</li>
            <li>Current billing period is honored at old rate</li>
            <li>You may cancel before new rate takes effect</li>
            <li>Price decreases apply immediately or at next renewal</li>
        </ul>

        <h2>10. Enterprise Customers</h2>
        <p>Enterprise customers with custom agreements may have different refund terms as specified in their contract. Contact your account manager for details.</p>

        <h2>11. Exceptions</h2>
        <p>We reserve the right to make exceptions to this policy at our discretion, particularly in cases of:</p>
        <ul>
            <li>Extended service outages</li>
            <li>Significant bugs affecting your use</li>
            <li>Documented customer hardship</li>
            <li>Long-term customer loyalty</li>
        </ul>

        <h2>12. Contact Us</h2>
        <p>For refund requests or billing questions:</p>
        <div class="highlight">
            <strong>Billing Support</strong><br>
            Email: <a href="mailto:billing@ayrto.dev">billing@ayrto.dev</a><br>
            Response Time: Within 24 hours (business days)<br><br>
            <strong>General Support</strong><br>
            Email: <a href="mailto:support@ayrto.dev">support@ayrto.dev</a>
        </div>

        <div class="footer">
            <p>&copy; 2026 Ayrto Engineering. All rights reserved.</p>
            <p>IndexerAPI is a trademark of Ayrto Engineering.</p>
        </div>
    </div>
</body>
</html>
"""

def get_refund_policy() -> str:
    """Return the Refund Policy HTML content."""
    return REFUND_POLICY
