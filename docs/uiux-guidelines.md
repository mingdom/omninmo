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
- Avoid !important declarations
- Use comments to explain non-obvious styling decisions

## Implementation Plan

To improve the current styling approach:

1. **Consolidate CSS Files**: Merge the multiple CSS files into a more organized structure
2. **Implement CSS Variables**: Convert hard-coded color values to CSS variables
3. **Create a Theme System**: Implement a proper theme system using CSS variables
4. **Standardize Component Styling**: Ensure all components follow the design guidelines
5. **Document Components**: Create a simple component library for reference

## Conclusion

Following these guidelines will ensure a consistent, professional, and user-friendly interface for Folio. As the application evolves, this document should be updated to reflect new design decisions and best practices.
