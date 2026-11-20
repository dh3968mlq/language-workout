import dash_mantine_components as dmc
import dash_ag_grid as dag

def cre_layout_vocab_lists(prefix, lspec):
    'Vocab list layout (admin mode only)'

    colheading = lspec["colheading"]

    lm = dmc.Modal(
            title=dmc.Text("Vocab lists", style={"fontWeight": 600}),
            id=prefix+"vl-modal",
            children=[
                dmc.Grid(
                    align='center',
                    children=[
                        dmc.GridCol(
                            children=[
                                dmc.Select(
                                    placeholder="Vocab lists",
                                    id=prefix+"vl-select-list",
                                    label="Lists",
                                    data=[],
                                    persistence=True, persistence_type="session",
                                    clearable=False,
                                    allowDeselect=False,
                                ),
                            ],
                            span="auto"
                        ),
                        dmc.GridCol(
                            dmc.Button(children="Add...", 
                                    id=prefix+"vl-vla-button-add-list", size="xs"),
                            span="content"
                        ),
                    ]
                ),
            dmc.Space(h=20),
            dag.AgGrid(
                    id=prefix+"vl-aggrid-words",
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
                        "cellStyle": {"wordBreak": "normal", "lineHeight": "unset"},
                    },
                    columnDefs=[
                        {"field":colheading, "flex":1},
                        {"field":"English word", "flex":2},
                    ],
                ),
                dmc.Space(h=20),
                dmc.Group(
                    [
                        dmc.Button("Add...", id=prefix+"vl-fw-btn-add-word"),  # Part of fw functional group
                        dmc.Button("Cancel", id=prefix+"vl-btn-cancel"),
                        dmc.Button("OK", id=prefix+"vl-btn-ok"),
                    ],
                    justify="flex-end",
                ),
            ],
        )
    return lm