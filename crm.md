# CRM (Customer Relationship Management)

## Overview

CRM refers to the strategies, processes, and technologies used to manage and analyze customer interactions throughout the customer lifecycle. The goal is to improve business relationships, retain customers, and drive sales growth.

---

## Core CRM Functions

### Contact Management
- Store and organize customer and prospect data (name, email, phone, company, role)
- Track interaction history across channels (email, call, chat, social)
- Segment contacts by attributes such as industry, deal stage, or engagement level

### Lead & Pipeline Management
- Capture leads from web forms, ads, email campaigns, and events
- Score leads based on behavior and fit criteria
- Move prospects through defined pipeline stages (Awareness → Interest → Decision → Close)

### Sales Automation
- Automate follow-up sequences and task reminders
- Trigger workflows based on contact actions (e.g., email open, link click, page visit)
- Auto-assign leads to reps based on territory or round-robin rules

### Marketing Automation
- Run drip campaigns and nurture sequences
- Personalize messaging based on CRM data (industry, lifecycle stage, past purchases)
- Sync campaign engagement data back to contact records

### Reporting & Analytics
- Track pipeline velocity, win/loss rates, and revenue forecasts
- Measure campaign ROI and attribution (first-touch, last-touch, multi-touch)
- Monitor customer health scores and churn risk indicators

---

## Key CRM Data Fields

| Field | Description |
|---|---|
| Contact Name | Full name of the individual |
| Company | Organization the contact belongs to |
| Email | Primary email address |
| Phone | Contact number |
| Lead Source | Origin of the lead (e.g., Organic, Paid, Referral) |
| Lifecycle Stage | Where the contact is in the buyer journey |
| Deal Stage | Current stage in the sales pipeline |
| Owner | Sales rep or team assigned to the contact |
| Last Activity Date | Most recent interaction logged |
| Close Date | Expected or actual date of deal close |

---

## CRM Lifecycle Stages

1. **Subscriber** — Opted in to receive communications but not yet qualified
2. **Lead** — Shown interest; needs qualification
3. **Marketing Qualified Lead (MQL)** — Meets marketing criteria; ready for sales review
4. **Sales Qualified Lead (SQL)** — Accepted by sales; active opportunity
5. **Opportunity** — In negotiation or evaluation
6. **Customer** — Closed and converted
7. **Evangelist** — Repeat buyer or active referrer

---

## CRM Best Practices

### Data Hygiene
- Deduplicate records regularly to avoid fragmented customer views
- Enforce required fields at the point of data entry
- Archive or delete contacts that are inactive beyond a defined threshold (e.g., 18 months)
- Standardize field formats (e.g., phone number format, state abbreviations)

### Segmentation
- Build dynamic lists based on behavioral and demographic attributes
- Use tags and custom properties to support niche targeting
- Refresh segment membership automatically as contact data changes

### Lead Scoring
- Assign positive scores for high-intent actions (demo request, pricing page visit)
- Assign negative scores for disqualifying signals (competitor domain, student email)
- Set a threshold score that triggers MQL designation and sales handoff

### Sales & Marketing Alignment
- Define shared definitions for MQL, SQL, and each pipeline stage
- Establish SLA agreements for lead follow-up time (e.g., contact within 24 hours of MQL)
- Use CRM activity logs as the single source of truth for handoff notes

### Integrations
- Connect CRM to email marketing platform for two-way sync of engagement data
- Integrate with ad platforms (Google, Meta) to import lead form submissions
- Link to customer support tools so reps see open tickets alongside deal history
- Sync with billing or ERP systems to surface revenue data in contact records

---

## Common CRM Platforms

| Platform | Best For |
|---|---|
| HubSpot CRM | SMBs and mid-market; strong marketing automation |
| Salesforce | Enterprise; highly customizable |
| Pipedrive | Sales-focused teams; visual pipeline management |
| Zoho CRM | Budget-conscious teams; broad feature set |
| ActiveCampaign | Email-first teams; deep automation workflows |
| Attio | Modern data-centric teams; flexible data model |
| Infusionsoft / Keap | Small businesses; combined CRM, e-commerce, and marketing automation |

---

## Infusionsoft / Keap Integration (PHP SDK)

The [infusionsoft-php](https://github.com/infusionsoft/infusionsoft-php) SDK provides a PHP client for the Infusionsoft (now Keap) API.

### Installation

```bash
composer require infusionsoft/php-sdk
```

### Authentication

The SDK supports three authentication modes:

| Mode | When to Use |
|---|---|
| OAuth2 (access token) | Standard third-party app integrations |
| Service Account Key (`KeapAK-` prefix) | Server-to-server integrations without user consent flow |
| Legacy API Key | Older integrations using the XML-RPC API |

**OAuth2 setup:**

```php
use Infusionsoft\Infusionsoft;

$infusionsoft = new Infusionsoft([
    'clientId'     => 'YOUR_CLIENT_ID',
    'clientSecret' => 'YOUR_CLIENT_SECRET',
    'redirectUri'  => 'https://yourapp.com/callback',
]);

// Redirect user to authorization URL, then exchange the code:
$infusionsoft->requestAccessToken($code);

// Persist the token for reuse
$token = $infusionsoft->getToken();
```

**Service account key setup:**

```php
$infusionsoft = new Infusionsoft([
    'clientId'     => 'YOUR_CLIENT_ID',
    'clientSecret' => 'YOUR_CLIENT_SECRET',
]);

$infusionsoft->setToken(new Token(['access_token' => 'KeapAK-...']));
```

### Token Refresh

```php
if ($infusionsoft->getToken()->isExpired()) {
    $infusionsoft->refreshAccessToken();
}
```

Store the refreshed token after each request to avoid re-authentication.

### Available API Services

#### REST API (`getRestApi()`)

```php
$contacts  = $infusionsoft->getRestApi('contacts');
$tags      = $infusionsoft->getRestApi('tags');
$campaigns = $infusionsoft->getRestApi('campaigns');
$companies = $infusionsoft->getRestApi('companies');
$emails    = $infusionsoft->getRestApi('emails');
$orders    = $infusionsoft->getRestApi('orders');
$products  = $infusionsoft->getRestApi('products');
```

#### XML-RPC API (`getApi()`)

```php
$contacts = $infusionsoft->getApi('contacts');
$invoices = $infusionsoft->getApi('invoices');
```

Use the REST API for new integrations; fall back to XML-RPC only for features not yet available via REST.

### Making Requests

**REST:**

```php
// List contacts
$contacts = $infusionsoft->getRestApi('contacts')->all();

// Create a contact
$infusionsoft->getRestApi('contacts')->create([
    'given_name'  => 'Jane',
    'family_name' => 'Smith',
    'email_addresses' => [['email' => 'jane@example.com', 'field' => 'EMAIL1']],
]);
```

**XML-RPC:**

```php
$result = $infusionsoft->request('ContactService.findByEmail', ['jane@example.com', ['Id', 'FirstName', 'LastName']]);
```

### Debugging

```php
use Monolog\Logger;
use Monolog\Handler\StreamHandler;

$logger = new Logger('infusionsoft');
$logger->pushHandler(new StreamHandler('infusionsoft.log', Logger::DEBUG));

$infusionsoft->setLogger($logger);
$infusionsoft->setDebug(true);
```

### Date Formatting

The SDK provides a helper to format dates for API compatibility:

```php
$formatted = $infusionsoft->formatDate('2026-05-08');
```

### Integration Checklist

- [ ] Register your app in the Keap developer portal and obtain `clientId` / `clientSecret`
- [ ] Choose authentication method (OAuth2 vs. service account key)
- [ ] Implement token storage and refresh logic before each API call
- [ ] Use REST API endpoints for contacts, tags, campaigns, and orders
- [ ] Enable PSR-3 logging in non-production environments for debugging
- [ ] Handle rate limit responses (HTTP 429) with exponential backoff

---

## CRM Metrics to Track

### Acquisition
- Lead volume by source
- Cost per lead (CPL)
- Lead-to-MQL conversion rate

### Conversion
- MQL-to-SQL rate
- SQL-to-close rate
- Average sales cycle length

### Revenue
- Average contract value (ACV)
- Monthly recurring revenue (MRR) from new vs. expansion
- Win rate by rep, segment, or channel

### Retention
- Customer churn rate
- Net Revenue Retention (NRR)
- Customer Lifetime Value (CLV)

---

## CRM Implementation Checklist

- [ ] Define your lifecycle stages and pipeline stages
- [ ] Map out required and optional data fields per object (Contact, Company, Deal)
- [ ] Set up lead capture forms and routing rules
- [ ] Configure lead scoring model with marketing and sales input
- [ ] Build core automation workflows (welcome sequence, MQL alert, re-engagement)
- [ ] Integrate with email, ad platforms, and support tools
- [ ] Import and deduplicate existing contact data
- [ ] Train team on data entry standards and activity logging
- [ ] Schedule recurring data audits (quarterly recommended)
- [ ] Set up dashboards for marketing, sales, and leadership reporting
