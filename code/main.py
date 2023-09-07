import pandas as pd
import plotly.express as px
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Load the World Energy dataset
df = pd.read_csv('energy-data.csv')

# Create a Dash web application
app = dash.Dash(__name__)

# Define the layout of the web app
app.layout = html.Div([
    html.H1("World Energy Consumption"),
    html.Div([
        dcc.Dropdown(
            id="year-dropdown",
            options=[{'label': str(year), 'value': year}
                     for year in df['year'].unique()],
            value=2019,  # Set the default value to 2019
            style={'width': '200px'}
        ),
    ]),
    html.Div([
        dcc.Graph(id="map-graph"),
        dcc.Graph(id="area-graph"),
        dcc.Graph(id="pie-graph"),
        dcc.Graph(id="bar-graph"),
        dcc.Graph(id="scatter"),
        dcc.Graph(id="grouped-bar-graph"),
    ]),
])


@app.callback(
    [Output("map-graph", "figure"), Output("area-graph",
                                           "figure"), Output("pie-graph", "figure"), Output("bar-graph", "figure"), Output("scatter", "figure"), Output("grouped-bar-graph", "figure")],
    [Input("year-dropdown", "value"),
     Input("map-graph", "clickData"),
     Input("bar-graph", "clickData")]
)
def update_graphs(selected_year, map_click_data, bar_click_data):
    # Creation of the choropleth map to visualize energy disparities
    # We exclude groupings of countries
    excluded_countries = [
        'World',
        'Asia',
        'High-income countries',
        'Upper-middle-income countries',
        'Lower-middle-income countries',
        'European Union (27)',
        'Europe',
        'North America',
        'Africa',
        'USSR',
        'South America'
    ]

    # Creating a new DataFrame that excludes the specified countries
    df_only_countries = df[~df['country'].isin(excluded_countries)]

    # Filter the dataset based on selected year
    df_selected = df_only_countries[df_only_countries['year'] == selected_year]

    # Find the top 2 countries with the highest primary_energy_consumption
    top_countries = df_selected.nlargest(2, 'primary_energy_consumption')[
        'country'].tolist()

    # Create the choropleth map to visualize energy disparities
    map_fig = px.choropleth(df_selected,
                            locations="country",
                            locationmode="country names",
                            color="primary_energy_consumption",
                            hover_name="country",
                            hover_data=["primary_energy_consumption"],
                            projection="natural earth",
                            title=f"<b>Energy Consumption Disparities ({selected_year})</b><br><span style='font-size: 12px'>{top_countries[0]} and {top_countries[1]} have the Highest Energy Consumption in {selected_year}</span>",
                            range_color=[0, 45000],
                            color_continuous_scale=[
                                'rgb(165, 165, 165)', 'rgb(255,255,0)'],
                            labels={
                                'primary_energy_consumption': 'Energy Consumption (TWh)'}
                            )

    # Creation of the area chart to visualize electricity generation and sources
    # Filter the dataset based on 'world' country and selected years
    df_world = df[df['country'] == 'World']
    df_selected_years = df_world[df_world['year'] >= 1985]

    # Define colors for each area
    colors = {
        'fossil_electricity': 'rgb(247, 92, 92)',  # Brown 'rgb(165, 165, 165)'
        'renewables_electricity': 'rgb(112, 173, 70)',  # Green
        'nuclear_electricity': 'rgb(254, 102, 203)',  # Grey
        'other_renewable_electricity': 'rgb(68, 115, 197)'  # Blue
    }

    # Create subplots with 1 row and 1 column
    area_fig = make_subplots(rows=1, cols=1)

    # Add area traces for each area with specified colors
    for col in colors:
        area_fig.add_trace(go.Scatter(x=df_selected_years['year'], y=df_selected_years[col],
                                      fill='tozeroy', mode='none', name=col.replace('_', ' ').title(),
                                      fillcolor=colors[col]), row=1, col=1)

    # Update layout
    area_fig = area_fig.update_layout(title_text="<b>World Electricity Generation and Sources</b><br><span style='font-size: 12px'>Increase of Energy Consumption and its Sources in terawatt-hours from 1985 to 2022. Fossil Electricity leading Energy Source</span>",
                                      title_font_size=18,  # Set the font size for the main title
                                      xaxis_title='Year',
                                      yaxis_title='Electricity Generation (TWh)')

    # Creation of a pie chart displaying the share of electricity sources in percentages
    # Create a new dataframe containing only world and the selected year
    df_world = df[df['country'] == 'World']
    df_selected = df_world[df_world['year'] == selected_year]

    # Calculate the percentage of each energy source in the total electricity generation
    total_generation = df_selected['fossil_electricity'] + df_selected['renewables_electricity'] + \
        df_selected['nuclear_electricity'] + \
        df_selected['other_renewable_electricity']

    fossil_percentage = (
        df_selected['fossil_electricity'] / total_generation) * 100
    renewables_percentage = (
        df_selected['renewables_electricity'] / total_generation) * 100
    nuclear_percentage = (
        df_selected['nuclear_electricity'] / total_generation) * 100
    other_renewable_percentage = (
        df_selected['other_renewable_electricity'] / total_generation) * 100

    # Create a DataFrame for hover data
    hover_data_df = pd.DataFrame({
        'source': ['Fossil', 'Renewables', 'Nuclear', 'Other Renewable'],
        'percentage': [fossil_percentage.values[0], renewables_percentage.values[0], nuclear_percentage.values[0], other_renewable_percentage.values[0]]
    })

    # Define colors for each energy source
    colors = {
        'Fossil': 'rgb(247, 92, 92)',  # Brown
        'Renewables': 'rgb(112, 173, 70)',  # Green
        'Nuclear': 'rgb(254, 102, 203)',  # Grey
        'Other Renewable': 'rgb(68, 115, 197)'  # Blue
    }

    # Create the pie chart using px.pie
    pie_fig = px.pie(
        hover_data_df,
        names='source',
        values='percentage',
        color='source',
        color_discrete_map=colors,
        hover_name='source',
        hover_data=['percentage'],
        labels={'percentage': 'Percentage'},
        title="<b>Share of World Electricity Sources</b>",
        width=600, height=600
    )

    # Update hovertemplate to show the custom color for percentages
    pie_fig.update_traces(
        hovertemplate='%{label}<br><extra></extra>')

    # Convert number to with 1 decimal for display
    fossil_dec = round(fossil_percentage.values[0], 1)
    renewable_dec = round(
        renewables_percentage.values[0], 1) + round(other_renewable_percentage.values[0], 1)

    pie_fig.update_layout(
        title_text=f"<b>Share of World Electricity Sources</b><br><span style='font-size: 12px'>In {selected_year}, {fossil_dec}% of the Worlds Energy Supply comes from Fossil Fuels and {renewable_dec}% is Renewable", title_font_size=18)

    # Center the pie chart
    pie_fig.update_layout(
        autosize=False, margin=dict(l=0, r=150, b=150, t=150))

    # Creation of a bar chart to visualize the greenhouse gas emissions of the top 10 countries
    # Group the data by country and calculate the total greenhouse gas emissions
    df_only_countries = df[~df['country'].isin(excluded_countries)]
    df_selected = df_only_countries[df_only_countries['year'] == selected_year]

    # Sort the data by greenhouse gas emissions in descending order
    df_sorted = df_selected .sort_values(
        by='greenhouse_gas_emissions', ascending=False)

    # Select the top 10 countries
    top_10_countries = df_sorted.head(10)

    # Define the custom color for the top 3 countries and others
    custom_colors = ['rgb(126, 96, 0)'] * 3 + \
        ['rgb(165, 165, 165)'] * (len(top_10_countries) - 3)

    # Create the bar chart
    bar_chart = px.bar(top_10_countries,
                       x='country',
                       y='greenhouse_gas_emissions',
                       labels={
                           'greenhouse_gas_emissions': 'Greenhouse Gas Emissions (Metric tons CO2)'},
                       color='country',
                       color_discrete_sequence=custom_colors)

    bar_chart.update_layout(
        title_text=f"<b>Top 10 Countries with the Highest Greenhouse Gas Emissions ({selected_year})</b><br><span style='font-size: 12px'>{top_10_countries.iloc[0]['country']}, {top_10_countries.iloc[1]['country']}, {top_10_countries.iloc[2]['country']} are the Top 3 countries with the Highest C02 Emissions</span>",
        title_font_size=18,
        showlegend=True
    )

    # Scatter plot with Plotly
    # Clean the data by removing any rows with missing or invalid values
    df_cleaned = df_world.dropna(subset=['primary_energy_consumption', 'gdp'])

    # Calculate the correlation coefficient between 'primary_energy_consumption' and 'GDP'
    correlation_coefficient = df_cleaned['primary_energy_consumption'].corr(
        df_cleaned['gdp'])

    # Create a scatter plot with trendline
    scatter = go.Figure()

    scatter.add_trace(go.Scatter(
        x=df_cleaned['primary_energy_consumption'],
        y=df_cleaned['gdp'],
        mode='markers',
        marker=dict(color='blue'),
        name='Data Points'
    ))

    # Calculate the trendline (line of best fit)
    import numpy as np
    coefficients = np.polyfit(
        df_cleaned['primary_energy_consumption'], df_cleaned['gdp'], 1)
    trendline = np.polyval(
        coefficients, df_cleaned['primary_energy_consumption'])

    scatter.add_trace(go.Scatter(
        x=df_cleaned['primary_energy_consumption'],
        y=trendline,
        mode='lines',
        line=dict(color='red', width=2),
        name='Trendline'
    ))

    # Update layout
    scatter.update_layout(
        title="<b>Scatter Plot of Primary Energy Consumption compared to Gross Domestic Product (GDP)</b><br><span style='font-size: 12px'>With a correlation coefficient of 0.99, there is an almost complete correlation between GDP and Energy consumption</span>",
        xaxis_title="Energy Consumption (TWh)",
        yaxis_title="GDP",
        showlegend=True
    )

    # Creation of a grouped bar chart to visualize the electricity sources by primary energy consumption
    # Sort the dataframe by 'primary_energy_consumption'
    # Assuming your original DataFrame is called 'df_only_countries'
    countries_of_interest = [
        'Asia', 'Europe', 'North America', 'South America', 'Africa', 'Australia']
    filtered_df = df[df['country'].isin(countries_of_interest)].copy()
    filtered_df = filtered_df[filtered_df['year'] == selected_year]

    # Calculate the total energy consumption for each country
    filtered_df['total_energy_consumption'] = filtered_df[
        ['fossil_electricity', 'renewables_electricity',
            'nuclear_electricity', 'other_renewable_electricity']
    ].sum(axis=1)

    # Calculate the share of each electricity source and normalize them
    filtered_df['share_fossil'] = filtered_df['fossil_electricity'] / \
        filtered_df['total_energy_consumption']
    filtered_df['share_renewables'] = filtered_df['renewables_electricity'] / \
        filtered_df['total_energy_consumption']
    filtered_df['share_nuclear'] = filtered_df['nuclear_electricity'] / \
        filtered_df['total_energy_consumption']
    filtered_df['share_other_renewable'] = filtered_df['other_renewable_electricity'] / \
        filtered_df['total_energy_consumption']

    # Group the data by country and sort by primary_energy_consumption in descending order
    grouped_df = filtered_df.groupby('country').sum().sort_values(
        by='primary_energy_consumption', ascending=False)

    # Normalize the shares for each country again, as grouping may have introduced rounding errors
    grouped_df['total_shares'] = (
        grouped_df['share_fossil']
        + grouped_df['share_renewables']
        + grouped_df['share_nuclear']
        + grouped_df['share_other_renewable']
    )

    grouped_df['share_fossil'] = grouped_df['share_fossil'] / \
        grouped_df['total_shares']
    grouped_df['share_renewables'] = grouped_df['share_renewables'] / \
        grouped_df['total_shares']
    grouped_df['share_nuclear'] = grouped_df['share_nuclear'] / \
        grouped_df['total_shares']
    grouped_df['share_other_renewable'] = grouped_df['share_other_renewable'] / \
        grouped_df['total_shares']

    # Define custom RGB colors for each energy source
    color_map = {
        'share_fossil': 'rgb(165, 165, 165)',  # Brown
        'share_renewables': 'rgb(112, 173, 70)',  # Green
        'share_nuclear': 'rgb(165, 165, 165)',  # Grey
        'share_other_renewable': 'rgb(68, 115, 197)',  # Blue
    }

    # Create the stacked proportional bar plot with custom colors
    grouped_bar_chart = go.Figure()

    # Initialize variables to store the country and percentage with the highest sum total share in renewable electricity
    highest_renewable_country = None
    highest_renewable_percentage = 0.0

    for source in ['share_fossil', 'share_nuclear', 'share_renewables', 'share_other_renewable']:
        energy_source = source.split('_')[1].title() + ' Electricity'

        if source == 'share_other_renewable':
            # Update the label for 'share_other_renewable'
            energy_source = 'Other Renewable Electricity'

        if source == 'share_renewables':
            # Update the label for 'share_other_renewable'
            energy_source = 'Renewable Electricity'

        # Initialize text_data as None for this trace
        text_data = None

        if source == 'share_renewables':
            # Calculate the sum of 'share_renewables' and 'share_other_renewable' for the text display
            sum_renewables_other = grouped_df['share_renewables'] + \
                grouped_df['share_other_renewable']
            # Format the sum as a percentage with two decimal places
            text_data = [f'{val*100:.2f}%' for val in sum_renewables_other]

            # Check if the current percentage is higher than the stored highest percentage
            max_percentage_index = sum_renewables_other.idxmax()
            max_percentage_value = sum_renewables_other.loc[max_percentage_index]
            if max_percentage_value > highest_renewable_percentage:
                highest_renewable_country = max_percentage_index
                highest_renewable_percentage = max_percentage_value

        grouped_bar_chart.add_trace(go.Bar(
            x=grouped_df.index,
            y=grouped_df[source],
            text=text_data,  # Use the appropriate text_data for each trace
            textposition='inside',  # Place the text inside the bars
            name=energy_source,
            marker=dict(color=color_map[source]),
        ))

    # Update layout
    grouped_bar_chart.update_layout(
        title=f"<b>Share of Electricity Sources by Continent in {selected_year} sorted by Energy Consumption</b><br><span style='font-size: 12px'>{highest_renewable_country} has the highest share of Renewable Energy in {selected_year} with {round(highest_renewable_percentage*100, 2)}%</span>",
        xaxis_title="Country",
        yaxis_title="Proportion of Electricity Source",
        barmode='stack',  # Display bars in stacked mode
        showlegend=True,
    )

    # Track which input triggered the callback
    triggered_chart = dash.callback_context.triggered[0]['prop_id'].split('.')[
        0]

    # If the map chart triggered the callback and there is click data available
    if triggered_chart == 'map-graph' and map_click_data is not None:
        # Get the selected country from the map click data
        selected_country = map_click_data['points'][0]['location']

        # Update the bar chart trace to highlight the selected country
        for trace in bar_chart['data']:
            if trace['x'] == selected_country:
                trace['marker']['color'] = 'rgb(255, 0, 0)'  # Red for selected
            else:
                # Grey for others
                trace['marker']['color'] = 'rgb(165, 165, 165)'

    # If the bar chart triggered the callback and there is click data available
    if triggered_chart == 'bar-graph' and bar_click_data is not None:
        # Get the selected country from the bar chart click data
        selected_country = bar_click_data['points'][0]['x']

        # Update the choropleth map trace to highlight the selected country
        map_fig['data'][0]['selectedpoints'] = [
            df_selected.index.get_loc(selected_country)]

    return map_fig, bar_chart, area_fig, pie_fig, scatter, grouped_bar_chart


# Run the Dash web application
if __name__ == '__main__':
    app.run_server(debug=True)
