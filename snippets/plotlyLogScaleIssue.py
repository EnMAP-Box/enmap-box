import plotly.graph_objects as go
import numpy as np

# Generate 100 random values with a logarithmic distribution
np.random.seed(42)
data = np.random.lognormal(mean=0, sigma=1, size=100)

# Create the violin plot using Plotly
fig = go.Figure()

fig.add_trace(go.Violin(y=np.log10(data),  # Use logarithmic scale on the y-axis
                        box_visible=True,
                        line_color='midnightblue',
                        meanline_visible=True,
                        fillcolor='lightseagreen',
                        opacity=0.6,
                        name='Distribution'
                        ))

fig.update_layout(title='Violin Plot with Logarithmic Scale',
                  yaxis_title='Logarithmic Scale',
                  xaxis_title='Data Points',
                  showlegend=False
                  )

fig.update_layout(
    yaxis=dict(
        tickmode='array',
        tickvals=[-1, 0, 1],
        ticktext=['Minus One', 'Zero', 'One']
    )
                  )

fig.show()
