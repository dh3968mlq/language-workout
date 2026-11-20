import dash_mantine_components as dmc

def cre_layout_add_vocab_list(prefix):
    'Add vocab list layout (admin mode only)'

    lm = dmc.Modal(
            title=dmc.Text("Add vocab list", style={"fontWeight": 600}),
            id=prefix+"vla-modal",
            children=[
                dmc.Textarea(
                    placeholder="New list name",
                    value="", 
                    id=prefix+"vla-new-list",
                    w="100%",
                    autosize=True,
                    debounce=250,
                ),
                dmc.Space(h=20),
                dmc.Group(
                    [
                        dmc.Button("Cancel", id=prefix+"vla-btn-cancel"),
                        dmc.Button("OK", id=prefix+"vla-btn-ok", disabled=True),
                    ],
                    justify="flex-end",
                ),
                dmc.Alert("List name is blank", id=prefix+"vla-alert-listname-blank"),
                dmc.Alert("Failed to add list - possible duplicate name?", id=prefix+"vla-alert-insert-failed", hide=True),
            ],
        )
    return lm