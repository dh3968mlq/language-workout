import dash_mantine_components as dmc
import dash_ag_grid as dag
from dash import dcc

def cre_layout_find_word(prefix, lspec):
    'Layout of the find word modal'

    colheading = lspec["colheading"]
    language = lspec["language"]

    lm = dmc.Modal(
            title=dmc.Text("Find",style={"fontWeight": 700, "fontSize":22, "line-height":24}),
            id=prefix+"fw-modal",
            styles={
                "header":{"padding-left":20, 
                          "padding-bottom":0, "padding-top":0,
                          "min-height":40,
                }
            },
            radius=20,
            children=[
                dmc.Group(
                    children=[                        
                            dmc.SegmentedControl(
                                id=prefix+"fw-segmented-within",
                                value="within",
                                data=[
                                    "within",
                                    "at start of",
                                ],
                            ),
                            dmc.SegmentedControl(
                                id=prefix+"fw-segmented-lang",
                                value=language.title(),
                                data=[
                                    language.title(),
                                    "English",
                                ],
                                styles={
                                    "label":{"p":"xs"},
                                },
                            ),
                    ],
                    gap='xs',
                ),
                dmc.Space(h=6),
                dmc.Grid(
                    align='center',
                    children=[
                        dmc.GridCol(
                            children=[
                                dmc.TextInput(value="", id=prefix+"fw-find-text",w="100%", debounce=500,
                                              placeholder="Enter search text"),
                            ],
                            span="auto"
                        ),
                    ]
                ),
                dmc.Text("0 words", id=prefix+"fw-text-wordcount", size="sm"),
                dag.AgGrid(
                    id=prefix+"fw-aggrid-find",
                    rowData=[],
                    dashGridOptions = {
                        'rowSelection': {
                            'mode': 'singleRow',
                            'enableClickSelection': True,
                            'checkboxes': False,
                        }
                    },
                    style = {
                        "height": 350, 
                    },
                    defaultColDef={
                        "wrapHeaderText": True,
                        "autoHeaderHeight": True,
                        "resizable": True,
                        "wrapText": True,
                        "autoHeight": True,
                        "cellStyle": {"lineHeight": "unset"},
                    },
                    columnDefs=[
                        {"field":colheading, "flex":1},
                        {
                            "field":"English word", 
                            "flex":2, 
                            "cellStyle": {"wordBreak": "normal", "lineHeight": "unset"}
                        },
                    ],
                ),
                dmc.Space(h=20),
                dmc.Group(
                    [
                        dmc.Button("Select", id=prefix+"fw-btn-select", disabled=True),
                        dmc.Button("Cancel", id=prefix+"fw-btn-cancel"),
                    ],
                    justify="flex-end",
                ),
            ],
        )
    return lm