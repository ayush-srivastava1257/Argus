import plotly.express as px
import plotly.graph_objects as go

# ------------------------------------------------------------------
# LUXURY DARK THEME PALETTE
# ------------------------------------------------------------------
THEME = {
    "bg": "#05070B",
    "card": "#111827",
    "border": "#1F2937",
    "text_primary": "#F9FAFB",
    "text_secondary": "#9CA3AF",
    "accent_blue": "#3B82F6",
    "accent_green": "#22C55E",
    "accent_orange": "#F59E0B",
    "accent_red": "#EF4444",
    "accent_purple": "#8B5CF6",
    "grid_color": "rgba(255, 255, 255, 0.05)"
}

def apply_enterprise_theme(fig: go.Figure, height: int = 340) -> go.Figure:
    """
    Applies the enterprise luxury dark theme to any Plotly figure.
    Removes background, styles grids, updates fonts to Inter, caps height.
    """
    fig.update_layout(
        height=height,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, -apple-system, sans-serif", color=THEME["text_primary"], size=12),
        title_font=dict(size=14, color=THEME["text_primary"], family="Inter, -apple-system, sans-serif"),
        legend=dict(
            font=dict(color=THEME["text_secondary"], size=11),
            bgcolor="rgba(0,0,0,0)",
            bordercolor=THEME["border"],
            borderwidth=1,
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=36, r=36, t=44, b=36),
        hoverlabel=dict(
            bgcolor=THEME["card"],
            bordercolor=THEME["border"],
            font_size=12,
            font_family="Inter, sans-serif"
        )
    )
    
    fig.update_xaxes(
        showgrid=True, 
        gridwidth=1, 
        gridcolor=THEME["grid_color"], 
        zeroline=False,
        tickfont=dict(color=THEME["text_secondary"], size=11),
        title_font=dict(color=THEME["text_secondary"], size=11)
    )
    
    fig.update_yaxes(
        showgrid=True, 
        gridwidth=1, 
        gridcolor=THEME["grid_color"], 
        zeroline=False,
        tickfont=dict(color=THEME["text_secondary"], size=11),
        title_font=dict(color=THEME["text_secondary"], size=11)
    )
    
    return fig

def validate_chart_data(df, x_col=None, y_col=None) -> bool:
    """Validates dataframe existence, column presence, and non-empty rows."""
    if df is None or not hasattr(df, "empty") or df.empty:
        return False
    if x_col and x_col not in df.columns:
        return False
    if y_col and y_col not in df.columns:
        return False
    return True

def smart_visualization(df, x_col: str, y_col: str, title: str, default_type: str = "line", color_sequence=None) -> go.Figure:
    """
    Selects the optimal visualization based on data length:
    - 0 points -> Empty figure
    - 1-5 points -> Bar chart
    - >5 points -> Line or Bar (as specified by default_type)
    """
    if not validate_chart_data(df, x_col, y_col):
        return go.Figure()
        
    n = len(df.dropna(subset=[x_col, y_col]))
    if n == 0:
        return go.Figure()
        
    colors = color_sequence or [THEME["accent_blue"]]
    
    if n <= 5 or default_type == "bar":
        fig = px.bar(df, x=x_col, y=y_col, title=title, color_discrete_sequence=colors)
    else:
        fig = px.line(df, x=x_col, y=y_col, title=title, color_discrete_sequence=colors)
        
    return apply_enterprise_theme(fig)

def create_histogram(df, x_col, title, color_col=None):
    if not validate_chart_data(df, x_col):
        return go.Figure()
    fig = px.histogram(
        df, 
        x=x_col, 
        color=color_col, 
        title=title, 
        color_discrete_sequence=[THEME["accent_blue"], THEME["accent_purple"], THEME["accent_orange"]]
    )
    return apply_enterprise_theme(fig)

def create_box_plot(df, x_col, y_col, title):
    if not validate_chart_data(df, y_col=y_col):
        return go.Figure()
    fig = px.box(
        df, 
        x=x_col, 
        y=y_col, 
        title=title,
        color_discrete_sequence=[THEME["accent_blue"]]
    )
    return apply_enterprise_theme(fig)

def create_heatmap(z, x, y, title, colorscale="Blues"):
    if z is None or len(z) == 0:
        return go.Figure()
    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=x,
        y=y,
        colorscale=colorscale,
        hoverongaps=False
    ))
    fig.update_layout(title=title)
    return apply_enterprise_theme(fig)

def create_line_chart(df, x_col, y_col, title):
    return smart_visualization(df, x_col, y_col, title, default_type="line")

def create_scatter(df, x_col, y_col, color_col, title):
    if not validate_chart_data(df, x_col, y_col):
        return go.Figure()
    fig = px.scatter(
        df,
        x=x_col,
        y=y_col,
        color=color_col,
        title=title,
        color_discrete_sequence=[THEME["accent_blue"], THEME["accent_red"], THEME["accent_green"]]
    )
    return apply_enterprise_theme(fig)

def get_categorical_colors(n):
    base_colors = [THEME["accent_blue"], THEME["accent_purple"], THEME["accent_orange"], THEME["accent_green"], THEME["accent_red"]]
    return [base_colors[i % len(base_colors)] for i in range(n)]


