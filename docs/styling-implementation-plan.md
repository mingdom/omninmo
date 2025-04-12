# Folio Styling Implementation Plan

This document outlines a practical approach to improving the styling system in Folio, addressing the current issues with multiple CSS files and inconsistent styling approaches. The goal is to create a consistent UI that's easy to change and enforce moving forward.

## Current State Analysis

After a comprehensive review of the codebase (see `docs/current-styling-issues.md` for details), the current styling approach has several issues:

1. **Multiple CSS Files**: There are several CSS files (`styles.css`, `enhanced-ui.css`, `dashboard.css`, `ai-analysis.css`, `premium-chat.css`, `ai-chat.css`) with overlapping and sometimes conflicting styles.

2. **Inline Styles**: Many components use inline styles, making it difficult to maintain consistency.

3. **Hard-coded Colors**: Color values are hard-coded throughout the CSS files with inconsistent values (e.g., primary buttons use `#007bff` in one file and a gradient in another).

4. **Inconsistent Button Styling**: Button styles are defined in multiple places with different approaches (solid colors, gradients, custom inline styles).

5. **No Clear Theme System**: There's no clear system for theming or color management, making it difficult to ensure consistency.

6. **Hard-coded CSS in app.index_string**: Custom CSS is defined directly in the app.index_string property, separating it from the main CSS files.

7. **Redundant Style Definitions**: Many styles are defined multiple times across different files.

8. **No Documentation**: There's no documentation for the overall styling approach, component-specific styling guidelines, or color usage guidelines.

## Implementation Plan

### Phase 1: CSS Variables and Base Structure

#### 1.1 Create a Base Theme File

Create a new file `src/folio/assets/theme.css` that defines CSS variables for all colors, spacing, typography, etc.:

```css
:root {
  /* Primary colors */
  --primary-color: #4B0082; /* Royal Purple */
  --primary-light: #5D1E9E;
  --primary-dark: #3A006B;

  /* Neutral colors */
  --white: #FFFFFF;
  --off-white: #F8F9FA;
  --light-gray: #E9ECEF;
  --medium-gray: #CED4DA;
  --dark-gray: #6C757D;
  --black: #212529;

  /* Semantic colors */
  --success-color: #28A745;
  --danger-color: #DC3545;
  --info-color: #17A2B8;
  --warning-color: #FFC107;

  /* Typography */
  --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  --font-size-base: 1rem;
  --font-size-sm: 0.875rem;
  --font-size-lg: 1.25rem;
  --font-size-xl: 1.5rem;
  --font-weight-normal: 400;
  --font-weight-bold: 700;
  --line-height-base: 1.5;

  /* Spacing */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;

  /* Borders */
  --border-radius-sm: 4px;
  --border-radius-md: 8px;
  --border-radius-lg: 12px;
  --border-width: 1px;

  /* Shadows */
  --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.05);
  --shadow-lg: 0 8px 16px rgba(0, 0, 0, 0.1);

  /* Transitions */
  --transition-fast: 0.2s;
  --transition-medium: 0.3s;
  --transition-slow: 0.5s;

  /* Z-index layers */
  --z-index-dropdown: 1000;
  --z-index-sticky: 1020;
  --z-index-fixed: 1030;
  --z-index-modal-backdrop: 1040;
  --z-index-modal: 1050;
  --z-index-popover: 1060;
  --z-index-tooltip: 1070;
}
```

#### 1.2 Create a Base Component Styles File

Create a new file `src/folio/assets/components.css` that defines base styles for common components using the CSS variables:

```css
/* Button styles */
.btn {
  border-radius: var(--border-radius-md);
  transition: all var(--transition-fast);
  font-weight: var(--font-weight-normal);
  padding: var(--spacing-sm) var(--spacing-md);
}

.btn-primary {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
  color: var(--white);
  box-shadow: 0 4px 10px rgba(75, 0, 130, 0.3);
}

.btn-primary:hover {
  background-color: var(--primary-light);
  border-color: var(--primary-light);
  box-shadow: 0 6px 15px rgba(75, 0, 130, 0.4);
  transform: translateY(-1px);
}

.btn-primary:active, .btn-primary:focus {
  background-color: var(--primary-dark);
  border-color: var(--primary-dark);
  box-shadow: 0 2px 5px rgba(75, 0, 130, 0.3);
}

/* Card styles */
.card {
  border: none;
  border-radius: var(--border-radius-md);
  box-shadow: var(--shadow-md);
  transition: transform var(--transition-fast), box-shadow var(--transition-fast);
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.card-header {
  background: linear-gradient(to right, var(--off-white), var(--white));
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  border-radius: var(--border-radius-md) var(--border-radius-md) 0 0 !important;
}

/* Form controls */
.form-control {
  border-radius: var(--border-radius-sm);
  border: var(--border-width) solid var(--medium-gray);
  padding: var(--spacing-sm);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.form-control:focus {
  box-shadow: 0 0 0 3px rgba(75, 0, 130, 0.2);
  border-color: var(--primary-color);
}

/* Table styles */
.table {
  background-color: var(--white);
  border-radius: var(--border-radius-md);
  overflow: hidden;
}

.table thead th {
  background-color: var(--off-white);
  border-bottom: 2px solid var(--light-gray);
  font-weight: var(--font-weight-bold);
  color: var(--black);
}

.table tbody tr:hover {
  background-color: rgba(75, 0, 130, 0.05);
}

/* Modal styles */
.modal-content {
  border: none;
  border-radius: var(--border-radius-lg);
  box-shadow: var(--shadow-lg);
}

.modal-header {
  border-bottom: 1px solid var(--light-gray);
  background: linear-gradient(to right, var(--off-white), var(--white));
}

/* Alert styles */
.alert {
  border: none;
  border-radius: var(--border-radius-md);
  box-shadow: var(--shadow-sm);
}

.alert-success {
  background-color: rgba(40, 167, 69, 0.1);
  color: var(--success-color);
}

.alert-danger {
  background-color: rgba(220, 53, 69, 0.1);
  color: var(--danger-color);
}

.alert-info {
  background-color: rgba(23, 162, 184, 0.1);
  color: var(--info-color);
}

.alert-warning {
  background-color: rgba(255, 193, 7, 0.1);
  color: var(--warning-color);
}
```

#### 1.3 Create a Layout Styles File

Create a new file `src/folio/assets/layout.css` for layout-specific styles:

```css
/* Container styles */
.container-fluid {
  padding: var(--spacing-md);
}

/* Spacing utilities */
.my-1 { margin-top: var(--spacing-xs); margin-bottom: var(--spacing-xs); }
.my-2 { margin-top: var(--spacing-sm); margin-bottom: var(--spacing-sm); }
.my-3 { margin-top: var(--spacing-md); margin-bottom: var(--spacing-md); }
.my-4 { margin-top: var(--spacing-lg); margin-bottom: var(--spacing-lg); }
.my-5 { margin-top: var(--spacing-xl); margin-bottom: var(--spacing-xl); }

.mx-1 { margin-left: var(--spacing-xs); margin-right: var(--spacing-xs); }
.mx-2 { margin-left: var(--spacing-sm); margin-right: var(--spacing-sm); }
.mx-3 { margin-left: var(--spacing-md); margin-right: var(--spacing-md); }
.mx-4 { margin-left: var(--spacing-lg); margin-right: var(--spacing-lg); }
.mx-5 { margin-left: var(--spacing-xl); margin-right: var(--spacing-xl); }

.py-1 { padding-top: var(--spacing-xs); padding-bottom: var(--spacing-xs); }
.py-2 { padding-top: var(--spacing-sm); padding-bottom: var(--spacing-sm); }
.py-3 { padding-top: var(--spacing-md); padding-bottom: var(--spacing-md); }
.py-4 { padding-top: var(--spacing-lg); padding-bottom: var(--spacing-lg); }
.py-5 { padding-top: var(--spacing-xl); padding-bottom: var(--spacing-xl); }

.px-1 { padding-left: var(--spacing-xs); padding-right: var(--spacing-xs); }
.px-2 { padding-left: var(--spacing-sm); padding-right: var(--spacing-sm); }
.px-3 { padding-left: var(--spacing-md); padding-right: var(--spacing-md); }
.px-4 { padding-left: var(--spacing-lg); padding-right: var(--spacing-lg); }
.px-5 { padding-left: var(--spacing-xl); padding-right: var(--spacing-xl); }

/* Grid system enhancements */
.row {
  margin-left: calc(-1 * var(--spacing-md));
  margin-right: calc(-1 * var(--spacing-md));
}

.col, .col-1, .col-2, .col-3, .col-4, .col-5, .col-6,
.col-7, .col-8, .col-9, .col-10, .col-11, .col-12,
.col-sm, .col-md, .col-lg, .col-xl {
  padding-left: var(--spacing-md);
  padding-right: var(--spacing-md);
}

/* App header */
.app-header {
  margin-bottom: var(--spacing-lg);
  padding-bottom: var(--spacing-sm);
  border-bottom: 1px solid var(--light-gray);
}

.app-header h2 {
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-light) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-weight: var(--font-weight-bold);
}

/* Empty state */
.empty-state {
  background: linear-gradient(135deg, var(--off-white) 0%, var(--white) 100%);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-xl);
  box-shadow: var(--shadow-md);
  text-align: center;
}

.empty-state i {
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-light) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-size: 3rem;
  margin-bottom: var(--spacing-lg);
}
```

#### 1.4 Create a Main CSS File

Create a new file `src/folio/assets/main.css` that imports all the other CSS files:

```css
/* Import theme variables */
@import 'theme.css';

/* Import component styles */
@import 'components.css';

/* Import layout styles */
@import 'layout.css';

/* Base styles */
body {
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  line-height: var(--line-height-base);
  color: var(--black);
  background-color: var(--off-white);
}

h1, h2, h3, h4, h5, h6 {
  font-weight: var(--font-weight-bold);
  line-height: 1.2;
  margin-bottom: var(--spacing-md);
}

a {
  color: var(--primary-color);
  text-decoration: none;
  transition: color var(--transition-fast);
}

a:hover {
  color: var(--primary-light);
  text-decoration: underline;
}

/* Utility classes */
.text-success { color: var(--success-color) !important; }
.text-danger { color: var(--danger-color) !important; }
.text-info { color: var(--info-color) !important; }
.text-warning { color: var(--warning-color) !important; }
.text-primary { color: var(--primary-color) !important; }

.bg-success { background-color: var(--success-color) !important; }
.bg-danger { background-color: var(--danger-color) !important; }
.bg-info { background-color: var(--info-color) !important; }
.bg-warning { background-color: var(--warning-color) !important; }
.bg-primary { background-color: var(--primary-color) !important; }

.font-weight-bold { font-weight: var(--font-weight-bold) !important; }
.font-weight-normal { font-weight: var(--font-weight-normal) !important; }

.text-center { text-align: center !important; }
.text-left { text-align: left !important; }
.text-right { text-align: right !important; }

/* Responsive adjustments */
@media (max-width: 768px) {
  .container-fluid {
    padding: var(--spacing-sm);
  }

  .app-header {
    margin-bottom: var(--spacing-md);
  }

  .empty-state {
    padding: var(--spacing-lg);
  }
}
```

### Phase 2: Integration with Dash Bootstrap Components

#### 2.1 Update App Creation

Update the `create_app` function in `src/folio/app.py` to use a theme from Dash Bootstrap Components and move inline styles to CSS files:

```python
def create_app(portfolio_file: str | None = None, _debug: bool = False) -> dash.Dash:
    """Create and configure the Dash application"""
    logger.info("Initializing Dash application")

    # Create Dash app
    app = dash.Dash(
        __name__,
        external_stylesheets=[
            dbc.themes.BOOTSTRAP,  # Base Bootstrap theme
            "https://use.fontawesome.com/releases/v5.15.4/css/all.css",
        ],
        title="Folio",
        # Enable async callbacks
        use_pages=False,
        suppress_callback_exceptions=True,
    )

    # Move inline styles from app.index_string to CSS files
    # Replace the custom index_string with a simpler version
    app.index_string = """
    <!DOCTYPE html>
    <html>
        <head>
            {%metas%}
            <title>{%title%}</title>
            {%favicon%}
            {%css%}
        </head>
        <body>
            {%app_entry%}
            <footer>
                {%config%}
                {%scripts%}
                {%renderer%}
            </footer>
        </body>
    </html>
    """

    # The rest of the function remains the same
    # ...
```

#### 2.2 Integrate with Dash Bootstrap Templates

Integrate with dash-bootstrap-templates to ensure Plotly figures match the Bootstrap theme:

```python
from dash_bootstrap_templates import load_figure_template

# Load the template in app.py
load_figure_template("bootstrap")

# Use the template in chart creation functions
def create_exposure_chart(portfolio_data):
    fig = px.bar(
        portfolio_data,
        x="Symbol",
        y="Exposure",
        color="Type",
        template="bootstrap"  # Apply the template
    )

    # Additional customizations
    fig.update_layout(
        title="Portfolio Exposure",
        xaxis_title="",
        yaxis_title="Market Exposure ($)"
    )

    return fig
```

#### 2.3 Remove Inline Styles from Components

Update components to use CSS classes instead of inline styles:

```python
# Before
def create_empty_state() -> html.Div:
    return html.Div(
        [
            html.H4("Welcome to Folio", className="text-center mb-3"),
            html.P(
                "Upload your portfolio CSV file to get started", className="text-center"
            ),
            html.Div(
                [
                    html.I(className="fas fa-upload fa-3x"),
                ],
                className="text-center my-4",
            ),
            html.P(
                "Or try a sample portfolio to explore the features",
                className="text-center mt-3",
            ),
            dbc.Button(
                "Load Sample Portfolio",
                id="load-sample",
                color="primary",
                className="mx-auto d-block",
                style={
                    "background": "#4B0082",  # Dark royal purple
                    "border-color": "#4B0082"
                }
            ),
        ],
        className="empty-state py-5",
    )

# After
def create_empty_state() -> html.Div:
    return html.Div(
        [
            html.H4("Welcome to Folio", className="text-center mb-3"),
            html.P(
                "Upload your portfolio CSV file to get started", className="text-center"
            ),
            html.Div(
                [
                    html.I(className="fas fa-upload fa-3x"),
                ],
                className="text-center my-4",
            ),
            html.P(
                "Or try a sample portfolio to explore the features",
                className="text-center mt-3",
            ),
            dbc.Button(
                "Load Sample Portfolio",
                id="load-sample",
                color="primary",
                className="mx-auto d-block load-sample-button",
            ),
        ],
        className="empty-state py-5",
    )
```

### Phase 3: Component-Specific Styling

#### 3.1 Create Component-Specific CSS Files

Create separate CSS files for each major component type, using the CSS variables defined in the theme file:

```css
/* src/folio/assets/components/buttons.css */
.btn {
  border-radius: var(--border-radius-md);
  transition: all var(--transition-fast);
  font-weight: var(--font-weight-normal);
  padding: var(--spacing-sm) var(--spacing-md);
}

.btn-primary {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
  color: var(--white);
  box-shadow: 0 4px 10px rgba(75, 0, 130, 0.3);
}

/* More button styles... */
```

```css
/* src/folio/assets/components/cards.css */
.card {
  border: none;
  border-radius: var(--border-radius-md);
  box-shadow: var(--shadow-md);
  transition: transform var(--transition-fast), box-shadow var(--transition-fast);
}

/* More card styles... */
```

```css
/* src/folio/assets/components/tables.css */
.table {
  background-color: var(--white);
  border-radius: var(--border-radius-md);
  overflow: hidden;
}

/* More table styles... */
```

#### 3.2 Import Component Styles in Main CSS

Update the main CSS file to import all component-specific CSS files:

```css
/* src/folio/assets/main.css */
@import 'theme.css';
@import 'layout.css';

/* Component styles */
@import 'components/buttons.css';
@import 'components/cards.css';
@import 'components/tables.css';
@import 'components/forms.css';
@import 'components/modals.css';
/* More component imports... */

/* Base styles */
body {
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  line-height: var(--line-height-base);
  color: var(--black);
  background-color: var(--off-white);
}
```

### Phase 4: Cleanup and Migration

#### 4.1 Audit Existing CSS

Review all existing CSS files and identify styles that need to be migrated to the new system.

#### 4.2 Migrate Styles

Migrate styles from the existing CSS files to the new system, updating them to use CSS variables.

#### 4.3 Remove Inline Styles

Identify and remove inline styles from components, replacing them with class names.

#### 4.4 Update Components

Update components to use the new styling system, ensuring consistency across the application.

#### 4.5 Testing

Test the application thoroughly to ensure that all styles are applied correctly and that the theme toggle works as expected.

## Integration with Dash Bootstrap Templates

To ensure that Plotly figures match the Bootstrap theme, integrate with dash-bootstrap-templates:

```python
from dash_bootstrap_templates import load_figure_template

# Load the template
load_figure_template("bootstrap")

# Use the template in figures
fig = px.line(df, x="date", y="value", template="bootstrap")
```

## Benefits of This Approach

1. **Consistency**: All styles are defined in one place and use CSS variables for consistency, making it easy to maintain a cohesive look and feel.
2. **Maintainability**: CSS is organized in a modular way with clear separation of concerns, making it easier to maintain and extend.
3. **Reusability**: Component-specific styles are defined in separate files, making it easy to reuse styles across components.
4. **Performance**: CSS is organized efficiently, reducing duplication and improving performance.
5. **Scalability**: The system can be easily extended to support additional components or styling needs.
6. **Documentation**: The UIUX guidelines document provides clear guidance for developers on how to style components.

## Timeline

- **Week 1**: Set up the base theme system with CSS variables (Phase 1)
- **Week 2**: Integrate with Dash Bootstrap Components and remove inline styles (Phase 2)
- **Week 3**: Create component-specific CSS files (Phase 3)
- **Week 4**: Clean up and migrate existing styles (Phase 4)

## Conclusion

This implementation plan provides a clear path to improving the styling system in Folio, addressing the current issues and providing a solid foundation for future development. By following this plan, we can create a more consistent, maintainable, and user-friendly interface for Folio.

The key benefits of this approach are:

1. **Simplified Maintenance**: With a clear structure and organization, it will be much easier to maintain and update the styling of the application.
2. **Consistent Look and Feel**: By using CSS variables and component-specific styles, we can ensure a consistent look and feel across the application.
3. **Easier Collaboration**: With clear documentation and guidelines, it will be easier for multiple developers to work on the application while maintaining consistency.
4. **Future-Proofing**: The modular approach makes it easier to adapt to future requirements or design changes.

By implementing this plan, we'll transform the current ad-hoc styling approach into a structured, maintainable system that will serve the application well as it continues to evolve.
