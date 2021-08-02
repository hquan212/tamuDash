import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
from dash_core_components.Graph import Graph
import dash_html_components as html
import dash_table.FormatTemplate as FormatTemplate
import dash_table
import plotly.express as px
import pandas as pd

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

df = pd.read_csv('merged.csv', dtype={'Year' : object})
df = df.drop(['idx'], axis = 1)


df['YearSemesterMajor'] = df['Year'].apply(lambda x: x[2:]) + '_' + \
        df['Semester'].apply(lambda x: x[:3]) + '_' + \
        df['Major'].apply(lambda x: x[:len(x) : 2].replace(' ', '')) + '_' +\
        df['Degree'].apply(lambda x: x[0])

PAGE_SIZE = 40

app.layout = html.Div(
    className="row",
    children=[
        html.Div(id='intro', children=[html.H1(children='Tamu Salary Dashboard'),
        dcc.Markdown("""
        A dashboard with the historic self reported New Grad Texas A&M salaries. 
        
        Pulled from here [Salary Report](https://aggiesurveys.tamu.edu/public/Reports.aspx)
        
        To download the dataset:

        [csv file](https://datasets-baggies.s3.us-west-2.amazonaws.com/merged.csv)

        [How to filter for you major](https://dash.plotly.com/datatable/filtering)      contact me at [reddit u/theSimpleTheorem](https://old.reddit.com/user/theSimpleTheorem)
        """, style={'margin': '20px'}),
        ], className='twelve columns',),
        html.Div(
            dash_table.DataTable(
                id='table-paging-with-graph',
                columns=[
                    {"name": i, "id": i, 'type':'text'} for i in ['Semester', 'Year', 'Major', 'Degree']
                    
                ] + [
                    {"name": i, "id": i, 'type': 'numeric', 'format' : FormatTemplate.money(0)} for i in ['Avg', 'Max', 'Min','25th', 'Median', '75th']
                ] + [{"name": i, "id": i, 'type':'numeric'} for i in ['NumSalariesReported']] +
                [{"name": i, "id": i, 'type':'text'} for i in [ 'StDev', 'College']],
                style_cell={'textAlign': 'left', 'minWidth': '100px', 'width': '100px', 'maxWidth': '220px',
                            'overflow': 'hidden', 'textOverflow': 'ellipsis',},
                page_current=0,
                page_size=PAGE_SIZE,
                page_action='custom',
                filter_action='custom',
                filter_query='',
                style_header={ 'border': '2px solid black' },
                fixed_rows={'headers': True},
                sort_action='custom',
                sort_by=[{'column_id':'Major', 'direction': 'asc'}],
                style_table={'height': '300px', 'overflowY': 'auto'}
            ),
            className='twelve columns'
        ),
        html.Div(
            id='table-paging-with-scatter',
            className="five columns"
        ),
        html.Div(
            id='table-paging-with-histogram',
            className="six columns"
        ),
        html.Div(
            id='Multiplot',
            className="twelve columns"
        )
    ]
)

operators = [['ge ', '>='],
            ['le ', '<='],
            ['lt ', '<'],
            ['gt ', '>'],
            ['ne ', '!='],
            ['eq ', '='],
            ['contains '],
            ['datestartswith ']]


def split_filter_part(filter_part):
    for operator_type in operators:
        for operator in operator_type:
            if operator in filter_part:
                name_part, value_part = filter_part.split(operator, 1)
                name = name_part[name_part.find('{') + 1: name_part.rfind('}')]

                value_part = value_part.strip()
                v0 = value_part[0]
                if (v0 == value_part[-1] and v0 in ("'", '"', '`')):
                    value = value_part[1: -1].replace('\\' + v0, v0)
                else:
                    try:
                        value = float(value_part)
                    except ValueError:
                        value = value_part

                # word operators need spaces after them in the filter string,
                # but we don't want these later
                return name, operator_type[0].strip(), value

    return [None] * 3


@app.callback(
    Output('table-paging-with-graph', "data"),
    Input('table-paging-with-graph', "page_current"),
    Input('table-paging-with-graph', "page_size"),
    Input('table-paging-with-graph', "sort_by"),
    Input('table-paging-with-graph', "filter_query"))
def update_table(page_current, page_size, sort_by, filter):
    filtering_expressions = filter.split(' && ')
    dff = df
    for filter_part in filtering_expressions:
        col_name, operator, filter_value = split_filter_part(filter_part)
        if operator in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
            # these operators match pandas series operator method names
            dff = dff.loc[getattr(dff[col_name], operator)(filter_value)]
        elif operator == 'contains':
            dff = dff.loc[dff[col_name].str.contains(str(filter_value))]
        elif operator == 'datestartswith':
            # this is a simplification of the front-end filtering logic,
            # only works with complete fields in standard format
            dff = dff.loc[dff[col_name].str.startswith(filter_value)]

    if len(sort_by):
        dff = dff.sort_values(
            [col['column_id'] for col in sort_by],
            ascending=[
                col['direction'] == 'asc'
                for col in sort_by
            ],
            inplace=False
        )

    return dff.iloc[
        page_current*page_size: (page_current + 1)*page_size
    ].to_dict('records')


def createScatterplot(df):
    fig = px.scatter(df, x="Median", y="Max",
                    size="Avg", color="Degree", hover_name="Major", height=PAGE_SIZE*18, 
                    hover_data=['Min', '25th', 'Median', '75th', 'Max', 'Avg'],
                    title='Selected Median vs Max Salaries')
    return fig


def createMultiBarPlot(df):
    df['MajorCount'] = df['Major'] + ' - ' + df['NumSalariesReported'].astype(str)
    return px.bar(df, x="Major", y="Median", color="Year", barmode="group",
            text="MajorCount", opacity=0.8,
            facet_col="Degree",facet_row="Semester",  hover_data=['Min', '25th', 'Median', '75th', 'Max', 'Avg'],
            category_orders={"Degree": ["Bachelor", "Master", "Doctorate"],
                            "Semester": ["Spring", "Summer", "Fall"]}, height=PAGE_SIZE*25)

@app.callback(
    Output('table-paging-with-scatter', "children"),
    Input('table-paging-with-graph', "data"))
def update_graph(rows):
    dff = pd.DataFrame(rows)
    return html.Div(
        [dcc.Graph(
                id='scatter',
                figure=createScatterplot(dff))]
    )

@app.callback(
    Output('table-paging-with-histogram', "children"),
    Input('table-paging-with-graph', "data"))
def update_graph(rows):
    dff = pd.DataFrame(rows).sort_values(by=['Median'], ascending=False)
    return html.Div(
        [
        dcc.Graph(
            id='barPlot',
            figure= px.bar(dff, x="YearSemesterMajor", y="Median", 
            color="Major", hover_data=['Min', '25th', 'Median', '75th', 'Max', 'Avg'],
            title="Selected Majors vs. Median Salaries",  height=PAGE_SIZE*18)
            )
        ]
    )


@app.callback(
    Output('Multiplot', "children"),
    Input('table-paging-with-graph', "data"))
def update_graph(rows):
    dff = pd.DataFrame(rows)
    return html.Div(
        dcc.Graph(id='test',
        figure=createMultiBarPlot(dff))
    )


if __name__ == '__main__':
    app.run_server(debug=True)