# Folio UIUX Guidelines

## Introduction

This document outlines the design philosophy, styling approach, and implementation guidelines for the Folio application's user interface. It serves as a reference for maintaining consistency across the application and guiding future UI/UX enhancements.

## Design Philosophy

Folio's design is guided by the following core principles:

1. **Simplicity**: Focus on essential information and functionality without overwhelming the user
2. **Precision**: Present financial data with appropriate precision and clarity
3. **Reliability**: Provide clear feedback and error states to build user trust
4. **Usability**: Create intuitive interfaces that require minimal learning
5. **Sophistication**: Present a professional, refined appearance appropriate for a financial application

## Styling Principles

### CSS-First Approach

When implementing UI changes, follow these principles:

1. **Use CSS Overrides**: Always prefer CSS overrides over code changes when styling components
2. **Target Component Structure**: Use CSS selectors that target the component structure rather than adding custom classes
3. **Centralize Styles**: Keep all styles in the appropriate CSS files rather than inline styles
4. **Specificity**: Use specific selectors (like IDs) for one-off styling needs and more general selectors for common patterns

Example of the CSS-first approach:

```css
/* Instead of adding a custom class to center text */
#summary-card .card-body > h4 {
  text-align: center;
}

/* Instead of adding a custom class to all collapsible headers */
.card .card-header button span {
  font-size: 1.5rem;
  font-weight: 500;
}
```

This approach ensures consistency, reduces code complexity, and makes styling changes easier to maintain.

## Color Palette

### Primary Colors

| Color Name | Hex Code | Usage |
|------------|----------|-------|
| Royal Purple | #4B0082 | Primary buttons, key UI elements, focus states |
| Light Purple | #5D1E9E | Hover states, secondary elements |
| Dark Purple | #3A006B | Active states, pressed buttons |
| White | #FFFFFF | Backgrounds, text on dark colors |
| Off-White | #F8F9FA | Secondary backgrounds, card backgrounds |

### Semantic Colors

| Color Name | Hex Code | Usage |
|------------|----------|-------|
| Success Green | #28A745 | Positive values, confirmations |
| Danger Red | #DC3545 | Negative values, errors, warnings |
| Info Blue | #17A2B8 | Informational elements |
| Warning Yellow | #FFC107 | Caution states |

### Chart Colors

Chart colors are defined in the `ChartColors` class in `src/folio/chart_data.py`:

| Color Name | Hex Code | Constant | Usage |
|------------|----------|----------|-------|
| Dark Green | #1A5D38 | `ChartColors.LONG` | Long positions in charts |
| Dark Gray | #2F3136 | `ChartColors.SHORT` | Short positions in charts |
| Purple | #9B59B6 | `ChartColors.OPTIONS` | Options in charts |
| Blue | #3498DB | `ChartColors.NET` | Net values in charts |

Always use these constants instead of hardcoded hex values to ensure consistency across charts.

### Gradients

For elements that need visual emphasis:

- Primary Gradient: `linear-gradient(135deg, #4B0082 0%, #8A2BE2 100%)`
- Header Gradient: `linear-gradient(to right, #4B0082, #5D1E9E)`

## Typography

### Font Family

```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
```

### Font Sizes

| Element | Size | Weight | Line Height |
|---------|------|--------|-------------|
| Page Title | 1.75rem (28px) | 700 | 1.2 |
| Section Headers | 1.25rem (20px) | 600 | 1.3 |
| Card Titles | 1.1rem (17.6px) | 600 | 1.4 |
| Body Text | 1rem (16px) | 400 | 1.5 |
| Small Text | 0.875rem (14px) | 400 | 1.4 |
| Table Headers | 0.9rem (14.4px) | 600 | 1.4 |

### Number Formatting

- Financial values should be displayed with 2 decimal places
- Large numbers should use thousands separators (commas)
- Percentages should be displayed with 2 decimal places
- Negative values should be displayed in red and with a minus sign

## Components

### Buttons

#### Primary Buttons

Used for primary actions like "Load Portfolio" or "Analysis":

```css
background-color: #4B0082;
border-color: #4B0082;
color: white;
border-radius: 6px;
padding: 0.5rem 1rem;
font-weight: 500;
box-shadow: 0 4px 10px rgba(75, 0, 130, 0.3);
```

#### Secondary Buttons

Used for secondary actions:

```css
background-color: transparent;
border-color: #4B0082;
color: #4B0082;
border-radius: 6px;
padding: 0.5rem 1rem;
font-weight: 500;
```

#### Button States

- **Hover**: Slightly lighter color, increased shadow
- **Active/Focus**: Slightly darker color, decreased shadow
- **Disabled**: Reduced opacity, no shadow

### Cards

Cards are used to group related content:

```css
border: none;
border-radius: 8px;
box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
background-color: white;
transition: transform 0.2s, box-shadow 0.2s;
```

Card headers should use a subtle gradient or solid color to distinguish them from the body.

### Collapsible Sections

Collapsible sections are used throughout the application to organize content and allow users to focus on specific areas. Following our CSS-first approach, the styling for collapsible sections is automatically applied through CSS targeting the Dash Bootstrap Components structure.

To create a collapsible section, use the standard Dash Bootstrap Components pattern:

```python
dbc.Card([
    dbc.CardHeader(
        dbc.Button(
            [
                html.I(className="fas fa-chart-bar me-2"),  # Icon before title
                html.Span("Section Title"),               # Section title
                html.I(className="fas fa-chevron-down ms-2", id="section-collapse-icon"),  # Chevron icon
            ],
            id="section-collapse-button",
            color="link",
            className="text-decoration-none text-dark p-0 d-flex align-items-center w-100 justify-content-between",
        ),
    ),
    dbc.Collapse(
        dbc.CardBody(your_content),
        id="section-collapse",
        is_open=True,
    ),
], className="mb-3")
```

The styling is automatically applied through CSS selectors in `src/folio/assets/components/cards.css`:

```css
/* Collapsible section headers */
.card .card-header button span {
  font-size: 1.5rem;
  font-weight: 500;
  margin-bottom: 0;
  line-height: 1.2;
}
```

This ensures consistent appearance across all collapsible sections without requiring any special classes or utility functions. When you need to make styling changes, update the CSS rather than modifying the component code.

### Tables

Tables should be clean and easy to read:

```css
background-color: white;
border-radius: 8px;
box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
```

- Table headers should be slightly emphasized with background color
- Alternating row colors can be used for better readability
- Clickable rows should have hover states
- Sort indicators should be clear but not distracting

### Charts

Charts should be consistent in style:

- Use a consistent color palette across all charts
- Provide clear labels and legends
- Use appropriate chart types for the data being displayed
- Ensure charts are responsive and readable on all devices
- Minimize chart junk (unnecessary decorative elements)
- Use descriptive labels rather than generic ones

### Form Elements

Form elements should be clearly visible and easy to interact with:

```css
border: 1px solid rgba(0, 0, 0, 0.2);
border-radius: 4px;
padding: 0.5rem;
transition: border-color 0.2s, box-shadow 0.2s;
```

Focus states should be clearly indicated:

```css
box-shadow: 0 0 0 3px rgba(75, 0, 130, 0.2);
border-color: #4B0082;
```

## Layout Guidelines

### Spacing

Use a consistent spacing system:

- **Extra Small**: 0.25rem (4px)
- **Small**: 0.5rem (8px)
- **Medium**: 1rem (16px)
- **Large**: 1.5rem (24px)
- **Extra Large**: 2rem (32px)

### Responsive Design

- Use Bootstrap's grid system for layout
- Design for mobile-first, then enhance for larger screens
- Ensure all interactive elements are large enough for touch input
- Test on various screen sizes and devices

### Content Hierarchy

- Most important information should be at the top
- Group related information together
- Use visual hierarchy (size, color, spacing) to guide the user's attention
- Provide clear section headers and dividers

## Implementation Approach

### Theming with Dash Bootstrap Components

Folio uses [Dash Bootstrap Components](https://dash-bootstrap-components.opensource.faculty.ai/) for layout and styling. To maintain consistency, we should:

1. Use a single theme as the base (e.g., BOOTSTRAP)
2. Customize the theme using CSS variables
3. Apply consistent styling through class names rather than inline styles

### CSS Organization

CSS should be organized in a modular way:

1. **Base Styles**: Typography, colors, and basic elements
2. **Component Styles**: Specific styles for components like cards, tables, etc.
3. **Layout Styles**: Grid, spacing, and responsive adjustments
4. **Utility Classes**: Helper classes for common styling needs

### Theme Implementation

Instead of creating separate CSS files for different themes or colors, use CSS variables to define a theme:

```css
:root {
  --primary-color: #4B0082;
  --primary-light: #5D1E9E;
  --primary-dark: #3A006B;
  --success-color: #28A745;
  --danger-color: #DC3545;
  --info-color: #17A2B8;
  --warning-color: #FFC107;
  --text-color: #212529;
  --background-color: #FFFFFF;
  --card-background: #FFFFFF;
  --border-radius: 8px;
  --box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

/* Then use these variables throughout the CSS */
.btn-primary {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
}

.btn-primary:hover {
  background-color: var(--primary-light);
  border-color: var(--primary-light);
}
```

This approach allows for easy theme switching by changing the variable values.

### Dash Bootstrap Templates

Consider using [dash-bootstrap-templates](https://pypi.org/project/dash-bootstrap-templates/) to ensure that Plotly figures match the Bootstrap theme:

```python
from dash_bootstrap_templates import load_figure_template

# Load the template
load_figure_template("bootstrap")

# Use the template in figures
fig = px.line(df, x="date", y="value", template="bootstrap")
```

## Best Practices

### Accessibility

- Ensure sufficient color contrast (WCAG AA compliance)
- Provide text alternatives for non-text content
- Ensure keyboard navigability
- Use semantic HTML elements
- Test with screen readers

### Performance

- Minimize CSS size by avoiding duplication
- Use efficient selectors
- Consider loading non-critical CSS asynchronously
- Optimize images and other assets

### Maintainability

- Use consistent naming conventions (BEM or similar)
- Document complex components
- Keep selectors as simple as possible
- Follow the CSS-first approach for styling components
- Centralize styles in appropriate CSS files rather than using inline styles
- Use CSS selectors that target component structure rather than adding custom classes
- Update CSS files when making styling changes rather than modifying component code
- Avoid !important declarations
- Use comments to explain non-obvious styling decisions

## Implementation Status

The styling system has been implemented with the following structure:

### CSS Organization

CSS is organized in a modular, maintainable way using CSS variables and component-specific files:

1. **Theme Variables**: All design tokens (colors, spacing, etc.) are defined as CSS variables in `theme.css`
2. **Component Files**: Each component type has its own CSS file in the `components/` directory
3. **Layout Styles**: Layout-specific styles are in `layout.css`
4. **Main CSS**: All CSS files are imported in `main.css`

### File Structure

```
src/folio/assets/
├── theme.css           # CSS variables for colors, spacing, etc.
├── layout.css          # Layout-specific styles
├── main.css            # Main CSS file that imports all other CSS files
└── components/
    ├── buttons.css     # Button styles
    ├── cards.css       # Card styles
    ├── tables.css      # Table styles
    ├── forms.css       # Form styles
    ├── modals.css      # Modal styles
    └── charts.css      # Chart styles
```

This implementation:

1. ✅ **Consolidates CSS Files**: Organized CSS into a logical structure
2. ✅ **Implements CSS Variables**: All design tokens are CSS variables
3. ✅ **Creates a Theme System**: Theme variables in a central location
4. ✅ **Standardizes Component Styling**: All components follow the design guidelines
5. ✅ **Documents Components**: This document serves as the reference

## Conclusion

Following these guidelines will ensure a consistent, professional, and user-friendly interface for Folio. As the application evolves, this document should be updated to reflect new design decisions and best practices.
