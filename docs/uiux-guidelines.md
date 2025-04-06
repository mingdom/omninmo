# Folio UI/UX Guidelines
**Date:** 2023-07-25

## Overview

This document establishes the UI/UX guidelines for the Folio application, a professional-grade financial portfolio dashboard designed for institutional portfolio managers. These guidelines ensure a consistent, modern, and professional user experience across all components of the application.

## Design Philosophy

Folio's design philosophy is centered around four core principles:

1. **Professional & Institutional**: Design for sophisticated financial professionals who need clear, accurate data visualization without unnecessary embellishments.

2. **Data-Focused**: Prioritize data clarity and accuracy above all else. Every design decision should enhance the user's ability to understand their portfolio data.

3. **Modern & Clean**: Employ contemporary design patterns with ample whitespace, subtle shadows, and a restrained color palette to create a premium feel.

4. **Intuitive & Efficient**: Optimize for quick understanding and efficient workflows. Users should be able to grasp complex financial information at a glance.

## Color Palette

### Primary Colors

- **Primary Blue**: `#2C3E50` - Used for headers, primary buttons, and key UI elements
- **Secondary Blue**: `#3498DB` - Used for interactive elements, links, and highlights
- **Accent Blue**: `#1ABC9C` - Used sparingly for emphasis and call-to-action elements

### Financial Indicator Colors

- **Positive/Long**: `#27AE60` - For positive values, long positions, and upward trends
- **Negative/Short**: `#E74C3C` - For negative values, short positions, and downward trends
- **Neutral/Cash**: `#95A5A6` - For cash positions, neutral values, and stable metrics
- **Options**: `#9B59B6` - For options-related data and visualizations

### Background Colors

- **Page Background**: `#F8F9FA` - Light gray background for the main application
- **Card Background**: `#FFFFFF` - White background for cards and content containers
- **Alternate Background**: `#ECF0F1` - For alternating rows and secondary containers

### Text Colors

- **Primary Text**: `#2C3E50` - For headings and important text
- **Secondary Text**: `#7F8C8D` - For descriptions and less important text
- **Muted Text**: `#BDC3C7` - For placeholder text and disabled elements

## Typography

- **Primary Font**: System font stack (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`)
- **Headings**: Bold weight (600+), slightly tighter line height
- **Body Text**: Regular weight (400), comfortable line height for readability
- **Data Values**: Medium weight (500) for better visibility
- **Financial Figures**: Monospace font for alignment of numerical data

## Chart Design

### Chart Colors

- Use a consistent, professional color palette across all charts
- Maintain semantic meaning in colors (green for long, red for short, etc.)
- Ensure sufficient contrast between adjacent colors
- Use opacity to indicate hierarchy or to de-emphasize less important data

### Chart Typography

- Keep chart titles concise and descriptive
- Use consistent font sizes across all charts
- Ensure all labels are legible at various screen sizes
- Format numbers consistently (currency, percentages, etc.)

### Chart Layout

- Maintain consistent padding and spacing between chart elements
- Ensure charts resize responsively on different screen sizes
- Use grid lines sparingly and with low opacity
- Provide clear legends that don't interfere with the data visualization

### Chart Interactions

- Implement consistent hover states across all charts
- Provide tooltips with detailed information on hover
- Allow zooming and panning where appropriate
- Ensure all interactive elements are obvious to the user

## Component Design

### Cards

- Use subtle shadows to create depth
- Maintain consistent padding within cards
- Use clear headings to identify card content
- Implement hover states for interactive cards

### Buttons

- Primary actions: Filled buttons with the primary color
- Secondary actions: Outline buttons with the primary color
- Destructive actions: Red buttons for deletion or irreversible actions
- Use consistent padding and border-radius across all buttons

### Forms and Inputs

- Clearly label all form fields
- Provide helpful placeholder text
- Show validation errors inline
- Use appropriate input types for different data

### Tables

- Use alternating row colors for better readability
- Highlight rows on hover
- Allow sorting and filtering where appropriate
- Ensure column headers are clearly distinguished from data

## Responsive Design

- Design for desktop first, then adapt for tablet and mobile
- Stack elements vertically on smaller screens
- Adjust font sizes and spacing for mobile devices
- Ensure touch targets are sufficiently large on mobile

## Accessibility

- Maintain a minimum contrast ratio of 4.5:1 for text
- Provide alternative text for all images and charts
- Ensure the application is navigable via keyboard
- Test with screen readers and other assistive technologies

## Animation and Transitions

- Use subtle animations to enhance the user experience
- Keep transitions short (150-300ms) and smooth
- Avoid animations that could distract from the data
- Ensure animations can be disabled for users who prefer no motion

## Implementation Guidelines

### CSS Organization

- Use a modular approach with component-specific CSS files
- Follow a consistent naming convention (BEM recommended)
- Minimize the use of !important declarations
- Use CSS variables for colors and other repeated values

### Component Structure

- Keep components focused on a single responsibility
- Maintain consistent naming across related components
- Document component props and expected behavior
- Create reusable components for common patterns

## Chart-Specific Guidelines

### Asset Allocation Charts

- Use a pie or donut chart for percentage-based views
- Use a bar chart for absolute value views
- Include clear labels with percentages
- Use consistent colors for asset categories

### Exposure Charts

- Use horizontal bar charts for exposure comparisons
- Include zero baseline for context
- Use consistent colors (green for long, red for short)
- Include both absolute values and percentages where appropriate

### Position Treemaps

- Size boxes proportionally to position size
- Use color to indicate long/short status
- Include ticker symbols and exposure values in labels
- Ensure sufficient contrast between adjacent boxes

### Time Series Charts

- Use line charts for continuous data
- Include appropriate time intervals on the x-axis
- Show clear markers for significant events
- Allow zooming to different time periods

## Future Considerations

- Dark mode support with appropriate color adjustments
- Customizable dashboards with draggable components
- Advanced filtering and search capabilities
- Export options for charts and data
- Internationalization support for different currencies and number formats
