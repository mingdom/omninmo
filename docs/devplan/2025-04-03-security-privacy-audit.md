# Security and Privacy Audit for External Deployment

Date: 2025-04-03

## Overview

This document presents a comprehensive security and privacy audit of the Folio application in preparation for its external deployment on Hugging Face Spaces. The audit identifies potential security and privacy risks and provides recommendations for addressing these concerns.

## Table of Contents

- [Current State Assessment](#current-state-assessment)
- [Risk Analysis](#risk-analysis)
- [Recommendations](#recommendations)
- [Implementation Plan](#implementation-plan)
- [Conclusion](#conclusion)

## Current State Assessment

### Application Architecture

Folio is a Dash-based web application that allows users to:
- Upload portfolio CSV files
- View portfolio analysis and metrics
- Interact with portfolio data through a web interface
- Fetch market data from external APIs (yfinance or FMP)

### Security Measures Currently in Place

1. **Environment Variables**
   - API keys stored as environment variables
   - Logging level configurable via environment variables
   - No log files written when deployed on Hugging Face (privacy measure)

2. **Data Handling**
   - Portfolio data processed in-memory
   - No persistent storage of user data
   - Sample portfolio provided with obfuscated data

3. **Deployment Configuration**
   - Docker containerization
   - Restricted write access in Hugging Face environment
   - Logging level set to WARNING in production

### Missing Security Measures

1. **Content Security Policy (CSP)**
   - No CSP headers to prevent XSS attacks

2. **CORS Configuration**
   - No explicit CORS policy

3. **Input Validation**
   - Limited validation of uploaded CSV files

4. **Authentication**
   - No user authentication mechanism

5. **Data Encryption**
   - No encryption for data in transit (relies on platform HTTPS)
   - No encryption for data at rest

6. **Rate Limiting**
   - No rate limiting for API calls or file uploads

## Risk Analysis

### High Priority Risks

1. **Sensitive Financial Data Exposure**
   - **Risk**: User portfolio data could contain sensitive financial information
   - **Impact**: Privacy breach, potential financial harm to users
   - **Likelihood**: High

2. **Cross-Site Scripting (XSS)**
   - **Risk**: Malicious code injection through unvalidated inputs
   - **Impact**: Session hijacking, data theft
   - **Likelihood**: Medium

3. **CSV Injection**
   - **Risk**: Malicious formula injection in CSV files
   - **Impact**: Data manipulation, potential code execution
   - **Likelihood**: Medium

### Medium Priority Risks

4. **API Key Exposure**
   - **Risk**: Exposure of API keys in logs or client-side code
   - **Impact**: Unauthorized API usage, potential billing issues
   - **Likelihood**: Low (mitigated by environment variables)

5. **Denial of Service (DoS)**
   - **Risk**: Resource exhaustion through large file uploads or frequent requests
   - **Impact**: Service unavailability
   - **Likelihood**: Low

6. **Data Persistence**
   - **Risk**: Unintended persistence of sensitive data in cache or logs
   - **Impact**: Privacy breach
   - **Likelihood**: Medium

### Low Priority Risks

7. **Cross-Site Request Forgery (CSRF)**
   - **Risk**: Unauthorized actions performed on behalf of authenticated users
   - **Impact**: Data manipulation
   - **Likelihood**: Low (no authentication currently)

8. **Insecure Dependencies**
   - **Risk**: Vulnerabilities in third-party libraries
   - **Impact**: Various security issues
   - **Likelihood**: Medium

## Recommendations

### High Priority Recommendations

1. **Implement Data Sanitization**
   - Sanitize all portfolio data before processing
   - Remove or mask sensitive information (account numbers, full names)
   - Add option for users to anonymize their data before upload

2. **Add Content Security Policy**
   - Implement CSP headers to prevent XSS attacks
   - Restrict loading of external resources to trusted domains
   - Add implementation to Dash app configuration

3. **Enhance CSV Validation**
   - Validate CSV structure and content before processing
   - Implement formula sanitization to prevent CSV injection
   - Add size limits for uploaded files

### Medium Priority Recommendations

4. **Implement CORS Policy**
   - Configure proper CORS headers
   - Restrict cross-origin requests to trusted domains
   - Add implementation to Dash app configuration

5. **Add Rate Limiting**
   - Implement rate limiting for file uploads
   - Add request throttling for API calls
   - Configure reasonable limits based on expected usage

6. **Improve Cache Security**
   - Implement secure cache management
   - Ensure cache data is properly isolated
   - Add cache expiration policies

### Low Priority Recommendations

7. **Dependency Management**
   - Regularly update dependencies
   - Implement dependency scanning
   - Pin dependency versions in requirements.txt

8. **Privacy Policy**
   - Create a clear privacy policy
   - Explain data handling practices
   - Add to application UI

9. **User Consent**
   - Add explicit consent for data processing
   - Provide clear information about data usage
   - Allow users to opt out of certain features

## Implementation Plan

### Phase 1: Critical Security Enhancements (1-2 days)

1. **Data Sanitization**
   ```python
   def sanitize_portfolio_data(df):
       # Remove sensitive columns if present
       sensitive_columns = ['Account Number', 'SSN', 'Full Name']
       for col in sensitive_columns:
           if col in df.columns:
               df = df.drop(columns=[col])

       # Mask partial account numbers if present
       if 'Account' in df.columns:
           df['Account'] = df['Account'].apply(lambda x: f"***{str(x)[-4:]}" if pd.notna(x) else x)

       return df
   ```

2. **Content Security Policy**
   ```python
   # Add to app creation in app.py
   app = dash.Dash(
       __name__,
       external_stylesheets=[
           dbc.themes.BOOTSTRAP,
           "https://use.fontawesome.com/releases/v5.15.4/css/all.css",
       ],
       title="Folio",
       meta_tags=[
           {
               'http-equiv': 'Content-Security-Policy',
               'content': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline' https://use.fontawesome.com; img-src 'self' data:; font-src 'self' https://use.fontawesome.com; connect-src 'self' https://query1.finance.yahoo.com;"
           }
       ]
   )
   ```

3. **CSV Validation**
   ```python
   def validate_csv(contents, filename):
       # Check file size
       content_type, content_string = contents.split(',')
       decoded = base64.b64decode(content_string)
       if len(decoded) > 10 * 1024 * 1024:  # 10MB limit
           raise ValueError("File too large (max 10MB)")

       # Check file extension
       if not filename.lower().endswith('.csv'):
           raise ValueError("Only CSV files are supported")

       # Parse and validate content
       try:
           df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))

           # Check for required columns
           required_columns = ['Symbol', 'Quantity', 'Last Price']
           missing_columns = [col for col in required_columns if col not in df.columns]
           if missing_columns:
               raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

           # Sanitize formula content to prevent CSV injection
           for col in df.columns:
               if df[col].dtype == 'object':
                   df[col] = df[col].astype(str).apply(lambda x: x.replace('=', '') if x.startswith('=') else x)

           return df
       except Exception as e:
           raise ValueError(f"Invalid CSV format: {str(e)}")
   ```

### Phase 2: Additional Security Measures (2-3 days)

1. **CORS Configuration**
   ```python
   # Add to app.py
   from flask_cors import CORS

   # After creating the Dash app
   CORS(app.server, resources={r"/*": {"origins": ["https://huggingface.co", "http://localhost:*"]}})
   ```

2. **Rate Limiting**
   ```python
   # Add to app.py
   from flask_limiter import Limiter
   from flask_limiter.util import get_remote_address

   # After creating the Dash app
   limiter = Limiter(
       app.server,
       key_func=get_remote_address,
       default_limits=["200 per day", "50 per hour"]
   )

   # Apply specific limits to routes
   @limiter.limit("10 per minute")
   @app.server.route('/upload', methods=['POST'])
   def upload_route():
       # Handle upload
       pass
   ```

3. **Secure Cache Management**
   ```python
   # Update cache configuration
   def get_cache_dir():
       is_huggingface = os.environ.get('HF_SPACE') == '1' or os.environ.get('SPACE_ID') is not None
       if is_huggingface:
           cache_dir = Path("/tmp/.cache_folio")
       else:
           cache_dir = Path(".cache_folio")

       # Create with restricted permissions
       cache_dir.mkdir(mode=0o700, exist_ok=True)
       return cache_dir
   ```

### Phase 3: Privacy Enhancements (1-2 days)

1. **Privacy Policy Component**
   ```python
   def create_privacy_policy():
       return html.Div([
           html.H4("Privacy Policy"),
           html.P("This application processes financial portfolio data for analysis purposes."),
           html.Ul([
               html.Li("Your data is processed in-memory and is not stored permanently."),
               html.Li("No personal information is collected or shared with third parties."),
               html.Li("Market data is fetched from public APIs (Yahoo Finance)."),
               html.Li("You can anonymize your portfolio data before uploading."),
           ]),
       ], id="privacy-policy", className="mt-4")
   ```

2. **User Consent Modal**
   ```python
   def create_consent_modal():
       return dbc.Modal([
           dbc.ModalHeader("Data Processing Consent"),
           dbc.ModalBody([
               html.P("By uploading your portfolio data, you consent to:"),
               html.Ul([
                   html.Li("Processing your data for analysis purposes"),
                   html.Li("Fetching market data related to your portfolio"),
                   html.Li("Temporary storage of data during your session"),
               ]),
               html.P("Your data is not permanently stored and is not shared with third parties."),
           ]),
           dbc.ModalFooter([
               dbc.Button("I Consent", id="consent-button", color="primary"),
               dbc.Button("Cancel", id="cancel-consent", color="secondary"),
           ]),
       ], id="consent-modal")
   ```

## Conclusion

The Folio application currently implements basic security measures but requires additional enhancements to ensure proper security and privacy for external deployment on Hugging Face Spaces. The recommendations in this audit focus on:

1. **Data Protection**: Ensuring user financial data is properly sanitized and protected
2. **Web Security**: Implementing standard web security measures like CSP and CORS
3. **Input Validation**: Enhancing validation of user inputs to prevent injection attacks
4. **Privacy Compliance**: Adding clear privacy policies and user consent mechanisms

By implementing these recommendations, the Folio application will significantly improve its security posture and better protect user privacy when deployed externally.

## Checklist

- [ ] Implement data sanitization for portfolio uploads
- [ ] Add Content Security Policy headers
- [ ] Enhance CSV validation and sanitization
- [ ] Configure CORS policy
- [ ] Implement rate limiting
- [ ] Improve cache security
- [ ] Create and display privacy policy
- [ ] Add user consent mechanism
- [ ] Update dependencies and pin versions
- [ ] Document security measures for future maintenance
