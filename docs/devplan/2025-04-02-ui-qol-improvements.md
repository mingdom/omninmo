# UI Quality of Life Improvements Development Plan
**Date:** 2025-04-02

## Overview
This development plan outlines the implementation of several UI Quality of Life (QoL) improvements for the Folio application to prepare it for MVP user release. The improvements focus on enhancing user experience through better visual feedback, more intuitive interactions, and professional styling.

## Checklist
- [ ] **Loading UI**: Implement loading spinners and visual feedback during data processing
- [ ] **User-friendly instructions**: Add clear instructions and hide portfolio on initial upload
- [ ] **Professional interface with dark mode**: Implement a dark theme as default with toggle option
- [ ] **Keyboard shortcuts**: Add CMD+O/CTRL+O for opening portfolio CSV files
- [ ] **File dialog improvements**: Default filter for portfolio CSV files

## Detailed Implementation Plan

### Phase 1: Loading UI and Visual Feedback

#### 1.1 Loading Indicators
- Implement loading spinners using Dash's dcc.Loading component
- Add loading states for:
  - Initial data loading
  - Portfolio file uploads
  - Data refreshing
  - Position details loading

#### 1.2 Implementation Details
- Wrap key components with dcc.Loading
- Add visual feedback for long-running operations
- Ensure loading states are properly triggered and cleared
- Add progress indicators where appropriate

#### 1.3 Technical Approach
```python
# Example implementation for loading wrapper
dcc.Loading(
    id="loading-portfolio",
    type="circle",  # Options: "circle", "dot", "default"
    children=[
        html.Div(id="portfolio-table-container")
    ],
)
```

### Phase 2: User-Friendly Instructions

#### 2.1 Improved Upload Experience
- Hide portfolio table when no data is loaded
- Show clear instructions for first-time users
- Add welcome message with quick-start guide
- Implement a "Getting Started" section

#### 2.2 Empty State Design
- Design an informative empty state for the application
- Include clear call-to-action for uploading a portfolio
- Add sample portfolio option for demonstration

#### 2.3 Technical Approach
```python
# Example implementation for empty state
def create_empty_state():
    return html.Div([
        html.H4("Welcome to Folio", className="text-center mb-3"),
        html.P("Upload your portfolio CSV file to get started", className="text-center"),
        html.Div([
            html.I(className="fas fa-upload fa-3x text-muted"),
        ], className="text-center my-4"),
        html.P("Or try a sample portfolio to explore the features", className="text-center mt-3"),
        dbc.Button("Load Sample Portfolio", id="load-sample", color="secondary", className="mx-auto d-block"),
    ], className="py-5")
```

### Phase 3: Professional Interface with Dark Mode

#### 3.1 Dark Mode Implementation
- Create a dark theme CSS file
- Implement theme switching functionality
- Set dark mode as the default theme
- Ensure all components support both themes

#### 3.2 Theme Toggle
- Add a theme toggle button in the header
- Persist theme preference in browser storage
- Ensure smooth transition between themes

#### 3.3 Professional Styling Updates
- Refine typography and spacing
- Improve table styling for better readability
- Enhance card and modal designs
- Update color scheme for better contrast

#### 3.4 Technical Approach
```python
# Example implementation for theme toggle
def create_theme_toggle():
    return html.Div([
        dbc.Button(
            html.I(className="fas fa-moon"),
            id="theme-toggle",
            color="link",
            size="sm",
            className="p-0",
        ),
        dcc.Store(id="theme-store", storage_type="local"),
    ])

# Theme switching callback
@app.callback(
    Output("theme-store", "data"),
    Input("theme-toggle", "n_clicks"),
    State("theme-store", "data"),
)
def toggle_theme(n_clicks, current_theme):
    if n_clicks is None:
        # Default to dark theme
        return {"theme": "dark"}

    if current_theme and current_theme.get("theme") == "dark":
        return {"theme": "light"}
    else:
        return {"theme": "dark"}
```

### Phase 4: Keyboard Shortcuts

#### 4.1 File Opening Shortcut
- Implement CMD+O (macOS) / CTRL+O (Windows/Linux) for opening files
- Add keyboard shortcut hints in the UI
- Ensure shortcuts work across different browsers

#### 4.2 Additional Shortcuts
- Add keyboard navigation for table rows
- Implement ESC key to close modals
- Add shortcut for refreshing data

#### 4.3 Technical Approach
```python
# Example implementation for keyboard shortcuts
app.clientside_callback(
    """
    function(n_intervals) {
        document.addEventListener('keydown', function(e) {
            // CMD+O or CTRL+O
            if ((e.metaKey || e.ctrlKey) && e.key === 'o') {
                e.preventDefault();
                document.getElementById('upload-portfolio').click();
                return true;
            }
        });
        return true;
    }
    """,
    Output("keyboard-shortcut-listener", "data"),
    Input("interval-component", "n_intervals"),
)
```

### Phase 5: File Dialog Improvements

#### 5.1 Default Filtering
- Set default filter for files starting with "portfolio" and .csv extension
- Implement custom file dialog with filtering capabilities
- Add recently used files list

#### 5.2 Technical Approach
```python
# Example implementation for file dialog improvements
dcc.Upload(
    id="upload-portfolio",
    children=html.Div([
        "Drag and Drop or ",
        html.A("Select a CSV File", className="text-primary"),
    ]),
    # Filter for CSV files
    accept=".csv",
    multiple=False,
)
```

## Testing Plan

### Unit Tests
- Test theme switching functionality
- Verify keyboard shortcut handling
- Test loading state transitions

### Integration Tests
- Test end-to-end file upload flow
- Verify theme persistence across sessions
- Test keyboard shortcuts in different browsers

### User Testing
- Conduct usability testing with sample users
- Gather feedback on the new UI improvements
- Measure time to complete common tasks

## Implementation Timeline

### Week 1: Loading UI and Instructions
- Implement loading indicators
- Design and implement empty states
- Add user-friendly instructions

### Week 2: Dark Mode and Professional Styling
- Create dark theme CSS
- Implement theme switching
- Refine overall styling

### Week 3: Keyboard Shortcuts and File Dialog
- Implement keyboard shortcuts
- Improve file dialog experience
- Final testing and refinements

## Conclusion
These UI Quality of Life improvements will significantly enhance the user experience of the Folio application, making it more intuitive, responsive, and professional. The implementation of loading indicators, clear instructions, dark mode, and keyboard shortcuts will bring the application to a level suitable for MVP users.
